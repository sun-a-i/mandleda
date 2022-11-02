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
import pyupbit
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

            self.login()


            self.socket_thread = socket_client_thread()
            self.socket_thread.sock_msg.connect(self.msg_by_server)
            self.socket_thread.start()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def test_func(self):

        pass


    def login(self):
        global main_upbit
        if not os.path.exists(api_data_path):
            self.real_log_prt("[error] 로그인 정보 없음 API.txt 작성 후 로그인")
            main_upbit = False
            return False
        else:
            try:
                with open(api_data_path) as f:  # api 저장 데이터가 있으면 파일을 열어서
                    line = f.readlines()
                    access_key = line[0].strip()
                    secret_key = line[1].strip()
                    self.real_log_prt("[system] 로그인 정보 있음 로그인 시도")
                    main_upbit = pyupbit.Upbit(access_key, secret_key)
                    balance = main_upbit.get_balance(ticker="KRW")
                    self.real_log_prt("[system] 로그인 성공")
                    self.after_login_initial()

            except:
                self.real_log_prt("[error] 로그인 실패")
                main_upbit = False
                return False


    def after_login_initial(self):
        # self.update_balance()
        pass


    def order(self,is_buy, coin, amt):
        try:
            global main_upbit
            if is_buy:
                ret = main_upbit.buy_market_order(coin, price = amt)
            else:
                ret = main_upbit.buy_market_order(coin, price=amt)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def update_balance(self):
        try:
            balance = main_upbit.get_balance(ticker="KRW")
            self.money_label.setText(str(int(balance)))
        except:
            self.real_log_prt("[error] 잔고 update 실패")

    def real_log_prt(self, txt):
        self.real_log.addItem(txt)
        logger.debug(txt)


    @pyqtSlot(str)
    def msg_by_server(self,data):
        self.real_log_prt("[msg] 데이터 수신 : " + str(data))

        tmp = data.split(';')

        if tmp[0] == "BUY":
            #self.order(1, tmp[1],tmp[2])
            pass
        elif tmp[0] == "SEL":
            #self.order(0, tmp[1],tmp[2])
            pass
        else:
            self.real_log_widget.addItem(str(data))
            print("데이터 형식 맞지 않음 " + str(data))




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
                        txt = "02김도훈" #todo :  + main.name?
                        logger.debug("입장로그 : %s", txt)
                        self.send_msg(txt)
                        sock_con_flag = True
                        while True:
                            data = self.s.recv(1024).decode('utf-8')
                            logger.debug(f'수신된 데이터 :{data}')
                            self.sock_msg.emit(data)
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



