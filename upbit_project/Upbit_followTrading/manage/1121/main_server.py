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
from PyQt5 import QtCore, QtGui, QtWidgets


import datetime as dt
from datetime import datetime

#import telegram
import pyupbit
import time

import socket
import select
import requests
#import request

import finplot as fplt
from qroundprogressbar import QRoundProgressBar
import datetime
from datetime import datetime

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
coin_list = {}
tickers = []

ax = object
coin_dic = {} #모든 코인
coin_dic_available = False #모든 코인 로딩 완료
current_price_dic = {} #모든 현재가 코인
import datetime



'''
coin_list = {'KRW-ETH': 
                 {'currency': 'ETH', #이름
                  'balance': '0.00696422',  #개수
                  'locked': '0', 
                  'avg_buy_price': '1579500', #평단가
                  'avg_buy_price_modified': False, 
                  'unit_currency': 'KRW', #화폐기준
                  
                  위까지 main_upbit.get_balances() 한 결과 전부 받아옴 
                  이하는 계산한 값
                  
                  'total_price': '10999.985490000001', #매수금액 balance * avg_buy_price 
                  'current_price': '1583000', #현재가, 매초 업데이트됨
                  'total_now_price': '11024.36026', #평가금액 현재가 * balance
                  'earing_rate': '0.22158911047799934', #손익률
                  'activate': None #활성화, 자동매매 중지, 활성화 플래그 변수
                  } 
             'KRW-BTC' : {...} , ... }

coin_dic = 5분봉 가격 500개 
'''

