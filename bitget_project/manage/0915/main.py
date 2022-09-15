# -*- coding: utf-8 -*-


import socket
import sys
import tempfile
import threading
#import numpy as np
import os
from datetime import datetime
import datetime as dt
import winsound as sd
import pickle
#import ccxt
import time

from PyQt5.QtGui import QIcon, QMovie, QPixmap
from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QTableWidgetItem
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QThread

if not os.path.exists('DATA'):
    os.makedirs('DATA')

if not os.path.exists('logFile'):
    os.makedirs('logFile')

import traceback
import logging
from logging.handlers import TimedRotatingFileHandler


import bitget_api.bitget.mix.market_api as market
import bitget_api.bitget.mix.account_api as accounts
import bitget_api.bitget.mix.position_api as position
import bitget_api.bitget.mix.order_api as order
import bitget_api.bitget.mix.plan_api as plan
import bitget_api.bitget.mix.trace_api as trace

nowDate = datetime.now()
filename = str("./logFile./" + nowDate.strftime("%Y-%m-%d_%H-%M") + "1.txt")
logger = logging.getLogger(__name__)

fileMaxByte = 10.24 * 1024 * 100
fileHandler = logging.handlers.TimedRotatingFileHandler(filename='./logFile/main.log', when='midnight', interval=1,
                                                        backupCount=10)
logger.addHandler(fileHandler)
fileHandler.suffix = "%Y-%m-%d_%H-%M1.log"

formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(funcName)15s():%(lineno)s] >> %(message)s')
fileHandler.setFormatter(formatter)

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)
logger.setLevel(level=10)

main_class = uic.loadUiType('./ui/main.ui')[0]
#start_class = uic.loadUiType('./ui/login.ui')[0]

#register_class = uic.loadUiType('./ui/register.ui')[0]

update_flag = False
key = {}  # ak = 이름, sk= 계좌정보
connection_flag = ''
update_p = 0
user_name = ''

div_data = {}

"""
div_data label 설명  

symbol = 'BTCUSDT_UMCBL' #선물거래

data_load #초기화

div_data = {}
div_data[symbol] = {}
div_data[symbol]['long'] = {}
div_data[symbol]['short'] = {}
div_data[symbol]['long']['state'] = '대기'
div_data[symbol]['short']['state'] = '대기'


div_data = {

    'BTCUSDT_UMCBL' : {
        price_comp_func(),data_load 에서 업데이트
        state : '대기', 0차매수, '1차매수', '2차매수', ... 
        
        set_div_data() 에서 업데이트
        start_amt : float : 시작 구매량
        refresh_rate : float : 
        leverage :
        div_step : int : 최대 open 진행단계
        rebuy : Boolean : close 후 재구매 여부
        
        short : { 
            cut_rate : float : 수익 컷 기준율
            cut_rate_b : float : 수익 보정률
            escape_rate : float : 손절률 
            mul_rate : float : 최대 물타기율 
            
            get_position() 에서 업데이트
            avr : 평균 단가
            leverage : str
            ROE : float(.2f) : 수익률
            total : float : 총 보유수량
            price : float : 현재가
            
            price_comp_func()에서 업데이트
            MAX_ROE : float : 각 차수 매수 후 최대 수익률
            MIN_ROE : float : 각 차수 매수 후 최소 수익률
            close_activate : Boolean : 매도(close) 기준 수익률 도달 여부
            open_activate : Boolean : 매수(open) 기준 수익률 도달 여부
        }
        
        long : { 
            cut_rate : float : 수익 컷 기준율
            cut_rate_b : float : 수익 보정률
            escape_rate : float : 손절률 
            mul_rate : float : 최대 물타기율 
            
            get_position() 에서 업데이트
            avr : 평균 단가
            leverage : str
            ROE : float(.2f) : 수익률
            total : float : 총 보유수량
            price : float : 현재가
            
            price_comp_func()에서 업데이트
            MAX_ROE : float : 각 차수 매수 후 최대 수익률
            MIN_ROE : float : 각 차수 매수 후 최소 수익률
            close_activate : Boolean : 매도(close) 기준 수익률 도달 여부
            open_activate : Boolean : 매수(open) 기준 수익률 도달 여부
        }
        
        set_div_data() 에서 업데이트
        1차매수 : {
            amt : float : 1차매수량
            mul : float : 매수 수익저하 기준율
            mul_b : float : 매수 수익저하 보정률
        }
        2차매수 : {
            amt : float : 2차매수량
            mul : float : 매수 수익저하 기준율
            mul_b : float : 매수 수익저하 보정률
        }
        ...
        

"""

div_data_path = './DATA/div_data.pickle'
setting_data_path = './DATA/settings.pickle'
# user_data
user_data = {}

# 자동매매 플래그
auto_flag = False

# 보유 현금 저장 변수
my_cash = 0

#보고있는 코인
symbol = 'BTCUSDT_UMCBL'
symbols = ['BTCUSDT_UMCBL',] # 여러 코인 등록시, for symbol in symbols : 로 symbol 있는 곳을 덮어줌
#사용자 설정 새로고침 주기
CLIENT_REFRESH_RATE = 3

#매매 상태 저장 변수
trade_state = []

