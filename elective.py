
import json
import requests
import unittest


class WebSession:
    def __init__(self):
        self.cookies = requests.cookies.RequestsCookieJar()
        self.user_agent = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
            'AppleWebKit/537.36 (KHTML, like Gecko) ' +
            'Chrome/72.0.3626.109 Safari/537.36')
        return

    def __do(self, func, url, kwargs):
        r = func(
            url,
            cookies=self.cookies,
            headers={
                'User-Agent': self.user_agent,
            },
            **kwargs)
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
    pass


class TestElectiveMethods(unittest.TestCase):
    def test_default(self):
        # Read username and password from tokens.json
        f = open('tokens.json', 'r', encoding='utf-8')
        j = json.loads(f.read())
        f.close()
        username = j['username']
        password = j['password']
        s = UserSession(username, password)
        d = s.login()
        print(d)
    pass

unittest.main()
