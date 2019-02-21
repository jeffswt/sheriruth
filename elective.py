
import base64
import bs4
import json
import pickle
import re
import requests
import time
import unittest
import urllib
import urllib.parse


class ElectiveClass:
    def __init__(self):
        self.class_name = '复变函数（退学班）'  # 教学班名称
        self.class_id = ''  # Class ID
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
        self.at_loc = '明学楼,M108'  # 上课信息：地点
        self.teacher = '裴礼文'  # 主讲教师
        self.teacher_id = ''  # Teacher ID
        self.test_mode = '考试'  # 考核方式
        self.filter_mode = '靠运气'  # 筛选方式
        self.foreign = False  # 外语限修课
        self.query_params = {}  # Params required to query class list
        self.update_time = 0  # Time updated
        return

    def __repr__(self):
        ls = ['class_name', 'class_id', 'selected', 'wish', 'course_name',
              'course_type', 'credits', 'cnt_expected', 'cnt_selected',
              'cnt_chosen', 'at_nansyuu', 'at_nanyoubi', 'at_nanme', 'at_loc',
              'teacher', 'teacher_id', 'test_mode', 'filter_mode', 'foreign',
              'query_params', 'update_time']
        p = ', '.join('%s=%s' % (i, repr(getattr(self, i))) for i in ls)
        return 'ElectiveClass(%s)' % p
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
        dom = bs4.BeautifulSoup(page, 'html5lib')
        table = dom.find(id='tb')
        tbody = table.find('tbody')
        tr_s = tbody.find_all('tr')[2:]
        result = {}
        for tr in tr_s:
            td = tr.find_all('td')[0]
            a = td.find('a')
            title = a.text.strip()
            href = re.sub(r'[ \t\r\n]', r'', a['href'])
            _1, _2, _3, query, _5 = urllib.parse.urlsplit(href)
            query = urllib.parse.parse_qs(query)
            query.pop('isNeedInitSQL')
            for i in query:
                query[i] = query[i][0]
            result[title] = query
        return result

    def parse_level_1_page(self, page):
        return self.parse_level_0_page(page)

    def parse_level_2_page(self, page):
        dom = bs4.BeautifulSoup(page, 'html5lib')
        table = dom.find(id='tb')
        tbody = table.find('tbody')
        tr_s = tbody.find_all('tr')[2:]
        result = []
        for tr in tr_s:
            td = tr.find_all('td')[1:]
            c = ElectiveClass()
            c.class_name = td[0].find('a').text.strip()
            c.selected = True if len(td[1].text.strip()) > 0 else False
            c.wish = True if len(td[2].text.strip()) > 0 else False
            c.course_name = td[3].find('a').text.strip()
            c.course_type = td[4].text.strip()
            c.credits = td[5].text.strip()
            c.cnt_expected = td[6].text.strip()
            c.cnt_selected = td[7].text.strip()
            c.cnt_chosen = td[8].text.strip()
            at_time = td[9].find_all('div')[1].text.strip()
            at_time = re.sub(r'[\t\r\n]', r'', at_time).split(' 　')
            c.at_nansyuu = tuple(map(
                int, re.findall(r'第0*(\d+)～0*(\d+)周', at_time[0])[0]))
            _ = re.findall(r'星期(.)', at_time[1])[0]
            _2 = {}
            for _3 in range(0, 7):
                _2['一二三四五六日'[_3]] = _3 + 1
            c.at_nanyoubi = _2[_]
            c.at_nanme = tuple(map(
                re.findall(r'第0*(\d+)～0*(\d+)节', at_time[1])[0]))
            c.at_loc = at_time[2]
            c.teacher = td[11].find('a').text.strip()
            c.test_mode = td[12].text.strip() or '-'
            c.filter_mode = td[13].text.strip() or '-'
            c.class_id = td[17].text.strip()
            c.foreign = True if len(td[18].text.strip()) > 0 else False
            c.teacher_id = td[21].text.strip()
            c.update_time = time.time()
            result.append(c)
        return result

    def detect_page_level(self, page):
        dom = bs4.BeautifulSoup(page, 'html5lib')
        table = dom.find(id='tb')
        tbody = table.find('tbody')
        th = tbody.find_all('tr')[0].find_all('th')
        if len(th) == 5:
            return 0
        if len(th) == 1:
            return 1
        if len(th) > 10:  # == 15
            return 2
        # Unknown type
        return 3

    def parse_page(self, page):
        """Parse page, returns page level and parsed data."""
        level = self.detect_page_level(page)
        result = [
            self.parse_level_0_page,
            self.parse_level_1_page,
            self.parse_level_2_page,
            lambda _: _,
        ][level](page)
        return level, result

    def get_page(self, params, parse=False):
        scheme = 'http'
        netloc = 'app.ruc.edu.cn'
        path = '/idc/education/selectcourses/studentselectcourse/'\
               'StudentSelectCourseAction.do'
        query = {
            'isNeedInitSQL': 'true',
            'pageSize': '50',
        }
        query.update(params)
        query = urllib.parse.urlencode(query)
        fragment = ''
        url = urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))
        r = self.session.get(url)
        if parse:
            return self.parse_page(r.text)
        return r.text
    pass


class TestElectiveMethods(unittest.TestCase):
    def test_download(self):
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
        if False:
            ls = {'method': 'listKclb'}  # Get level 0
            # ls = {'method': 'listJxb', 'kclb': '24'}  # Get level 1
            # ls = {'method': 'listJxb', 'kclb': '02'}  # Get level 2
            p = s.get_page(ls)
            f = open('a.html', 'w', encoding='utf-8')
            f.write(p)
            f.close()
        else:
            f = open('a.html', 'r', encoding='utf-8')
            pg = f.read()
            f.close()
            level, data = s.parse_page(pg)
            print(data)
            # l = s.parse_level_2_page(pg)
            # for _ in l:
            #     print(_)
    pass

unittest.main()
