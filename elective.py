
import base64
import bs4
import json
import openpyxl
import os
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
        self.cnt_expected = 0  # 修读人数 [*]
        self.cnt_selected = 0  # 选上人数 [*]
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


class ClassDatabase:
    """CSV database manager."""
    def __init__(self):
        self.array = []
        self.index = {}
        self.patterns = [
            ('class_name', '教学班名称', '%s', str),
            ('class_id', '教学班ID', '%s', str),
            ('selected', '已选', '%d', bool),
            ('wish', '志愿', '%d', bool),
            ('course_name', '课程名称', '%s', str),
            ('course_type', '课程类别', '%s', str),
            ('credits', '学分', '%d', int),
            ('cnt_expected', '修读人数', '%d', int),
            ('cnt_selected', '选上人数', '%d', int),
            ('cnt_chosen', '已选人数', '%d', int),
            ('at_nansyuu', '上课周次', '(%d, %d)', lambda _:
                tuple(map(int, re.findall(r'\((\d+), (\d+)\)', _)[0]))),
            ('at_nanyoubi', '上课曜日', '%d', int),
            ('at_nanme', '上课节次', '(%d, %d)', lambda _:
                tuple(map(int, re.findall(r'\((\d+), (\d+)\)', _)[0]))),
            ('at_loc', '上课地点', '%s', str),
            ('teacher', '主讲教师', '%s', str),
            ('teacher_id', '教师ID', '%s', str),
            ('test_mode', '考核方式', '%s', str),
            ('filter_mode', '筛选方式', '%s', str),
            ('foreign', '外语限修课', '%d', bool),
            ('query_params', '查询参数', lambda _: json.dumps(_), lambda _:
                json.loads(_)),
            ('update_time', '更新时间', '%f', float),
        ]
        return

    def add(self, clz):
        if clz.class_id in self.index:
            self.array[self.index[clz.class_id]] = clz
        else:
            self.array.append(clz)
            self.index[clz.class_id] = len(self.array) - 1
        return

    def get(self, class_id):
        if class_id not in self.index:
            raise KeyError(class_id)
        return self.array[self.index[class_id]]

    def load(self, filename):
        wb = openpyxl.load_workbook(filename)
        ws = wb.active
        first_row = True
        for row in ws.rows:
            if first_row:
                first_row = False
                continue
            # Is data row, do not skip
            td = list(str(i.value) for i in row)
            clz = ElectiveClass()
            for i in range(0, len(self.patterns)):
                val = self.patterns[i][3](td[i])
                setattr(clz, self.patterns[i][0], val)
            self.add(clz)
        return

    def save(self, filename):
        wb = openpyxl.Workbook()
        ws = wb.active
        thead = list(i[1] for i in self.patterns)
        ws.append(thead)
        for clz in self.array:
            row = []
            for attr in self.patterns:
                val = getattr(clz, attr[0])
                rule = attr[2]
                if type(rule) == str:
                    val = rule % val
                else:
                    val = rule(val)
                row.append(val)
            ws.append(row)
        wb.save(filename)
        return
    pass


class InteractiveLogger:
    def __init__(self):
        self.log = []
        return

    def clear_screen(self):
        os.system('cls')
        return

    def add(self, data):
        n = 79 - 16
        lines = [data[i:i+n] for i in range(0, len(data), n)]
        tm = time.time()
        _, _, _, h, m, s, _, _, _ = tuple(time.localtime(tm))
        tms = ' [%.2d:%.2d:%.2d.%.3d] ' % (h, m, s, (tm - int(tm)) * 1000)
        lines[0] = tms + lines[0]
        for i in range(1, len(lines)):
            lines[i] = ' ' * 16 + lines[i]
        for line in lines[::-1]:
            self.log.append(line)
        return

    def output(self, cnt):
        lines = self.log[-cnt:][::-1]
        for line in lines:
            print(line)
        return
    pass

