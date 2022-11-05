import re
import sys
import os
import pickle
import tempfile
import threading
from time import sleep
import pandas as pd

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

# import telegram
import pyupbit
import time

import socket
import select
import requests
# import request
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

#path
csv_path = './DATA/save_data.pickle'
sub_csv_path = './DATA/save_data2.pickle'
setting_path = './DATA/setting.pickle'
telegram_path = './DATA/tel.pickle'
money_csv_path = './DATA/cash_data.pickle'
image_path = './DATA/image_data.pickle'
key_path = './DATA/key.pickle'
condition_path = './DATA/condition.pickle'
condition_buy_path = './DATA/condition_buy_list.pickle'
income_path = './DATA/income_list.pickle'

setting_data_path = './DATA/settings.pickle'
api_data_path = './DATA/API.txt'
telegram_data_path = './DATA/telegram.txt'
#path end

if not os.path.exists('DATA'):
    os.makedirs('DATA')


coin_data_list = {}
coin_data_list_save = {}
labels = ['coin_name', 'fir_invest_money', 'fir_price', 'avr_price', 'balance', 'quintuple_batting',
          'invest_cash', 'tot_invest_cash', 'set_stage', 'cur_stage', 'div_per', 'in_per', 'out_per',
          'next_buy_price', 'next_income_price', 'next_out_price', 'outcome_state', 'rebuy_chkbox',
          'state', 'gubun', 'high', 'gamsi_per', 'gamsi_price', 'trailing_per', 'trailing_income_price',
          'trailing_state', 'last_trade_time']

#UI path
main_class = uic.loadUiType('./ui_data/main_server.ui')[0]
start_class = uic.loadUiType('./ui_data/login.ui')[0]
register_class = uic.loadUiType('./ui_data/register.ui')[0]

auto_flag = False

coin_Kname = {}
coin_Ename = {}
tickers = []
coin_list = {}

