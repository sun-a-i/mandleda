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

import telegram
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

            self.login_flag = False

            self.login_btn.clicked.connect(self.login_btn_func)
            self.test_btn.clicked.connect(self.test_func)

            self.start_btn.clicked.connect(lambda: self.state_func('start'))
            self.stop_btn.clicked.connect(lambda: self.state_func('stop'))

            self.load_data()
            self.check_tele_data()

            self.worker = Mythread()
            self.worker.start()

            self.login()

        except Exception as e:
            logger.debug(e)

    def test_func(self):
        buy = main_upbit.buy_market_order('KRW-BTC', main.money.text())
        print(type(buy))
        if type(buy) != dict:
            main.real_log_print("[error] 구매 불가 오류")
            tel_send_msg("구매 불가 오류")
        main.update_balance()

    #=============login func==================

    def login(self):
        access_key , secret_key = self.login_data_check()
        if (access_key , secret_key) != (False, False):
            self.login_upbit(access_key, secret_key)
            self.login_btn_func(access_key, secret_key)

    def login_data_check(self):
        if not os.path.exists(api_data_path):
            self.real_log_print("[error] 로그인 정보 없음 API.txt 작성 후 로그인")
            return False, False
        else:
            with open(api_data_path) as f:  # api 저장 데이터가 있으면 파일을 열어서
                line = f.readlines()
                access_key = line[0].strip()
                secret_key = line[1].strip()
                self.real_log_print("[system] 로그인 정보 있음 자동 로그인 시도")
                return access_key,secret_key

    def login_upbit(self, access_key, secret_key):
        global main_upbit
        main_upbit = pyupbit.Upbit(access_key, secret_key)

    def login_status_check(self):
        global main_upbit
        balance = main_upbit.get_balance('KRW-ETH')
        if type(balance) == float or type(balance) == int:
            self.login_flag = True
            return True
        else:
            return False

    def login_btn_func(self,access_key, secret_key): #로그인 버튼 클릭 펑션
        try:
            if self.login_status_check() : # 로그인이 성공하면 api 데이터 저장
                self.real_log_print("[system] 로그인 성공")
                with open(api_data_path,"w") as f:
                    f.write(access_key)
                    f.write('\n')
                    f.write(secret_key)
                    f.write('\n')

                self.login_btn.setEnabled(False)
                self.login_btn.setStyleSheet("color:gray")

                self.start_btn.setEnabled(True)  # 시작 중지 버튼 활성화
                self.start_btn.setStyleSheet("background:red")
                self.stop_btn.setEnabled(False)

                self.after_login_initial()
            else:
                self.real_log_print("[error] 로그인 실패")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


