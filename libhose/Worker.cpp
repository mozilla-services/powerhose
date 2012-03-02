#include <string.h>
#include <zmq.hpp>
#include <iostream>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <map>
#include <sstream>
#include <vector>
#include "Worker.h"
#include "util.h"


void callSocket(::std::string* request, ::std::string* response, ::zmq::socket_t* socket, int timeout) {
    ::std::cout << "" << " Sending " << *request << ::std::endl;

    // setting up the poller for this exchange

    zmq_pollitem_t poll_items[1];
    zmq_pollitem_t item1;
    item1.socket = *socket;
    item1.events = ZMQ_POLLIN;
    poll_items[0] = item1;

    // sending the message to the master
    ::zmq::message_t msg;
    str2msg(request, &msg);
    try {
        socket->send(msg, ZMQ_NOBLOCK);
    }
    catch (...) {
        ::std::cout << "" << " could not send a msg" << ::std::endl;
        throw RegisterError();
    }

    ::std::cout << "" << " waiting for an answer" << ::std::endl;

    // waiting for an answer now
    ::zmq::poll(poll_items, 1, timeout);

    ::std::cout << "" <<  " poll is over" << ::std::endl;
    // no answer in time
    if (poll_items[0].revents == 0) {
        ::std::cout << "did not get anything" << ::std::endl;
        throw RegisterError();
    }
    else {
    // getting the result
    ::zmq::message_t res;
    socket->recv(&res);

    ::std::string result;
    msg2str(&res, &result);

    ::std::cout <<"" <<  " we got " << result << ::std::endl;
    ::std::cout << "" << " we want " << *response << ::std::endl;

    if (result != *response) {
        throw RegisterError();
    }
    else ::std::cout << "" << " Registered!" << ::std::endl;
    }
}

/*
    heartbeat -- pings the master 
*/
void *heartbeat(void *ptr) {
Worker *worker = (Worker*) ptr;
::std::string pong = "PONG";
::std::vector< ::std::string> vreq;
vreq.push_back("PING");
vreq.push_back(worker->receiverChannel);
::std::string req;
serialize(&vreq, &req);
int failures = 0;
int max_failures = 10;

while (worker->heartbeatRunning && failures < max_failures) {
    try {
        callSocket(&req, &pong, worker->endpoint, worker->timeout);
        ::std::cout << "ping did work" << ::std::endl;
    }
    catch (...) {
        ::std::cout << "ping did not work!" << ::std::endl;
        failures += 1;
    }
    // we need to sleep here
    sleep(worker->heartbeatDelay);
}
// if we quit because of failures, we need to toggle the worker flag
if (failures >= max_failures) {
    worker->heartbeatFailed = true;
}
::std::cout << "bye!" << ::std::endl;
}


/*
* Workers Class
*
*/

Worker::Worker(const char* receiverChannel, const char* endPoint) {
this->heartbeatDelay = 10;
this->timeout = 1000000;  // zmq timeout is in microseconds
this->ctx = new ::zmq::context_t(1);
this->receiver = new ::zmq::socket_t(*this->ctx, ZMQ_REP);
this->receiver->bind(receiverChannel);
this->receiverChannel = receiverChannel;
this->endpoint = new ::zmq::socket_t(*this->ctx, ZMQ_REQ);
this->endpoint->connect(endPoint);
this->heartbeatFailed = false;
zmq_pollitem_t item1;
item1.socket = *this->receiver;
item1.events = ZMQ_POLLIN;
this->poll_items[0] = item1;
}

Worker::~Worker() {
this->receiver->close();
delete this->receiver;
this->endpoint->close();
delete this->endpoint;
delete this->ctx;
}

void Worker::execute(::std::vector< ::std::string>* vreq,  ::std::vector< ::std::string>* vres) {
    vres->push_back("NOTIMPLEMENTED");
}

void Worker::reg() {
    // register to the master
    ::std::cout << "registering" << ::std::endl;
    ::std::vector< ::std::string> vreq;
    vreq.push_back("PING");
    vreq.push_back(this->receiverChannel);
    ::std::string req;
    serialize(&vreq, &req);
    ::std::string resp = "PONG";
    callSocket(&req, &resp, this->endpoint, this->timeout);
}

void Worker::run() {
// register
this->reg();

// wait a bit
sleep(1);

// start the heartbeat
pthread_t th;
::std::cout << "creating the HB" << ::std::endl;
this->heartbeatRunning = true;
pthread_create(&th, NULL, heartbeat, (void*)this);

::std::cout << "Now waiting for some job" << ::std::endl;
// now loop and wait for some work to do
zmq_pollitem_t poll_items[1];
zmq_pollitem_t item1;
item1.socket = *this->receiver;
item1.events = ZMQ_POLLIN;
poll_items[0] = item1;

::std::vector< ::std::string> vresp;
::std::vector< ::std::string> vreq;

this->running = true;

while (this->running && !this->heartbeatFailed) {
    // waiting for an answer now
    ::zmq::poll(poll_items, 1, this->timeout);

    for (short j = 0; j < poll_items[0].revents; j++) {

    vresp.clear();
    vreq.clear();

    recv(this->receiver, &vreq);

    if (vreq.at(0) != "JOB") {
        // error, raise something
    }

    vresp.push_back("JOBRES");

    try {
        this->execute(&vreq, &vresp);
    }
    catch (...) {
        vresp.push_back("ERROR");
    }
    // sending back the response
    send(this->receiver, &vresp);
    }
}

// stop the heartbeat
::std::cout << "stopping the heartbeat" << ::std::endl;
this->heartbeatRunning = false;
pthread_join(th, NULL);
::std::cout << "The worker is done" << ::std::endl;
}

