=========
Powerhose
=========

.. note::

   This is still a work in progress - no stable version has
   been released yet.


.. image:: images/medium-powerhose.png
   :align: right

**Powerhose turns your CPU-bound tasks into I/O-bound tasks so your applications
are easier to scale.**

Powerhose is an implementation of the
`Request-Reply Broker <http://zguide.zeromq.org/page:all#A-Request-Reply-Broker>`_
pattern in ZMQ.

The two main parts are:

- a broker that binds a socket to get some job (*"front"*) and a
  socket for workers (*"back"*) to connect to the broker.

- workers that connect to the "back" socket, receives jobs and
  send back results.

When a job comes in, the broker simply re-route it to its workers from
the front to the back socket, then get back the result and go from the back
to the front socket.

Workers also ping the broker on a regular basis via a *"heartbeat"* socket
and die in case the broker has been offline for too long.

Powerhose uses `Circus <http://circus.readthedocs.org>`_ to manage the
life of the broker and the workers, and provide high level APIs for your
program.

Workers can be written in Python but also in any language that has a
ZeroMQ library.

If you have CPU-Bound tasks that could be performed in a specialized C++
program for example, Powerhose is a library you could use to ease your
life.

If you are curious about why we wrote this library see :ref:`why`.


Example
=======

Here's a full example of usage -- we want to delegate some work
to a specialized worker.

Let's create a function that just echoes back what was sent to it,
and save it in an :file:`example` module::

    def echo(job):
        return job.data


This function takes a :class:`Job` instance that contains the data sent by
Powerhose. It returns its content immediately.

Let's run our Powerhose cluster with the *powerhose* command, by simply
pointing the :func:`echo` callable::

    $ powerhose echo_worker.echo
    [circus] Starting master on pid 51177
    [circus] broker started
    [circus] workers started
    [circus] Arbiter now waiting for commands


That's it !  By default one broker and 5 workers are launched, but you can
run as many workers as you need, and even add more while the system is
running.

Now that the system is up and running, let's try it out in a Python
shell::

    >>> from powerhose.client import Client
    >>> client = Client()
    >>> client.execute('test')
    'test'


Congrats ! You have a Powerhose system up and running !

To learn about all existing commands and their options, see :ref:`commands`.


Using Powerhose programmaticaly
===============================

The simplest way to run a Powerhose system is to use the command line as
previously shown, but you can also do everything programmatically via
the :func:`get_cluster` function.

Here's an example::

    from powerhose import get_cluster
    from powerhose.client import Client


    cluster = get_cluster('example.echo', background=True)
    cluster.start()

    client = Client()

    for i in range(10):
        print client.execute(str(i))

    cluster.stop()


Here, the cluster is launched programmatically in the background and the
client uses it as before.

To learn more about Powerhose APIs, see :ref:`library`.



More documentation
==================

.. toctree::
   :maxdepth: 2

   installation
   commands
   library
   examples
   why

Contributions and Feedback
==========================

You can reach us for any feedback, bug report, or to contribute, at
https://github.com/mozilla-services/powerhose

We can also be found in the **#services-dev** channel on irc.mozilla.org.
