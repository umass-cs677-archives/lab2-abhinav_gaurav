import utils


class Team:
    '''Team class stores medal tally and score of each game for a given 
       team
    '''

    def __init__(self, name, games):
        assert type(name) == str, "Not a string" + str(type(name))

        self.medals = {medal: 0 for medal in utils.medals}
        self.games = dict(zip(games, [0] * len(games)))
        self.games_time = dict(zip(games, [0] * len(games)))
        self.medals_time = {medal: 0 for medal in utils.medals}

    def set_game_score(self, score, game, time):
        self.games[game] = int(score)
        self.games_time[game] = time

    def increment_medal_tally(self, medalType, time):
        self.medals_time[medalType] = time
        self.medals[medalType] += 1
