import requests
import time

import config
import utils
import random


class Cacofonix():
    """
    Implementatin of Score updater to server
    """

    def __init__(self, server_ip_address, server_port):
        self.server_ip_address = server_ip_address
        self.server_port = server_port
        self.server_address = utils.create_address(server_ip_address, server_port)

    def setScore(self, eventType, romeScore, gaulScore, authID=config.AUTH_ID, to_print=True):
        if not romeScore.isdigit():
            raise Exception("Rome Score '%s' is not a positive integer" % (romeScore))

        if not gaulScore.isdigit():
            raise Exception("Gaul Score '%s' is not a positive integer" % (gaulScore))

        if eventType not in utils.games:
            raise Exception("Invalid team name '%s'" % eventType)

        r = requests.get(self.server_address + '/setScore/%s/%s/%s/%s' % (eventType, romeScore, gaulScore, authID))
        obj = utils.check_response_for_failure(r.text)
        if to_print:
            print "Operation Successful"
        return obj

    def incrementMedalTally(self, team, medalType, authID=config.AUTH_ID, to_print=True):
        if team not in utils.teams:
            raise Exception("Invalid Team Name '%s'" % team)

        if medalType not in utils.medals:
            raise Exception("Invalid medal type '%s'" % medalType)

        r = requests.get(self.server_address + '/incrementMedalTally/%s/%s/%s' % (team, medalType, authID))
        obj = utils.check_response_for_failure(r.text)
        if (to_print):
            print "Operation Successful"
        return obj

    def evaluate(self, n_requests, request_delay):
        """

        :param n_requests: the number of requests to hit server with
        :param request_delay: delay in each request
        :return:
        """
        i = 0
        setScore_time = 0
        while i < n_requests:
            game = random.sample(utils.games, 1)[0]
            time.sleep(request_delay)
            t, r = utils.timeit(self.setScore, game, "10", "10", to_print=False)
            setScore_time += t
            i += 1

        incrementMedalTally_time = 0
        i = 0
        while i < n_requests:
            team = random.sample(utils.teams, 1)[0]
            time.sleep(request_delay)
            medal_type = random.sample(utils.medals, 1)[0]
            t, r = utils.timeit(self.incrementMedalTally, team, medal_type, to_print=False)
            incrementMedalTally_time += t
            i += 1

        print "Time taken to perform %d setScore requests:" % n_requests, setScore_time
        print "Time taken to perform each setScore request:", float(setScore_time) / n_requests
        print "Time taken to perform %d incrementMedalTally_time requests:" % n_requests, incrementMedalTally_time
        print "Time taken to perform each incrementMedalTally request:", float(incrementMedalTally_time) / n_requests

    def do(self):
        '''Main loop of Cacofinix
        '''
        while True:
            print ('-----------------')
            print ('Select from following choices:\n')
            print ('1. setScore')
            print ('2. incrementMedalTally')

            choice = int(raw_input('Enter Choice (1 or 2):'))
            if (choice == 1):
                event = raw_input("Enter event type (%s): " % (str(utils.games)))
                romeScore = raw_input("Enter Rome Score: ")
                gaulScore = raw_input("Enter Gaul Score: ")
                try:
                    self.setScore(event, romeScore, gaulScore)
                except Exception as e:
                    print e

            elif (choice == 2):
                team = raw_input("Enter team name (%s): " % (str(utils.teams)))
                medalType = raw_input("Enter medal type (%s): " % (str(utils.medals)))
                try:
                    self.incrementMedalTally(team, medalType)
                except Exception as e:
                    print e


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Client Pull')
    parser.add_argument('--server_ip_addr', type=str, help='Server IP Address', required=True)
    parser.add_argument('--server_port', type=int, help='Server port number', required=True)
    parser.add_argument('--num_requests', type=int, help='Number of requests')
    parser.add_argument('--request_delay', type=float, help='Time delay in requests')

    args = parser.parse_args()

    cacofonix = Cacofonix(args.server_ip_addr, args.server_port)

    if args.num_requests is not None and args.request_delay is not None:
        try:
            n_requests = args.num_requests
            request_delay = args.request_delay
            cacofonix.evaluate(n_requests, request_delay)
        except Exception as e:
            print e
    else:
        cacofonix.do()
