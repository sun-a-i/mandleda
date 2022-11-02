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

import socket
import select
import requests
#import request
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

coin_Kname = {}
coin_Ename = {}
tickers = []

class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("upbit auto system")


            self.t1.clicked.connect(self.test_func)
            self.t2.clicked.connect(self.test_func2)
            self.t3.clicked.connect(self.test_func3)


            self.login()
            self.get_tickers()
            #한글, 영어 코인명 가져오기
            self.get_eng_workd()
            self.get_korean_workd()
            #자동완성 검색
            self.init_nameList()

            self.buy_btn.clicked.connect(self.buy_btn_func)
            self.sell_btn.clicked.connect(self.sell_btn_func)

            #=========소켓 서버 스레드
            self.socket_server = socket_server_thread()
            self.socket_server.start()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func(self):
        logger.debug("testbtn clicked")
        try:
            logger.debug(tickers)
            logger.debug(coin_Kname)
            logger.debug(coin_Ename)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func2(self):
        logger.debug("testbtn2 clicked")
        try:
            send_to_clients(0,'btc',0.2)
            send_to_clients(1, 'btc', 0.1)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func3(self):
        logger.debug("testbtn2 clicked")
        try:
            #logger.debug(self.socket_server.clients)
            self.add_coin_to_table()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def get_tickers(self):
        global tickers
        try:
            tickers = pyupbit.get_tickers(fiat='KRW')
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def get_eng_workd(self):
        global tickers, coin_Ename
        try:
            for i in range(len(tickers)):
                coin_Ename[tickers[i][4:]] = tickers[i]

        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def get_korean_workd(self):
        global tickers, coin_Kname
        try:
            url = "https://api.upbit.com/v1/market/all?isDetails=false"
            headers = {"Accept": "application/json"}
            response = requests.request("GET", url, headers=headers)
            t = response.text.split('"')
            k = 0
            for i in range(len(t)):
                if t[i] == 'market':
                    if t[i + 2] in tickers:
                        coin_Kname[t[i + 2]] = t[i + 6]
                        # logger.debug("%s = %s", t[i + 2], t[i + 6])
                        k = k + 1
            logger.debug("한글 name 불러들이기 성공, 총 = %s", k)
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def init_nameList(self):
        try:
            global coin_Kname, tickers, coin_Ename, trade_list

            # 한글이름
            kName = coin_Kname.values()
            kName = list(kName)

            # 영문이름
            eName = coin_Ename.keys()
            eName = list(eName)
            # logger.debug(eName)

            total_name = []
            for i in kName:
                total_name.append(i)

            for i in eName:
                total_name.append(i)

            completer = QCompleter(total_name)
            self.coin_search.setCompleter(completer)

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def after_login_initial(self):
        self.update_thread = Mythread()
        self.update_thread.signal.connect(self.update_table)
        self.update_thread.start()
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
                    if self.update_balance():
                        self.real_log_prt("[system] 로그인 성공")
                        self.after_login_initial()

            except:
                self.real_log_prt("[error] 로그인 실패")
                main_upbit = False
                return False

    def update_balance(self):
        try:
            balance = main_upbit.get_balance(ticker="KRW")
            self.money_label.setText(str(int(balance)))
            return True
        except:
            self.real_log_prt("[error] 잔고 update 실패")

    def order(self,is_buy, coin, amt):
        try:
            global main_upbit
            if is_buy:
                ret = main_upbit.buy_market_order(coin, price = amt)
            else:
                ret = main_upbit.sell_market_order(coin, volume = amt) #todo : 매도는 수량 기준 ?
            #todo : 메세지

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def real_log_prt(self, txt):
        self.real_log.addItem(txt)
        logger.debug(txt)

    def buy_btn_func(self):
        try:
            data = self.coin_search.text().upper()
            logger.debug(data)
            symbol = self.get_coin_symbol(data)
            if symbol:
               if self.per_radio.isChecked(): #퍼센트 구매
                   tmp = float(self.price_per.text())
                   if self.price_per.text().isdigit():#숫자인지
                       if tmp > 0 and tmp <= 100 : #100%보다 적게
                           amt = float(self.money_label.text()) * tmp / 100
                           self.real_log_prt("비율 금액 매수 symbol : " + str(symbol) + " amt : " + str(amt))
                           self.order(1,symbol,amt)
                       else:
                           txt = "[error] 구매 금액 에러 : 0~100 사이의 값"
                           self.floating_msg(txt)
                   else:
                       txt = "[error] 구매 비율 에러 : 자연수를 입력해야합니다."
                       self.floating_msg(txt)

               else:#지정가 구매
                   if self.price_pri.text().isdigit():
                       tmp = int(self.price_pri.text())
                       if tmp > 0 and tmp <= float(self.money_label.text()) : #가진돈보다 적게
                           amt = tmp
                           self.real_log_prt("지정 금액 매수 symbol : " + str(symbol) + " amt : " + str(amt))
                           self.order(1,symbol,amt)
                       else:
                           txt = "[error] 구매 금액 에러 : 소지금액 이하의 값"
                           self.floating_msg(txt)
                   else:
                       txt = "[error] 구매 금액 에러 : 숫자를 입력해야합니다."
                       self.floating_msg(txt)
            else:
                txt = "[error] 코인 이름 에러 : 정확하지 않은 코인명."
                self.floating_msg(txt)

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def floating_msg(self,txt):
        try:
            QMessageBox.information(self, '확인', txt)
            logger.debug(txt)
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def sell_btn_func(self):
        try:
            data = self.coin_search.text().upper()
            logger.debug(data)
            symbol = self.get_coin_symbol(data)
            if symbol:
                #amt = coin_list[symbol]["total"]
                #self.real_log_prt("매도 symbol : " + str(symbol) + " amt : " + str(amt))
                #self.order(0,symbol,amt)
                pass
            else:
                txt = "[error] 코인 이름 에러 : 정확하지 않은 코인명."
                self.floating_msg(txt)

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())


    def get_coin_symbol(self, data):
        global coin_Kname, tickers, coin_Ename
        try:
            #logger.debug("get_coin_symbol 호출 data : " + data)
            if data in tickers: #무조건 여기에서 걸려야함 ! 재귀로 구현하엿음
                #logger.debug("get_coin_symbol 성공 data : " + data)
                return data
            elif data in coin_Ename:
                return self.get_coin_symbol(coin_Ename[data])
            else:
                for symbol, k_name in coin_Kname.items():
                    if data == k_name:
                        return self.get_coin_symbol(symbol)
                #logger.debug("get_coin_symbol 실패 data : " + data)
                #self.real_log_prt("[system] 코인명 에러")
                return False

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())


    @pyqtSlot()
    def update_table(self):
        global coin_list
        try:
            self.table_coin.setRowCount(len(coin_list))

            #가지고 있는 것과 없는 것 비교

            idx = 0
            for coin_name in coin_list:
                stop_btn = QPushButton("중지")
                start_btn = QPushButton("시작")
                stop_btn.clicked.connect(lambda: self.handleButtonClicked(0))
                start_btn.clicked.connect(lambda: self.handleButtonClicked(1))

                #logger.debug(coin_name)

                self.table_coin.setItem(idx, 0, QTableWidgetItem(coin_list[coin_name]["currency"]))
                self.table_coin.setItem(idx, 1, QTableWidgetItem(coin_list[coin_name]["current_price"]))
                self.table_coin.setItem(idx, 3, QTableWidgetItem(coin_list[coin_name]["avg_buy_price"]))
                self.table_coin.setItem(idx, 4, QTableWidgetItem(coin_list[coin_name]["balance"]))
                self.table_coin.setItem(idx, 5, QTableWidgetItem(coin_list[coin_name]["total_price"]))
                #self.table_coin.setItem(idx, 0, QTableWidgetItem(i))

                #self.table_coin.setItem(idx, 3, QTableWidgetItem(str(coin_list[coin_name]["avr"])))

                self.table_coin.setCellWidget(idx, 6, stop_btn)
                self.table_coin.setCellWidget(idx, 7, start_btn)
                idx =+ 1

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())


    def handleButtonClicked(self,state):
        #button = QtGui.qApp.focusWidget()
        button = self.sender()
        index = self.table_coin.indexAt(button.pos())
        if index.isValid():
            print(index.row(), index.column())