class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("upbit auto system")
            global run_program
            run_program = False

            self.t1.clicked.connect(self.test_func)
            #self.t2.clicked.connect(self.test_func2)
            #self.t3.clicked.connect(self.test_func3)
            self.table_coin.cellClicked.connect(self.table_cell_clicked_func)

            self.initial()
            self.login()
            self.get_tickers()
            #한글, 영어 코인명 가져오기
            self.get_eng_workd()
            self.get_korean_workd()
            #자동완성 검색
            self.init_nameList()

            self.start_btn.clicked.connect(lambda: self.state_func('start'))
            self.stop_btn.clicked.connect(lambda: self.state_func('stop'))

            self.chart_bun.currentIndexChanged.connect(lambda: self.coin_chart(self.coin_search_1.text()))
            self.buy_btn.clicked.connect(self.buy_btn_func)
            self.sell_btn.clicked.connect(self.sell_btn_func)

            # 우선 여기에 #todo : 다른 함수에서 부를 수 있는 전역함수, 모든 코인값가져옴
            #init_coin_dic()

            #=========소켓 서버 스레드
            self.socket_server = socket_server_thread()
            self.socket_server.start()


            self.state_func('stop')
            run_program = True
            logger.debug("main init 완료")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func(self):
        logger.debug("testbtn clicked")
        try:
            logger.debug(coin_list)
            for i in coin_list:
                logger.debug(i)
                logger.debug(len(coin_list[i]))
                logger.debug(coin_list[i])


        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func2(self):
        logger.debug("testbtn2 clicked")
        try:
            #send_to_clients(0,'btc')
            send_to_clients(1, 'btc')

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

    def initial(self):
        try:

            logger.debug('table init..')
            table = self.table_coin
            table.setColumnWidth(0, 80)
            table.setColumnWidth(2, 90)
            table.setColumnWidth(1, 110)
            table.setColumnWidth(3, 110)
            table.setColumnWidth(4, 120)
            table.setColumnWidth(5, 110)
            table.setColumnWidth(6, 110)
            table.setColumnWidth(7, 90)
            table.setColumnWidth(8, 90)


            #table.setAlignment(QtCore.Qt.AlignCenter)
            self.real_log.setFont(QtGui.QFont('맑은 고딕', 9))
            self.rpb = QRoundProgressBar()
            # self.rpb.setStyleSheet('QRoundProgressBar{background-color:#123;}')
            # self.rpb.setValue(15)
            self.gridLayout_2.addWidget(self.rpb)
            #global ax, axs, axo

            fplt.candle_bull_color = "#FF0000"
            fplt.candle_bull_body_color = "#FF0000"
            fplt.candle_bear_color = "#0000FF"
            fplt.display_timezone = datetime.timezone.utc
            fplt.show(qt_exec=False)

            global ax, df, plot
            ax = fplt.create_plot(init_zoom_periods=0)  # pygtgraph.graphicsItems.PlotItem
            #axo = ax.overlay()  # pygtgraph.graphicsItems.PlotItem
            #axs = [ax]  # finplot requres this property
            self.gridLayout.addWidget(ax.vb.win, 0, 0)  # ax.vb     (finplot.FinViewBox)

            self.table_coin.setFocusPolicy(QtCore.Qt.NoFocus)
            self.table_coin.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.table_coin.setSelectionMode(QAbstractItemView.NoSelection)
            self.table_coin.setShowGrid(False)
            # self.table_coin.setSelectionBehavior(QAbstractItemView.SelectRows)
            # self.table_coin.setSelectionMode(QAbstractItemView.SingleSelection)
            self.table_coin.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.table_coin.setEditTriggers(QAbstractItemView.NoEditTriggers)
            # self.table_coin.verticalHeader().setVisible(False)
            self.table_coin.horizontalHeader().setFocusPolicy(QtCore.Qt.NoFocus)
            self.table_coin.horizontalHeader().setFixedHeight(60)

            self.table_coin.horizontalHeader().setStyleSheet('''
                        QHeaderView {
                            /* set the bottom border of the header, in order to set a single 
                               border you must declare a generic border first or set all other 
                               borders */
                            border: none;
                            border-bottom: 0px ;
                            background-color:white;
                        }

                        QHeaderView::section:horizontal {
                            /* set the right border (as before, the overall border must be 
                               declared), and a minimum height, otherwise it will default to 
                               the minimum required height based on the contents (font and 
                               decoration sizes) */
                            border: none;
                            border-right: 0px ;
                            background-color:white;
                        }
                    ''')
            self.table_coin.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)


            self.table_coin.setShowGrid(False)
            #self.table_coin.setStyleSheet('background-color : red;')
            self.start_btn.setStyleSheet("""
                    QPushButton {
                        color: white ; 
                        background-color: gray
                    }
                    QPushButton:hover {
                        color: yellow;
                        background-color: red
                    }
                    QPushButton:pressed {
                        color: yellow;
                        background-color: gray
                    }
                    """)
            self.stop_btn.setStyleSheet("""
                        QPushButton {
                            color: white ; 
                            background-color: gray
                        }
                        QPushButton:hover {
                            color: yellow;
                            background-color: blue
                        }
                        QPushButton:pressed {
                            color: yellow;
                            background-color: gray
                        }
                    """)
            #self.coin_chart(self.coin_search_1.text())
            self.table_coin.setRowCount(0)

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
        try:
            self.update_thread = Mythread()
            self.update_thread.update_table_signal.connect(self.update_table)
            self.update_thread.update_coin_chart_signal.connect(lambda: self.coin_chart(self.coin_search_1.text()))
            self.update_thread.start()

            # todo : thread
            #self.condition_thread = condition_search_thread()
            #self.condition_thread.condition_func_signal.connect(self.auto_order)
            #self.condition_thread.start()

            pass
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def login(self):
        global main_upbit
        if not os.path.exists(api_data_path):
            self.real_log.addItem("[error] 로그인 정보 없음 API.txt 작성 후 로그인")
            main_upbit = False
            return False
        else:
            try:
                with open(api_data_path) as f:  # api 저장 데이터가 있으면 파일을 열어서
                    line = f.readlines()
                    access_key = line[0].strip()
                    secret_key = line[1].strip()
                    self.real_log.addItem("[system] 로그인 정보 있음 로그인 시도")
                    main_upbit = pyupbit.Upbit(access_key, secret_key)
                    if self.update_balance():
                        self.real_log.addItem("[system] 로그인 성공")
                        self.after_login_initial()
                    else:
                        main_upbit = False
                        return False

            except Exception as e:
                logger.debug("예외가 발생했습니다. %s", e)
                logger.debug(traceback.format_exc())
                self.real_log.addItem("[error] 로그인 실패")
                main_upbit = False
                return False

    def update_balance(self): #todo : del
        try:
            global main_upbit
            balance = main_upbit.get_balance(ticker="KRW")
            self.money_label.setText(format(round(balance), ','))
            #self.money_label.setText(str(int(balance)))
            return True
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            self.real_log_prt("[error] 잔고 update 실패")

    def order(self,is_buy, coin, amt):
        try:
            global main_upbit
            send_to_clients(is_buy, coin) #일단 날림 !

            if is_buy:
                ret = main_upbit.buy_market_order(coin, price = amt)

            else:
                ret = main_upbit.sell_market_order(coin, volume = amt)
                logger.debug(ret)

            return self.ckeck_order_state(ret)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def ckeck_order_state(self,ret):
        try:
            if ret == None:
                logger.debug("주문 : None 에러")
                return False
            elif type(ret) == dict:
                if 'error' in ret:
                    logger.debug(ret)
                    logger.debug("주문 : 에러메세지 수신")
                    return False
                else:
                    logger.debug("주문 : 성공")
                    return True
            else:
                logger.debug("주문 : 알수없는오류")
                logger.debug(ret)
                return False

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def real_log_prt(self, txt):
        try:
            self.real_log.addItem(txt)
            logger.debug(txt)
            self.real_log.scrollToBottom()
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

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
                           amt = float(self.money_label.text().replace(',','')) * tmp / 100
                           if amt >= 5000:
                               txt = str(symbol) + " : " + str(amt)
                               reply = QMessageBox.question(self, '확인', txt + '원 매수 하시겠습니까?')
                               if reply == QMessageBox.Yes:
                                   if self.order(1,symbol,amt):
                                       self.real_log_prt("비율 금액 매수 " + str(symbol) + " : " + str(amt))
                                   else:
                                       txt = "[error] 매수 에러"
                                       self.floating_msg(txt)
                           else:
                               txt = "[error] 구매 금액 에러 : 최소주문 5000원 이상"
                               self.floating_msg(txt)
                       else:
                           txt = "[error] 구매 금액 에러 : 0~100 사이의 값"
                           self.floating_msg(txt)
                   else:
                       txt = "[error] 구매 비율 에러 : 자연수를 입력해야합니다."
                       self.floating_msg(txt)

               else:#지정가 구매
                   if self.price_pri.text().isdigit():
                       tmp = int(self.price_pri.text())
                       if tmp > 0 and tmp <= float(self.money_label.text().replace(',','')) : #가진돈보다 적게
                           amt = tmp
                           if amt >= 5000:
                               txt = str(symbol) + " : " + str(amt)
                               reply = QMessageBox.question(self, '확인', txt + '원 매수 하시겠습니까?')
                               if reply == QMessageBox.Yes:
                                   if self.order(1,symbol,amt):
                                       self.real_log_prt("지정 금액 매수 " + str(symbol) + " : " + str(amt))
                                   else:
                                       txt = "[error] 구매 에러"
                                       self.floating_msg(txt)
                           else:
                               txt = "[error] 구매 금액 에러 : 최소주문 5000원 이상"
                               self.floating_msg(txt)
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
            global coin_list
            data = self.coin_search.text().upper()
            logger.debug(data)
            symbol = self.get_coin_symbol(data)
            if symbol:
                if symbol in coin_list:
                    amt = coin_list[symbol]["balance"]
                    txt = str(symbol) + " : " + str(amt)
                    reply = QMessageBox.question(self, '확인', txt + '개 매도 하시겠습니까?')
                    if reply == QMessageBox.Yes:
                        if self.order(0,symbol,amt):
                            self.real_log_prt("전량 매도 " + str(symbol) + " : " + str(amt))
                        else:
                            txt = "[error] 매도 에러"
                            self.floating_msg(txt)
                else:
                    txt = "[error] 코인 에러 : 소지하지 않은 코인명."
                    self.floating_msg(txt)
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

    def table_cell_clicked_func(self, row, column):
        try:
            global coin_list
            item = self.table_coin.item(row, 0)
            value = item.text()
            label_string = 'Cell Clicked Row: ' + str(row + 1) + ', Column: ' + str(column + 1) + ', Value: ' + str(
                value)
            symbol =  self.get_coin_symbol(value)
            self.focus_coin_update(symbol)
            self.coin_search.setText(symbol)
            logger.debug(label_string)
            self.coin_chart(symbol)
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def focus_coin_update(self, symbol):
        try:
            symbol = self.get_coin_symbol(symbol)
            if symbol:
                if symbol in coin_list:
                    #self.coin_search.setText(symbol)
                    self.coin_search_1.setText(symbol)
                    self.coin_search_2.setText(format(round(float(coin_list[symbol]["current_price"])), ','))

                    txt = round(float(coin_list[symbol]["earing_rate"]), 2)
                    if coin_list[symbol]["earing_rate"][0] != '-':
                        txt = "▲" + str(txt)
                        self.coin_search_3.setText(txt)
                        self.coin_search_2.setStyleSheet('QLabel{color:red;background-color:gray;}')
                        self.coin_search_3.setStyleSheet('QLabel{color:red;background-color:gray;}')
                    else:
                        txt = "▼" + str(txt)
                        self.coin_search_3.setText(txt)
                        self.coin_search_2.setStyleSheet('QLabel{color:blue;background-color:gray;}')
                        self.coin_search_3.setStyleSheet('QLabel{color:blue;background-color:gray;}')
                else:
                    self.coin_search_1.setText(symbol)
                    self.coin_search_2.setText('-')
                    self.coin_search_3.setText('-')

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    #@pyqtSlot()#list,list,list? or dict oly? or for문? str, str, str?#todo : thread
    def auto_order(self,is_buy,coin, amt = 0):
        try:
            return 0

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    @pyqtSlot()
    def coin_chart(self, coin):
        try:
            global coin_list
            symbol = self.get_coin_symbol(coin)
            if symbol:
                if self.bun_to_min():
                    global ax, df, plot
                    self.gridLayout.removeWidget(self.gridLayout.itemAtPosition(0,0).widget())
                    ax.clear()
                    fplt.close()
                    ax = fplt.create_plot()

                    # if 'df' in coin_list[symbol]:
                    #     pass
                    # else:
                    #     coin_list[symbol]['df'] = pyupbit.get_ohlcv(symbol, self.bun_to_min(), 200)

                    df = pyupbit.get_ohlcv(symbol, self.bun_to_min(), 200)
                    plot = fplt.candlestick_ochl(df[['open', 'close', 'high', 'low']])

                    #fplt.set_x_pos(0, 200, ax) #시작위치 줌
                    fplt.refresh()
                    self.gridLayout.addWidget(ax.vb.win, 0, 0)  # ax.vb     (finplot.FinViewBox)


        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    @pyqtSlot(dict,dict)
    def update_table(self, coin_dict, jango_dict):
        try:
            global coin_list
            coin_list = coin_dict
            jango_list = jango_dict
            #logger.debug(len(coin_list))
            self.money_label.setText(format(round(float(jango_list["balance"])),','))  # update krw balance
            self.money_label_2.setText(format(round(jango_list["total_buy"]), ','))
            self.money_label_3.setText(format(round(jango_list["total_now_buy"]), ','))
            self.money_label_4.setText(str(round(jango_list["total_rate"],2)))
            self.rpb.setValue(
                (jango_list["total_buy"] / (float(jango_list["balance"]) + float(jango_list["total_buy"]))) * 100)

            #self.table_coin.setRowCount(len(coin_list))
            self.focus_coin_update(self.coin_search_1.text())


            if len(coin_list) != self.table_coin.rowCount():
                self.table_coin.setRowCount(len(coin_list))
                idx = 0
                for coin_name in coin_list:
                    stop_btn = QPushButton("중지")
                    start_btn = QPushButton("활성화")


                    start_btn.setStyleSheet("color:white;background-color:red")
                    stop_btn.setStyleSheet("color:white;background-color:blue")

                    #button.setStyleSheet("color:(33,33,00)")
                    self.table_coin.setItem(idx, 0, QTableWidgetItem(coin_list[coin_name]["currency"]))
                    if float(coin_list[coin_name]["current_price"]) < 10:
                        self.table_coin.setItem(idx, 1, QTableWidgetItem(
                            format(round(float(coin_list[coin_name]["current_price"]), 2), ',')))  #
                    elif float(coin_list[coin_name]["current_price"]) < 100:
                        self.table_coin.setItem(idx, 1, QTableWidgetItem(
                            format(round(float(coin_list[coin_name]["current_price"]), 1), ',')))  #
                    else:
                        self.table_coin.setItem(idx, 1, QTableWidgetItem(
                            format(round(float(coin_list[coin_name]["current_price"])), ',')))  #

                    txt = str(round(float(coin_list[coin_name]["earing_rate"]), 2))
                    if coin_list[coin_name]["earing_rate"][0] != '-':
                        txt = "▲" + str(txt)
                        self.table_coin.setItem(idx, 2, QTableWidgetItem(txt))
                        self.table_coin.item(idx, 2).setForeground(QtGui.QColor(255, 0, 0))
                    else:
                        txt = "▼" + str(txt)
                        self.table_coin.setItem(idx, 2, QTableWidgetItem(txt))
                        self.table_coin.item(idx, 2).setForeground(QtGui.QColor(0, 0, 255))

                    self.table_coin.setItem(idx, 3, QTableWidgetItem(
                        format(round(float(coin_list[coin_name]["avg_buy_price"])), ',')))  #
                    self.table_coin.setItem(idx, 4, QTableWidgetItem(coin_list[coin_name]["balance"]))
                    self.table_coin.setItem(idx, 5, QTableWidgetItem(
                        format(round(float(coin_list[coin_name]["total_price"])), ',')))  #
                    self.table_coin.setItem(idx, 6, QTableWidgetItem(
                        format(round(float(coin_list[coin_name]["total_now_price"])), ',')))  #

                    self.table_coin.item(idx, 0).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.table_coin.item(idx, 1).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.table_coin.item(idx, 2).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                    self.table_coin.item(idx, 3).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.table_coin.item(idx, 4).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.table_coin.item(idx, 5).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.table_coin.item(idx, 6).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    self.table_coin.setRowHeight(idx, 60)
                    stop_btn.clicked.connect(lambda: self.handleButtonClicked(0))
                    start_btn.clicked.connect(lambda: self.handleButtonClicked(1))
                    self.table_coin.setCellWidget(idx, 7, stop_btn)
                    self.table_coin.setCellWidget(idx, 8, start_btn)
                    if coin_list[coin_name]['activate'] != None:
                        if coin_list[coin_name]['activate']:
                            self.change_state_button(1, idx, 8)
                        else:
                            self.change_state_button(0, idx, 7)
                    idx += 1


            idx = 0

            for coin_name in coin_list:
                #logger.debug(coin_name)
                self.table_coin.setItem(idx, 0, QTableWidgetItem(coin_list[coin_name]["currency"]))
                if float(coin_list[coin_name]["current_price"]) < 10 :
                    self.table_coin.setItem(idx, 1, QTableWidgetItem(format(round(float(coin_list[coin_name]["current_price"]),2),',')))#
                elif float(coin_list[coin_name]["current_price"]) < 100 :
                    self.table_coin.setItem(idx, 1, QTableWidgetItem(format(round(float(coin_list[coin_name]["current_price"]),1),',')))#
                else:
                    self.table_coin.setItem(idx, 1, QTableWidgetItem(format(round(float(coin_list[coin_name]["current_price"])),',')))#

                txt = str(round(float(coin_list[coin_name]["earing_rate"]),2))
                if coin_list[coin_name]["earing_rate"][0] != '-':
                    txt = "▲" + str(txt)
                    self.table_coin.setItem(idx, 2, QTableWidgetItem(txt))
                    self.table_coin.item(idx, 2).setForeground(QtGui.QColor(255, 0, 0))
                else:
                    txt = "▼" + str(txt)
                    self.table_coin.setItem(idx, 2, QTableWidgetItem(txt))
                    self.table_coin.item(idx, 2).setForeground(QtGui.QColor(0, 0, 255))

                self.table_coin.setItem(idx, 3, QTableWidgetItem(format(round(float(coin_list[coin_name]["avg_buy_price"])),',')))#
                self.table_coin.setItem(idx, 4, QTableWidgetItem(coin_list[coin_name]["balance"]))
                self.table_coin.setItem(idx, 5, QTableWidgetItem(format(round(float(coin_list[coin_name]["total_price"])),',')))#
                self.table_coin.setItem(idx, 6, QTableWidgetItem(format(round(float(coin_list[coin_name]["total_now_price"])),',')))#

                self.table_coin.item(idx, 0).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.table_coin.item(idx, 1).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 2).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.table_coin.item(idx, 3).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 4).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 5).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 6).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.setRowHeight(idx, 60)
                #logger.debug(coin_name)

                idx += 1

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def bun_to_min(self):
        try:
            nbun = self.chart_bun.currentText()
            if nbun == '5분':
                return 'minute5'
            elif nbun == '15분':
                return 'minute15'
            elif nbun == '30분':
                return 'minute30'
            elif nbun == '1시간':
                return 'minute60'
            elif nbun == '4시간':
                return 'minute240'
            elif nbun == '1일':
                return 'day'
            else:
                return False

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def handleButtonClicked(self,is_activate):
        try:
            global coin_list
            #button = QtGui.qApp.focusWidget()
            button = self.sender()
            index = self.table_coin.indexAt(button.pos())
            if index.isValid():
                #print(index.row(), index.column())

                self.change_state_button(is_activate, index.row(), index.column())


        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())


    def change_state_button(self,is_activate, row, col):
        try:
            button = self.table_coin.cellWidget(row, col)
            item = self.table_coin.item(row, 0)
            value = item.text()

            if is_activate:
                txt = "매수 활성화"

                # button.setEnabled(False) #진짜 개 얼탱이가 없네 진짜
                button.setStyleSheet("color:gray;background-color:#FFCCCC")
                coin_list[self.get_coin_symbol(value)]["activate"] = True

                other_button = self.table_coin.cellWidget(row, col - 1)
                other_button.setEnabled(True)
                other_button.setStyleSheet("color:white;background-color:blue")

            else:
                txt = "매수 중지"
                # button.setEnabled(False)
                button.setStyleSheet("color:gray;background-color:#333300")
                coin_list[self.get_coin_symbol(value)]["activate"] = False

                other_button = self.table_coin.cellWidget(row, col + 1)
                other_button.setEnabled(True)
                other_button.setStyleSheet("color:white;background-color:red")

            label_string = txt + ' Clicked , Value: ' + str(value)
            logger.debug(label_string)

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def state_func(self, state):
        global auto_flag
        try:
            if state == 'start':

                auto_flag = True
                self.start_btn.setEnabled(False)
                self.start_btn.setStyleSheet("color:gray")
                self.stop_btn.setEnabled(True)
                self.stop_btn.setStyleSheet("color:white")
                self.stop_btn.setStyleSheet("background:blue")

                # 자동매매 시작 버튼 클릭시 옵션값 변경 못하도록 변경

                self.real_log_prt("[system] 자동매매 시작")
            else:
                auto_flag = False
                self.start_btn.setEnabled(True)
                self.start_btn.setStyleSheet("color:white")
                self.start_btn.setStyleSheet("background:red")
                self.stop_btn.setEnabled(False)
                self.stop_btn.setStyleSheet("color:gray")

                # 자동매매 중지 버튼 클릭시 옵션값 변경 가능하도록 변경

                self.real_log_prt("[system] 자동매매 종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())



class Mythread(QThread):
    update_table_signal = pyqtSignal(dict,dict)
    update_coin_chart_signal = pyqtSignal()
    def __init__(self):
        super().__init__()

    def run(self):
        time.sleep(1)
        while True:
            try:
                if run_program:
                    coin_dict,jango_dict = update_coin_list()
                    self.update_table_signal.emit(coin_dict, jango_dict)

                    if update_coin_dic():
                        logger.debug("coin_dic 업데이트")
                        if update_coin_chart():
                            logger.debug("차트 업데이트")
                            self.update_coin_chart_signal.emit()

                        time.sleep(5)


                time.sleep(1)

            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())