class Main(QMainWindow, main_class):  # param1 = windows : 창,  param2 = ui path

    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("BITGET_COIN AutoTrading System ver 0.01")
            #self.setWindowIcon(QIcon("./image/icon.ico"))

            # ==============bitget=========================
            self.login_success = False

            # init
            self.initial()

            # 쓰레드1
            self.mythread1 = MyThread()
            self.mythread1.finished.connect(self.price_comp_func)
            self.mythread1.finished2.connect(self.get_position)
            self.mythread1.start()

            #==========UI=============
            self.login_btn.clicked.connect(self.login_btn_func)
            self.setting_save_btn.clicked.connect(self.setting_save_func)
            self.setting_load_btn.clicked.connect(self.setting_load_func)
            self.trading_start_btn.clicked.connect(lambda: self.trading_state_func('start'))
            self.trading_stop_btn.clicked.connect(lambda: self.trading_state_func('stop'))
            self.setting_apply_btn.clicked.connect(self.setting_apply_btn_func)


        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def initial(self):
        global div_data, symbol

        logger.debug("initiating ...")
        self.login()
        self.table_init()
        self.setting_load_func()

    def after_login_initial(self):
        if self.login_success:
            self.data_load()
            self.update_jango()
            self.get_position()
            global test
            if test:
                self.test()
            else:
                return 0

        logger.debug("종료")
        self.real_log_widget.addItem("[system] 프로그램 시작")

    def test(self): #todo : test 함수 여기에
        pass




