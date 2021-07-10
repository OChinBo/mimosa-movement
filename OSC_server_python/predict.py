from MyTcpServer import MyTcpServer
from PredictUI import PredictUI

from PyQt5 import QtWidgets

import sys
import traceback

# Config
IP = '192.168.0.16'
# IP = '192.168.3.3'
PORT = 5589

window = None  # Initializing PredictUI


def excepthook(exc_type, exc_value, exc_tb):
    """
    For Exception traceback
    """
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    QtWidgets.QApplication.quit()


def run_tcp_server():
    global window

    sys.excepthook = excepthook
    window = PredictUI()
    server = MyTcpServer(IP, PORT, window)
    server.start()
    ret = window.run()
    print("event loop exited")
    sys.exit(ret)


if __name__ == "__main__":
    run_tcp_server()
