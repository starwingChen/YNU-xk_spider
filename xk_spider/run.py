from concurrent.futures import ThreadPoolExecutor, as_completed

from xk_spider.AutoLogin import AutoLogin
from xk_spider.GetCourse import GetCourse

# 程序全自动运行，如果出现bug请提issue
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/114.0.3987.116 Safari/537.36'
}
url = 'http://xk.ynu.edu.cn/'
stdCode = ''  # 在''中填入你的学号
pswd = ''  # 填你的密码,如果你有安全上的考虑也可以等浏览器打开了再填
key = ''  # 填你在server酱上获取到的key
path = ''  # 填写你的chromedriver路径，如 '/usr/local/bin/chromedriver'
# 下面这个列表填你想查询的 素选课 ，以 ['课程名称', '授课老师'], 的格式填，注意最后有一个 英文 逗号

# -----  注意，课程名称要保证在选课页面你能用这个名称搜得出来 !!!  -----

publicCourses = [
    # ['环境教育', '蔡葵'],  # 这是个测试用例，可以先不修改直接运行看看是否成功，如果不小心抢到了自己手动退掉就好
]

# 下面这个列表填你想查询的 主修课，包括必修和选修，格式填写同上
programCourse = [
    ['电子商务与政务', '赵娜'],
]

'''以上两个列表理论上可以接受任意数量的课程，填写模板如下。但数量最好不要超过你CPU的核心数（一般电脑都在4核以上）
programCourse = [
    ['课程1', '老师1'], 
    ['课程2', '老师2'], 
    ['课程3', '老师3'], 
]
'''
while True:
    al = AutoLogin(url, path, stdCode, pswd)
    headers['cookie'], batchCode = al.get_params()

    '''至此程序已经可以运行了。在程序运行期间请不要登录选课系统，否则程序会终止运行'''
    '''已破除自动注销机制，实现了7*24小时运行，如果程序突然中止了，那是选课系统在更新，这个没办法解决，只能等更新结束后重新运行'''
    '''因为用了线程池，按理说会有线程同步上的问题，但在这个爬虫上几乎不会产生，如果您遇到了可以联系我，我再对代码做修改'''

    '''如果本项目有帮到你，还请点击GitHub主页右上角的star支持下 :)'''
    gc = GetCourse(headers, stdCode, batchCode, al.driver)

    ec = ThreadPoolExecutor()
    taskList = []
    for course in publicCourses:
        taskList.append(ec.submit(gc.judge, course[0], course[1], key, kind='素选'))
    for course in programCourse:
        taskList.append(ec.submit(gc.judge, course[0], course[1], key, kind='主修'))

    for future in as_completed(taskList):
        print(future.result())
