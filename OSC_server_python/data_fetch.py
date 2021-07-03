from MyUdpServer import MyUdpServer
from MyTcpServer import MyTcpServer
from DynamicPlotter import DynamicPlotter

from PyQt5.QtWidgets import QApplication
from PyQt5 import QtWidgets
import sys
import numpy as np
import traceback
import json
from pythonosc import dispatcher

# IP Config
IP = '192.168.0.14'
# IP = '192.168.3.3'
PORT = 5589

dy_plot = None  # Initializing DynamicPlotter


def excepthook(exc_type, exc_value, exc_tb):
    """
    For Exception traceback
    """
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    QtWidgets.QApplication.quit()


def udp_handler(_address, *args):
    # print(_address, args)
    data = args[0]
    dy_plot.update_plot(data)


# def tcp_handler(json_input):
#     for obj in json_input:
#         json_obj = json.loads(obj)
#         data = json_obj['data']
#         dy_plot.update_plot(data)


def run_udp_server():
    global dy_plot
    dp = dispatcher.Dispatcher()
    dp.set_default_handler(udp_handler)

    dy_plot = DynamicPlotter()
    server = MyUdpServer(IP, PORT, dp)
    server.create_blocking_server()
    server.run()
    dy_plot.run()


def run_tcp_server():
    global dy_plot

    sys.excepthook = excepthook
    dy_plot = DynamicPlotter()
    server = MyTcpServer(IP, PORT, dy_plot)
    server.start()
    ret = dy_plot.run()
    print("event loop exited")
    sys.exit(ret)


if __name__ == "__main__":
    # run_udp_server()
    run_tcp_server()
