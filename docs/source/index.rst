=========
Powerhose
=========

.. note::

   This is still a work in progress - no stable version has
   been released yet.


.. image:: images/medium-powerhose.png
   :align: right

Powerhose is a single master / multiple worker ZeroMQ library, that can be
used to push some work to specialized workers.

ZeroMQ is mainly used as an IPC library, so the master and the workers can
interact, but since ZeroMQ can use TCP as a transport, Powerhose can also
work with distant workers.

Powerhose uses `Circus <http://circus.readthedocs.org>`_ to manage the life
of workers.

If you have CPU-Bound tasks that could be performed in a specialized C++
program for example, Powerhose is a library you could use to ease your
life

If you are curious about why we wrote this library see :ref:`why`.


Example
=======

Here's a full example of library usage: we want to delegate some maths
to a specialized worker.

Let's create a function that just echoes back what was sent to it,
and save it in an :file:`example` module::

    def echo(job):
        return job.data


This function takes a :class:`Job` instance that contains the data sent by
Powerhose. It returns it immediatly.

Let's try this worker in a shell with `powerhose-worker`::

    $ powerhose-worker example.echo
    Worker registers at ipc:///tmp/powerhose-registration.ipc
    Worker receives job at ipc:///tmp/worker-$WID.ipc
    The master did not respond - quitting...

The program exits immediatly because there are no Powerhose Router running
yet.

Let's run one ::

    $ powerhose-router
    Listening to incoming jobs at ipc:///tmp/powerhose-routing.ipc
    Workers may register at ipc:///tmp/powerhose-registration.ipc

If the worker is launched again in another shell, it will register itself to
the router.

Now that both router and worker are alive, let's try it out in a Python
shell::

    >>> from powerhose.client import Client
    >>> client = Client()
    >>> client.execute('test')
    'test'


Congrats ! You have a powerhose system up and running !


More documentation
------------------

.. toctree::
   :maxdepth: 2

   installation
   library
   protocol
   why

Contributions and Feedback
--------------------------

You can reach us for any feedback, bug report, or to contribute, at
https://github.com/mozilla-services/powerhose

We can also be found in the **#services-dev** channel on irc.mozilla.org.
