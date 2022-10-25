import sys
import os
import pickle
import time

from PyQt5.QtGui import QIcon, QMovie, QPixmap
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QTableWidgetItem
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QThread
import traceback

import datetime as dt
from datetime import datetime

#import telegram
#import pyupbit
import time
#====================logger=========================
import os
from logging.handlers import TimedRotatingFileHandler
import logging
from datetime import datetime
import traceback


if not os.path.exists('logFile'):
    os.makedirs('logFile')
nowDate = datetime.now()
filename = str("./logFile./" + nowDate.strftime("%Y-%m-%d_%H-%M") + "1.txt")
logger = logging.getLogger(__name__)

fileMaxByte = 10.24 * 1024 * 100
fileHandler = logging.handlers.TimedRotatingFileHandler(filename='./logFile/main.log', when='midnight', interval=1,
                                                        backupCount=10)

logger.addHandler(fileHandler)
fileHandler.suffix = "%Y-%m-%d_%H-%M1.log"

formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
fileHandler.setFormatter(formatter)

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

logger.setLevel(level=10)
#====================logger=========================

if not os.path.exists('DATA'):
    os.makedirs('DATA')

setting_data_path = './DATA/settings.pickle'
api_data_path = './DATA/API.txt'
telegram_data_path = './DATA/telegram.txt'

main_class = uic.loadUiType('./ui_data/main.ui')[0]

auto_flag = False



class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("upbit auto system")

            self.t1.clicked.connect(self.test_func)


        except Exception as e:
            logger.debug(e)

    def test_func(self):
        self.a = socket_client_thread()
        self.a.start()
        pass



class Mythread(QThread):
    #signal = pyqtSignal()

    def __init__(self):
        super().__init__()


    def run(self):
        #global auto_flag, main_upbit
        while True:
            try:
                if auto_flag:
                    pass
            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())

import socket
import requests

#HOST_socket = '192.168.0.7'
#내부아이피
TY_IP = '124.61.26.131'
DH_IP = '118.37.147.48'
CUSTOM_IP = '1.242.216.122'


HOST_socket = DH_IP
PORT_socket = 5000
sock_con_flag = False

class socket_client_thread(QThread):
    sock_msg = pyqtSignal(str) #todo : signal to main order
    def __init__(self):
        super().__init__()
        self.con = False
        logger.debug("socket_client_thread start")

    def send_msg(self, msg):
        global login_flag,test
        try:
            if self.con and (login_flag or test):
                self.s.sendall(msg.encode('utf-8'))
            else:
                logger.debug("서버 접속 불가, 메세지 전송되지 않음")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def run(self):
        global login_flag, test, sock_con_flag
        while True:
            try:
                if login_flag or test:
                    #time.sleep(10)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
                        self.s.connect((HOST_socket, PORT_socket))
                        self.con = True
                        logger.debug("소켓 서버 접속 완료")
                        #main.real_log_widget.addItem("소켓 서버 접속 완료")
                        txt = "02 김도훈" # + main.name?
                        logger.debug("입장로그 : %s", txt)
                        self.send_msg(txt)
                        sock_con_flag = True
                        while True:
                            data = self.s.recv(1024).decode('utf-8')
                            logger.debug(f'수신 데이터 :{data}')
                            #self.sock_msg.emit(data)
                else:
                    logger.debug("로그인 확인되지 않음")
            except Exception as e:
                logger.debug(e)
                #logger.debug(traceback.format_exc())
                self.con = False
                logger.debug("소켓 서버 접속 불가 재접속중 ...")
                #main.real_log_widget.addItem("소켓 서버 접속 불가 재접속중 ...")
                sock_con_flag = False
                time.sleep(1)






if __name__ == "__main__":
    global test
    test = True

    if test :
        global login_flag , main
        login_flag = 1
        app = QApplication(sys.argv)
        main = Main()
        main.show()
        app.exec_()



