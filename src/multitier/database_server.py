import utils
import json
import threading
import urllib
import requests
import config
import prwlock
import time
import server
import database

class DatabaseHTTPServer(server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''
    def __init__(self, *args, **kwargs):
        MultiThreadedHTTPServer.__init__(self, *args, **kwargs)
        
    def join_all_threads(self):
        for thread in self.__requests_thread:
            thread.join ()
            
    def get_medal_tally_by_game_by_team(self, team=None, game=None):
        with self.rwlock.reader_lock():
            return self.teams[team].games[game]

    def get_score_by_game(self, game):
        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)

        with self.rwlock.reader_lock():
            return {team: self.teams[team].games[game] for team in self.teams}

    def get_medal_tally_by_team(self, team):
        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)

        with self.rwlock.reader_lock():
            return self.teams[team].medals

    def set_score_for_game_by_team(self, game, team, tally):
        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)

        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)

        with self.rwlock.writer_lock():
            self.teams[team].games[game] = tally

    def check_authentication(self, authID):
        if (authID != self.authID):
            raise Exception("Authentication Failed '%s'" % authID)

    def set_score_by_game(self, game, tally_rome, tally_gaul, authID):
        self.check_authentication(authID)
        tallys = [tally_gaul, tally_rome]
        for idx, team in enumerate(utils.teams):
            self.set_score_for_game_by_team(game, team, int(tallys[idx]))
        self.do_server_push(game)

    def increment_medal_tally(self, teamName, medalType, authID):
        self.check_authentication(authID)

        if teamName not in utils.teams:
            raise Exception("Invalid team '%s'" % teamName)

        if medalType not in utils.medals:
            raise Exception("Invalid Medal: '%s'" %medalType)

        self.teams[teamName].medals[medalType] += 1

if __name__ == "__main__":
    import signal
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Server')
    parser.add_argument('-p', '--port', type=int, help='Port number', required=True)
    args = parser.parse_args()

    httpd = server.create_server(DatabaseHTTPServer, 
                                 server.ServerRequestHandler, args.port)

    def signal_handler(signal, frame):
        '''Signal handler for SIGINT. Joins all request threads and 
           close server socket before exiting.
        '''
        print "Shutting down server"
        print "Number of pushupdate requests made", httpd.n_push_requests
        if httpd.n_push_requests != 0:
            print "Time taken to handle each push request", float(httpd.push_request_time)/httpd.n_push_requests
        httpd.join_all_threads()
        httpd.socket.close()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    print "Running HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever()
