#!/usr/bin/env python 
from watchtower.web import Watchtower
from watchtower.utils import import_class

from datetime import datetime
from pprint import pprint
import time
import sys

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

            time.sleep(30)
            pprint(self.app.storage.summary([check.name for check in self.app.checks]))

if __name__ == "__main__":
    app = Watchtower()
    w = Worker(app)
    if '--reset' in sys.argv:
        app.storage.reset()
    w.run()
