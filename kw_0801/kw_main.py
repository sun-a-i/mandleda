import logging
import sys
import pythoncom
#import const
#import log_manager as lm
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
if not os.path.exists('logFile'):
    os.makedirs('logFile')
from datetime import datetime
import winsound as sd

nowDate = datetime.now()
filename = str("./logFile./" + nowDate.strftime("%Y-%m-%d_%H-%M") + "1.txt")
logger = logging.getLogger(__name__)

fileMaxByte = 10.24*1024*100
fileHandler = logging.handlers.TimedRotatingFileHandler(filename='./logFile/main.log', when='midnight', interval=1, backupCount=10)

logger.addHandler(fileHandler)
fileHandler.suffix = "%Y-%m-%d_%H-%M1.log"

formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
fileHandler.setFormatter(formatter)

streamHandler = logging.StreamHandler()
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

logger.setLevel(level=10)

main_ui = './ui/main.ui'
main_class = uic.loadUiType(main_ui)[0]

kname_list = {}
code_list = {}

MAX_BUY_LIMIT = 10000000

class MyWindow(QMainWindow, main_class): #param1 = windows : 창,  param2 = ui path

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        #==============키움==============================
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.login = False #로그인 리시브 대기 변수
        self.condition = False #조건검색 리시브 대기 변수
        self.auto_maemae = False  # 자동매매 변수

        self.con_list = {}
        self.recieved_dic = {}
        self.jango = {}
        self.jango["종목리스트"] = []


        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
        self.ocx.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.ocx.OnReceiveMsg.connect(self.OnReceiveMsg)
        self.ocx.OnReceiveChejanData.connect(self.OnReceiveChejanData)
        self.ocx.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)



        #===================UI=====================
        #self.pushButton.clicked.connect(self.order)#매수
        self.sell_btn.clicked.connect(self.order_sell)#매도
        #self.con_re.clicked.connect(self.condition_refresh)#직접갱신
        #self.auto_mm_start.clicked(self.auto_maemae_True)  # 자동매매 시작
        #self.auto_mm_end.clicked(self.auto_maemae_False)  # 자동매매 중단

        self.cbox_con.activated.connect(self.update_table)
        self.cbox_con.activated.connect(self.deactivate_real)
        self.buy_amount_edit.textChanged.connect(self.amount_change_function)




        # cell 선택 시
        self.table_con.cellClicked.connect(self.cell_cliked_func)
        self.table_maedo.cellClicked.connect(self.cell_cliked_func_2)

        # init
        self.initial()



    def initial(self):
        try:
            self.CommConnect()
            self.SetConditionSearchFlag()
            self.condition_refresh()
            self.set_info()
            self.load_code() #update_table 보다 우선순위로 작동
            self.update_table()
            try:
                self.mythread1 = MyThread()
                self.mythread1.finished.connect(self.update_table)
                self.mythread1.start()
            except Exception as e:
                logger.debug(e)
                logger.debug(traceback.format_exc())
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def set_info(self):
        try:
            account_cnt = self.GetLoginInfo("ACCOUNT_CNT")
            account_list = self.GetLoginInfo("ACCLIST").split(';')[:-1]
            user_id = self.GetLoginInfo("USER_ID")
            user_name = self.GetLoginInfo("USER_NAME")
            sever = self.GetLoginInfo("GetServerGubun")

            self.name.setText(user_name)  # 이름 설정

            logger.debug("기본 데이터 수집 완료 계좌 수 : %s, 계좌 번호 %s,  유저 아이디 : %s, 유저 이름 %s, %s",
                account_cnt,
                account_list,
                user_id,
                user_name,
                sever)

            for i in account_list:
                self.account_list.addItem(i)#계좌 목록

            for i in self.con_list:
                self.cbox_con.addItem(i + " " + self.con_list[i]["name"])#조건검색 목록

            self.Calljango(account_list[0])

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def condition_refresh(self):
        try:
            self.GetConditionLoad()
            for i in self.con_list:
                self.SendCondition(i)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def load_code(self):
        try:
            global kname_list, code_list
            # 종목코드 불러오기
            kospi_code_list = self.GetCodeListByMarket("0")
            if len(kospi_code_list) > 0:
                for i in kospi_code_list:  # 삼성전자 : 006950
                    kname_list.update({i: self.GetMasterCodeName(i)})
                    code_list.update({self.GetMasterCodeName(i): i})
            time.sleep(1)

            kosdak_code_list = self.GetCodeListByMarket('10')
            if len(kosdak_code_list) > 0:
                for i in kosdak_code_list:
                    kname_list.update({i: self.GetMasterCodeName(i)})
                    code_list.update({self.GetMasterCodeName(i): i})

            logger.debug("kospi = %s, kosdak = %s, kname_list = %s, code_list = %s", len(kospi_code_list),
                         len(kosdak_code_list),
                         len(kname_list), len(code_list))

            #logger.debug(kname_list)
            time.sleep(1)
        except Exception as e:
            logger.debug("except")
            logger.debug(traceback.format_exc())




    # ===================================키움 api======================================
     #==============================로그인 관련 함수 ========================
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
        try:
            ret = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
            return ret
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def GetMasterCodeName(self, code):
        try:
            ret = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
            return ret
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def GetMasterLastPrice(self, code):
        try:
            ret = self.ocx.dynamicCall("GetMasterLastPrice(QString)", code)
            return ret
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def GetCodeListByMarket(self, market):
        try:
            ret = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market)
            codes = ret.split(';')[:-1]
            return codes
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    # ============== 조건검색 관련 함수 =============

    def GetConditionLoad(self):  # 조건검색 목록 (이름, 번호 )요청 함수
        self.condition = False
        logger.debug("조건검색 목록 호출")
        try:
            er = self.ocx.dynamicCall("GetConditionLoad()")
            if er :
                logger.debug("조건검색 목록 호출 성공")
                while self.condition is False:
                    pythoncom.PumpWaitingMessages()
                self.condition = False
            else : logger.debug("조건검색 목록 호출 실패")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveConditionVer(self):  # 이게 호출
        self.condition = True
        logger.debug("조건검색 목록 수신 이벤트")
        try:
            self.con_list = {}
            con_str = self.ocx.dynamicCall("GetConditionNameList()").split(";")[:-1]
            if con_str == []:
                logger.debug("조건검색 조건이 없음!")
            else:
                for i in con_str:
                    i = i.split("^")
                    self.con_list[i[0]] = {} #con_list["000"] = {}
                    self.con_list[i[0]]["name"] = i[1] #con_list["000"]["name"] = "1번조건식"
                logger.debug("수집된 조건식 : " + str(self.con_list))
            logger.debug("조건검색 목록 호출 완료")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def SendCondition(self, key): #조건식에 맞는 코드 요청 함수
        self.condition = False
        try:
            logger.debug(str(key) + " 조건식 조회 요청")
            er = self.ocx.dynamicCall("SendCondition(QString,QString,QInt,QInt)", "0156",
                                      self.con_list[key]["name"], key, 1) # 실시간옵션. 0:조건검색만, 1:조건검색+실시간 조건검색
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
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def OnReceiveRealCondition(self, code, etype, con_name, con_idx): #테스트 중 # 조건검색 변동 이벤트 함수
        logger.debug("OnReceiveRealCondition 조건검색 변동 이벤트 발생 :" + str(code))
        print("OnReceiveRealCondition 조건검색 변동 이벤트 발생 :", code, etype, con_name, con_idx)
        try:
            if str_format(con_idx) ==  str(self.cbox_con.currentText()[:3]):
                if etype == 'I':  # 종목편입
                    logger.debug(code + "종목 편입 이벤트 발생")
                    self.con_list[str_format(con_idx)]["list"][code] = "0"
                    self.SetRealReg("0101",code,"9001;10;16;17;302;", '1') #실시간 추가 등록
                    sd.Beep(400, 200)
                    sd.Beep(480, 300)
                elif etype == 'D':  # 종목이탈
                    logger.debug(code + "종목 이탈 이벤트 발생")
                    del self.self.con_list[str_format(con_idx)]["list"][code]
                    self.SetRealRemove("0101",code)
                else:
                    logger.debug("이건 뭐지 ? OnReceiveRealCondition")
                pass
            else:
                logger.debug("현재 설정한 조건검색과 다른 변동 이벤트 무시" )
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    #==========================TR 관련 함수==============================

    def SetInputValue(self, id, value):
        try:
            self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def CommRqData(self, rqname, trcode, next, screen):
        try:
            return self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def GetCommData(self, trcode, rqname, index, item):
        try:
            data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item)
            return data.strip()
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def GetTRCount(self, trcode, rqname):
        try:
            return self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def Calljango(self, accno):  # 잔고 요청
        logger.debug("잔고요청 전송됨")
        try:
            self.SetInputValue("계좌번호", accno)
            self.SetInputValue("비밀번호", "")
            self.SetInputValue("비밀번호입력매체구분", "00")

            ret = self.CommRqData("잔고요청", "opw00005", "0", "0101")
            if ret != 0:
                logger.debug("잔고 조회 오류코드 : ", ret)
            else:
                logger.debug("잔고요청 성공")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def Calljango2(self, accno):  # 잔고 요청2
        logger.debug("잔고요청2 전송됨")
        try:
            self.SetInputValue("계좌번호", accno)
            self.SetInputValue("비밀번호", "")
            self.SetInputValue("상장폐지조회구분", "1")
            self.SetInputValue("비밀번호입력매체구분", "00")

            ret = self.CommRqData("잔고요청2", "opw00004", "0", "0101")
            if ret != 0:
                logger.debug("잔고 조회2 오류코드 : ", ret)
            else:
                logger.debug("잔고요청2 성공")
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())



    def OnReceiveTrData(self, screen, rcname, trcode, record, next):# tr 수신 이벤트
        logger.debug("OnReceiveTrData %s, %s, %s, %s, %s", screen, rcname, trcode, record, next)
        try:
            if next == "2":
                logger.debug("데이터 더 있음 !! 요청 이름 : " + str(rcname))

            # logger.debug(screen, rcname, trcode, record, next)
            # name = self.GetCommData(trcode, rcname, 0, "종목명")\
            # price = self.GetCommData(trcode, rcname, 0, "현재가")

            if rcname == "잔고요청":
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

                # ====멀티tr====
                self.jango["종목리스트"] = []
                for i in range(self.GetTRCount("opw00005", "잔고요청")):
                    tmp = {}
                    tmp["종목코드"] = self.GetCommData("opw00005", "잔고요청", i, "종목번호").lstrip("0")[1:]#A123455->123455
                    tmp["종목이름"] = self.GetCommData("opw00005", "잔고요청", i, "종목명").lstrip("0")
                    tmp["현재가"] = self.GetCommData("opw00005", "잔고요청", i, "현재가").lstrip("0")
                    tmp["매입금액"] = self.GetCommData("opw00005", "잔고요청", i, "매입금액").lstrip("0")
                    tmp["평가금액"] = self.GetCommData("opw00005", "잔고요청", i, "평가금액").lstrip("0")
                    self.jango["종목리스트"].append(tmp)

                tmp_list = []
                for j in self.jango["종목리스트"] :
                    tmp_list.append(j["종목코드"])
                self.SetRealReg("0102", tmp_list, "9001;10;16;17;302;", '0')

                self.update_jango()
                self.update_table()
                logger.debug("잔고요청 업데이트 완료")

            elif rcname == "order":
                #print(screen, rcname, trcode, record, next)#debug 메세지 에러
                #update jango?
                pass

            elif rcname == "잔고요청2":
                logger.debug("잔고요청2 수신 발생")
                self.jango["예수금"] = self.GetCommData("opw00004", "잔고요청2", 0, "예수금").lstrip("0")
                self.jango["D+2추정예수금"] = self.GetCommData("opw00004", "잔고요청2", 0, "D+2추정예수금").lstrip("0")
                self.jango["총매입금액"] = self.GetCommData("opw00004", "잔고요청2", 0, "총매입금액").lstrip("0")
                self.jango["누적손익률"] = self.GetCommData("opw00004", "잔고요청2", 0, "누적손익률").lstrip("0")

                # ====멀티tr====
                self.jango["종목리스트"] = []
                for i in range(self.GetTRCount("opw00004", "잔고요청2")):
                    tmp = {}
                    tmp["종목코드"] = self.GetCommData("opw00004", "잔고요청2", i, "종목코드").lstrip("0")[1:]#A123455->123455
                    tmp["종목명"] = self.GetCommData("opw00004", "잔고요청2", i, "종목명").lstrip("0")
                    tmp["현재가"] = self.GetCommData("opw00004", "잔고요청2", i, "현재가").lstrip("0")
                    tmp["매입금액"] = self.GetCommData("opw00004", "잔고요청2", i, "매입금액").lstrip("0")
                    tmp["평가금액"] = self.GetCommData("opw00004", "잔고요청2", i, "평가금액").lstrip("0")
                    tmp["보유수량"] = self.GetCommData("opw00004", "잔고요청2", i, "보유수량").lstrip("0")
                    tmp["결제잔고"] = self.GetCommData("opw00004", "잔고요청2", i, "결제잔고").lstrip("0")
                    self.jango["종목리스트"].append(tmp)

                self.update_jango()
                self.update_table()
                logger.debug("잔고요청2 업데이트 완료")

            else:
                logger.debug("이 수신 데이터는 ?")
                logger.debug(screen, rcname, trcode, record, next)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())






    """
    def GetPrice(self,code):
        self.SetInputValue("종목코드", code)
        self.CommRqData("con_1rq", "opt10001", 0, "0101")#ONrecieveTrdata 안에서 써야함
        return self.GetCommData(code, "myrequest", 0, "현재가")
    """


    # =======================실시간 관련 함수===========================

    def SetRealReg(self, screen, codelist, FID_list, type): #codelist : list
        try:
            if type == "0": logger.debug(str(self.cbox_con.currentText()[:3]) + " 조건식 실시간 등록")
            elif type == "1" : logger.debug(str(codelist) + " 종목 실시간 추가 등록")
            codelist = ";".join(codelist)
            self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                                 screen, codelist, FID_list, type)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def GetCommRealData(self, code, fid):
        try:
            data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
            return data
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveRealData(self, code, realtype, realdata): #스레드로 스트림 데이터 처리
        try:
            # logger.debug(code, "리시브 이벤트 발생")
            price = self.GetCommRealData(code, 10)
            self.recieved_dic[code] = price
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

    def SetRealRemove(self, screen, code):
        try:
            self.ocx.dynamicCall("DisconnectRealData(QString, QString)", screen, code)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    # =======================주문 관련 함수===========================

    def SendOrder(self, type, accno, code, amount):  # 시장가 매매 TR
        try:
            # logger.debug("send order")
            return self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int   , int, QString, QString)",
                ["order", "0101", accno, type, code, amount, 0, "03", ""])
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg):
        try:
            logger.debug("OnReceiveMsg %s, %s, %s, %s", sScrNo, sRQName, sTrCode, sMsg)
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def OnReceiveChejanData(self, gubun, nItemCnt, sFIdList):
        print("OnReceiveChejanData ", gubun, nItemCnt, sFIdList)#debug msg error
        """
        for i in sFIdList.split(";")[:-1]:
            print(i, ", ", self.GetChejanData(i))
        """
        try:

            if gubun == '1': #국내주식 잔고변경
                if str(self.GetChejanData("946")) == "2":
                    tmp = "매수"
                elif str(self.GetChejanData("946")) == "1":
                    tmp = "매도"
                logger.debug(str(self.GetChejanData("9001")[1:]) + str(self.GetChejanData("302").strip() + " : " + tmp + " 주문 성공 "))

                self.Calljango(self.account_list.currentText())
                pass

            elif gubun == '4': #파생잔고변경
                pass

            # logger.debug(self.GetChejanData(Fid))

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

    def auto_buy(self):
        pass

    def auto_sell(self,code):
        pass






