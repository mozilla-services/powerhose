

class Job(object):
    """A Job is composed of headers and raw data"""
    def __init__(self, data='', headers=None):
        self.data = data
        self.headers = {}

        if headers is not None:
            for name, value in headers.items():
                self.add_header(name, value)

    def add_header(self, name, value):
        name = name.replace(':', '\:')
        value = value.replace(':', '\:')
        self.headers[name] = value

    def serialize(self):
        if len(self.headers) == 0:
            headers = ['NONE']
        else:
            headers = ['%s:%s' (name, value) for name, value in
                        self.headers.items()]

        headers = '::'.join(headers)
        return headers + ':::' + self.data

    @classmethod
    def load_from_string(cls, data):
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
