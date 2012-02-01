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

#include "util.h"

using namespace zmq;
using namespace std;


namespace powerhose
{


  void str2msg(string* data, message_t* msg) {
    const char* sres = data->c_str();
    msg->rebuild((void *)(sres), data->size(), NULL, NULL);
  }

  void msg2str(message_t* msg, string* res) {
    size_t size = msg->size();
    char* data = new char[msg->size() + 1];
    memcpy(data, msg->data(), size);
    data[size] = 0;
    res->assign(data);
  }

  void serialize(vector<string>* data, string* res) {
    res->clear();
    for (unsigned int i = 0; i < data->size(); i++) {
        res->append(data->at(i));
        if (i < data->size() - 1) {
            res->append(":::");
        }
    }
  }

  void unserialize(string* data, vector<string>* res) {
    size_t found = 0;
    int current = 0;
    string sep = ":::";

    while (found != string::npos) {
        found = data->find_first_of(sep, current);
        if (found > 0) {
            res->push_back(data->substr(current, found));
            current = found + sep.size();
        }
    }
   }

  void send(socket_t* socket, vector<string>* data) {
      message_t msg;
      string res;
      serialize(data, &res);
      cout << "sending " << res << endl;
      str2msg(&res, &msg);
      socket->send(msg);
  }

  void recv(socket_t* socket, vector<string>* data) {
      message_t msg;
      string smsg;
      socket->recv(&msg);
      msg2str(&msg, &smsg);
      cout << "received " << smsg << endl;
      data->clear();
      unserialize(&smsg, data);
  }



}
