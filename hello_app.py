# A minimal version of web framework
import socket 
import StringIO
import sys
import datetime

class WSGIServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 10

    def __init__(self, server_address):
        # Create a listening socket
        self.listen_socket = listen_socket = \
            socket.socket(self.address_family, self.socket_type)
        # Allow reuse of the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind on input address
        listen_socket.bind(server_address)
        # Activate
        listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework
        self.headers_set = []

    def set_app(self, application):
        self.application = application

    def server_run(self):
        listen_socket = self.listen_socket
        while True:
            # New client connection
            client_connection, client_addr = listen_socket.accept()
            # Hanlde a single request
            self.handle_request(client_connection)

    def handle_request(self, client_connection):
        request_data = client_connection.recv(1024)
        # Print formatted request data 
        print(''.join(
            '< {line}\n'.format(line=line)
            for line in request_data.splitlines()
        ))

        request_info = self.parse_request(request_data)

        # Construct environment dictionary using request data
        env = self.get_environ(request_info, request_data)

        # Process the request
        result = self.application(env, self.start_response)

        # Construct a response and send it back to the client
        self.finish_response(result, client_connection)

    def parse_request(self, text):
        text = text.strip()
        info = {}

        #print(text)
        # Default value
        info['method'] = 'GET'
        info['path'] = '/'
        info['version'] = 'HTTP/1.1'

        if text:
            request_line = text.splitlines()[0]
            request_line = request_line.rstrip('\r\n')
            
            (info['method'],
             info['path'],
             info['version']
            ) = request_line.split()
        else:
            print("Invalid http request info: ", text)

        return info

    def get_environ(self, request_info, request_data):
        env = {}
        # Required WSGI variables
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = StringIO.StringIO(request_data)
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False
        # Required CGI variables
        env['REQUEST_METHOD'] = request_info['method']
        env['PATH_INFO'] = request_info['path']
        env['SERVER_NAME'] = self.server_name
        env['SERVER_PORT'] = str(self.server_port)
        return env

    def start_response(self, status, response_headers, exc_info=None):
        # Add necessary server headers
        server_headers = [
            ('Date', str(datetime.datetime.now())),
            ('Server', 'WSGIServer 0.2')
        ]
        self.headers_set = [status, response_headers + server_headers]

    def finish_response(self, result, client_connection):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 {status}\r\n'.format(status=status)
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data 
            # Print formatted response data 
            print(''.join(
                '> {line}\n'.format(line=line)
                for line in response.splitlines()
            ))
            client_connection.sendall(response)
        finally:
            client_connection.close()


(HOST, PORT) = '', 80
HTML = 'index.html'

def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server 

def hello_world_app(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    # Default response with plain text
    response = []
    response.append('Hello world!\n')
    response.append('Current time: ' + str(datetime.datetime.now()))

    # Use HTML if exists
    try:
        file = open(HTML, 'r')
        response = file.read()
    finally:
        file.close()

    return response

"""Collect command-line options in a dictionary"""
def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts

if __name__ == '__main__':
    from sys import argv
    args = getopts(argv)
    if '-p' in args: # Change default port
        PORT = int(args['-p'])

    server_address = (HOST, PORT)
    httpd = make_server(server_address, hello_world_app)
    print('WSGIServer: Serving HTTP on port {port} ...\n'.format(port = PORT))
    httpd.server_run()





