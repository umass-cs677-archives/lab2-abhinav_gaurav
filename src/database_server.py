from multi_thread_server import MultiThreadedHTTPServer, create_server, set_sigint_handler, ServerRequestHandler
from multitier.database import Database
from clocksync.leader_election import LeaderElection
from clocksync.clock_sync import Clock
import argparse
import requests
import utils
import config
import prwlock
from random import randint

class DatabaseHTTPServer(MultiThreadedHTTPServer, Database, LeaderElection, Clock):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''

    def __init__(self, server_addr_port, handler_class, disp_ip_addr, is_leader_election, is_clock_sync):
        MultiThreadedHTTPServer.__init__(self, server_addr_port, handler_class)
        Database.__init__(self)
        if is_leader_election:
            LeaderElection.__init__(self, '127.0.0.1:' + str(server_addr_port[1]))
        if is_clock_sync:
            Clock.__init__(self, randint(1, config.DELTA), '127.0.0.1:' + str(server_addr_port[1]))
        self.disp_addr = disp_ip_addr
        self.n_requests_lock = prwlock.RWLock()

    def get_all_servers(self):
        r = requests.get('http://' + self.disp_addr + '/getAllServers/')
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
    parser.add_argument('--is_leader_election',type=str, default="True", help="Leader Election Enabled?")
    parser.add_argument('--is_clock_sync',type=str, default="True", help="Clock Synchronization Enabled?")
    
    cmdargs = parser.parse_args()

    def str2bool (s):
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
        raise Exception("Invalid Argument to str2bool, '%s'"%s)
    cmdargs = parser.parse_args()

    # Run Database server
    httpd = create_server(DatabaseHTTPServer, ServerRequestHandler, cmdargs.db_port,
                          "127.0.0.1" + ":" + str(cmdargs.disp_port), str2bool(cmdargs.is_leader_election), 
                          str2bool(cmdargs.is_clock_sync))

    set_sigint_handler(httpd)

    print "Running Database Server HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever()


if __name__ == "__main__":
    main()
