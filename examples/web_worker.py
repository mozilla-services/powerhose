import json
import pprint
import StringIO


page = """\
<html>
  <body>
    <h1>Hello</h1>
    <pre>%s
    </pre>
  </body>
</html>
"""


def hello(job):
    environ = json.loads(job.data)
    printed = StringIO.StringIO()
    pprint.pprint(environ, stream=printed)
    printed.seek(0)
    return page % printed.read()