class Mythread(QThread):
    signal = pyqtSignal()

    def __init__(self):
        super().__init__()


    def run(self):
        global auto_flag, main_upbit, coin_list
        while True:
            try:
                tmp = main_upbit.get_balances()
                #logger.debug(tmp)
                tmp_list = {}
                for i in tmp:
                    tmp = {}
                    for j,k in i.items():
                        tmp[j] = k
                    if tmp["currency"] == 'KRW':
                        main.money_label.setText(str(int(float(tmp["balance"])))) #update krw balance
                    else:
                        symbol = main.get_coin_symbol(tmp["currency"])
                        if symbol: #ETHF 등 제외
                            tmp_list[symbol] = {}
                            tmp_list[symbol] = tmp
                            tmp_list[symbol]["total_price"] = str(float(tmp_list[symbol]['avg_buy_price']) * float(tmp_list[symbol]['balance']))
                            tmp_list[symbol]["current_price"] = str(pyupbit.get_current_price(symbol))
                logger.debug(tmp_list)
                coin_list = tmp_list
                self.signal.emit()
                time.sleep(5)


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
                self.socket_try += 1
                if self.socket_try > 30:
                    self.socket_try = 0

                time.sleep(0.2)

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
                                                main.client_list.addItem("클라이언트 접속 : " + str(conn.getpeername()[0]))
                                                logger.debug("클라이언트 : " + data)

                                    except ConnectionResetError:
                                        client_ip  = sock.getpeername()[0]
                                        name = self.clients[client_ip]
                                        sock.close()
                                        self.socks.remove(sock)
                                        del self.clients[client_ip]
                                        logger.debug("클라이언트 접속 해제 : " + name)
                                        main.client_list.addItem("클라이언트 접속 해제 : " + str(client_ip))
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


def send_to_clients(is_buy, coin): #
    try:
        if main.per_radio.isChecked():
            #amt =
            pass

        if is_buy:
            txt = "BUY;" + coin + ";" + str(amt)
        else:
            txt = "SEL;" + coin + ";" + str(amt)

        main.socket_server.send_all(txt)
        main.real_log_prt("[msg] 메세지 전송됨 '" + txt + "'")

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