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



void str2msg(::std::string* data, ::zmq::message_t* msg) {
    const char* sres = data->c_str();
    msg->rebuild((void *)(sres), data->size(), NULL, NULL);
}

void msg2str(::zmq::message_t* msg, ::std::string* res) {
    size_t size = msg->size();
    char* data = new char[msg->size() + 1];
    memcpy(data, msg->data(), size);
    data[size] = 0;
    res->assign(data);
}

void serialize(::std::vector< ::std::string>* data, ::std::string* res) {
    res->clear();
    for (unsigned int i = 0; i < data->size(); i++) {
        res->append(data->at(i));
        if (i < data->size() - 1) {
            res->append(":::");
        }
    }
}

void unserialize(::std::string* data, ::std::vector< ::std::string>* res) {
    size_t found = 0;
    int current = 0;
    int size;
    ::std::string sep = ":::";

    while (found != ::std::string::npos) {
        found = data->find_first_of(sep, current + 1);
        if (found > 0) {
            size = found - current;
            res->push_back(data->substr(current, size));
            current = found + sep.size();
        }
    }
}

void send(::zmq::socket_t* socket, ::std::vector< ::std::string>* data) {
    ::zmq::message_t msg;
    ::std::string res;
    serialize(data, &res);
    ::std::cout << "sending " << res << ::std::endl;
    str2msg(&res, &msg);
    socket->send(msg);
}

void recv(::zmq::socket_t* socket, ::std::vector< ::std::string>* data) {
    ::zmq::message_t msg;
    ::std::string smsg;
    socket->recv(&msg);
    msg2str(&msg, &smsg);
    ::std::cout << "received " << smsg << ::std::endl;
    data->clear();
    unserialize(&smsg, data);
}
