#include "Worker.h"


int main(int argc, const char* const argv[]) {


  const char* receiver = "ipc://worker-cpp.ipc";
  const char* endpoint = "ipc:///tmp/master-routing.ipc";

  cout << "Creating a worker" << endl;
  powerhose::Worker worker(receiver, endpoint);

  cout << "Let's run it" << endl;
  worker.run();

  return 1;
}


