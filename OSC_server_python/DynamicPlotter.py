import sys
import time

import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from PyQt5.QtWidgets import *

import json
import gc
import collections
from time import gmtime, strftime
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import itertools


class DynamicPlotter:

    def __init__(self, timewindow=500):
        print("-----Start initialize DynamicPlotter-----")
        # QT Data stuff
        self._timewindow = timewindow
        self._diff_preserve = 1
        self._bufsize = timewindow + self._diff_preserve
        self.databuffer = collections.deque([0.0] * self._bufsize, self._bufsize)
        self.x = np.linspace(0.0, self._timewindow, self._timewindow)
        self.y = np.zeros(self._timewindow, dtype=np.float)

        # Pre-process and other monitor stuff
        self.time0 = time.time()  # dps
        self.count_dots = 0  # dps
        self.count_dots0 = 0  # dps
        self.arr_diff = collections.deque([0.0] * self._timewindow, self._timewindow)  # difference buffer
        self.tag = None  # labels radio-button
        self.PAUSE = False
        self.FLAG_DIFFERENCE = False  # 差分
        self.FLAG_SAVGOL = False
        self.FLAG_DPS = True
        self.FLAG_GC = False

        # gc
        if self.FLAG_GC:
            gc.set_threshold(100, 10, 10)
            print("gc_threshold:", gc.get_threshold())

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
        # self.plt.resize(800, 600)
        self.plt.showGrid(x=True, y=True)
        self.plt.setDownsampling(auto=True)
        self.plt.setClipToView(True)
        self.plt.setLabel('left', 'amplitude', 'V')
        self.plt.setLabel('bottom', 'time', 's')
        self.curve = self.plt.plot(self.x, self.y, pen=(0, 0, 255))

        # Right form layout 右邊控制
        self.right_form = QFormLayout()

        # Difference
        self.checkbox_difference = QCheckBox()
        self.checkbox_difference.stateChanged.connect(self.preprocess_difference)
        self.right_form.addRow(QLabel('差分:'), self.checkbox_difference)
        # self.slider_difference = QSlider(QtCore.Qt.Horizontal)
        # self.slider_difference.setRange(0, 2)
        # self.slider_difference.valueChanged.connect(self.preprocess_difference)
        # self.label_difference = QLabel('差分:' + str(self.slider_difference.value()) + "\t")
        # self.right_form.addRow(self.label_difference, self.slider_difference)

        self.right_form.addWidget(QLabel(' '))  # blank line
        self.right_form.addWidget(QLabel(' '))  # blank line

        # Savitzky-Golay filter 平滑
        self.checkbox_savgol = QCheckBox()
        self.checkbox_savgol.stateChanged.connect(self.preprocess_savgol)
        self.right_form.addRow(QLabel('Savitzky-Golay'), self.checkbox_savgol)
        if self.FLAG_SAVGOL:
            self.checkbox_savgol.setChecked(True)
        # Savgol window_length
        self.slider_savgol_window_length = QSlider(QtCore.Qt.Horizontal)
        self.slider_savgol_window_length.setRange(1, self._timewindow - ((self._timewindow + 1) & 1))
        self.slider_savgol_window_length.setSingleStep(2)
        self.slider_savgol_window_length.setValue(85)
        self.slider_savgol_window_length.valueChanged.connect(self.preprocess_savgol_window_length)
        self.label_savgol_window_length = QLabel(
            'window_length:{}\t'.format(self.slider_savgol_window_length.value()))
        self.right_form.addRow(self.label_savgol_window_length, self.slider_savgol_window_length)
        # Savgol polyorder
        self.slider_savgol_polyorder = QSlider(QtCore.Qt.Horizontal)
        self.slider_savgol_polyorder.setRange(1, 10)
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
        self.right_form.addRow(self.pause_button)
        self.right_form.addRow(self.save_button)
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

        self.grid_layout = QGridLayout()
        self.grid_layout.addLayout(self.left_vbox, 0, 0, 1, 1)
        self.grid_layout.addWidget(self.plt, 0, 1, 1, 1)
        self.grid_layout.addLayout(self.right_form, 0, 2, 1, 1)
        self.grid_layout.setColumnStretch(0, 0)
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 0)

        self.win.setLayout(self.grid_layout)
        self.win.setWindowTitle('Dynamic Plotting with PyQtGraph')
        self.win.show()

        # QTimer
        if self.FLAG_GC:
            self.timer = QtCore.QTimer()
            # self.timer.timeout.connect(self.app.processEvents)
            self.timer.timeout.connect(self.gc_collect)
            self.timer.start(5000)
        self.timer = QtCore.QTimer()
        # self.timer.timeout.connect(self.app.processEvents)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

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

    def preprocess_difference(self, state):
        if QtCore.Qt.Checked == state:
            print("difference selected.")
            self.FLAG_DIFFERENCE = True
        else:
            print("difference canceled.")
            self.FLAG_DIFFERENCE = False
            # self.arr_diff = None  # reset arr_diff
        # self.label_difference.setText('差分:' + str(value) + "\t")
        # self.FLAG_DIFFERENCE = value
        # print("Difference level:" + str(self.FLAG_DIFFERENCE))

    def onClickedTag(self):
        if self.radiobtn_none.isChecked():
            self.tag = None
        elif self.radiobtn_nothing.isChecked():
            self.tag = 'nothing'
        elif self.radiobtn_passing.isChecked():
            self.tag = 'passing'
        elif self.radiobtn_touching.isChecked():
            self.tag = 'touching'

    def get_dps(self):
        self.time0 = time.time()
        dps = self.count_dots - self.count_dots0
        self.count_dots0 = self.count_dots
        return dps

    def gc_collect(self):
        print("[gc] collect:", gc.collect())

    def save_data(self):
        path = "./data/{}/".format(self.tag if self.tag else '')
        file_name = strftime("%Y-%m-%d_%H-%M-%S", gmtime())
        save_path = path + file_name + '.csv'

        data = list(self.databuffer)  # save raw data
        # data = self.y.tolist()  # save pre-process data
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
            self.append_data(data, addr)

    def append_data(self, data, address=None):
        # print("append_data:", data)
        self.arr_diff.append(data - self.databuffer[-1])
        self.databuffer.append(data)

    def update_plot(self):
        """
        We do all calculate fix on self.y
        Source data is in databuffer
        """

        if not self.PAUSE:
            self.count_dots += 1
            self.y = list(itertools.islice(self.databuffer, self._diff_preserve, None))  # get last windowsize elements

            if self.FLAG_DIFFERENCE:
                # if self.arr_diff is None:
                #     self.arr_diff = np.diff(self.databuffer)
                #     self.arr_diff = collections.deque(self.arr_diff, self._timewindow)
                # else:
                #     self.arr_diff.append(data - self.databuffer[-2])
                self.y = self.arr_diff
                # arr_diff = np.diff(list(self.databuffer), n=self.FLAG_DIFFERENCE)
                # self.y = self.arr_diff[-self._timewindow:]
                # assert len(self.y) == self._timewindow

            if self.FLAG_SAVGOL:
                win_val = self.slider_savgol_window_length.value()
                pol_val = self.slider_savgol_polyorder.value()
                try:
                    if (win_val & 1) == 0:  # window-length must be odd
                        self.slider_savgol_window_length.setValue(win_val + 1)
                        self.preprocess_savgol_window_length()
                    if pol_val >= win_val:  # polyorder must smaller than window-length
                        self.slider_savgol_polyorder.setValue(win_val - 1)
                        self.preprocess_savgol_polyorder()
                    self.y = savgol_filter(self.y,
                                           self.slider_savgol_window_length.value(),
                                           self.slider_savgol_polyorder.value())
                except Exception as e:
                    print(e.with_traceback(sys.exc_info()[2]))
                    print(win_val, pol_val)
                    self.update_plot()
                    # os.system('pause')

                # assert len(self.y) == self._timewindow

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
        print("Running Plot")
        return self.app.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    m = DynamicPlotter()
    sys.exit(app.exec_())
