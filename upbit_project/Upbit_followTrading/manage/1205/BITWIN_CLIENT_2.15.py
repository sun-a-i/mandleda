import random
import re
import sys
import os
import pickle
import tempfile
import threading
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

from qroundprogressbar import QRoundProgressBar
# pip install qroundprogressbar
import datetime as dt
from datetime import datetime
import finplot as fplt

import pyupbit
import time

import pandas_datareader as pdr
import requests_cache





# ====================logger=========================
import os
from logging.handlers import TimedRotatingFileHandler
import logging
from datetime import datetime
import traceback

if not os.path.exists('./logFile'):
    os.makedirs('./logFile')
nowDate = datetime.now()
filename = str("./logFile./" + nowDate.strftime("%Y-%m-%d_%H-%M") + "1.txt")
logger = logging.getLogger(__name__)

fileMaxByte = 10.24 * 1024 * 100
fileHandler = logging.handlers.TimedRotatingFileHandler(filename='./logFile/client.log', when='midnight', interval=1,
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

if not os.path.exists('./DATA'):
    os.makedirs('./DATA')

setting_data_path = './DATA/settings.pickle'
api_data_path = './DATA/API.txt'
telegram_data_path = './DATA/telegram.txt'
coin_data_path = './DATA/save_data.pickle'

main_class = uic.loadUiType('./ui_data/main_client.ui')[0]
start_class = uic.loadUiType('./ui_data/login.ui')[0]
register_class = uic.loadUiType('./ui_data/register.ui')[0]

auto_flag = False
login_flag = False
coin_Kname = {}
coin_Ename = {}
tickers = []
coin_list = {}
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
coin_data_list = {}
kospi_nasdaq_comp = {}
class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("BITWIN - We'll Show New Freedom")

            # self.t1.clicked.connect(self.test_func)
            self.init()
            self.login()

            self.get_tickers()
            # 한글, 영어 코인명 가져오기
            self.get_eng_workd()
            self.get_korean_workd()
            # 자동완성 검색

            init_coin_data_list()

            self.table_coin.cellClicked.connect(self.table_cell_clicked_func)

            self.chart_bun.currentIndexChanged.connect(lambda: self.coin_chart(self.coin_search.text()))

            self.start_btn.clicked.connect(lambda: self.state_func('start'))
            self.stop_btn.clicked.connect(lambda: self.state_func('stop'))

            self.socket_thread = socket_client_thread()
            self.socket_thread.sock_msg.connect(self.msg_by_server)
            self.socket_thread.start()

            self.update_thread = Mythread()
            self.update_thread.update_table_signal.connect(self.update_table)
            #self.update_thread.update_coin_chart_signal.connect(update_coin_chart)
            self.update_thread.update_coin_chart_signal.connect(lambda: self.coin_chart(self.coin_search.text()))

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
        global ax  #, axs, axo
        ax = fplt.create_plot(init_zoom_periods=0)  # pygtgraph.graphicsItems.PlotItem
        #axo = ax.overlay()  # pygtgraph.graphicsItems.PlotItem
        #axs = [ax]  # finplot requres this property

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
                    access_key = key['ak']
                    secret_key = key['sk']
                    self.real_log_prt("[system] 로그인 정보 있음 로그인 시도")
                    main_upbit = pyupbit.Upbit(access_key, secret_key)
                    balance = main_upbit.get_balance(ticker="KRW")
                    if float(balance) > 0:
                        self.real_log_prt("[system] 로그인 성공")
                        self.after_login_initial()
                        login_flag = True
                    else:
                        self.real_log_prt("잔고 없음. 로그인 실패 간주")

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
                return self.ckeck_order_state(ret)

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
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def real_log_prt(self, txt):
        self.real_log.addItem(txt)
        logger.debug(txt)

    @pyqtSlot(str)
    def msg_by_server(self, data):
        try:
            logger.debug("[msg] 데이터 수신 : " + str(data))
            global coin_list,coin_data_list
            tmp = data.split(';')

            # order_type; coin; per ; amt; is_auto; is_first   ; A or B
            # 0 or 1; btc.. ; per or pri ; amt; 0 or 1; 0 or 1 : 0 or 1
            if  True:
                return 0
            if data[:2] == '01':
                logger.debug("[socket] 입장 완료 : " + str(data))
                return 0

            txt = ''
            sel_or_buy = tmp[0]
            coin = tmp[1]
            per_or_pri = tmp[2]
            server_amt = tmp[3]
            is_auto = int(tmp[4])
            is_first = int(tmp[5])
            type = tmp[6] # 1 : A, 0: B

            logger.debug(tmp)
            symbol = self.get_coin_symbol(coin)
            if len(tmp) == 7 :
                date = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
                if sel_or_buy == "BUY" :
                    if is_auto:
                        amt = server_amt
                        if is_first:
                            list_up = []
                            mycash = int(float(int(self.money_label.text().replace(',',''))))
                            invest = mycash / 20 / 2 / 2 / 2
                            if invest < 5000:
                                invest = 5100
                            for i in range(7):
                                list_up.append(int(invest))
                                invest = invest * 1.03
                            invest = int(random.choice(list_up))
                            if not type: #defensive 모드가 아니면
                                invest *= 2
                            logger.debug("진입가격 결정 : %s, my_cash = %s", invest, mycash)
                            if mycash > invest:
                                if not coin in coin_list:
                                    amt = invest
                                    txt = symbol + ': 1차 매수, ' + str(amt)+"원"
                                else:
                                    logger.debug(f'{coin} 보유코인으로 매수 금지')
                                    return False
                            else:
                                logger.debug("%s 종목 잔고 부족으로 매수 실패", coin)
                                return False
                        else:
                            if symbol in coin_list: #코인 리스트에 있으면
                                amt = coin_data_list[symbol]['last_money'] * 2
                                txt = symbol + ': 다음 매수 참여 , ' + str(amt)
                                pass
                            else:
                                self.real_log_prt("[매수] 매수 단계 맞지 않음 : ")
                                return False
                    else:
                        if per_or_pri == 'per':
                            amt = int(float(server_amt) * int(self.money_label.text().replace(',','')))
                            if amt < 5000 :
                                amt = 5000
                                logger.debug("최소주문금액보다 낮은 비율 금액, 최소주문금액 매수 " + str(round(float(server_amt) * 100)))
                                txt = str(round(float(server_amt) * 100)) + '% : ' + str(amt) + "원"
                            else:
                                logger.debug("비율 금액 매수 소지금액의 " + str(round(float(tmp[3]) * 100)))
                                txt = str(round(float(server_amt) * 100)) + '% : ' + str(amt) + "원"
                        elif per_or_pri == 'pri':
                            amt = int(server_amt)
                            if int(self.money_label.text().replace(',','')) < amt :
                                amt = int(self.money_label.text().replace(',',''))
                                logger.debug("소지금액보다 많은 지정금액, 소지금액 전부 매수")
                                txt = symbol + ", " + str(amt) + "원"
                            elif int(self.money_label.text().replace(',','')) < 5000:
                                self.real_log_prt("[매수] 소지금액 오류 ")
                                return False
                            else:
                                txt = symbol + ", " + str(amt) + "원"
                        else:
                            self.real_log_prt("[msg] 데이터 형식 맞지 않음 : " + str(data))
                            return False

                    if self.order(1, symbol ,amt):

                        self.real_log_prt(f"{date}, [매수] : {symbol[4:]}, {str(amt)}원")
                        coin_data_list[symbol]['state'] = 2
                        if is_auto:
                            coin_data_list[symbol]['last_money'] = amt
                    else:
                        self.real_log_prt(f"[매수] 오류 : {symbol}:{amt}")

                elif sel_or_buy == "SEL": #auto 따질 필요 없이 바로 sell

                    if symbol in coin_list:
                        amt = coin_list[symbol]["balance"]
                        if self.order(0, symbol,amt):
                            self.real_log_prt(f"{date}, [매도] : {symbol[4:]}, {str(amt)}개")
                        else:
                            self.real_log_prt("[매도] 오류 : 보유수량이 없거나, 매도 불가능 종목(예약 수량 확인 요망)")
                    else:
                        logger.debug('보유하지 않은 코인 매도 주문 ' + str(tmp[1]))
                else:
                    self.real_log_prt("[msg] 데이터 형식 맞지 않음 : " + str(data))
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    @pyqtSlot(dict, dict)
    def update_table(self, coin_dict, jango_dict):
        try:

            global coin_list

            if (datetime.datetime.now().hour == 8) and (datetime.datetime.now().minute == 58):
                if (datetime.datetime.now().second < 0) and (datetime.datetime.now().second > 30):
                    self.real_log.clear()
                    self.read_log.addItem("하루 2회 Log기록을 지웁니다(12시, 9시)")

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
                if coin_data_list[coin_name]['state'] != 2:
                    self.table_coin.item(idx, 0).setForeground(QtGui.QColor(0, 255, 0))

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

            #코스프 나스닥 지수 변경
            self.kospi_val.setText(str(round(kospi_nasdaq_comp['kospi']['val'], 2)))
            self.nasdaq_val.setText(str(round(kospi_nasdaq_comp['nasdaq']['val'], 2)))

            k_per = float(str(kospi_nasdaq_comp['kospi']['per']))
            if k_per >= 0:
                pixmap = QPixmap("./image/up_img.png")
                self.kospi_lbl.setPixmap(pixmap)
            else:
                pixmap = QPixmap("./image/down_img.png")
                self.kospi_lbl.setPixmap(pixmap)
            self.kospi_per.setText(str(k_per))

            n_per = float(str(kospi_nasdaq_comp['nasdaq']['per']))
            if n_per >= 0:
                pixmap = QPixmap("./image/up_img.png")
                self.nasdaq_lbl.setPixmap(pixmap)
            else:
                pixmap = QPixmap("./image/down_img.png")
                self.nasdaq_lbl.setPixmap(pixmap)
            self.nasdaq_per.setText(str(n_per))

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
                if symbol in coin_list:
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
                else:
                    self.coin_search.setText(symbol)
                    self.coin_search_2.setText('-')
                    self.coin_search_3.setText('-')

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
                    self.gridLayout.removeWidget(self.gridLayout.itemAtPosition(0, 0).widget())
                    ax.clear()
                    fplt.close()
                    ax = fplt.create_plot()
                    df = pyupbit.get_ohlcv(symbol, self.bun_to_min(), 200)
                    plot = fplt.candlestick_ochl(df[['open', 'close', 'high', 'low']])

                    # fplt.set_x_pos(0, 200, ax) #시작위치 줌
                    fplt.refresh()
                    self.gridLayout.addWidget(ax.vb.win, 0, 0)  # ax.vb     (finplot.FinViewBox)

        except Exception as e:
            logger.debug(e)
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

        program_list = []
        upbit_list = tmp_list.keys()  # 업비트에서 가지고있는 전부
        # logger.debug(coin_data_list)
        for j in coin_data_list:
            if (coin_data_list[j]['state'] == 2) | (coin_data_list[j]['state'] == 1):
                program_list.append(j)  # 프로그램이 가지고있는 전부

        for k in list(set(program_list) - set(upbit_list)):
            logger.debug(' %s 프로그램 매수한 코인이 서버에 존재하지 않음. 초기화진행', k)
            coin_init(k)  # 1,2 -> 0

        for l in list(set(upbit_list) - set(program_list)):
            # logger.debug(upbit_list)
            # logger.debug(program_list)
            logger.debug(' %s 손매수한 코인 발견. 손매수 처리', l)
            # if l in coin_data_list:
            coin_data_list[l]['state'] = 1
            logger.debug(l)

        all_modify_csv()

        return tmp_list, tmp_jango_list


    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())

