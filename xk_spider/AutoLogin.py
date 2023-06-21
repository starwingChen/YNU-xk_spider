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
    def __init__(self, url, path, name='', pswd='', token=''):
        self.driver = webdriver.Chrome(executable_path=path)
        self.name = name
        self.url = url
        self.pswd = pswd
        self.token = token

    def get_params(self):
        # 获得必要参数
        self.driver.get(self.url)
        self.driver.implicitly_wait(5)
        # 查找img标签
        img_tag = self.driver.find_element_by_id('vcodeImg')
        src = img_tag.get_attribute('src')
        vcode = imgcode_online(src, self.token)
        name_ele = self.driver.find_element_by_xpath('//input[@id="loginName"]')
        name_ele.send_keys(self.name)
        pswd_ele = self.driver.find_element_by_xpath('//input[@id="loginPwd"]')
        pswd_ele.send_keys(self.pswd)
        vcode_ele = self.driver.find_element_by_xpath('//input[@id="verifyCode"]')
        vcode_ele.send_keys(vcode)
        login_ele = self.driver.find_element_by_xpath('//button[@id="studentLoginBtn"]')
        login_ele.click()
        time.sleep(1)
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
