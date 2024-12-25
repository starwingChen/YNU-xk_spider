import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from fake_useragent import UserAgent

from xk_spider.AutoLogin import AutoLogin
from xk_spider.GetCourse import GetCourse

if hasattr(sys, '_MEIPASS'):
    data_path = os.path.join(sys._MEIPASS, 'data', 'browsers.json')
else:
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'browsers.json')
# 程序全自动运行，如果出现bug请提issue
ua = UserAgent()
headers = {
    'User-Agent': ua.random
}
url = 'http://xk.ynu.edu.cn/'
stdCode = ''  # 在''中填入你的学号
pswd = ''  # 填你的密码
key = ''  # 填你在server酱上获取到的key
path = ''  # 填写你的chromedriver路径，如 '/usr/local/bin/chromedriver 或 C:/Program Files/Google/Chrome/Application/chromedriver'
# 下面这个列表填你想查询的 素选课 ，以 ['课程名称', '授课老师'], 的格式填，注意最后有一个 英文 逗号

# -----  注意，课程名称要保证在选课页面你能用这个名称搜得出来 !!!  -----

publicCourses = [
    # ['大学生创新创业教育', '何鸣皋'],  # 这是个测试用例，可以先不修改直接运行看看是否成功，如果不小心抢到了自己手动退掉就好
]

'''下面这个列表填你想查询的体育课，包括必修和选修，格式填写同上
体育课格式如下，请确保完全按照体育课程名填写，有的课程名没有括号'''
peCourses = [
    # ['羽毛球（四）', '范丽霞'],
]

# 下面这个列表填你想查询的 主修课，包括必修和选修，格式填写同上
programCourse = [
    # ['大学生创新创业教育', '段连丽'],
]

'''以上两个列表理论上可以接受任意数量的课程，填写模板如下。但数量最好不要超过你CPU的核心数（一般电脑都在4核以上）
programCourse = [
    ['课程1', '老师1'], 
    ['课程2', '老师2'], 
    ['课程3', '老师3'], 
]
'''

while True:
    try:
        al = AutoLogin(url, path, stdCode, pswd)
        params = al.get_params()
        if not params:
            continue
        headers['cookie'], batchCode, Token = params
        headers['Token'] = Token
        headers['Authorization'] = 'Bearer ' + Token

        gc = GetCourse(headers, stdCode, batchCode, al.driver, url, path, stdCode, pswd)

        ec = ThreadPoolExecutor()
        taskList = []
        for course in publicCourses:
            taskList.append(ec.submit(gc.judge, course[0], course[1], key, kind='素选'))
        for course in programCourse:
            taskList.append(ec.submit(gc.judge, course[0], course[1], key, kind='主修'))
        for course in peCourses:
            taskList.append(ec.submit(gc.judge, course[0], course[1], key, kind='体育'))

        for future in as_completed(taskList):
            result = future.result()
            print(result)
            if not result:
                break  # If the judge method returns False, break the loop to start a new login process
    except Exception as e:
        print(f"An error occurred: {e}, restarting the login process.")
