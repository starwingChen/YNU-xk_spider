import requests
import ast
import time
import re
from requests.exceptions import HTTPError


def to_wechat(key, title, string):
    url = 'https://sc.ftqq.com/' + key + '.send'
    dic = {
        'text': title,
        'desp': string
    }
    requests.get(url, params=dic)

    return title + '：已发送至微信'


class GetCourse:
    def __init__(self, headers: dict, stdcode, batchcode):
        self.headers = headers
        self.stdcode = stdcode
        self.batchcode = batchcode

        # self.flag = 0
        # self.cookies = {
        #     '_WEU': '',
        #     'JSESSIONID': '',
        #     'route': ['', '', ''],
        # }

    def judge(self, course_name, teacher, key='', kind='素选'):
        # 人数未满才返回classid
        classtype = "XGXK"
        if kind == '素选':
            kind = 'publicCourse.do'
        elif kind == '主修':
            kind = 'programCourse.do'
            classtype = "FANKC"
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
                    setcookie = r.headers['set-cookie']
                except KeyError:
                    setcookie = ''
                if setcookie:
                    print(f'[set-cookie]: {setcookie}')
                    update = re.search(r'_WEU=.+?; ', setcookie).group(0)
                    self.headers['cookie'] = re.sub(r'_WEU=.+?; ', update, self.headers['cookie'])

                    print(f'[current cookie]: {self.headers["cookie"]}')

                temp = r.text.replace('null', 'None').replace('false', 'False').replace('true', 'True')
                res = ast.literal_eval(temp)
                if kind == 'publicCourse.do':
                    datalist = res['dataList']
                elif kind == 'programCourse.do':
                    datalist = res['dataList'][0]['tcList']
                else:
                    print('kind参数错误，请重新输入')
                    return False

                if res['msg'] == '未查询到登录信息':
                    print('登录失效，请重新登录')
                    to_wechat(key, '登录失效，请重新登录', '线程结束')
                    return False

                for course in datalist:
                    remain = int(course['classCapacity']) - int(course['numberOfFirstVolunteer'])
                    if remain and course['teacherName'] == teacher:
                        string = f'{course_name} {teacher}：{remain}人空缺'
                        print(string)
                        return to_wechat(key, f'{course_name} 余课提醒', string)
                        # return course_name, teacher, classtype, course['teachingClassID']

                print(f'{course_name} {teacher}：人数已满 {time.ctime()}')
                time.sleep(15)

            except HTTPError or SyntaxError:
                print('登录失效，请重新登录')
                to_wechat(key, '登录失效，请重新登录', '线程结束')
                return False

    def __judge_datastruct(self, course, classtype) -> dict:
        data = {
            "data": {
                "studentCode": self.stdcode,
                "campus": "05",
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

    # def update_cookie(self, string):
    #     if '_WEU' in string:
    #         self.cookies['_WEU'] = re.search(r'_WEU=(.+?)[,;]', string).group(1)
    #     if 'JSESSIONID' in string:
    #         self.cookies['JSESSIONID'] = re.search(r'JSESSIONID=(.+?)[,;]', string).group(1)
    #     if 'route' in string:
    #         routes = re.findall(r'route=(.+?)[,;]', string)
    #         for route in routes:
    #             self.cookies['route'][self.flag] = route
    #             self.flag = (self.flag + 1) % 3
    #
    #     current = ''
    #     for key, value in self.cookies.items():
    #         if isinstance(value, list):
    #             for s in value:
    #                 current += key + '=' + s + '; '
    #         else:
    #             current += key + '=' + value + '; '
    #
    #     print(self.flag)
    #     return current


if __name__ == '__main__':
    Headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/80.0.3987.116 Safari/537.36',
        'cookie': '',
        'token': ''
    }
    stdCode = ''
    batchCode = ''

    test = GetCourse(Headers, stdCode, batchCode)
    # print(test.judge('初级泰语', '李娟'))