# ===================================setting data func============================
    def save_data(self):
        try:
            if os.path.exists(setting_data_path):
                with open(setting_data_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                data = {}

            RSI_Length = self.rsi_len.text()
            RSI_lower_val = self.rsi_min.text()
            stock_RSI_strong_peoriod = self.srsi_rel.text()  # todo : 상대강도기간, stoch 기간
            SmoothK = self.srsi_k.text()
            SmoothD = self.srsi_d.text()
            stock_RSI_lower_val = self.k_d_min.text()
            money = self.money.text()
            buy_ck = self.buy_ck.isChecked()
            set_time = self.settime_cbox.currentIndex()


            data['RSI_Length'] = RSI_Length
            data['RSI_lower_val'] = RSI_lower_val
            data['stock_RSI_strong_peoriod'] = stock_RSI_strong_peoriod
            data['stock_RSI_strong_peoriod'] = stock_RSI_strong_peoriod
            data['SmoothK'] = SmoothK
            data['SmoothD'] = SmoothD
            data['stock_RSI_lower_val'] = stock_RSI_lower_val
            data['money'] = money
            data['buy_ck'] = buy_ck
            data['set_time'] = set_time

            with open(setting_data_path, 'wb') as f:
                pickle.dump(data, f)


        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def load_data(self):
        try:
            if not os.path.exists(setting_data_path):
                self.real_log_print("[system] 저장된 설정 데이터 없음")
            else:
                self.real_log_print("[system] 저장된 설정 데이터 있음")
                with open(setting_data_path, 'rb') as f:
                    data = pickle.load(f)

                    self.rsi_len.setText(data['RSI_Length'])
                    self.rsi_min.setText(data['RSI_lower_val'])
                    self.srsi_rel.setText(data['stock_RSI_strong_peoriod'])
                    self.srsi_k.setText(data['SmoothK'])
                    self.srsi_d.setText(data['SmoothD'])
                    self.k_d_min.setText(data['stock_RSI_lower_val'])
                    self.money.setText(data['money'])
                    if self.buy_ck.isChecked() != data['buy_ck']:
                        self.buy_ck.toggle()
                    self.settime_cbox.setCurrentIndex(data['set_time'])
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def after_login_initial(self):
        self.update_balance()


#================telegram func===============================
    def check_tele_data(self):
        try:
            if not os.path.exists(telegram_data_path):
                self.real_log_print("[error] 저장된 텔레그램 데이터 없음 DATA/telegram.txt 작성")
            else:
                self.real_log_print("[system] 저장된 텔레그램 데이터 있음")
                with open(telegram_data_path) as f:  # api 저장 데이터가 있으면 파일을 열어서
                    global tel_token, tel_id
                    line = f.readlines()
                    tel_token = line[0].strip()
                    tel_id = line[1].strip()
                    self.real_log_print("[system] 텔레그램 프로그램 시작 메세지 전송")
                    #tel_send_msg("프로그램 시작")
                    return True

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    #update jango
    def update_balance(self):
        balance = main_upbit.get_balance(ticker="KRW")
        self.money_label.setText(str(int(balance)))
        pass

    #real_log and debug print
    def real_log_print(self, txt):
        self.real_log.addItem(txt)
        logger.debug(txt)

    def state_func(self, state):
        global auto_flag
        try:
            self.save_data()
            if state == 'start':
                global RSI_Length, RSI_lower_val, stock_RSI_strong_peoriod, SmoothK, SmoothD, stock_RSI_lower_val, money, set_time
                try:
                    RSI_Length = int(main.rsi_len.text())
                    RSI_lower_val = int(main.rsi_min.text())
                    stock_RSI_strong_peoriod = int(main.srsi_rel.text())
                    SmoothK = int(main.srsi_k.text())
                    SmoothD = int(main.srsi_d.text())
                    stock_RSI_lower_val = int(main.k_d_min.text())
                    set_time = main.settime_cbox.currentText()
                    money = main.money.text()
                except:
                    main.real_log_print('[error] 값 오류 : 작성 후 다시 시작')
                    return 0

                auto_flag = True
                self.start_btn.setEnabled(False)
                self.start_btn.setStyleSheet("color:gray")
                self.stop_btn.setEnabled(True)
                self.stop_btn.setStyleSheet("color:white")
                self.stop_btn.setStyleSheet("background:blue")

                # 자동매매 시작 버튼 클릭시 옵션값 변경 못하도록 변경
                self.rsi_len.setEnabled(False)
                self.rsi_min.setEnabled(False)

                self.srsi_rel.setEnabled(False)
                self.srsi_k.setEnabled(False)
                self.srsi_d.setEnabled(False)

                self.k_d_min.setEnabled(False)
                self.money.setEnabled(False)

                self.settime_cbox.setEnabled(False)

                self.real_log_print("[system] 자동매매 시작")
            else:
                auto_flag = False
                self.start_btn.setEnabled(True)
                self.start_btn.setStyleSheet("color:white")
                self.start_btn.setStyleSheet("background:red")
                self.stop_btn.setEnabled(False)
                self.stop_btn.setStyleSheet("color:gray")

                # 자동매매 중지 버튼 클릭시 옵션값 변경 가능하도록 변경
                self.rsi_len.setEnabled(True)
                self.rsi_min.setEnabled(True)

                self.srsi_rel.setEnabled(True)
                self.srsi_k.setEnabled(True)
                self.srsi_d.setEnabled(True)

                self.k_d_min.setEnabled(True)
                self.money.setEnabled(True)

                self.settime_cbox.setEnabled(True)

                self.real_log_print("[system] 자동매매 종료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

RSI_Length= 0
RSI_lower_val= 0
stock_RSI_strong_peoriod= 0
SmoothK= 0
SmoothD= 0
stock_RSI_lower_val = 0

class Mythread(QThread):
    #signal = pyqtSignal()

    def __init__(self):
        super().__init__()


    def run(self):
        global auto_flag, main_upbit
        while True:
            try:
                if auto_flag:
                    ret = False
                    set_time = main.settime_cbox.currentText()
                    now_time = dt.datetime.now()
                    if set_time == '60' and now_time.minute == 0:
                        ret = True
                    elif set_time == '240' and now_time.minute == 0 and now_time.hour % 4 == 0:
                        ret = True
                    elif set_time == 'day' and now_time.minute == 0 and now_time.hour == 9:
                        ret = True

                    if ret:
                        logger.debug("자동거래 시간 도달 자동매매 시작")
                        CC = Check_Condition('KRW-BTC', set_time)
                        if CC and main.buy_ck.isChecked():
                            buy = main_upbit.buy_market_order('KRW-BTC', main.money.text())
                            if type(buy) != dict:
                                main.real_log_print("[error] 구매 불가 오류")
                                tel_send_msg("구매 불가 오류")
                            main.update_balance()
                        time.sleep(60)
                    main.update_balance()
                    time.sleep(10)
                else:
                    time.sleep(10)
                    main.update_balance()
            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())





#========================telegram func===================================



def tel_send_msg(txt):
    try:
        global tel_token, tel_id
        bot = telegram.Bot(token = tel_token)
        bot.sendMessage(chat_id = tel_id, text = txt)

    except Exception as e:
        logger.debug(e)




#param1 : coin, param2:기준봉(1시간, 4시간, 1일)
def Check_Condition(coin, bunbong):

    try:
        global RSI_Length, RSI_lower_val, stock_RSI_strong_peoriod, SmoothK, SmoothD, stock_RSI_lower_val
        con_fir = False
        con_sec = False
        #print("###########")
        #print(RSI_Length, RSI_lower_val, stock_RSI_strong_peoriod, SmoothK, SmoothD, stock_RSI_lower_val)
        if str(bunbong).isdigit(): #60 or 240만 있음
            df = pyupbit.get_ohlcv(coin, interval="minutes" + str(bunbong), count=200)
        else:
            df = pyupbit.get_ohlcv(coin, interval="day", count=200)

        #RSI calc - 1차 조건
        delta = df['close'].diff(1)
        delta = delta.dropna()
        up = delta.copy()
        down = delta.copy()
        up[ up < 0 ] = 0
        down[ down > 0 ] = 0
        time_period = RSI_Length
        AVG_Gain = up.ewm(com=time_period-1, min_periods=time_period).mean()
        AVG_Loss = abs(down.ewm(com=time_period-1, min_periods=time_period).mean())
        RS = AVG_Gain / AVG_Loss
        RSI = 100.0 - (100.0/(1.0 + RS))
        df['RSI'] = RSI

        if df['RSI'][-1] < RSI_lower_val:
            if df['RSI'][-3] >= df['RSI'][-2]:
                if df['RSI'][-2] < df['RSI'][-1]:
                    # 1차 부합 시 로그 & 텔레그램
                    con_fir = True
                    txt = "1차부합, coin : {}, RSI[1봉전] : {}, RSI[종가] : {}".format(coin, df['RSI'][-2],df['RSI'][-1])
                    print(txt)
                    tel_send_msg(txt)


        #stoch_RSI - 2차 조건
        min_val  = df['RSI'].rolling(window=stock_RSI_strong_peoriod, center=False ).min()
        max_val = df['RSI'].rolling(window=stock_RSI_strong_peoriod, center=False).max()
        stoch = ( (df['RSI'] - min_val) / (max_val - min_val) ) * 100
        K = stoch.rolling(window=SmoothK, center=False).mean()
        D = K.rolling(window=SmoothD, center=False).mean()
        df['K'], df['D'] = K, D

        if df['K'][-1] < stock_RSI_lower_val and df['D'][-1] < stock_RSI_lower_val:
            if df['K'][-2] < df['D'][-2]:
                if df['K'][-1] >= df['D'][-1]:
                    # 2차 부합 시 로그 & 텔레그램
                    con_sec = True
                    txt = "매수포착 coin:{}, stock[K]:{}, stock[D]:{}".format(coin, df['K'][-1], df['D'][-1])
                    print(txt)
                    tel_send_msg(txt)

        #1,2차 부합 시
        if con_fir == True and con_sec == True:
            return True
        else:
            return False

    except Exception as e:
        logger.debug(e)
        logger.debug(traceback.format_exc())




if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = Main()
    main.show()
    app.exec_()



