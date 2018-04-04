import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(sys.modules[__name__].__file__)))

import utils
import json
import threading
import requests
import multi_thread_server
import time
import config
from random import randint, random


class DispatcherHTTPServer(multi_thread_server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''

    def __init__(self, server_addr, handler_cls, front_end_server_cls, fes_port, db_ip, db_port, ip, n_servers,
                 is_leader_election, is_clock_sync, is_total_ordering, is_raffle):
        multi_thread_server.MultiThreadedHTTPServer.__init__(self, server_addr, handler_cls)
        self.n_servers = n_servers
        self.server_ip = "127.0.0.1"
        self.server_port = fes_port
        self.mutex = threading.RLock()
        self.front_end_server_cls = front_end_server_cls
        self.db_ip = db_ip
        self.db_port = db_port
        self.full_addr = ip + ":" + str(server_addr[1])
        self.servers = {}  # Dictionary of Server addresses and number of clients associated with them
        self.server_threads = []  # List of tuples of server objects and threads
        self.is_leader_election = is_leader_election
        self.is_clock_sync = is_clock_sync
        self.is_total_ordering = is_total_ordering
        self.is_raffle = is_raffle
        self.central_lock = threading.RLock()
        self.can_lock = True
        print "dispatcher leader election", is_leader_election
        self.create_front_end_servers(self.n_servers, self.server_ip, self.server_port)
        if is_raffle:
            self.start_raffle_thread()

    def create_front_end_servers(self, number, server_ip, port):
        '''
        Dispatcher creates front-end servers
        :param number: number of servers to create
        '''
        for i in range(0, number):
            print "Starting server %d at " % i, server_ip, port
            server, th = multi_thread_server.create_and_run_server(self.front_end_server_cls,
                                                                   multi_thread_server.ServerRequestHandler, port,
                                                                   self.db_ip, str(self.db_port), randint(1, 100),
                                                                   self.full_addr,
                                                                   self.is_leader_election, self.is_clock_sync,
                                                                   self.is_total_ordering)
            full_address = self.server_ip + ":" + str(port)
            port += 1
            self.servers[full_address] = 0
            self.server_threads.append((server, th))

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
        return json.dumps(
            {"response": "success", "servers": list(self.servers.keys()) + [self.db_ip + ":" + str(self.db_port)]})

    def getAllFrontEndServers(self):
        return json.dumps({"response": "success", "servers": list(self.servers.keys())})

    def getLeaderElectionLock(self):
        '''
        Centralized lock API for leader election lock.
        :return:
        '''
        with self.central_lock:
            if self.can_lock:
                self.can_lock = False
                return json.dumps({"response": "success", "can_lock": True})
            else:
                return json.dumps({"response": "success", "can_lock": False})

    def releaseLeaderElectionLock(self):
        '''
        API to release leader election lock.
        :return:
        '''
        with self.central_lock:
            self.can_lock = True
        return json.dumps({"response": "success"})

    def shutdown_server(self):
        for server, th in self.server_threads:
            server.shutdown()
            server.shutdown_server()
            th.join()

        self.end_raffle_thread()
        multi_thread_server.MultiThreadedHTTPServer.shutdown_server(self)

    def get_all_servers(self):
        return [x[0] for x in self.server_threads]

    def start_raffle_thread(self):
        '''
        Separate thread to run raffle
        '''
        self.__raffle_running = True
        self.raffle_thread = utils.run_thread(self.__raffle_thread_func)

    def __raffle_thread_func(self):
        while self.__raffle_running:
            time.sleep(config.RAFFLE_TIME)

            r = requests.get('http://'+self.servers.keys()[0]+'/chooseRaffleWinner/%f'%(random()))

            obj = utils.check_response_for_failure(r.text)
            print "Winner of Raffle is", obj.winner
            for server in self.servers.keys():
                r = requests.get('http://' + server + "/clearReqQueue")

    def end_raffle_thread(self):
        self.__raffle_running = False
        if self.is_raffle:
            self.raffle_thread.join()


if __name__ == "__main__":
    multi_thread_server.main(DispatcherHTTPServer)
