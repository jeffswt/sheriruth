
import base64
import bs4
import json
import openpyxl
import optparse
import os
import pickle
import re
import requests
import sys
import threading
import time
import traceback
import urllib
import urllib.parse


consts = {
    'version': '[Present] 7',
    'request-delay': 0.3,
    'refresh-rate': 1.8,
    'save-rate': 6.0,
}


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
        self.post_params = {}  # Params used to select course
        self.update_time = 0  # Time updated
        return

    def __repr__(self):
        ls = ['class_name', 'class_id', 'selected', 'wish', 'course_name',
              'course_type', 'credits', 'cnt_expected', 'cnt_selected',
              'cnt_chosen', 'at_nansyuu', 'at_nanyoubi', 'at_nanme', 'at_loc',
              'teacher', 'teacher_id', 'test_mode', 'filter_mode', 'foreign',
              'query_params', 'post_params', 'update_time']
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
            ('selected', '已选', '%d', lambda _: bool(int(_))),
            ('wish', '志愿', '%d', lambda _: bool(int(_))),
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
            ('foreign', '外语限修课', '%d', lambda _: bool(int(_))),
            ('query_params', '查询参数', lambda _: json.dumps(_), lambda _:
                json.loads(_)),
            ('post_params', '提交参数', lambda _: json.dumps(_), lambda _:
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
        wb = openpyxl.load_workbook(filename, read_only=True)
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
        while True:
            try:
                wb.save(filename)
            except Exception:
                time.sleep(0.5)
                logger.add('ファイルの保存に失敗します。')
            break
        return
    pass


class InteractiveLogger:
    def __init__(self):
        self.log = []
        self.is_alive = True
        return

    def clear_screen(self):
        os.system('cls')
        return

    def alive(self):
        return self.is_alive

    def kill(self):
        self.is_alive = False
        return

    def add(self, data):
        n = 79 - 16
        lines = sum([[line[i:i+n] for i in range(0, len(line), n)]
                     for line in data.split('\n')], [])
        tm = time.time()
        _, _, _, h, m, s, _, _, _ = tuple(time.localtime(tm))
        tms = ' [%.2d:%.2d:%.2d.%.3d] ' % (h, m, s, (tm - int(tm)) * 1000)
        lines[0] = tms + lines[0]
        for i in range(1, len(lines)):
            lines[i] = ' ' * 16 + lines[i]
        for line in lines[::-1]:
            self.log.append(line)
        return

    def traceback(self, exc_info):
        self.add(''.join(traceback.format_exception(*exc_info)))
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
        req_delay = consts['request-delay']
        if t < self.last_request_time + req_delay:
            time.sleep(self.last_request_time + req_delay - t)
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
        self.login_fail_count = 0
        return

    def login(self):
        if self.login_fail_count > 3:
            logger.add('登録失敗が多すぎました、続行できません。')
            time.sleep(1.0)
            return False
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
        if len(r.text) == 0:
            return True
        if r.text.startswith(fail_marker):
            self.login_fail_count += 1
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
        # Parse post params
        _1 = dom.find('input', id='method')
        _2 = _1.next_sibling
        post_params = {}
        while type(_2) != type(_1) or _2.name != 'table':
            if _2.name == 'input':
                post_params[_2['name']] = _2['value']
            _2 = _2.next_sibling
        # Parse classes
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
            c.post_params = dict(post_params)
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

    def parse_page(self, params, page):
        """Parse page, returns page level and parsed data."""
        level = self.detect_page_level(page)
        result = [
            self.parse_level_0_page,
            self.parse_level_1_page,
            self.parse_level_2_page,
            lambda _: _,
        ][level](page)
        # Patch query_params
        if level == 2:
            for clz in result:
                clz.query_params = dict(params)
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
        logger.add('「%s」から取得したページ' % json.dumps(params))
        if parse:
            try:
                return self.parse_page(params, r.text)
            except Exception as err:
                if not self.login():
                    logger.add('レンダー失敗しました。')
                    logger.kill()
                    raise Exception()
                return self.get_page(params, parse=parse)
        return r.text

    def get_data_recursive(self, db, params):
        level, data = self.get_page(params, parse=True)
        if level == 0 or level == 1:
            for title in data:
                logger.add('メニュー「%s」に入ります' % title)
                self.get_data_recursive(db, data[title])
        elif level == 2:
            for clz in data:
                db.add(clz)
        return

    def update_data(self, classes):
        logger.add('新しい課程状態を取得中...')
        methods = set()
        for cid in classes:
            methods.add(json.dumps(classes[cid].query_params))
        for param_j in methods:
            param = json.loads(param_j)
            level, data = self.get_page(param, parse=True)
            if level != 2:
                continue
            for clz in data:
                if clz.class_id not in classes:
                    continue
                classes[clz.class_id] = clz
            pass
        logger.add('新しい課程状態が取得されました。')
        return classes

    def get_data(self, db):
        return self.get_data_recursive(db, {'method': 'listKclb'})

    def select_class(self, clz):
        scheme = 'http'
        netloc = 'app.ruc.edu.cn'
        path = '/idc/education/selectcourses/studentselectcourse/'\
               'StudentSelectCourseAction.do'
        query = dict(clz.post_params)
        query.update({
            'method': 'selectCourses',
            'wish': '1',
            'condition_kclb': '',
            'rowid': clz.class_id,
            'pageNo': '1',
            'pageSize': '50',
        })
        query = urllib.parse.urlencode(query)
        fragment = ''
        url = urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))
        r = self.session.post(url)
        # Process error cases
        if r.status_code != 200:
            logger.add('課程「%s」選択中に HTTP 錯誤が発生します。' %
                       r.class_name)
            return False
        if '选课成功' in r.text:
            logger.add('課程「%s」の選択が成功しました。' % clz.class_name)
            r.selected = True
            return True
        err_cnt = re.findall(r'/idc/images/error/', r.text)
        # if len(err_cnt) >= 8:  # 10 actually
        logger.add('サーバーは課程「%s」の選択を拒否します。' %
                   clz.class_name)
        return False
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
    if not session:
        return
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

    def print_worker(classes):
        while logger.alive():
            logger.clear_screen()
            tm = time.time()
            for cid in classes:
                clz = classes[cid]
                s = (('[OK]' if clz.selected else '....') + ' %s (%d/%d)' %
                     (clz.class_name, clz.cnt_selected, clz.cnt_expected) +
                     ' | Updated %.2fs ago' % (tm - clz.update_time))
                print(s)
            print('-' * 79)
            logger.output(19 - 1 - len(classes))
            time.sleep(0.1)
        return

    def update_worker(classes, session):
        has_no_remain_cnt = 0
        while logger.alive():
            try:
                time.sleep(consts['refresh-rate'])
                session.update_data(classes)
                # Check if class available
                has_remaining = False
                for cid in classes:
                    clz = classes[cid]
                    if clz.selected:
                        continue
                    has_remaining = True
                    if clz.cnt_selected >= clz.cnt_chosen:
                        continue
                    logger.add('課程「%s」は選択することが可能である。' %
                               clz.class_name)
                    session.select_class(clz)
                if not has_remaining:
                    has_no_remain_cnt += 1
                if has_no_remain_cnt > 4:
                    logger.add('全部の目標は達成されました。')
                    time.sleep(1.0)
                    logger.kill()
            except Exception as err:
                logger.traceback(sys.exc_info())
            except BaseException:
                logger.kill()
        return

    def save_worker(db, db_filename):
        while logger.alive():
            time.sleep(consts['save-rate'])
            try:
                db.save(db_filename)
                logger.add('新しい変更がテーブルに保存されました。')
            except Exception as err:
                logger.traceback(sys.exc_info())
            except BaseException:
                logger.kill()
        return
    # Define threads
    print_thread = threading.Thread(target=print_worker, args=[classes])
    update_thread = threading.Thread(target=update_worker,
                                     args=[classes, session])
    save_thread = threading.Thread(target=save_worker, args=[db, db_filename])
    # Start threads
    print_thread.start()
    update_thread.start()
    save_thread.start()
    # Sleep for a while or listen for keyboard interrupt
    try:
        while logger.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.kill()
    # Join threads
    logger.kill()
    print_thread.join()
    update_thread.join()
    save_thread.join()
    return


