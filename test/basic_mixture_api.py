import unittest
import random
# import time

from ..src.server import MultiThreadedFrontEndServer, ServerRequestHandler, create_server
from ..src.multi_thread_server import create_and_run_server
from ..src.multitier.dispatcher import DispatcherHTTPServer
from ..src.client_pull import Client
from ..src.cacofonix import Cacofonix
from ..src import config as config
from ..src import utils as utils
from ..src.multitier.team import Team


class BasicTests(unittest.TestCase):
    def setUp(self):
        self.n_servers = 2
        self.server, self.server_thread = create_and_run_server(DispatcherHTTPServer, ServerRequestHandler,
                                                                config.DISPATCHER_PORT,
                                                                MultiThreadedFrontEndServer, config.FRONT_END_PORT,
                                                                "127.0.0.1", config.DATABASE_PORT,
                                                                "127.0.0.1", self.n_servers)
        self.clients = []

        for i in range(self.n_servers):
            self.clients.append(Client("127.0.0.1", "5000"))

        self.teams = {team: Team(team, utils.games) for team in utils.teams}
        self.cacofonix = Cacofonix("127.0.0.1", "5000")
        # self.database = create_and_run_server()     #TODO run database server

    def test_database_locking(self):
        self.front_end_servers = self.server.get_all_servers()

        t = []
        for i in range(1):
            team = random.sample(utils.teams, 1)[0]
            medal_type = random.sample(utils.medals, 1)[0]

            # update cacofinix's state
            self.teams[team].medals[medal_type] += 1

            # API call to update server
            q = utils.run_thread(self.cacofonix.incrementMedalTally, team, medal_type)
            t.append(q)

        # join threads
        for _t in t:
            print 'shit', _t
            _t.join()

        for team in utils.teams:
            print "Test case data", self.teams[team].medals
            response = self.front_end_servers[0].getMedalTally(team)
            obj = utils.check_response_for_failure(response)
            print "Received from server", obj.medals
            self.assertTrue(obj.medals == self.teams[team].medals)

    def cacofonix_to_client(self):
        self.cacofonix.setScore(utils.games[0], "5", "11")
        scores = self.clients[0].getScore(utils.games[0]).scores
        for team in utils.teams:
            self.assertTrue(hasattr(scores, team))

        self.assertTrue(getattr(scores, "Gaul") == 11)
        self.assertTrue(getattr(scores, "Rome") == 5)

    def load_balancing(self):
        pass

    def tearDown(self):
        self.server.shutdown()
        self.server.shutdown_server()
        # self.server.shutdown()
        # self.server.socket.close()
        # self.server_thread.join()
        # self.cacofonix = None
        # self.client = None


if __name__ == '__main__':
    unittest.main()
