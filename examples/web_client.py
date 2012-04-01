from wsgiref.simple_server import make_server
import json
import sys

from powerhose.client import Client
from powerhose.job import Job


client = Client()


def application(environ, start_response):
    sys.stdout.write('.')
    sys.stdout.flush()
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    data = {}
    for key, value in environ.items():
        if key.startswith('wsgi.') or key.startswith('gunicorn.'):
            continue
        data[key] = value

    job = Job(json.dumps(data))
    try:
        return client.execute(job)
    finally:
        sys.stdout.write('+')
        sys.stdout.flush()


if __name__ == '__main__':
    httpd = make_server('', 8000, application)
    print "Listening on port 8000...."
    httpd.serve_forever()