def update_class_database(token_filename, db_filename):
    logger.add('インターフェースがロード中...')
    session, clz_list = login_json(token_filename)
    if not session:
        return
    logger.add('インターフェースのロードが完成しました。')

    def print_worker():
        while logger.alive():
            logger.clear_screen()
            logger.output(19)
            time.sleep(0.1)
        return
    print_thread = threading.Thread(target=print_worker, args=[])
    print_thread.start()
    # Main sequence
    try:
        db = ClassDatabase()
        session.get_data(db)
        db.save(db_filename)
        logger.add('課程がテーブルに保存されました。')
    except KeyboardInterrupt:
        logger.kill()
    # Terminate
    time.sleep(1.0)
    logger.kill()
    print_thread.join()
    return


def main():
    opts = optparse.OptionParser(usage='sheriruth (-r|-s) [OPTIONS]',
                                 version=consts['version'])
    opts.add_option(
        '-r', '--reload', dest='reload', action='store_true', default=False,
        help='(Re)Load course database')
    opts.add_option(
        '-s', '--start', dest='start', action='store_true', default=False,
        help='Begin procedure')
    opts.add_option(
        '-t', '--token-file', dest='token_fn', type='string',
        default='token.json',
        help='JSON file in which user information is stored')
    opts.add_option(
        '-d', '--database-file', dest='database_fn', type='string',
        default='database.xlsx',
        help='XLSX file in which course database is stored')
    opts.add_option(
        '--request-delay', dest='request_delay', type='float',
        default=consts['request-delay'],
        help='Minimum delay (%.1f) seconds between requests' %
        consts['request-delay'])
    opts.add_option(
        '--refresh-rate', dest='refresh_rate', type='float',
        default=consts['refresh-rate'],
        help='Refresh course status every (%.1f) seconds' %
        consts['refresh-rate'])
    opts.add_option(
        '--save-rate', dest='save_rate', type='float',
        default=consts['save-rate'],
        help='Update database every (%.1f) seconds' %
        consts['save-rate'])
    commands, args = opts.parse_args()
    # Apply settings
    consts['request-delay'] = commands.request_delay
    consts['refresh-rate'] = commands.refresh_rate
    consts['save-rate'] = commands.save_rate
    # Check files
    token_filename = commands.token_fn
    db_filename = commands.database_fn
    missing_files = False
    for _ in {token_filename, db_filename}:
        if _ == db_filename and commands.reload:
            continue
        if not os.path.exists(_):
            print('sheriruth: error: %s: no such file or directory' % _)
            missing_files = True
    if missing_files:
        print('sheriruth: fatal error: missing files')
        print('procedure terminated.')
        return
    # Check mode
    if commands.reload:
        update_class_database(token_filename, db_filename)
    if commands.start:
        classes_monitor(token_filename, db_filename)
    if not commands.reload and not commands.start:
        print('sheriruth: fatal error: nothing to do')
        print('sheriruth: info: try "-h" for help')
        print('procedure terminated.')
    return

if __name__ == "__main__":
    main()
