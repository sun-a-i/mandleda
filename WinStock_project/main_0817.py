import logging
import re
import socket
import sys
import tempfile
import threading

import pythoncom
from PyQt5.QtGui import QIcon, QMovie, QPixmap
from const import *

import traceback
import time

from PyQt5 import uic, QtGui
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QTableWidgetItem
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QThread

from logging.handlers import TimedRotatingFileHandler
import logging
import traceback
import os

if not os.path.exists('DATA'):
    os.makedirs('DATA')

if not os.path.exists('logFile'):
    os.makedirs('logFile')

import datetime as dt
from datetime import datetime

import winsound as sd
import pickle

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

main_class = uic.loadUiType('./ui/main.ui')[0]
start_class = uic.loadUiType('./ui/login.ui')[0]


register_class = uic.loadUiType('./ui/register.ui')[0]

kname_list = {}
code_list = {}

update_flag = False
key = {}  # ak = 이름, sk= 계좌정보
connection_flag = ''
update_p = 0
user_name = ''

stock_data_path = './DATA/stock_data.pickle'
stock_data_sub_path = './DATA/stock_data_sub.pickle'
div_stock_data_path = './DATA/div_stock_data.pickle'

# === stock data STATE stage ===
BUY = 1
OBSERVATION = 2

# === etc Hard Coding ===

MAX_BUY_LIMIT = 10000000  # 최대 매수 가능 금액
OBS_PER = 2.5  # 감시 퍼센티지
TRAIL_PER = -1.5  # 트레일링 퍼센티지
LOSS_PER = -4  # 손절 퍼센티지
""" 
===== stock data 파라미터 설명 =====
code : 종목코드
name : 종목명

pur_p : 매수 시 종목 가격
buy_amt : 체결누계금액
amount : 수량

avr_p : 평단가
high : 최고가

obs_per : 감시가 퍼센티지
obs_p : 감시가 도달 가격

trail_per : 트레일링 퍼센티지
trail_p : 트레일링 도달 가격

loss_per : 손절 퍼센티지
loss_p : 손절 도달 가격

STATE : 현재 상태 [BUY = 매수 직후 상태, OBSERVATION = 감시가 도달 상태(매도 대기)]
gubun : 조건식 별 매매 로직 설정

=== 추후 사용 ===
down_1_per : 1차 하락 퍼센티지
down_1_p : 1차 하락 도달가

down_2_per : 2차 하락 퍼센티지
down_2_p : 2차 하락 도달가

down_3_per : 3차 하락 퍼센티지
down_3_p : 3차 하락 도달가

===== div_stock_data 파라미터 설명 =====
5일간 보관
div_stock_data['code'] = { 
name:한글이름,  (편입시 업데이트)
fir_date : MM:dd (종목편입시 업데이트)
last_price : 전일종가 가격 (load시 업데이트)
avr_price : 평단가 (calljango 시 업데이트)
amt : 보유물량 (calljango 시 업데이트)
state : 현재상태 (감시중, 등록?, 1차매수, 2차매수, 3차매수)


종가 기준(load, 편입시 업데이트)
1차매수가격: -3% 보유금액의 7% 
2차매수가격: -11% 보유금액의 7%
3차매수가격: -20% (1차매수액+2차매수액) * 2/3
4차매수가격: -40% (1차매수액+2차매수액+3차매수액) * 2/3

익절
1차매도가격 : 1차매수시 입력 3%
2차매도가격 : 2차매수시 입력 5%
3차매도가격 : 3차매수시 입력 10%
4차매도가격 : 4차매수시 입력 10%

}
"""
#div_stock_data HARD CODING LIST
FIR_BUY_PERCENT = -3
SEC_BUY_PERCENT = -11
THIR_BUY_PERCENT = -20
FORTH_BUY_PERCENT = -40
FIR_INCOME_PERCENT = 3
SEC_INCOME_PERCENT = 5
THIR_INCOME_PERCENT = 10
FORTH_INCOME_PERCENT = 10

# 매매 데이터 저장 딕셔너리
stock_data = {}
div_stock_data = {}


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

                        key['ak'] = split_data[1]
                        key['sk'] = split_data[2]
                        key['time'] = split_data[3]
                        key['stage'] = split_data[4]
                        key['ver'] = split_data[5]
                        logger.debug("my_key = %s", key)
                        # 향후 업데이트 필요 시
                        """
                        file_list = os.listdir('./')
                        ver = 200

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

                        file_name = "TYANT_" + split_data[5][:1] + "." + split_data[5][1:] + ".exe"

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
                        else:
                            client_socket.sendall('ok'.encode())
                            connection_flag = 'ok'
                            break
                        """

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
            self.init_process()
            resp = {}
            resp['resp'] = 1
            self.init_read_data.emit(resp)
            time.sleep(0.25)

        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.information(self, "경고", "데이터 통신에 실패하였습니다. 프로그램을 다시 시작하여 주세요.")

    def init_process(self):
        try:
            global tickers
            pass
            # 과거 데이터 수집하기
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 담당자에게 문의주세요.')


# user_data
user_data = {}

# 자동매매 플래그
auto_flag = False

# 선택된 매매기법 플래그
CloseTradeMethod = 1
FellDownMethod = 2

trade_method = 0

