from concurrent.futures import ThreadPoolExecutor, as_completed

from xk_spider.AutoLogin import AutoLogin
from xk_spider.GetCourse import GetCourse

# 程序运行后会打开浏览器进入选课登录页面，请登录进去直到能看到具体的课程，然后就可以把浏览器关了
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/80.0.3987.116 Safari/537.36'
}

url = 'http://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do'
stdCode = ''  # 在''中填入你的学号
pswd = ''  # 填你的密码
# 如果你有安全上的考虑，上两行不填也行，等浏览器打开了再填也可以
key = ''  # 填你在server酱上获取到的key

# 下面这个列表填你想查询的 素选课 ，以 ['课程全称', '授课老师'], 的格式填，注意最后有一个 英文 逗号
publicCourses = [
    ['初级泰语', '赵娟'],  # 这是个测试用例，可以先不修改直接运行看看是否成功
]

# 下面这个列表填你想查询的 主修课，包括必修和选修，格式填写同上
programCourse = [
    ['课程全称', '授课老师'],  # 格式同上，如果不需要请把 整行 都删掉
]

'''以上两个列表理论上可以接受任意数量的课程，填写模板如下。但数量最好不要超过你CPU的核心数（一般电脑都在4核以上）
programCourse = [
    ['课程1', '老师1'], 
    ['课程2', '老师2'], 
    ['课程3', '老师3'], 
]
'''
al = AutoLogin(url, stdCode, pswd)
headers['cookie'], headers['token'], batchCode = al.get_params()

# 想让程序出错几率少点就把下面这行取消注释(即把最前面的#号和空格都删掉)，但就不能把打开的浏览器关掉了
# al.keep_connect()

'''至此程序已经可以运行了'''
gc = GetCourse(headers, stdCode, batchCode)

ec = ThreadPoolExecutor(max_workers=6)
taskList = []
for course in publicCourses:
    taskList.append(ec.submit(gc.judge, course[0], course[1], key, kind='素选'))
for course in programCourse:
    taskList.append(ec.submit(gc.judge, course[0], course[1], key, kind='主修'))

for future in as_completed(taskList):
    print(future.result())
