from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import requests
import json
import random
import uuid
from loguru import logger
import cv2
import numpy as np
import os
from PIL import Image
import io
import time
from datetime import datetime

max_attempts = 20  # 最大尝试次数
attempt = 0  # 计数器

base_url = "https://zhcjsmz.sc.yichang.gov.cn"

headers = {
    "Host": "zhcjsmz.sc.yichang.gov.cn",
    "Connection": "keep-alive",
    "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
    "Accept": "*/*",
    "Content-Type": "application/json;charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.289 Safari/537.36",
    "Origin": "https://zhcjsmz.sc.yichang.gov.cn",
    "Referer": "https://zhcjsmz.sc.yichang.gov.cn/login/",
}

# AES 加密函数（使用 CBC 模式）
def aes_encrypt(word, key_word):
    key = key_word.encode('utf-8')
    iv = key[:16]  # 取前16字节作为 IV
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(pad(word.encode('utf-8'), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')

def aes_decrypt(ciphertext, key_word):
    key = key_word.encode('utf-8')
    iv = key[:16]  
    ciphertext = base64.b64decode(ciphertext)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return decrypted.decode('utf-8')

# 生成 UUID
def generate_client_uuid():
    return f"slider-{uuid.uuid4()}"

# 获取图片缺口位置
def getImgPos(bg, tp, scale_factor):
    try:
        bg = base64.b64decode(bg)
        tp = base64.b64decode(tp)

        bg_img = cv2.imdecode(np.frombuffer(bg, np.uint8), cv2.IMREAD_COLOR)
        tp_img = cv2.imdecode(np.frombuffer(tp, np.uint8), cv2.IMREAD_COLOR)

        if bg_img is None or tp_img is None:
            logger.error("图片解码失败")
            return None

        bg_img = cv2.resize(bg_img, (0, 0), fx=scale_factor, fy=scale_factor)
        tp_img = cv2.resize(tp_img, (0, 0), fx=scale_factor, fy=scale_factor)

        bg_edge = cv2.Canny(bg_img, 50, 400)
        tp_edge = cv2.Canny(tp_img, 50, 400)

        res = cv2.matchTemplate(bg_edge, tp_edge, cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(res)

        logger.info(f"缺口的X坐标: {max_loc[0]:.4f}")
        return max_loc[0] - 2.5

    except Exception as e:
        logger.error(f"计算图片缺口位置失败: {str(e)}")
        return None

# 读取 access_token
def read_access_token():
    try:
        with open('access_token.json', 'r') as json_file:
            data = json.load(json_file)
            return data.get('access_token'), data.get('timestamp', 0)
    except FileNotFoundError:
        return None, 0

# 读取 access_token
existing_access_token, existing_timestamp = read_access_token()

if not existing_access_token or (time.time() - existing_timestamp) > (6 * 60 * 60):
    session = requests.session()
    
    while attempt < max_attempts:
        attempt += 1
        logger.info(f"第 {attempt} 次尝试获取 access_token...")

        try:
            session.get(f"{base_url}/login/#/login", headers=headers)

            clientUUID = generate_client_uuid()
            current_timestamp_milliseconds = round(time.time() * 1000)

            data = {
                "captchaType": "blockPuzzle",
                "clientUid": clientUUID,
                "ts": current_timestamp_milliseconds
            }

            response = session.post(f"{base_url}/code/create", headers=headers, json=data)
            response_data = response.json()

            secret_key = response_data["data"]["repData"]["secretKey"]
            token = response_data["data"]["repData"]["token"]
            bg_img_base64 = response_data["data"]["repData"]["originalImageBase64"]
            hk_img_base64 = response_data["data"]["repData"]["jigsawImageBase64"]

            pos = getImgPos(bg_img_base64, hk_img_base64, scale_factor=400 / 310)
            if pos is None:
                logger.error("未能成功计算滑块位置，重试...")
                continue

            posStr = json.dumps({"x": pos * (310 / 400), "y": 5})
            pointJson = aes_encrypt(posStr, secret_key)

            pverdat = {
                "captchaType": "blockPuzzle",
                "clientUid": clientUUID,
                "pointJson": pointJson,
                "token": token,
                "ts": current_timestamp_milliseconds
            }

            htm = session.post(f"{base_url}/code/check", json=pverdat, headers=headers)
            logger.info(f"图形验证check回参 {htm.json()}")

            captcha = aes_encrypt(token + '---' + posStr, secret_key)

            htm = session.post(
                f"{base_url}/auth/custom/token?username=13487283013&grant_type=password&scope=server&code={captcha}&randomStr=blockPuzzle",
                json={"sskjPassword": "2giTy1DTppbddyVBc0F6gMdSpT583XjDyJJxME2ocJ4="},
                headers=headers
            )

            response_json = htm.json()
            access_token_value = response_json.get('access_token')

            if access_token_value:
                logger.info(f"成功获取 access_token: {access_token_value}")
                with open('access_token.json', 'w') as json_file:
                    json.dump({'access_token': access_token_value, 'timestamp': int(time.time())}, json_file)
                break

        except Exception as e:
            logger.error(f"尝试 {attempt} 失败: {str(e)}")
            time.sleep(random.uniform(1, 3))

else:
    logger.info(f"Token仍有效，到期时间: {datetime.fromtimestamp(existing_timestamp + 21600).strftime('%Y-%m-%d %H:%M:%S')}")  
