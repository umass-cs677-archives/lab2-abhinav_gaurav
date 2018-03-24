import sys
import requests
import time
import random
import utils


class Client():
    """

    """

    def __init__(self, server_ip_address, server_port):
        self.dispatcher_ip = server_ip_address
        self.dispatcher_port = server_port
        self.dispatcher_address = utils.create_address(server_ip_address, server_port)
        self.server_address = ""
        self.periodic_running = False
        self.sleeping_time = 5
        self.periodic_thread = None
        
    def getMedalTally(self, team, to_print=True):
        self.getServer ()
        if team not in utils.teams:
            raise Exception("Invalid team name '%s'" % team)

        r = requests.get(self.server_address + '/getMedalTally/' + team)
        return self.parse_getmedaltally_response(r.text, to_print)

    def getScore(self, eventType, to_print=True):
        self.getServer ()
        if eventType not in utils.games:
            raise Exception("Invalid event type '%s'" % eventType)

        r = requests.get(self.server_address + '/getScore/' + eventType)
        return self.parse_getscore_response(r.text, to_print)
    
    def getServer(self):
        if (self.server_address != ""):
            return
        
        r = requests.get(self.dispatcher_address + '/getServer')
        obj = utils.check_response_for_failure (r.text)
        self.server_address = obj.server
        print "Server Address obtained", self.server_address
        
    def releaseServer(self):
        if (self.server_address == ""):
            print "Server not registered"
            return
        
        r = requests.get(self.dispatcher_address + '/releaseServer/'+self.server_address)
        utils.check_response_for_failure (r.text)
        self.server_address = ""
        
    def parse_getmedaltally_response(self, response, to_print):
        """
        Parses server's response to the GET API and prints only in debug mode.
        """
        obj = utils.check_response_for_failure(response)

        if to_print:
            print "Medals:"
            for medal in utils.medals:
                print medal, "= ", getattr(obj.medals, medal)

        return obj

    def parse_getscore_response(self, response, to_print):
        """
            Parses server's response to the GET API and prints only in debug mode.
        """
        obj = utils.check_response_for_failure(response)

        if to_print:
            print "Score:"
            for team in utils.teams:
                if hasattr(obj.scores, team):
                    print team, ":", getattr(obj.scores, team)

        return obj

    def evaluate(self, n_requests, request_delay):
        """
        Performance benchmarking for client-pull

        :param n_requests: number of requests to hit the server
        :param request_delay: delay in each request
        """
        i = 0
        getScore_time = 0
        while i < n_requests:
            game = random.sample(utils.games, 1)[0]
            time.sleep(request_delay)
            t, r = utils.timeit(self.getScore, game, False)
            getScore_time += t
            i += 1

        getMedalTally_time = 0
        i = 0
        while i < n_requests:
            team = random.sample(utils.teams, 1)[0]
            time.sleep(request_delay)
            medal_type = random.sample(utils.medals, 1)[0]
            t, r = utils.timeit(self.getMedalTally, team, False)
            getMedalTally_time += t
            i += 1

        print "Time taken to perform %d getScore requests:" % n_requests, getScore_time
        print "Time taken to perform each getScore request:", float(getScore_time) / n_requests
        print "Time taken to perform %d getMedalTally_time requests:" % n_requests, getMedalTally_time
        print "Time taken to perform each getMedalTally request:", float(getMedalTally_time) / n_requests

    def start_periodic_do(self):
        self.periodic_running = True
        self.sleeping_time = 5
        self.periodic_thread = utils.run_thread (Client._periodic_do_fun, self)
        
    def _periodic_do_fun(self):
        while self.periodic_running:
            for team in utils.teams:
                print "Getting Medal Tally for", team
                self.getMedalTally(team)
            
            for event in utils.games:
                print "Getting Score for", game
                self.getScore(event)
            
            time.sleep (self.sleeping_time)
            
    def end_periodic_do (self):
        self.periodic_running = False
        self.periodic_thread.join()
        
    def do(self):
        while True:
            print ('-----------------')
            print ('Select from following choices:\n')
            print ('1. getMedalTally')
            print ('2. getScore')

            choice = int(raw_input('Enter Choice (1 or 2):'))
            if (choice == 1):
                team = raw_input("Enter team name (%s)" % (str(utils.teams)) + ":")
                try:
                    self.getMedalTally(team)
                except Exception as e:
                    print e

            elif (choice == 2):
                eventType = raw_input("Enter event type (%s)" % (str(utils.games)) + ":")
                try:
                    self.getScore(eventType)
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

    server_ip_address = args.server_ip_addr
    server_port = args.server_port
    client = Client(server_ip_address, server_port)

    if args.num_requests is not None and args.request_delay is not None:
        try:
            n_requests = args.num_requests
            request_delay = args.request_delay
            client.evaluate(n_requests, request_delay)
            sys.exit(0)
        except Exception as e:
            print "Provide number of requests and delay parameter in integer with -evaluate"
            print e

    client.periodic_do ()
    
    def signal_handler(signal, frame):
        '''Signal handler for SIGINT. Joins all request threads and 
           close server socket before exiting.
        '''
        print "Shutting down client"
        client.end_periodic_do ()
        print "Client shutdown"
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)

    client.do()
