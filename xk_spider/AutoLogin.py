import base64
import json
import threading
import time
import traceback
from urllib.parse import urlparse, parse_qs

import requests
from requests.exceptions import RequestException
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

REQUEST_TIMEOUT = 10


class AutoLogin:
    def __init__(self, url, path, name='', pswd=''):
        self.timer = None
        self._driver_lock = threading.RLock()
        # 设置 Chrome 为无界面模式
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920x1080')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-extensions')

        service = Service(executable_path=path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.name = name
        self.url = url
        self.pswd = pswd

    def start_timer(self):
        self.timer = threading.Timer(60.0, self.close_driver)
        self.timer.start()

    def close_driver(self):
        with self._driver_lock:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def get_params(self):
        # 获得必要参数
        self.start_timer()
        try:
            self.driver.get(self.url)
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.ID, 'vcodeImg')))
            # 查找验证码标签
            img_tag = self.driver.find_element(By.ID, 'vcodeImg')
            src = img_tag.get_attribute('src')
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
            flag = 0
            # 如果出现验证码错误弹窗 重新获取验证码
            while True:
                if flag < 3:
                    try:
                        error_message = self.driver.find_element(By.XPATH, '//button[@id="errorMsg"]')
                        error_text = error_message.text
                    except NoSuchElementException:
                        # 元素不存在，可能登录成功跳转了
                        break
                    login_ele = self.driver.find_element(By.XPATH, '//button[@id="studentLoginBtn"]')
                    print(error_text)
                    if error_text == "验证码不正确":
                        flag += 1
                        vcode_ele.clear()
                        img_tag = self.driver.find_element(By.ID, 'vcodeImg')
                        img_tag.click()
                        time.sleep(3)
                        src = img_tag.get_attribute('src')
                        src = img_to_base64(src)
                        vcode = imgcode_online(src)
                        vcode_ele = self.driver.find_element(By.XPATH, '//input[@id="verifyCode"]')
                        vcode_ele.send_keys(vcode)
                        login_ele.click()
                        time.sleep(1)
                    elif error_text == "认证失败":
                        self.close_driver()
                        return False
                    else:
                        break
                else:
                    self.close_driver()
                    return False
            # 点击选课按钮
            try:
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.XPATH, '//button[@class="bh-btn '
                                                                                              'cv-btn bh-btn-primary '
                                                                                              'bh-pull-right"]')))
                # 如果按钮出现，点击按钮
                button_ele = self.driver.find_element(By.XPATH, '//button[@class="bh-btn cv-btn bh-btn-primary '
                                                                'bh-pull-right"]')
                button_ele.click()
            except TimeoutException:
                # 如果按钮没有出现，可以选择忽略，继续运行其他代码
                pass
            # 等待确认按钮，最多刷新 3 次
            ok_btn_xpath = '//button[@class="bh-btn bh-btn bh-btn-primary bh-pull-right"]'
            for retry in range(3):
                try:
                    WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, ok_btn_xpath)))
                    ok_ele = self.driver.find_element(By.XPATH, ok_btn_xpath)
                    ok_ele.click()
                    break
                except TimeoutException:
                    if retry < 2:
                        print(f"[WARNING] 确认按钮未找到，刷新页面重试 ({retry + 1}/3)")
                        self.driver.refresh()
                        time.sleep(2)
                    else:
                        print("[ERROR] 确认按钮重试 3 次仍未找到")
                        self.close_driver()
                        return False
            time.sleep(1)
            try:
                start_ele = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//button[@id="courseBtn"]'))
                )
                self.driver.execute_script("arguments[0].click();", start_ele)
            except TimeoutException:
                print("在尝试点击时发生超时。")
                self.close_driver()
                return False

            # 等待选课页面加载，最多刷新 3 次
            for retry in range(3):
                try:
                    WebDriverWait(self.driver, 8).until(EC.presence_of_element_located((By.ID, 'aPublicCourse')))
                    break
                except TimeoutException:
                    if retry < 2:
                        print(f"[WARNING] 选课页面未加载，刷新重试 ({retry + 1}/3)")
                        self.driver.refresh()
                        time.sleep(2)
                    else:
                        print("[ERROR] 选课页面重试 3 次仍未加载")
                        self.close_driver()
                        return False

            time.sleep(2)  # waiting for loading
            cookie_lis = self.driver.get_cookies()
            cookies = ''
            for item in cookie_lis:
                cookies += item['name'] + '=' + item['value'] + '; '
            batch_str = self.driver.execute_script('return sessionStorage.getItem("currentBatch");')
            if not batch_str:
                print("[ERROR] sessionStorage 中未找到 currentBatch")
                self.close_driver()
                return False
            try:
                batch = json.loads(batch_str)
            except json.JSONDecodeError:
                print(f"[ERROR] currentBatch 解析失败: {batch_str[:100] if batch_str else 'None'}")
                self.close_driver()
                return False
            # 获取当前的网址
            current_url = self.driver.current_url

            # 解析 URL 并获取查询参数
            parsed_url = urlparse(current_url)
            query_params = parse_qs(parsed_url.query)

            # 获取 token
            token = query_params.get('token', [None])[0]

            if token is not None:
                print(f"Token: {token[:10]}...")
            else:
                print("No token found in the URL")
            self.close_driver()
            batch_code = batch.get('code')
            if not batch_code:
                print("[ERROR] batch 中未找到 code 字段")
                return False
            return cookies, batch_code, token
        except Exception as e:
            print(f"登录过程发生异常: {e}")
            traceback.print_exc()
            self.close_driver()
            return False


def imgcode_online(imgurl):
    if not hasattr(imgcode_online, "counter"):
        imgcode_online.counter = 0
    if not hasattr(imgcode_online, "timestamp"):
        imgcode_online.timestamp = time.time()

    current_time = time.time()
    if current_time - imgcode_online.timestamp > 60:
        imgcode_online.counter = 0
        imgcode_online.timestamp = current_time

    imgcode_online.counter += 1
    if imgcode_online.counter > 10:
        imgcode_online.counter = 0
        imgcode_online.timestamp = current_time
        return False

    for attempt in range(3):
        try:
            d = {'data': imgurl}
            response = requests.post('http://127.0.0.1:5000/base64img', data=d, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            if response.text:
                result = response.json()
                if result.get('code') == 200:
                    print(result.get('data'))
                    return result.get('data')
                elif result.get('code') != 200:
                    time.sleep(5)
                    continue
                else:
                    print(result.get('msg'))
                    return False
        except (RequestException, ValueError) as e:
            print(f"OCR 请求失败 (尝试 {attempt + 1}/3): {e}")
            time.sleep(3)
    return False


def img_to_base64(img_url):
    try:
        response = requests.get(img_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except RequestException as e:
        print(f"获取验证码图片失败: {e}")
        return False
    img_data = base64.b64encode(response.content).decode('utf-8')
    return 'data:image/jpeg;base64,' + img_data
