from xmlrpc.server import SimpleXMLRPCRequestHandler, SimpleXMLRPCServer


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/rpc',)


class XMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, *args, **kwargs):
        super().__init__(requestHandler=RequestHandler, allow_none=True, *args, **kwargs)
        self._quit = False

    def serve_forever(self, **kwargs):
        """
        Overrides the serve_forever function to wait for the server to be ready to quit

        :param kwargs: N/A
        :return: None
        """
        while not self._quit:
            self.handle_request()

    def terminate(self):
        """
        Marks the server as ready for termination

        :return: None
        """

        self._quit = True
