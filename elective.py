
import base64
import json
import pickle
import requests
import time
import unittest
import urllib
import urllib.parse


class ElectiveClass:
    def __init__(self):
        self.class_name = '复变函数（退学班）'  # 教学班名称
        self.selected = False  # 已选
        self.wish = False  # 志愿
        self.course_name = '复变函数'  # 课程名称
        self.course_type = '数学'  # 课程类别
        self.credits = 6  # 学分
        self.cnt_expected = 0  # 修读人数
        self.cnt_selected = 0  # 选上人数
        self.cnt_chosen = 0  # 已选人数
        self.at_nansyuu = (1, 18)  # 上课信息：第x到x周
        self.at_nanyoubi = 2  # 上课信息：星期x
        self.at_nanme = (7, 8)  # 上课信息：第x节
        self.teacher = '裴礼文'  # 主讲教师
        self.test_mode = '考试'  # 考核方式
        self.filter_mode = '靠运气'  # 筛选方式
        self.foreign = False  # 外语限修课
        return
    pass


class WebSession:
    def __init__(self):
        self.cookies = requests.cookies.RequestsCookieJar()
        self.user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
            'AppleWebKit/537.36 (KHTML, like Gecko) ' +
            'Chrome/72.0.3626.109 Safari/537.36')
        self.request_delay = 0.5
        self.last_request_time = 0
        return

    def dump_cookies(self):
        s = base64.b64encode(pickle.dumps(self.cookies))
        return s.decode('utf-8', 'ignore')

    def load_cookies(self, s):
        s = s.encode('utf-8', 'ignore')
        self.cookies = pickle.loads(base64.b64decode(s))
        return

    def __do(self, func, url, kwargs):
        # Ensure spider's speed is slow enough
        t = time.time()
        if t < self.last_request_time + self.request_delay:
            time.sleep(self.last_request_time + self.request_delay - t)
            self.last_request_time = t
        # Request
        r = func(
            url,
            cookies=self.cookies,
            headers={
                'User-Agent': self.user_agent,
            },
            **kwargs)
        # Update cookies jar
        self.cookies = r.cookies
        return r

    def get(self, url, **kwargs):
        return self.__do(requests.get, url, kwargs)

    def post(self, url, **kwargs):
        return self.__do(requests.post, url, kwargs)
    pass


class UserSession:
    """Manages user and related information."""
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = WebSession()
        return

    def login(self):
        url = 'https://v.ruc.edu.cn/auth/login'
        payload = {
            "username": "ruc:%s" % self.username,
            "password": "%s" % self.password,
            "remember_me": "false",
            "redirect_uri": "",
            "twofactor_password": "",
            "twofactor_recovery": ""
        }
        old_cookies = self.session.cookies
        r = self.session.post(
            url,
            data=json.dumps(payload),
            allow_redirects=False)
        fail_marker = '{"error":"'
        if len(old_cookies) != len(self.session.cookies):
            return True
        if r.text.startswith(fail_marker):
            return False
        return False

    def parse_level_0_page(self, page):
        return []

    def parse_level_1_page(self, page):
        return []

    def parse_level_2_page(self, page):
        return []

    def get_page(self, params):
        scheme = 'http'
        netloc = 'app.ruc.edu.cn'
        path = '/idc/education/selectcourses/studentselectcourse/'\
               'StudentSelectCourseAction.do'
        query = {
            'isNeedInitSQL': 'true',
        }
        query.update(params)
        query = urllib.parse.urlencode(query)
        fragment = ''
        url = urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))
        r = self.session.get(url)
        return r.text
    pass


class TestElectiveMethods(unittest.TestCase):
    def download_page(self):
        # Read username, password and cookies from tokens.json
        f = open('tokens.json', 'r', encoding='utf-8')
        j = json.loads(f.read())
        f.close()
        username = j['username']
        password = j['password']
        cookies = j['cookies']
        s = UserSession(username, password)
        # Lazy load cookie data
        if cookies != "":
            s.session.load_cookies(cookies)
        else:
            d = s.login()
            f = open('tokens.json', 'w', encoding='utf-8')
            j = json.dumps({
                'username': username,
                'password': password,
                'cookies': s.session.dump_cookies()
            }, indent=4)
            f.write(j)
            f.close()
        # Prepare to download page
        p = s.get_page({'method': 'listKclb'})
        open('a.html', 'w', encoding='utf-8').write(p)

    def test_parser(self):
        return
    pass

unittest.main()
