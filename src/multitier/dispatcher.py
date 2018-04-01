import sys

sys.path.insert(0, "../")

import utils
import json
import threading
import requests
import multi_thread_server


class DispatcherHTTPServer(multi_thread_server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''

    def __init__(self, server_addr, handler_cls, front_end_server_cls, fes_port, db_ip, db_port, ip):
        multi_thread_server.MultiThreadedHTTPServer.__init__(self, server_addr, handler_cls)
        self.n_servers = 1 #TODO: command line args
        self.server_ip = "127.0.0.1"            # TODO
        self.server_port = fes_port
        self.mutex = threading.RLock()
        self.front_end_server_cls = front_end_server_cls
        self.db_ip = db_ip
        self.db_port = db_port
        self.full_addr = ip+":"+str(server_addr[1])
        self.servers = {}  # Dictionary of Server addresses and number of clients associated with them
        self.create_front_end_servers(self.n_servers, self.server_ip, self.server_port)

    def create_front_end_servers(self, number, server_ip, port):
        for i in range(0, number):
            print "Starting server %d at " % number, server_ip, port
            server, th = multi_thread_server.create_and_run_server(self.front_end_server_cls,
                                                                   multi_thread_server.ServerRequestHandler, port,
                                                                   self.db_ip, str(self.db_port), self.full_addr)
            full_address = self.server_ip + ":" + str(port)
            port += 1
            self.servers[full_address] = 0

    def getServer(self):
        ''' REST endpoint for getting server.
            Returns the address to server and increments the load count
        '''
        self.mutex.acquire()
        # Cannot use reader writer locks because following code requires
        # both reader and writer lock are required. Hence, using threading.RLock.
        try:
            minload = sys.maxint
            minload_server = None
            for server in self.servers:
                if minload > self.servers[server]:
                    minload = self.servers[server]
                    minload_server = server

            assert (minload != sys.maxint and minload_server != None)
            self.servers[minload_server] += 1
        finally:
            self.mutex.release()

        if (minload_server == None):
            return json.dumps({"response": "failure", "message": "Failed to get server, try again"})
        r = requests.get("http://" + minload_server + "/registerClient")
        utils.check_response_for_failure(r.text)
        return json.dumps({"response": "success", "server": minload_server})

    def releaseServer(self, serveraddress):
        ''' REST Endpoint for a client to release the server. 
            Decrements the load count on server
        '''
        if (serveraddress not in self.servers):
            return json.dumps({"response": "failure", "message": "No server with address %s found" % (serveraddress)})

        if (self.servers[serveraddress] == 0):
            return json.dumps({"response": "failure", "message": "No load on %s" % (serveraddress)})

        self.mutex.acquire()
        try:
            self.servers[serveraddress] -= 1
            r = requests.get("http://" + serveraddress + "/unregisterClient")
            utils.check_response_for_failure(r.text)
        finally:
            self.mutex.release()

        return json.dumps({"response": "success"})

    def getAllServers(self):
        return json.dumps({"response": "success", "servers": list(self.servers.keys()) + [self.db_ip+":"+str(self.db_port)]})


if __name__ == "__main__":
    multi_thread_server.main(DispatcherHTTPServer)