class condition_search_thread(QThread):
    #condition_func_signal = pyqtSignal() #list,list,list?  #todo : thread

    def __init__(self):
        super().__init__()

    def run(self):

        while True:
            try:
                global coin_dic

                #
                time.sleep(1)

                """
                condition_list = condition_func()
                if condition_list:
                    self.condition_func_signal.emit(condition_list)
                
                
                """

            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())




def condition_func(coin_dict): #조건검색하는 함수
    return True


def update_coin_dic():
    try:
        global coin_dic
        now_time = dt.datetime.now()
        if now_time.minute % 5 == 0 and now_time.second < 5:
            if coin_dic.keys() == current_price_dic.keys():
                #logger.debug('coin dic update 시작')
                for coin in coin_dic:
                    if coin in ncoin_dic and coin in current_price_dic:
                        coin_dic[coin].append(current_price_dic[coin])
                    else:
                        logger.debug('coin dic 맞지 않음')
                    if len(coin_dic[coin]) > 500:
                        del coin_dic[coin][0]
                    #logger.debug(coin_dic[coin])
                logger.debug('coin dic update 완료됨')
                return True
            else:
                logger.debug('coin_dic update 중 current_price_dic와 coin_dic의 키가 맞지 않음 !')
                return False

        return False

    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())


