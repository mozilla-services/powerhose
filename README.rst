=========
Powerhose
=========

Powerhose is a single master/ multiple worker zmq lib, that can be used to
push some work to specialized workers.

Protocol
========

Principles:

- The system is based on a single master and multiple workers.
- The worker registers itself to the master, provides a socket,
  and wait for some work on it.
- Workers are performing the work synchronously and send back the
  result immediatly.
- The master load-balances on available workers, and if all are busy
  waits a bit before it times out.
- The worker pings the master on a regular basis and commit suicide
  if it's unable to reach it. It attempts several time to reconnect
  to give a chance to the master to come back.
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

- The Master chooses a worker that's in the list of available workers
- The Master ask the worker if it can accept the job
- If the worker fails to answer the Master removes it from the list
- Once the master has a worker, it removes it from the list of available
  workers and send work to it
- The worker peforms the job synchronously then return the result
- The master waits for the result, and after a certain timeout, ask another
  worker and remove the laggy worker from the list of available workers
- The master gets back the result, and put back the worker in the list


::

 M                 W
   --- WAKE        --> Acks
   <-- GIVE        ---
   --> JOB         --> do the job
   <-- JOBRES      ---



Heartbeat
---------

- The worker pings the master every N seconds.
- If the master fails to answer after several attempts, the worker commit
  suicide.
- The master that receives a ping from a unknown worker, registers it

::
   W                      M
   --- PING        -->   possibly : Register the Worker
   <-- PONG        ---


