import time
import random
import sys
import zmq


endpoint = "ipc://master-routing.ipc"
workpoint = "ipc://%s-routing.ipc"


def worker(identity):
    context = zmq.Context()
    identity = workpoint % identity

    print 'I am worker ' + identity

    # ping the master we are online, with an ID
    master = context.socket(zmq.REQ)
    master.connect(endpoint)
    master.send_multipart(['READY', identity], zmq.NOBLOCK)
    # XXX need to push this in into a poll
    # for registration timeout
    print 'waiting for ack'
    res = master.recv()

    # set up the work channel
    work = context.socket(zmq.REP)
    work.bind(identity)

    # setting a poller
    poller = zmq.Poller()
    poller.register(work, zmq.POLLIN)

    now = time.time()

    print 'waiting for some work now'
    while True:
        try:
            events = dict(poller.poll(1000))
        except zmq.ZMQError:
            print 'oopsie'
            break # interrupted

        for socket in events:
            msg = socket.recv_multipart()
            print msg
            if msg == ['WAKE']:
                # yeah I can work
                socket.send('GIVE')
            elif msg[0] == 'JOB':
                # do the job and send the result
                print '%s is doing some work' % identity
                socket.send_multipart(["JOBRES", msg[1], "RESULT"])
    context.destroy(0)


if __name__ == '__main__':
    try:
        worker(sys.argv[1])
    except KeyboardInterrupt:
        print 'bye'



