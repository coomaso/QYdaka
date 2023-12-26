import requests
import json
import time
import datetime
import os
import random

login_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/workordereng/getEngsPageByUser"
getActivity_url = "https://zhcjsmz.sc.yichang.gov.cn/auth/oauth/token"
wexinqq_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c54716bc-1e20-4e2c-99cd-e61267902850"
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

#远程获取access_token.json
def get_access_token():
    try:
        url = 'https://bimcn.co/bid/SHIMING/access_token.json'
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            data = response.json()
            return data.get('access_token')
        else:
            print(f"Failed to fetch access token. Status code: {response.status_code}")
            return None

    except requests.RequestException as e:
        # Handle network or request-related errors
        print(f"Error fetching access token: {e}")
        return None
    except json.JSONDecodeError:
        # Handle the case where the response content is not valid JSON
        print(f"Error decoding JSON in the response")
        return None

def update_access_token():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = 'access_token.json'
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
        access_token = get_access_token()
    except KeyError:
        access_token = get_access_token()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f'bearer {access_token}',
        "Referer": "https://zhcjsmz.sc.yichang.gov.cn/cyrygl/"
    }
    

    page = 1
    pages = 1
    while page <= pages:
        url = f'{login_url}?limit=10&page={page}'        
        try:
            response_list = requests.get(url=url, headers=headers).json()
        except KeyError:
            access_token = get_access_token()
            response_list = requests.get(url=url, headers=headers).json()
        pages = response_list['data']['pages']
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
                    f">请假人员:<font color=\"comment\">{str(GESHIHUAXMB_QUE_NAME(XMB['JIA']))}</font>\n"
                    f">完成人员:<font color=\"comment\">{str(GESHIHUAXMB_QUE_NAME(XMB['OK']))}</font>\n"
                )
                send_wexinqq_md(wexinqq_url, content)
                time.sleep(3 + 2 * random.random())
        time.sleep(3 + 2 * random.random())
        page += 1

get_login()
