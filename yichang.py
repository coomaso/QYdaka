import requests
from bs4 import BeautifulSoup
import pandas as pd

# 发送HTTP GET请求获取网页内容
url = 'http://ggzyjy.yichang.gov.cn/TPFront/InfoDetail/?InfoID=0c949814-e6b0-4ff1-9876-98cc1cd8cdab&CategoryNum=003001004001'
response = requests.get(url)

# 创建BeautifulSoup对象并解析网页内容
soup = BeautifulSoup(response.text, 'html.parser')

# 找到网页中的表格元素
table = soup.find('table')

# 将表格转换为DataFrame
df = pd.read_html(str(table))[0]

# 将DataFrame保存为图片
df.to_html('table.html')
imgkit.from_file('table.html', 'table.png')
