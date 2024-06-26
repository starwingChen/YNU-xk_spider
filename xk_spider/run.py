from concurrent.futures import ThreadPoolExecutor, as_completed

from fake_useragent import UserAgent

from xk_spider.AutoLogin import AutoLogin
from xk_spider.GetCourse import GetCourse

# 程序全自动运行，如果出现bug请提issue
ua = UserAgent()
headers = {
    'User-Agent': ua.random
}
url = 'http://xk.ynu.edu.cn/'
stdCode = ''  # 在''中填入你的学号
pswd = ''  # 填你的密码,如果你有安全上的考虑也可以等浏览器打开了再填
key = ''  # 填你在server酱上获取到的key
path = ''  # 填写你的chromedriver路径，如 '/usr/local/bin/chromedriver'
# 下面这个列表填你想查询的 素选课 ，以 ['课程名称', '授课老师'], 的格式填，注意最后有一个 英文 逗号

# -----  注意，课程名称要保证在选课页面你能用这个名称搜得出来 !!!  -----

publicCourses = [
    ['幸福在哪里', '姜素萍'],  # 这是个测试用例，可以先不修改直接运行看看是否成功，如果不小心抢到了自己手动退掉就好
]

# 下面这个列表填你想查询的 主修课，包括必修和选修，格式填写同上
programCourse = [
    # ['启发式与元启发式算法', '江华'],
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

        for future in as_completed(taskList):
            result = future.result()
            print(result)
            if not result:
                break  # If the judge method returns False, break the loop to start a new login process
    except Exception as e:
        print(f"An error occurred: {e}, restarting the login process.")
