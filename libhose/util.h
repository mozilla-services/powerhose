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



using namespace zmq;
using namespace std;


namespace powerhose
{
  void str2msg(string* data, message_t* msg);
  void msg2str(message_t* msg, string* res);
  void serialize(vector<string>* data, string* res);
  void unserialize(string* data, vector<string>* res);
  void send(socket_t* socket, vector<string>* data);
  void recv(socket_t* socket, vector<string>* data);
}