#보유 현금 저장 변수
my_cash = 0
class Main(QDialog, main_class):  # param1 = windows : 창,  param2 = ui path

    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)

            # ==============키움==============================
            self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

            self.login = False  # 로그인 리시브 대기 변수
            self.condition = False  # 조건검색 리시브 대기 변수
            # self.auto_maemae = False  # 자동매매 변수

            self.con_list = {}

            self.recieved_dic = {}  # 실시간 종목별 금액 데이터 저장 딕셔너리
            self.recieved_dic_sub = {}  # 비교 딕셔너리

            self.jango = {}  # 계좌 귀속 데이터 저장 딕셔너리
            self.jango["종목리스트"] = []

            self.one_stock_data = ""
            self.one_stock_flag = False

            self.ocx.OnEventConnect.connect(self.OnEventConnect)
            self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
            self.ocx.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)
            self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
            self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)
            self.ocx.OnReceiveMsg.connect(self.OnReceiveMsg)
            self.ocx.OnReceiveChejanData.connect(self.OnReceiveChejanData)
            self.ocx.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)

            # init
            self.initial()

            # ===================UI=====================
            # self.pushButton.clicked.connect(self.order)#매수
            self.sell_btn.clicked.connect(self.order_sell)  # 매도
            # self.con_re.clicked.connect(self.condition_refresh)  # 직접갱신
            self.cbox_con.currentIndexChanged.connect(self.condition_refresh)
            self.trading_start_btn.clicked.connect(lambda: self.trading_state_func('start'))
            self.trading_stop_btn.clicked.connect(lambda: self.trading_state_func('stop'))
            self.buy_amount_edit.textChanged.connect(self.amount_change_function)
            self.account_list.currentIndexChanged.connect(self.accno_change_func)

            # cell 선택 시
            self.table_holding.cellClicked.connect(self.cell_cliked_func)



            # 쓰레드1
            self.mythread1 = MyThread()
            self.mythread1.finished.connect(self.price_comp_func)
            self.mythread1.start()



        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def initial(self):
        self.CommConnect()

        self.load_code()  # update_table보다 우선순위로 작동
        self.data_load()  # update_table보다 우선순위로 작동

        self.SetConditionSearchFlag()
        self.GetConditionLoad()  # 조건검색식 호출
        self.set_info()
        self.condition_refresh()


        self.update_con_table()
        self.update_div_table()
        self.update_holding_table()
        self.table_init()

    """
    @ 매매 시간 도달 프로세스
    @ 매수할 종목 있는지 체크 후 매수 프로세스 진행 
    """

    @pyqtSlot(str)
    def same_time_process(self):
        try:
            txt = "매매 시간 도달 : " + str(self.timeEdit.time().toString()[:5])
            logger.debug(txt)
            self.real_log_widget.addItem(txt)

            # todo - 검색식 확인 후 매수
            idx = str_format(self.cbox_con.currentText()[:3])

            if 'list' in self.con_list[idx]:  # 키 값 존재 확인
                if len(self.con_list[idx]['list']) > 0:  # 아이템 유무 확인
                    conList = list(self.con_list[idx]['list'].keys())
                    logger.debug("선택 조건식 리스트 : %s", conList)

                    accno = self.account_list.currentText()
                    code = conList[0]

                    buy_amount = str(self.buy_amount_edit.text()).replace(",", "")

                    # if int(buy_amount) > int(self.jango["출금가능금액"]):
                    #    self.real_log_widget.addItem("설정한 금액보다 보유 현금이 적으므로 보유금액에 맞추어 매수 진행")
                    #    logger.debug("설정한 금액보다 보유 현금이 적으므로 보유금액에 맞추어 매수 진행")
                    #    buy_amount = int(self.jango["출금가능금액"])

                    """
                    SendOrder(
                    BSTR sRQName,     // 사용자 >구분명
                    BSTR sScreenNo,   // 화면 번호
                    BSTR sAccNo,      // 계좌번호 10자리
                    LONG nOrderType,  // 주문 유형(1: 신규 매수, 2: 신규 매도 3: 매수 취소, 4: 매도 취소, 5: 매수 정정, 6: 매도 정정)
                    BSTR sCode,       // 종목 코드(6자리)
                    LONG nQty,        // 주문 수량
                    LONG nPrice,      // 주문 가격
                    BSTR sHogaGb,     // 거래 구분(시장가:03, 지정가:00, 시간외단일가:62, 장후시간외종가:81)
                    BSTR sOrgOrderNo  // 원주문 번호. 신규 주문에는 공백 입력, 정정/취소 시 입력합니다.
                    )
                    """
                    self.OPT10001(code)
                    while self.one_stock_flag is False:
                        pythoncom.PumpWaitingMessages()
                        time.sleep(1)

                    # 현재가
                    self.one_stock_data = self.one_stock_data.strip().lstrip('+').lstrip('-')
                    logger.debug("self.one_stock_data = %s", int(self.one_stock_data))
                    amt = int(int(buy_amount) / int(self.one_stock_data))

                    #                계좌,  주문유형,코드,  수량, 가격(시장가=0),  거래구분(시장가=03)
                    # SendOrder(self, accno, type, code, amount, price=0, HogaOrGubun='03')
                    ret = self.SendOrder(accno, '1', code, amt, 0, '03')
                    if ret == 0:
                        txt = "매수 주문 요청 성공"
                        logger.debug(txt)
                        self.real_log_widget.addItem(txt)
                        self.SetRealReg("0102", [code], "9001;10;16;17;302;", '0')
                        # !! 체잔데이터때 실시간 등록함 !

                        # 여기서 딕셔너리 key 생성, 전문 오는 곳에서는 key 없는 종목들은 거르도록...
                        # 안그러면 사용자가 매수한 종목도 키 값에 들어가는 에러 발생
                        if code not in stock_data.keys():
                            stock_data[code] = {}
                            stock_data[code]["현재가"] = 0

                    else:
                        txt = "매수 주문 요청 실패 오류코드 : " + str(ret)
                        logger.debug(txt)
                        self.real_log_widget.addItem(txt)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    """
    매매 데이터 load
    path : ./DATA/stock_data.pickle
    valiable : stock_data
    """

    def data_load(self):
        try:
            global stock_data, div_stock_data
            if not os.path.exists(stock_data_path):
                logger.debug("매매 데이터 없음")
            else:
                logger.debug("매매 데이터 있음. load")
                with open(stock_data_path, 'rb') as f:
                    stock_data = pickle.load(f)

                trade_list = list(stock_data.keys())
                self.SetRealReg("0102", trade_list, "9001;10;16;17;302;", '1')
                # 체잔데이터 받아올때 실시간 등록함 !!

                txt = ""
                for i in trade_list:
                    txt = txt + i

                txt = "매수한 종목 : " + txt
                self.real_log_widget.addItem(txt)

            if not os.path.exists(div_stock_data_path):
                logger.debug("분할 매매 데이터 없음")
            else:
                logger.debug("분할 매매 데이터 있음. load")
                logger.debug(div_stock_data)
                with open(div_stock_data_path, 'rb') as g:
                    div_stock_data = pickle.load(g)

                sub_dict = div_stock_data
                for j in sub_dict:
                    fd = datetime.strptime(sub_dict[j]["fir_date"], '%Y-%m-%d').date()
                    diff = datetime.now().date() - fd
                    diff = diff.days

                    #전일 종목 검색되어 아직 전일 종가를 모르는 상태
                    if diff > 0 and sub_dict[j]["state"] == "등록":
                        logger.debug('{}, 전일 등록 종목. "감시"로 상태 변경'.format(sub_dict[j]["name"]))
                        sub_dict[j]["last_price"] = self.GetMasterLastPrice(j)  ## day 1부터? 0부터 ?
                        time.sleep(0.2)
                        sub_dict[j]["1차매수가격"] = calc_next_price(sub_dict[j]["last_price"], FIR_BUY_PERCENT)
                        sub_dict[j]["2차매수가격"] = calc_next_price(sub_dict[j]["last_price"], SEC_BUY_PERCENT)
                        sub_dict[j]["3차매수가격"] = calc_next_price(sub_dict[j]["last_price"], THIR_BUY_PERCENT)
                        sub_dict[j]["4차매수가격"] = calc_next_price(sub_dict[j]["last_price"], FORTH_BUY_PERCENT)
                        sub_dict[j]["state"] = "감시중"

                    elif diff > 5 and sub_dict[j]["state"] == "감시중":  # 감시중인 종목 5일이 넘으면 삭제
                        logger.debug("{} 종목, 감시 이후 5일 경과, 파일 삭제".format(sub_dict[j]["name"]))
                        del sub_dict[j]

                div_stock_data = sub_dict
                self.save_div_data_func()

                div_trade_list = list(div_stock_data.keys())
                self.SetRealReg("0103", div_trade_list, "9001;10;", '1')

                txt = ""
                for i in div_trade_list:
                    txt = txt + i

                txt = "분할 매매 종목 : " + txt
                self.real_log_widget.addItem(txt)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    """
    매매 데이터 저장
    """
    def save_data_func(self):
        with open(stock_data_path, 'wb') as f:
            pickle.dump(stock_data, f)

        with open(stock_data_sub_path, 'wb') as f:
            pickle.dump(stock_data, f)

    def save_div_data_func(self):
        with open(div_stock_data_path, 'wb') as f:
            pickle.dump(div_stock_data, f)

    """
    table의 width 조정 외 기타 init
    """
    def table_init(self):
        try:
            logger.debug('table init..')
            table = self.table_holding
            table.setColumnWidth(0, 60)
            table.setColumnWidth(1, 120)
            table.setColumnWidth(2, 80)
            table.setColumnWidth(3, 60)
            table.setColumnWidth(4, 80)
            table.setColumnWidth(5, 60)

            table = self.table_con
            table.setColumnWidth(0, 60)
            table.setColumnWidth(1, 130)
            table.setColumnWidth(4, 60)

            table = self.table_div
            table.setColumnWidth(0, 60)
            table.setColumnWidth(1, 100)
            table.setColumnWidth(2, 80)
            table.setColumnWidth(3, 80)
            table.setColumnWidth(4, 80)
            table.setColumnWidth(5, 60)
            table.setColumnWidth(6, 60)
            table.setColumnWidth(7, 100)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def trading_state_func(self, state):
        try:
            global auto_flag, trade_method
            logger.debug("trading_state_func : %s", state)

            if state == 'start':

                if self.closeBuy_rdo_btn.isChecked():
                    trade_method = CloseTradeMethod
                    txt = "[종가매매 기법]"

                    # 시간 체크 쓰레드, 종가매매일 때만 필요한 쓰레드
                    self.timer_thread = TimerThread()
                    self.timer_thread.time_flag.connect(self.same_time_process)
                    self.timer_thread.start()

                elif self.fellDown_rdo_btn.isChecked():
                    trade_method = FellDownMethod
                    txt = "[하락매수 기법]"
                else:
                    txt = '매매기법 선택 안됨'

                reply = QMessageBox.question(self, '확인', txt + '으로 자동매매를 시작 하시겠습니까?')
                if reply == QMessageBox.Yes:

                    auto_flag = True
                    self.trading_start_btn.setEnabled(False)
                    self.trading_start_btn.setStyleSheet("color:gray")

                    self.trading_stop_btn.setEnabled(True)
                    self.trading_stop_btn.setStyleSheet("color:white")
                    self.trading_stop_btn.setStyleSheet("background:blue")

                    # 자동매매 시작 버튼 클릭시 옵션값 변경 못하도록 변경
                    self.timeEdit.setEnabled(False)
                    self.buy_amount_edit.setEnabled(False)
                    self.order_amount_4.setEnabled(False)
                    self.closeBuy_rdo_btn.setEnabled(False)
                    self.fellDown_rdo_btn.setEnabled(False)
                    self.cbox_con.setEnabled(False)

                    if trade_method == CloseTradeMethod:
                        txt = "종가매매로 시작 : " + self.timeEdit.time().toString()[:5] + ", 매수금 : " + self.buy_amount_edit.text()
                    elif trade_method == FellDownMethod:
                        txt = "하락매수로 시작 : " + self.timeEdit.time().toString()[:5]

                    self.real_log_widget.addItem(txt)
                    logger.debug(txt)
                else:
                    # 선택안할 시 다시 0으로 설정
                    trade_method = 0

            else:
                trade_method = 0
                auto_flag = False
                self.trading_start_btn.setEnabled(True)
                self.trading_start_btn.setStyleSheet("color:white")
                self.trading_start_btn.setStyleSheet("background:red")
                self.trading_stop_btn.setEnabled(False)
                self.trading_stop_btn.setStyleSheet("color:gray")

                # 자동매매 중지 버튼 클릭시 옵션값 변경 가능하도록 변경
                self.timeEdit.setEnabled(True)
                self.buy_amount_edit.setEnabled(True)
                self.order_amount_4.setEnabled(True)
                self.closeBuy_rdo_btn.setEnabled(True)
                self.fellDown_rdo_btn.setEnabled(True)
                self.cbox_con.setEnabled(True)

                txt = "자동매매 중단 : " + self.timeEdit.time().toString()[:5]
                self.real_log_widget.addItem(txt)
                logger.debug(txt)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def condition_refresh(self):
        try:
            if self.cbox_con.currentText() != "":
                logger.debug("조건검색식 종목 호출")
                logger.debug(self.cbox_con.currentText())
                logger.debug(self.con_list)
                con_txt = self.cbox_con.currentText()[:3]

                if str(con_txt).isdigit():
                    self.SendCondition(con_txt)
                    self.SendConditionStopExcept(con_txt)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def load_code(self):
        try:
            global kname_list, code_list
            # 종목코드 불러오기
            kospi_code_list = self.GetCodeListByMarket("0")
            if len(kospi_code_list) > 0:
                for i in kospi_code_list:  # 006950 : 삼성전자
                    kname_list.update({i: self.GetMasterCodeName(i)})
                    code_list.update({self.GetMasterCodeName(i): i})
            time.sleep(1)

            kosdak_code_list = self.GetCodeListByMarket('10')
            if len(kosdak_code_list) > 0:
                for i in kosdak_code_list:
                    kname_list.update({i: self.GetMasterCodeName(i)})
                    code_list.update({self.GetMasterCodeName(i): i})

            logger.debug("kospi = %s, kosdak = %s, \n\nkname_list = %s,\n\ncode_list = %s", len(kospi_code_list),
                         len(kosdak_code_list),
                         kname_list, code_list)

            # logger.debug(kname_list)
            self.real_log_widget.addItem('로그인 성공')
            self.real_log_widget.addItem('프로그램 시작')
            time.sleep(1)
        except Exception as e:
            logger.debug("except")
            logger.debug(traceback.format_exc())

    # ===================================키움 api======================================
    # ==============================로그인 관련 함수 ========================
    def CommConnect(self):
        logger.debug("로그인 요청")
        try:
            logger.debug("로그인 요청 진행중..")
            self.ocx.dynamicCall("CommConnect()")
            logger.debug("로그인 요청 대기중...")
            while self.login is False:
                pythoncom.PumpWaitingMessages()
                time.sleep(1)
        except Exception as e:
            logger.debug("로그인 예외처리 발생")
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnEventConnect(self, code):
        logger.debug("로그인 서버 메세지 수신발생")
        if code == 0:
            self.login = True
            logger.debug("로그인 완료")
        else:
            logger.debug("로그인 에러 에러코드 :" + str(code))

    # ======기타 요청 함수==========
    def GetLoginInfo(self, tag):
        ret = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def GetMasterCodeName(self, code):
        ret = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return ret

    def GetMasterLastPrice(self, code):
        ret = self.ocx.dynamicCall("GetMasterLastPrice(QString)", code)
        return ret

    def GetCodeListByMarket(self, market):
        ret = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market)
        codes = ret.split(';')[:-1]
        return codes

    # ============== 조건검색 관련 함수 =============

    def GetConditionLoad(self):  # 조건검색 목록 (이름, 번호 )요청 함수
        self.condition = False
        try:
            logger.debug("조건검색 목록 호출")
            er = self.ocx.dynamicCall("GetConditionLoad()")
            if er:
                logger.debug("조건검색 목록 호출 성공")
                while self.condition is False:
                    pythoncom.PumpWaitingMessages()
                self.condition = False
            else:
                logger.debug("조건검색 목록 호출 실패")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveConditionVer(self):  # 이게 호출
        try:

            self.condition = True
            logger.debug("조건검색 목록 수신 이벤트")
            self.con_list = {}
            con_str = self.ocx.dynamicCall("GetConditionNameList()").split(";")[:-1]

            logger.debug("con_str = %s", con_str)
            if con_str == []:
                logger.debug("조건검색 조건이 없음!")
            else:
                for i in con_str:
                    i = i.split("^")
                    self.con_list[i[0]] = {}  # con_list["000"] = {}
                    self.con_list[i[0]]["name"] = i[1]  # con_list["000"]["name"] = "1번조건식"
                    self.con_list[i[0]]["list"] = []

                logger.debug("수집된 조건식 : " + str(self.con_list))
            logger.debug("조건검색 목록 호출 완료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def SendCondition(self, key):  # 조건식에 맞는 코드 요청 함수
        self.condition = False
        try:
            logger.debug(str(key) + " 조건식 조회 요청")
            er = self.ocx.dynamicCall("SendCondition(QString,QString,QInt,QInt)", "0156",
                                      self.con_list[key]["name"], key, 1)  # 실시간옵션. 0:조건검색만, 1:조건검색+실시간 조건검색
            if er:
                logger.debug(str(key) + " 조건식 조회 요청 성공")
                while self.condition is False:
                    pythoncom.PumpWaitingMessages()
                self.condition = False
            else:
                logger.debug(str(key) + " 조건식 조회 요청 실패")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def SendConditionStopExcept(self, index):  # 현재 인덱스 제외하고 나머지 실시간 조건검색 해제
        try:
            for i in self.con_list:
                if index != i:
                    self.ocx.dynamicCall("SendConditionStop(QString,QString,QInt)", "0156",
                                         self.con_list[i]["name"], i)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveTrCondition(self, screennomb, codelist, conname, idx, next):  # 조건검색 후 받아오는 이벤트
        self.condition = True
        try:
            idx = str_format(idx)
            logger.debug("조건식 조회 수신 이벤트")
            logger.debug("조건식 이름: " + conname + ", 조건식 인덱스 : " + idx)

            tmp = codelist.split(";")[:-1]
            ret = {}
            for i in tmp:
                kv = i.split("^")
                if len(kv[0]) == 6:
                    ret[kv[0]] = kv[1].lstrip("0")
                else:
                    logger.debug("종목코드 자리수 오류", kv[0], kv[1])
            # logger.debug(ret)
            self.con_list[idx]["list"] = ret
            logger.debug("조건식 이름: " + conname + ", 조건식 인덱스 : " + idx + ", 조건검색 업데이트 완료")
            logger.debug(str(self.con_list))
            self.update_con_table()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveRealCondition(self, code, etype, con_name, con_idx):  # 테스트 중 # 조건검색 변동 이벤트 함수
        global div_stock_data, trade_method, kname_list

        #logger.debug("OnReceiveRealCondition 조건검색 변동 이벤트 발생 : %s %s %s %s ", code, etype, con_name, con_idx)
        try:
            if str_format(con_idx) == str(self.cbox_con.currentText()[:3]):
                if etype == 'I':  # 종목편입
                    # logger.debug(code + "종목 편입 이벤트 발생")
                    self.con_list[str_format(con_idx)]["list"][code] = "0"
                    sd.Beep(400, 200)
                    sd.Beep(480, 300)
                    if trade_method == FellDownMethod:
                        if code not in div_stock_data:
                            div_stock_data[code] = {}
                            div_stock_data[code]["name"] = kname_list[code]
                            div_stock_data[code]["fir_date"] = str(datetime.today().date())

                            # 종목이 검색된 다음날, 전일 종가를 설정
                            div_stock_data[code]["last_price"] = 0
                            div_stock_data[code]["avr_price"] = 0
                            div_stock_data[code]["amt"] = 0

                            div_stock_data[code]["1차매수가격"] = 0
                            div_stock_data[code]["2차매수가격"] = 0
                            div_stock_data[code]["3차매수가격"] = 0
                            div_stock_data[code]["4차매수가격"] = 0

                            div_stock_data[code]["1차매도가격"] = 999999999
                            div_stock_data[code]["2차매도가격"] = 999999999
                            div_stock_data[code]["3차매도가격"] = 999999999
                            div_stock_data[code]["4차매도가격"] = 999999999
                            div_stock_data[code]["state"] = "등록"
                            div_stock_data[code]["현재가"] = 0
                            logger.debug("하락매수 - 종목 검색됨")
                            logger.debug("name : {}, data : {}".format(kname_list[code], div_stock_data[code]))
                            self.save_div_data_func()
                            self.SetRealReg("0103", [code], "9001;10", '1')

                elif etype == 'D':  # 종목이탈
                    # logger.debug(code + "종목 이탈 이벤트 발생")
                    # logger.debug("%s", self.con_list)
                    del self.con_list[str_format(con_idx)]["list"][code]
                    # self.SetRealRemove("0101", code)
                else:
                    logger.debug("이건 뭐지 ? OnReceiveRealCondition")

                self.update_con_table()
            else:
                # logger.debug("현재 설정한 조건검색과 다른 변동 이벤트 무시 %s", con_idx)
                # self.SetRealRemove(ALL, code)
                pass
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    # ==========================TR 관련 함수==============================

    def SetInputValue(self, id, value):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def CommRqData(self, rqname, trcode, next, screen):
        return self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen)

    def GetCommData(self, trcode, rqname, index, item):
        data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item)
        return data.strip()

    def GetTRCount(self, trcode, rqname):
        return self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

    def Calljango(self, accno):  # 잔고 요청
        logger.debug("잔고요청 전송됨")
        try:
            self.SetInputValue("계좌번호", accno)
            self.SetInputValue("비밀번호", "")
            self.SetInputValue("비밀번호입력매체구분", "00")

            ret = self.CommRqData("잔고요청", "opw00005", "0", "0101")
            if ret != 0:
                logger.debug("잔고 조회 오류코드 : %s", ret)
            else:
                logger.debug("잔고요청 성공")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveTrData(self, screen, rcname, trcode, record, next):  # tr 수신 이벤트
        global div_stock_data
        logger.debug("OnReceiveTrData %s, %s, %s, %s, %s", screen, rcname, trcode, record, next)
        try:
            if next == "2":
                logger.debug("데이터 더 있음 !! 요청 이름 : " + str(rcname))

            # logger.debug(screen, rcname, trcode, record, next)
            # name = self.GetCommData(trcode, rcname, 0, "종목명")\
            # price = self.GetCommData(trcode, rcname, 0, "현재가")

            if rcname == "잔고요청": #Calljango()
                logger.debug("잔고요청 수신 발생")
                self.jango["예수금"] = self.GetCommData("opw00005", "잔고요청", 0, "예수금").lstrip("0")
                self.jango["예수금D+1"] = self.GetCommData("opw00005", "잔고요청", 0, "예수금D+1").lstrip("0")
                self.jango["예수금D+2"] = self.GetCommData("opw00005", "잔고요청", 0, "예수금D+2").lstrip("0")
                self.jango["출금가능금액"] = self.GetCommData("opw00005", "잔고요청", 0, "출금가능금액").lstrip("0")
                self.jango["미수확보금"] = self.GetCommData("opw00005", "잔고요청", 0, "미수확보금").lstrip("0")
                self.jango["현금미수금"] = self.GetCommData("opw00005", "잔고요청", 0, "현금미수금").lstrip("0")
                self.jango["주식매수총액"] = self.GetCommData("opw00005", "잔고요청", 0, "주식매수총액").lstrip("0")
                self.jango["증거금현금"] = self.GetCommData("opw00005", "잔고요청", 0, "증거금현금").lstrip("0")
                self.jango["평가금액합계"] = self.GetCommData("opw00005", "잔고요청", 0, "평가금액합계").lstrip("0")
                self.jango["총손익합계"] = self.GetCommData("opw00005", "잔고요청", 0, "총손익합계").lstrip("0")
                self.jango["총손익률"] = self.GetCommData("opw00005", "잔고요청", 0, "총손익률").lstrip("0")
                logger.debug(self.jango)
                # ====멀티tr====
                self.jango["종목리스트"] = []
                for i in range(self.GetTRCount("opw00005", "잔고요청")):
                    tmp = {}
                    tmp["종목코드"] = self.GetCommData("opw00005", "잔고요청", i, "종목번호").lstrip("0")[1:]  # A123455->123455
                    tmp["종목이름"] = self.GetCommData("opw00005", "잔고요청", i, "종목명").lstrip("0")
                    tmp["현재가"] = self.GetCommData("opw00005", "잔고요청", i, "현재가").lstrip("0")
                    tmp["매입금액"] = self.GetCommData("opw00005", "잔고요청", i, "매입금액").lstrip("0")
                    tmp["결제잔고"] = self.GetCommData("opw00005", "잔고요청", i, "결제잔고").lstrip("0")
                    tmp["보유수량"] = self.GetCommData("opw00005", "잔고요청", i, "현재잔고").lstrip("0")  # 보유수량
                    tmp["매입단가"] = self.GetCommData("opw00005", "잔고요청", i, "매입단가").lstrip("0")
                    tmp["매입금액"] = self.GetCommData("opw00005", "잔고요청", i, "매입금액").lstrip("0")
                    tmp["평가금액"] = self.GetCommData("opw00005", "잔고요청", i, "평가금액").lstrip("0")
                    tmp["평가손익"] = self.GetCommData("opw00005", "잔고요청", i, "평가손익").lstrip("0")
                    self.jango["종목리스트"].append(tmp)
                    # print(tmp)
                    if tmp["종목코드"] in div_stock_data:
                        div_stock_data[tmp["종목코드"]]["현재가"] = tmp["현재가"]
                        div_stock_data[tmp["종목코드"]]["amt"] = tmp["보유수량"]
                        div_stock_data[tmp["종목코드"]]["avr_price"] = tmp["매입단가"]
                        div_stock_data[tmp["종목코드"]]["매입금액"] = tmp["매입금액"]

                logger.debug(self.jango["종목리스트"])

                tmp_list = []
                for j in self.jango["종목리스트"]:
                    tmp_list.append(j["종목코드"])
                self.SetRealReg("0102", tmp_list, "9001;10;16;17;302;", '0')

                self.update_jango()
                self.update_div_table()
                logger.debug('1')
                self.update_holding_table()
                logger.debug("잔고요청 업데이트 완료")

            elif rcname == "order":
                # print(screen, rcname, trcode, record, next)#debug 메세지 에러
                # update jango?
                pass

            elif rcname == "OPT10001":
                self.one_stock_data = self.GetCommData(trcode, record, 0, "현재가")
                self.one_stock_flag = True
                logger.debug("one stock data = %s", self.one_stock_data)
                pass
            else:
                logger.debug("이 수신 데이터는 ?")
                logger.debug("%s %s %s %s %s", screen, rcname, trcode, record, next)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    """
    def GetPrice(self,code):
        self.SetInputValue("종목코드", code)
        self.CommRqData("myrequest", "opt10001", 0, "0101")#ONrecieveTrdata 안에서 써야함
        return self.GetCommData(code, "myrequest", 0, "현재가")
    """

    # =======================실시간 관련 함수===========================

    """
    스크린 넘버
    0101 : 조건검색의 실시간 # 현재는 쓰지 않음
    0102 : 잔고 데이터의 실시간
    0103 : 분할매수의 실시간
    """

    def SetRealReg(self, screen, codelist, FID_list, type):  # codelist : list
        try:
            global kname_list

            for i in codelist:
                if i in kname_list:
                    logger.debug("%s 종목 실시간 등록", kname_list[i])

            # logger.debug(codelist)
            if type == "0":  # 체잔데이터 이벤트때 등록
                logger.debug("보유주식목록 실시간 등록")
            elif type == "1":  # 종목편입 이벤트때 추가등록
                logger.debug(str(codelist) + " 종목 실시간 추가 등록")
            codelist = ";".join(codelist)

            logger.debug(codelist)
            self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                                 screen, codelist, FID_list, type)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OPT10001(self, code):
        self.SetInputValue("종목코드", code)
        self.CommRqData("OPT10001", "OPT10001", 0, "0101")

        # return self.kiwoom.ret_data['OPT10001']

    def GetCommRealData(self, code, fid):
        try:
            data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
            return data
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveRealData(self, code, realtype, realdata):  # 스레드로 스트림 데이터 처리
        try:
            price = self.GetCommRealData(code, 10)
            if len(price) != 0:
                self.recieved_dic[code] = int_format(price)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def DisconnectRealData(self, screen):
        try:
            self.ocx.dynamicCall("DisconnectRealData(QString)", screen)
            logger.debug("실시간 구독해지됨")
            self.recieved_dic = {}

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    # =======================주문 관련 함수===========================

    # (self, rqname, screen_no, order_type, code, order_quantity, order_price, gubun, origin_order_number=""):
    def SendOrder(self, accno, type, code, amount, price=0, HogaOrGubun='00'):  # 시장가 매매 TR
        try:
            logger.debug("send order, type:%s, code:%s, amount:%s, price:%s, HoG:%s", type, code, amount, price,
                         HogaOrGubun)
            return self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int   , int, QString, QString)",
                ["order", "0101", accno, type, code, amount, price, HogaOrGubun, ""])
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg):
        try:
            logger.debug("OnReceiveMsg %s, %s, %s, %s", sScrNo, sRQName, sTrCode, sMsg)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    """
    gubun : 0 - 주문접수 | 주문체결, 1 - 잔고 내 데이터 변동
    nItemCnt
    FidList
    """

    def OnReceiveChejanData(self, s_gubun, nItemCnt, s_fid_list):
        try:
            global stock_data, kname_list
            logger.debug("OnReceiveChejanData is called {} / {} / {}".format(s_gubun, nItemCnt, s_fid_list))

            code = ""
            dummy = {}
            for fid in s_fid_list.split(";"):
                if fid in FID_CODES:
                    code = self.GetChejanData('9001')[1:]
                    data = self.GetChejanData(str(fid))
                    data = data.strip().lstrip('+').lstrip('-')
                    if data.isdigit():
                        data = int(data)
                    item_name = FID_CODES[fid]
                    logger.debug("{}: {}".format(item_name, data))
                    if code not in dummy.keys():
                        dummy[code] = {}
                    dummy[code].update({item_name: data})
                    """
                    === 로그 기록 예시 === #FID 변환됨
                    계좌번호: 8011111111
                    주문번호: 195410
                    관리자사번:
                    종목코드: A007700
                    주문업무분류: JJ
                    주문상태: 체결
                    종목명: F&F홀딩스
                    주문수량: 1
                    주문가격: 37600
                    미체결수량: 0
                    체결누계금액: 37500
                    원주문번호: 0
                    주문구분: 매수
                    매매구분: 보통
                    매도수구분: 2
                    주문시간: 151124
                    체결번호: 1423924
                    체결가: 37500
                    체결량: 1
                    현재가: 37500
                    (최우선)매도호가: 37500
                    (최우선)매수호가: 37450
                    단위체결가: 37500
                    단위체결량: 1
                    당일매매 수수료: 130
                    당일매매세금: 0
                    """

            if s_gubun == '0':
                pass

            elif s_gubun == '1':  # 국내주식 잔고변경
                if str(self.GetChejanData("946")) == "2":
                    tmp = "매수"
                elif str(self.GetChejanData("946")) == "1":
                    tmp = "매도"

                txt = str(self.GetChejanData("9001")[1:]) + str(
                    self.GetChejanData("302").strip() + " : " + tmp + " 주문 성공 ")
                logger.debug(txt)
                self.real_log_widget.addItem(txt)

                self.Calljango(self.account_list.currentText())
                pass

            elif s_gubun == '4':  # 파생잔고변경
                pass

            if (dummy[code]['매도수구분'] == 2) & (dummy[code]['주문상태'] == '체결'):  # 1:매도, 2:매수
                if code in stock_data.keys():
                    stock_data[code].update({'code': code})  # 종목코드
                    stock_data[code].update({'name': dummy[code]['종목명']})  # 종목명

                    stock_data[code].update({'pur_p': dummy[code]['체결가']})
                    stock_data[code].update({'buy_amt': dummy[code]['체결누계금액']})
                    stock_data[code].update({'amount': dummy[code]['체결량']})

                    stock_data[code].update({'high': dummy[code]['체결가']})  # 매수 당시 가격으로 최고가 지정

                    stock_data[code].update({'obs_per': OBS_PER})  # 감시 퍼센티지
                    res = calc_next_price(dummy[code]['체결가'], OBS_PER)
                    stock_data[code].update({'obs_p': res})  # 감시가 저장
                    stock_data[code].update({'trail_per': TRAIL_PER})  # 트레일링 퍼센티지 설정
                    stock_data[code].update({'trail_p': 0})  # 트레일링 도달가는 미지정

                    stock_data[code].update({'loss_per': LOSS_PER})  # 트레일링 퍼센티지 설정
                    res = calc_next_price(dummy[code]['체결가'], LOSS_PER)
                    stock_data[code].update({'loss_p': res})  # 트레일링 도달가는 미지정

                    stock_data[code].update({'STATE': BUY})  # 현재 상태 [매수됨] 으로 변경

                    self.save_data_func()  # 데이터 저장
                    logger.debug("stock data : %s", stock_data)

                elif code in div_stock_data.keys():
                    self.Calljango(self.account_list.currentText())  # Calljango update : amt, avr_price
                    # todo - state가 1차매수 ~ 4차매수 변경되는 타이밍 ? onreceive 타이밍에 맞게 진행돼야함 ?
                    if div_stock_data[code]["state"] == "등록":
                        pass
                    elif div_stock_data[code]["state"] == "감시중":
                        pass
                    elif div_stock_data[code]["state"] == "1차매수":
                        div_stock_data[code]["1차매도가격"] = calc_next_price(div_stock_data[code][avr_price],
                                                                         FIR_INCOME_PERCENT)
                    elif div_stock_data[code]["state"] == "2차매수":
                        div_stock_data[code]["2차매도가격"] = calc_next_price(div_stock_data[code][avr_price],
                                                                         SEC_INCOME_PERCENT)
                    elif div_stock_data[code]["state"] == "3차매수":
                        div_stock_data[code]["3차매도가격"] = calc_next_price(div_stock_data[code][avr_price],
                                                                         THIR_INCOME_PERCENT)
                    elif div_stock_data[code]["state"] == "4차매수":
                        div_stock_data[code]["4차매도가격"] = calc_next_price(div_stock_data[code][avr_price],
                                                                         FORTH_INCOME_PERCENT)
                    else:
                        logger.debug("체잔 데이터 분류 에러 div stock data : %s", div_stock_data)

                    self.save_div_data_func()
                    logger.debug("div stock data : %s", div_stock_data)

            #매수매도되어 잔고 변경 -> 잔고요청하여 업데이트
            self.Calljango(self.account_list.currentText())

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def GetChejanData(self, nFid):
        try:
            ret = self.ocx.dynamicCall("GetChejanData(int)", nFid)
            return ret
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    # ==========KOA_Function() 함수======

    def SetConditionSearchFlag(self):  # 조건검색에 결과에 현재가 포함으로 설정
        try:
            self.ocx.dynamicCall("KOA_Functions(QString, QString)", "SetConditionSearchFlag", "AddPrice")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    # ==============기타 함수==================

    # ==========================================UI FUNCTION ====================================================
    # ==========================================================================================================
    # ==========================================================================================================
    # ==========================================================================================================

    """
    -매수금 가능 금액 제한 함수
    -MAX_BUY_LIMIT 하드코딩
    """

    def amount_change_function(self):
        try:
            val = self.buy_amount_edit.text()
            val = val.replace(",", "")

            if int(val) > MAX_BUY_LIMIT:
                format_max_buy_limit = format(int(MAX_BUY_LIMIT), ",")
                txt = format_max_buy_limit + "만원 이상 매수할 수 없습니다."
                QMessageBox.information(self, '확인', txt)
                self.buy_amount_edit.setText(format_max_buy_limit)
            elif val.isdigit():
                format_val = format(int(val), ",")
                self.buy_amount_edit.setText(str(format_val))

        except ValueError as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    """
    cell selected fuction
    """

    def cell_cliked_func(self):
        try:
            num = self.table_holding.currentRow()
            select_code = self.table_holding.item(num, 0).text()

            self.view_selec_coin_lbl.setText(select_code)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def accno_change_func(self):
        try:
            self.Calljango(self.account_list.currentText())
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def set_info(self):
        try:
            global user_data, key, login_flag

            account_cnt = self.GetLoginInfo("ACCOUNT_CNT")
            account_list = self.GetLoginInfo("ACCLIST").split(';')[:-1]
            user_id = self.GetLoginInfo("USER_ID")
            user_name = self.GetLoginInfo("USER_NAME")
            sever = self.GetLoginInfo("GetServerGubun")
            self.name.setText(user_name)  # 이름 설정
            for i in account_list:
                self.account_list.addItem(i)  # 계좌 목록

            for i in self.con_list:
                self.cbox_con.addItem(i + " " + self.con_list[i]["name"])  # 조건검색 목록

            # 유저 정보 저장
            account_list_re = []
            global test
            if not test:
                for i in range(len(account_list)):
                    account_list_re.append(account_list[i][:-2])

                user_data[user_name] = account_list_re

                logger.debug("기본 데이터 수집 완료 계좌 수 : %s, 계좌 번호 %s,  유저 아이디 : %s, 유저 이름 %s, %s",
                             account_cnt,
                             account_list,
                             user_id,
                             user_name,
                             sever)

                logger.debug("%s %s", key['ak'], key['sk'])
                logger.debug("%s %s", user_data.keys(), user_data.values())
                if key['ak'] in user_data.keys():
                    if key['sk'] in user_data[key['ak']]:
                        logger.debug("name, account 인증 완료, 로그인 성공")

                        login_flag = True
                        self.close()
                    else:
                        logger.debug("등록된 계좌와 서버 저장계좌가 다름, 로그인 실패")
                        QMessageBox.information(self, '확인', '등록된 회원이나, 계좌정보가 다릅니다.\n실 사용자만 등록 후 사용 가능합니다.')
                        self.close()
                else:
                    logger.debug("user name 과 서버 name 다름, 로그인 실패")
                    QMessageBox.information(self, '확인', '등록된 회원이나, 이름이 다릅니다.\n실 사용자만 등록 후 사용 가능합니다.')
                    self.close()

            self.Calljango(self.account_list.currentText())
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    @pyqtSlot(str)
    def price_comp_func(self, stock_code):
        try:
            global stock_data, kname_list, trade_method
            stock_sub = stock_data
            # logger.debug("차이발생")

            if trade_method == CloseTradeMethod:
                if (len(stock_code) >= 1) & (len(stock_data) >= 1):
                    price = self.recieved_dic[stock_code]
                    code = stock_code
                    if stock_code in stock_sub:
                        logger.debug("매매 종목 내 가격 변동 생성 : %s, %s", kname_list[code], price)

                        # 현 상태 BUY
                        if stock_data[code]['STATE'] == BUY:
                            # 감시가 도달
                            if int(stock_data[code]['obs_p']) <= int(price):
                                logger.debug("%s 종목 감시가 도달 : %s", code, price)
                                txt = code + " 종목 감시가 도달, " + str(price)
                                self.real_log_widget.addItem(txt)

                                # 트레일링가 계산
                                res = calc_next_price(price, TRAIL_PER)
                                stock_data[code]['trail_p'] = res
                                stock_data[code]['STATE'] = OBSERVATION  # 감시가 도달 상태로 변경

                                # 데이터 저장
                                self.save_data_func()

                            # 손절가 도달
                            elif int(stock_data[code]['obs_p']) < int(price):
                                logger.debug("%s 종목 손절가 도달 : %s", code, price)

                                # todo - sell
                                accno = self.account_list.currentText()
                                code = code
                                amt = stock_data[code]['amount']

                                # SendOrder(
                                # BSTR sRQName,     // 사용자 >구분명
                                # BSTR sScreenNo,   // 화면 번호
                                # BSTR sAccNo,      // 계좌번호 10자리
                                # LONG nOrderType,  // 주문 유형(1: 신규 매수, 2: 신규 매도 3: 매수 취소, 4: 매도 취소, 5: 매수 정정, 6: 매도 정정)
                                # BSTR sCode,       // 종목 코드(6자리)
                                # LONG nQty,        // 주문 수량
                                # LONG nPrice,      // 주문 가격
                                # BSTR sHogaGb,     // 거래 구분(시장가:03, 지정가:00, 시간외단일가:62, 장후시간외종가:81)
                                # BSTR sOrgOrderNo  // 원주문 번호. 신규 주문에는 공백 입력, 정정/취소 시 입력합니다.
                                # )

                                #                계좌,  주문유형,코드,  수량,     가격,       거래구분
                                # SendOrder(self, accno, type, code, amount, price=0, HogaOrGubun='00')
                                ret = self.SendOrder(accno, '2', code, amt, 0, '03')
                                if ret == 0:
                                    txt = "종목 손절가 도달, 매도 진행"
                                    logger.debug(txt)
                                    self.real_log_widget.addItem(txt)

                                else:
                                    txt = "종목 손절가 도달, 매도 요청 실패 오류코드 : " + str(ret)
                                    logger.debug(txt)
                                    self.real_log_widget.addItem(txt)

                                # todo - stock_data 에서 pop
                                self.stock_data.pop(code)
                                # 데이터 저장
                                self.save_data_func()

                                # 데이터 저장
                                self.save_data_func()

                        # 현 상태 OBSERVATION
                        elif stock_data[code]['STATE'] == OBSERVATION:
                            # 최고가 갱신
                            if stock_data[code]['high'] < price:
                                logger.debug("%s 종목 감시가 도달 : %s->%s", stock_data[code]['high'], price)
                                stock_data[code]['high'] = price
                                txt = code + " 종목 최고가 갱신, " + str(stock_data[code]['high']) + "->" + str(price)
                                self.real_log_widget.addItem(txt)

                                # 트레일링가 재계산
                                res = calc_next_price(price, TRAIL_PER)
                                stock_data[code]['trail_p'] = res

                                # 데이터 저장
                                self.save_data_func()

                            # 트레일링가 도달
                            elif stock_data[code]['trail_p'] > price:
                                logger.debug("%s 종목 트레일링가 도달 : %s", code, stock_data[code]['trail_p'])
                                # 매도 진행
                                txt = code + " 종목 트레일링 실현"
                                self.real_log_widget.addItem(txt)

                                # todo - sell
                                accno = self.account_list.currentText()
                                code = code
                                amt = stock_data[code]['amount']

                                # SendOrder(
                                # BSTR sRQName,     // 사용자 >구분명
                                # BSTR sScreenNo,   // 화면 번호
                                # BSTR sAccNo,      // 계좌번호 10자리
                                # LONG nOrderType,  // 주문 유형(1: 신규 매수, 2: 신규 매도 3: 매수 취소, 4: 매도 취소, 5: 매수 정정, 6: 매도 정정)
                                # BSTR sCode,       // 종목 코드(6자리)
                                # LONG nQty,        // 주문 수량
                                # LONG nPrice,      // 주문 가격
                                # BSTR sHogaGb,     // 거래 구분(시장가:03, 지정가:00, 시간외단일가:62, 장후시간외종가:81)
                                # BSTR sOrgOrderNo  // 원주문 번호. 신규 주문에는 공백 입력, 정정/취소 시 입력합니다.
                                # )

                                #                계좌,  주문유형,코드,  수량,     가격,       거래구분
                                # SendOrder(self, accno, type, code, amount, price=0, HogaOrGubun='00')
                                ret = self.SendOrder(accno, '2', code, amt, 0, '03')
                                if ret == 0:
                                    txt = "트레일링 매도 완료"
                                    logger.debug(txt)
                                    self.real_log_widget.addItem(txt)

                                else:
                                    txt = "트레일링 매도 완료 요청 실패 오류코드 : " + str(ret)
                                    logger.debug(txt)
                                    self.real_log_widget.addItem(txt)

                                # todo - stock_data 에서 pop
                                self.stock_data.pop(code)
                                # 데이터 저장
                                self.save_data_func()
                        self.update_holding_table()

            elif trade_method == FellDownMethod:
                if (len(stock_code) >= 1) & (len(div_stock_data) >= 1):  # 분할매매
                    price = self.recieved_dic[stock_code]
                    code = stock_code
                    div_stock_data_sub = div_stock_data
                    if code in div_stock_data_sub:
                        #logger.debug("분할 매매 종목 내 가격 변동 생성 : %s, %s", kname_list[code], price)
                        if div_stock_data_sub[code]["state"] == "감시중":
                            #calc_per(현재가, 비교가)
                            if calc_per(price, div_stock_data_sub[code]["last_price"]) < FIR_BUY_PERCENT:
                                self.div_order_buy(1, code)  # 1차매수진행
                        elif div_stock_data_sub[code]["state"] == "1차매수":
                            if calc_per(price, div_stock_data_sub[code]["last_price"]) < SEC_BUY_PERCENT:
                                self.div_order_buy(2, code)  # 2차매수진행
                            elif calc_per(price, div_stock_data_sub[code]["last_price"]) > FIR_INCOME_PERCENT:
                                self.div_order_sell(1, code)  # 1차매도진행
                        elif div_stock_data_sub[code]["state"] == "2차매수":
                            if calc_per(price, div_stock_data_sub[code]["last_price"]) < THIR_BUY_PERCENT:
                                self.div_order_buy(3, code)  # 3차매수진행
                            elif calc_per(price, div_stock_data_sub[code]["last_price"]) > SEC_INCOME_PERCENT:
                                self.div_order_sell(2, code)  # 2차매도진행
                        elif div_stock_data_sub[code]["state"] == "3차매수":
                            if calc_per(price, div_stock_data_sub[code]["last_price"]) < FORTH_BUY_PERCENT:
                                self.div_order_buy(4, code)  # 4차매수진행
                            elif calc_per(price, div_stock_data_sub[code]["last_price"]) > THIR_INCOME_PERCENT:
                                self.div_order_sell(3, code)  # 3차매도진행
                        elif div_stock_data_sub[code]["state"] == "4차매수":
                            if calc_per(price, div_stock_data_sub[code]["last_price"]) > FORTH_INCOME_PERCENT:
                                self.div_order_sell(4, code)  # 4차매도진행
                    self.update_div_table()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def div_order_buy(self, state, code):
        logger.debug(str(code) + "종목 " + str(state) + "차 매수 진행")
        global div_stock_data, my_cash
        try:
            if state == 1:
                amt_p = calc_next_price(int(my_cash), -93)  # 가진 금액의 7%
                amt = int(amt_p / int(div_stock_data[code]["현재가"]))

            elif state == 2:
                amt_p = calc_next_price(int(my_cash), -93)  # 가진 금액의 7%
                amt = int(amt_p / int(div_stock_data[code]["현재가"]))

            elif state == 3:
                amt_p = int(div_stock_data[code]["매입금액"] * 2 / 3)  # 저장된 매입금액의 2/3
                amt = int(amt_p / int(div_stock_data[code]["현재가"]))

            elif state == 4:
                amt_p = int(div_stock_data[code]["매입금액"] * 2 / 3)  # 저장된 매입금액의 2/3
                amt = int(amt_p / int(div_stock_data[code]["현재가"]))
            else:
                logger.debug("알수없는 데이터")

            #종목 개수 계산 후 1개 이상일 시 매수 진행
            if amt > 0:
                ret = self.SendOrder(self.account_list.currentText(), 1, code, amt, 0, '03')
                if ret == 0:
                    logger.debug("매수 주문 요청 성공")
                    div_stock_data[code]["state"] = str(state)+"차매수"
                    self.real_log_widget.addItem("{} 종목 매수 성공".format(div_stock_data[code]["name"]))
                else:
                    logger.debug("매수 주문 요청 실패 오류코드 : " + str(ret))
                    self.real_log_widget.addItem("{} 매수실패 오류코드 : ".format(div_stock_data[code]["name"]) + str(ret))

                self.save_div_data_func()
            else:
                logger.debug("매수하려는 종목보다 보유 현금 부족")
                self.real_log_widget.addItem("{} : 보유 현금 부족".format(div_stock_data[code]["name"]))

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def div_order_sell(self, state, code):
        logger.debug(str(code) + "종목 " + str(state) + "차 매도 진행")
        try:
            amt = div_stock_data[code]["amt"]
            ret = self.SendOrder(self.account_list.currentText(), 2, code, amt, 0, '03')
            if ret == 0:
                logger.debug("매도 주문 요청 성공")
                del div_stock_data[code]
            else:
                logger.debug("매도 주문 요청 실패 오류코드 : " + str(ret))
            self.save_div_data_func()
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def update_con_table(self):  # 테이블 업데이트 함수
        global kname_list, code_list, stock_data, div_stock_data
        try:
            try:
                combobox_list_index = self.cbox_con.currentText()[:3]
            except:
                logger.debug("콤보박스 리스트 인덱스 없음 !")
                combobox_list_index = ""
            self.table_con.setRowCount(len(self.con_list[combobox_list_index]["list"]))
            tmp_index = 0
            for code_key in self.con_list[combobox_list_index]["list"]:
                # logger.debug(code_key)
                self.table_con.setItem(tmp_index, 0, QTableWidgetItem(code_key))
                self.table_con.setItem(tmp_index, 1, QTableWidgetItem(kname_list[code_key]))
                last = int(self.GetMasterLastPrice(code_key).lstrip("0"))
                self.table_con.setItem(tmp_index, 2, QTableWidgetItem(format(int(str(last).lstrip("0")), ",")))

                tmp_index += 1

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def update_div_table(self):  # 테이블 업데이트 함수
        global kname_list, code_list, stock_data, div_stock_data
        try:
            self.table_div.setRowCount(len(div_stock_data))

            for i, j in enumerate(div_stock_data.keys()):
                #logger.debug("{} {}".format(i, j))
                #logger.debug("{} {}".format(div_stock_data[j]["name"], div_stock_data[j]["현재가"]))
                #logger.debug(div_stock_data[j])
                self.table_div.setItem(i, 0, QTableWidgetItem(j))
                self.table_div.setItem(i, 1, QTableWidgetItem(div_stock_data[j]["name"]))

                if int(div_stock_data[j]["last_price"]) > 100:
                    self.table_div.setItem(i, 2, QTableWidgetItem(format(int(str(div_stock_data[j]["last_price"]).lstrip('0')), ",")))

                self.table_div.setItem(i, 3, QTableWidgetItem(format(int(div_stock_data[j]["현재가"]), ",")))
                self.table_div.setItem(i, 4, QTableWidgetItem(format(int(div_stock_data[j]["avr_price"]), ",")))
                self.table_div.setItem(i, 5, QTableWidgetItem(div_stock_data[j]["amt"]))
                self.table_div.setItem(i, 6, QTableWidgetItem(div_stock_data[j]["state"]))
                self.table_div.setItem(i, 7, QTableWidgetItem(div_stock_data[j]["fir_date"]))

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def update_holding_table(self):  # 테이블 업데이트 함수
        global kname_list, code_list, stock_data, div_stock_data
        try:
            self.table_holding.setRowCount(len(self.jango["종목리스트"]))
            for i in range(len(self.jango["종목리스트"])):
                self.table_holding.setItem(i, 0, QTableWidgetItem(self.jango["종목리스트"][i]["종목코드"]))
                self.table_holding.setItem(i, 1, QTableWidgetItem(self.jango["종목리스트"][i]["종목이름"]))
                self.table_holding.setItem(i, 3, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["매입단가"]), ",")))
                self.table_holding.setItem(i, 4, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["보유수량"]), ",")))
                per = int_format(
                    str(round(float(int(self.jango["종목리스트"][i]["현재가"]) / int(self.jango["종목리스트"][i]["매입단가"]) - 1) * 100,
                              2)))
                last_p = int(self.jango["종목리스트"][i]["매입단가"].lstrip("0"))
                cp = int(self.jango["종목리스트"][i]["현재가"])
                if cp >= last_p:
                    txt = "▲" + format(cp, ",")
                    per = "▲" + str(per)
                    self.table_holding.setItem(i, 2, QTableWidgetItem(txt))
                    self.table_holding.item(i, 2).setForeground(QtGui.QColor(255, 0, 0))
                    self.table_holding.setItem(i, 5, QTableWidgetItem(per))
                    self.table_holding.item(i, 5).setForeground(QtGui.QColor(255, 0, 0))
                else:
                    txt = "▼" + format(cp, ",")
                    per = "▼" + str(per)
                    self.table_holding.setItem(i, 2, QTableWidgetItem(txt))
                    self.table_holding.item(i, 2).setForeground(QtGui.QColor(0, 0, 255))
                    self.table_holding.setItem(i, 5, QTableWidgetItem(per))
                    self.table_holding.item(i, 5).setForeground(QtGui.QColor(0, 0, 255))

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def order(self):
        try:
            accno = self.account_list.currentText()
            code = self.view_selec_coin_lbl.text()
            amt = self.order_amount.text()
            if amt == "":
                amt = 1

            ret = self.SendOrder(1, accno, code, amt)
            if ret == 0:
                logger.debug("매수 주문 요청 성공")
            else:
                logger.debug("매수 주문 요청 실패 오류코드 : " + str(ret))

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def order_sell(self):
        try:
            global kname_list

            accno = self.account_list.currentText()
            code = self.view_selec_coin_lbl.text()
            # amt = self.order_amount_2.text()
            amt = 1
            print(accno)
            name = kname_list[code]
            reply = QMessageBox.question(self, '확인', name + ' 종목을 매도하시겠습니까?')
            if reply == QMessageBox.Yes:
                ret = self.SendOrder(2, str(accno), code, amt, 0, "03")
                if ret == 0:
                    logger.debug("매도 주문 요청 성공")
                else:
                    logger.debug("매도 주문 요청 실패 오류코드 : " + str(ret))

        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def update_jango(self):  # 잔고 데이터, 분할매매 데이터 업데이트
        global div_stock_data, my_cash
        try:
            my_cash = int(str(self.jango["출금가능금액"]).strip().lstrip('+').lstrip('-'))

            self.table_jango.setItem(0, 0, QTableWidgetItem(format(int(self.jango["예수금"]), ",")))
            self.table_jango.setItem(1, 0, QTableWidgetItem(
                format(int(str(self.jango["출금가능금액"]).strip().lstrip('+').lstrip('-')), ",")))
            self.table_jango.setItem(2, 0, QTableWidgetItem(format(int(self.jango["주식매수총액"]), ",")))
            self.table_jango.setItem(3, 0, QTableWidgetItem(format(int(self.jango["평가금액합계"]), ",")))

            tot_hab = self.jango["총손익합계"]
            if tot_hab[0] == '-':
                res = "-" + format(int(tot_hab[1:]), ",")
            else:
                res = format(int(tot_hab), ",")
            self.table_jango.setItem(4, 0, QTableWidgetItem(res))

            logger.debug("jango update suc")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

        # logger.debug(self.jango)