class ConditionThread(QThread):
    condition_buy = pyqtSignal(str)

    def run(self):
        try:
            """
            - 구현한 보조지표 리스트
                get_stoch
                get_cci
                get_envelope
                get_Bollinger
                get_line
                get_ilmoc
            """
            pass
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("upbit auto system")

            self.t1.clicked.connect(self.test_func)
            self.t2.clicked.connect(self.test_func2)
            self.t3.clicked.connect(self.test_func3)
            self.table_coin.cellClicked.connect(self.table_cell_clicked_func)

            self.initial()
            self.login()
            self.get_tickers()
            # 한글, 영어 코인명 가져오기
            self.get_eng_workd()
            self.get_korean_workd()
            # 자동완성 검색
            self.init_nameList()

            self.buy_btn.clicked.connect(self.buy_btn_func)
            self.sell_btn.clicked.connect(self.sell_btn_func)

            # =========소켓 서버 스레드
            self.socket_server = socket_server_thread()
            self.socket_server.start()

            # condition thread
            self.autotrading_thread = ConditionThread()  # Qthread 시작(실시간 가격 수집)
            self.autotrading_thread.condition_buy.connect(self.buy_condition_coin_func)
            self.autotrading_thread.start()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    @pyqtSlot(str)
    def buy_condition_coin_func(self, a_data):
        global coin_data_list, my_auto_count, buy_auto_setting, level, value_dict
        try:
            if a_data == "dead":
                logger.debug("\n\nWorker Thread Dead, and re-alive\n\n")
                self.get_thread.start()

            logger.debug("조건식 부합 코인 발견 = %s", a_data)
            split_data = str(a_data).split("_")
            # split_data = coin _ buy _ level _ score
            # 2 - nomal, 3 - good, 4 - very good

            if split_data[1] == 'buy':
                if int(coin_data_list[split_data[0]]['state']) != 0:
                    if int(coin_data_list[split_data[0]]['state']) == 2:
                        if float(coin_data_list[split_data[0]]['div_per']) < (int(level) * 5 * (-1)):
                            logger.debug("%s 이미 매수하였으나, 매집 허용 ", split_data[0])
                            self.re_condition_buy_coin_func(a_data + "_re")

                        elif (int(split_data[3]) >= 3) & (
                                float(coin_data_list[split_data[0]]['div_per']) < (int(level) * 2 * (-1))):
                            logger.debug("%s 이미 매수하였으나, 매집 강력 허용", split_data[0])
                            self.re_condition_buy_coin_func(a_data + "_re")

                        else:
                            logger.debug("%s 이미 매수하였으므로 추가매수 금지", split_data[0])

                    else:
                        logger.debug("%s 이미 매수하였으므로 추가매수 금지", split_data[0])
                else:
                    logger.debug("기존 매수 코인 아님. 매수 로직 진행.")
                    if buy_auto_setting == 'auto':

                        key = 21

                        if my_auto_count < key:
                            self.condition_buy_coin_func(a_data + "_fir")
                    else:
                        if my_auto_count < int(self.buy_coin_limit.text()):
                            self.condition_buy_coin_func(a_data + "_fir")
                        else:
                            self.listView.addItem('개수 제한으로 매수 금지!')
            elif split_data[1] == 'sell':
                logger.debug("데드 크로스 발생, 매도 진행")
            else:
                pass
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
            send_to_clients(0, 'btc', 0.2)
            send_to_clients(1, 'btc', 0.1)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def test_func3(self):
        logger.debug("testbtn2 clicked")
        try:
            # logger.debug(self.socket_server.clients)
            self.add_coin_to_table()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def initial(self):
        try:
            logger.debug('table init..')
            table = self.table_coin
            table.setColumnWidth(0, 50)
            table.setColumnWidth(1, 80)
            table.setColumnWidth(2, 65)
            table.setColumnWidth(3, 80)
            table.setColumnWidth(4, 90)
            table.setColumnWidth(5, 75)
            table.setColumnWidth(6, 75)
            table.setColumnWidth(7, 80)
            table.setColumnWidth(8, 80)
            # table.setAlignment(QtCore.Qt.AlignCenter)

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

    def update_balance(self):  # todo : del
        try:
            balance = main_upbit.get_balance(ticker="KRW")
            self.money_label.setText(format(round(balance), ','))
            # self.money_label.setText(str(int(balance)))
            return True
        except:
            self.real_log_prt("[error] 잔고 update 실패")

    def order(self, is_buy, coin, amt):
        try:
            global main_upbit
            if is_buy:
                ret = main_upbit.buy_market_order(coin, price=amt)
            else:
                ret = main_upbit.sell_market_order(coin, volume=amt)  # todo : 매도는 수량 기준 ?
            # todo : 메세지

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def real_log_prt(self, txt):
        self.real_log.addItem(txt)
        logger.debug(txt)
        self.real_log.scrollToBottom()

    def buy_btn_func(self):
        try:
            data = self.coin_search.text().upper()
            logger.debug(data)
            symbol = self.get_coin_symbol(data)
            if symbol:
                if self.per_radio.isChecked():  # 퍼센트 구매
                    tmp = float(self.price_per.text())
                    if self.price_per.text().isdigit():  # 숫자인지
                        if tmp > 0 and tmp <= 100:  # 100%보다 적게
                            amt = float(self.money_label.text().replace(',', '')) * tmp / 100
                            if amt >= 5000:
                                txt = str(symbol) + " : " + str(amt)
                                reply = QMessageBox.question(self, '확인', txt + '원 매수 하시겠습니까?')
                                if reply == QMessageBox.Yes:
                                    self.real_log_prt("비율 금액 매수 " + str(symbol) + " : " + str(amt))
                                    self.order(1, symbol, amt)
                            else:
                                txt = "[error] 구매 금액 에러 : 최소주문 5000원 이상"
                                self.floating_msg(txt)
                        else:
                            txt = "[error] 구매 금액 에러 : 0~100 사이의 값"
                            self.floating_msg(txt)
                    else:
                        txt = "[error] 구매 비율 에러 : 자연수를 입력해야합니다."
                        self.floating_msg(txt)

                else:  # 지정가 구매
                    if self.price_pri.text().isdigit():
                        tmp = int(self.price_pri.text())
                        if tmp > 0 and tmp <= float(self.money_label.text().replace(',', '')):  # 가진돈보다 적게
                            amt = tmp
                            if amt >= 5000:
                                txt = str(symbol) + " : " + str(amt)
                                reply = QMessageBox.question(self, '확인', txt + '원 매수 하시겠습니까?')
                                if reply == QMessageBox.Yes:
                                    self.real_log_prt("지정 금액 매수 " + str(symbol) + " : " + str(amt))
                                    self.order(1, symbol, amt)
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

    def floating_msg(self, txt):
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
                amt = coin_list[symbol]["balance"]
                txt = str(symbol) + " : " + str(amt)
                reply = QMessageBox.question(self, '확인', txt + '개 매도 하시겠습니까?')
                if reply == QMessageBox.Yes:
                    self.real_log_prt("전량 매도 " + str(symbol) + " : " + str(amt))
                    self.order(0, symbol, amt)
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

    def table_cell_clicked_func(self, row, column):
        try:
            item = self.table_coin.item(row, 0)
            value = item.text()
            label_string = 'Cell Clicked Row: ' + str(row + 1) + ', Column: ' + str(column + 1) + ', Value: ' + str(
                value)
            self.coin_search.setText(value)
            logger.debug(label_string)
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    @pyqtSlot()
    def update_table(self):
        global coin_list
        try:
            # logger.debug(len(coin_list))
            if len(coin_list) != self.table_coin.rowCount():
                self.table_coin.setRowCount(len(coin_list))
                idx = 0
                for coin_name in coin_list:
                    stop_btn = QPushButton("중지")
                    stop_btn.resize(100,30)
                    start_btn = QPushButton("활성화")
                    start_btn.resize(150, 50)
                    stop_btn.clicked.connect(lambda: self.handleButtonClicked(0))
                    start_btn.clicked.connect(lambda: self.handleButtonClicked(1))
                    self.table_coin.setCellWidget(idx, 7, stop_btn)
                    self.table_coin.setCellWidget(idx, 8, start_btn)
                    idx += 1

            idx = 0

            for coin_name in coin_list:
                # logger.debug(coin_name)
                # logger.debug(idx)
                # format(num, ',')
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

                # self.table_coin.setItem(idx, 2, QTableWidgetItem())

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
                self.table_coin.setItem(idx, 4, QTableWidgetItem(str(round(float(coin_list[coin_name]["balance"]), 7))))
                self.table_coin.setItem(idx, 5, QTableWidgetItem(
                    format(round(float(coin_list[coin_name]["total_price"])), ',')))  #
                self.table_coin.setItem(idx, 6, QTableWidgetItem(
                    format(round(float(coin_list[coin_name]["total_now_price"])), ',')))  #

                """self.table_coin.item(idx, 0).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.table_coin.item(idx, 1).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 2).setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.table_coin.item(idx, 3).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 4).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 5).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.table_coin.item(idx, 6).setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)"""
                self.table_coin.item(idx, 0).setTextAlignment(Qt.AlignCenter)
                self.table_coin.item(idx, 1).setTextAlignment(Qt.AlignRight)
                self.table_coin.item(idx, 2).setTextAlignment(Qt.AlignCenter)
                self.table_coin.item(idx, 3).setTextAlignment(Qt.AlignRight)
                self.table_coin.item(idx, 4).setTextAlignment(Qt.AlignRight)
                self.table_coin.item(idx, 5).setTextAlignment(Qt.AlignRight)
                self.table_coin.item(idx, 6).setTextAlignment(Qt.AlignRight)

                # logger.debug(coin_name)
                idx += 1


        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def handleButtonClicked(self, state):
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


