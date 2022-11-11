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
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QAction,
                             QTableWidget, QTableWidgetItem, QVBoxLayout, QAbstractItemView)
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush
import pyupbit
import matplotlib.pyplot as plt
from mplfinance.original_flavor import candlestick_ohlc
import matplotlib.dates as mpdates

from qroundprogressbar import QRoundProgressBar
# pip install qroundprogressbar
import datetime as dt
from datetime import datetime
import finplot as fplt

import pyupbit
import time






# ====================logger=========================
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
# ====================logger=========================

if not os.path.exists('DATA'):
    os.makedirs('DATA')

setting_data_path = './DATA/settings.pickle'
api_data_path = './DATA/API.txt'
telegram_data_path = './DATA/telegram.txt'

main_class = uic.loadUiType('./ui_data/main_client.ui')[0]

auto_flag = False
login_flag = False
coin_Kname = {}
coin_Ename = {}
tickers = []


from dateutil.tz import gettz
# fplt.display_timezone = gettz('Asia/Jakarta')

# ... or in UTC = "display same as timezone-unaware data"
import datetime

# todo : pandas 아닌가 ?

"""
fin_plot/class YAxisItem(pg.AxisItem):/def tickStrings(self, values, scale, spacing):

return [format(xform(value), ',.12g') for value in values]
#return [self.next_fmt%xform(value) for value in values]

"""


