#ifndef WORKER_H
#define WORKER_H

#include <exception>
#include <string.h>
#include <zmq.hpp>
#include <iostream>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/wait.h>
#include <map>
#include <sstream>
#include "util.h"
#include <pthread.h>

using namespace zmq;
using namespace std;


namespace powerhose
{

  class RegisterError: public exception {
    virtual const char* what() const throw() {
      return "Registration error";
    }
  };

  class Worker {

    private:
        bool running;
        context_t* ctx;
        socket_t* receiver;
        zmq_pollitem_t poll_items[1];
        void reg();

    protected:
        virtual void execute(vector<string>* vreq,  vector<string>* vres);

    public:
       Worker(const char* receiverChannel, const char* endPoint);
       ~Worker();
       void run();

       int timeout;

       const char* receiverChannel;
       socket_t* endpoint;
       bool heartbeatRunning;
       bool heartbeatFailed;
       bool heartbeatDelay;
  };

}

#endif