"""
@ 가격 정보 변동 체크 쓰레드
"""


class MyThread(QThread):
    finished = pyqtSignal(str)

    def __init__(self):
        try:
            super().__init__()
            # time.sleep(10)
            self.run_auto_buy = True
            logger.debug("run thread")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def run(self):  # 매초마다 받아온 데이터 집어넣기
        try:
            global stock_data, login_flag, auto_flag, test, kname_list
            heartBeat = 0
            while True:
                time.sleep(1)
                heartBeat += 1
                if heartBeat > 300:
                    logger.debug("myThread heartBeat...!")
                    heartBeat = 0

                if login_flag == True: #todo - 핀포인트 업데이트
                    combobox_list_index = main.cbox_con.currentText()[:3]
                    if len(main.recieved_dic) > 1:
                        for code_key, price in main.recieved_dic.items():
                            #logger.debug("{} {}".format(kname_list[code_key], price))

                            for jong in main.jango["종목리스트"]:
                                if code_key == jong["종목코드"]:
                                    if jong["현재가"] != int_format(price):  # 가격이 변동되었을때
                                        jong["현재가"] = int_format(price)
                                        logger.debug(str(code_key) + "종목 가격 변동 to : " + str(int_format(price)))
                                        self.finished.emit(str(code_key))

                            if trade_method == CloseTradeMethod:
                                if code_key in stock_data:
                                    if stock_data[code_key]["현재가"] != int_format(price):  # 가격이 변동되었을때
                                        stock_data[code_key]["현재가"] = int_format(price)
                                        self.finished.emit(str(code_key))

                            if trade_method == FellDownMethod:
                                if code_key in div_stock_data:
                                    if div_stock_data[code_key]["현재가"] != int_format(price):  # 가격이 변동되었을때
                                        div_stock_data[code_key]["현재가"] = int_format(price)
                                        #logger.debug("1. {} {}".format(div_stock_data[code_key]["현재가"], int_format(price)))
                                        self.finished.emit(str(code_key))
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


