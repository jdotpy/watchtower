#!/usr/bin/env python 
from watchtower.web import Watchtower
from watchtower.utils import import_class

from datetime import datetime
from pprint import pprint
import time

class Worker():
    def __init__(self, app):
        self.app = app

    def run(self):
        while True:
            print('Doing iteration')
            for check in self.app.checks:
                result = check.check()
                self.app.storage.log_result(check.name, datetime.now(), result)
                print('Check {} got result: {}'.format(
                    check, result
                ))

            time.sleep(3)
            pprint(self.app.storage.summary([check.name for check in self.app.checks]))

if __name__ == "__main__":
    w = Worker(Watchtower())
    w.run()
