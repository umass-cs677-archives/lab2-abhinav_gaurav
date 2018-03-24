import unittest
import time

from ..src.server import MultiThreadedHTTPServer, ServerRequestHandler, create_server
from ..src.client_pull import Client
from ..src.client_receive import ServerPushClientHTTPServer, ServerPushClientRequestHandler, create_client
from ..src.cacofonix import Cacofonix
from ..src import utils as utils

from utils import run_thread


class BasicTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(MultiThreadedHTTPServer, ServerRequestHandler, 5000)
        self.server_thread = run_thread(self.server.serve_forever)
        self.cacofonix = Cacofonix("127.0.0.1", "5000")
        self.client = Client("127.0.0.1", "5000")

    def test_medal_tally_incr_and_get(self):
        '''Test incrementalMedalTally and getMedalTally requests
        '''
        self.cacofonix.incrementMedalTally(utils.teams[0], utils.medals[0])
        medals = self.client.getMedalTally(utils.teams[0])
        self.assertTrue(getattr(medals.medals, utils.medals[0]) == 1)

    def test_score_get_and_set(self):
        '''Test getScore and setScore requests
        '''
        self.cacofonix.setScore(utils.games[0], "5", "11")
        scores = self.client.getScore(utils.games[0]).scores
        for team in utils.teams:
            self.assertTrue(hasattr(scores, team))

        self.assertTrue(getattr(scores, "Gaul") == 11)
        self.assertTrue(getattr(scores, "Rome") == 5)

    def test_server_push(self):
        '''Test registerClient and pushUpdate request of client
        '''
        self.client_receive = create_client(ServerPushClientHTTPServer, 
                                            ServerPushClientRequestHandler,
                                            utils.games,
                                            "127.0.0.1", "5000", 
                                            "127.0.0.1", 4000)
        self.client_receive.register_with_server()
        client_thread = run_thread (self.client_receive.serve_forever)
        self.cacofonix.setScore(utils.games[0], "5", "11")
        time.sleep(1)
        self.assertTrue(self.client_receive.record["Rome"].games[utils.games[0]] == "5")
        self.assertTrue(self.client_receive.record["Gaul"].games[utils.games[0]] == "11")
        self.client_receive.shutdown ()
        
    def tearDown(self):
        self.server.shutdown()
        self.server.socket.close()
        self.server_thread.join()
        self.cacofonix = None
        self.client = None


if __name__ == '__main__':
    unittest.main()
