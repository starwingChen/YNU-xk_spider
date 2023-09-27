from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
import time
import ast
import random
import requests
import json


class AutoLogin:
    def __init__(self, url, path, name='', pswd='', token=''):  # 增加自动登录中过验证码功能
        self.driver = webdriver.Chrome(executable_path=path)
        self.name = name
        self.url = url
        self.pswd = pswd
        self.token = token

    def get_params(self):
        # 获得必要参数
        self.driver.get(self.url)
        self.driver.implicitly_wait(15)
        # 查找验证码标签
        img_tag = self.driver.find_element_by_id('vcodeImg')
        src = img_tag.get_attribute('src')
        # 如果验证码为空 刷新页面
        while src == '':
            self.driver.refresh()
            time.sleep(3)
            img_tag = self.driver.find_element_by_id('vcodeImg')
            img_tag.click()
            time.sleep(3)
            src = img_tag.get_attribute('src')
        # 通过识别接口识别并获取验证码
        vcode = imgcode_online(src, self.token)
        # 输入用户名 密码 验证码
        name_ele = self.driver.find_element_by_xpath('//input[@id="loginName"]')
        name_ele.send_keys(self.name)
        pswd_ele = self.driver.find_element_by_xpath('//input[@id="loginPwd"]')
        pswd_ele.send_keys(self.pswd)
        vcode_ele = self.driver.find_element_by_xpath('//input[@id="verifyCode"]')
        vcode_ele.send_keys(vcode)
        # 进行自动登录
        login_ele = self.driver.find_element_by_xpath('//button[@id="studentLoginBtn"]')
        login_ele.click()
        time.sleep(1)
        # 如果出现验证码错误弹窗 重新获取验证码
        while True:
            error_message = self.driver.find_element(By.XPATH, '//button[@class="cv-btn cv-btn-error"]')
            error_text = error_message.text
            print(error_text)
            if error_text == "验证码不正确":
                vcode_ele.clear()
                img_tag = self.driver.find_element_by_id('vcodeImg')
                src = img_tag.get_attribute('src')
                vcode = imgcode_online(src, self.token)
                vcode_ele = self.driver.find_element_by_xpath('//input[@id="verifyCode"]')
                vcode_ele.send_keys(vcode)
                login_ele = self.driver.find_element_by_xpath('//button[@id="studentLoginBtn"]')
                login_ele.click()
                time.sleep(1)
            elif error_text == "认证失败":
                login_ele = self.driver.find_element_by_xpath('//button[@id="studentLoginBtn"]')
                login_ele.click()
                time.sleep(1)
            else:
                break
        # 点击选课按钮
        ok_ele = self.driver.find_element_by_xpath('//button[@class="bh-btn bh-btn bh-btn-primary bh-pull-right"]')
        ok_ele.click()
        time.sleep(1)
        start_ele = self.driver.find_element_by_xpath('//button[@id="courseBtn"]')
        start_ele.click()

        if WebDriverWait(self.driver, 180).until(EC.presence_of_element_located((By.ID, 'aPublicCourse'))):
            time.sleep(2)  # waiting for loading
            cookie_lis = self.driver.get_cookies()
            cookies = ''
            for item in cookie_lis:
                cookies += item['name'] + '=' + item['value'] + '; '
            token = self.driver.execute_script('return sessionStorage.getItem("token");')
            batch_str = self.driver. \
                execute_script('return sessionStorage.getItem("currentBatch");').replace('null', 'None').replace(
                'false', 'False').replace('true', 'True')
            batch = ast.literal_eval(batch_str)
            self.driver.quit()

            return cookies, token, batch['code']

        else:
            print('page load failed')
            self.driver.quit()
            return False

    # 暂时无用
    def keep_connect(self):
        flag = 1
        st = time.perf_counter()
        while True:
            try:
                if flag == 1:
                    ele = self.driver.find_element_by_xpath('//a[@id="aPublicCourse"]')
                    ele.click()
                    flag = 2
                    time.sleep(random.randint(20, 40))
                elif flag == 2:
                    ele = self.driver.find_element_by_xpath('//a[@id="aProgramCourse"]')
                    ele.click()
                    flag = 1
                    time.sleep(random.randint(20, 40))

            except NoSuchElementException:
                print('连接已断开')
                print(f'运行时间：{(time.perf_counter() - st) // 60} min')
                # self.driver.quit()
                break


# 识别验证码(该借口地址每天提供30次识别，精度问题可通过重复识别解决)
def imgcode_online(imgurl, token):
    data = {
        'token': token,
        'type': 'online',
        'uri': imgurl
    }
    # URL =   # 接口地址
    response = requests.post('http://www.bhshare.cn/imgcode/', data=data)
    print(response.text)
    result = json.loads(response.text)
    if result['code'] == 200:
        print(result['data'])
        return result['data']
    elif result['code'] == 0:
        time.sleep(10)
        imgcode_online(imgurl, token)
    else:
        print(result['msg'])
        return 'error'


if __name__ == '__main__':
    Url = 'http://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do'
    Name = ''
    Pswd = ''
    Headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/114.0.3987.116 Safari/537.36'
    }