class Mythread(QThread):
    signal = pyqtSignal()

    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            try:
                time.sleep(1)
                update_coin_list()
                # update_current_price()
                # todo : 자동매매 플래그, 자동매매 로직
                self.signal.emit()
                time.sleep(1)
            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())


def str_to_krw():
    pass


def krw_to_str():
    pass


# coin list update func
def update_coin_list():
    try:
        global auto_flag, main_upbit, coin_list
        tmp = main_upbit.get_balances()
        # logger.debug(tmp)
        tmp_list = {}
        for i in tmp:
            tmp = {}
            for j, k in i.items():
                tmp[j] = k
            if tmp["currency"] == 'KRW':
                main.money_label.setText(format(round(float(tmp["balance"])), ','))  # update krw balance
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

        main.money_label_2.setText(format(round(total_buy), ','))
        main.money_label_3.setText(format(round(total_now_buy), ','))
        if total_buy != 0:
            total_rate = ((float(total_now_buy) - float(total_buy)) / float(total_buy)) * 100
        else:
            total_rate = 0
        main.money_label_4.setText(str(round(total_rate, 2)))

        coin_list = tmp_list

        # logger.debug(coin_list)


    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())


def update_current_price():
    global coin_list

    for symbol in coin_list:
        coin_list[symbol]["current_price"] = str(pyupbit.get_current_price(symbol))


SERVER_PORT = 5000
# 외부아이피
TY_IP = '192.168.123.100'
DH_IP = '192.168.0.7'
DH_OFFICE_IP = '175.212.249.4'
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
            self.SERVER_HOST = TY_IP
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
                    main.real_log_prt('[system] 서버가 시작되었습니다.')

                    while True:
                        try:
                            self.readables, self.writeables, self.excpetions = select.select(self.socks, [],
                                                                                             [])  # 이벤트 대기 ex)클라이언트 접속, 리시브
                            for sock in self.readables:
                                if sock == self.s:  # 신규 클라이언트 접속
                                    newsock, addr = self.s.accept()
                                    self.socks.append(newsock)
                                    logger.debug("새로운 클라이언트 접속" + str(addr))
                                    # main.real_log_widget.addItem("새로운 클라이언트 접속")

                                else:  # 이미 접속한 클라이언트의 요청
                                    try:
                                        conn = sock
                                        data = conn.recv(1024).decode('utf-8')
                                        if len(data) > 1:
                                            logger.debug(f'데이터 수신 : {data}')
                                            if data[:2] == "02":
                                                data = data[2:]
                                                self.clients[conn.getpeername()[0]] = data
                                                main.client_list.addItem("클라이언트 접속 : " + str(conn.getpeername()[0]))
                                                logger.debug("클라이언트 : " + data)

                                    except ConnectionResetError:
                                        client_ip = sock.getpeername()[0]
                                        name = self.clients[client_ip]
                                        sock.close()
                                        self.socks.remove(sock)
                                        del self.clients[client_ip]
                                        logger.debug("클라이언트 접속 해제 : " + name)
                                        main.client_list.addItem("클라이언트 접속 해제 : " + str(client_ip))
                                        # main.real_log_widget.addItem("클라이언트 접속 해제 : " + name)


                                    except Exception as e:
                                        logger.debug(traceback.format_exc())
                                        logger.debug(e)
                                        pass
                                        # 중요정보 로그 !!
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
                    if i != self.s:  # 본인을 제외한 모든 소켓에 송신
                        try:
                            name = self.clients[i.getpeername()[0]]
                        except:
                            logger.debug("찾을 수 없음")
                            name = '없음'

                        logger.debug(i)
                        logger.debug("수신자 : " + name + ", 메세지 : " + data)
                        # main.real_log_widget.addItem("수신자 : " + name + ", 메세지 : " + data + "전송 완료")
                        res = i.sendall(data.encode('utf-8'))
                        logger.debug(res)
            else:
                logger.debug("연결되지 않음 메세지 전송 실패")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


