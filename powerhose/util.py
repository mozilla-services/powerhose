

# will do better later
def serialize(*seq):
    for part in seq:
        if '****' in part:
            raise NotImplementedError
    return '****'.join(seq)


def unserialize(data):
    return data.split('****')
