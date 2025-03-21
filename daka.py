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
from pathlib import Path
import io
import time
from datetime import datetime, timedelta

max_attempts = 20  # 最大尝试次数
attempt = 0  # 计数器

BASE_url = "https://zhcjsmz.sc.yichang.gov.cn"
login_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/workordereng/getEngsPageByUser"
getActivity_url = "https://zhcjsmz.sc.yichang.gov.cn/auth/oauth/token"
wexinqq_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c54716bc-1e20-4e2c-99cd-e61267902850"
idCardNumber_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/person/pageNotAvatar?idCardNumber=420526198606271020"
idPP_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/person/27faee7bb9cccc3322cad7d9da6ed623"
idXMB_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/workordereng/getEngInfoById?id=2f8af612cce346a69227890d4474abcd"

headers = {
 "Host": "zhcjsmz.sc.yichang.gov.cn",
 "Connection": "keep-alive",
 "sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114"',
 "Accept": "*/*",
 "Content-Type": "application/json;charset=UTF-8",
 "sec-ch-ua-mobile": "?0",
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.289 Safari/537.36",
 "sec-ch-ua-platform": '"Windows"',
 "Origin": "https://zhcjsmz.sc.yichang.gov.cn",
 "Referer": "https://zhcjsmz.sc.yichang.gov.cn/login/",
 "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,vi;q=0.7",
 "Accept-Encoding": "gzip, deflate",
 "Authorization": "Basic cGlnOnBpZw=="
}

# 加密函数
def aes_encrypt(word, key_word):
 key = bytes(key_word, 'utf-8')
 srcs = bytes(word, 'utf-8')
 cipher = AES.new(key, AES.MODE_ECB)
 encrypted = cipher.encrypt(pad(srcs, AES.block_size))
 return base64.b64encode(encrypted).decode('utf-8')

def aes_decrypt(ciphertext, key_word):
 key = bytes(key_word, 'utf-8')
 ciphertext = base64.b64decode(ciphertext)
 cipher = AES.new(key, AES.MODE_ECB)
 decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
 return decrypted.decode('utf-8')

# 初始化 UUID
def generate_client_uuid():
 s = []
 hex_digits = "0123456789abcdef"
 for i in range(36):
     s.append(hex_digits[random.randint(0, 15)])
 s[14] = "4"  # time_hi_and_version字段的12-15位设置为0010
 s[19] = hex_digits[(int(s[19], 16) & 0x3) | 0x8]  # clock_seq_hi_and_reserved字段的6-7位设置为01
 s[8] = s[13] = s[18] = s[23] = "-"
 return 'slider-' + ''.join(s)

# 获取图片函数
def getImgPos(bg, tp, scale_factor):
 '''
 bg: 背景图片
 tp: 缺口图片
 out:输出图片
 '''
 # 解码Base64字符串为字节对象
 bg = base64.b64decode(bg)
 tp = base64.b64decode(tp)

 # 读取背景图片和缺口图片
 bg_img = cv2.imdecode(np.frombuffer(bg, np.uint8), cv2.IMREAD_COLOR) # 背景图片
 tp_img = cv2.imdecode(np.frombuffer(tp, np.uint8), cv2.IMREAD_COLOR)  # 缺口图片

 # 对图像进行缩放
 bg_img = cv2.resize(bg_img, (0, 0), fx=scale_factor, fy=scale_factor)
 tp_img = cv2.resize(tp_img, (0, 0), fx=scale_factor, fy=scale_factor)

 # 识别图片边缘
 bg_edge = cv2.Canny(bg_img, 50, 400)
 tp_edge = cv2.Canny(tp_img, 50, 400)

 # 转换图片格式
 bg_pic = cv2.cvtColor(bg_edge, cv2.COLOR_GRAY2RGB)
 tp_pic = cv2.cvtColor(tp_edge, cv2.COLOR_GRAY2RGB)

 # 缺口匹配
 res = cv2.matchTemplate(bg_pic, tp_pic, cv2.TM_CCOEFF_NORMED)
 _, _, _, max_loc = cv2.minMaxLoc(res)  # 寻找最优匹配

 # 缩放坐标
 #scaled_max_loc = (max_loc[0] * scale_factor, max_loc[1] * scale_factor)

 # 绘制方框
 th, tw = tp_pic.shape[:2]
 tl = max_loc  # 左上角点的坐标
 br = (tl[0] + tw, tl[1] + th)  # 右下角点的坐标
 cv2.rectangle(bg_img, (int(tl[0]), int(tl[1])), (int(br[0]), int(br[1])), (0, 0, 255), 2)  # 绘制矩形

 # 保存至本地
 output_path = os.path.join(os.getcwd(), "output_imageX.jpg")
 cv2.imwrite(output_path, bg_img)
 tp_img_path = os.path.join(os.getcwd(), "tp_imgX.jpg")
 cv2.imwrite(tp_img_path, tp_img)

 logger.info(f"缺口的X坐标: {max_loc[0]:.4f}")

 # 返回缺口的X坐标
 return max_loc[0] - 2.5