def coin_init(name):
    try:
        global coin_data_list

        logger.debug("%s 종목 초기화", name)
        coin_data_list[name]['coin_name'] = name
        #coin_data_list[name]['fir_price'] = 0
        coin_data_list[name]['fir_invest_money'] = 0
        coin_data_list[name]['state'] = 0  # state - 0:미진입, 1:손매수, 2:프로그램매수
        #todo : 추가매수 30분 이내 무시
        #todo : 마지막 거래 시간

        all_modify_csv()
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())

def init_coin_data_list():
    logger.debug("init_coin_data_list start")
    try:
        global coin_data_list

        #코인 저장 딕셔너리 저장
        if os.path.exists(coin_data_path):
            with open(coin_data_path, 'rb') as f:
                coin_data_list = pickle.load(f)
        else:
            logger.debug("csv file not exists..!")
            for i in tickers:
                logger.debug("add %s", i)
                coin_data_list[i] = {'coin_name': coin_Kname[i],
                                     'fir_invest_money': 0,
                                     'fir_price': 0,
                                     'state': 0
                                     }
            all_modify_csv()

    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())

def all_modify_csv():
    try:
        global coin_data_list
        with open(coin_data_path, 'wb') as f:
            pickle.dump(coin_data_list, f)
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())


def calc_income_rate(close, current):
    try:
        close = float(close)
        current = float(current)

        if (close - current) == 0:
            # logger.debug("close = %s, current = %s", close, current)
            return str(0)
        elif (close == 0) | (current == 0):
            # logger.debug("close = %s, current = %s", close, current)
            return str(0)
        else:
            val = (current - close) / close * 100
            val = round(val, 2)
            return str(val)
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())