"""
@ 매수 시간 감지 쓰레드
"""


class TimerThread(QThread):
    time_flag = pyqtSignal(str)

    def __init__(self):
        try:
            super().__init__()
            # time.sleep(10)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def run(self):  # 동작
        try:
            global login_flag, auto_flag, trade_method
            logger.debug("Timer Thread Run")
            TimerHeartBeat = 0
            while True:
                TimerHeartBeat += 1
                if TimerHeartBeat == 20:
                    logger.debug("Timer heart beat!")
                    TimerHeartBeat = 0

                if login_flag == True:
                    if trade_method == CloseTradeMethod:
                        set_time = main.timeEdit.time().toString()[:5]
                        now_time = time.strftime('%H:%M', time.localtime(time.time()))

                        logger.debug("set_time = %s, now_time = %s, %s", set_time, now_time, set_time == now_time)
                        if set_time == now_time:
                            # logger.debug("시간 같음")
                            self.time_flag.emit("")
                            time.sleep(60)
                        else:
                            pass
                            # logger.debug('시간 다름')

                # 30s 간격
                time.sleep(30)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


def int_format(val):  # "+12304" -> "12304"
    if val[0] == '+' or val[0] == '-':
        return val[1:]
    else:
        return val


def str_format(val):  # 1 -> "001"
    val = str(val)
    while len(val) != 3:
        val = "0" + val
    return val


