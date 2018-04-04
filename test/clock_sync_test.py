import unittest

from ..src.multitier.dispatcher import DispatcherHTTPServer
from ..src.server import MultiThreadedFrontEndServer, ServerRequestHandler
from ..src.database_server import DatabaseHTTPServer
from ..src.multi_thread_server import create_and_run_server
from ..src import config as config
from random import randint

class TestTotalOrdering(unittest.TestCase):
    """
    Class that tests whether server is multi-threaded or not.
    """
    
    def test_clock_sync(self):
        '''Test clock synchronization by randomly assigning offsets less than
        DELTA, then performing 10 iterations of clock synchronization by server and
        itself. At the end checks if the clocks after synchronization are correct
        and the drift between each of the clocks is less than DELTA
        '''
        self.n_servers = 2
        self.server, self.server_thread = create_and_run_server(DispatcherHTTPServer, ServerRequestHandler,
                          config.DISPATCHER_PORT,
                          MultiThreadedFrontEndServer, config.FRONT_END_PORT,
                          "127.0.0.1", config.DATABASE_PORT,
                          "127.0.0.1", self.n_servers, False, True, False, False)
        self.clients = []
        self.db_server, self.db_thread = create_and_run_server(DatabaseHTTPServer, ServerRequestHandler, config.DATABASE_PORT,
                          "127.0.0.1" + ":" + str(config.DISPATCHER_PORT))
        
        
        front_end_servers = self.server.get_all_servers () + [self.db_server]
        initial_offsets = [randint(1,config.DELTA) for i in front_end_servers]
        curr_offsets = initial_offsets
        for i, server in enumerate(front_end_servers):
            server.set_current_time_offset(initial_offsets[i])
        #perform n iterations of clock sync and check the result after each
        #iteration
        front_end_servers[0].set_leader (False)
        it = 0
        while it < 10:
            front_end_servers[0].perform_clock_sync_func ()
            off_sum = 0
            for off in initial_offsets:
                off_sum += off - initial_offsets[0]
                
            avg_offset = off_sum/len(initial_offsets)
            for i, off in enumerate(curr_offsets):
                curr_offsets[i] = avg_offset - initial_offsets[i]
                
            it += 1
        
        for i, x in enumerate(curr_offsets):
            self.assertTrue (front_end_servers[i].get_current_time_offset () == x)
        
        for i1, x1 in enumerate(curr_offsets):
            for i2, x2 in enumerate(curr_offsets):
                self.assertTrue (abs(x1 - x2) <= config.DELTA)
            
        self.server.shutdown()
        self.server.shutdown_server()
        self.db_server.shutdown()
        self.db_thread.join()
        
    #def tearDown(self):
    #    self.server.shutdown()
    #    self.server.shutdown_server()

if __name__ == '__main__':
    unittest.main()