def init_coin_dic():
    logger.debug("init_coin_dic start")
    try:
        global coin_dic
        tmp_dic = {}
        idx = 0
        for coin in tickers:
            df = pyupbit.get_ohlcv(coin, 'minute5', 3)
            price_list = df['close'].to_list() #제일 뒤에가 최근
            #logger.debug(df['close'])
            #logger.debug(price_list)
            tmp_dic[coin] = price_list
            time.sleep(0.5)
            idx += 1
            logger.debug("init_coin_dic : " + str(idx)+'/' +str(len(tickers)))

        coin_dic = tmp_dic
       #logger.debug(coin_dic)
        logger.debug(len(coin_dic))

    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())



def update_coin_chart():
    try:
        ret = False
        now_time = dt.datetime.now()
        nbun = main.chart_bun.currentText()

        if nbun == '5분' and now_time.minute % 5 == 0 and now_time.second < 5:
            return True
        elif nbun == '15분' and now_time.minute % 15 == 0 and now_time.second < 5:
            return True
        elif nbun == '30분' and now_time.minute % 30 == 0 and now_time.second < 5:
            return True
        elif nbun == '1시간' and now_time.minute == 0 and now_time.second < 5:
            return True
        elif nbun == '4시간' and now_time.hour % 4 == 0 and now_time.second < 5:
            return True
        elif nbun == '1일' and now_time.hour == 9 and now_time.minute == 0 and now_time.second < 5:
            return True
        else:
            return False

    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())