# 接受原始图像的Base64编码字符串和新的宽度作为参数，返回调整大小后的图像的Base64编码字符串
def resize_image(base64_string, new_width):
 # 将Base64字符串解码为字节数据
 image_data = base64.b64decode(base64_string)

 # 将字节数据转换为图像对象
 image = Image.open(io.BytesIO(image_data))

 # 确保图像的模式是RGB
 if image.mode != 'RGB':
     image = image.convert('RGB')

 # 计算高度以保持宽高比
 original_width, original_height = image.size
 new_height = int((new_width / original_width) * original_height)

 # 调整图像大小
 resized_image = image.resize((new_width, new_height))

 # 将调整大小后的图像转换为Base64字符串
 buffered = io.BytesIO()
 resized_image.save(buffered, format="JPEG")
 resized_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

 return resized_base64


def send_wexinqq_md(webhook, content):
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    alarm = {
        'msgtype': 'markdown',
        'markdown': {
            'content': content
        }
    }
    data = json.dumps(alarm)
    requests.post(url=webhook, data=data, headers=header)

def GESHIHUAXMB_QUE_NAME(data):
    if data:
        return ''.join(data)
    else:
        return "没有"

def get_ppname(access_token, XMB_ID, XMB_KEY):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f'bearer {access_token}',
        "host": "zhcjsmz.sc.yichang.gov.cn",
        "Referer": "https://zhcjsmz.sc.yichang.gov.cn/cyrygl/"
    }
    JobCheckurl = f'https://zhcjsmz.sc.yichang.gov.cn/laboratt/statisticsManager/getGlgwJobIsCheck?engId={XMB_ID}&workId={XMB_KEY}&checkDay={datetime.now().strftime("%Y-%m-%d")}'
    response_name = requests.get(url=JobCheckurl, headers=headers).json()
    
    NAME = {"OK": [], "QUE": [], "JIA": []}
    
    for item in response_name['data']:
        if item['pp'] == '施工单位' and item['state'] == 1:
            NAME['QUE'].append('@' + item['name'] + ' ')
        elif item['pp'] == '施工单位' and item['state'] == 2:
            NAME['JIA'].append('@' + item['name'] + ' ')
        elif item['pp'] == '施工单位' and item['state'] == 0:
            NAME['OK'].append('@' + item['name'] + ' ')
    
    return NAME

def format_result(data):
    result = ""
    for item in data:
        project = item[0]
        names = ''.join(item[1].split("'")[1:-1])
        result += f">{project}:<font color=\"warning\">@{names}</font>\n"
    return result

def get_login(access_token_value):
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f'bearer {access_token_value}',
        "Referer": "https://zhcjsmz.sc.yichang.gov.cn/cyrygl/"
    }
    
    page = 1
    pages = 1
    while page <= pages:
        url = f'{login_url}?limit=10&page={page}'        
        try:
            response_list = requests.get(url=url, headers=headers).json()
            pages = response_list['data']['pages']
            for item in response_list['data']['records']:
                if item['isFinish'] == '否':
                    XMB_NAME = item['sgxkName']
                    XMB_ID = item['sgxkId']
                    XMB_KEY = item['workOrderId']
                    XMB = get_ppname(access_token_value, XMB_ID, XMB_KEY)
                    current_time = (datetime.now() + timedelta(hours=8)).strftime("%m-%d %H:%M")
                    content = (
                        f'## 考勤提示:<font color=\"info\">{XMB_NAME}</font>{current_time}\n'
                        f">**<font color=\"warning\">缺勤人员:{str(GESHIHUAXMB_QUE_NAME(XMB['QUE']))}</font>**\n"
                        f">请假人员:<font color=\"comment\">{str(GESHIHUAXMB_QUE_NAME(XMB['JIA']))}</font>\n"
                        f">完成人员:<font color=\"comment\">{str(GESHIHUAXMB_QUE_NAME(XMB['OK']))}</font>\n"
                    )
                    send_wexinqq_md(wexinqq_url, content)
                    time.sleep(3 + 2 * random.random())
        except KeyError as e:
            logger.error(f"数据解析错误: {e}")
        except requests.RequestException as e:
            logger.error(f"请求失败: {e}")             
        time.sleep(3 + 2 * random.random())
        page += 1

