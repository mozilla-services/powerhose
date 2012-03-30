from powerhose.jobrunner import JobRunner


job = JobRunner()

try:
    job.start()
finally:
    job.stop()
