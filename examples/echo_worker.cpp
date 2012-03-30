#include "Worker.h"
#include <iostream>
#include <sstream>

class SquareWorker: public Worker {

    protected:
        void execute(::std::vector< ::std::string>* vreq,  ::std::vector< ::std::string>* vres);
    public:
       SquareWorker(const char* receiverChannel, const char* endPoint);
};


SquareWorker::SquareWorker(const char* receiverChannel, const char* endPoint) : Worker(receiverChannel, endPoint) {
 //
};


void SquareWorker::execute(::std::vector< ::std::string>* vreq,  ::std::vector< ::std::string>* vres) {
  int value;
  ::std::string number = vreq->at(2);
  ::std::stringstream ss(number);
  ss >> value;
  value *= value;
  ::std::stringstream out;
  out << value;
  vres->push_back(out.str());
}


int main(int argc, const char* const argv[]) {


  const char* receiver = argv[1];   //"ipc://worker-cpp.ipc";
  const char* endpoint = argv[2];  // "ipc:///tmp/master-routing.ipc";

  ::std::cout << receiver << ::std::endl;
  ::std::cout << endpoint << ::std::endl;
  ::std::cout << "Creating a worker" << ::std::endl;
  SquareWorker worker(receiver, endpoint);

  ::std::cout << "Let's run it" << ::std::endl;
  worker.run();

  return 1;
}