def calc_kospi_nasdaq_data():
    try:
        global kospi_nasdaq_comp
        today = datetime.datetime.now()
        yesterday = datetime.datetime.now() - datetime.timedelta(10)

        today = today.strftime('%Y%m%d')
        yesterday = yesterday.strftime('%Y%m%d')

        session = requests_cache.CachedSession(cache_name='cache', backend='sqlite')
        # just add headers to your session and provide it to the reader
        session.headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
                           'Accept': 'application/json;charset=utf-8'}
        kospi = pdr.DataReader('^KS11', 'yahoo', yesterday, today, session=session)
        kospi_nasdaq_comp['kospi'] = {'val' : kospi['Close'][-1], 'per' : calc_income_rate(kospi['Close'][-2], kospi['Close'][-1])}

        nasdaq = pdr.get_data_yahoo('^IXIC', yesterday, today, session=session)
        kospi_nasdaq_comp['nasdaq'] = {'val' : nasdaq['Close'][-1],'per' : calc_income_rate(nasdaq['Close'][-2], nasdaq['Close'][-1])}

        #logger.debug(kospi_nasdaq_comp)
    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())

class Mythread(QThread):
    update_table_signal = pyqtSignal(dict, dict)
    update_coin_chart_signal = pyqtSignal()
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            try:
                global login_flag
                if login_flag:
                    time.sleep(1)
                    calc_kospi_nasdaq_data()
                    coin_dict, jango_dict = update_coin_list()
                    # todo : 자동매매 플래그, 자동매매 로직
                    self.update_table_signal.emit(coin_dict, jango_dict)
                    # logger.debug("?")
                    if update_coin_chart():
                        logger.debug("차트 업데이트")
                        self.update_coin_chart_signal.emit()
                        time.sleep(5)
                time.sleep(1)
                # logger.debug("!")
            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())

