=========
Powerhose
=========

Powerhose is a single master/ multiple worker zmq lib, that can be used to
push some work to specialized workers.

**WARNING: This is still a work in progress - no stable version has been 
released yet**

**WARNING 2: consider using the https://github.com/traviscline/gevent-zeromq 
fork until it's merged into gevent-zeromq**


Example
=======

Let's create a worker that knows how to calculate a square of a number::

    from powerhose.client.worker import Worker

    endpoint = "ipc:///tmp/master-routing.ipc"
    workpoint = "ipc://worker-routing.ipc"

    def square(*args):
        number = int((args)[0][1])
        return str(number * number)

    worker = Worker(endpoint, workpoint, target=square)
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()


In this example, the Worker is instanciated with:

- the **endpoint**, which is the socket where the master listens
  to workers that want to register.
- the **workpoint**, the socket where the worker gets his jobs.
- the **target**, which is the callable that receives jobs to perform.

The **square** function is getting the value in a string, and has to return
the result as a string that's sent back to the master. Of course, you would
use a real serializer/deserialzer when you operate with more complex data
structures.

The master can look like this::

    from powerhose.jobrunner import JobRunner
    import time
    import random
    import sys

    endpoint = "ipc:///tmp/master-routing.ipc"

    runner = JobRunner(endpoint)
    runner.start()

    try:
        # wait to have at least 1 worker
        print 'Waiting for some workers to register -- run square_worker.py'
        while len(runner.workers) < 1:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.)

        while True:
            print runner.execute('1', str(random.randrange(1000)))
    except KeyboardInterrupt:
        runner.stop()
        print 'bye'


The master is run by create a JobRunner instance tied to am **endpoint**. Then the jobs
are sent via the *execute* method.


Protocol
========

Principles:

- The system is based on a single master and multiple workers.
- The worker registers itself to the master, provides a socket,
  and wait for some work on it.
- Workers are performing the work synchronously and send back the
  result immediatly.
- The master use a simple round robin strategy to send some work
  to the workers. If all are busy, it waits a bit before it times out.
- The worker pings the master on a regular basis and exits if it's
  unable to reach it. It attempts several time to reconnect to give
  a chance to the master to come back.
- Workers are language agnostic
- the system is not responsible to respawn a master or a worker that
  dies. It can use daemontools for this.


Registering a worker
--------------------

- The Master binds an *endpoint* and wait for workers to connect to it
- The Worker connects to the master and provides its own socket.
- The Master adds the worker in the list of available workers, and
  connect to the worker socket.


::

   W                          M
   --- PING + endoint  -->   Register the Worker
   <-- PONG            ---


A worker can also unregister itself::

   W                      M
   --- REMOVE       -->   Register the Worker
   <-- REMOVED      ---



Performing a task
-----------------

- The Master chooses the next worker in the queue of available workers
- Once the master has a worker, it removes it from the queue and send work
  to it.
- The worker peforms the job synchronously then return the result.
- The master waits for the result, and after a certain timeout, ask another
  worker and remove the laggy worker from the queue
- The master gets back the result, and put back the worker in the queue


::

 M                 W
   --> JOB         --> do the job
   <-- JOBRES      ---



Heartbeat
---------

- The worker pings the master every N seconds.
- If the master fails to answer after several attempts, the worker exits
- The master that receives a ping from a unknown worker, registers it
  by adding it to the queue.

::

   W                      M
   --- PING + endpoint   -->   possibly : Register the Worker
   <-- PONG              ---


