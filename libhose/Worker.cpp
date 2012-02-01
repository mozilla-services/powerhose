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

using namespace zmq;
using namespace std;


namespace powerhose
{
  /*
   * Workers Class
   *
   */

  Worker::Worker(const char* receiverChannel, const char* endPoint) {
    this->timeout = 2000000;  // configurable
    this->ctx = new context_t(1);
    this->receiver = new socket_t(*this->ctx, ZMQ_REP);
    this->receiver->bind(receiverChannel);
    this->receiverChannel = receiverChannel;
    this->endpoint = new socket_t(*this->ctx, ZMQ_REQ);
    this->endpoint->connect(endPoint);

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

  void Worker::execute(vector<string>* vreq,  vector<string>* vres) {
      vres->push_back("NOTIMPLEMENTED");
  }

  void Worker::reg() {
      // register to the master
      cout << "registering" << endl;
      vector<string> vreq;
      vreq.push_back("READY");
      vreq.push_back(this->receiverChannel);
      string req;
      serialize(&vreq, &req);
      string resp = "REGISTERED";
      this->callMaster(&req, &resp);
  }

  // we want to add the replay feature here
  void Worker::callMaster(string* request, string* response) {
      // setting up the poller for this exchange
      zmq_pollitem_t poll_items[1];
      zmq_pollitem_t item1;
      item1.socket = *this->endpoint;
      item1.events = ZMQ_POLLIN;
      poll_items[0] = item1;
      cout << "Sending a call" << endl;

      // sending the message to the master
      message_t msg;
      str2msg(request, &msg);
      try {
          this->endpoint->send(msg, ZMQ_NOBLOCK);
      }
      catch (...) {
          throw RegisterError();
      }

      cout << "waiting for an answer" << endl;

      // waiting for an answer now
      poll(poll_items, 1, this->timeout);

      cout << "poll is over" << endl;
      // no answer in time
      if (poll_items[0].revents == 0) {
          cout << "did not get anything" << endl;
          throw RegisterError();
      }
      else {
        // getting the result
        message_t res;
        this->endpoint->recv(&res);

        string result;
        msg2str(&res, &result);

        cout << "we got " << result << endl;
        cout << "we want " << *response << endl;

        if (result != *response) {
            throw RegisterError();
        }
        else cout << "Registered!" << endl;
      }
  }


  void Worker::run() {

    // register
    this->reg();

    cout << "Now waiting for some job" << endl;
    // now loop and wait for some work to do
    zmq_pollitem_t poll_items[1];
    zmq_pollitem_t item1;
    item1.socket = *this->receiver;
    item1.events = ZMQ_POLLIN;
    poll_items[0] = item1;

    vector<string> vresp;
    vector<string> vreq;

    this->running = true;

    while (this->running) {
      // waiting for an answer now
      poll(poll_items, 1, this->timeout);

      for (short j = 0; j < poll_items[0].revents; j++) {

        vresp.clear();
        vreq.clear();

        recv(this->receiver, &vreq);

        if (vreq.at(0) == "WAKE") {
           vresp.push_back("GIVE");
           send(this->receiver, &vresp);
        }
        else {
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
    }
  }
}
