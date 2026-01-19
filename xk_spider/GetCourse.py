import json
import random
import re
import threading
import time

import requests
from requests.exceptions import HTTPError, RequestException

DEFAULT_TIMEOUT = 10
from requests.utils import dict_from_cookiejar



def to_wechat(key, title, string):
    if not key:
        return title + '：未配置微信通知'
    url = 'https://sctapi.ftqq.com/' + key + '.send'
    dic = {
        'text': title,
        'desp': string
    }
    try:
        requests.get(url, params=dic, timeout=DEFAULT_TIMEOUT)
    except RequestException as e:
        print(f"微信通知发送失败: {e}")
        return title + '：发送失败'
    return title + '：已发送至微信'


class GetCourse:
    def __init__(self, headers: dict, stdcode, batchcode, driver, url, path, stdCode, pswd):
        self._cookie_lock = threading.Lock()
        self._running = True
        self.driver = driver
        self.headers = headers
        self.stdcode = stdcode
        self.batchcode = batchcode
        self.url = url
        self.path = path
        self.stdCode = stdCode
        self.pswd = pswd

    def stop(self):
        self._running = False

    def __build_request_headers(self):
        with self._cookie_lock:
            headers = self.headers.copy()
        headers['Referer'] = 'https://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/*default/index.do'
        headers['Origin'] = 'https://xk.ynu.edu.cn'
        headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'
        headers['X-Requested-With'] = 'XMLHttpRequest'
        return headers

    def __build_url(self, endpoint):
        separator = '&' if '?' in endpoint else '?'
        with self._cookie_lock:
            token = self.headers.get('Token', '')
        return f"{endpoint}{separator}token={token}"

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
        url = 'https://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/elective/' + kind

        while self._running:
            try:
                query = self.__judge_datastruct(course_name, classtype)
                request_headers = self.__build_request_headers()
                request_url = self.__build_url(url)
                r = requests.post(request_url, data=query, headers=request_headers, timeout=DEFAULT_TIMEOUT)
                try:
                    r.raise_for_status()
                except HTTPError:
                    print(f"[ERROR] API returned {r.status_code}: {r.text[:200]}")
                    raise

                # 更新 session cookies
                setcookie = r.cookies
                if setcookie:
                    cookies_dict = dict_from_cookiejar(setcookie)
                    setcookie_str = '; '.join([f'{k}={v}' for k, v in cookies_dict.items()])
                    with self._cookie_lock:
                        match_weu = re.search(r'_WEU=.+?; ', setcookie_str)
                        if match_weu:
                            self.headers['cookie'] = re.sub(r'_WEU=.+?; ', match_weu.group(0), self.headers.get('cookie', ''))
                        match_jsessionid = re.search(r'JSESSIONID=.+?; ', setcookie_str)
                        if match_jsessionid:
                            self.headers['cookie'] = re.sub(r'JSESSIONID=.+?; ', match_jsessionid.group(0), self.headers.get('cookie', ''))
                        match_pgv_pvi = re.search(r'pgv_pvi=.+?; ', setcookie_str)
                        if match_pgv_pvi:
                            self.headers['cookie'] = re.sub(r'pgv_pvi=.+?; ', match_pgv_pvi.group(0), self.headers.get('cookie', ''))

                try:
                    res = json.loads(r.text)
                except json.JSONDecodeError:
                    print(f"[ERROR] 无效的 JSON 响应: {r.text[:200]}")
                    return False

                if res.get('msg') == '未查询到登录信息':
                    print('登录失效，请重新登录')
                    return False

                if kind == 'publicCourse.do':
                    datalist = res.get('dataList', [])
                elif kind == 'programCourse.do':
                    data_list = res.get('dataList', [])
                    datalist = data_list[0].get('tcList', []) if data_list else []
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
                sleep_time = random.randint(300, 1000)
                time.sleep(sleep_time)

            except (HTTPError, SyntaxError, RequestException):
                print('登录失效，请重新登录')
                return False

    def post_add(self, classname, teacher, classtype, classid, key):
        query = self.__add_datastruct(classid, classtype)
        request_headers = self.__build_request_headers()
        url = self.__build_url('https://xk.ynu.edu.cn/xsxkapp/sys/xsxkapp/elective/volunteer.do')
        r = requests.post(url, headers=request_headers, data=query, timeout=DEFAULT_TIMEOUT)

        try:
            message = json.loads(r.text).get('msg', '未知结果')
        except json.JSONDecodeError:
            message = f'响应解析失败: {r.text[:100]}'
        title = '抢课结果'
        string = '[' + teacher + ']' + classname + ': ' + message
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
                "campus": "02",  # 01是东陆的校区代码
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
                "campus": "02",  # 01是东陆的校区代码
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
