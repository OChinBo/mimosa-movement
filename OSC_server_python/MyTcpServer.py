import socket
import threading
from threading import Thread
import re


class MyTcpServer(Thread):

    def __init__(self, ip, port, window, handler='classic'):
        Thread.__init__(self)
        self.window = window
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((ip, port))
        self.s.listen(10)
        self.handler = handler
        # if self.handler == 'local':
        #     self.local_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     self.local_socket.connect(('localhost', 5590))

        self.sockets = []
        # self.handler = handler
        self.t = threading.Thread(target=self.handle)

        print('server start at: %s:%s' % (ip, port))
        print('wait for connection...')

    def __exit__(self, exc_type, exc_value, traceback):
        if self.handler == 'local':
            self.local_socket.close()

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
                # if self.handler == 'local':
                #     self.local_socket.send(recv_data)
                # elif self.handler:  # json handler
                #     self.handler(json_data)

    def run(self):
        self.t.start()
        while True:
            conn, addr = self.s.accept()
            print('connected by ' + str(addr))
            conn.setblocking(0)
            self.sockets.append(conn)


if __name__ == "__main__":
    # Receive data form IP, then send to local port
    IP = '192.168.0.14'
    PORT = 5589

    server = MyTcpServer(IP, PORT, 'local')
    server.start()
