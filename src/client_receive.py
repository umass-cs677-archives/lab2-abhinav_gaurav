import requests
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from server import Team
import utils


def get_open_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class ServerPushClientRequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.server.parse_response(self.path)


class ServerPushClientHTTPServer(HTTPServer):
    def __init__(self, server_ip_address, server_port,
                 eventTypes, client_ip, port, *args, **kwargs):
        HTTPServer.__init__(self, *args, **kwargs)

        self.client_id = client_ip + ":" + str(port)
        self.eventTypes = eventTypes
        self.updates = []
        self.server_ip_address = server_ip_address
        self.server_port = server_port
        self.server_address = utils.create_address(server_ip_address, server_port)
        self.record = {team: Team(team, utils.games) for team in utils.teams}

    def register_with_server(self):
        """
        In server-push client needs to register with the server.
        Client hits the server to register it's ip_addr, port, events.
        """
        for event in self.eventTypes:
            r = requests.get(self.server_address + '/registerClient/' + self.client_id + '/' + event)
            obj = utils.check_response_for_failure(r.text)
            print "Registered for event", event

    def parse_response(self, path):
        """
        Parse and print the HTTP response from server.
        """
        path_split = path.split('/')
        if path_split[0] == '':
            path_split = path_split[1:]

        game = path_split[1]
        print "Scores Updated for event", game
        i = 2
        while i < len(path_split):
            team = path_split[i]
            score = path_split[i + 1]
            print "%s: %s" % (team, score)
            self.record[team].games[game] = score
            i += 2


def create_client(server_class, handler_class, events, server_ip_address, 
                  server_port, client_ip, port):
    server_address = ('', port)

    print ('-----------------')
    if events == []:
        print ('Select choice for event type for which client wants to get the notification:\n')
        for idx, game in enumerate(utils.games):
            print '"' + str(idx) + '.', game + '"'
        choice = int(raw_input('Enter Choice (0 or 1 or 2):'))
        events = [utils.games[choice]]

    httpd = server_class(server_ip_address, server_port,
                         events, client_ip, port, 
                         server_address, handler_class)
    return httpd
    
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Client Pull')
    parser.add_argument('--server_ip_addr', type=str, help='Server IP Address', required=True)
    parser.add_argument('--server_port', type=int, help='Server port number', required=True)
    parser.add_argument('--client_ip_addr', type=str, help='Client IP Address', required=True)
    parser.add_argument('--client_port', type=int, default=4000, help='Client IP Address')
    parser.add_argument('--events', nargs='+', help='List of events to subscribe to', default=utils.games)

    args = parser.parse_args()

    server_ip_address = args.server_ip_addr
    server_port = args.server_port
    client_ip = args.client_ip_addr
    client_port = args.client_port
    events = args.events

    httpd = create_client(ServerPushClientHTTPServer, ServerPushClientRequestHandler,
                  events, server_ip_address, server_port, client_ip, client_port)
    httpd.register_with_server()
    print 'Client and Listening for Server Requests'
    httpd.serve_forever()