#=============login_func===================
    def login(self):
        logger.debug("initiating ...")
        self.access_key.setEchoMode(self.access_key.Password)
        self.secret_key.setEchoMode(self.secret_key.Password)
        self.password.setEchoMode(self.password.Password)
        if not os.path.exists('DATA/API.txt'): #api 저장 데이터가 없으면
            logger.debug("로그인 정보 없음 API 키 입력 후 로그인")
            self.real_log_widget.addItem("[system] 로그인 정보 없음 API 키 입력 후 로그인")
        else:
            with open('DATA/API.txt') as f: #api 저장 데이터가 있으면 파일을 열어서
                line = f.readlines()
                api_key = line[0].strip()
                secret = line[1].strip()
                password = line[2].strip()

                self.access_key.setText(api_key)
                self.secret_key.setText(secret)
                self.password.setText(password)

            self.set_login(api_key,secret,password) #로그인 시도
        logger.debug("종료")

    def login_btn_func(self): #로그인 버튼 클릭 펑션
        try:
            logger.debug("initiating ...")
            api_key = self.access_key.text()
            secret = self.secret_key.text()
            password = self.password.text()
            self.set_login(api_key, secret, password) #  ui에 입력값 가져와서 로그인 시도
            if self.login_success : # 로그인이 성공하면 api 데이터 저장
                with open('DATA/API.txt',"w") as f:
                    f.write(api_key)
                    f.write('\n')
                    f.write(secret)
                    f.write('\n')
                    f.write(password)

            logger.debug("종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def set_login(self, api_key,secret_key, passphrase ): #로그인 시도
        try:
            logger.debug("initiating ...")
            ret = False
            try:
                self.marketApi = market.MarketApi(api_key, secret_key, passphrase, use_server_time=True, first=False)
                self.accountApi = accounts.AccountApi(api_key, secret_key, passphrase, use_server_time=True, first=False)
                self.positionApi = position.PositionApi(api_key, secret_key, passphrase, use_server_time=True, first=False)
                self.orderApi = order.OrderApi(api_key, secret_key, passphrase, use_server_time=True, first=False)
                #로그인 체크
                result = self.accountApi.account(symbol, marginCoin='USDT')  # 계좌 귀속 정보
                if result["msg"] == 'success': #성공하면
                    ret = True
                else:
                    logger.debug("account error what is this msg? : ", result)
            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())
            if ret :
                logger.debug("로그인 성공")
                self.real_log_widget.addItem("[system] 로그인 성공")
                self.login_btn.setEnabled(False)
                self.login_btn.setStyleSheet("color:gray")
                self.login_success = True
                self.trading_start_btn.setEnabled(True) #시작 중지 버튼 활성화
                self.trading_start_btn.setStyleSheet("color:white")
                self.trading_start_btn.setStyleSheet("background:red")
                self.trading_stop_btn.setEnabled(True)
                self.trading_stop_btn.setStyleSheet("color:white")
                self.trading_stop_btn.setStyleSheet("background:blue")
                self.after_login_initial()
            else:
                logger.debug("로그인 실패 : API key 확인")
                self.real_log_widget.addItem("[system] 로그인 실패 : API key 확인")
                self.login_success = False
                QMessageBox.information(self, '확인', '로그인 실패 : API key 확인.\nAPI 확인 후 [로그인]을 눌러주세요.')
            logger.debug("종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())
            logger.debug("로그인 실패 : API key 확인")
            self.real_log_widget.addItem("[system] 로그인 실패 : API key 확인")
            QMessageBox.information(self, '확인', '로그인 실패 : API key 확인.\nAPI 확인 후 [로그인]을 눌러주세요.')
            self.login_success = False


#=====================data_load_func===============
    def data_load(self):
        try:
            logger.debug("initiating ...")
            global div_data
            if not os.path.exists(div_data_path):
                logger.debug("매매 데이터 없음")
                div_data = {}
                div_data[symbol] = {}
                div_data[symbol]['long'] = {}
                div_data[symbol]['short'] = {}
                div_data[symbol]['long']['state'] = '대기'
                div_data[symbol]['short']['state'] = '대기'

                div_data[symbol]['setting'] = False #세팅값 존재 변수
                div_data[symbol]['count'] = 0

                div_data[symbol]['start_amt'] = None
                div_data[symbol]['refresh_rate'] = None
                div_data[symbol]['leverage'] = None
                div_data[symbol]['div_step'] = None
                div_data[symbol]['rebuy'] = None

                div_data[symbol]['short']['cut_rate'] = None
                div_data[symbol]['short']['cut_rate_b'] = None
                div_data[symbol]['short']['escape_rate'] = None
                div_data[symbol]['short']['mul_rate'] = None

                div_data[symbol]['long']['cut_rate'] = None
                div_data[symbol]['long']['cut_rate_b'] = None
                div_data[symbol]['long']['escape_rate'] = None
                div_data[symbol]['long']['mul_rate'] = None

                div_data[symbol]['short']['close_activate'] = False
                div_data[symbol]['long']['close_activate'] = False
                div_data[symbol]['short']['open_activate'] = False
                div_data[symbol]['long']['open_activate'] = False

                for i in range(6):
                    n_state = str(i + 1) + "차매수"
                    div_data[symbol][n_state] = {}
                    div_data[symbol][n_state]["amt"] = None
                    div_data[symbol][n_state]["mul"] = None
                    div_data[symbol][n_state]["mul_b"] = None
            else:
                logger.debug("매매 데이터 있음. load")
                with open(div_data_path, 'rb') as f:
                    div_data = pickle.load(f)
                div_data[symbol]['setting'] = True
            self.real_log_widget.addItem("[system] 저장된 매매 데이터 불러오기 완료")
            logger.debug("종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    #매매 데이터 저장
    def save_div_data_func(self):
        try:
            #logger.debug("initiating ...")
            with open(div_data_path, 'wb') as f:
                pickle.dump(div_data, f)
            #self.real_log_widget.addItem("매매 데이터 저장 완료")
            #logger.debug("종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    #table의 width 조정 외 기타 init
    def table_init(self):
        try:
            logger.debug('table init..')
            #self.table_div.setEnabled(False)
            if not self.login_success: #로그인 돼있지 않으면 잠금
                self.trading_start_btn.setEnabled(False)
                self.trading_stop_btn.setEnabled(False)
                self.trading_start_btn.setStyleSheet("color:gray")
                self.trading_stop_btn.setStyleSheet("color:gray")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())





#=============================bitget_api_func==========================

    """
    umcbl   USDT future
    dmcbl   Coin  future
    cmcbl    USDC  future

    """

    def get_all_symbol(self):
        result = self.marketApi.contracts('umcbl')
        print(result)
        for i in result["data"]:
            print("###################################")
            for j, k in i.items():
                print(j, k)

    def get_last_price(self, symbol):
        #Limit rule: 20 times/1s (IP)
        try:
            result = self.marketApi.ticker(symbol)
            """
            print(result)
            print("###################################")
            for j, k in result["data"].items():
                print(j, k)"""
            return result["data"]["last"]
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return False

    def get_usdt(self):
        result = self.accountApi.account(symbol, marginCoin='USDT')  # 계좌 귀속 정보
        """
        print(result)
        print(result["msg"])
        print(result["data"]["crossMaxAvailable"])"""

        return str(int(float(result["data"]["crossMaxAvailable"])))

    def bill(self): #order history
        result = self.accountApi.accountBill(symbol, 'USDT',str(int(time.time()-86400 * 1000)), str(int(time.time() * 1000))) #24h
        print(result["data"])

        for i in result["data"]['result']:
            print("###################################################################")
            for j,k in i.items():
                print(j,k)

    @pyqtSlot()
    def get_position(self):
        global div_data
        #logger.debug("get_position")
        #Limitrule: 5times / 2s(uid)
        try:

            #productType: umcbl(USDT专业合约) dmcbl(混合合约) sumcbl(USDT专业合约模拟盘)  sdmcbl(混合合约模拟盘)
            #result = self.positionApi.all_position(productType='umcbl', marginCoin = 'USDT')
            result = self.positionApi.single_position(symbol, marginCoin='USDT')
            ret = {}
            #logger.debug(result)
            for i in result["data"]: #long, short
                tmp = {}
                for j,k in i.items():
                    tmp[j] = k

                if tmp['margin'] =='0' or tmp['unrealizedPL'] == '0': # zero division, anyway roe = 0
                    tmp['ROE'] = '0'
                else:
                    tmp['ROE'] = str( round((float(tmp['unrealizedPL'])/float(tmp['margin']))*100,2) )

                if tmp['holdSide'] =='long':
                    ret['long'] = tmp
                elif tmp['holdSide'] =='short':
                    ret['short'] = tmp


                #div_data[tmp['symbol']][tmp['holdSide']]['avr'] == div_data['USDT']['long']['avr']

                
                div_data[tmp['symbol']][tmp['holdSide']]['avr'] = tmp['averageOpenPrice']
                div_data[tmp['symbol']][tmp['holdSide']]['leverage'] = str(tmp['leverage'])
                div_data[tmp['symbol']][tmp['holdSide']]['ROE'] = float(tmp['ROE'])
                div_data[tmp['symbol']][tmp['holdSide']]['total'] = float(tmp['total'])
                div_data[tmp['symbol']][tmp['holdSide']]['price'] = float(tmp['marketPrice'])
                #div_data[tmp['symbol']][tmp['holdSide']]['available'] = float(tmp['available'])

                #logger.debug(str(div_data[tmp['symbol']][tmp['holdSide']]['close_activate']))
                #logger.debug(str(div_data[tmp['symbol']][tmp['holdSide']]['open_activate']))

                if div_data[tmp['symbol']][tmp['holdSide']]['total'] == 0.0 and div_data[tmp['symbol']][tmp['holdSide']]['state'] != '대기':
                    div_data[tmp['symbol']][tmp['holdSide']]['state'] = '대기'
                    logger.debug("상태값 이상")
                    div_data[tmp['symbol']][tmp['holdSide']]['close_activate'] = False
                    div_data[tmp['symbol']][tmp['holdSide']]['open_activate'] = False
                    div_data[tmp['symbol']][tmp['holdSide']]['MAX_ROE'] = 0
                    div_data[tmp['symbol']][tmp['holdSide']]['MIN_ROE'] = 9999
                    self.update_jango()
                    self.save_div_data_func()

            self.update_div_table()
            return ret
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())
            return False

