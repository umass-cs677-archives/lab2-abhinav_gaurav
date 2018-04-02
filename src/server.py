from multi_thread_server import MultiThreadedHTTPServer, create_server, set_sigint_handler, ServerRequestHandler
from multitier.front_end_server import FrontEndHTTPServer
from multitier.dispatcher import DispatcherHTTPServer
from multitier.database_server import Database
from clocksync.leader_election import LeaderElection
from clocksync.clock_sync import Clock
from raffle.total_ordering import TotalOrdering

import argparse
import requests
import utils
import config

################TODO: All functions that defined in child class but not defined in parent has to be defined in parent with exception "Not Implemented"
#TODO: Add clock offset for each server in different directory
server_count = 0

class MultiThreadedFrontEndServer(FrontEndHTTPServer, MultiThreadedHTTPServer, LeaderElection, Clock, TotalOrdering):
    def __init__(self, server_addr_port, handler_class, database_ip, database_port, disp_addr):
        self.addr_port = server_addr_port
        FrontEndHTTPServer.__init__(self, database_ip, database_port, disp_addr)
        MultiThreadedHTTPServer.__init__(self, server_addr_port, handler_class)
        #LeaderElection.__init__(self, '127.0.0.1:' + str(server_addr_port[1]))
        #Clock.__init__(self, 100)
        global server_count
        TotalOrdering.__init__(self, server_count)
        server_count += 1
        
    def get_all_servers(self):
        print "get all servers "+self.disp_addr
        r = requests.get('http://' + self.disp_addr + '/getAllServers/')    # TODO change to dispatcher port and addr
        obj = utils.check_response_for_failure(r.text)
        return obj.servers
    
    def process_request(self, request, client_address):
        #self.multicast_ordering()
        return MultiThreadedHTTPServer.process_request(self, request, client_address)
        
    def call_request_handler(self, path, request):        
        #try:
            #~ if ("getMedalTally" in path or "getScore" in path):
                #~ self.multicast_ordering()
            meth, args = self.parse_request_path(path)
            return meth(*args)
        #except Exception as e:
        #    return json.dumps({"response": "failure", "me
    def get_all_front_end_servers(self):
        r = requests.get('http://' + self.disp_addr + '/getAllFrontEndServers/')    # TODO change to dispatcher port and addr
        print r.text
        obj = utils.check_response_for_failure(r.text)
        return obj.servers
        
def main():
    parser = argparse.ArgumentParser(description="MuliThreadedFrontEndServer")
    parser.add_argument('--disp_ip', type= str, default = "127.0.0.1", help = "Dispatcher IP")
    parser.add_argument('--disp_port', type=int, default=config.DISPATCHER_PORT, help='Dispatcher Port number')
    parser.add_argument('--fes_port', type=int, default=config.FRONT_END_PORT, help='Front-end servers starting port number')
    parser.add_argument('--db_ip', type=str, default="127.0.0.1", help='Database IP Addr')
    parser.add_argument('--db_port', type=int, default=config.DATABASE_PORT, help='Database Port number')
    parser.add_argument('--n_servers', type=int, default=2, help='Number of Front End Servers')
    cmdargs = parser.parse_args()
    
    #Run Dispatcher and Front End servers
    httpd = create_server(DispatcherHTTPServer, ServerRequestHandler, 
                          cmdargs.disp_port,
                          MultiThreadedFrontEndServer, cmdargs.fes_port,
                          cmdargs.db_ip, cmdargs.db_port, 
                          cmdargs.disp_ip, cmdargs.n_servers)
    set_sigint_handler(httpd)

    print "Running Front End HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever ()

if __name__ == "__main__":
    main()
