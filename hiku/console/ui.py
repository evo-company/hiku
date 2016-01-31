import pkgutil

from ..compat import text_type
from ..writers.json import dumps
from ..readers.simple import read


ERROR_CODES = {
    400: (
        'Bad Request',
        ('The browser (or proxy) sent a request that this server could '
         'not understand.'),
    )
}


def error_response(code, start_response):
    description, message = ERROR_CODES[code]
    start_response('{} {}'.format(code, description), [
        ('Content-Type', 'text/plain'),
        ('Content-Length', text_type(len(message))),
    ])
    return [message]


class ConsoleResponse(object):

    def __init__(self):
        self.page = pkgutil.get_data('hiku.console', 'assets/console.html')

    def __call__(self, environ, start_response):
        start_response('200 OK', [
            ('Content-Type', 'text/html'),
            ('Content-Length', text_type(len(self.page))),
        ])
        return [self.page]


class QueryResponse(object):

    def __init__(self, engine, root):
        self.engine = engine
        self.root = root

    def __call__(self, environ, start_response):
        if 'CONTENT_LENGTH' not in environ:
            return error_response(400, start_response)
        pattern = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
        query = read(pattern.decode('utf-8'))
        result = self.engine.execute(self.root, query)
        result_data = dumps(result).encode('utf-8')
        start_response('200 OK', [
            ('Content-Type', 'application/json'),
            ('Content-Length', text_type(len(result_data))),
        ])
        return [result_data]