def update_coin_chart():
    try:
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
            time.sleep(1)
            try:
                if auto_flag:
                    # time.sleep(10)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
                        self.s.connect((HOST_socket, PORT_socket))
                        self.con = True
                        #logger.debug("소켓 서버 접속 완료")
                        #main.real_log_widget.addItem("소켓 서버 접속 완료")
                        txt = "01"+user_name  # todo :  + main.name?
                        logger.debug("입장로그 : %s", txt)
                        self.send_msg(txt)
                        sock_con_flag = True
                        while True:
                            data = self.s.recv(1024).decode('utf-8')
                            if len(data) > 1 :
                                logger.debug(f'수신된 데이터 :{data}')
                                self.sock_msg.emit(data)
                else:
                    logger.debug("로그인 확인되지 않음")
            except Exception as e:
                logger.debug(e)
                # logger.debug(traceback.format_exc())
                self.con = False
                logger.debug("소켓 서버 접속 불가 재접속중 ...")
                #main.real_log_widget.addItem("소켓 서버 접속 불가 재접속중 ...")
                sock_con_flag = False
                time.sleep(5)


stylesheet = """
    QTableWidget {
        background-color: white; 
    }

    QTableWidget::item {
        color: gray;                    
        background-color: gray;
    }

"""

update_p = 0
key = {}
# 1. login_[val]  2. register_[id]_[ak]_[sk]
def check_socket_connect(user_data):
    try:
        global key, update_flag, connection_flag, update_p

        logger.debug('socket start')

        f = open("./DATA/socket_ip.txt")
        lines = f.readlines()
        f.close()

        case = ""
        split_data = user_data.split("_")
        if len(split_data) == 2:
            logger.debug("login socket try..")
            case = 'login'
        elif len(split_data) == 4:
            logger.debug("register socket try..")
            case = 'register'

        # 서버의 주소입니다. hostname 또는 ip address를 사용할 수 있습니다.
        HOST = str(lines[0]).strip()
        # 서버에서 지정해 놓은 포트 번호입니다.
        PORT = str(lines[1]).strip()
        logger.debug("host = %s, port = %s", HOST.strip(), PORT.strip())
        # 소켓 객체를 생성합니다.
        # 주소 체계(address family)로 IPv4, 소켓 타입으로 TCP 사용합니다.
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 지정한 HOST와 PORT를 사용하여 서버에 접속합니다.
        c = client_socket.connect((HOST, int(PORT)))
        logger.debug("socket connect retrunr = %s", c)

        res = ''
        count = 0
        while True:
            logger.debug('통신 상태 표시.. ')
            client_socket.sendall(user_data.encode())

            logger.debug("수신 대기 중...")

            # 수신 대기
            data = client_socket.recv(1024)

            if not data:
                res = 'no'
                logger.debug("빈 데이터를 수신받아 종료합니다.")
                connection_flag = 'no'
                break

            # 수신받은 문자열을 출력합니다. #Received from , ip주소, 알수없는숫자열
            logger.debug('Received from %s', data.decode())

            # 메시지를 전송합니다.
            if len(data) > 1:
                logger.debug("수신받은 데이터 = %s", data.decode())

                split_data = data.decode().split("_")
                logger.debug('split_data={}'.format(split_data))
                if case == 'login':
                    if split_data[0] == 'ok':
                        logger.debug('로그인 성공 %s', data.decode())

                        file_list = os.listdir('./')
                        ver = 200
                        for i in file_list:
                            if (i[-3:] == 'exe') and (i[:6] == 'BITWIN'):

                                i = i[:-4]
                                logger.debug(i)
                                read_ver = int(re.sub(r'[^0-9]', '', i))
                                if int(read_ver) > int(ver):
                                    ver = read_ver
                                    logger.debug("프로그램 현재 버전 = %s", ver)

                        key['ak'] = split_data[1]
                        key['sk'] = split_data[2]
                        key['time'] = split_data[3]
                        key['stage'] = split_data[4]
                        key['ver'] = split_data[5]

                        file_name = "BITWIN_" + split_data[5][:1] + "." + split_data[5][1:] + ".exe"
                        if int(ver) != int(key['ver']):
                            logger.debug("프로그램 업데이트 필요 %s -> %s", ver, key['ver'])
                            connection_flag = 'update'
                            try:
                                client_socket.sendall('update'.encode())
                                file_size = int.from_bytes(client_socket.recv(4096), byteorder="big")

                                if file_size == 0:
                                    print("Error: cannot find '" + file_name + "' at server")
                                    return

                                logger.debug("file name : " + file_name)
                                logger.debug("size : %s", file_size)
                                logger.debug("\nStart Downloading...")
                                client_socket.sendall(bytes([255]))

                                nowdown_size = 0
                                downbuff_size = 1048576

                                with tempfile.NamedTemporaryFile(delete=False, dir=".") as f:
                                    temp_name = f.name
                                    while True:
                                        if nowdown_size < file_size:
                                            resp = client_socket.recv(min(downbuff_size, file_size - nowdown_size))
                                            nowdown_size += len(resp)
                                            f.write(resp)
                                            update_p = str(min(100, nowdown_size / file_size * 100))
                                            logger.debug("Download %s", update_p)
                                            sys.stdout.flush()
                                        else:
                                            client_socket.recv(1)
                                            logger.debug("Finish!\n")
                                            break
                                os.replace(temp_name, file_name)
                                connection_flag = 'end'
                                break
                            except ConnectionError:
                                logger.debug("Error: connection closed")
                            except OSError:
                                logger.debug("Error: cannot write file")
                            except:
                                logger.debug("Error: bad response")
                            """
                            nowdir = os.getcwd()
                            data_transferred = 0
                            with open(nowdir + "\\TYANT_" + split_data[5][:1] + "." + split_data[5][1:]+".exe", 'wb') as f:  # 현재dir에 filename으로 파일을 받는다
                                try:
                                    while data:  # 데이터가 있을 때까지
                                        f.write(data)  # 1024바이트 쓴다
                                        data_transferred += len(data)
                                        #logger.debug(data)
                                        data = client_socket.recv(1024)  # 1024바이트를 받아 온다
                                except Exception as ex:
                                    logger.debug(ex)
                            logger.debug('파일 %s 받기 완료. 전송량 %s',filename, data_transferred)
                            connection_flag = 'end'
                            res = 'update'
                            break
                            """
                        else:
                            client_socket.sendall('ok'.encode())
                            connection_flag = 'ok'
                            time.sleep(3)
                            break

                    elif split_data[0] == 'quit':
                        logger.debug('미승인 = %s', data.decode())
                        connection_flag = 'quit'
                        break
                elif case == 'register':
                    if split_data[0] == 'already':
                        logger.debug('기등록된 아이디 = %s', data.decode())
                        connection_flag = data.decode()
                        break
                    elif split_data[0] == 'success':
                        logger.debug('등록 성공 = %s', data.decode())
                        connection_flag = data.decode()
                        break
            else:
                time.sleep(1)
                # pass

        # 소켓을 닫습니다.
        client_socket.close()
        logger.debug('통신 종료')
    except Exception as e:
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())


