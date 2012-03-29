# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
""" Job class.
"""


class Job(object):
    """A Job is just a container that's passed into the wire.

    A job is composed of headers and raw data, and offers serialization.

    Options:

    - **data**: the raw string data (default: '')
    - **headers**: a mapping of headers (default: None)
    """
    def __init__(self, data='', headers=None):
        self.data = data
        self.headers = {}

        if headers is not None:
            for name, value in headers.items():
                self.add_header(name, value)

    def add_header(self, name, value):
        """Adds a header.

        Options:

        - **name**: header name
        - **value**: value

        Both values should be strings. If the header already exists
        it's overwritten.
        """
        name = name.replace(':', '\:')
        value = value.replace(':', '\:')
        self.headers[name] = value

    def serialize(self):
        """Serializes the job.

        The output can be sent over a wire. A serialized job
        can be read with a cursor with no specific preprocessing.
        """
        if len(self.headers) == 0:
            headers = ['NONE']
        else:
            headers = ['%s:%s' % (name, value) for name, value in
                       self.headers.items()]

        headers = '::'.join(headers)
        return headers + ':::' + self.data

    @classmethod
    def load_from_string(cls, data):
        """Loads a job from a serialized string and return a Job instance.

        Options:

        - **data** : serialized string.
        """
        if ':::' not in data:
            raise ValueError(data)
        headers, data = data.split(':::', 1)
        res = {}
        for header in headers.split('::'):
            if header == 'NONE':
                break
            header_data = header.strip().split(':')
            if len(header_data) != 2:
                raise ValueError(header_data)
            res[header_data[0]] = header_data[1]

        return cls(data, res)