# coin list update func
def update_coin_list():
    try:
        global auto_flag, main_upbit, tickers, current_price_dic
        tmp = main_upbit.get_balances()
        #logger.debug(tmp)
        tmp_list = {}
        tmp_jango_list = {}
        for i in tmp:
            tmp = {}
            for j, k in i.items():
                tmp[j] = k
            if tmp["currency"] == 'KRW':
                #main.money_label.setText(format(round(float(tmp["balance"])),','))  # update krw balance
                tmp_jango_list["balance"] = tmp["balance"]

                pass
            else:
                symbol = main.get_coin_symbol(tmp["currency"])
                if symbol:  # ETHF 등 제외
                    tmp_list[symbol] = {}
                    tmp_list[symbol] = tmp
                    tmp_list[symbol]["total_price"] = str(
                        float(tmp_list[symbol]['avg_buy_price']) * float(tmp_list[symbol]['balance']))
        #logger.debug(tmp_list)
        current_list = {}

        current_price_dic = pyupbit.get_current_price(tickers)

        for coin in tmp_list.keys() :
            current_list[coin] = current_price_dic[coin]

        #logger.debug(tmp_list.keys())
        #logger.debug(current_list)

        total_buy = 0
        total_now_buy = 0

        for symbol in tmp_list:
            tmp_list[symbol]["current_price"] = str(current_list[symbol])

            tmp_list[symbol]["total_now_price"] = str(
                float(tmp_list[symbol]['current_price']) * float(tmp_list[symbol]['balance']))

            tmp_list[symbol]["earing_rate"] = str(((float(tmp_list[symbol]["current_price"]) - float(
                tmp_list[symbol]['avg_buy_price'])) / float(tmp_list[symbol]['avg_buy_price'])) * 100)

            total_buy += float(tmp_list[symbol]["total_price"])
            total_now_buy += float(tmp_list[symbol]["total_now_price"])

            #logger.debug(tmp_list)
            #logger.debug(coin_list)
            if coin_list != {}:
                if symbol in coin_list:
                    if "activate" in coin_list[symbol]:
                        tmp_list[symbol]["activate"] = coin_list[symbol]["activate"]
                    else:
                        tmp_list[symbol]["activate"] = None
                else:
                    tmp_list[symbol]["activate"] = None
            else:
                tmp_list[symbol]["activate"] = None

        if total_buy != 0:
            total_rate = ((float(total_now_buy) - float(total_buy)) / float(total_buy)) * 100
        else:
            total_rate = 0
        tmp_jango_list["total_buy"] = total_buy
        tmp_jango_list["total_now_buy"] = total_now_buy
        tmp_jango_list["total_rate"] = total_rate



        return tmp_list,tmp_jango_list


    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())