def send_to_clients(is_buy, coin):  #
    try:
        if main.per_radio.isChecked():
            # amt =
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
                if case == 'login':
                    if split_data[0] == 'ok':
                        logger.debug('로그인 성공 %s', data.decode())

                        file_list = os.listdir('./')
                        ver = 215
                        for i in file_list:
                            if i[-3:] == 'exe':
                                i = i[:-4]
                                read_ver = re.sub(r'[^0-9]', '', i)
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
                            break

                    elif split_data[0] == 'quit':
                        logger.debug('미승인 = %s', data.decode())
                        connection_flag = data.decode()
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
                sleep(1)
                # pass

        # 소켓을 닫습니다.
        client_socket.close()
        logger.debug('통신 종료')
    except Exception as e:
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())



class RegisterDialog(QDialog, register_class):
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("Register Setting")
            self.setWindowIcon(QIcon("./image/bitwin_icon.ico"))
            self.register_btn.clicked.connect(self.register_connect_func)
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



def read_csv_file():
    global coin_data_list, ing_count, set_1, set_2, set_3, set_4, set_5, set_6, set_7, set_8, set_9, set_10, total_invest_money, tickers, coin_Kname
    try:

        # state - 0:미진입, 1:손매수, 2:프로그램매수
        # gubun - 0:init, 1:익절, 2:트레일링
        # trailing_state - 0:감시가미진입, 1:감시가도달
        if not os.path.exists(csv_path):
            logger.debug("csv file not exists..!")
            """labels = ['coin_name', 'fir_invest_money', 'fir_price', 'avr_price', 'balance', 'quintuple_batting',
          'invest_cash','tot_invest_cash', 'set_stage', 'cur_stage', 'div_per', 'in_per', 'out_per',
          'next_buy_price', 'next_income_price', 'next_out_price', 'outcome_state', 'rebuy_chkbox',
          'state', 'gubun','high','gamsi_per','gamsi_price','trailing_per','trailing_income_price','last_trade_time']"""

            df = pd.DataFrame(columns=labels)
            for i in tickers:
                logger.debug("add %s", i)
                coin_data_list[i] = {'coin_name': coin_Kname[i], 'fir_invest_money': 0, 'fir_price': 0,
                                     'avr_price': 0, 'balance': 0, 'invest_cash': 0, 'tot_invest_cash': 0,
                                     'set_stage': 0, 'cur_stage': 0,
                                     'div_per': 0, 'in_per': 0, 'out_per': 0, 'next_buy_price': 0,
                                     'next_income_price': 0, 'next_out_price': 0,
                                     'outcome_state': 0, 'rebuy_chkbox': False, 'state': 0, 'gubun': 0, 'high': 0,
                                     'gamsi_per': 0, 'gamsi_price': 0,
                                     'trailing_per': 0, 'trailing_income_price': 0, 'trailing_state': 0,
                                     'last_trade_time': 0}

            all_modify_csv()
        else:
            with open(csv_path, 'rb') as f:
                coin_data_list = pickle.load(f)

            if len(coin_data_list) != len(tickers):
                logger.debug("load 한 코인 개수와 서버 코인 수량 다름")
                for i in tickers:
                    if not i in coin_data_list.keys():
                        logger.debug("%s 코인 추가", i)
                        coin_data_list[i] = {'coin_name': coin_Kname[i], 'fir_invest_money': 0, 'fir_price': 0,
                                             'avr_price': 0, 'balance': 0, 'invest_cash': 0, 'tot_invest_cash': 0,
                                             'set_stage': 0, 'cur_stage': 0,
                                             'div_per': 0, 'in_per': 0, 'out_per': 0, 'next_buy_price': 0,
                                             'next_income_price': 0, 'next_out_price': 0,
                                             'outcome_state': 0, 'rebuy_chkbox': False, 'state': 0, 'gubun': 0,
                                             'high': 0,
                                             'gamsi_per': 0, 'gamsi_price': 0,
                                             'trailing_per': 0, 'trailing_income_price': 0, 'trailing_state': 0,
                                             'last_trade_time': 0}
                all_modify_csv()

        ing_count = 0
        set_1 = 0
        set_2 = 0
        set_3 = 0
        set_4 = 0
        set_5 = 0
        set_6 = 0
        set_7 = 0
        set_8 = 0
        set_9 = 0
        set_10 = 0

        for line in coin_data_list:
            # logger.debug(line)
            if str(coin_data_list[line]['cur_stage']) != '0':
                ing_count = ing_count + 1
                if str(coin_data_list[line]['cur_stage']) == '1':
                    set_1 = set_1 + 1
                elif str(coin_data_list[line]['cur_stage']) == '2':
                    set_2 = set_2 + 1
                elif str(coin_data_list[line]['cur_stage']) == '3':
                    set_3 = set_3 + 1
                elif str(coin_data_list[line]['cur_stage']) == '4':
                    set_4 = set_4 + 1
                elif str(coin_data_list[line]['cur_stage']) == '5':
                    set_5 = set_5 + 1
                elif str(coin_data_list[line]['cur_stage']) == '6':
                    set_6 = set_6 + 1
                elif str(coin_data_list[line]['cur_stage']) == '7':
                    set_7 = set_7 + 1
                elif str(coin_data_list[line]['cur_stage']) == '8':
                    set_8 = set_8 + 1
                elif str(coin_data_list[line]['cur_stage']) == '9':
                    set_9 = set_9 + 1
                elif str(coin_data_list[line]['cur_stage']) == '10':
                    set_10 = set_10 + 1

            # logger.debug("coin_data_list[line]= %s", coin_data_list[line['coin_code']])

        logger.debug("read file success...!")
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())



