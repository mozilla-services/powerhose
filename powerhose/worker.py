import time
import random
import sys
import zmq
import threading


endpoint = "ipc://master-routing.ipc"
workpoint = "ipc://%s-routing.ipc"

class RegisterError(Exception):
    pass


class Pinger(threading.Thread):
    def __init__(self, identity, socket, locker, failed, timeout=1.):
        threading.Thread.__init__(self)
        self.identity = identity
        self.socket = socket
        self.locker = locker
        self.running = False
        self.failed = failed
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        self.timeout = timeout
        self.disabled = False

    def disable(self):
        self.disabled = True

    def enable(self):
        self.disabled = False

    def run(self):
        self.running = True

        while self.running:
            if self.disabled:
                time.sleep(1.)
                continue

            with self.locker:
                try:
                    self.socket.send_multipart(['PING', self.identity], zmq.NOBLOCK)
                except zmq.ZMQError, e:
                    print 'could not ping ' + str(e)
                    self.running = False
                    break  # interrupted

                try:
                    events = dict(self.poller.poll(100))  #self.timeout))
                except zmq.ZMQError, e:
                    print 'pinging failed'
                    self.running = False
                    break  # interrupted

                for socket in events:
                    res = socket.recv()
                    if res != 'PONG':
                        print 'ping failed'
                        self.running = False
                    else:
                        print 'master pinged'

            time.sleep(5.)

        self.failed()
        print 'done'

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.join()


class Worker(object):

    def __init__(self, identity, timeout=1.):
        self.identity = identity
        self.ctx = zmq.Context()
        self.timeout = timeout * 1000
        self.master = self.ctx.socket(zmq.REQ)
        self.master.connect(endpoint)
        self.work = self.ctx.socket(zmq.REP)
        self.work.bind(identity)
        self.registered = self.running = False
        # setting a poller
        self.poller = zmq.Poller()
        self.poller.register(self.work, zmq.POLLIN)
        self.locker = threading.RLock()
        self.pinger = Pinger(self.identity, self.master, self.locker, self.failed)

    def failed(self):
        print 'ping failed lets try to reconnect and die'
        try:
            self._msg('REMOVE', 'REMOVED')
        except RegisterError:
            pass
        self.stop()

    def register(self):
        self._msg('READY', 'REGISTERED')
        self.registered = True

    def _msg(self, req, rep):
        print 'sending to master'

        self.pinger.disable()
        try:
            print 'locking'
            with self.locker:
                poller = zmq.Poller()
                poller.register(self.master, zmq.POLLIN)

                # ping the master we are online, with an ID
                try:
                    print '%s => %s' % (req, self.identity)
                    self.master.send_multipart([req, self.identity], zmq.NOBLOCK)
                except zmq.ZMQError, e:
                    print 'sending failed'
                    raise RegisterError()

                try:
                    events = dict(poller.poll(self.timeout))
                except zmq.ZMQError:
                    print 'polling failed'
                    raise RegisterError()

                if events == {}:
                    # a well
                    print 'no answer'
                    raise RegisterError()
                else:
                    for socket in events:
                        print 'answer, reading'
                        res = socket.recv()
                        if res != rep:
                            raise RegisterError(res)
                        print '%s <= %s' % (rep, socket.identity)
        finally:
            print 'reenable the pinger'
            self.pinger.enable()

    def stop(self):
        self.running = False
        self.pinger.stop()
        time.sleep(.5)
        self.ctx.destroy(0)

    def run(self):
        self.running = True
        self.register()
        self.pinger.start()

        while self.running:
            try:
                events = dict(self.poller.poll(self.timeout))
            except zmq.ZMQError:
                break # interrupted

            for socket in events:
                msg = socket.recv_multipart()
                print msg
                if msg == ['WAKE']:
                    # yeah I can work
                    socket.send('GIVE')
                elif msg[0] == 'JOB':
                    # do the job and send the result
                    print '%s is doing some work' % self.identity
                    socket.send_multipart(["JOBRES", msg[1], "RESULT"])

        self._msg('REMOVE', 'REMOVED')


if __name__ == '__main__':

    try:
        worker = Worker(workpoint % sys.argv[1])
        worker.run()
        worker.stop()
        print 'bye'
    except KeyboardInterrupt:
        worker.stop()
        print 'bye'