SERVER_PORT = 5000
#외부아이피
TY_IP = '192.168.123.100'
DH_IP = '192.168.0.7'
DH_OFFICE_IP = '175.212.249.4'
CUSTOM_IP = '1.242.216.122'

class socket_server_thread(QThread):

    def __init__(self):
        try:
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
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def run(self):
        try:
            time.sleep(2)
            global SERVER_PORT, main
            while self.con == False:
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
                    main.real_log_prt('[system] 서버가 시작되었습니다.')

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
        logger.debug(str(is_buy)+str(coin))
        if main.per_radio.isChecked():
            p_amt = "per;" + str(float(main.price_per.text())/100)
        else:
            p_amt = "pri;" + main.price_pri.text()

        if is_buy:
            txt = "BUY;" + coin + ";" + p_amt
        else:
            txt = "SEL;" + coin

        main.socket_server.send_all(txt)
        main.real_log_prt("[msg] 메세지 전송됨 '" + txt + "'")

    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())


stylesheet = """
    QTableWidget {
        background-color: white; 
    }

    QTableWidget::item {
        color: gray;                    
        background-color: gray;
    }

"""


if __name__ == "__main__":
    try:
        global test
        test = True
        app = QApplication(sys.argv)
        app.setStyleSheet(stylesheet)
        app.setStyleSheet('QTableView::item {border-top: 1px solid #d6d9dc;}')
        main = Main()
        main.show()
        app.exec_()
    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())