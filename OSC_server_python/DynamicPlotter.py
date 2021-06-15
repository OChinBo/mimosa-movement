import os
import sys
import time

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import *

import json
import collections
from time import gmtime, strftime
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import itertools


class DynamicPlotter:

    def __init__(self, timewindow=1500):
        print("-----Start initialize DynamicPlotter-----")
        # Data stuff
        self._timewindow = timewindow
        self._bufsize = timewindow + 10
        self.databuffer = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.x = np.linspace(0.0, self._timewindow, self._timewindow)
        self.y = np.zeros(self._timewindow, dtype=np.float)

        # Flags and other stuff
        self.time0 = time.time()  # dps
        self.count_dots = 0  # dps
        self.count_dots0 = 0  # dps
        self.tag = None  # labels radio-button
        self.PAUSE = False
        self.FLAG_DIFFERENCE = 0  # 差分
        self.FLAG_SAVGOL = False
        self.FLAG_DPS = True

        # PyQtGraph stuff
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        self.win = QWidget()

        # Left vbox 左邊狀態欄
        self.left_vbox = QVBoxLayout()

        self.label_max = QLabel('Max: {:.2f}\t'.format(np.max(self.y)))  # max label
        self.left_vbox.addWidget(self.label_max)
        self.label_min = QLabel('Min: {:.2f}\t'.format(np.min(self.y)))  # min label
        self.left_vbox.addWidget(self.label_min)
        self.label_avg = QLabel('Avg: {:.2f}\t'.format(np.mean(self.y)))  # avg label
        self.left_vbox.addWidget(self.label_avg)
        self.left_vbox.addWidget(QLabel(' '))  # blank line
        self.left_vbox.addWidget(QLabel('WindowSize:{}\t'.format(self._timewindow)))  # timewindow label
        self.label_dots = QLabel('Total dots: {}\t'.format(self.count_dots))  # total dots label
        self.left_vbox.addWidget(self.label_dots)
        if self.FLAG_DPS:
            self.label_dps = QLabel('dps:{:.2f}\t'.format(self.get_dps()))  # dps label
            self.left_vbox.addWidget(self.label_dps)
        self.left_vbox.addStretch(30)

        # Middle graph 中間電波圖
        self.plt = pg.PlotWidget()
        self.plt.resize(800, 600)
        self.plt.showGrid(x=True, y=True)
        self.plt.setLabel('left', 'amplitude', 'V')
        self.plt.setLabel('bottom', 'time', 's')
        self.curve = self.plt.plot(self.x, self.y, pen=(0, 0, 255))

        # Right form layout 右邊控制
        self.right_form = QFormLayout()

        # Difference
        self.slider_difference = QSlider(QtCore.Qt.Horizontal)
        self.slider_difference.setRange(0, 2)
        self.slider_difference.valueChanged.connect(self.preprocess_difference)
        self.label_difference = QLabel('差分:' + str(self.slider_difference.value()) + "\t")
        self.right_form.addRow(self.label_difference, self.slider_difference)

        self.right_form.addWidget(QLabel(' '))  # blank line
        self.right_form.addWidget(QLabel(' '))  # blank line

        # Savitzky-Golay filter 平滑
        self.checkbox_savgol = QCheckBox()
        self.checkbox_savgol.stateChanged.connect(self.preprocess_savgol)
        self.right_form.addRow(QLabel('Savitzky-Golay'), self.checkbox_savgol)
        # Savgol window_length
        self.slider_savgol_window_length = QSlider(QtCore.Qt.Horizontal)
        self.slider_savgol_window_length.setRange(1, self._timewindow - ((self._timewindow + 1) & 1))
        self.slider_savgol_window_length.setSingleStep(2)
        self.slider_savgol_window_length.setValue(65)
        self.slider_savgol_window_length.valueChanged.connect(self.preprocess_savgol_window_length)
        self.label_savgol_window_length = QLabel(
            'window_length:{}\t'.format(self.slider_savgol_window_length.value()))
        self.right_form.addRow(self.label_savgol_window_length, self.slider_savgol_window_length)
        # Savgol polyorder
        self.slider_savgol_polyorder = QSlider(QtCore.Qt.Horizontal)
        self.slider_savgol_polyorder.setRange(1, 20)
        self.slider_savgol_polyorder.setValue(2)
        self.slider_savgol_polyorder.valueChanged.connect(self.preprocess_savgol_polyorder)
        self.label_savgol_polyorder = QLabel('polyorder:{}\t'.format(self.slider_savgol_polyorder.value()))
        self.right_form.addRow(self.label_savgol_polyorder, self.slider_savgol_polyorder)

        self.right_form.addWidget(QLabel(' '))  # blank line
        self.right_form.addWidget(QLabel(' '))  # blank line
        self.right_form.addWidget(QLabel(' '))  # blank line

        # Pause
        self.pause_button = QPushButton('Pause')
        self.pause_button.clicked.connect(self.pause)
        # save
        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_data)
        self.right_form.addRow(self.pause_button, self.save_button)

        self.right_form.addWidget(QLabel(' '))  # blank line

        # Tag radio button
        self.radiobtn_none = QRadioButton('none')
        self.radiobtn_nothing = QRadioButton('nothing')
        self.radiobtn_passing = QRadioButton('passing')
        self.radiobtn_touching = QRadioButton('touching')
        self.radiobtn_none.toggled.connect(self.onClickedTag)
        self.radiobtn_nothing.toggled.connect(self.onClickedTag)
        self.radiobtn_passing.toggled.connect(self.onClickedTag)
        self.radiobtn_touching.toggled.connect(self.onClickedTag)
        self.tag_btngroup = QButtonGroup()
        self.tag_btngroup.addButton(self.radiobtn_none)
        self.tag_btngroup.addButton(self.radiobtn_nothing)
        self.tag_btngroup.addButton(self.radiobtn_passing)
        self.tag_btngroup.addButton(self.radiobtn_touching)
        self.radiobtn_none.setChecked(True)
        self.right_form.addRow(self.radiobtn_none)
        self.right_form.addRow(self.radiobtn_nothing)
        self.right_form.addRow(self.radiobtn_passing)
        self.right_form.addRow(self.radiobtn_touching)

        # Global hbox
        self.hbox = QHBoxLayout()
        self.hbox.addStretch(1)
        self.hbox.addLayout(self.left_vbox)
        self.hbox.addWidget(self.plt)
        self.hbox.addLayout(self.right_form)
        self.hbox.addStretch(1)

        self.win.setLayout(self.hbox)
        self.win.setWindowTitle('Dynamic Plotting with PyQtGraph')
        self.win.show()

        # QTimer
        # self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.update_plot)
        # self.timer.start(self._interval)
        # self.timer.start()
        print("-----Finish initialize DynamicPlotter-----")

    def pause(self):
        print(self.pause_button.text())
        if self.pause_button.text() == 'Pause':
            self.pause_button.setText('Play')
            self.PAUSE = True
        else:
            self.pause_button.setText('Pause')
            self.PAUSE = False

    def preprocess_savgol(self, state):
        if QtCore.Qt.Checked == state:
            print("Savgol selected.")
            self.FLAG_SAVGOL = True
        else:
            print("Savgol canceled.")
            self.FLAG_SAVGOL = False

    def preprocess_savgol_window_length(self):
        if self.slider_savgol_window_length.value() <= self.slider_savgol_polyorder.value():
            step = self.slider_savgol_window_length.value() - 1
            if step == 0:
                self.slider_savgol_window_length.setValue(3)
                step = self.slider_savgol_polyorder.value()
            self.slider_savgol_polyorder.setValue(step)

        self.label_savgol_window_length.setText(
            'window_length:{}\t'.format(self.slider_savgol_window_length.value()))
        print("savgol_window_length:{}".format(self.slider_savgol_window_length.value()))
        self.update_plot()

    def preprocess_savgol_polyorder(self):
        if self.slider_savgol_window_length.value() <= self.slider_savgol_polyorder.value():
            polyorder = self.slider_savgol_polyorder.value()
            step = polyorder + 1 if (polyorder & 1) == 0 else polyorder + 2
            self.slider_savgol_window_length.setValue(step)

        self.label_savgol_polyorder.setText(
            'polyorder:{}\t'.format(self.slider_savgol_polyorder.value()))
        print("savgol_polyorder:{}".format(self.slider_savgol_polyorder.value()))
        self.update_plot()

    def preprocess_difference(self, value):
        self.label_difference.setText('差分:' + str(value) + "\t")
        self.FLAG_DIFFERENCE = value
        print("Difference level:" + str(self.FLAG_DIFFERENCE))

    def get_dps(self):
        self.time0 = time.time()
        dps = self.count_dots - self.count_dots0
        self.count_dots0 = self.count_dots
        return dps

    def onClickedTag(self):
        if self.radiobtn_none.isChecked():
            self.tag = None
        elif self.radiobtn_nothing.isChecked():
            self.tag = 'nothing'
        elif self.radiobtn_passing.isChecked():
            self.tag = 'passing'
        elif self.radiobtn_touching.isChecked():
            self.tag = 'touching'

    def save_data(self):
        path = "./data/{}/".format(self.tag if self.tag else '')
        file_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
        save_path = path + file_name + '.csv'

        data = self.y.tolist()
        if self.tag:
            data.append(self.tag)
        df = pd.DataFrame([data], dtype=str)
        print('shape={}'.format(df.shape))
        df.to_csv(save_path, header=None, index=None)
        print("Save {}".format(save_path))

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

    def update_plot(self, data=None, address=None):
        """
        We do all calculate fix on self.y
        Source data is in databuffer
        """
        self.databuffer.append(data)

        if not self.PAUSE:
            self.count_dots += 1
            self.y = list(itertools.islice(self.databuffer, 10, None))  # get last windowsize elements

            if self.FLAG_DIFFERENCE > 0:
                diff_tmp = np.diff(list(self.databuffer), n=self.FLAG_DIFFERENCE)
                self.y = diff_tmp[-self._timewindow:]
                assert len(self.y) == self._timewindow

            if self.FLAG_SAVGOL:
                try:
                    self.y = savgol_filter(self.y,
                                           self.slider_savgol_window_length.value(),
                                           self.slider_savgol_polyorder.value())
                except Exception as e:
                    print(e.with_traceback())
                    win_val = self.slider_savgol_window_length.value()
                    pol_val = self.slider_savgol_polyorder.value()
                    print(win_val, pol_val)
                    self.slider_savgol_window_length.setValue(win_val - 1)
                    os.system('pause')

                assert len(self.y) == self._timewindow

            self.y = np.array(self.y)
            self.curve.setData(self.x, self.y)
            self.label_dots.setText('Total dots: {}\t'.format(self.count_dots))
            self.label_max.setText('Max: {:.2f}\t'.format(np.max(self.y)))
            self.label_min.setText('Min: {:.2f}\t'.format(np.min(self.y)))
            self.label_avg.setText('Avg: {:.2f}\t'.format(np.mean(self.y)))
            if self.FLAG_DPS:
                if time.time() - self.time0 >= 1:  # call get_dps() every second
                    self.label_dps.setText('dps:{:.2f}\t'.format(self.get_dps()))
        self.app.processEvents()

    def run(self):
        self.app.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    m = DynamicPlotter()
    sys.exit(app.exec_())
