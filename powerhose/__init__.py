import logging
from gevent import monkey
from powerhose.jobrunner import JobRunner  # NOQA


monkey.patch_all()
logger = logging.getLogger('powerhose')
