import utils
import json
import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urllib
import config
import prwlock


class ServerRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        """
        Overridden function of BaseHTTPRequestHandler.
        Processes every HTTP GET request.
        :return:
        """
        self._set_headers()
        self.wfile.write(self.server.call_request_handler(urllib.unquote(self.path), self.request))

class MultiThreadedHTTPServer(HTTPServer):
    def __init__(self, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)
        self.teams = {team: Team(team, utils.games) for team in utils.teams}  # utils.teams to utils.teams_names
        self.registered_clients = {}  # dictionary of eventType to list of registered clients
        self.authID = config.AUTH_ID
        self.rwlock = prwlock.RWLock()
        self.register_client_rwlock = prwlock.RWLock()
        self.__requests_thread = []
        self.push_request_time = 0
        self.n_push_requests = 0
        
    def join_all_threads(self):
        for thread in self.__requests_thread:
            thread.join ()
        
    def process_request_thread(self, request, client_address):
        """
        The method that every thread executes.
        Calls finish_request, shutdown_request and handle_error of HTTPServer.

        :return: void
        """
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        """
        Overridden method of SocketServer from which HTTPServer derives.
        Runs a thread for each request and appends the thread in list.

        :return: void
        """
        t = threading.Thread(target=self.process_request_thread,
                             args=(request, client_address))
        t.start()
        self.__requests_thread.append(t)
        
    def call_request_handler(self, path, request):
        
        try:
            meth, args = self.parse_request_path(path)
            return meth(*args)
        except Exception as e:
            return json.dumps({"response": "failure", "message": str(e)})

    def parse_request_path(self, path):
        '''Finds and the appropriate method for given request.
           For example, for `getScore' request, this method will parse 
           the request path, get all arguments, and
           call the getScore method with all arguments. This method use
           reflection for finding the appropriate method.
        '''
        # Parses request path and returns the method to be called with the arguments
        path_split = path.split('/')
        if (path_split[0] == ''):
            path_split = path_split[1:]
        if (path_split[-1] == ''):
            path_split = path_split[:-1]
        request = path_split[0]

        try:
            request_method = getattr(self, request)
        except AttributeError:
            raise Exception("Invalid Request '%s'" % request)

        args = path_split[1:]

        return (request_method, args)

#~ class MultiThreadedHTTPServer(MultiThreadedHTTPServer):
    #~ '''Mult-Threaded HTTP Server to handle several client requests
       #~ concurrently.
    #~ '''
    #~ def __init__(self, *args, **kwargs):
        #~ HTTPServer.__init__(self, *args, **kwargs)
        #~ self.teams = {team: Team(team, utils.games) for team in utils.teams}  # utils.teams to utils.teams_names
        #~ self.registered_clients = {}  # dictionary of eventType to list of registered clients
        #~ self.authID = config.AUTH_ID
        #~ self.rwlock = prwlock.RWLock()
        #~ self.register_client_rwlock = prwlock.RWLock()
        #~ self.__requests_thread = []
        #~ self.push_request_time = 0
        #~ self.n_push_requests = 0

    #~ def registerClient(self, clientID, eventType):
        #~ if eventType not in utils.games:
            #~ raise Exception("Event '%s' not supported" % (eventType))
        #~ with self.register_client_rwlock.writer_lock ():
            #~ if eventType not in self.registered_clients:
                #~ self.registered_clients[eventType] = []
                
            #~ self.registered_clients[eventType].append(clientID)
            
        #~ return json.dumps({"response":"success"})
        
    #~ def do_server_push(self, eventType):
        #~ '''Called when score is set for a team and a game.
           #~ Sends pushUpdate request to all registered clients.
        #~ '''
        #~ if eventType not in self.registered_clients:
            #~ return
        
        #~ with self.rwlock.reader_lock():
            #~ t1 = time.clock ()
            #~ request_str = '/pushUpdate/' + eventType
            #~ for team in self.teams:
                #~ request_str += '/' + team + '/' + str(self.teams[team].games[eventType])

            #~ for client in self.registered_clients[eventType]:
                #~ r = requests.get('http://' + client + request_str)
            
            #~ t = time.clock () - t1
            #~ self.push_request_time += t
            #~ self.n_push_requests += 1
            
    #~ def get_medal_tally_by_game_by_team(self, team=None, game=None):
        #~ with self.rwlock.reader_lock():
            #~ return self.teams[team].games[game]

    #~ def get_score_by_game(self, game):
        #~ if game not in utils.games:
            #~ raise Exception("Invalid game '%s'" % game)

        #~ with self.rwlock.reader_lock():
            #~ return {team: self.teams[team].games[game] for team in self.teams}

    #~ def get_medal_tally_by_team(self, team):
        #~ if team not in utils.teams:
            #~ raise Exception("Invalid team '%s'" % team)

        #~ with self.rwlock.reader_lock():
            #~ return self.teams[team].medals

    #~ def set_score_for_game_by_team(self, game, team, tally):
        #~ if team not in utils.teams:
            #~ raise Exception("Invalid team '%s'" % team)

        #~ if game not in utils.games:
            #~ raise Exception("Invalid game '%s'" % game)

        #~ with self.rwlock.writer_lock():
            #~ self.teams[team].games[game] = tally

    #~ def check_authentication(self, authID):
        #~ if (authID != self.authID):
            #~ raise Exception("Authentication Failed '%s'" % authID)

    #~ def set_score_by_game(self, game, tally_rome, tally_gaul, authID):
        #~ self.check_authentication(authID)
        #~ tallys = [tally_gaul, tally_rome]
        #~ for idx, team in enumerate(utils.teams):
            #~ self.set_score_for_game_by_team(game, team, int(tallys[idx]))
        #~ self.do_server_push(game)

    #~ def getMedalTally(self, teamName):
        #~ medalTally = self.get_medal_tally_by_team(teamName)
        #~ response = {"response": "success", "medals": medalTally}
        #~ return json.dumps(response)

    #~ def increment_medal_tally(self, teamName, medalType, authID):
        #~ self.check_authentication(authID)

        #~ if teamName not in utils.teams:
            #~ raise Exception("Invalid team '%s'" % teamName)

        #~ if medalType not in utils.medals:
            #~ raise Exception("Invalid Medal: '%s'" %medalType)

        #~ self.teams[teamName].medals[medalType] += 1

    #~ def incrementMedalTally(self, teamName, medalType, authID):
        #~ self.increment_medal_tally(teamName, medalType, authID)
        #~ return json.dumps({"response": "success"})

    #~ def getScore(self, eventType):
        #~ sc = self.get_score_by_game(eventType)
        #~ response = {"response": "success", "scores": sc}
        #~ return json.dumps(response)

    #~ def setScore(self, eventType, romeScore, gaulScore, authId):
        #~ self.set_score_by_game(eventType, romeScore, gaulScore, authId)
        #~ return json.dumps({"response": "success"})


def create_server(server_class, handler_class, port):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    return httpd

def create_and_run_server(server_class, handler_class, port):
    ''' Create and Run server in another thread.
        Returns the (server object, thread)
    '''
    httpd = create_server(server_class, handler_class, args.port)
    th = run_thread (HTTPServer.serve_forever(), http)
    return (httpd, th)

def parse_command_line_args (desc):
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port', type=int, help='Port number', required=True)
    return parser.parse_args()

def main (serverclass):
    import signal
    import argparse
    import sys
    
    args = parse_command_line_args("Server")
    httpd = create_server(serverclass, ServerRequestHandler, args.port)

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
    
if __name__ == "__main__":
    main (serverclass=MultiThreadedHTTPServer)
