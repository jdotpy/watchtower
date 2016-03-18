from quickconfig import Configuration
from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import SharedDataMiddleware
from .checks import BaseCheck
import os

from .utils import import_class

class Watchtower():
    DEFAULT_STORAGE = 'watchtower.storage.memory.MemoryStorage'

    def __init__(self):
        self.settings = Configuration('config.yaml', Configuration.Arg('config'))

        print(' == Watchtower == ')
        print('\tStorage:', self.settings.get('storage.type'))
        self._load_storage(
            self.settings.get('storage.type', self.DEFAULT_STORAGE),
            self.settings.get('storage.options', {}),
        )

        self.alerts = self._parse_alerts(self.settings.get('alerts', {}))
        print('\tAlerts:')
        for alert_name, alert in self.alerts.items():
            print('\t\t{}: {}'.format(
                alert.__class__.__name__,
                alert.name
            ))

        self.checks = self._parse_checks(self.settings.get('checks', []))
        print('\tChecks:')
        for check in self.checks:
            print('\t\t{}: {}'.format(
                check.__class__.__name__,
                check.name
            ))

    def _parse_checks(self, checks_config):
        checks = []
        for check_info in checks_config:
            name = check_info['name']
            title = check_info.get('title', None)

            # Parse Alert
            alerts = []
            alert_names = check_info["alerts"]
            for alert_name in alert_names:
                alert = self.alerts.get(alert_name, None)
                if alert is None:
                    continue
                else:
                    alerts.append(alert)

            # Make Alert of Type
            type_path = check_info['type']
            type_class = import_class(type_path)
            options = check_info.get('options', {})
            checks.append(type_class(name, title, options, alerts))
        return checks

    def _parse_alerts(self, alerts_config):
        alerts = {}
        for name, alert_info in alerts_config.items():
            type_path = alert_info['type']
            type_class = import_class(type_path)
            options = alert_info.get('options', {})
            issue_options = alert_info.get('issues', {})
            alerts[name] = type_class(name, options, issue_options)
        return alerts

    def _load_storage(self, path, settings):
        StorageClass = import_class(path)
        self.storage = StorageClass(**settings)
        return self.storage

class WebApp():
    def __init__(self, app):
        self.app = app
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        self.template_paths = self.app.settings.get('web.template_paths', [])
        self.template_paths.append(self.app_dir + '/templates')
        self.jinja_loader = FileSystemLoader(self.template_paths)
        self.jinja_env = Environment(loader=self.jinja_loader)
        self.static_handler = SharedDataMiddleware(lambda x, y: print('foo'), {
            '/static':  self.app_dir + '/static'
        })

        if self.app.settings.get('web.static', True):
            self.__call__ = SharedDataMiddleware(self.__call__, {
                '/static':  self.app_dir + '/static'
            })

    def __call__(self, environ, start_response):
        request = Request(environ)
        if request.path.startswith('/static'):
            return self.static_handler(environ, start_response)
        else:
            response = self.handle(request)

        return response(environ, start_response)

    def handle(self, request):
        request.app = self
        response = self.dashboard(request)
        if isinstance(response, str):
            response = Response(response)
        response.headers['Content-Type'] = 'text/html'
        return response

    def _base_context(self):
        return {
            'settings': self.app.settings
        }

    def render_template(self, path, extra_context=None):
        context = self._base_context()
        if extra_context:
            context.update(extra_context)

        template = self.jinja_env.get_template(path)
        return template.render(context)

    def dashboard(self, request):
        # Create Results
        checks = self.app.checks
        check_names = [check.name for check in checks]
        checks_summary = self.app.storage.summary(check_names)
        statuses = []
        check_data = {}
        for check in checks:
            summary = checks_summary.get(check.name, None)
            # Add percentage uptime
            success_count = summary['total_success_count'] or 0 
            total_count = summary['total_entry_count'] or 0
            try:
                summary['percent_success'] = (success_count / total_count) * 100
            except ZeroDivisionError:
                summary['percent_success'] = 0

            # Add status message
            last_check = summary.get('last_check', None)
            if last_check:
                last_check['status_text'] = check.get_status_label(last_check['status'])
                statuses.append(last_check['status'])

            check_data[check.name] = {
                'title': check.title,
                'summary': summary
            }
        try:
            overall_status = max(statuses)
        except ValueError:
            overall_status = None
        return self.render_template("dashboard.html", {
            'overall': {
                'status': overall_status,
                'status_text': BaseCheck.get_status_label(overall_status)
            },
            'summary_by_check': check_data
        })
