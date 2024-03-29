import utils
import threading
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import urllib
import config
import signal
import argparse


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
        self.__requests_thread = []
        self.authID = config.AUTH_ID

    def check_authentication(self, authID):
        if (authID != self.authID):
            raise Exception("Authentication Failed '%s'" % authID)

    def join_all_threads(self):
        for thread in self.__requests_thread:
            thread.join()

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
        # try:
        meth, args = self.parse_request_path(path)
        return meth(*args)
        # except Exception as e:
        #    return json.dumps({"response": "failure", "message": str(e)})

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

    def shutdown_server(self):
        #self.shutdown()
        self.join_all_threads()
        self.socket.close()
        
def create_server(server_class, handler_class, port, *args):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class, *args)
    return httpd


def create_and_run_server(server_class, handler_class, port, *args):
    ''' Create and Run server in another thread.
        Returns the (server object, thread)
    '''
    httpd = create_server(server_class, handler_class, port, *args)
    th = utils.run_thread(HTTPServer.serve_forever, httpd)
    return (httpd, th)


def parse_command_line_args(desc):
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-p', '--port', type=int, help='Port number', required=True)
    return parser.parse_args()


def set_sigint_handler(httpd):
    import sys

    def signal_handler(signal, frame):
        '''Signal handler for SIGINT. Joins all request threads and
           close server socket before exiting.
        '''
        print "Shutting down server"
        httpd.shutdown_server()

        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)


def main(serverclass):
    cmdargs = parse_command_line_args("Server")
    httpd = create_server(serverclass, ServerRequestHandler, cmdargs.port)
    set_sigint_handler(httpd)

    print "Running HTTP Server"
    print "Press CTRL+C to exit"
    httpd.serve_forever()


if __name__ == "__main__":
    main(serverclass=MultiThreadedHTTPServer)
