from multi_thread_server import MultiThreadedHTTPServer, create_server, set_sigint_handler, ServerRequestHandler
from multitier.front_end_server import FrontEndHTTPServer
from multitier.dispatcher import DispatcherHTTPServer
from clocksync.leader_election import LeaderElection
from clocksync.clock_sync import Clock
import argparse
import requests
import utils

################TODO: All functions that has to be defined in child class but not defined in parent has to be defined in parent with exception "Not Implemented"

class MultiThreadedFrontEndServer(FrontEndHTTPServer, MultiThreadedHTTPServer, LeaderElection, Clock):
    def __init__(self, server_address, handler_class, database_ip, database_port):
        FrontEndHTTPServer.__init__(self, database_ip, database_port)
        MultiThreadedHTTPServer.__init__(self, server_address, handler_class)
        LeaderElection.__init__(self, '127.0.0.1:' + str(server_address[1]))
        Clock.__init__(self, 100)
        
    def get_all_servers(self):
        r = requests.get('http://127.0.0.1:6000/getAllServers/')    # TODO change to dispatcher port and addr
        obj = utils.check_response_for_failure(r.text)
        return obj.servers
    
def main():
    parser = argparse.ArgumentParser(description="MuliThreadedFrontEndServer")
    parser.add_argument('-p', '--port', type=int, help='Port number', required=True)
    parser.add_argument('--db_ip', type=str, help='Database IP Addr', required=True)
    parser.add_argument('--db_port', type=int, help='Database Port number', required=True)

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
