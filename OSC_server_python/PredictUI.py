from MyUdpServer import MyUdpServer
from MyTcpServer import MyTcpServer

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import *

import os
import sys
import itertools
import json
import numpy as np
from pythonosc import dispatcher
import collections
import socket

# Config
# IP = '192.168.0.14'
# PORT = 5589
PAUSE_TIME = 0.0000001  # Frequency of plots update. Must be greater than zero.
FLAG_MA = False

SIZE_MA = 10  # Number of moving average size.
SIZE_DATA = 300  # Number of data points width.
SIZE_PAUSER = SIZE_DATA - 1

# Global graph params
ma_tmp = []

# Global ETL params
model = None
sc = None
sc_max = -np.inf
sc_min = np.inf
labels = {
    "a": "nothing",
    "b": "passing",
    "c": "touching"
}


class MainWindow:
    def __init__(self, mode='normal'):
        print("-----Start initialize QT Window-----")
        # Initialize Data
        self._timewindow = 500
        self._bufsize = self._timewindow + 10
        self.databuffer01 = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.databuffer02 = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.x = np.linspace(0.0, self._timewindow, self._timewindow)
        self.y01 = np.zeros(self._timewindow, dtype=np.float)
        self.y02 = np.zeros(self._timewindow, dtype=np.float)

        # UI Components
        self.win = QWidget()

        # Plot 01  /mimosa04
        self.plt01 = pg.PlotWidget()
        self.plt01.showGrid(x=True, y=True)
        # self.plt01.setLabel('left', 'amplitude', 'V')
        # self.plt01.setLabel('bottom', 'time', 's')
        self.curve01 = self.plt01.plot(self.x, self.y01, pen=(0, 0, 255))

        # Plot 02  /mimosa09
        self.plt02 = pg.PlotWidget()
        self.plt02.showGrid(x=True, y=True)
        # self.plt02.setLabel('left', 'amplitude', 'V')
        # self.plt02.setLabel('bottom', 'time', 's')
        self.curve02 = self.plt02.plot(self.x, self.y02, pen=(0, 0, 255))

        self.label_predict01 = QLabel("[ pred 01 ]")
        self.label_predict02 = QLabel("[ pred 02 ]")
        style_sheet_qlabel = "QLabel { font-size : 20px; color : green; font-weight:bold; }"
        self.label_predict01.setStyleSheet(style_sheet_qlabel)
        self.label_predict02.setStyleSheet(style_sheet_qlabel)

        # Global Grid
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.label_predict01, 0, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.grid_layout.addWidget(self.plt01, 0, 1, 1, 12)
        self.grid_layout.addWidget(self.label_predict02, 1, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.grid_layout.addWidget(self.plt02, 1, 1, 1, 12)

        self.win.setLayout(self.grid_layout)
        self.win.setStyleSheet("background-color: black;")
        self.win.setWindowTitle("Mimosa prediction")
        self.win.show()

        # self.server = MyTcpServer(IP, PORT, self.tcp_handler)
        print("-----Finish initialize QT Window-----")

    def update_plot(self, data, address=''):

        if address == '/mimosa04':
            # print('~~~~~~~')
            self.databuffer01.append(data)
            self.y01 = list(itertools.islice(self.databuffer01, 10, None))
            self.y01 = np.array(self.y01)
            assert len(self.y01) == self._timewindow
            # self.curve01.setData(self.x, self.y01)
        elif address == '/mimosa09':
            # print('____________________________')
            self.databuffer02.append(data)
            self.y02 = list(itertools.islice(self.databuffer02, 10, None))
            self.y02 = np.array(self.y02)
            assert len(self.y02) == self._timewindow
            # self.curve02.setData(self.x, self.y02)
        self.curve01.setData(self.x, self.y01)
        self.curve02.setData(self.x, self.y02)
        # self.app.processEvents()

    def tcp_handler(self, json_input):
        for obj in json_input:
            json_obj = json.loads(obj)
            addr = json_obj['address']
            data = json_obj['data']
            self.append_data(addr, data)

    def append_data(self, address, *args):
        # print(address, args)
        data = args[0]
        self.update_plot(data, address)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec_())
