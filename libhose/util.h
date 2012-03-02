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




namespace powerhose
{
  void str2msg(::std::string* data, ::zmq::message_t* msg);
  void msg2str(::zmq::message_t* msg, ::std::string* res);
  void serialize(::std::vector< ::std::string>* data, ::std::string* res);
  void unserialize(::std::string* data, ::std::vector< ::std::string>* res);
  void send(::zmq::socket_t* socket, ::std::vector< ::std::string>* data);
  void recv(::zmq::socket_t* socket, ::std::vector< ::std::string>* data);
}
