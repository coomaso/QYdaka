import requests
import json
import time
import datetime
import os


# 实例属性
# 登录接口url https://www.sskj-hengyun.com/laboratt/statisticsManager/getGlgwJobIsCheck?engId=122bc04151764d4dbeaa9490e2ced0d5&workId=2945d191797449cd69f60dffeeaa3d0f&checkDay=2023-07-06
login_url = "https://zhcjsmz.sc.yichang.gov.cn/labor/workordereng/getEngsPageByUser"
# 需要使用token获取数据接口url
getActivity_url = "https://zhcjsmz.sc.yichang.gov.cn/auth/oauth/token"
#企业微信机器人hook
wexinqq_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=c54716bc-1e20-4e2c-99cd-e61267902850"
#身份证idCardNumber查询接口 获取电话号码,身份证号码,头像
idCardNumber_url="https://www.sskj-hengyun.com/labor/person/pageNotAvatar?idCardNumber=420526198606271020"
#身份证idCardNumber反查接口
idPP_url="https://www.sskj-hengyun.com/labor/person/27faee7bb9cccc3322cad7d9da6ed623"
#项目信息反查
idXMB_url="https://www.sskj-hengyun.com/labor/workordereng/getEngInfoById?id=2f8af612cce346a69227890d4474abcd"

def Send_Wexinqq_MD(webhook, content):
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
    info = requests.post(url=webhook, data=data, headers=header)

def get_access_token():
# 从JSON API中获取最新的access_token
    data = {
    "username":"13487283013",
    "password":"13487283013",
    "type":"account",
    "grant_type":"password"
    }
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
    "Content-Type": "application/x-www-form-urlencoded",
    "Authorization": "Basic cGlnOnBpZw==",
    "Host": "zhcjsmz.sc.yichang.gov.cn",
    "Origin": "https://zhcjsmz.sc.yichang.gov.cn",
    "Referer": "https://zhcjsmz.sc.yichang.gov.cn/login/"
    }
    # 编码格式为application/x-www-form-urlencoded;charset=UTF-8，所以请求参数为dict，使用data参数
    response = requests.post(url=getActivity_url, data=data, headers=headers).json()
    access_token = response["access_token"]
    return access_token
    
def update_access_token():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = 'access_token.txt'
    file_path = os.path.join(current_dir, file_name)
    # 读取本地txt文件中的写入时间属性
    with open(file_path, 'r') as file:
        data = json.load(file)
        access_token = data.get('access_token')
        current_time = data.get('current_time')
    # 检查access_token是否过期
    expiration_time = float(current_time) + 1800
    # 设置access_token的过期时间为1小时，单位为秒
    if expiration_time < datetime.datetime.now().timestamp():
        # 获取JSON API中最新的access_token
        new_access_token = get_access_token()
        # 更新本地txt文件中的access_token和current_time值
        with open(file_path, 'w') as file:
            json.dump({'access_token': new_access_token, 'current_time': datetime.datetime.now().timestamp()}, file)
    else:
        return access_token

def get_ppname(Access_token,XMB_ID,XMB_KEY):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f'bearer {Access_token}',
        "host": "www.sskj-hengyun.com",
        "Referer": "https://www.sskj-hengyun.com/cyrygl/"
        }
    JobCheckurl = 'https://www.sskj-hengyun.com/laboratt/statisticsManager/getGlgwJobIsCheck?engId='+XMB_ID+'&workId='+XMB_KEY+'&checkDay='+datetime.datetime.now().strftime("%Y-%m-%d")
    #JobCheckurl = 'https://www.sskj-hengyun.com/laboratt/statisticsManager/getGlgwJobIsCheck?engId='+XMB_ID+'&workId='+XMB_KEY+'&checkDay='+(datetime.datetime.now()+datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
    response_name = requests.get(url=JobCheckurl,headers=headers).json()
    #print(response_name)
    #data = json.loads(response_name)
    #print(JobCheckurl)
    #print(response_name)
    #print(data)
    NAME = {
    "OK": [], 
    "QUE": [], 
    "JIA": []
    }
    for item in response_name['data']:
        if item['pp'] == '施工单位' and item['state'] == 1:
             # 获取state=1对应的key=name的values值并打印 缺勤人员
            #XMB_QUE_NAME = item['name']
            NAME['QUE'].append('@' + item['name'] +' ')
        elif item['pp'] == '施工单位' and item['state'] == 2:
#            # 获取state=2对应的key=name的values值并打印 请假人员
#            #XMB_JIA_NAME = item['name']
            NAME['JIA'].append('@' + item['name'] +' ')
        elif item['pp'] == '施工单位' and item['state'] == 0:
#            # 获取state=0对应的key=name的values值并打印 正常人员
#            #XMB_OK_NAME = item['name']
            NAME['OK'].append('@' + item['name'] +' ')
#        else:
#            break
#        NAME = json.dumps(NAME)
    #XMB_QUE_NAME = json.dumps(XMB_QUE_NAME)
    #if len(XMB_QUE_NAME)>2:
    return NAME
    #print("考勤信息,请假人员:"+XMB_JIA_NAME.encode('utf-8').decode('unicode_escape')+"缺卡人员:"+XMB_QUE_NAME.encode('utf-8').decode('unicode_escape'))
def GESHIHUAXMB2(data):
    for item in data:
        project = item[0]
        names = ''.join(item[1].split("'")[1:-1])
        result = f">{project}:<font color=\"warning\">@{names}</font>\n"
    return result
    
def GESHIHUA2(data):
    for item in data:
        project = item[0]
        names = ''.join(item[1].split("'")[1:-1])
        result = f">{project}:<font color=\"comment\">@{names}</font>\n"
    return result
    
