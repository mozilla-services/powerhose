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
        int timeout;
        bool running;
        context_t* ctx;
        socket_t* receiver;
        socket_t* endpoint;
        zmq_pollitem_t poll_items[1];
        void callMaster(string* request, string* response);
        const char* receiverChannel;
    protected:        
        void execute(vector<string>* vreq,  vector<string>* vres);

    public:
       Worker(const char* receiverChannel, const char* endPoint);
       ~Worker();
       void reg();
       void run();
  };

}

#endif