class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("upbit auto system")

            # self.t1.clicked.connect(self.test_func)
            self.init()
            self.login()

            self.get_tickers()
            # 한글, 영어 코인명 가져오기
            self.get_eng_workd()
            self.get_korean_workd()
            # 자동완성 검색
            self.table_coin.cellClicked.connect(self.table_cell_clicked_func)
            self.chart_bun.currentIndexChanged.connect(lambda: self.coin_chart(self.coin_search.text()))


            self.socket_thread = socket_client_thread()
            self.socket_thread.sock_msg.connect(self.msg_by_server)
            self.socket_thread.start()

            self.update_thread = Mythread()
            self.update_thread.update_table_signal.connect(self.update_table)
            self.update_thread.start()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func(self):

        pass

    def init(self):
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
        table.setFont(QtGui.QFont('맑은 고딕', 9))
        self.real_log.setFont(QtGui.QFont('맑은 고딕', 9))
        self.rpb = QRoundProgressBar()
        # self.rpb.setStyleSheet('QRoundProgressBar{background-color:#123;}')
        # self.rpb.setValue(15)
        self.gridLayout_2.addWidget(self.rpb)
        global ax, axs, axo
        ax = fplt.create_plot(init_zoom_periods=0)  # pygtgraph.graphicsItems.PlotItem
        axo = ax.overlay()  # pygtgraph.graphicsItems.PlotItem
        axs = [ax]  # finplot requres this property

        fplt.candle_bull_color = "#FF0000"
        fplt.candle_bull_body_color = "#FF0000"
        fplt.candle_bear_color = "#0000FF"
        fplt.display_timezone = datetime.timezone.utc
        fplt.show(qt_exec=False)
        self.gridLayout.addWidget(ax.vb.win, 0, 0)  # ax.vb     (finplot.FinViewBox)

        self.table_coin.setFocusPolicy(QtCore.Qt.NoFocus)
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
        self.trading_start_btn.setStyleSheet("""
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
        self.trading_stop_btn.setStyleSheet("""
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

    def login(self):
        global main_upbit, login_flag
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
                    login_flag = True

            except:
                self.real_log_prt("[error] 로그인 실패")
                main_upbit = False
                return False

    def after_login_initial(self):
        # self.update_balance()
        pass

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

    def get_coin_symbol(self, data):
        global coin_Kname, tickers, coin_Ename
        try:
            # logger.debug("get_coin_symbol 호출 data : " + data)
            if data in tickers:  # 무조건 여기에서 걸려야함 ! 재귀로 구현하엿음
                # logger.debug("get_coin_symbol 성공 data : " + data)
                return data
            elif data in coin_Ename:
                return self.get_coin_symbol(coin_Ename[data])
            else:
                for symbol, k_name in coin_Kname.items():
                    if data == k_name:
                        return self.get_coin_symbol(symbol)
                # logger.debug("get_coin_symbol 실패 data : " + data)
                # self.real_log_prt("[system] 코인명 에러")
                return False
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def order(self, is_buy, coin, amt):
        try:
            global main_upbit
            if is_buy:
                ret = main_upbit.buy_market_order(coin, price=amt)
                return self.ckeck_order_state(ret)

            else:
                ret = main_upbit.sell_market_order(coin, volume=amt)
                logger.debug(ret)
                # return self.ckeck_order_state(ret)
            # todo : 메세지

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def ckeck_order_state(self, ret):
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
    def msg_by_server(self, data):
        self.real_log_prt("[msg] 데이터 수신 : " + str(data))
        global coin_list
        tmp = data.split(';')
        #BUY;KRW-BTC;per;0.1
        #SEL;KRW-BTC;
        if tmp[0] == "BUY" and len(tmp) == 4:
            if tmp[2] == 'per':
                amt = int(float(tmp[3]) * int(self.money_label.text().replace(',','')))
                if amt < 5000 :
                    amt = 5000
                    txt = "최소주문금액보다 낮은 비율 금액, 최소주문금액 매수 " + str(round(float(tmp[3]) * 100)) + '% : ' + str(amt) + "원"
                else:
                    txt = "비율 금액 매수 소지금액의 " + str(round(float(tmp[3]) * 100)) + '% : ' + str(amt) + "원"
            elif tmp[2] == 'pri':
                amt = int(tmp[3])
                if int(self.money_label.text().replace(',','')) < amt :
                    amt = int(self.money_label.text().replace(',',''))
                    txt = "소지금액보다 많은 지정금액, 소지금액 전부 매수 " + str(amt) + "원"
                elif int(self.money_label.text().replace(',','')) < 5000:
                    self.real_log_prt("[매수] 소지금액 오류 : ")
                    return False
                else:
                    txt = "지정 금액 매수  " + str(amt) + "원"
            else:
                self.real_log_prt("[msg] 데이터 형식 맞지 않음 : " + str(data))
                return False

            if self.order(1, tmp[1],amt):
                self.real_log_prt("[매수] : " + txt)
            else:
                self.real_log_prt("[매수] 오류 : ")

        elif tmp[0] == "SEL":
            symbol = self.get_coin_symbol(tmp[1])
            amt = coin_list[symbol]["balance"]
            if self.order(0, symbol,amt):
                self.real_log_prt("[매도]  : " + symbol + ' 수량 : ' + str(amt))
            else:
                self.real_log_prt("[매도] 오류 : ")
        else:
            self.real_log_prt("[msg] 데이터 형식 맞지 않음 : " + str(data))

    @pyqtSlot(dict, dict)
    def update_table(self, coin_dict, jango_dict):
        try:

            global coin_list
            coin_list = coin_dict
            jango_list = jango_dict
            # logger.debug(len(coin_list))
            self.money_label.setText(format(round(float(jango_list["balance"])), ','))  # update krw balance
            self.money_label_2.setText(format(round(jango_list["total_buy"]), ','))
            self.money_label_3.setText(format(round(jango_list["total_now_buy"]), ','))
            self.money_label_4.setText(str(round(jango_list["total_rate"], 2)))

            # self.coin_per_cash.setText( str(round( jango_list["total_buy"] / (float(jango_list["balance"]) + jango_list["total_buy"]) , 2)))
            # self.coin_per_cash.setText( )
            # self.coin_per_cash = roundProgressBar()
            # self.coin_per_cash.rpb_setValue()

            # logger.debug((    )))
            self.rpb.setValue(
                (jango_list["total_buy"] / (float(jango_list["balance"]) + float(jango_list["total_buy"]))) * 100)

            self.table_coin.setRowCount(len(coin_list))
            self.focus_coin_update(self.coin_search.text())

            idx = 0

            for coin_name in coin_list:
                # logger.debug(coin_name)
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

                # needs pyqt version >= 5.15.7
                self.table_coin.item(idx, 0).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.table_coin.item(idx, 1).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 2).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.table_coin.item(idx, 3).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 4).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 5).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 6).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.setRowHeight(idx, 60)
                # logger.debug(coin_name)
                idx += 1

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def bun_to_min(self):
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

    def handleButtonClicked(self, state):
        try:
            # button = QtGui.qApp.focusWidget()
            button = self.sender()
            index = self.table_coin.indexAt(button.pos())
            if index.isValid():
                # print(index.row(), index.column())
                item = self.table_coin.item(index.row(), 0)
                value = item.text()
                if state:
                    txt = "매수 활성화"
                else:
                    txt = "매수 중지"
                label_string = txt + ' Clicked , Value: ' + str(value)
                # self.coin_search.setText(value)
                logger.debug(label_string)
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def real_log_prt(self, txt):
        try:
            self.real_log.addItem(txt)
            logger.debug(txt)
            # self.real_log.scrollToBottom()
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
            self.focus_coin_update(self.get_coin_symbol(value))
            logger.debug(label_string)
            self.coin_chart(value)
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def focus_coin_update(self, symbol):
        try:
            symbol = self.get_coin_symbol(symbol)
            if symbol:
                self.coin_search.setText(symbol)
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


        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def coin_chart(self, coin):
        try:
            symbol = self.get_coin_symbol(coin)
            if symbol:
                if self.bun_to_min():
                    global ax, axs, axo

                    ax = fplt.create_plot()  # pygtgraph.graphicsItems.PlotItem
                    axo = ax.overlay()  # pygtgraph.graphicsItems.PlotItem
                    axs = [ax]  # finplot requres this property
                    self.gridLayout.addWidget(ax.vb.win, 0, 0)  # ax.vb     (finplot.FinViewBox)

                    df = pyupbit.get_ohlcv(symbol, self.bun_to_min(), 200)
                    self.plot = fplt.candlestick_ochl(df[['open', 'close', 'high', 'low']])

                    #fplt.set_x_pos(0, 200, ax) #시작위치 줌
                    fplt.refresh()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


