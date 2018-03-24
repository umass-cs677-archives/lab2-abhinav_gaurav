import unittest
import time

from ..src.server import MultiThreadedHTTPServer, ServerRequestHandler, create_server

from ..src.client_pull import Client
from ..src import utils as utils

from utils import run_thread


class DelayedMultiThreadedServer(MultiThreadedHTTPServer):
    def call_request_handler(self, path, request):
        if path.startswith('/getScore'):
            time.sleep(2)
        return MultiThreadedHTTPServer.call_request_handler(self, path, request)


class TestMultiThreading(unittest.TestCase):
    """
    Class that tests whether server is multi-threaded or not.
    """

    def setUp(self):
        self.server = create_server(DelayedMultiThreadedServer, ServerRequestHandler, 5000)
        self.server_thread = run_thread(self.server.serve_forever)
        self.client = Client("127.0.0.1", "5000")

    def test_multi_threaded(self):
        """
        Overrides one method of server and delays its execution. Meanwhile send other request and see
        if they are responded by server or not.
        """
        t1 = run_thread(self.client.getScore, utils.games[0])
        t2 = run_thread(self.client.getMedalTally, utils.teams[0])

        """
        If the server is multi threaded then t2 will finish early.
        Let t2 finish but t1 won't finish before 2 second
        """
        t2.join()

        while t1.is_alive():
            self.assertTrue(t1.is_alive() == True and t2.is_alive() == False)
            time.sleep(0.7)

        t1.join()

    def tearDown(self):
        self.server.shutdown()


if __name__ == '__main__':
    unittest.main()
