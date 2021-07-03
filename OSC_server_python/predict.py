from MyUdpServer import MyUdpServer
from MyTcpServer import MyTcpServer
from PredictUI import MainWindow

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import *

import os
import sys
import itertools
import json
import joblib
import numpy as np
from pythonosc import dispatcher
# import collections
# import multiprocessing
# from multiprocessing import Process
# from multiprocessing.managers import BaseManager
import socket
from threading import Thread

# from sklearn.preprocessing import StandardScaler

# Config
# IP = '192.168.0.14'
IP = '192.168.3.3'
PORT = 5589
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


def standardize():
    global sc
    global y_vec

    # Standardize
    # if sc is None or (data < sc_min).any() or (data > sc_max).any():
    #     assert SIZE_DATA == len(y_vec)
    #
    #     if (data < sc_min).any():
    #         sc_min = data
    #     if (data > sc_max).any():
    #         sc_max = data
    #     sc = StandardScaler()
    #     sc.fit(np.array([[sc_max, sc_min]]))

    d = sc.transform([y_vec])

    return d


def predict(method='model'):
    """
    Predict state, input data should be standardize.
    """
    global model
    global y_vec

    if method == 'threshold':
        max_peak = y_vec.max()
        min_peak = y_vec.min()
        diff = max_peak - min_peak
        print("max:{} min:{} diff:{}".format(max_peak, min_peak, diff))

        if diff > 80:
            p = 'touching'
        elif diff >= 20:
            p = 'passing'
        else:
            p = 'nothing'

    elif method == 'model':
        if model is None:
            model = joblib.load('./model/model.pkl')

        ## Check if data all same
        # result = np.all(arr == arr[0])
        # if result:
        #     print("nothing")
        #     print('All Values in Array are same / equal')

        data = standardize()
        p = model.predict(data)

    return p


def osc_input_handler(address, *args):
    global mw
    global ma_tmp
    data = args[1]
    mw.update_plot(data, address)


def tcp_handler(json_input, mw):
    for obj in json_input:
        json_obj = json.loads(obj)
        addr = json_obj['address']
        data = json_obj['data']

        if addr == '/mimosa04':
            mw.databuffer01.append(data)
        elif addr == '/mimosa09':
            mw.databuffer02.append(data)
        mw.update_plot(data)


def run_qt_window(mw: MainWindow):
    print('[QT process]')
    print('parent process:', os.getppid())
    print('process id:', os.getpid())

    mw.run()


def run_tcp_server(mw: MainWindow):
    print('[TCP process]')
    print('parent process:', os.getppid())
    print('process id:', os.getpid())
    server = MyTcpServer(IP, PORT, tcp_handler)
    server.run()


def run_osc_server(mw: MainWindow):
    print('[OSC process]')
    print('parent process:', os.getppid())
    print('process id:', os.getpid())
    dp = dispatcher.Dispatcher()
    dp.map("/mimosa09", mw.append_data, "Mimosa raw data")
    dp.map("/mimosa04", mw.append_data, "Mimosa raw data")
    server = MyUdpServer(IP, PORT, dp)
    server.create_threading_server()
    server.run()


class ClientThread(Thread):
    def __init__(self, window):
        Thread.__init__(self)
        self.window = window

    def run(self):
        global tcpClientA
        tcpClientA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpClientA.connect((IP, PORT))

        while True:
            data = tcpClientA.recv(1024)
            self.window.append(data.decode("utf-8"))
        tcpClientA.close()


if __name__ == "__main__":
    # df = pd.read_csv('./data/train_data_UU.csv', header=None)
    # df_data = df.drop(columns=[300])
    # sc = StandardScaler()
    # sc.fit(df_data)

    ########################## UDP ##########################
    # BaseManager.register('MainWindow', MainWindow)
    #
    # manager = BaseManager()
    # manager.start()
    # mw = manager.MainWindow()
    #
    # while mw is None:
    #     print('Waiting for MainWindow initializing...')
    #
    # process = []
    #
    # process_qt = Process(target=run_qt_window, args=[mw])
    # process_qt.start()
    # process.append(process_qt)
    #
    # process_osc_server = Process(target=run_osc_server, args=[mw])
    # process_osc_server.start()
    # process.append(process_osc_server)
    #
    # process_qt.join()
    # process_osc_server.join()

    ########################## TCP ##########################
    app = QApplication(sys.argv)

    window = MainWindow()
    server = MyTcpServer(IP, PORT, window)
    server.start()

    sys.exit(app.exec_())
