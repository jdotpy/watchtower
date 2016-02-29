#!/usr/bin/env python 
from watchtower.web import WebApp, Watchtower
from werkzeug.serving import run_simple

import sys

if __name__ == "__main__":
    debug = '--debug' in sys.argv
    run_simple('0.0.0.0', 5000, WebApp(Watchtower()), use_debugger=True)
