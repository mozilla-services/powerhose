Powerhose
=========

.. note::

   This is still a work in progress - no stable version has
   been released yet.


.. image:: images/medium-powerhose.png
   :align: right

Powerhose is a single master/ multiple worker zmq lib, that can be used to
push some work to specialized workers.

Powerhose uses Circus to manage the life of workers.


Example
=======


Worker
------

Let's create a worker that knows how to calculate a square of a number::

    import sys
    from powerhose.client.worker import Worker

    endpoint = sys.argv[1]
    workpoint = sys.argv[2]

    def square(*args):
        number = int((args)[0][1])
        return str(number * number)

    worker = Worker(endpoint, workpoint, target=square)
    try:
        worker.run()
    except KeyboardInterrupt:
        worker.stop()

The program can then be called like this::

    $ python worker.py ipc://master.ipc ipc://routing.ipc

In this example, the Worker is instanciated with:

- the **endpoint**, which is the socket where the master listens
  to workers that want to register.
- the **workpoint**, the socket where the worker gets his jobs.
- the **target**, which is the callable that receives jobs to perform.

The **square** function is getting the value in a string, and has to return
the result as a string that's sent back to the master. Of course, you would
use a real serializer/deserialzer when you operate with more complex data
structures.

Workers
-------

Now we want to run several workers, let's create another script for this::

    from powerhose.client.workers import Workers
    import sys

    cmd = '%s examples/square_worker.py ipc://worker-routing-$WID.ipc'


    workers = Workers(cmd % sys.executable)
    try:
        workers.run()
    except KeyboardInterrupt:
        workers.stop()


The Workers class will take care if creating 5 workers (default value) by
running the provided command. Notice the **$WID** value - it will be changed
with an id that's unique per worker.

Running the workers is then simply done with::

    $ python workers.py

The script uses the Circus library, which takes care of making sure the
workers are respawned in case they die.

Master
------

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


More documentation
------------------

.. toctree::
   :maxdepth: 2

   installation
   library
   protocol


Contributions and Feedback
--------------------------

You can reach us for any feedback, bug report, or to contribute, at
https://github.com/mozilla-services/powerhose

We can also be found in the **#services-dev** channel on irc.mozilla.org.