def all_modify_csv():
    try:
        global coin_data_list
        with open(csv_path, 'wb') as f:
            pickle.dump(coin_data_list, f)

        with open(sub_csv_path, 'wb') as f:
            pickle.dump(coin_data_list, f)
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())


def diff_coin_totalNum():
    try:
        global tickers, coin_data_list, coin_Kname, csv_path, sub_csv_path

        if os.path.exists(csv_path):
            with open(csv_path, 'rb') as f:
                coin_data_list = pickle.load(f)
        else:
            read_csv_file()

        c = list(set(list(coin_data_list.keys())) - set(tickers))
        if len(c) > 0:
            logger.debug('기존데이터에서 {} 제거해야함. sub 파일에 저장'.format(c))

            all_modify_csv()
            for i in c:
                coin_data_list.pop(i)
            all_modify_csv()

        c = list(set(tickers) - set(list(coin_data_list.keys())))
        if len(c) > 0:
            logger.debug('기존데이터에서 리스트 추가.{}'.format(c))
            for i in c:
                if not i in coin_data_list.keys():
                    logger.debug("%s 코인 추가", i)
                    coin_data_list[i] = {'coin_name': coin_Kname[i], 'fir_invest_money': 0, 'fir_price': 0,
                                         'avr_price': 0, 'balance': 0, 'invest_cash': 0, 'tot_invest_cash': 0,
                                         'set_stage': 0, 'cur_stage': 0,
                                         'div_per': 0, 'in_per': 0, 'out_per': 0, 'next_buy_price': 0,
                                         'next_income_price': 0, 'next_out_price': 0,
                                         'outcome_state': 0, 'rebuy_chkbox': False, 'state': 0, 'gubun': 0,
                                         'high': 0,
                                         'gamsi_per': 0, 'gamsi_price': 0,
                                         'trailing_per': 0, 'trailing_income_price': 0, 'trailing_state': 0,
                                         'last_trade_time': 0}

            all_modify_csv()

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


