.. _why:

Why Powerhose ?
===============

Python is a great language but as soon as you are doing CPU-bound tasks,
you might bump into the GIL issue if you try to run in parallel multiple
threads.

The GIL is the *Global Interpreter Lock* used by the CPython & the PyPy
implementations to protect some parts of the language implementation
itself.

The effect on CPU-bound tasks that are performed by several threads is
that you won't be able to use all your machine CPU cores in parallel
like in other languages.

To solve this issue, the simplest thing to do is to use **multiprocessing**,
a module that comes with the standard library and will let you
spawn processes and interact with them using pickles.

But that limits you to using the Python language on both sides.

You could also use a C++ library binded into Python, but it turns out
you're still locking the GIL here and there when you use a C++
bind through CPython. Unless you delegate *everything* to the C++ side,
the contention can be smaller but is still there.

So ideally, we'd want a library where you can delegate some specific
tasks to specialized workers, whatever language they are written into.

Of course this is feasible with the standard library, but requires
extra work to set up a protocol between the master and the workers,
and decide how to transport the data.

There's also tools like RabbitMQ that can let you set up a queue
where the master put some job to be performed, workers can pick up.

But here, we're talking about running specific CPU-Bound jobs
as fast as possible, synchronously, with no persistency at all.

Our driving use case is Mozilla's Token Server -
https://wiki.mozilla.org/Services/Sagrada/TokenServer

On this server, we have an API you can call to trade a BrowserID
assertion for a token you can use to authenticate to some of our
services.

Powerhose is our attempt to solve this issue, and is based
on ZeroMQ.

We chose ZeroMQ because:

- it's insanely fast.
- it greatly simplifies our code.
- it can work over TCP, IPC (Inter Process Communication) or even in
  the same process.

Powerhose allows us to:

- deploy dynamically as many workers as we want, even on other
  servers when it makes sense.

- write workers in C++

- greatly simplify the usage for our Python apps, since all it
  takes is a single :func:`execute` call to get the job done.

Read more about this here: http://ziade.org/2012/02/06/scaling-crypto-work-in-python/
