import ast
import random
import re
import time

import requests
from requests.exceptions import HTTPError
from requests.utils import dict_from_cookiejar


def to_wechat(key, title, string):
    url = 'https://sc.ftqq.com/' + key + '.send'
    dic = {
        'text': title,
        'desp': string
    }
    requests.get(url, params=dic)

    return title + '：已发送至微信'


class GetCourse:
    def __init__(self, headers: dict, stdcode, batchcode, driver, url, path, stdCode, pswd):
        self.driver = driver
        self.headers = headers
        self.stdcode = stdcode
        self.batchcode = batchcode
        self.url = url
        self.path = path
        self.stdCode = stdCode
        self.pswd = pswd

    def judge(self, course_name, teacher, key='', kind=''):
        # 人数未满才返回classid
        classtype = "XGXK"
        if kind == '素选':
            kind = 'publicCourse.do'
        elif kind == '主修':
            kind = 'programCourse.do'
            classtype = "FANKC"
        elif kind == '体育':
            kind = 'programCourse.do'
            classtype = "TYKC"
        elif kind == '跨专业':
            kind = 'programCourse.do'
            classtype = "FAWKC"
        url = 'http://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/elective/' + kind

        while True:
            try:
                query = self.__judge_datastruct(course_name, classtype)
                r = requests.post(url, data=query, headers=self.headers)
                r.raise_for_status()
                flag = 0
                while not r:
                    if flag > 2:
                        to_wechat(key, f'{course_name} 查询失败，请检查失败原因', '线程结束')
                        return False
                    print(f'[warning]: jugde()函数正尝试再次爬取')
                    time.sleep(3)
                    r = requests.post(url, data=query, headers=self.headers)
                    try:
                        setcookie = r.cookies
                    except KeyError:
                        setcookie = ''

                    if setcookie:
                        # 将 RequestsCookieJar 对象转换为字典
                        cookies_dict = dict_from_cookiejar(setcookie)
                        # 将字典转换为字符串
                        setcookie_str = '; '.join([f'{k}={v}' for k, v in cookies_dict.items()])

                        # 在字符串中搜索_WEU Cookie
                        match_weu = re.search(r'_WEU=.+?; ', setcookie_str)
                        if match_weu:
                            update_weu = match_weu.group(0)
                            self.headers['cookie'] = re.sub(r'_WEU=.+?; ', update_weu, self.headers.get('cookie', ''))
                        else:
                            print("No _WEU match found")

                        # 在字符串中搜索其他Cookie并进行更新
                        match_jsessionid = re.search(r'JSESSIONID=.+?; ', setcookie_str)
                        if match_jsessionid:
                            update_jsessionid = match_jsessionid.group(0)
                            self.headers['cookie'] = re.sub(r'JSESSIONID=.+?; ', update_jsessionid,
                                                            self.headers.get('cookie', ''))

                        match_pgv_pvi = re.search(r'pgv_pvi=.+?; ', setcookie_str)
                        if match_pgv_pvi:
                            update_pgv_pvi = match_pgv_pvi.group(0)
                            self.headers['cookie'] = re.sub(r'pgv_pvi=.+?; ', update_pgv_pvi,
                                                            self.headers.get('cookie', ''))

                        print(f'[current cookie]: {self.headers["cookie"]}')
                    else:
                        print("No setcookie found")

                temp = r.text.replace('null', 'None').replace('false', 'False').replace('true', 'True')
                res = ast.literal_eval(temp)

                if res['msg'] == '未查询到登录信息':
                    print('登录失效，请重新登录')
                    return False

                if kind == 'publicCourse.do':
                    datalist = res['dataList']
                elif kind == 'programCourse.do':
                    datalist = res['dataList'][0]['tcList']
                else:
                    print('kind参数错误，请重新输入')
                    return False

                for course in datalist:
                    remain = int(course['classCapacity']) - int(course['numberOfFirstVolunteer'])
                    if remain > 0 and course['teacherName'] == teacher:
                        string = f'{course_name} {teacher}：{remain}人空缺'
                        print(string)
                        to_wechat(key, f'{course_name} 余课提醒', string)
                        res = self.post_add(course_name, teacher, classtype, course['teachingClassID'], key)
                        # 若同一个老师开设多门同样课程，持续抢课
                        if '该课程与已选课程时间冲突' in res:
                            continue
                        if '人数已满' in res:
                            continue
                        if '添加选课志愿成功' in res:
                            return res
                        return res

                print(f'{course_name} {teacher}：人数已满 {time.ctime()}')
                sleep_time = random.randint(3, 10)
                time.sleep(sleep_time)

            except HTTPError or SyntaxError:
                print('登录失效，请重新登录')
                return False

    def post_add(self, classname, teacher, classtype, classid, key):
        query = self.__add_datastruct(classid, classtype)

        url = 'http://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/elective/volunteer.do'
        r = requests.post(url, headers=self.headers, data=query)
        flag = 0
        while not r:
            if flag > 2:
                to_wechat(key, f'{classname} 有余课，但post未成功', '线程结束')
                break
            print(f'[warning]: post_add()函数正尝试再次请求')
            time.sleep(3)
            r = requests.post(url, headers=self.headers, data=query)
            flag += 1

        messge_str = r.text.replace('null', 'None').replace('false', 'False').replace('true', 'True')
        messge = ast.literal_eval(messge_str)['msg']
        title = '抢课结果'
        string = '[' + teacher + ']' + classname + ': ' + messge
        to_wechat(key, title, string)
        return string

    def __add_datastruct(self, classid, classtype) -> dict:
        post_course = {
            "data": {
                "operationType": "1",
                "studentCode": self.stdcode,
                "electiveBatchCode": self.batchcode,
                "teachingClassId": classid,
                "isMajor": "1",
                "campus": "05",  # 01是东陆的校区代码
                "teachingClassType": classtype
            }
        }
        query = {
            'addParam': str(post_course)
        }

        return query

    def __judge_datastruct(self, course, classtype) -> dict:
        data = {
            "data": {
                "studentCode": self.stdcode,
                "campus": "05",  # 01是东陆的校区代码
                "electiveBatchCode": self.batchcode,
                "isMajor": "1",
                "teachingClassType": classtype,
                "checkConflict": "2",
                "checkCapacity": "2",
                "queryContent": course
            },
            "pageSize": "10",
            "pageNumber": "0",
            "order": ""
        }
        query = {
            'querySetting': str(data)
        }

        return query
