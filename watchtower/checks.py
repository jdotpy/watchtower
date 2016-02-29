import random
import requests

class BaseCheck():
    STATUS_OK = 1
    STATUS_WARNING = 2
    STATUS_ERROR = 3
    STATUSES = {
        STATUS_OK: "Ok",
        STATUS_WARNING: "Warning",
        STATUS_ERROR: "Error"
    }

    @classmethod
    def get_status_label(cls, status):
        return cls.STATUSES.get(status, '<Unknown>')

    def __init__(self, name, title=None, options=None):
        self.name = name
        self.title = title or name
        self.options = options or {}

    def check(self):
        return self.STATUS_OK

class RandomCheck():
    def check(self):
        return random.choice(self.STATUSES.values())

class SimpleWeb(BaseCheck):
    def check(self):
        response = requests.get(self.options['url'])
        if response.status_code == 200:
            return self.STATUS_OK
        else:
            return self.STATUS_ERROR
