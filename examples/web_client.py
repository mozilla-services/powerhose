from wsgiref.simple_server import make_server
import json
import time

from powerhose.client import Client
from powerhose.job import Job
from powerhose.util import set_logger

set_logger(True)

client = Client()


def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    data = {}
    for key, value in environ.items():
        if key.startswith('wsgi.') or key.startswith('gunicorn.'):
            continue
        data[key] = value

    job = Job(json.dumps(data))

    start = time.time()
    try:
        return client.execute(job)
    finally:
        print('Time : %.4f\n' % (time.time() - start))


if __name__ == '__main__':
    httpd = make_server('', 8000, application)
    print "Listening on port 8000...."
    httpd.serve_forever()
