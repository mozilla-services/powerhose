import argparse
import sys
import os

from powerhose.worker._worker import Worker, RegisterError
from powerhose.router import _WORKER_ENDPOINT, _REGISTRATION_ENDPOINT


# taken from distutils2
def resolve_name(name):
    """Resolve a name like ``module.object`` to an object and return it.

    This functions supports packages and attributes without depth limitation:
    ``package.package.module.class.class.function.attr`` is valid input.
    However, looking up builtins is not directly supported: use
    ``__builtin__.name``.

    Raises ImportError if importing the module fails or if one requested
    attribute is not found.
    """
    if '.' not in name:
        # shortcut
        __import__(name)
        return sys.modules[name]

    # FIXME clean up this code!
    parts = name.split('.')
    cursor = len(parts)
    module_name = parts[:cursor]
    ret = ''

    while cursor > 0:
        try:
            ret = __import__('.'.join(module_name))
            break
        except ImportError:
            cursor -= 1
            module_name = parts[:cursor]

    if ret == '':
        raise ImportError(parts[0])

    for part in parts[1:]:
        try:
            ret = getattr(ret, part)
        except AttributeError, exc:
            raise ImportError(exc)

    return ret


def main(args=sys.argv):
    parser = argparse.ArgumentParser(description='Run some watchers.')

    parser.add_argument('--endpoint', dest='endpoint', default=_WORKER_ENDPOINT,
                        help="ZMQ socket to receive jobs.")

    parser.add_argument('--worker-endpoint', dest='registration_endpoint',
                        default=_REGISTRATION_ENDPOINT,
                        help="ZMQ socket where the worker will register.")

    parser.add_argument('target', help="Fully qualified name of the callable.")
    args = parser.parse_args()

    sys.path.insert(0, os.getcwd())  # XXX
    target = resolve_name(args.target)

    print('Worker registers at %s' % args.registration_endpoint)
    print('Worker receives job at %s' % args.endpoint)
    worker = Worker(args.registration_endpoint,
                    args.endpoint,
                    target=target)

    try:
        worker.run()
    except RegisterError:
        print('The master did not respond - quitting...')
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()


if __name__ == '__main__':
    main()
