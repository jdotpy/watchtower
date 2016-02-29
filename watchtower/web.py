from quickconfig import Configuration
from jinja2 import Template
from jinja2 import Environment, PackageLoader, FileSystemLoader
from werkzeug.wrappers import Request, Response
from werkzeug.wsgi import SharedDataMiddleware
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
        self.checks = self._parse_checks(self.settings.get('checks', {}))
        print('\tChecks:')
        for check in self.checks:
            print('\t\t{}: {}'.format(
                str(check.__class__),
                check.name
            ))

    def _parse_checks(self, checks_config):
        checks = []
        for name, check_info in checks_config.items():
            type_path = check_info['type']
            type_class = import_class(type_path)
            title = check_info.get('title', None)
            options = check_info.get('options', {})
            checks.append(type_class(name, title, options))
        return checks


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
            check_data[check.name] = {
                'title': check.title,
                'summary': summary
            }
        return self.render_template("dashboard.html", {
            'summary_by_check': check_data
        })
