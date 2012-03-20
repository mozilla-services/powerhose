import logging

from gevent import monkey
import gevent_zeromq

monkey.patch_all()
gevent_zeromq.monkey_patch()

logger = logging.getLogger('powerhose')
