# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import logging

from gevent import monkey
import gevent_zeromq

monkey.patch_all()
gevent_zeromq.monkey_patch()

logger = logging.getLogger('powerhose')
