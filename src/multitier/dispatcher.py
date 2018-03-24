import utils
import json
import threading
import urllib
import requests
import config
import prwlock
import time
import server
import front_end_server
import sys

class DispatcherHTTPServer(server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''
    def __init__(self, *args, **kwargs):
        MultiThreadedHTTPServer.__init__(self, *args, **kwargs)
        self.n_servers = 10
        self.server_port = 5000
        self.server_ip = "127.0.0.1"
        self.create_front_end_servers (self.n_servers, self.server_port)
        self.mutex = threading.RLock ()
        
    def create_front_end_servers (self, number, server_ip, port):
        self.servers = {} #Dictionary of Server addresses and number of clients associated with them
        for i in range (0, number):
            server, th = server.create_and_run_server (front_end_server.FrontEndHTTPServer,
                                                       server.ServerRequestHandler, port)
            port += 1
            full_address = utils.create_address (self.server_ip, port)
            
            self.servers [full_address] = 0
        
    def getServer (self):
        ''' REST endpoint for getting server.
            Returns the address to server and increments the load count
        '''
        self.mutex.acquire ()
        #Cannot use reader writer locks because following code requires
        #both reader and writer lock are required. Hence, using threading.RLock.
        try:        
            minload = sys.intmax
            minload_server = None
            for server in self.servers:
                if minload > self.servers[server]:
                    minload = self.servers[server]
                    minload_server = server
            
            assert (minload != sys.intmax and minload_server != None)
            self.servers[server] += 1
        finally:
            self.mutex.release ()
        
        if (minload_server == None)
            return json.dump ({"response":"failure", "message":"Failed to get server, try again"})
        return json.dump ({"response":"success", "server":minload_server})

    def releaseServer (self, serveraddress):
        ''' REST Endpoint for a client to release the server. 
            Decrements the load count on server
        '''
        if (serveraddress not in self.servers):
            return json.dump ({"response":"failure", "message":"No server with address %s found"%(serveraddress)})
            
        self.mutex.acquire ()
        try:        
            self.servers[serveraddress] -= 1
        finally:
            self.mutex.release ()
        
        return json.dump ({"response":"success", "server":minload_server})

if __name__=="__main__":
    server.main(DispatcherHTTPServer)
