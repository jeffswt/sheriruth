
import json
import requests


class WebSession:
    def __init__(self):
        self.cookies_jar = requests.cookies.RequestsCookieJar()
        return

    def get(self, url, **kwargs):
        return requests.get(url, cookies=self.cookies_jar, **kwargs)

    def post(self, url, **kwargs):
        return requests.post(url, cookies=self.cookies_jar, **kwargs)
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
            "redirect_uri": "https%3A%2F%2Fv.ruc.edu.cn%2Foauth2%2Fauthorize",
            "twofactor_password": "",
            "twofactor_recovery": ""
        }
        r = self.session.get(url, data=json.dumps(payload))
        return r.text
    pass