test_case = False
def get_yesterday_price():
    global yesterday_price, get_data_flag, tickers, test_case
    try:
        logger.debug("일봉 데이터 수집중........")
        get_data_flag = False
        sleep(0.5)
        if test_case == True:
            for ticker in tickers:
                yesterday_price[ticker] = {'open':[10000,10000,10000],'close':[10000,10000,10000],'high':[10000,10000,10000]}
                yesterday_updown = float(
                    calc_income_rate(yesterday_price[ticker]['open'][-2], yesterday_price[ticker]['close'][-1]))
                yesterday_price[ticker] = {'today': yesterday_price[ticker]['open'][-1], 'yesterday': yesterday_updown,
                                           'high': yesterday_price[ticker]['high'][-1]}
        else:
            for ticker in tickers:
                yesterday_price[ticker] = pyupbit.get_ohlcv(ticker, 'day', 3)

                if (len(yesterday_price[ticker]['open']) >= 2) & (len(yesterday_price[ticker]['close']) >= 2):
                    yesterday_updown = float(
                        calc_income_rate(yesterday_price[ticker]['open'][-2], yesterday_price[ticker]['close'][-1]))

                    yesterday_price[ticker] = {'today': yesterday_price[ticker]['open'][-1], 'yesterday': yesterday_updown,
                                               'high': yesterday_price[ticker]['high'][-1]}
                    sleep(0.3)
                else:
                    yesterday_updown = float(
                        calc_income_rate(yesterday_price[ticker]['open'][0], yesterday_price[ticker]['close'][0]))

                    yesterday_price[ticker] = {'today': yesterday_price[ticker]['open'][-1], 'yesterday': yesterday_updown,
                                               'high': yesterday_price[ticker]['high'][-1]}
                    sleep(0.3)
                    # logger.debug("%s 종목 일봉 데이터 수집중.. 금일 시가 - %s, 전일 등락율 - %s", ticker, str(yesterday_price[ticker]['open'][-1]), str(yesterday_updown))
                # if ticker == "KRW-BTC":
                #    break
        get_data_flag = True
        logger.debug("일봉 데이터 수집 완료")
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("get_yesterday_price error. %s", e)
        logger.debug(traceback.format_exc())

class init_data(QThread):
    init_read_data = pyqtSignal(dict)

    def run(self):
        try:
            logger.debug("init_data_read start")
            self.init_process()
            resp = {}
            resp['resp'] = 1
            self.init_read_data.emit(resp)
            sleep(0.25)

        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.information(self, "경고", "데이터 통신에 실패하였습니다. 프로그램을 다시 시작하여 주세요.")

    def init_process(self):
        try:
            global tickers

            diff_coin_totalNum()

            read_csv_file()  # csv파일 읽기
            get_yesterday_price()  # 전일 종가 데이터
            # 과거 데이터 수집하기
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 담당자에게 문의주세요.')

update_p = 0
main = object
class MyWindow(QMainWindow, start_class):

    def __init__(self):
        try:
            global get_data_flag, my_cash_data, key

            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("BIT-WIN Auto Trading Realtime Program ")
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

            self.regi_lbl.clicked.connect(self.register_func)

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
                    previous_date = datetime(int(key['time'][:4]), int(key['time'][4:6]),
                                                      int(key['time'][6:8]),
                                                      23, 59, 0)
                    if previous_date < datetime.now():
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
                        sleep(0.2)
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
            QMessageBox.information(self,'확인', '로그인 에러. 아이디 패스워드 또는\nIP 주소를 확인해주세요.')

    def login_btn_func(self):
        global MAIN_UPBIT, user_name, my_cash, key, update_flag, connection_flag
        try:
            self.update_frame.setVisible(True)
            key = {}
            user_name = self.userName.text()
            txt = "login_" + user_name

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


# condition algorithm

def get_stoch(candle_data):
    try:
        N = 20
        M = 10
        T = 10
        L = candle_data["low"].rolling(window=N).min()
        H = candle_data["high"].rolling(window=N).max()

        fast_k = ((candle_data["close"] - L) / (H - L)) * 100
        slow_k = fast_k.ewm(span=M).mean()
        slow_d = slow_k.ewm(span=T).mean()

        if (slow_k[-3] < slow_d[-3]) & (slow_k[-2] >= slow_d[-2]):
            return 'ok'
        else:
            return 'fail'
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("get_stoch error. %s", e)
        logger.debug(traceback.format_exc())


# -----------------------------------------------------------------------------
# - Name : get_cci
# - Desc : CCI 조회
# - Input
#   1) candle_data : 캔들 정보
#   2) loop_cnt : 조회 건수
# - Output
#   1) CCI 값
# -----------------------------------------------------------------------------
def get_cci(candle_data, len):
    try:
        len = int(len)

        df = pd.DataFrame(candle_data)

        # 계산식 : (Typical Price - Simple Moving Average) / (0.015 * Mean absolute Deviation)
        df['TP'] = (df['high'] + df['low'] + df['close']) / 3
        df['SMA'] = df['TP'].rolling(window=len).mean()
        df['MAD'] = df['TP'].rolling(window=len).apply(lambda x: pd.Series(x).mad())
        df['CCI'] = (df['TP'] - df['SMA']) / (0.015 * df['MAD'])

        # logger.debug("%s %s", df['CCI'][-3], df['CCI'][-2])
        # 개수만큼 조립
        if ((df['CCI'][-5] < -200) & (df['CCI'][-4] < -150) & (df['CCI'][-3] < -130) & (df['CCI'][-2] >= -130)):
            # logger.debug("1. %s %s %s", df['CCI'][-3], df['CCI'][-2], g1)
            return 'ok'

        """
        if ((df['CCI'][-3] < g2) & (df['CCI'][-2] >= g2)):
            logger.debug("2. %s %s %s", df['CCI'][-3], df['CCI'][-2], g2)
            return 'ok'

        if ((df['CCI'][-3] < g3) & (df['CCI'][-2] >= g3)):
            logger.debug("3. %s %s %s", df['CCI'][-3], df['CCI'][-2], g3)
            return 'ok'
        """

        return 'fail'
    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("error. %s", e)
        logger.debug(traceback.format_exc())