class init_data(QThread):
    init_read_data = pyqtSignal(dict)

    def run(self):
        try:
            logger.debug("init_data_read start")
            resp = {}
            resp['resp'] = 1
            self.init_read_data.emit(resp)
            time.sleep(0.25)

        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.information(self, "경고", "데이터 통신에 실패하였습니다. 프로그램을 다시 시작하여 주세요.")



class RegisterDialog(QDialog, register_class):
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("Register Setting")
            self.setWindowIcon(QIcon("./image/icon.ico"))
            self.register_btn.clicked.connect(self.register_connect_func)
            self.register_btn.setStyleSheet("""
                                QPushButton {
                                    color: black; 
                                    background-color: white
                                }
                                QPushButton:hover {
                                    color: #6799FF;
                                    background-color: #BDBDBD
                                }
                                QPushButton:pressed {
                                    color: yellow;
                                    background-color: #D5D5D5
                                }
                                """)
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 담당자에게 문의주세요.')

    def register_connect_func(self):
        global connection_flag
        val1 = self.id.text()
        val2 = self.ak.text()
        val3 = self.sk.text()

        list_par = []
        # re.
        for i in val1:
            # 영어,숫자 및 공백 제거.
            text = re.sub('[^a-zA-Z0-9]', ' ', i).strip()
            # 빈 리스트는 제거.
            if (text != ''):
                list_par.append(text)
        val1 = "".join(list_par)

        txt = 'register_' + str(val1) + "_" + str(val2) + "_" + str(val3)

        reply = QMessageBox.question(self, "확인", "등록하실 ID 는 [" + val1 + "] 입니다. \n맞으십니까?")
        if reply == QMessageBox.Yes:
            reply = QMessageBox.question(self, "확인",
                                         "API 키 값을 다시 한번 확인해 주세요.\n키값오류가 있을 시 등록 절차가 길어질 수 있습니다.\n진행하시겠습니까?")
            if reply == QMessageBox.Yes:
                check_socket_connect(txt)

                if connection_flag == 'already':
                    QMessageBox.information(self, '확인', '사용되고 있는 아이디입니다.\n다른 아이디로 신청해주세요.')
                elif connection_flag == 'success':
                    QMessageBox.information(self, '확인', '신청이 완료되었습니다.\n인증 후 등록 완료되므로 담당자에게 등록요청해주세요.')
                else:
                    QMessageBox.information(self, '확인', '잘못된 메세지입니다. : ' + str(connection_flag))


