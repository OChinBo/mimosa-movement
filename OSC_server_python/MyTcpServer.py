import socket
import threading
from threading import Thread
import re


class MyTcpServer(Thread):

    def __init__(self, ip, port, window):
        Thread.__init__(self)
        self.window = window
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((ip, port))
        self.s.listen(10)

        self.sockets = []
        self.t = threading.Thread(target=self.handle)

        print('server start at: %s:%s' % (ip, port))
        print('wait for connection...')

    # def __exit__(self, exc_type, exc_value, traceback):
    #     self.local_socket.close()

    def handle(self):
        while True:
            for s in self.sockets:
                try:
                    recv_data = s.recv(1024)
                except Exception as e:
                    continue
                if len(recv_data) == 0:  # connection closed
                    s.close()
                    print('client closed connection.')
                    self.sockets.remove(s)
                    continue

                json_data = recv_data.decode('unicode_escape')
                # print(json_data)
                json_data = re.findall('{.*?}', json_data)  # array of str:json

                self.window.tcp_handler(json_data)

    def run(self):
        self.t.start()
        while True:
            conn, addr = self.s.accept()
            print('connected by ' + str(addr))
            conn.setblocking(0)
            self.sockets.append(conn)
