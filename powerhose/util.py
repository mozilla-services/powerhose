

_SEP = '*****'

# will do better later
def serialize(*seq):
    for part in seq:
        if _SEP in part:
            raise NotImplementedError
    return _SEP.join(seq)


def unserialize(data):
    return data.split(_SEP)
