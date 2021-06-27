"""Small example OSC server

This program listens to several addresses, and prints some information about
received packets.
"""

from pythonosc import osc_server
import asyncio


class MyUdpServer:
    IP = None
    PORT = None
    DP = None
    SERVER = None

    def __init__(self, ip, port, dp):
        self.IP = ip
        self.PORT = port
        self.DP = dp

    def create_threading_server(self):
        """
        Each incoming packet will be handled in it’s own thread.
        This also blocks further program execution, but allows concurrent handling of multiple incoming messages.
        Otherwise usage is identical to blocking type.
        Use for lightweight message handlers.
        """
        print("Create Threading Server")
        self.SERVER = osc_server.ThreadingOSCUDPServer((self.IP, self.PORT), self.DP)

    def create_blocking_server(self):
        """
        The blocking server type is the simplest of them all.
        Once it starts to serve, it blocks the program execution forever and remains idle inbetween handling requests.
        This type is good enough if your application is very simple and only has to react to OSC messages coming in and
        nothing else.
        """
        print("Create Blocking Server")
        self.SERVER = osc_server.BlockingOSCUDPServer((self.IP, self.PORT), self.DP)

    def create_async_exclusive_server(self):
        """
        This mode comes without a main loop.
        You only have the OSC server running in the event loop initially.
        You could of course use an OSC message to start a main loop from within a handler.
        """
        self.SERVER = osc_server.AsyncIOOSCUDPServer((self.IP, self.PORT), self.DP, asyncio.get_event_loop())

    def run(self):
        if self.SERVER is None:
            print("Sorry, please create server first.")
            return

        # Blocking server
        if isinstance(self.SERVER, osc_server.BlockingOSCUDPServer):
            print("Serving on {}".format(self.SERVER.server_address))
            self.SERVER.serve_forever()

        # Threading server
        if isinstance(self.SERVER, osc_server.ThreadingOSCUDPServer):
            print("Serving on {}".format(self.SERVER.server_address))
            self.SERVER.serve_forever()

        # AsyncIO server
        if isinstance(self.SERVER, osc_server.AsyncIOOSCUDPServer):
            print("Serving on {}".format(self.IP))
            self.SERVER.serve()
