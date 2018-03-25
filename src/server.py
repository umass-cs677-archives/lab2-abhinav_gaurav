from multi_thread_server import MultiThreadedHTTPServer, create_server, set_sigint_handler, ServerRequestHandler
from multitier.front_end_server import FrontEndHTTPServer
import argparse
from multitier.dispatcher import DispatcherHTTPServer
from clocksync.leader_election import LeaderElection

class MultiThreadedFrontEndServer(FrontEndHTTPServer, MultiThreadedHTTPServer, LeaderElection):
    def __init__(self, server_address, handler_class, database_ip, database_port):
        FrontEndHTTPServer.__init__(self, database_ip, database_port)
        MultiThreadedHTTPServer.__init__(self, server_address, handler_class)


def main():
    parser = argparse.ArgumentParser(description="MuliThreadedFrontEndServer")
    parser.add_argument('-p', '--port', type=int, help='Port number', required=True)
    parser.add_argument('--db_ip', type = str, help = 'Database IP Addr', required = True)
    parser.add_argument('--db_port', type = int, help = 'Database Port number', required = True)

    cmdargs = parser.parse_args()
    httpd = create_server(DispatcherHTTPServer, ServerRequestHandler, cmdargs.port, MultiThreadedFrontEndServer,
                          cmdargs.db_ip,
                          cmdargs.db_port)
    set_sigint_handler(httpd)

    print "Running HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever()

if __name__ == "__main__":
    main()
