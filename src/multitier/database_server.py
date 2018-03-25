import sys
sys.path.insert (0, "../")

import utils
import json
import prwlock
<<<<<<< HEAD
import server

=======
import time
import team
import multi_thread_server
import os
>>>>>>> cdf39e6bb56c09fd8c774f4037818cb1e1e2a20a

data_dir = "data/"
def write_data(fname, data):
    """
    Write the data to json file.
    :param fname: The filename.
    :param data: The data that needs to be written.
    :return:
    """
    with open(os.path.join (data_dir, fname), 'w') as outfile:
        json.dump(data, outfile)


def read_data(fname):
    """
    Reads a json file.
    :param fname: The name of the file to read.
    :return: json
    """
    data = json.load(open(os.path.join (data_dir, fname)))
    return data


class DatabaseHTTPServer(multi_thread_server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''
    def __init__(self, *args, **kwargs):
        multi_thread_server.MultiThreadedHTTPServer.__init__(self, *args, **kwargs)
        self.teams = {_team: team.Team(_team, utils.games) for _team in utils.teams}
        self.team_locks = {team: prwlock.RWLock() for team in utils.teams}
        self.game_locks = {game: prwlock.RWLock() for game in utils.games}
        if not os.path.exists (data_dir):
          os.makedirs (data_dir)
        
    def join_all_threads(self):
        for thread in self.__requests_thread:
            thread.join ()

    def query_score_by_game(self, game):
        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)

        lock = self.game_locks[game]
        with lock.reader_lock():
            sc = {team: self.teams[team].games[game] for team in self.teams}
            return json.dumps({"response":"success", "scores":sc})

    def query_medal_tally_by_team(self, team):
        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)
        
        lock = self.team_locks[team]
        with lock.reader_lock():
            return json.dumps({"response":"success", "medals":self.teams[team].medals})

    def update_score_by_game(self, game, tally_rome, tally_gaul, authID):
        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)

        self.check_authentication(authID)
        tallys = [tally_gaul, tally_rome]

        lock = self.game_locks[game]
        with lock.writer_lock():
            for idx, team in enumerate(utils.teams):
                self.teams[team].games[game] = tallys[idx]
            write_data(game+'_score.json', {team: self.teams[team].games[game] for team in utils.teams})
        
        return json.dumps({"response":"success"})

    def increment_medal_tally(self, team, medalType, authID):
        self.check_authentication(authID)

        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)

        if medalType not in utils.medals:
            raise Exception("Invalid Medal: '%s'" %medalType)

        lock = self.team_locks[team]
        with lock.writer_lock():
            self.teams[team].medals[medalType] += 1
            write_data(team+'_medal.json', {game: self.medals[game] for game in utils.games})
        
        return json.dumps({"response":"success"})

if __name__ == "__main__":
    import signal
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Database Server')
    parser.add_argument('-p', '--port', type=int, default=6000, help='Port number')
    args = parser.parse_args()

    httpd = multi_thread_server.create_server(DatabaseHTTPServer, 
                                              multi_thread_server.ServerRequestHandler, args.port)

    def signal_handler(signal, frame):
        '''Signal handler for SIGINT. Joins all request threads and 
           close server socket before exiting.
        '''
        print "Shutting down server"
        httpd.join_all_threads()
        httpd.socket.close()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    print "Running HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever()

