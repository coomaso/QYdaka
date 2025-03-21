from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import requests
import json
import random
from loguru import logger
import cv2
import numpy as np
import os
from PIL import Image
import io
import time
from datetime import datetime
from pathlib import Path

# 全局配置常量
CONFIG = {
    "base_url": "https://zhcjsmz.sc.yichang.gov.cn",
    "token_file": Path(os.path.expanduser("~/access_token.json")),
    "max_attempts": 20  # 最大尝试次数
}

headers = {
    "Host": "zhcjsmz.sc.yichang.gov.cn",
    "Connection": "keep-alive",
    "Accept": "*/*",
    "Content-Type": "application/json;charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.289 Safari/537.36",
    "Origin": "https://zhcjsmz.sc.yichang.gov.cn",
    "Referer": "https://zhcjsmz.sc.yichang.gov.cn/login/",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Authorization": "Basic cGlnOnBpZw=="
}

# AES 加密函数
def aes_encrypt(word, key_word):
    key = bytes(key_word, 'utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    encrypted = cipher.encrypt(pad(bytes(word, 'utf-8'), AES.block_size))
    return base64.b64encode(encrypted).decode('utf-8')

# AES 解密函数
def aes_decrypt(ciphertext, key_word):
    key = bytes(key_word, 'utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = unpad(cipher.decrypt(base64.b64decode(ciphertext)), AES.block_size)
    return decrypted.decode('utf-8')

# 生成客户端 UUID
def generate_client_uuid():
    hex_digits = "0123456789abcdef"
    s = [random.choice(hex_digits) for _ in range(36)]
    s[14] = "4"  # time_hi_and_version 字段
    s[19] = hex_digits[(int(s[19], 16) & 0x3) | 0x8]  # clock_seq_hi_and_reserved
    s[8] = s[13] = s[18] = s[23] = "-"
    return 'slider-' + ''.join(s)

# 计算缺口位置
def get_image_position(bg, tp, scale_factor):
    bg_img = cv2.imdecode(np.frombuffer(base64.b64decode(bg), np.uint8), cv2.IMREAD_COLOR)
    tp_img = cv2.imdecode(np.frombuffer(base64.b64decode(tp), np.uint8), cv2.IMREAD_COLOR)
    
    # 调整图像大小
    bg_img = cv2.resize(bg_img, (0, 0), fx=scale_factor, fy=scale_factor)
    tp_img = cv2.resize(tp_img, (0, 0), fx=scale_factor, fy=scale_factor)
    
    # 进行模板匹配
    res = cv2.matchTemplate(cv2.Canny(bg_img, 50, 400), cv2.Canny(tp_img, 50, 400), cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)
    
    logger.info(f"缺口的X坐标: {max_loc[0]:.4f}")
    return max_loc[0] - 2.5  # 适当调整偏移

# 读取 access_token.json 文件
def read_access_token():
    try:
        with open(CONFIG["token_file"], 'r') as json_file:
            data = json.load(json_file)
            return data.get('access_token'), data.get('timestamp', 0)
    except FileNotFoundError:
        return None, 0

# 获取或刷新 access_token
def get_access_token():
    attempt = 0
    while attempt < CONFIG["max_attempts"]:
        attempt += 1
        logger.info(f"第 {attempt} 次尝试获取 access_token...")

        session = requests.session()
        response = session.get(f"{CONFIG['base_url']}/login/#/login", headers=headers)
        session.cookies.update(requests.utils.dict_from_cookiejar(session.cookies))
        
        clientUUID = generate_client_uuid()
        timestamp = round(time.time() * 1000)
        
        data = {"captchaType": "blockPuzzle", "clientUid": clientUUID, "ts": timestamp}
        response = session.post(f"{CONFIG['base_url']}/code/create", headers=headers, json=data)
        response_data = response.json()
        
        secret_key = response_data["data"]["repData"]["secretKey"]
        token = response_data["data"]["repData"]["token"]
        
        pos = get_image_position(response_data["data"]["repData"]["originalImageBase64"], 
                                 response_data["data"]["repData"]["jigsawImageBase64"], 
                                 scale_factor=400/310)
        pos_str = json.dumps({"x": pos * (310 / 400), "y": 5})
        point_json = aes_encrypt(pos_str, secret_key)
        
        check_data = {"captchaType": "blockPuzzle", "clientUid": clientUUID, "pointJson": point_json, "token": token, "ts": timestamp}
        session.post(f"{CONFIG['base_url']}/code/check", json=check_data, headers=headers)
        
        captcha = aes_encrypt(token + '---' + pos_str, secret_key)
        
        login_data = {"sskjPassword": "2giTy1DTppbddyVBc0F6gMdSpT583XjDyJJxME2ocJ4="}
        
        response = session.post(f"{CONFIG['base_url']}/auth/custom/token?username=13487283013&grant_type=password&scope=server&code={captcha}&randomStr=blockPuzzle", json=login_data, headers=headers)
        
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            if access_token:
                with open(CONFIG["token_file"], 'w') as json_file:
                    json.dump({'access_token': access_token, 'timestamp': int(time.time())}, json_file)
                logger.info(f"成功获取 access_token: {access_token}")
                return access_token
        
        time.sleep(random.uniform(1, 3))  # 避免请求过于频繁
    
    logger.error("无法获取 access_token")
    return None

if __name__ == "__main__":
    existing_token, existing_timestamp = read_access_token()
    if not existing_token or (time.time() - existing_timestamp) > 21600:
        get_access_token()
    else:
        logger.info(f"Token 仍然有效, 到期时间: {datetime.fromtimestamp(existing_timestamp + 21600).strftime('%Y-%m-%d %H:%M:%S')}")
