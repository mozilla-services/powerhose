import logging
from gevent import monkey

monkey.patch_all()
logger = logging.getLogger('powerhose')
