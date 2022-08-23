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

update_flag = False
key = {}  # ak = 이름, sk= 계좌정보
connection_flag = ''
update_p = 0
user_name = ''

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

            self.recieved_dic = {}  # 실시간 종목별 금액 데이터 저장 딕셔너리
            self.recieved_dic_sub = {}  # 비교 딕셔너리

            self.jango = {}  # 계좌 귀속 데이터 저장 딕셔너리
            self.jango["종목리스트"] = []

            self.one_stock_data = ""
            self.one_stock_flag = False

            self.ocx.OnEventConnect.connect(self.OnEventConnect)
            self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
            self.ocx.OnReceiveMsg.connect(self.OnReceiveMsg)
            self.ocx.OnReceiveChejanData.connect(self.OnReceiveChejanData)
            self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)

            # init
            self.initial()

            # ===================UI=====================
            self.account_list.currentIndexChanged.connect(self.accno_change_func)
            # 쓰레드1
            self.mythread1 = MyThread()
            self.mythread1.finished.connect(self.update_holding_table)
            self.mythread1.start()

            #쓰레드2 socket통신
            self.socket_thread = socket_client_thread()
            self.socket_thread.finished.connect(self.msg_by_server)
            self.socket_thread.start()

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def initial(self):
        self.CommConnect()
        self.set_info()
        self.update_holding_table()
        self.table_init()

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

        except Exception as e:
            logger.debug(e)
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

                logger.debug(self.jango["종목리스트"])

                tmp_list = []
                for j in self.jango["종목리스트"]:
                    tmp_list.append(j["종목코드"])
                self.SetRealReg("0102", tmp_list, "9001;10;16;17;302;", '0')
                self.update_jango()
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

    # =======================실시간 관련 함수===========================

    """
    스크린 넘버
    0101 : 조건검색의 실시간 # 현재는 쓰지 않음
    0102 : 잔고 데이터의 실시간
    0103 : 분할매수의 실시간
    """

    def SetRealReg(self, screen, codelist, FID_list, type):  # codelist : list
        try:
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
        while self.one_stock_flag is False:
            pythoncom.PumpWaitingMessages()
        self.one_stock_flag = False



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
            #logger.debug(str(code)+str( price ))
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
            global stock_data
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
                pass

            elif s_gubun == '4':  # 파생잔고변경
                pass

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

    # ==========================================UI FUNCTION ====================================================
    # ==========================================================================================================
    # ==========================================================================================================
    # ==========================================================================================================

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

    @pyqtSlot()
    def update_holding_table(self):  # 테이블 업데이트 함수
        global code_list
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


    def update_jango(self):  # 잔고 데이터
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

    def div_order_buy(self, state, code):
        logger.debug(str(code) + "종목 " + str(state) + "차 매수 진행")
        global my_cash, test
        try:
            self.OPT10001(str(code))
            tmp_price = int_format(self.one_stock_data)
            self.one_stock_data = ''

            if state == '1':
                amt_p = calc_next_price(int(my_cash), -93)  # 가진 금액의 7%
                amt = int(amt_p / int(tmp_price))

            elif state == '2':
                amt_p = calc_next_price(int(my_cash), -93)  # 가진 금액의 7%
                amt = int(amt_p / int(tmp_price))

            elif state == '3' or state == '4':
                for i in self.jango["종목리스트"]:
                    if code == i["종목코드"]:
                        tmp_m = int(i["매입단가"])
                        tmp_a = int(i["보유수량"])
                        amt_p = int(tmp_m * tmp_a * 2 / 3)  # 저장된 매입금액의 2/3
                        amt = int(amt_p / int(tmp_price))
                try:
                    if amt > 0:
                        pass
                except:
                    amt = -1
            else:
                logger.debug("알수없는 데이터")

            #종목 개수 계산 후 1개 이상일 시 매수 진행

            print("종목코드 : " ,code,"현재가격 : ",tmp_price,"보유 현금 : ", my_cash, " 수량 : ",amt,"state : ",state)

            if amt > 0:
                if not test:
                    ret = self.SendOrder(self.account_list.currentText(), 1, code, amt, 0, '03')
                else:
                    ret = 0
                if ret == 0:
                    logger.debug("매수 주문 요청 성공")
                    self.real_log_widget.addItem("{} 종목 매수 성공".format(code))
                else:
                    logger.debug("매수 주문 요청 실패 오류코드 : " + str(ret))
                    self.real_log_widget.addItem("{} 매수실패 오류코드 : ".format(code) + str(ret))
            elif amt == -1 :
                logger.debug("참여할 수 없는 매수 진행")
            else:
                logger.debug("매수하려는 종목보다 보유 현금 부족")
                self.real_log_widget.addItem("{} : 보유 현금 부족".format(code))

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def div_order_sell(self, state, code):
        global test
        logger.debug(str(code) + "종목 " + str(state) + "차 매도 진행")
        try:
            for i in self.jango["종목리스트"] :
                if code == i["종목코드"]:
                    amt = int(i["보유수량"])
                    break;
                try:
                    if amt > 0:
                        pass
                except:
                    amt = -1
            if amt > 0 :
                if not test :
                    ret = self.SendOrder(self.account_list.currentText(), 2, code, amt, 0, '03')
                else:
                    ret = 0
            elif amt == -1 :
                logger.debug("미보유 참여 불가 매도")
            else:
                logger.debug("보유 수량 에러")
            if ret == 0:
                logger.debug("매도 주문 요청 성공")
            else:
                logger.debug("매도 주문 요청 실패 오류코드 : " + str(ret))

            print("보유수량 : ", amt, "종목코드 : ", code)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    @pyqtSlot(str)
    def msg_by_server(self,data):
        """
        data form : 마지막에 ';' 없음 ! , 빈 공간 없음 ! strip 해서 넘겨야함

        SEL; 123456 ; 1      #매수 ; 종목코드; state
        BUY; 123456 ; 3     #매도 ; 종목코드; state
        MDU; 123434 ; 44600 # 매도 결과; 종목코드; 금액 ->보류
        MSU; 123131 ; 54600 # 매수 결과; 종목코드; 금액 ->보류

        """
        logger.debug(str(data)+":까지 받았습니다 !")
        main.real_log_widget.addItem("데이터 수신 : " + str(data))

        #self.socket_thread.send_msg("받은만큼 돌려볼게요 ! :" + str(data))


        if check_data_integrity(data):
            tmp = data.split(';')
            if tmp[0] == "SEL":
                self.div_order_sell(tmp[2],tmp[1])
            elif tmp[0] == "BUY":
                self.div_order_buy(tmp[2],tmp[1])
            elif tmp[0] == "MDU":  # 매도결과 , 보류
                pass
            elif tmp[0] == "MSU":  # 매수결과 , 보류
                pass

        else :
            print("데이터 형식 맞지 않음 " + str(data))




