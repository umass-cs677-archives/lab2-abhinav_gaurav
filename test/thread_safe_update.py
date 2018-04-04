import unittest
import random

from ..src.server import MultiThreadedHTTPServer, ServerRequestHandler, create_server
from ..src import utils as utils
from ..src.cacofonix import Cacofonix
from ..src.config import AUTH_ID
from ..src.server import Team
from utils import run_thread


class TestStringMethods(unittest.TestCase):
    def setUp(self):
        self.cacofinix = Cacofonix("127.0.0.1", "5000")
        self.teams = {team: Team(team, utils.games) for team in utils.teams}
        self.server = create_server(MultiThreadedHTTPServer, ServerRequestHandler, 5000)
        self.server_thread = run_thread(self.server.serve_forever)

    def test_medal_update(self):
        """
        Test if updates in server are thread safe or not i.e. is there any race-condition?
        """
        t = []
        for i in range(1000):
            team = random.sample(utils.teams, 1)[0]
            medal_type = random.sample(utils.medals, 1)[0]

            # update cacofinix's state
            self.teams[team].medals[medal_type] += 1

            # API call to update server
            q = run_thread(self.cacofinix.incrementMedalTally, team, medal_type, AUTH_ID)
            t.append(q)

        for _t in t:
            _t.join()

        for team in utils.teams:
            print "Received from server", self.server.get_medal_tally_by_team(team)
            print "Test case data", self.teams[team].medals
            self.assertTrue(self.server.get_medal_tally_by_team(team) == self.teams[team].medals)

    def tearDown(self):
        self.server.shutdown()


if __name__ == '__main__':
    unittest.main()
