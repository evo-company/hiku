import json
import string
import pkgutil

from ..result import denormalize
from ..typedef.kinko import dumps as dumps_typedef
from ..readers.simple import read


ERROR_CODES = {
    400: (
        'Bad Request',
        ('The browser (or proxy) sent a request that this server could '
         'not understand.'),
    ),
    404: (
        'Not Found',
        ('The requested URL was not found on the server.  '
         'If you entered the URL manually please check your spelling and '
         'try again.'),
    ),
    405: (
        'Method Not Allowed',
        'The method is not allowed for the requested URL.',
    ),
}


def _decode(b, charset='utf-8'):
    return b.decode(charset)


def _encode(s, charset='utf-8'):
    return s.encode(charset)


class ConsoleApplication(object):
    _urls = {
        'index_url': '/',
        'docs_url': '/docs',
    }

    def __init__(self, root, engine):
        self.root = root
        self.engine = engine
        self._console_html = string.Template(_decode(
            pkgutil.get_data('hiku.console', 'assets/console.html')
        ))
        self._docs_content = dumps_typedef(root)

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO'] or '/'

        if path_info == self._urls['index_url']:
            if environ['REQUEST_METHOD'] == 'GET':
                return self._index_get(environ, start_response)
            elif environ['REQUEST_METHOD'] == 'POST':
                return self._index_post(environ, start_response)
            else:
                return self._error(405, start_response)

        elif path_info == self._urls['docs_url']:
            if environ['REQUEST_METHOD'] == 'GET':
                return self._docs_get(environ, start_response)
            else:
                return self._error(405, start_response)

        else:
            return self._error(404, start_response)

    def _urls_map(self, environ):
        script_name = environ.get('SCRIPT_NAME', '').rstrip('/')
        return {name: '{}{}'.format(script_name, path)
                for name, path in self._urls.items()}

    def _error(self, code, start_response, message=None):
        description, standard_message = ERROR_CODES[code]
        message = message or standard_message
        content = _encode(message + '\n')
        start_response('{} {}'.format(code, description), [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(content))),
        ])
        return [content]

    def _index_get(self, environ, start_response):
        content = _encode(
            self._console_html.safe_substitute(
                **self._urls_map(environ)
            )
        )
        start_response('200 OK', [
            ('Content-Type', 'text/html'),
            ('Content-Length', str(len(content))),
        ])
        return [content]

    def _index_post(self, environ, start_response):
        limit = max(0, int(environ.get('CONTENT_LENGTH') or 0))
        if limit > 2 ** 20:  # 1MB
            return self._error(400, start_response, 'Payload is too big')

        pattern = environ['wsgi.input'].read(limit)
        query = read(_decode(pattern))
        result = self.engine.execute(self.root, query)
        result_data = _encode(json.dumps(denormalize(self.root, result, query)))
        start_response('200 OK', [
            ('Content-Type', 'application/json'),
            ('Content-Length', str(len(result_data))),
        ])
        return [result_data]

    def _docs_get(self, environ, start_response):
        content = _encode(self._docs_content)
        start_response('200 OK', [
            ('Content-Length', str(len(content))),
        ])
        return [content]