logger = InteractiveLogger()


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
        # Request
        r = func(
            url,
            cookies=self.cookies,
            headers={
                'User-Agent': self.user_agent,
            },
            **kwargs)
        self.last_request_time = time.time()
        # Update cookies jar
        self.cookies.update(r.cookies)
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
            c.credits = int(td[5].text.strip())
            c.cnt_expected = int(td[6].text.strip())
            c.cnt_selected = int(td[7].text.strip())
            c.cnt_chosen = int(td[8].text.strip())
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
                int, re.findall(r'第0*(\d+)～0*(\d+)节', at_time[1])[0]))
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
            try:
                return self.parse_page(r.text)
            except Exception as err:
                print(r.text)
                raise Exception()
        return r.text

    def get_data_recursive(self, db, params):
        level, data = self.get_page(params, parse=True)
        if level == 0 or level == 1:
            for title in data:
                print('Entering menu "%s".' % title)
                self.get_data_recursive(db, data[title])
        elif level == 2:
            for clz in data:
                clz.query_params = params
                db.add(clz)
        return

    def update_data(self, classes):
        methods = set()
        for clz in classes:
            methods.add(clz.query_params)
        for param in methods:
            level, data = self.get_page(param, parse=True)
            if level != 2:
                continue
            for clz in data:
                if clz.class_id not in classes:
                    continue
                clz.query_params = param
                classes[clz.class_id] = clz
            pass
        return classes

    def get_data(self, db):
        return self.get_data_recursive(db, {'method': 'listKclb'})
    pass


def login_json(filename):
    """Login from token (json) data, returns session and wished class ids."""
    f = open(filename, 'r', encoding='utf-8')
    j = json.loads(f.read())
    f.close()
    username = j['username']
    password = j['password']
    cookies = j['cookies']
    update_classes = j['select']
    s = UserSession(username, password)
    # Lazy load cookie data
    if cookies != "":
        logger.add('以前のトークンを見つけ、それを再利用しました。')
        s.session.load_cookies(cookies)
        logger.add('トークンのロードが完成しました。')
    else:
        logger.add('トークンが見つかりません、ログインしています')
        if not s.login():
            logger.add('登録に失敗しました、再試行不可能です。')
            return None, []
        f = open(filename, 'w', encoding='utf-8')
        j = json.dumps({
            'username': username,
            'password': password,
            'cookies': s.session.dump_cookies(),
            'select': update_classes
        }, indent=4)
        f.write(j)
        f.close()
    logger.add('登録に成功しました。')
    return s, update_classes


def classes_monitor(token_filename, db_filename):
    logger.add('インターフェースがロード中...')
    session, clz_list = login_json(token_filename)
    logger.add('データベースがロード中...')
    db = ClassDatabase()
    db.load(db_filename)
    logger.add('データベースのロードが完成しました。')
    logger.add('インターフェースのロードが完成しました。')
    classes = {}
    # Select known classes from db
    for clz in clz_list:
        if clz in db.index:
            classes[clz] = db.get(clz)

    def print_thread(classes):
        for _ in range(0, 60*3):
            logger.clear_screen()
            tm = time.time()
            for cid in classes:
                clz = classes[cid]
                s = (('[OK]' if clz.selected else '....') + ' %s (%d/%d)' %
                     (clz.class_name, clz.cnt_selected, clz.cnt_expected) +
                     ' | Updated %.2fs ago' % (tm - clz.update_time))
                print(s)
            print('-' * 79)
            logger.output(15 - len(classes))
            time.sleep(0.016)
        return
    print_thread(classes)
    return


class TestElectiveMethods(unittest.TestCase):
    def test_download(self):
        classes_monitor('tokens.json', 't.xlsx')
        return
        # Prepare to download page
        db = ClassDatabase()
        # db.load('t.xlsx')
        s.get_data(db)
        db.save('t.xlsx')
    pass

unittest.main()