# -----------------------------------------------------------------------------
# - Name : envelope
# - Desc : 엔벨로프 조회
# - Input
#   1) candle_data : 캔들 정보
#   2) 기간
#   3) percent
# - Output
#   1) 엔벨로프 하방 탈출 여부
# -----------------------------------------------------------------------------
def get_envelope(candle_datas, line, diff):
    try:
        # 볼린저밴드 데이터 리턴용


        val1 = int(line)
        val2 = float(diff)

        df = pd.DataFrame(candle_datas)

        df['ma20'] = df['close'].rolling(window=val1).mean()  # 20일 이동평균
        val = df['ma20'][-2] - ((df['ma20'][-2] * val2) / 100)

        if (val > df['close'].iloc[-2]) & (df['close'].iloc[-2] < df['close'].iloc[-1]):
            return 'ok'
        else:
            return 'no'

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("error. %s", e)
        logger.debug(traceback.format_exc())


# -----------------------------------------------------------------------------
# - Name : Bollinger
# - Desc : 볼린저밴드 조회
# - Input
#   1) candle_data : 캔들 정보
#   2) 이동평균
#   3) 승수
# - Output
#   1) 볼린저밴드 하방 탈출 여부
# -----------------------------------------------------------------------------
def get_Bollinger(candle_datas, line, diff):
    try:
        # 볼린저밴드 데이터 리턴용

        val1 = int(line)
        val2 = int(diff)

        df = pd.DataFrame(candle_datas)

        df['ma20'] = df['close'].rolling(window=val1).mean()  # 20일 이동평균
        df['stddev'] = df['close'].rolling(window=val1).std()  # 20일 이동표준편차
        # df['upper'] = df['ma20'] + val2 * df['stddev']  # 상단밴드
        df['lower'] = df['ma20'] - val2 * df['stddev']  # 하단밴드
        # df = df[19:]  # 20일 이동평균을 구했기 때문에 20번째 행부터 값이 들어가 있음

        if (df['lower'].iloc[-2]) > (df['close'].iloc[-2]):
            return 'ok'
        else:
            return 'no'

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("error. %s", e)
        logger.debug(traceback.format_exc())


# -----------------------------------------------------------------------------
# - Name : get_line
# - Desc : 이동평균선 조회
# - Input
#   1) candle_data : 캔들 정보
# - Output
#   1) 이평선 유지 유무 값, ex)2봉 유지면 이전봉과 현재봉 비교
# -----------------------------------------------------------------------------
def get_line(candle_datas, stand, use):
    try:
        # logger.debug("%s %s", stand, use)

        stand = int(stand)
        use = int(use)

        df = pd.DataFrame(candle_datas)
        # dfDt = df['candle_date_time_kst'].iloc[::-1]
        # df = df.reindex(index=df.index[::-1]).reset_index()

        close_prices = df['close']

        line_period = df['close'].rolling(window=stand).mean()

        count = int(use) * -1
        break_flag = False
        for i in range(count, -1):
            if not line_period[i] <= line_period[i + 1]:
                break_flag = True
                break

        if break_flag == False:
            return 'ok'
        else:
            return 'fail'

    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())