#==========================================UI FUNCTION ====================================================
#==========================================================================================================
#==========================================================================================================
#==========================================================================================================


    """
    -매수금 가능 금액 제한 함수
    -MAX_BUY_LIMIT 하드코딩
    """
    def amount_change_function(self):
        try:
            val = self.buy_amount_edit.text()
            val = val.replace(",", "")

            if int(val) > MAX_BUY_LIMIT:
                QMessageBox.information(self, '확인', '100만원 이상 매수할 수 없습니다.')
                self.buy_amount_edit.setText(format(MAX_BUY_LIMIT, ","))
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
            num = self.table_con.currentRow()
            select_code = self.table_con.item(num, 0).text()

            self.view_selec_coin_lbl.setText(select_code)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def cell_cliked_func_2(self):
        try:
            num = self.table_maedo.currentRow()
            select_code = self.table_maedo.item(num, 0).text()

            self.view_selec_coin_lbl.setText(select_code)

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def auto_maemae_True(self): #자동매매 시작 클릭 이벤트 함수
        try:
            self.auto_maemae = True
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())
    def auto_maemae_False(self): #자동매매 중단 클릭 이벤트 함수
        try:
            self.auto_maemae = False
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    @pyqtSlot()
    def update_table(self): #테이블 업데이트 함수
        global kname_list, code_list
        try:
            try:
                combobox_list_index = self.cbox_con.currentText()[:3]
            except:
                logger.debug("콤보박스 리스트 인덱스 없음 !")
                combobox_list_index = ""

            self.table_con.setRowCount(len(self.con_list[combobox_list_index]["list"]))

            tmp_index = 0
            for code_key in self.con_list[combobox_list_index]["list"]:
                #logger.debug(code_key)

                self.table_con.setItem(tmp_index, 0, QTableWidgetItem(code_key))
                self.table_con.setItem(tmp_index, 1, QTableWidgetItem(kname_list[code_key]))
                #self.table_con.setItem(tmp_index, 2, QTableWidgetItem(self.con_list[combobox_list_index]["list"][code_key]))

                cp = int(self.con_list[combobox_list_index]["list"][code_key])
                last_p = int(self.GetMasterLastPrice(code_key).lstrip("0"))
                if cp >= last_p:
                    txt = "▲" + format(cp, ",")
                    self.table_con.setItem(tmp_index, 2, QTableWidgetItem(txt))
                    self.table_con.item(tmp_index, 2).setForeground(QtGui.QColor(255, 0, 0))
                else:
                    txt = "▼" + format(cp, ",")
                    self.table_con.setItem(tmp_index, 2, QTableWidgetItem(txt))
                    self.table_con.item(tmp_index, 2).setForeground(QtGui.QColor(0, 0, 255))

                self.table_con.setItem(tmp_index, 3,QTableWidgetItem(format(int(str(last_p).lstrip("0")), ",")))
                #self.table_con.setItem(tmp_index, 3, QTableWidgetItem(str(self.GetMasterLastPrice(code_key).lstrip("0"))))

                #self.table_con.setItem(tmp_index, 4, QTableWidgetItem(str(tmp_index)))
                tmp_index += 1
            self.table_maedo.setRowCount(len(self.jango["종목리스트"]))
            for i in range(len(self.jango["종목리스트"])):
                self.table_maedo.setItem(i, 0, QTableWidgetItem(self.jango["종목리스트"][i]["종목코드"]))
                self.table_maedo.setItem(i, 1, QTableWidgetItem(self.jango["종목리스트"][i]["종목이름"]))
                self.table_maedo.setItem(i, 2, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["현재가"]), ",")))
                self.table_maedo.setItem(i, 3, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["매입금액"]), ",")))
                self.table_maedo.setItem(i, 4, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["평가금액"]), ",")))
                # self.table_maedo.setItem(i, 5, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["보유수량"]), ",")))
                # self.table_maedo.setItem(i, 6, QTableWidgetItem(self.jango["종목리스트"][i]["결제잔고"]))


        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def deactivate_real(self): #조건검색 변경시 전의 실시간을 등록 해지 후 새로운 조건검색 인덱스로 실시간 등록
        try:
            combobox_list_index = self.cbox_con.currentText()[:3]
            self.DisconnectRealData("0101")
            self.SetRealReg("0101", self.con_list[combobox_list_index]["list"].keys(), "9001;10;16;17;302;", '0')

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
                logger.debug("매수 주문 요청 실패 오류코드 : "+str(ret))

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def order_sell(self):
        try:
            accno = self.account_list.currentText()
            code = self.view_selec_coin_lbl.text()
            amt = 1 # 우선 1개
            if amt == "":
                amt = 1

            ret = self.SendOrder(2, accno, code, amt)
            if ret == 0:
                logger.debug("매도 주문 요청 성공")
            else:
                logger.debug("매도 주문 요청 실패 오류코드 : " + str(ret))

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())


    def update_jango(self):
        try:
            """
            tmp = 0
            for i in range(self.jango):
                self.table_jango.setItem(tmp, 0, QTableWidgetItem(self.jango[i]))"""
            #self.money.setText(self.jango["D+2추정예수금"])
            self.table_jango.setItem(0,0,QTableWidgetItem(format(int(self.jango["예수금"]), ",")))
            self.table_jango.setItem(1,0,QTableWidgetItem(format(int(self.jango["예수금D+2"]), ",")))
            self.table_jango.setItem(2,0,QTableWidgetItem(format(int(self.jango["출금가능금액"]), ",")))
            self.table_jango.setItem(3,0,QTableWidgetItem(format(int(self.jango["주식매수총액"]), ",")))
            self.table_jango.setItem(4,0,QTableWidgetItem(format(int(self.jango["평가금액합계"]), ",")))
            """
            self.table_maedo.setRowCount(len(self.jango["종목리스트"]))
            for i in range(len(self.jango["종목리스트"])):
                self.table_maedo.setItem(i, 0, QTableWidgetItem(self.jango["종목리스트"][i]["종목코드"]))
                self.table_maedo.setItem(i, 1, QTableWidgetItem(self.jango["종목리스트"][i]["종목이름"]))
                self.table_maedo.setItem(i, 2, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["현재가"]), ",")))
                self.table_maedo.setItem(i, 3, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["매입금액"]), ",")))
                self.table_maedo.setItem(i, 4, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["평가금액"]), ",")))
                #self.table_maedo.setItem(i, 5, QTableWidgetItem(format(int(self.jango["종목리스트"][i]["보유수량"]), ",")))
                #self.table_maedo.setItem(i, 6, QTableWidgetItem(self.jango["종목리스트"][i]["결제잔고"]))"""

        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

        #logger.debug(self.jango)


