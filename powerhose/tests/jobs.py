import time


def fail(job):
    raise ValueError(job.data)


def timeout(job):
    time.sleep(5.)


def success(job):
    return job.data