def check_data_integrity(data):
    tmp = data.split(';')
    if len(tmp) == 3:
        if tmp[0] == "SEL" or tmp[0] == "BUY" or tmp[0] == "MDU" or tmp[0] == "MSU":
            pass
            if len(tmp[1]) == 6:
                pass
                if tmp[2] == '1' or tmp[2] == '2' or tmp[2] == '3' or tmp[2] == '4': #매수매도 결과가 보류이니 tmp[2] 접근을 state로 가능
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
    else:
       return False

"""
@ 가격 정보 변동 체크 쓰레드
"""


class MyThread(QThread):
    finished = pyqtSignal()

    def __init__(self):
        try:
            super().__init__()
            # time.sleep(10)
            logger.debug("run thread")

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def run(self):  # 매초마다 받아온 데이터 집어넣기
        try:
            global login_flag, test
            heartBeat = 0
            while True:
                time.sleep(3)
                heartBeat += 1
                if heartBeat > 300:
                    logger.debug("myThread heartBeat...!")
                    heartBeat = 0

                if login_flag == True: #todo - 핀포인트 업데이트
                    if len(main.recieved_dic) > 0:
                        for code_key, price in main.recieved_dic.items():
                            for jong in main.jango["종목리스트"]:
                                if code_key == jong["종목코드"]:
                                    if jong["현재가"] != int_format(price):  # 가격이 변동되었을때
                                        jong["현재가"] = int_format(price)
                                        #logger.debug(str(code_key) + "종목 가격 변동 to : " + str(int_format(price)))
                                        self.finished.emit()
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

"""
@소켓 통신 쓰레드


"""
import socket

HOST_socket = '192.168.0.7'
PORT_socket = 5000

class socket_client_thread(QThread):
    finished = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.con = False

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
        global login_flag,test
        while True:
            try:
                if login_flag or test:
                    time.sleep(10)
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.s:
                        self.s.connect((HOST_socket, PORT_socket))
                        self.con = True
                        logger.debug("소켓 서버 접속 완료")
                        main.real_log_widget.addItem("소켓 서버 접속 완료")
                        while True:
                            data = self.s.recv(1024).decode('utf-8')
                            #logger.debug(f'수신 데이터 :{data}')
                            self.finished.emit(data)
                else:
                    logger.debug("로그인 확인되지 않음")
            except Exception as e:
                logger.debug(e)
                #logger.debug(traceback.format_exc())
                self.con = False
                logger.debug("소켓 서버 접속 불가 재접속중 ...")
                main.real_log_widget.addItem("소켓 서버 접속 불가 재접속중 ...")




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