class MyThread(QThread):
    def __init__(self):
        super().__init__()
        finished = pyqtSignal()
        self.run_auto_buy  = True

    def update_signal(self):#매초마다 받아온 데이터 집어넣기
        try:
            self.em = False
            combobox_list_index = myWindow.cbox_con.currentText()[:3]
            for code_key, price in myWindow.recieved_dic.items():
                if code_key in myWindow.con_list[combobox_list_index]["list"]:  # 현재의 조건식에 있는 코드만 비교
                    if myWindow.con_list[combobox_list_index]["list"][code_key] != int_format(price):  # 가격이 변동되었을때
                        myWindow.con_list[combobox_list_index]["list"][code_key] = int_format(price)
                        self.em = True
                for jango_code in myWindow.jango["종목리스트"]:
                    if jango_code["종목코드"] == code_key:
                        if jango_code["현재가"] != int_format(price):  # 가격이 변동되었을때
                            jango_code["현재가"] = int_format(price)
                            self.em = True
            if self.em:
                self.finished.emit()  # 업데이트 발생
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def check_time_buy(self):
        try:
            set_time = myWindow.timeEdit.time().toString()[:5]
            now_time = time.strftime('%H:%M', time.localtime(time.time()))
            if set_time == now_time : return True
            else: return False
        except Exception as e:
            logger.debug(e)
            logger.debug(traceback.format_exc())

    def auto_buy_check(self):
        if myWindow.auto_maemae:
            if self.check_time_buy() and self.run_auto_buy:  # 매수 단 1회 정해진 시각
                self.run_auto_buy = False
                myWindow.auto_buy()



    def run(self): #동작
        while True:
            self.update_signal()
            time.sleep(1)
            self.auto_buy_check()


def int_format(val): # "+12304" -> "12304"
    if val[0] == '+' or val[0] == '-':
        return val[1:]
    else:
        return val

def str_format(val): # 1 -> "001"
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

        return val
    except Exception as e:  # 모든 예외의 에러 메시지를 출력할 때는 Exception을 사용
        logger.debug("예외가 발생했습니다. %s", e)
        logger.debug(traceback.format_exc())



if  __name__ == "__main__":
    logger.debug("window start")
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()