user_name = ""
main = object

class MyWindow(QMainWindow, start_class):

    def __init__(self):
        try:
            global get_data_flag, my_cash_data, key

            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("BIT-WIN Auto Trading Realtime Wallet")
            self.setWindowIcon(QIcon("./image/bitwin_icon.ico"))
            logger.debug("login init_process close...")

            self.update_frame.setVisible(False)

            # elf.movie = QMovie('./image/login_gif.gif', QByteArray(), self)
            # self.movie.setCacheMode(QMovie.CacheAll)
            # QLabel에 동적 이미지 삽입
            # self.login_gif.setMovie(self.movie)
            # self.movie.start()

            self.movie = QMovie('./image/ai_gif.gif', QByteArray(), self)
            self.movie.setCacheMode(QMovie.CacheAll)
            # QLabel에 동적 이미지 삽입
            self.updating.setMovie(self.movie)
            self.movie.start()

            self.login_btn.clicked.connect(self.login_btn_func)
            self.login_btn.setStyleSheet("""
                    QPushButton {
                        color: white ; 
                        background-color: #002266
                    }
                    QPushButton:hover {
                        color: #6799FF;
                        background-color: #4641D9
                    }
                    QPushButton:pressed {
                        color: yellow;
                        background-color: #6B66FF
                    }
                    """)

            self.regi_lbl.clicked.connect(self.register_func)
            self.regi_lbl.setStyleSheet("""
                    QPushButton {
                        color: white ; 
                        background-color: #005766
                    }
                    QPushButton:hover {
                        color: #6799FF;
                        background-color: #22741C
                    }
                    QPushButton:pressed {
                        color: yellow;
                        background-color: #2F9D27
                    }
                    """)

            self.init_read_thread = init_data()
            self.init_read_thread.init_read_data.connect(self.window_close)

            pixmap = QPixmap("./image/banner_main.jpg")
            self.backImg_lbl.setPixmap(pixmap)

            # self.access_key.setText(key['a_key'])
            # self.secret_key.setText(key['s_key'])
            # self.access_key.setEchoMode(QLineEdit.Password)
            # self.secret_key.setEchoMode(QLineEdit.Password)


        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 담당자에게 문의주세요.')


    def register_func(self):
        logger.debug("Register btn clicked")
        self.osdlg = RegisterDialog()
        self.osdlg.show()

    @pyqtSlot(dict)
    def window_close(self, resp):
        global user_name, key, main
        try:
            logger.debug("data read success, window close()")
            # self.read_sucess.emit(user_name)
            main = Main()
            main.show()

            self.close()
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 프로그램을 재시작하여 주세요.')

    def login_process(self):
        try:
            global connection_flag, update_flag, update_p, my_cash, MAIN_UPBIT, version_level, key
            self.update_per.setText(str(update_p) + "%")
            list_men = ['더 나은 버전으로 개선 중입니다.', '안전 투자를 위해 개선 중이니 잠시만 기다려주세요.', '고장난게 아닙니다, 업데이트가 느릴 뿐!'
                , '업데이트가 완료되면 메시지로 알려드립니다.', '지속 발전하는 탼트로 함께 성공 투자!', '탼트는 고급스럽고 값진 프로그램입니다. 아무나 사용하는 로직이 아닙니다!']
            self.sentence.setText(random.choice(list_men))

            if connection_flag != '':
                if connection_flag == 'update':
                    pass
                elif connection_flag == 'end':
                    update_flag = False
                    QMessageBox.information(self, '확인', "최신버전으로 업데이트했습니다.\n기존 프로그램은 삭제 후 최신버전을 시작하여 주세요.")
                    self.login_timer.stop()
                    connection_flag = ''
                    self.close()
                elif connection_flag == 'ok':
                    self.update_frame.setVisible(False)
                    previous_date = datetime.datetime(int(key['time'][:4]), int(key['time'][4:6]),
                                                      int(key['time'][6:8]),
                                                      23, 59, 0)
                    if previous_date < datetime.datetime.now():
                        QMessageBox.information(self, "알람", "유효기간이 지났습니다.")
                        # logger.debug("작동시간 아님. peoriod1 = %s,  peoriod1 = %s",previous_date ,previous_date2)
                        self.login_timer.stop()
                        connection_flag = ''
                    else:
                        logger.debug("user_name = %s", user_name)
                        self.movie = QMovie('./image/loading3.gif', QByteArray(), self)
                        self.movie.setCacheMode(QMovie.CacheAll)
                        # QLabel에 동적 이미지 삽입
                        self.loading_lbl.setMovie(self.movie)
                        self.movie.start()

                        access_key = key['ak']
                        secret_key = key['sk']
                        version_level = key['stage']
                        logger.debug("version level = %s", key['stage'])
                        MAIN_UPBIT = pyupbit.Upbit(access_key, secret_key)

                        balances = MAIN_UPBIT.get_balances()
                        time.sleep(0.2)
                        total_val = 0
                        logger.debug(balances)
                        if balances == 'no':
                            logger.debug("balances = %s", balances)
                            txt = "등록 회원입니다. 하지만 키값 불일치로 로그인에 실패하였습니다.\n키값을 확인하여 주시길 바랍니다.\nAccess Key : " + access_key + "\nSecret Key : " + secret_key
                            self.movie.stop()
                            QMessageBox.warning(self, '확인', txt)
                            self.login_timer.stop()
                        else:
                            for i in range(len(balances)):
                                # logger.debug("balances")

                                if balances[i]['currency'] == 'KRW':
                                    my_cash = int(float(balances[i]['balance']))

                            logger.debug("login start!")
                            # self.loading_lbl.setText("LOADING...")

                            self.login_timer.stop()
                            connection_flag = ''

                            self.init_read_thread.start()

                elif connection_flag == 'quit':
                    self.update_frame.setVisible(False)
                    self.login_timer.stop()
                    connection_flag = ''
                    QMessageBox.warning(self, '경고', '등록되지 않은 사용자입니다.')
                else:
                    self.update_frame.setVisible(False)
                    self.login_timer.stop()
                    connection_flag = ''
                    QMessageBox.warning(self, '경고', '서버와 통신이 원활하지 않습니다. : ' + str(connection_flag))


        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self,'경고', '로그인 실패 : 아이디 또는 IP를 확인해주세요')

    def login_btn_func(self):
        global MAIN_UPBIT, user_name, my_cash, key, update_flag, connection_flag
        try:
            self.update_frame.setVisible(True)
            user_name = self.userName.text()
            txt = "login_" + user_name
            logger.debug("user id = {}".format(user_name))

            t = threading.Thread(target=check_socket_connect, args=(txt,))
            t.daemon = True
            t.start()

            self.login_timer = QTimer()
            self.login_timer.timeout.connect(self.login_process)
            self.login_timer.start()
            self.login_timer.setInterval(5000)


        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 담당자에게 문의주세요.')


from PyQt5.QtGui import QFontDatabase
from PyQt5.QtGui import QFont
if __name__ == "__main__":
    global test
    test = True

    if test:
        app = QApplication(sys.argv)
        app.setStyleSheet(stylesheet)
        app.setStyleSheet('QTableView::item {border-top: 1px solid #d6d9dc;}')

        font = QFontDatabase()
        font.addApplicationFont('.DATA/AGENCYB.TTF')
        app.setFont(QFont('AGENCYB'))
        myWindow = MyWindow()
        myWindow.show()
        app.exec_()