"""
param1:현재가
param2:계산할 퍼센티지
리턴 : 계산 후 가격
"""


def calc_next_price(cp, per):
    try:
        cp = int(cp)
        per = float(per)

        val = 0.0
        val = cp + ((cp / 100) * per)
        val = int(val)
        return val

    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())


"""
param1 str   120  80 
param2 str   100 100
return float 20  -20 
"""


def calc_per(cp, np):  # 손익률 계산
    cp = int(cp)
    np = int(np)
    res = round(float((cp / np ) - 1) * 100, 2)

    return float(res)


class RegisterDialog(QDialog, register_class):
    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("Register Setting")
            self.setWindowIcon(QIcon("./image/icon.ico"))
            self.register_btn.clicked.connect(self.register_connect_func)
        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 담당자에게 문의주세요.')

    def register_connect_func(self):
        try:
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
                                             "성함과 계좌를 다시 한번 확인해 주세요.\n오류가 있을 시 등록 절차가 길어질 수 있습니다.\n진행하시겠습니까?")
                if reply == QMessageBox.Yes:
                    check_socket_connect(txt)

                    if connection_flag == 'already':
                        QMessageBox.information(self, '확인', '사용되고 있는 아이디입니다.\n다른 아이디로 신청해주세요.')
                    elif connection_flag == 'success':
                        QMessageBox.information(self, '확인', '신청이 완료되었습니다.\n인증 후 등록 완료되므로 담당자에게 등록요청해주세요.')
                    else:
                        QMessageBox.information(self, '확인', '잘못된 메세지입니다. : ' + str(connection_flag))
        except Exception as e:
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())


