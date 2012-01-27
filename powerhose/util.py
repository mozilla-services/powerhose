import zmq


def polling(sockets, onreceive, condition, multipart=True, timeout=1000,
            onempty=None):
    poller = zmq.Poller()

    if not isinstance(sockets, (tuple, list)):
        sockets = [sockets]

    for socket in sockets:
        poller.register(socket, zmq.POLLIN)

    while condition():
        try:
            events = dict(poller.poll(timeout))
        except zmq.ZMQError:
            break

        if events == {} and onempty is not None:
            onempty()

        for socket in events:
            if multipart:
                msg = socket.recv_multipart()
            else:
                msg = socket.recv()

            onreceive(msg, socket)
