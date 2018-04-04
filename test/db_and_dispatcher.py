import unittest
import random

from ..src.server import MultiThreadedFrontEndServer, ServerRequestHandler, create_server
from ..src.multi_thread_server import create_and_run_server
from ..src.multitier.dispatcher import DispatcherHTTPServer
from ..src.database_server import DatabaseHTTPServer
from ..src.client_pull import Client
from ..src.cacofonix import Cacofonix
from ..src import config as config
from ..src import utils as utils
from ..src.multitier.team import Team


class DatabaseAndDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.n_servers = 2
        self.server, self.server_thread = create_and_run_server(DispatcherHTTPServer, ServerRequestHandler,
                                                                config.DISPATCHER_PORT,
                                                                MultiThreadedFrontEndServer, config.FRONT_END_PORT,
                                                                "127.0.0.1", config.DATABASE_PORT,
                                                                "127.0.0.1", self.n_servers,
                                                                False, True, False, False)
        self.clients = []

        for i in range(self.n_servers):
            self.clients.append(Client("127.0.0.1", "5000"))

        self.teams = {team: Team(team, utils.games) for team in utils.teams}
        self.cacofonix = Cacofonix("127.0.0.1", "5000")
        self.db_server, self.db_thread = create_and_run_server(DatabaseHTTPServer, ServerRequestHandler, config.DATABASE_PORT,
                          "127.0.0.1" + ":" + str(config.DISPATCHER_PORT))

    def test_database_locking(self):
        '''
        Test to check if database implements locking or not. Is there any race-condition?
        '''
        self.front_end_servers = self.server.get_all_servers()

        t = []
        for i in range(100):
            team = random.sample(utils.teams, 1)[0]
            medal_type = random.sample(utils.medals, 1)[0]

            # update cacofinix's state
            self.teams[team].medals[medal_type] += 1

            # API call to update server
            q = utils.run_thread(self.cacofonix.incrementMedalTally, team, medal_type)
            t.append(q)

        # join threads
        for _t in t:
            _t.join()

        for team in utils.teams:
            print "Test case data", self.teams[team].medals
            response = self.front_end_servers[0].getMedalTally(team)
            obj = utils.check_response_for_failure(response)
            print "Received from server", obj.medals
            for key in self.teams[team].medals.keys():
                #rint getattr(obj.medals, key), self.teams[team].medals[key], key
                self.assertTrue(getattr(obj.medals, key) == self.teams[team].medals[key])

    def test_cacofonix_to_client(self):
        '''
        This tests the basic functionality of the application.
        We send update from cacofonix and test at the client.
        '''
        self.cacofonix.setScore(utils.games[0], "5", "11")
        scores = self.clients[0].getScore(utils.games[0]).scores
        for team in utils.teams:
            self.assertTrue(hasattr(scores, team))

        self.assertTrue(getattr(scores, "Gaul") == 11)
        self.assertTrue(getattr(scores, "Rome") == 5)

    def test_load_balancing(self):
        '''
        Test if there is load balancing or not.
        We add more clients and see if they are distributed among front-end servers or not.
        '''

        self.front_end_servers = self.server.get_all_servers()

        [client.getServer() for client in self.clients]
        for idx, server in enumerate(self.front_end_servers):
            print "The load on :", idx, server.get_load(), "Expected load:", len(self.clients)/self.n_servers


        # increase clients hence load
        for i in range(self.n_servers):
            self.clients.append(Client("127.0.0.1", "5000"))
        [client.getServer() for client in self.clients]
        for idx, server in enumerate(self.front_end_servers):
            print "The load on :", idx, server.get_load(), "Expected load:", len(self.clients) / self.n_servers
            self.assertTrue(server.get_load() == len(self.clients) / self.n_servers)

        # increase clients hence load
        for i in range(self.n_servers):
            self.clients.append(Client("127.0.0.1", "5000"))
        [client.getServer() for client in self.clients]
        for idx, server in enumerate(self.front_end_servers):
            print "The load on :", idx, server.get_load(), "Expected load:", len(self.clients) / self.n_servers
            self.assertTrue(server.get_load() == len(self.clients) / self.n_servers)

    def tearDown(self):
        self.db_server.shutdown()
        self.db_server.socket.close()
        self.server.shutdown()
        self.server.shutdown_server()
        self.server.socket.close()
        # self.server.shutdown()
        # self.server.socket.close()
        # self.server_thread.join()
        # self.cacofonix = None
        # self.client = None


if __name__ == '__main__':
    unittest.main()