# -----------------------------------------------------------------------------
# - Name : get_ilmoc
# - Desc : 일목균형표 조회
# - Input
#   1) candle_data : 캔들 정보
# - Output
#   1) 일목균형표 값
# -----------------------------------------------------------------------------
def get_ilmoc(candle_datas, val1, val2, val3):
    try:
        # RSI 데이터 리턴용
        ilmoc_data = []

        # logger.debug("%s %s %s", val1, val2, val3)
        val1 = int(val1)
        val2 = int(val2)
        val3 = int(val3)

        df = pd.DataFrame(candle_datas)
        # dfDt = df['candle_date_time_kst'].iloc[::-1]
        # df = df.reindex(index=df.index[::-1]).reset_index()

        high_prices = df['high']
        close_prices = df['close']
        low_prices = df['low']
        dates = df.index

        nine_period_high = df['high'].rolling(window=val1).max()
        nine_period_low = df['low'].rolling(window=val1).min()
        df['tenkan_sen'] = (nine_period_high + nine_period_low) / 2

        period26_high = high_prices.rolling(window=val2).max()
        period26_low = low_prices.rolling(window=val2).min()
        df['kijun_sen'] = (period26_high + period26_low) / 2

        df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(val2)

        period52_high = high_prices.rolling(window=val3).max()
        period52_low = low_prices.rolling(window=val3).min()
        df['senkou_span_b'] = ((period52_high + period52_low) / 2).shift(val2)

        m_val2 = int(val2) * (-1)
        df['chikou_span'] = close_prices.shift(m_val2)

        # logger.debug('전환선: %s', df['tenkan_sen'].iloc[-2]) #전환선 - 텐칸센 - 붉은색
        # logger.debug('기준선: %s', df['kijun_sen'].iloc[-2]) #기준선 - 키준센 - 파란색 => 파란색 빨간색을 골드, or 데드
        # print('후행스팬: ', df['chikou_span'].iloc[-27])
        # print('선행스팬1: ', df['senkou_span_a'].iloc[-1])
        # logger.debug('선행스팬2: %s', df['senkou_span_b'].iloc[-1]) #선행스팬B
        # print('')
        time.sleep(1)

        # rsi = round(rsi(df, 14).iloc[-1], 4)
        # ilmoc_data.append({"type": "RSI", "DT": dfDt[0], "RSI": rsi})

        if (df['tenkan_sen'].iloc[-3] > df['kijun_sen'].iloc[-3]) & (
                df['tenkan_sen'].iloc[-2] < df['kijun_sen'].iloc[-2]):
            return 'fail'
        elif (df['tenkan_sen'].iloc[-3] < df['kijun_sen'].iloc[-3]) & (
                df['tenkan_sen'].iloc[-2] > df['kijun_sen'].iloc[-2]) & (
                df['tenkan_sen'].iloc[-2] <= df['tenkan_sen'].iloc[-1]):
            return 'ok'
        else:
            return 'pass'

    # ----------------------------------------
    # 모든 함수의 공통 부분(Exception 처리)
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("error. %s", e)
        logger.debug(traceback.format_exc())


server_url = 'https://api.upbit.com'


def get_candle(target_item, tick_kind, inq_range):
    try:

        # ----------------------------------------
        # Tick 별 호출 URL 설정
        # ----------------------------------------
        # 분붕
        if tick_kind == "1" or tick_kind == "3" or tick_kind == "5" or tick_kind == "10" or tick_kind == "15" or tick_kind == "30" or tick_kind == "60" or tick_kind == "240":
            target_url = "minutes/" + tick_kind
        # 일봉
        elif tick_kind == "D":
            target_url = "days"
        # 주봉
        elif tick_kind == "W":
            target_url = "weeks"
        # 월봉
        elif tick_kind == "M":
            target_url = "months"
        # 잘못된 입력
        else:
            raise Exception("잘못된 틱 종류:" + str(tick_kind))

        logging.debug(target_url)

        # ----------------------------------------
        # Tick 조회
        # ----------------------------------------
        querystring = {"market": target_item, "count": inq_range}
        res = send_request("GET", server_url + "/v1/candles/" + target_url, querystring, "")
        candle_data = res.json()

        logging.debug(candle_data)

        return candle_data

    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("error. %s", e)
        logger.debug(traceback.format_exc())


def send_request(reqType, reqUrl, reqParam, reqHeader):
    try:

        # 요청 가능회수 확보를 위해 기다리는 시간(초)
        err_sleep_time = 0.3

        # 요청에 대한 응답을 받을 때까지 반복 수행
        while True:

            # 요청 처리
            response = requests.request(reqType, reqUrl, params=reqParam, headers=reqHeader, verify=False)

            # 요청 가능회수 추출
            if 'Remaining-Req' in response.headers:

                hearder_info = response.headers['Remaining-Req']
                start_idx = hearder_info.find("sec=")
                end_idx = len(hearder_info)
                remain_sec = hearder_info[int(start_idx):int(end_idx)].replace('sec=', '')
            else:
                logging.error("헤더 정보 이상")
                logging.error(response.headers)
                break

            # 요청 가능회수가 3개 미만이면 요청 가능회수 확보를 위해 일정시간 대기
            if int(remain_sec) < 3:
                logging.debug("요청 가능회수 한도 도달! 남은횟수:" + str(remain_sec))
                time.sleep(err_sleep_time)

            # 정상 응답
            if response.status_code == 200 or response.status_code == 201:
                break
            # 요청 가능회수 초과인 경우
            elif response.status_code == 429:
                logging.error("요청 가능회수 초과!:" + str(response.status_code))
                time.sleep(err_sleep_time)
            # 그 외 오류
            else:
                logging.error("기타 에러:" + str(response.status_code))
                logging.error(response.status_code)
                break

            # 요청 가능회수 초과 에러 발생시에는 다시 요청
            logging.info("[restRequest] 요청 재처리중...")

        return response

    # ----------------------------------------
    # Exception Raise
    # ----------------------------------------
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("error. %s", e)
        logger.debug(traceback.format_exc())

if __name__ == "__main__":
    try:
        global test
        test = True
        app = QApplication(sys.argv)
        main = MyWindow()
        main.show()
        app.exec_()
    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())