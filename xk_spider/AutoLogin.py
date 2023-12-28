import ast
import base64
import json
import time

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from urllib.parse import urlparse, parse_qs


class AutoLogin:
    def __init__(self, url, path, name='', pswd=''):  # 增加自动登录中过验证码功能
        self.driver = webdriver.Chrome(executable_path=path)
        self.name = name
        self.url = url
        self.pswd = pswd

    def get_params(self):
        # 获得必要参数
        self.driver.get(self.url)
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, 'vcodeImg')))
        # 查找验证码标签
        img_tag = self.driver.find_element(By.ID, 'vcodeImg')
        src = img_tag.get_attribute('src')
        print(src)
        # 如果验证码为空 刷新页面
        while src == '':
            self.driver.refresh()
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, 'vcodeImg')))
            img_tag = self.driver.find_element(By.ID, 'vcodeImg')
            img_tag.click()
            time.sleep(3)
            src = img_tag.get_attribute('src')
        # 通过识别接口识别并获取验证码
        src = img_to_base64(src)
        vcode = imgcode_online(src)
        # 输入用户名 密码 验证码
        name_ele = self.driver.find_element(By.XPATH, '//input[@id="loginName"]')
        name_ele.send_keys(self.name)
        pswd_ele = self.driver.find_element(By.XPATH, '//input[@id="loginPwd"]')
        pswd_ele.send_keys(self.pswd)
        vcode_ele = self.driver.find_element(By.XPATH, '//input[@id="verifyCode"]')
        vcode_ele.send_keys(vcode)
        # 进行自动登录
        login_ele = self.driver.find_element(By.XPATH, '//button[@id="studentLoginBtn"]')
        login_ele.click()
        time.sleep(1)
        # 如果出现验证码错误弹窗 重新获取验证码
        while True:
            error_message = self.driver.find_element(By.XPATH, '//button[@class="cv-btn cv-btn-error"]')
            error_text = error_message.text
            print(error_text)
            if error_text == "验证码不正确":
                vcode_ele.clear()
                img_tag = self.driver.find_element(By.ID, 'vcodeImg')
                img_tag.click()
                time.sleep(3)
                src = img_tag.get_attribute('src')
                src = img_to_base64(src)
                vcode = imgcode_online(src)
                vcode_ele = self.driver.find_element(By.XPATH, '//input[@id="verifyCode"]')
                vcode_ele.send_keys(vcode)
                login_ele = self.driver.find_element(By.XPATH, '//button[@id="studentLoginBtn"]')
                login_ele.click()
                time.sleep(1)
            elif error_text == "认证失败":
                time.sleep(3)
                login_ele = self.driver.find_element(By.XPATH, '//button[@id="studentLoginBtn"]')
                login_ele.click()
                time.sleep(1)
            else:
                break
        # 点击选课按钮
        WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//button[@class="bh-btn '
                                                                                       'bh-btn bh-btn-primary '
                                                                                       'bh-pull-right"]')))
        ok_ele = self.driver.find_element(By.XPATH, '//button[@class="bh-btn bh-btn bh-btn-primary bh-pull-right"]')
        ok_ele.click()
        time.sleep(1)
        start_ele = self.driver.find_element(By.XPATH, '//button[@id="courseBtn"]')
        start_ele.click()

        try:
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//button[@class="bh-btn '
                                                                                           'cv-btn bh-btn-primary '
                                                                                           'bh-pull-right"]')))
            # 如果按钮出现，点击按钮
            button_ele = self.driver.find_element(By.XPATH, '//button[@class="bh-btn cv-btn bh-btn-primary '
                                                            'bh-pull-right"]')
            button_ele.click()
        except TimeoutException:
            # 如果按钮没有出现，可以选择忽略，继续运行其他代码
            pass
        if WebDriverWait(self.driver, 180).until(EC.presence_of_element_located((By.ID, 'aPublicCourse'))):
            time.sleep(2)  # waiting for loading
            cookie_lis = self.driver.get_cookies()
            cookies = ''
            for item in cookie_lis:
                cookies += item['name'] + '=' + item['value'] + '; '
            token = self.driver.execute_script('return sessionStorage.getItem("token");')  # 暂时无用
            batch_str = self.driver. \
                execute_script('return sessionStorage.getItem("currentBatch");').replace('null', 'None').replace(
                'false', 'False').replace('true', 'True')
            batch = ast.literal_eval(batch_str)
            # 获取当前的网址
            current_url = self.driver.current_url

            # 解析 URL 并获取查询参数
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)

            # 获取 token
            token = query_params.get('token', [None])[0]

            if token is not None:
                print("Token found in the URL")
                print("Token: {}".format(token))
            else:
                print("No token found in the URL")
            self.driver.quit()
            return cookies, batch['code'], token

        else:
            print('page load failed')
            self.driver.quit()
            return False


# 识别验证码(自己在本地部署或者嫖别人的)
def imgcode_online(imgurl):
    d = {'data': imgurl}
    response = requests.post('http://127.0.0.1:5000/base64img', data=d)
    if response.text:
        try:
            result = json.loads(response.text)
            if result['code'] == 200:
                print(result['data'])
                return result['data']
            elif result['code'] != 200:
                time.sleep(10)
                imgcode_online(imgurl)
            else:
                print(result['msg'])
                return 'error'
        except json.JSONDecodeError:
            print("Invalid JSON received")
            return 'error'
    else:
        print("Empty response received")
        return 'error'


def img_to_base64(img_url):
    response = requests.get(img_url)
    img_data = base64.b64encode(response.content).decode('utf-8')
    return 'data:image/jpeg;base64,' + img_data


if __name__ == '__main__':
    Url = 'http://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do'
    Name = ''
    Pswd = ''
    Headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/114.0.3987.116 Safari/537.36'
    }
