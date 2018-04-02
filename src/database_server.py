from multi_thread_server import MultiThreadedHTTPServer, create_server, set_sigint_handler, ServerRequestHandler
from multitier.front_end_server import FrontEndHTTPServer
from multitier.dispatcher import DispatcherHTTPServer
from multitier.database_server import Database
from clocksync.leader_election import LeaderElection
from clocksync.clock_sync import Clock
import argparse
import requests
import utils
import config
import prwlock


class DatabaseHTTPServer(MultiThreadedHTTPServer, Database, LeaderElection, Clock):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''

    def __init__(self, server_addr_port, handler_class, disp_ip_addr):
        MultiThreadedHTTPServer.__init__(self, server_addr_port, handler_class)
        Database.__init__(self)
        # LeaderElection.__init__(self, '127.0.0.1:' + str(server_addr_port[1]))
        # Clock.__init__(self, 100)
        self.disp_ip_addr = disp_ip_addr
        self.n_requests_lock = prwlock.RWLock()

    def get_all_servers(self):
        r = requests.get('http://' + self.disp_ip_addr + '/getAllServers/')  # TODO change to dispatcher port and addr
        print r.text
        obj = utils.check_response_for_failure(r.text)
        return obj.servers

    def get_load(self):
        with self.n_requests_lock.reader_lock():
            return self.number_of_requests

    def call_request_handler(self, path, request):
        with self.n_requests_lock.writer_lock():
            self.number_of_requests += 1
        to_ret = MultiThreadedHTTPServer.call_request_handler(self, path, request)
        with self.n_requests_lock.writer_lock():
            self.number_of_requests -= 1
        return to_ret


def main():
    parser = argparse.ArgumentParser(description="MuliThreadedFrontEndServer")
    parser.add_argument('--disp_port', type=int, default=config.DISPATCHER_PORT, help='Dispatcher Port number')
    parser.add_argument('--fes_port', type=int, default=config.FRONT_END_PORT,
                        help='Front-end servers starting port number')
    parser.add_argument('--db_ip', type=str, default="127.0.0.1", help='Database IP Addr')
    parser.add_argument('--db_port', type=int, default=config.DATABASE_PORT, help='Database Port number')

    cmdargs = parser.parse_args()

    # Run Database server
    httpd = create_server(DatabaseHTTPServer, ServerRequestHandler, cmdargs.db_port,
                          "127.0.0.1" + ":" + str(cmdargs.disp_port))

    set_sigint_handler(httpd)

    print "Running Database Server HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever()


if __name__ == "__main__":
    main()
