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

import socket
import select
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

main_class = uic.loadUiType('./ui_data/main_server.ui')[0]


auto_flag = False



class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("upbit auto system")


            self.t1.clicked.connect(self.test_func)
            self.t2.clicked.connect(self.test_func2)

            self.login()


        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func(self):
        logger.debug("testbtn clicked")
        try:
            self.a = socket_server_thread()
            self.a.start()
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func2(self):
        logger.debug("testbtn2 clicked")
        try:
            self.a.send_all("buy;btc;0.2")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def after_login_initial(self):
        #self.update_balance()
        #self.coin_list = pyupbit.get_tickers(fiat='KRW')
        pass

    def login(self):
        global main_upbit
        if not os.path.exists(api_data_path):
            self.real_log_print("[error] 로그인 정보 없음 API.txt 작성 후 로그인")
            return False
        else:
            try:
                with open(api_data_path) as f:  # api 저장 데이터가 있으면 파일을 열어서
                    line = f.readlines()
                    access_key = line[0].strip()
                    secret_key = line[1].strip()
                    self.real_log_print("[system] 로그인 정보 있음 로그인 시도")
                    main_upbit = pyupbit.Upbit(access_key, secret_key)
                    balance = main_upbit.get_balance(ticker="KRW")
                    self.real_log_print("[system] 로그인 성공")
                    self.after_login_initial()

            except:
                self.real_log_print("[error] 로그인 실패")
                main_upbit = False
                return False

    def update_balance(self):
        try:
            balance = main_upbit.get_balance(ticker="KRW")
            self.money_label.setText(str(int(balance)))
        except:
            self.real_log_print("[error] 잔고 update 실패")

    def real_log_print(self, txt):
        self.real_log.addItem(txt)
        logger.debug(txt)

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


SERVER_PORT = 5000
#외부아이피
TY_IP = '192.168.123.100'
DH_IP = '192.168.0.7'
CUSTOM_IP = '1.242.216.122'

class socket_server_thread(QThread):

    def __init__(self):
        super().__init__()
        self.socks = []
        self.con = False
        self.socket_try = 0
        self.clients = {}
        logger.debug("socker_server_start")

        global test
        if test:
            # 내 아이피
            self.SERVER_HOST = DH_IP
        else:
            # 고객사 아이피
            self.SERVER_HOST = CUSTOM_IP

    def run(self):
        global SERVER_PORT, main
        while self.con == False:
            try:
                logger.debug("asdasd1")
                self.socket_try += 1
                if self.socket_try > 30:
                    self.socket_try = 0

                time.sleep(0.2)
                logger.debug("asdasd")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
                    logger.debug("{} ,{}".format(self.SERVER_HOST, SERVER_PORT))

                    res = self.s.bind((self.SERVER_HOST, SERVER_PORT))

                    logger.debug("연결 상태 return = {} ".format(res))
                    self.s.listen()
                    self.con = True
                    self.socks = [self.s]
                    logger.debug('서버가 시작되었습니다.')

                    while True:
                        try:
                            self.readables, self.writeables, self.excpetions = select.select(self.socks, [], []) # 이벤트 대기 ex)클라이언트 접속, 리시브
                            for sock in self.readables:
                                if sock == self.s:  # 신규 클라이언트 접속
                                    newsock, addr = self.s.accept()
                                    self.socks.append(newsock)
                                    logger.debug("새로운 클라이언트 접속" +str(addr))
                                    #main.real_log_widget.addItem("새로운 클라이언트 접속")

                                else:  # 이미 접속한 클라이언트의 요청
                                    try:
                                        conn = sock
                                        data = conn.recv(1024).decode('utf-8')
                                        if len(data) > 1:
                                            logger.debug(f'데이터 수신 : {data}')
                                            if data[:2] =="02":
                                                data = data[2:]
                                                self.clients[conn.getpeername()[0]] = data
                                                #main.real_log_widget.addItem("클라이언트 접속 : " +data)
                                                logger.debug("클라이언트 : " + data)

                                    except ConnectionResetError:
                                        client_ip  = sock.getpeername()[0]
                                        name = self.clients[client_ip]
                                        sock.close()
                                        self.socks.remove(sock)
                                        del self.clients[client_ip]
                                        logger.debug("클라이언트 접속 해제 : " + name)
                                        #main.real_log_widget.addItem("클라이언트 접속 해제 : " + name)


                                    except Exception as e:
                                        logger.debug(traceback.format_exc())
                                        logger.debug(e)
                                        pass
                                        #중요정보 로그 !!
                        except Exception as e:
                            logger.debug(e)
                            logger.debug(traceback.format_exc())
            except Exception as e:
                server_flag = False
                logger.debug(e)
                logger.debug(traceback.format_exc())


    def send_all(self, data):
        try:
            global main
            if self.con:
                logger.debug("메세지 송신 : " + data)
                for i in self.socks:
                    if i != self.s:#본인을 제외한 모든 소켓에 송신
                        try:
                            name = self.clients[i.getpeername()[0]]
                        except:
                            logger.debug("찾을 수 없음")
                            name = '없음'

                        logger.debug(i)
                        logger.debug("수신자 : " + name + ", 메세지 : " + data)
                        #main.real_log_widget.addItem("수신자 : " + name + ", 메세지 : " + data + "전송 완료")
                        res = i.sendall(data.encode('utf-8'))
                        logger.debug(res)
            else:
                logger.debug("연결되지 않음 메세지 전송 실패")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


if __name__ == "__main__":
    try:
        global test
        test = True
        app = QApplication(sys.argv)
        main = Main()
        main.show()
        app.exec_()
    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())