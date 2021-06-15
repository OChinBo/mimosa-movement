from MyUdpServer import MyUdpServer
from MyTcpServer import MyTcpServer
from DynamicPlotter import DynamicPlotter

from PyQt5.QtWidgets import QApplication
import sys
import numpy as np
import json
from pythonosc import dispatcher

# IP Config
IP = '192.168.0.14'
PORT = 5589

dy_plot = None  # Initializing DynamicPlotter

FLAG_MA = False  # Moving Average
SIZE_MA = 15
ma_tmp = []


def osc_input_handler(_address, *args):  # For early udp osc handle. Bind to MyUdpServer.class
    global dy_plot
    global ma_tmp

    data = args[1]

    if FLAG_MA:  # Moving Average
        ma_tmp = np.append(ma_tmp, data)  # Add data to ma_tmp
        if len(ma_tmp) == SIZE_MA:
            data = ma_tmp.mean()
            ma_tmp = []
        else:
            return
    # dy_plot.databuffer.append(data)
    dy_plot.update_plot(data)


def tcp_handler(json_input):
    for obj in json_input:
        json_obj = json.loads(obj)
        # addr = json_obj['address']
        data = json_obj['data']
        # dy_plot.databuffer.append(data)
        dy_plot.update_plot(data)


if __name__ == "__main__":
    # dp = dispatcher.Dispatcher()
    # dp.map("/mimosa09", osc_input_handler, "Mimosa raw data")
    # dp.map("/mimosa04", osc_input_handler, "Mimosa raw data")
    dy_plot = DynamicPlotter()
    server = MyTcpServer(IP, PORT, dy_plot)
    server.start()
    dy_plot.run()
