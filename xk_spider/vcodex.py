# 该文件用于提供识别验证码思路及进行验证码识别测试（可自行修改AutoLogin.py中的过验证码函数）
from selenium import webdriver
import json
import requests

# 配置WebDriver的路径（根据你的实际情况进行设置）
webdriver_path = '/usr/local/bin/chromedriver'

# 创建一个Chrome WebDriver实例
driver = webdriver.Chrome(webdriver_path)

# 打开网页
url = 'http://xk.ynu.edu.cn/'
driver.get(url)

# 查找img标签
img_tag = driver.find_element_by_id('vcodeImg')

# 获取src属性的值
src = img_tag.get_attribute('src')

# 打印src
print(src)

# 关闭WebDriver
driver.quit()

TOKEN = ' '  # token 获取：http://www.bhshare.cn/imgcode/gettoken
URL = 'http://www.bhshare.cn/imgcode/'  # 接口地址


def imgcode_online(imgurl):
    """
    在线图片识别
    :param imgurl: 在线图片网址 / 图片base64编码（包含头部信息）
    :return: 识别结果
    """
    data = {
        'token': TOKEN,
        'type': 'online',
        'uri': imgurl
    }
    response = requests.post(URL, data=data)
    print(response.text)
    result = json.loads(response.text)
    if result['code'] == 200:
        print(result['data'])
        return result['data']
    else:
        print(result['msg'])
        return 'error'


def imgcode_local(imgpath):
    """
    本地图片识别
    :param imgpath: 本地图片路径
    :return: 识别结果
    """
    data = {
        'token': TOKEN,
        'type': 'local'
    }

    # binary上传文件
    files = {'file': open(imgpath, 'rb')}

    response = requests.post(URL, files=files, data=data)
    print(response.text)
    result = json.loads(response.text)
    if result['code'] == 200:
        print(result['data'])
        return result['data']
    else:
        print(result['msg'])
        return 'error'


if __name__ == '__main__':
    imgcode_online(src)