# coin list update func
def update_coin_list():
    try:
        global auto_flag, main_upbit
        tmp = main_upbit.get_balances()
        # logger.debug(tmp)
        tmp_list = {}
        tmp_jango_list = {}
        for i in tmp:
            tmp = {}
            for j, k in i.items():
                tmp[j] = k
            if tmp["currency"] == 'KRW':
                # main.money_label.setText(format(round(float(tmp["balance"])),','))  # update krw balance
                tmp_jango_list["balance"] = tmp["balance"]

                pass
            else:
                symbol = main.get_coin_symbol(tmp["currency"])
                if symbol:  # ETHF 등 제외
                    tmp_list[symbol] = {}
                    tmp_list[symbol] = tmp
                    tmp_list[symbol]["total_price"] = str(
                        float(tmp_list[symbol]['avg_buy_price']) * float(tmp_list[symbol]['balance']))
        # logger.debug(tmp_list)
        current_list = {}
        if len(tmp_list.keys()):
            current_list = pyupbit.get_current_price(tmp_list.keys())
        # logger.debug(tmp_list.keys())
        # logger.debug(current_list)

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

        # main.money_label_2.setText(format(round(total_buy), ','))
        # main.money_label_3.setText(format(round(total_now_buy), ','))

        if total_buy != 0:
            total_rate = ((float(total_now_buy) - float(total_buy)) / float(total_buy)) * 100
        else:
            total_rate = 0
        # main.money_label_4.setText(str(round(total_rate,2)))
        tmp_jango_list["total_buy"] = total_buy
        tmp_jango_list["total_now_buy"] = total_now_buy
        tmp_jango_list["total_rate"] = total_rate

        # logger.debug(tmp_list)
        return tmp_list, tmp_jango_list


    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())


class Mythread(QThread):
    update_table_signal = pyqtSignal(dict, dict)

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            try:
                global login_flag
                if login_flag:
                    time.sleep(1)
                    coin_dict, jango_dict = update_coin_list()
                    # todo : 자동매매 플래그, 자동매매 로직
                    self.update_table_signal.emit(coin_dict, jango_dict)
                    # logger.debug("?")
                time.sleep(1)
                # logger.debug("!")
            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())


import socket
import requests

# HOST_socket = '192.168.0.7'
# 내부아이피
TY_IP = '124.61.26.131'
DH_IP = '118.37.147.48'
CUSTOM_IP = '1.242.216.122'

HOST_socket = DH_IP
PORT_socket = 5000
sock_con_flag = False


class socket_client_thread(QThread):
    sock_msg = pyqtSignal(str)  # todo : signal to main order

    def __init__(self):
        super().__init__()
        self.con = False
        logger.debug("socket_client_thread start")

    def send_msg(self, msg):
        global login_flag, test
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
                    # time.sleep(10)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
                        self.s.connect((HOST_socket, PORT_socket))
                        self.con = True
                        logger.debug("소켓 서버 접속 완료")
                        # main.real_log_widget.addItem("소켓 서버 접속 완료")
                        txt = "02김도훈"  # todo :  + main.name?
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
                # logger.debug(traceback.format_exc())
                self.con = False
                logger.debug("소켓 서버 접속 불가 재접속중 ...")
                # main.real_log_widget.addItem("소켓 서버 접속 불가 재접속중 ...")
                sock_con_flag = False
                time.sleep(1)


stylesheet = """
    QTableWidget {
        background-color: white; 
    }

    QTableWidget::item {
        color: gray;                    
        background-color: gray;
    }

"""


from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QFont
if __name__ == "__main__":
    global test
    test = True

    if test:
        global main
        app = QApplication(sys.argv)
        app.setStyleSheet(stylesheet)
        app.setStyleSheet('QTableView::item {border-top: 1px solid #d6d9dc;}')

        font = QFontDatabase()
        font.addApplicationFont('.DATA/AGENCYB.TTF')
        app.setFont(QFont('AGENCYB'))
        main = Main()
        main.show()
        app.exec_()


