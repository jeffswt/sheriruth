
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
