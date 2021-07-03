import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import *

import sys
import json
import itertools
import collections

import numpy as np
import pandas as pd
from tensorflow import keras
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import LabelEncoder

# Config
model_path = "model/LSTM_a9_03_std_sv85_2.h5"
sc_path = "scaler/a9_03_clean.csv"
LABELS = ["nothing", "passing", "touching"]
savgol_window_length = 85
savgol_polyorder = 2


# sc_max = -np.inf
# sc_min = np.inf
# labels = {
#     "a": "nothing",
#     "b": "passing",
#     "c": "touching"
# }


class PredictUI:
    def __init__(self, timewindow=500, mode="model"):
        """
        mode: ['model', 'threshold']
            'model': Load keras model to predict.
            'threshold': Use threshold to classify.
        """

        print("-----Start initialize QT Window-----")
        self.mode = mode
        # QT Data stuff
        self._timewindow = timewindow  # Time window we see in UI layout.
        self._diff_preserve = 1  # If we need to diff our data, we need to preserve n space for n-differences.
        self._bufsize = timewindow + self._diff_preserve  # Size of data buffer.
        self.databuffer01 = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.databuffer02 = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.x = np.linspace(0.0, self._timewindow, self._timewindow)
        self.y01 = np.zeros(self._timewindow, dtype=np.float)
        self.y02 = np.zeros(self._timewindow, dtype=np.float)

        ## Preprocess and model stuff
        # Load model
        self.model = None
        if self.mode == "model":
            self.model = keras.models.load_model(model_path)
        # LabelEncoder
        self.le = LabelEncoder()
        self.le.fit(LABELS)
        # Standardize
        df_sc = pd.read_csv(sc_path, header=None)
        df_sc = df_sc.iloc[:, :-1]
        self.sc = StandardScaler()
        self.sc.fit(df_sc)

        # QT App
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])

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

        # Label Predict
        self.vbox_pred01 = QVBoxLayout()
        self.vbox_pred02 = QVBoxLayout()
        self.label_device01 = QLabel("\t/mimosa04\t")
        self.label_device02 = QLabel("\t/mimosa09\t")
        self.label_predict01 = QLabel("[ init ]")
        self.label_predict02 = QLabel("[ init ]")
        style_sheet_qlabel = "QLabel { font-size : 40px; color : green; font-weight:bold; text-align : center}"
        self.label_device01.setStyleSheet(style_sheet_qlabel)
        self.label_device02.setStyleSheet(style_sheet_qlabel)
        self.label_predict01.setStyleSheet(style_sheet_qlabel)
        self.label_predict02.setStyleSheet(style_sheet_qlabel)

        self.vbox_pred01.addWidget(self.label_device01, alignment=QtCore.Qt.AlignHCenter)
        self.vbox_pred01.addWidget(self.label_predict01, alignment=QtCore.Qt.AlignHCenter)
        self.vbox_pred02.addWidget(self.label_device02, alignment=QtCore.Qt.AlignHCenter)
        self.vbox_pred02.addWidget(self.label_predict02, alignment=QtCore.Qt.AlignHCenter)
        # self.vbox_pred01.setAlignment(QtCore.Qt.AlignHCenter)
        # self.vbox_pred02.setAlignment(QtCore.Qt.AlignHCenter)

        # Global Grid
        self.grid_layout = QGridLayout()
        self.grid_layout.addLayout(self.vbox_pred01, 0, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.grid_layout.addWidget(self.plt01, 0, 1, 1, 12)
        self.grid_layout.addLayout(self.vbox_pred02, 1, 0, 1, 1, alignment=QtCore.Qt.AlignCenter)
        self.grid_layout.addWidget(self.plt02, 1, 1, 1, 12)

        self.win.setLayout(self.grid_layout)
        self.win.setStyleSheet("background-color: black;")
        self.win.setWindowTitle("Mimosa prediction")
        self.win.show()

        # QTimer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        # self.server = MyTcpServer(IP, PORT, self.tcp_handler)
        print("-----Finish initialize QT Window-----")

    def preprocess(self, data):
        # Standardize
        data = self.sc.transform([data])

        # Savgol filter
        if isinstance(data, pd.DataFrame):
            for i in range(len(data)):
                row = data.iloc[i]
                data.iloc[i] = savgol_filter(row, savgol_window_length, savgol_polyorder)
        else:
            for i in range(len(data)):
                row = data[i]
                data[i] = savgol_filter(row, savgol_window_length, savgol_polyorder)
        return data

    def predict(self, data):
        """
        params:
            data: raw data of databuffer
        return: text of predict result
        """
        pred = None
        if self.mode == "model":
            data = self.preprocess(data)

            # reshape to feed model
            if isinstance(data, np.ndarray):
                x_test_reshape = data.reshape((data.shape[0], 1, data.shape[1]))
            else:
                x_test_reshape = data.values.reshape((data.shape[0], 1, data.shape[1]))
            pred = self.model.predict(x_test_reshape, batch_size=64, verbose=0)
            pred_bool = np.argmax(pred, axis=1)
            pred = self.le.inverse_transform(pred_bool)
        return pred

    def tcp_handler(self, json_input):
        for obj in json_input:
            json_obj = json.loads(obj)
            addr = json_obj['address']
            data = json_obj['data']
            self.append_data(data, addr)

    def append_data(self, data, address=None):
        # print("append_data:", data)
        if address == "/mimosa04":
            # print("append /mimosa04:", data)
            self.databuffer01.append(data)
        elif address == "/mimosa09":
            # print("append /mimosa09:", data)
            self.databuffer02.append(data)

    def update_plot(self):

        self.y01 = list(itertools.islice(self.databuffer01, self._diff_preserve, None))
        self.y01 = np.array(self.y01)
        # assert len(self.y01) == self._timewindow

        self.y02 = list(itertools.islice(self.databuffer02, self._diff_preserve, None))
        self.y02 = np.array(self.y02)
        # assert len(self.y02) == self._timewindow

        self.curve01.setData(self.x, self.y01)
        self.curve02.setData(self.x, self.y02)

        # Predict
        pred01 = self.predict(self.databuffer01)
        self.label_predict01.setText("\t{}\t".format(str(pred01)))
        pred02 = self.predict(self.databuffer02)
        self.label_predict02.setText("\t{}\t".format(str(pred02)))

        self.app.processEvents()

    def run(self):
        print("Running Plot")
        return self.app.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = PredictUI()
    sys.exit(app.exec_())
