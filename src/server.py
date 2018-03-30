from multi_thread_server import MultiThreadedHTTPServer, create_server, set_sigint_handler, ServerRequestHandler
from multitier.front_end_server import FrontEndHTTPServer
from multitier.dispatcher import DispatcherHTTPServer
from clocksync.leader_election import LeaderElection
import argparse
import requests
import utils


class MultiThreadedFrontEndServer(FrontEndHTTPServer, MultiThreadedHTTPServer, LeaderElection):
    def __init__(self, server_addr_port, handler_class, database_ip, database_port):
        self.addr_port = server_addr_port
        FrontEndHTTPServer.__init__(self, database_ip, database_port)
        MultiThreadedHTTPServer.__init__(self, server_addr_port, handler_class)
        LeaderElection.__init__(self, '127.0.0.1:' + str(server_addr_port[1]))

    def get_all_servers(self):
        server_address = ':'.join(self.addr_port)
        r = requests.get('http://' + server_address + '/getAllServers/')    # TODO change to dispatcher port and addr
        obj = utils.check_response_for_failure(r.text)
        print obj.servers
        return obj.servers


def main():
    parser = argparse.ArgumentParser(description="MuliThreadedFrontEndServer")
    parser.add_argument('--disp_port', type=int, default=config.DISPATCHER_PORT, help='Dispatcher Port number')
    parser.add_argument('--fes_port', type=int, default=config.FRONT_END_PORT, help='Front-end servers starting port number')
    parser.add_argument('--db_ip', type=str, help='Database IP Addr', required=True)
    parser.add_argument('--db_port', type=int, default=config.DATABASE_PORT, help='Database Port number')

    cmdargs = parser.parse_args()
    httpd = create_server(DispatcherHTTPServer, ServerRequestHandler, cmdargs.port, MultiThreadedFrontEndServer,
                          cmdargs.fes_port,
                          cmdargs.db_ip,
                          cmdargs.db_port)
    set_sigint_handler(httpd)

    print "Running HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever()


if __name__ == "__main__":
    main()