# 初始化 existing_access_token 和 existing_timestamp
existing_access_token = None
existing_timestamp = 0

# 判断 access_token 是否过期（6 小时）
if not existing_access_token or (time.time() - existing_timestamp) > (6 * 60 * 60):
    logger.info("需要刷新Token")
    success = False
    while attempt < max_attempts and not success:
        attempt += 1
        logger.info(f"第 {attempt} 次尝试获取 access_token...")

        session = requests.session()
        response = session.get("https://zhcjsmz.sc.yichang.gov.cn/login/#/login", headers=headers)
        
        # 解析 Cookie
        cookies_dict = requests.utils.dict_from_cookiejar(session.cookies)
        session.cookies.update(cookies_dict)

        clientUUID = generate_client_uuid()
        current_timestamp_milliseconds = round(time.time() * 1000)

        data = {
            "captchaType": "blockPuzzle",
            "clientUid": clientUUID,
            "ts": current_timestamp_milliseconds
        }

        # 获取 API 响应
        response = session.post(f"{BASE_url}/code/create", headers=headers, json=data)
        
        # 先检查状态码
        if response.status_code != 200:
            logger.error(f"API 请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
            raise ValueError("API 请求失败，请检查请求参数或服务器状态")
        
        # 尝试解析 JSON
        try:
            response_data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 失败，响应内容: {response.text}, 错误信息: {str(e)}")
            raise ValueError("API 返回的不是有效的 JSON 数据")
        
        # 确保 response_data 不是 None
        if not response_data:
            logger.error(f"API 返回空数据，响应内容: {response.text}")
            raise ValueError("API 返回的数据为空")
        
        # 确保 response_data 结构正确
        if "data" not in response_data or "repData" not in response_data["data"]:
            logger.error(f"API 返回的数据格式不正确: {response_data}")
            raise ValueError("API 返回的数据缺少 'data' 或 'repData' 字段")
        
        # 解析数据
        secret_key = response_data["data"]["repData"]["secretKey"]
        token = response_data["data"]["repData"]["token"]
        bg_img_base64 = response_data["data"]["repData"]["originalImageBase64"]
        hk_img_base64 = response_data["data"]["repData"]["jigsawImageBase64"]


        pos = getImgPos(bg_img_base64, hk_img_base64, scale_factor=400 / 310)
        posStr = '{"x":' + str(pos * (310 / 400)) + ',"y":5}'
        pointJson = aes_encrypt(posStr, secret_key)
        logger.info(f"pointJson {pointJson}")
        
        pverdat = json.dumps({
            "captchaType": "blockPuzzle",
            "clientUid": clientUUID,
            "pointJson": pointJson,
            "token": token,
            "ts": current_timestamp_milliseconds
        })

        htm = session.post(f"{BASE_url}/code/check", json=json.loads(pverdat), headers=headers)
        logger.info(f"图形验证check回参 {htm.json()}")

        captcha = aes_encrypt(token + '---' + posStr, secret_key)
        logger.info(f"加密后的 captcha: {captcha}")

        data = {
            "sskjPassword": "2giTy1DTppbddyVBc0F6gMdSpT583XjDyJJxME2ocJ4="
        }
        headers["Content-Type"] = "application/json"

        htm = session.post(
            f"{BASE_url}/auth/custom/token?username=13487283013&grant_type=password&scope=server&code={captcha}&randomStr=blockPuzzle",
            json=data, 
            headers=headers
        )

        logger.info(f"请求返回状态码: {htm.status_code}, 返回内容: {htm.text}")

        try:
            response_json = htm.json()
            logger.info(f"返回 JSON: {response_json}")  
            access_token_value = response_json.get('access_token')

            if access_token_value:
                logger.info(f"第{attempt}次尝试成功")
                success = True
                break
        except Exception as e:
            logger.error(f"尝试{attempt}失败: {str(e)}")
            time.sleep(random.uniform(1, 10))
    
    if not success:
        logger.critical("达到最大尝试次数仍失败")
        exit(1)

else:
    logger.info(f"Token 仍有效，到期时间: {datetime.fromtimestamp(existing_timestamp + 21600).strftime('%Y-%m-%d %H:%M:%S')}")

get_login(access_token_value)
