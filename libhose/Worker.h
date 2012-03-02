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


namespace powerhose
{

  class RegisterError: public ::std::exception {
    virtual const char* what() const throw() {
      return "Registration error";
    }
  };

  class Worker {

    private:
        bool running;
        ::zmq::context_t* ctx;
        ::zmq::socket_t* receiver;
        zmq_pollitem_t poll_items[1];
        void reg();

    protected:
        virtual void execute(::std::vector< ::std::string>* vreq,  
                             ::std::vector< ::std::string>* vres);

    public:
       Worker(const char* receiverChannel, const char* endPoint);
       ~Worker();
       void run();

       int timeout;

       const char* receiverChannel;
       ::zmq::socket_t* endpoint;
       bool heartbeatRunning;
       bool heartbeatFailed;
       bool heartbeatDelay;
  };

}

#endif