#===============================update========================
    # 잔고 데이터, 분할매매 데이터 업데이트
    def update_jango(self):
        #logger.debug("initiating ...")
        global div_data, my_cash
        try:
            balance = self.get_usdt()
            #logger.debug(balance) #-> balance_example.txt
            self.usdt_amt.setText(balance) #가용 가능 usdt
            self.btc_count.setText(str(div_data[symbol]['count']))

            #logger.debug("종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

        # logger.debug(self.jango)

    def view_control_func(self, state):
        global auto_flag
        try:
            if state == 'start':
                auto_flag = True
                #self.trading_start_btn.setEnabled(False)
                #self.trading_start_btn.setStyleSheet("color:gray")
                self.trading_stop_btn.setEnabled(True)
                self.trading_stop_btn.setStyleSheet("color:white")
                self.trading_stop_btn.setStyleSheet("background:blue")

                # 자동매매 시작 버튼 클릭시 옵션값 변경 못하도록 변경
                self.setting_name.setEnabled(False)
                self.setting_save_btn.setEnabled(False)
                self.setting_load_btn.setEnabled(False)

                self.div_symbol.setEnabled(False)
                self.start_amt.setEnabled(False)
                self.refresh_rate.setEnabled(False)
                self.leverage.setEnabled(False)
                self.div_step.setEnabled(False)
                self.rebuy.setEnabled(False)

                self.short_cut_rate.setEnabled(False)
                self.short_cut_rate_b.setEnabled(False)
                self.short_escape_rate.setEnabled(False)
                self.short_mul_rate.setEnabled(False)

                self.long_cut_rate.setEnabled(False)
                self.long_cut_rate_b.setEnabled(False)
                self.long_escape_rate.setEnabled(False)
                self.long_mul_rate.setEnabled(False)

                self.div_setting_table.setEnabled(False)

                self.set_div_data()
                self.real_log_widget.addItem("[system] 자동매매 시작")
                logger.debug("자동매매 시작")
            else:
                auto_flag = False
                #self.trading_start_btn.setEnabled(True)
                #self.trading_start_btn.setStyleSheet("color:white")
                #self.trading_start_btn.setStyleSheet("background:red")
                self.trading_stop_btn.setEnabled(False)
                self.trading_stop_btn.setStyleSheet("color:gray")

                # 자동매매 중지 버튼 클릭시 옵션값 변경 가능하도록 변경
                self.setting_name.setEnabled(True)
                self.setting_save_btn.setEnabled(True)
                self.setting_load_btn.setEnabled(True)

                self.div_symbol.setEnabled(True)
                self.start_amt.setEnabled(True)
                self.refresh_rate.setEnabled(True)
                self.leverage.setEnabled(True)
                self.div_step.setEnabled(True)
                self.rebuy.setEnabled(True)

                self.short_cut_rate.setEnabled(True)
                self.short_cut_rate_b.setEnabled(True)
                self.short_escape_rate.setEnabled(True)
                self.short_mul_rate.setEnabled(True)

                self.long_cut_rate.setEnabled(True)
                self.long_cut_rate_b.setEnabled(True)
                self.long_escape_rate.setEnabled(True)
                self.long_mul_rate.setEnabled(True)

                self.div_setting_table.setEnabled(True)

                self.real_log_widget.addItem("[system] 자동매매 종료")
                logger.debug("자동매매 종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def trading_state_func(self, state):
        try:
            global auto_flag, trade_state

            if self.radio_all.isChecked():
                trade_state = ['long','short']
            elif self.radio_long.isChecked():
                trade_state = ['long']
            elif self.radio_short.isChecked():
                trade_state = ['short']
            else:
                pass

            logger.debug("trading_state_func : %s, trade_state : %s", state,trade_state)
            reply = QMessageBox.question(self, '확인', '매매를 {} 하시겠습니까?'.format(state))
            if reply == QMessageBox.Yes:
                self.view_control_func(state)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    # ==========================================UI FUNCTION ====================================================
    # ==========================================================================================================
    # ==========================================================================================================
    # ==========================================================================================================

    @pyqtSlot()
    def price_comp_func(self):
        global div_data, auto_flag,symbol
        try:
            if auto_flag:

                for position in ['long', 'short']:
                    if 'MAX_ROE' not in div_data[symbol][position] :
                        div_data[symbol][position]['MAX_ROE'] = 0.0
                    if 'MIN_ROE' not in div_data[symbol][position] :
                        div_data[symbol][position]['MIN_ROE'] = 9999.0
                    if 'close_activate' not in div_data[symbol][position] :
                        div_data[symbol][position]['close_activate'] = None
                    if 'open_activate' not in div_data[symbol][position] :
                        div_data[symbol][position]['open_activate'] = None
                    if 'state' not in div_data[symbol][position]:
                        div_data[symbol][position]['state'] = '대기'
                        logger.debug("이 if문은 로직상 타면 안됨")
                    """
                    logger.debug("########################################")
                    logger.debug("position : " + str(position))
                    logger.debug("ROE : " + str(div_data[symbol][position]['ROE']))
                    logger.debug("MAX_ROE : " + str(div_data[symbol][position]['MAX_ROE']))
                    logger.debug("MIN_ROE : " + str(div_data[symbol][position]['MIN_ROE']))
                    logger.debug("state : " + str(div_data[symbol][position]['state']))
                    logger.debug("cut_rate : " + str(div_data[symbol][position]['cut_rate']))
                    logger.debug("close_activate : " + str(div_data[symbol][position]['close_activate']))
                    logger.debug("open_activate : " + str(div_data[symbol][position]['open_activate']))
                    logger.debug("div_step : " + str(div_data[symbol]['div_step']))
                    #logger.debug("refresh_rate : " + str(div_data[symbol]['refresh_rate']))
                    #logger.debug("########################################" )"""

                    if div_data[symbol][position]['MAX_ROE'] < div_data[symbol][position]['ROE']: #최고수익률 갱신
                        div_data[symbol][position]['MAX_ROE'] = div_data[symbol][position]['ROE']
                        logger.debug(position + "MAX_ROE 갱신 : " + str(div_data[symbol][position]['MAX_ROE']))

                    #if div_data[symbol][position]['close_activate'] == False:
                    if div_data[symbol][position]['ROE'] >= div_data[symbol][position]['cut_rate'] : #매도준비
                            div_data[symbol][position]['close_activate'] = True
                            #logger.debug("cut_rate 넘어감 익절 대기중 ...")

                    if div_data[symbol][position]["close_activate"] : #매도준비 상태면
                        if (div_data[symbol][position]['MAX_ROE'] - div_data[symbol][position]['ROE'] >=
                            div_data[symbol][position]['MAX_ROE'] * div_data[symbol][position]['cut_rate_b']):
                            # 최고 수익 - 현재 수익 = 수익차 >= 최고 수익 * 수익 보정(10% = 0.1)
                            # 22 - 20 = 2 >=  2.2 = 22 * 10% 대기
                            # 10 - 9 = 1 >= 1 = 10 * 10% 매도 !
                            # 10 - 9 = 2 > 1  10 * 0.1 매도 !

                            #max ROE,현재 ROE, 수익보정%, 수익보정적용값

                            logger.debug("MAX_ROE : " + str(div_data[symbol][position]['MAX_ROE'] ) )
                            logger.debug("현재 ROE : " + str(div_data[symbol][position]['ROE']) )
                            logger.debug("수익보정 : " + str(div_data[symbol][position]['cut_rate_b']))

                            logger.debug("수익차 : " + str(div_data[symbol][position]['MAX_ROE'] - div_data[symbol][position]['ROE']))
                            logger.debug("수익보정 적용값  : " + str(div_data[symbol][position]['MAX_ROE'] * div_data[symbol][position]['cut_rate_b'] ))


                            if self.order_close(div_data[symbol][position]['state'], position):
                                logger.debug(div_data[symbol][position]['state'] + str(position))
                                div_data[symbol]['count'] += 1
                                #self.real_log_widget.addItem('익절 완료')

                                if div_data[symbol]['rebuy'] :
                                    if self.order_open(div_data[symbol]['start_amt'],
                                                       div_data[symbol][position]['state'],
                                                       position,'0차매수', rebuy = 1):
                                        #div_data[symbol][position]['state'] = '0차매수'
                                        #self.real_log_widget.addItem('재구매 완료')
                                        logger.debug('재구매 완료')

                                else:
                                    div_data[symbol][position]['state'] = '대기'

                            self.update_jango()

                    if div_data[symbol][position]['state'][-2:] == '매수': #매수 상태일때
                        if int(div_data[symbol][position]['state'][0]) == div_data[symbol]['div_step']:  # 마지막 단계면
                            if div_data[symbol][position]['escape_rate'] >= div_data[symbol][position]['ROE']:  # 손절
                                # -40 > -41
                                if self.order_close(div_data[symbol][position]['state'], position, 1):
                                    logger.debug("손절 실행 ...")
                                    continue
                                    #self.real_log_widget.addItem('손절 완료')

                        if int(div_data[symbol][position]['state'][0]) < div_data[symbol]['div_step'] : #마지막 단계보다 작으면
                            next_state = str(int(div_data[symbol][position]['state'][0]) + 1) + '차매수'  # 다음 차수
                            if div_data[symbol][position]['mul_rate'] > div_data[symbol][position]['ROE']: #물타기 강제분할
                                logger.debug("강제분할매수 실행 ...")
                                if self.order_open(div_data[symbol][next_state]['amt'],
                                                   div_data[symbol][position]['state'], position , next_state):
                                    logger.debug('강제분할매수 완료')
                                    continue

                                    #self.real_log_widget.addItem('강제분할매수 완료')


                            if div_data[symbol][position]['MIN_ROE'] > div_data[symbol][position]['ROE']:  # 최저수익률 갱신
                                div_data[symbol][position]['MIN_ROE'] = div_data[symbol][position]['ROE']
                                logger.debug(position + "MIN_ROE 갱신 : " + str(div_data[symbol][position]['MIN_ROE']))

                            if div_data[symbol][next_state]['mul'] > div_data[symbol][position]["ROE"] : #다음 차수 매수준비
                                div_data[symbol][position]['open_activate'] = True
                                logger.debug("cut_rate 넘어감 매수 대기중 ...")
                                # -10 > -9 대기
                                # -10 > -11 매수

                            if div_data[symbol][position]["open_activate"] : #매수준비 상태면
                                if (div_data[symbol][position]['MIN_ROE'] - div_data[symbol][position]['ROE'] <
                                    div_data[symbol][position]['MIN_ROE'] * div_data[symbol][next_state]['mul_b']):
                                    logger.debug("분할매수 실행 ...")
                                    # 최저 수익 - 현재 수익 = 변화량 < 최저 수익 * 수익 보정(10%)
                                    #-10 - -9.5 = -0.5  # -1보다 작아야됨
                                    #-20 - -19 = -1  # -2보다 작아야됨
                                    #-10 - -8 = -2 < -1
                                    if self.order_open(div_data[symbol][next_state]['amt'], div_data[symbol][position]['state'], position, next_state) :
                                        #self.real_log_widget.addItem('분할매수 완료')
                                        logger.debug('분할매수 완료')
                                        continue

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def order_open(self, amt, state, position,next_state,rebuy = 0 ):
        global div_data, my_cash, symbol
        logger.debug(str(state) + " open 진행")
        #print(str(amt), state, position)
        try:
            if position == "long":
                posi = "open_long"
            elif position == "short":
                posi = "open_short"
            else:
                logger.debug("position name error")
                return False

            result = self.orderApi.place_order(symbol, marginCoin='USDT', size=amt, side=posi, orderType='market', price='11', timeInForceValue='normal')
            #logger.debug(result)
            if result['msg'] == 'success': #주문 반응
                #logger.debug(result['data']['orderId'])
                for i in range(10):
                    order = self.orderApi.detail(symbol, orderId=result['data']['orderId']) #주문 주회 반응
                    #logger.debug(order)
                    if order['data']['state'] == 'filled': #주문 완료
                        logger.debug(posi + ' 상태 : ' + str(state) + " 수량 : " + str(amt))
                        if rebuy: #재구매
                            txt = '[재구매]'
                        else:
                            txt = ''
                        self.real_log_widget.addItem(txt + '[open][' + position + '] ' + state + ' -> ' + str(next_state) + ' : 수량 : ' + str(amt))
                        div_data[symbol][position]['state'] = next_state  # state변경
                        div_data[symbol][position]['open_activate'] = False
                        div_data[symbol][position]['MIN_ROE'] = 9999.0
                        self.save_div_data_func()
                        self.update_jango()  # 현재 잔고 업데이트
                        return True #주문 성공일시 참 반환
                    time.sleep(0.5)
                return False
            else:
                logger.debug("order didnt well " + result)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def order_close(self, state, position, sonjeol = 0):
        global div_data
        logger.debug(str(state) +" close 진행")
        try:
            if position == "long":
                posi = "close_long"
            elif position == "short":
                posi = "close_short"
            else:
                logger.debug("position name error")
                return False

            amt = div_data[symbol][position]['total']

            result = self.orderApi.place_order(symbol, marginCoin='USDT', size=amt, side=posi, orderType='market',
                                               price='11', timeInForceValue='normal')
            #logger.debug(result)
            if result['msg'] == 'success':  # 주문 반응
                logger.debug(result['data']['orderId'])
                for i in range(10):
                    order = self.orderApi.detail(symbol, orderId=result['data']['orderId'])  # 주문 주회 반응
                    logger.debug('########################')
                    logger.debug(order)
                    if order['data']['state'] == 'filled':  # 주문 완료
                        logger.debug(posi + ' 상태 : ' +str(state) + " 수량 : " + str(amt))
                        if sonjeol :
                            txt = '[손절]'
                        else:
                            txt = '[익절]'
                        self.real_log_widget.addItem(txt + '[close][' + position + '] ' + state + ' -> 대기 : 수량 : ' + str(amt) + ' 수익(USDT) : ' + str(order['data']['totalProfits']))
                        div_data[symbol][position]['close_activate'] = False
                        div_data[symbol][position]['MAX_ROE'] = 0
                        div_data[symbol][position]['state'] = '대기' #state 변경
                        self.save_div_data_func() #저장
                        self.update_jango()  # 현재 잔고 업데이트
                        return True  # 주문 성공일시 참 반환
                    time.sleep(0.5)
                return False

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def update_div_table(self):  # 테이블 업데이트 함수
        global div_data, symbol
        try:

            #long
            item_name = QTableWidgetItem(symbol)
            self.table_div.setItem(0, 0, item_name)
            setting_txt = "수익률:{}\n수익보정:{}\n손절설정:{}\n최대물타기:{}".format(div_data[symbol]['long']['cut_rate'],
                                                                      div_data[symbol]['long']['cut_rate_b'],
                                                                      div_data[symbol]['long']['escape_rate'],
                                                                      div_data[symbol]['long']['mul_rate'])
            #logger.debug(setting_txt)
            item_name.setToolTip(setting_txt)

            self.table_div.setItem(0, 1, QTableWidgetItem(str(div_data[symbol]['long']['price'])))
            self.table_div.setItem(0, 2, QTableWidgetItem(div_data[symbol]['long']['avr']))

            if div_data[symbol]['long']['ROE'] >= 0:
                txt = "▲" + str(div_data[symbol]['long']['ROE'])
                self.table_div.setItem(0, 3, QTableWidgetItem(txt))
                self.table_div.item(0, 3).setForeground(QtGui.QColor(255, 0, 0))
            else:
                txt = "▼" + str(div_data[symbol]['long']['ROE'])
                self.table_div.setItem(0, 3, QTableWidgetItem(txt))
                self.table_div.item(0, 3).setForeground(QtGui.QColor(0, 0, 255))

            self.table_div.setItem(0, 4, QTableWidgetItem(str(div_data[symbol]['long']['total'])))
            self.table_div.setItem(0, 5, QTableWidgetItem(div_data[symbol]['long']['leverage']))
            self.table_div.setItem(0, 6, QTableWidgetItem(div_data[symbol]['long']['state']))



            #short
            item_name = QTableWidgetItem(symbol)
            self.table_div.setItem(1, 0, item_name)
            setting_txt = "수익률:{}\n수익보정:{}\n손절설정:{}\n최대물타기:{}".format(div_data[symbol]['short']['cut_rate'],
                                                                      div_data[symbol]['short']['cut_rate_b'],
                                                                      div_data[symbol]['short']['escape_rate'],
                                                                      div_data[symbol]['short']['mul_rate'])
            item_name.setToolTip(setting_txt)
            self.table_div.setItem(1, 1, QTableWidgetItem(str(div_data[symbol]['short']['price'])))
            self.table_div.setItem(1, 2, QTableWidgetItem(div_data[symbol]['short']['avr']))

            if div_data[symbol]['short']['ROE'] >= 0:
                txt = "▲" + str(div_data[symbol]['short']['ROE'])
                self.table_div.setItem(1, 3, QTableWidgetItem(txt))
                self.table_div.item(1, 3).setForeground(QtGui.QColor(255, 0, 0))
            else:
                txt = "▼" + str(div_data[symbol]['short']['ROE'])
                self.table_div.setItem(1, 3, QTableWidgetItem(txt))
                self.table_div.item(1, 3).setForeground(QtGui.QColor(0, 0, 255))

            self.table_div.setItem(1, 4, QTableWidgetItem(str(div_data[symbol]['short']['total'])))
            self.table_div.setItem(1, 5, QTableWidgetItem(div_data[symbol]['short']['leverage']))
            self.table_div.setItem(1, 6, QTableWidgetItem(div_data[symbol]['short']['state']))


            #현재가 업데이트
            self.btc_price.setText(str(div_data[symbol]['long']['price']))

            for position in ['long','short']:
                if position == 'long':
                    idx = 0
                else:
                    idx = 1

                if div_data[symbol][position]['state'][-2:] == '매수':  # 매수 상태일때
                    if int(div_data[symbol][position]['state'][0]) == div_data[symbol]['div_step']:  # 마지막 단계면
                        self.table_div.item(idx, 6).setForeground(QtGui.QColor(255, 0, 0))  # 색깔 적용
                    else:
                        self.table_div.item(idx, 6).setForeground(QtGui.QColor(0, 0, 0))

                if div_data[symbol][position]['close_activate'] == True and div_data[symbol][position]['state'] != '대기' :
                    self.table_div.setItem(idx, 6, QTableWidgetItem("익절대기"))
                    logger.debug(str(position)+" : 익절대기상태")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


#######################################setting 값 관련 함수 ##################################

    def setting_save_func(self):
        try:
            if os.path.exists(setting_data_path):
                with open(setting_data_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                data = {}

            name = self.setting_name.currentText()  # combobox
            data[name] = {}

            div_symbol = self.div_symbol.currentText()#combobox
            start_amt = self.start_amt.text()
            refresh_rate = self.refresh_rate.text()
            leverage = self.leverage.text()
            div_step = self.div_step.currentText()#combox
            rebuy = self.rebuy.isChecked() #checkbox

            short_cut_rate = self.short_cut_rate.text()
            short_cut_rate_b = self.short_cut_rate_b.text()
            short_escape_rate = self.short_escape_rate.text()
            short_mul_rate = self.short_mul_rate.text()

            long_cut_rate = self.long_cut_rate.text()
            long_cut_rate_b = self.long_cut_rate_b.text()
            long_escape_rate = self.long_escape_rate.text()
            long_mul_rate = self.long_mul_rate.text()

            div_setting_table = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
            for i in range(6):
                for j in range(3):
                    div_setting_table[i][j] = self.div_setting_table.item(i, j).text()


            data[name]['div_symbol'] = div_symbol
            data[name]['start_amt'] = start_amt
            data[name]['refresh_rate'] = refresh_rate
            data[name]['leverage'] = leverage
            data[name]['div_step'] = div_step
            data[name]['rebuy'] = rebuy

            data[name]['short_cut_rate'] = short_cut_rate
            data[name]['short_cut_rate_b'] = short_cut_rate_b
            data[name]['short_escape_rate'] = short_escape_rate
            data[name]['short_mul_rate'] = short_mul_rate

            data[name]['long_cut_rate'] = long_cut_rate
            data[name]['long_cut_rate_b'] = long_cut_rate_b
            data[name]['long_escape_rate'] = long_escape_rate
            data[name]['long_mul_rate'] = long_mul_rate

            data[name]['div_setting_table'] = div_setting_table


            with open(setting_data_path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug("설정값 : "+name+"에 저장 완료")
            self.real_log_widget.addItem("[system] 설정값 : "+name+"에 저장 완료")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def setting_load_func(self):
        try:
            name = self.setting_name.currentText()  # combobox

            if not os.path.exists(setting_data_path):
                logger.debug("세팅 데이터 없음")
                self.real_log_widget.addItem("[system] 저장된 설정 데이터 없음")

            else:
                logger.debug("세팅 데이터 있음. load")
                with open(setting_data_path, 'rb') as f:
                    data = pickle.load(f)

                if name in data:
                    self.div_symbol.setCurrentText(data[name]['div_symbol'])
                    self.start_amt.setText(data[name]['start_amt'])
                    self.refresh_rate.setText(data[name]['refresh_rate'])
                    self.leverage.setText(data[name]['leverage'])
                    self.div_step.setCurrentText(data[name]['div_step'])

                    if data[name]['rebuy'] == True:
                        if self.rebuy.isChecked() == True:
                            pass
                        else:
                            self.rebuy.toggle()
                    elif data[name]['rebuy']== False:
                        if self.rebuy.isChecked() == True:
                            self.rebuy.toggle()
                        else:
                            pass

                    self.short_cut_rate.setText(data[name]['short_cut_rate'])
                    self.short_cut_rate_b.setText(data[name]['short_cut_rate_b'])
                    self.short_escape_rate.setText(data[name]['short_escape_rate'])
                    self.short_mul_rate.setText(data[name]['short_mul_rate'])

                    self.long_cut_rate.setText(data[name]['long_cut_rate'])
                    self.long_cut_rate_b.setText(data[name]['long_cut_rate_b'])
                    self.long_escape_rate.setText(data[name]['long_escape_rate'])
                    self.long_mul_rate.setText(data[name]['long_mul_rate'])
                    for i in range(6):
                        for j in range(3):
                            self.div_setting_table.setItem(i, j, QTableWidgetItem(data[name]['div_setting_table'][i][j]))

                    logger.debug("설정값 : " + name + " 불러오기 완료")
                    self.real_log_widget.addItem("[system] 저장된 설정이름 : " + name + " 불러오기 완료")
                else:
                    logger.debug("세팅값 데이터 없음")
                    self.real_log_widget.addItem("[system] 저장된 설정 데이터 없음")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def apply_setting_data(self):
        global div_data, symbol, CLIENT_REFRESH_RATE, trade_state
        try:

            leverage_t = self.leverage.text()
            try:
                self.accountApi.leverage(symbol, marginCoin='USDT', leverage=int(leverage_t), holdSide='long')
                self.accountApi.leverage(symbol, marginCoin='USDT', leverage=int(leverage_t), holdSide='short')
            except:
                self.real_log_widget.addItem("[system] 레버리지 값 설정 오류")
                QMessageBox.information(self, '확인', '레버리지 설정 값 오류\n재 설정 후 [시작]을 눌러주세요.')
                logger.debug("레버리지 값 설정 오류")
                self.view_control_func('stop')

            div_symbol = self.div_symbol.currentText()  # combobox
            start_amt = self.start_amt.text()
            refresh_rate = self.refresh_rate.text()

            CLIENT_REFRESH_RATE = float(refresh_rate)


            div_step = self.div_step.currentText()  # combox
            rebuy = self.rebuy.isChecked()  # checkbox

            short_cut_rate = self.short_cut_rate.text()
            short_cut_rate_b = self.short_cut_rate_b.text()
            short_escape_rate = self.short_escape_rate.text()
            short_mul_rate = self.short_mul_rate.text()

            long_cut_rate = self.long_cut_rate.text()
            long_cut_rate_b = self.long_cut_rate_b.text()
            long_escape_rate = self.long_escape_rate.text()
            long_mul_rate = self.long_mul_rate.text()

            div_setting_table = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]
            for i in range(6):
                for j in range(3):
                    div_setting_table[i][j] = self.div_setting_table.item(i, j).text()

            if symbol in div_data:  # todo pyqt 입력값 제한 굿 ~
                div_data[symbol]['start_amt'] = abs(float(start_amt))
                div_data[symbol]['refresh_rate'] = abs(float(refresh_rate))
                div_data[symbol]['leverage'] = leverage_t
                div_data[symbol]['div_step'] = abs(int(div_step))
                div_data[symbol]['rebuy'] = rebuy

                div_data[symbol]['short']['cut_rate'] = abs(float(short_cut_rate))
                div_data[symbol]['short']['cut_rate_b'] = abs(float(short_cut_rate_b)) / 100
                div_data[symbol]['short']['escape_rate'] = abs(float(short_escape_rate)) * -1
                div_data[symbol]['short']['mul_rate'] = abs(float(short_mul_rate)) * -1

                div_data[symbol]['long']['cut_rate'] = abs(float(long_cut_rate))
                div_data[symbol]['long']['cut_rate_b'] = abs(float(long_cut_rate_b)) / 100
                div_data[symbol]['long']['escape_rate'] = abs(float(long_escape_rate)) * -1
                div_data[symbol]['long']['mul_rate'] = abs(float(long_mul_rate)) * -1

                for i in range(len(div_setting_table)):
                    if i <= int(div_step):
                        if div_setting_table[i][0] == '' or div_setting_table[i][1] == '' or div_setting_table[i][2] == '':
                            self.real_log_widget.addItem("[system] 빈값 발견, 빈값 없이 채우고 진행")
                            self.view_control_func("stop")
                            QMessageBox.information(self, '확인', '분할매수 설정 값에 빈칸이 없어야 합니다.\n재 설정 후 [시작]을 눌러주세요.')
                        else:
                            n_state = str(i + 1) + "차매수"
                            div_data[symbol][n_state] = {}
                            div_data[symbol][n_state]["amt"] = abs(float(div_setting_table[i][0]))
                            div_data[symbol][n_state]["mul"] = abs(float(div_setting_table[i][1])) * -1  # 음수값으로 비교
                            div_data[symbol][n_state]["mul_b"] = abs(float(div_setting_table[i][2])) / 100

                self.real_log_widget.addItem("[system] 새로운 설정값으로 적용 완료")
                logger.debug("새로운 설정값으로 수정 완료")
            else:
                logger.debug("[system]심볼 없음 !")

            self.save_div_data_func()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def set_div_data(self):
        global div_data, symbol, CLIENT_REFRESH_RATE, trade_state
        try:
            if (div_data[symbol]['long']['state'] == '대기' and
                    div_data[symbol]['short']['state'] == '대기'):  # 둘 다 대기상태면 setting update
                self.apply_setting_data()
                #logger.debug("대기상태이므로 setting update 됨")
                #self.real_log_widget.addItem("대기상태이므로 setting update 됨")
            else:
                logger.debug("매수상태이므로 setting update 무시")
                #self.real_log_widget.addItem("기존 설정값 적용")

            for position in trade_state:
                if div_data[symbol][position]['state'] == '대기': #대기상태면 매수
                    if self.order_open(div_data[symbol]['start_amt'], div_data[symbol][position]['state'], position, '0차매수'):
                        div_data[symbol][position]['close_activate'] = False
                        div_data[symbol][position]['open_activate'] = False
                        div_data[symbol][position]['MAX_ROE'] = 0
                        div_data[symbol][position]['MIN_ROE'] = 9999
            self.save_div_data_func()
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def setting_apply_btn_func(self): #todo : 설정값 수정시 div_data에는 저장됨 그러나 세팅 피클값에는 적용 안됨 적용되게 해야하나 ?
        reply = QMessageBox.question(self, '확인', '진행중인 자동매매에 현재 설정값으로 수정 하시겠습니까? \n현재 진입 상태에 유의하십시오.')
        if reply == QMessageBox.Yes:
            self.apply_setting_data()
            #self.real_log_widget.addItem("새로운 설정값으로 수정 완료")
            #logger.debug("새로운 설정값으로 수정 완료")





"""
@ 가격 정보 변동 체크 쓰레드
"""

class MyThread(QThread):
    finished = pyqtSignal()
    finished2 = pyqtSignal()

    def __init__(self):
        try:
            super().__init__()
            logger.debug("run thread")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def run(self):  # 매초마다 받아온 데이터 집어넣기
        try:
            global login_flag, auto_flag, test,main,symbol , CLIENT_REFRESH_RATE
            heartBeat = 0
            while True:
                time.sleep(CLIENT_REFRESH_RATE)
                #time.sleep(4)
                heartBeat += 1
                if heartBeat > 60:
                    logger.debug("myThread heartBeat...!")
                    heartBeat = 0
                if main.login_success :
                    price = main.get_last_price(symbol)
                    if price != False:
                        self.finished.emit()
                    self.finished2.emit()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())




if __name__ == "__main__":
    logger.debug("window start")
    app = QApplication(sys.argv)
    global test
    test = 1
    if test:
        logger.debug("test start")
        login_flag = True
        main = Main()
        main.show()
    else:
        logger.debug("real start")
        myWindow = MyWindow()
        myWindow.show()


    app.exec_()
