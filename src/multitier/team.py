class Team:
    '''Team class stores medal tally and score of each game for a given 
       team
    '''
    def __init__(self, name, games):
        assert type(name) == str, "Not a string" + str(type(name))

        self.medals = {medal:0 for medal in utils.medals}
        self.games = dict(zip(games, [0] * len(games)))

    def set(self, score, game):
        self.games[game] = int(score)