# 플래그 없으면 스레드 돌면서 main 작동되어 에러 발생함
login_flag = False
main = object


class MyWindow(QMainWindow, start_class):

    def __init__(self):
        try:
            super().__init__()
            self.setupUi(self)
            self.setWindowTitle("WIN_STOCK AutoTrading System ver 1.01")
            self.setWindowIcon(QIcon("./image/icon.ico"))
            logger.debug("login init_process close...")

            self.update_frame.setVisible(False)

            self.movie = QMovie('./image/login_gif.gif', QByteArray(), self)
            self.movie.setCacheMode(QMovie.CacheAll)
            # QLabel에 동적 이미지 삽입
            self.login_gif.setMovie(self.movie)
            self.movie.start()

            self.movie = QMovie('./image/faceman.gif', QByteArray(), self)
            self.movie.setCacheMode(QMovie.CacheAll)
            # QLabel에 동적 이미지 삽입
            self.updating.setMovie(self.movie)
            self.movie.start()

            self.login_btn.clicked.connect(self.login_btn_func)
            self.login_btn.setStyleSheet(
                '''
                QPushButton{image:url(./image/login_2.png); border:0px;}
                QPushButton:hover{image:url(./image/login_1.png); border:0px;}
                ''')

            self.regi_lbl.clicked.connect(self.register_func)
            self.regi_lbl.setStyleSheet(
                '''
                QPushButton{image:url(./image/register_1.png); border:0px;}
                QPushButton:hover{image:url(./image/register_2.png); border:0px;}
                ''')

            # pixmap = QPixmap("./image/login_back_img.png")
            # self.backImg_lbl.setPixmap(pixmap)

        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())

    def login_btn_func(self):
        global user_name, key, update_flag, connection_flag
        try:
            self.update_frame.setVisible(True)
            key = {}
            user_name = self.userName.text()
            user_name = str(user_name).lower()
            logger.debug("user_name : %s", user_name)
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

    def register_func(self):
        logger.debug("Register btn clicked")
        self.osdlg = RegisterDialog()
        self.osdlg.show()

    @pyqtSlot(dict)
    def window_close(self):
        global user_data, key, login_flag, main
        try:

            # self.read_sucess.emit(user_name)
            # self.mainDlg = Main()
            # self.mainDlg.show()
            main = Main()
            main.show()
            self.close()


        except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
            logger.debug("예외가 발생했습니다. %s", e)
            logger.debug(traceback.format_exc())
            QMessageBox.warning(self, '경고', '알 수 없는 에러 발생, 프로그램을 재시작하여 주세요.')

    def login_process(self):
        try:
            global connection_flag, update_flag, update_p, version_level, key
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
                    previous_date = dt.datetime(int(key['time'][:4]), int(key['time'][4:6]),
                                                      int(key['time'][6:8]),
                                                      23, 59, 0)
                    if previous_date < dt.datetime.now():
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

                        logger.debug("login start!")
                        # self.loading_lbl.setText("LOADING...")

                        self.login_timer.stop()
                        connection_flag = ''

                        self.window_close()

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


if __name__ == "__main__":
    logger.debug("window start")
    app = QApplication(sys.argv)

    # main = Main()
    # myWindow = MyWindow()
    # myWindow.show()

    # test main
    global test
    test = 0
    if test:
        logger.debug("test start")
        login_flag = True
        main = Main()
        main.show()
    else:
        logger.debug("real start")
        myWindow = MyWindow()
        myWindow.show()

    # test version
    # main = Main_UI()
    # main.show()
    ####

    app.exec_()
