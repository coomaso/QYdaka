import requests
import json
import time
import datetime
import os
import random

login_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/workordereng/getEngsPageByUser"
getActivity_url = "https://zhcjsmz.sc.yichang.gov.cn/auth/oauth/token"
wexinqq_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4576c3a0-9e34-4857-92b1-96f91a6246cf"
idCardNumber_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/person/pageNotAvatar?idCardNumber=420526198606271020"
idPP_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/person/27faee7bb9cccc3322cad7d9da6ed623"
idXMB_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/workordereng/getEngInfoById?id=2f8af612cce346a69227890d4474abcd"

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

def get_access_token():
    data = {
        "username": "13487283013",
        "password": "13487283013",
        "type": "account",
        "grant_type": "password"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic cGlnOnBpZw==",
        "Host": "zhcjsmz.sc.yichang.gov.cn",
        "Origin": "https://zhcjsmz.sc.yichang.gov.cn",
        "Referer": "https://zhcjsmz.sc.yichang.gov.cn/login/"
    }
    response = requests.post(url=getActivity_url, data=data, headers=headers).json()
    access_token = response["access_token"]
    return access_token

def update_access_token():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = 'access_token.txt'
    file_path = os.path.join(current_dir, file_name)
    
    with open(file_path, 'r') as file:
        data = json.load(file)
        access_token = data.get('access_token')
        current_time = data.get('current_time')
    
    expiration_time = float(current_time) + 1800
    
    if expiration_time < datetime.datetime.now().timestamp():
        new_access_token = get_access_token()
        with open(file_path, 'w') as file:
            json.dump({'access_token': new_access_token, 'current_time': datetime.datetime.now().timestamp()}, file)
    else:
        return access_token

def get_ppname(access_token, XMB_ID, XMB_KEY):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f'bearer {access_token}',
        "host": "zhcjsmz.sc.yichang.gov.cn",
        "Referer": "https://zhcjsmz.sc.yichang.gov.cn/cyrygl/"
    }
    JobCheckurl = f'https://zhcjsmz.sc.yichang.gov.cn/laboratt/statisticsManager/getGlgwJobIsCheck?engId={XMB_ID}&workId={XMB_KEY}&checkDay={datetime.datetime.now().strftime("%Y-%m-%d")}'
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

def get_login():
    try:
        access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsaWNlbnNlIjoibWFkZSBieSBzc2tqIiwidXNlcl9uYW1lIjoiMTM0ODcyODMwMTMiLCJzY29wZSI6WyJzZXJ2ZXIiXSwib3JnYW5JZCI6IjQwMjg4MWM0MmNhZWM5YmYwMTJjYWVjYTM5N2YwMzcwIiwiZXhwIjoxNzAzNDQ0NDQ1LCJ1c2VySWQiOjExMDQsImF1dGhvcml0aWVzIjpbIlJPTEVfTEFCT1JfQ0lPIiwiUk9MRV9MQUJPUl9TTUIiXSwianRpIjoiMjhlMjg3MzctNjNkMi00OWU1LTk1NWEtOGFmMTlmYTE3MGZiIiwiY2xpZW50X2lkIjoicGlnIn0.AY4jCWbn22aUKU22dgkZHICrS_gXO7j51fUVz_WtQZY"
    except KeyError:
        access_token = get_access_token()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f'bearer {access_token}',
        "Referer": "https://zhcjsmz.sc.yichang.gov.cn/cyrygl/"
    }
    
    pages = 3
    page = 1

    while page <= pages:
        url = f'{login_url}?limit=10&page={page}'        
        try:
            response_list = requests.get(url=url, headers=headers).json()
        except KeyError:
            access_token = get_access_token()
            response_list = requests.get(url=url, headers=headers).json()
        
        for item in response_list['data']['records']:
            if item['isFinish'] == '否':
                XMB_NAME = item['sgxkName']
                XMB_ID = item['sgxkId']
                XMB_KEY = item['workOrderId']
                XMB = get_ppname(access_token, XMB_ID, XMB_KEY)
                current_time = (datetime.datetime.now() + datetime.timedelta(hours=8)).strftime("%m-%d %H:%M")
                content = (
                    f'## 考勤提示:<font color=\"info\">{XMB_NAME}</font>{current_time}\n'
                    f">**<font color=\"warning\">缺勤人员:{str(GESHIHUAXMB_QUE_NAME(XMB['QUE']))}</font>**\n"
                    f">请假人员:<font color=\"comment\">{str(GESHIHUAXMB_JIA_NAME(XMB['JIA']))}</font>\n"
                    f">完成人员:<font color=\"comment\">{str(GESHIHUAXMB_JIA_NAME(XMB['OK']))}</font>\n"
                )
                send_wexinqq_md(wexinqq_url, content)
             time.sleep(3 + 2 * random.random())               
        time.sleep(3 + 2 * random.random())   
        page += 1

get_login()
