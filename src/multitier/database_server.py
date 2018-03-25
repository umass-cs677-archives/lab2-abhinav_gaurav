import utils
import json
import prwlock
import server


def write_data(fname, data):
    """
    Write the data to json file.
    :param fname: The filename.
    :param data: The data that needs to be written.
    :return:
    """
    with open(fname, 'w') as outfile:
        json.dump(data, outfile)


def read_data(fname):
    """
    Reads a json file.
    :param fname: The name of the file to read.
    :return: json
    """
    data = json.load(open('data/'+ fname))
    return data


class DatabaseHTTPServer(server.MultiThreadedHTTPServer):
    '''Multi-Threaded Database HTTP Server to handle several client requests
       concurrently.
    '''
    def __init__(self, *args, **kwargs):
        server.__init__(self, *args, **kwargs)
        self.team_locks = {team: prwlock.RWLock() for team in utils.teams}
        self.game_locks = {game: prwlock.RWLock() for game in utils.games}

    def join_all_threads(self):
        for thread in self.__requests_thread:
            thread.join ()

    def query_score_by_game(self, game):
        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)

        lock = self.game_locks[game]
        with lock.reader_lock():
            return read_data(fname = game + '_score.json')
            # return {team: self.teams[team].games[game] for team in self.teams}

    def query_medal_tally_by_team(self, team):
        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)

        lock = self.team_locks[team]
        with lock.reader_lock():
            return read_data(team + '_medal.json')
            # return self.teams[team].medals

    def check_authentication(self, authID):
        if (authID != self.authID):
            raise Exception("Authentication Failed '%s'" % authID)

    def update_score_by_game(self, game, tally_rome, tally_gaul, authID):
        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)

        self.check_authentication(authID)
        tallys = [tally_gaul, tally_rome]

        lock = self.game_locks[game]
        with lock.writer_lock():
            for idx, team in enumerate(utils.teams):
                self.teams[team].games[game] = tallys[idx]
            write_data(fname = game+'_score.json', {team: self.teams[team].games[game] for team in utils.teams})


    def update_increment_medal_tally(self, team, medalType, authID):
        self.check_authentication(authID)

        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)

        if medalType not in utils.medals:
            raise Exception("Invalid Medal: '%s'" %medalType)

        lock = self.team_locks[team]
        with lock.writer_lock():
            self.teams[team].medals[medalType] += 1
            write_data(fname = team+'_medal.json', {game: self.medals[game] for game in utils.games})


if __name__ == "__main__":
    import signal
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Databse Server')
    parser.add_argument('-p', '--port', type=int, default=6000, help='Port number')
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

