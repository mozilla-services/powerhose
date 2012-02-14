#include "Worker.h"


class SquareWorker: public powerhose::Worker {

    protected:
        void execute(vector<string>* vreq,  vector<string>* vres);
    public:
       SquareWorker(const char* receiverChannel, const char* endPoint);
};


SquareWorker::SquareWorker(const char* receiverChannel, const char* endPoint) : Worker(receiverChannel, endPoint) {
 //
};


void SquareWorker::execute(vector<string>* vreq,  vector<string>* vres) {
  int value;
  string number = vreq->at(2);
  stringstream ss(number);
  ss >> value;
  value *= value;
  stringstream out;
  out << value;
  vres->push_back(out.str());
}


int main(int argc, const char* const argv[]) {


  const char* receiver = argv[1];   //"ipc://worker-cpp.ipc";
  const char* endpoint = argv[2];  // "ipc:///tmp/master-routing.ipc";

  cout << receiver << endl;
  cout << endpoint << endl;
  cout << "Creating a worker" << endl;
  SquareWorker worker(receiver, endpoint);

  cout << "Let's run it" << endl;
  worker.run();

  return 1;
}


