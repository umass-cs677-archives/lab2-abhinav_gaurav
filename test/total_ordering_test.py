import unittest
import time

from ..src.multitier.dispatcher import DispatcherHTTPServer
from ..src.server import MultiThreadedFrontEndServer, ServerRequestHandler
from ..src.multi_thread_server import create_and_run_server
from ..src.client_pull import Client
from ..src import utils as utils
from ..src import config as config

class TestTotalOrdering(unittest.TestCase):
    """
    Class that tests whether server is multi-threaded or not.
    """

    def setUp(self):
        self.n_servers = 2
        self.server, self.server_thread = create_and_run_server(DispatcherHTTPServer, ServerRequestHandler,
                          config.DISPATCHER_PORT,
                          MultiThreadedFrontEndServer, config.FRONT_END_PORT,
                          "127.0.0.1", config.DATABASE_PORT,
                          "127.0.0.1", self.n_servers, False, False, True, False)
        self.clients = []
        
        for i in range(self.n_servers):
            self.clients.append(Client("127.0.0.1", "5000"))

    def __start_clients(self):
        ''' Do not place this function in setUp.'''
        for i in range(self.n_servers):
            self.clients[i].start_periodic_do(False)
    
    def test_total_ordering(self):
        self.__start_clients()
        time.sleep(2)
        self.__end_clients()
        self.server.shutdown()
        self.server.shutdown_server()
        self.front_end_servers = self.server.get_all_servers ()
        print '-----------------------------------'
        print 'front end servers', self.front_end_servers
        for server in self.front_end_servers:
            print "server", server.get_all_processed_reqs()
        #TODO: @Gaurav, write code to check that all the lists returned from
        #server.get_all_processed_reqs() (defined in TotalOrder class) are same
    def __end_clients(self):
        '''Do not place this function in tearDown.'''
        for i in range(self.n_servers):
            self.clients[i].end_periodic_do()
        
    #def tearDown(self):
    #    self.server.shutdown()
    #    self.server.shutdown_server()

if __name__ == '__main__':
    unittest.main()
