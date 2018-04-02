import sys

sys.path.insert(0, "../")

import utils
import json
import prwlock
import time
import team
import multi_thread_server
import os

data_dir = "data/"


def write_data(fname, data):
    """
    Write the data to json file.
    :param fname: The filename.
    :param data: The data that needs to be written.
    :return:
    """
    with open(os.path.join(data_dir, fname), 'w') as outfile:
        json.dump(data, outfile)


def read_data(fname):
    """
    Reads a json file.
    :param fname: The name of the file to read.
    :return: json
    """
    data = json.load(open(os.path.join(data_dir, fname)))
    return data


class Database:
    '''Database '''

    def __init__(self):
        self.teams = {_team: team.Team(_team, utils.games) for _team in utils.teams}
        self.team_locks = {team: prwlock.RWLock() for team in utils.teams}
        self.game_locks = {game: prwlock.RWLock() for game in utils.games}
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        self.number_of_requests = 0
        # TODO: Read data again if there are files and databse server is restarted

    def join_all_threads(self):
        for thread in self.__requests_thread:
            thread.join()

    def query_score_by_game(self, game):
        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)
        print "TODO: Write file if not there"
        lock = self.game_locks[game]
        with lock.reader_lock():
            sc = {team: self.teams[team].games[game] for team in self.teams}
            return json.dumps({"response": "success", "scores": sc,
                               "time": {team: self.teams[team].games_time[game] for team in utils.teams}})

    def query_medal_tally_by_team(self, team):
        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)

        lock = self.team_locks[team]
        with lock.reader_lock():
            return json.dumps({"response": "success", "medals": self.teams[team].medals,
                               "time": {medalType: self.teams[team].medals_time[medalType] for medalType in
                                        utils.medals}})

    def update_score_by_game(self, game, tally_rome, tally_gaul, authID, time):
        if game not in utils.games:
            raise Exception("Invalid game '%s'" % game)

        self.check_authentication(authID)
        tallys = [tally_gaul, tally_rome]

        lock = self.game_locks[game]
        with lock.writer_lock():
            for idx, team in enumerate(utils.teams):
                self.teams[team].set_game_score(tallys[idx], game, time)

            write_data(game + '_score.json', [{team: self.teams[team].games[game] for team in utils.teams},
                                              {team: self.teams[team].games_time[game] for team in utils.teams}])

        return json.dumps({"response": "success"})

    def increment_medal_tally(self, team, medalType, authID, time):
        self.check_authentication(authID)

        if team not in utils.teams:
            raise Exception("Invalid team '%s'" % team)

        if medalType not in utils.medals:
            raise Exception("Invalid Medal: '%s'" % medalType)

        lock = self.team_locks[team]
        with lock.writer_lock():
            self.teams[team].increment_medal_tally(medalType, time)
            write_data(team + '_medal.json', [{medal: self.teams[team].medals[medal] for medal in utils.medals},
                                              {medal: self.teams[team].medals_time[medal] for medal in utils.medals}])

        return json.dumps({"response": "success"})