def GESHIHUAXMB_QUE_NAME(data):
    if data:
        return ''.join(data)
    else:
        return "没有"

# def GESHIHUAXMB_QUE_NAME(data):
#     for item in data:
#         project = item[0]
#         names = ''.join(item[1].split("'")[1:-1])
#         result += f"><font color=\"warning\">缺勤人员:{names}</font>\n"
#         return result
#     else:
#         return "没有缺勤人员"
    
def GESHIHUAXMB_JIA_NAME(data):
    if data:
        return ''.join(data)
    else:
        return "没有"

# def GESHIHUAXMB_JIA_NAME(data):
#     for item in data:
#         project = item[0]
#         names = ''.join(item[1].split("'")[1:-1])
#         result += f">请假人员:<font color=\"comment\">{names}</font>\n"
#         return result
#     else:
#         return "没有请假人员"
    
def get_login():
    try:
        access_token = get_access_token()
    except KeyError:
        access_token = get_access_token()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36 Edg/87.0.664.47",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f'bearer {access_token}',
        "Referer": "https://www.sskj-hengyun.com/cyrygl/"
        }
    #获取在建项目列表
    #response = requests.get(url=login_url,headers=headers).json()
    #pages = response['data']['pages']
    #print(pages)
    pages = 3
    page = 1

    while page <= pages:
        begin = time.time()
        #初始化起始循环时间
        url = login_url+'?limit=10&page='+str(page)
        try:
            response_list = requests.get(url=url,headers=headers).json()
        except KeyError:
            access_token = get_access_token()
            response_list = requests.get(url=url,headers=headers).json()
        #print(response_array["data"])
        #response2 = json.loads(response_array)
        # 遍历data列表，找到state=0的项
        #response_list = json.loads(response_array)
        #print(response_list["data"]["records"])
        #response_list = json.loads(response_array)
        #print(response_list["data"]["records"])
        for item in response_list['data']['records']:
            #print(item['sgxkName'])
            #XMB = []
            if item['isFinish'] == '否':
                # 获取state=0对应的key=name的values值并打印
                XMB_NAME = item['sgxkName']
                XMB_ID = item['sgxkId']
                XMB_KEY = item['workOrderId']
                XMB_MANAGER = item['sgdwXmLxr']
                XMB_PHONE = item['sgdwXmPhone']
                #print(XMB_NAME+XMB_ID+XMB_MANAGER+XMB_PHONE)
                XMB = get_ppname(access_token,XMB_ID,XMB_KEY)
                #print(XMB)
                current_time = (datetime.datetime.now()+datetime.timedelta(hours=8)).strftime("%m-%d %H:%M") 
                #content = f'#考勤提示:<font color=\"warning\">'+XMB_NAME+'</font>'+datetime.datetime.now().strftime("%m-%d %H:%M")+'\n'+str(GESHIHUAXMB_QUE_NAME(XMB['QUE']))+'\n'+str(GESHIHUAXMB_JIA_NAME(XMB['JIA']))
                content = f'## 考勤提示:<font color=\"info\">'+XMB_NAME+'</font>'+current_time+'\n>**<font color=\"warning\">缺勤人员:'+str(GESHIHUAXMB_QUE_NAME(XMB['QUE']))+'</font>**\n>请假人员:<font color=\"comment\">'+str(GESHIHUAXMB_JIA_NAME(XMB['JIA']))+'</font>\n>完成人员:<font color=\"comment\">'+str(GESHIHUAXMB_JIA_NAME(XMB['OK'])+'</font>\n')
                #content = f'#考勤提示:<font color=\"warning\">'+XMB_NAME+'</font>'+datetime.datetime.now().strftime("%m-%d %H:%M")+'\n'+XMB['QUE']+'\n'+XMB['JIA']
                #print(content)
                #if  len(message)>4:
                #    XMB.append([XMB_NAME,message])
                #    content = f'#'+XMB_NAME+'考勤提示:'+ datetime.datetime.now().strftime("%m-%d %H:%M")+'\n'+GESHIHUAXMB(XMB_QUE_NAME)'\n'+GESHIHUA(XMB_JIA_NAME)
                Send_Wexinqq_MD(wexinqq_url, content)
                #print(GESHIHUA(XMB))
                #message = json.dumps(message)
                #print(message.encode('utf-8').decode('unicode_escape'))
                #Send_Wexinqq_MD(wexinqq_url,message.encode('utf-8').decode('unicode_escape'))
        #content = XMB_NAME +' '+ datetime.datetime.now().strftime("%m-%d %h")+'# 考勤提示 \n'+ message
            time.sleep( (3.0-time.time()+begin) if time.time()-begin<3.0 else 0.0)
        #Send_Wexinqq_MD(wexinqq_url, content)
        #发送企业信息
        time.sleep( (5.0-time.time()+begin) if time.time()-begin<5.0 else 0.0)
        #间隔10秒执行下次循环
        #print(XMB)
        page += 1
        #result = get_all_keys_and_values(XMB, "")
        #print(result)
        #print(XMB)
    #print(GESHIHUA(XMB))
    #print(XMB)
    #content = f'# 考勤提示:'+ datetime.datetime.now().strftime("%m-%d %H:%M")+'\n'+str(GESHIHUA(XMB))
    #Send_Wexinqq_MD(wexinqq_url, content)
#KEY = update_access_token()
#XMB_ID = "2f8af612cce346a69227890d4474abcd"
#XMB_KEY = "d17ca274f07a85ee581624c7d1dfe0a0"
#get_ppname(KEY,XMB_ID,XMB_KEY)
get_login()
