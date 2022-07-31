import time

from PyQt5.QAxContainer import *
import pythoncom
import sys
from queue import Queue
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
import const
import log_manager as lm

class Kiwoom():
    def __init__(self):
        self.rd = False
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.login = False
        self.condition = False
        self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer) #안에 ?
        self.ocx.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)#안에 ?
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.ocx.OnReceiveMsg.connect(self.OnReceiveMsg)
        self.ocx.OnReceiveChejanData.connect(self.OnReceiveChejanData)
        self.ocx.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)
        self.con_list = []
        self.code_list = []
        self.recieved_dic = {}
        self.realcondition = False
        self.jango = {}

    #=======로그인 관련 함수========
    def CommConnect(self):
        try:
            self.ocx.dynamicCall("CommConnect()")
            while self.login is False:
                pythoncom.PumpWaitingMessages()

        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def OnEventConnect(self, code):
        self.login = True
        lm.logger.debug("login is done %s", code)

    #======기타 요청 함수==========
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


    #============== 조건검색 관련 함수 =============


    def GetConditionLoad(self):#이걸 부르면
        try:
            self.ocx.dynamicCall("GetConditionLoad()")
            while self.condition is False:
                #lm.logger.debug("asd")
                pythoncom.PumpWaitingMessages()
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def OnReceiveConditionVer(self): #이게 호출
        self.condition = True
        lm.logger.debug("condition is got")
        con_str = self.ocx.dynamicCall("GetConditionNameList()").split(";")[:-1]
        self.con_list = []

        lm.logger.debug("수집된 조건식명 리스트 : %s", con_str)
        for i in con_str:
            self.con_list.append(i.split("^"))
        lm.logger.debug(self.con_list)

    def SendCondition(self,i):
        try:
            self.condition = False
            er = self.ocx.dynamicCall("SendCondition(QString,QString,QInt,QInt)", "0156",
                                      self.con_list[i][1], int(self.con_list[i][0]), 0)
            if er:
                lm.logger.debug("조건식 조회 성공")
                pass
            else:
                lm.logger.debug("조건식 조회 실패")

            count = 1
            while self.condition is False:
                if count > 5: break
                pythoncom.PumpWaitingMessages()
                count += 1
            #===초기설정===
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def OnReceiveTrCondition(self,screennomb,codelist,conname,idx,next): #조건검색 후 받아오는 이벤트
        try:
            self.condition = True
            #lm.logger.debug(screennomb,codelist,conname,idx,next)
            ret = {}

            tmp = codelist.split(";")[:-1]

            for i in tmp:
                kv = i.split("^")
                if len(kv[0]) == 6:
                    ret[kv[0]] = kv[1].lstrip("0")
                else:
                    lm.logger.debug("종목코드 자리수 오류",kv[0],kv[1])

            #lm.logger.debug(ret)
            self.code_list.append(ret)
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def SetInputValue(self, id, value):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def CommRqData(self, rqname, trcode, next, screen):
        return self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen)

    def GetCommData(self, trcode, rqname, index, item):
        data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item)
        return data.strip()

    def GetTRCount(self,trcode, rqname):
        return self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

    def OnReceiveTrData(self, screen, rcname, trcode, record, next):
        lm.logger.debug("OnReceiveTrData %s, %s, %s, %s, %s", screen, rcname, trcode, record, next)
        if next == "2":
            lm.logger.debug("데이터 더 있음 !!")

        #lm.logger.debug(screen, rqname, trcode, record, next)
        #name = self.GetCommData(trcode, rcname, 0, "종목명")\
        #price = self.GetCommData(trcode, rcname, 0, "현재가")

        if rcname == "잔고요청":
            """
            lm.logger.debug("잔고요청 받습니다")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"예수금"),"예수금")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"예수금D+1"),"예수금D+1")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"예수금D+2"),"예수금D+2")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"출금가능금액"),"출금가능금액")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"미수확보금"),"미수확보금")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"현금미수금"),"현금미수금")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"주식매수총액"),"주식매수총액")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"증거금현금"),"증거금현금")
            lm.logger.debug(self.GetCommData("opw00005", "잔고요청", 0,"평가금액합계"),"평가금액합계")
            #====멀티tr====
            #lm.logger.debug(self.GetTRCount("opw00005", "잔고요청"), "trconut")
            for i in range(self.GetTRCount("opw00005", "잔고요청")):
                lm.logger.debug(self.GetCommData("opw00005", "잔고요청", i,"종목번호"),"종목번호")
                lm.logger.debug(self.GetCommData("opw00005", "잔고요청", i,"종목명"),"종목명")
                lm.logger.debug(self.GetCommData("opw00005", "잔고요청", i, "현재가"), "현재가")
                lm.logger.debug(self.GetCommData("opw00005", "잔고요청", i,"매입금액"),"매입금액")
                lm.logger.debug(self.GetCommData("opw00005", "잔고요청", i,"평가금액"),"평가금액")"""


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
            # lm.logger.debug(self.GetTRCount("opw00005", "잔고요청"), "trconut")

            self.jango["종목리스트"] = []
            for i in range(self.GetTRCount("opw00005", "잔고요청")):
                tmp = {}
                tmp["종목번호"] = self.GetCommData("opw00005", "잔고요청", i, "종목번호").lstrip("0")
                tmp["종목명"] = self.GetCommData("opw00005", "잔고요청", i, "종목명").lstrip("0")
                tmp["현재가"] = self.GetCommData("opw00005", "잔고요청", i, "현재가").lstrip("0")
                tmp["매입금액"] = self.GetCommData("opw00005", "잔고요청", i, "매입금액").lstrip("0")
                tmp["평가금액"] = self.GetCommData("opw00005", "잔고요청", i, "평가금액").lstrip("0")
                self.jango["종목리스트"].append(tmp)

            #signal to update jango
            #lm.logger.debug(self.jango)

        elif rcname == "othertr":
            pass


        #lm.logger.debug(name, price)

    def OnReceiveRealCondition(self, code, etype, con_name, con_idx):
        self.realcondition = True
        lm.logger.debug("조건검색 변동 이벤트 발생 :", etype, code)
        if etype == 'I':#종목편입
            self.code_list[con_idx][code] = None
        elif etype == 'D':#종목이탈
            del self.code_list[con_idx][code]
        else:
            lm.logger.debug("이건 뭐지 ? OnReceiveRealCondition")
        pass

    """
    def GetPrice(self,code):
        self.SetInputValue("종목코드", code)
        kiwoom.CommRqData("myrequest", "opt10001", 0, "0101")
        #return self.GetCommData(code, "myrequest", 0, "현재가")
    """

    # =======================실시간 관련 함수===========================

    def SetRealReg(self, screen, codelist, FID_list, type):
        codelist = ";".join(codelist)
        self.rd = False
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                             screen, codelist, FID_list, type)

        while self.rd is False:
            #lm.logger.debug(0)
            pythoncom.PumpWaitingMessages()
            #lm.logger.debug(1)

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data

    def OnReceiveRealData(self, code, realtype, realdata):
        try:
            self.rd = True
            #lm.logger.debug(code, "리시브 이벤트 발생")
            #lm.logger.debug(self.GetCommRealData(code, 302))
            #lm.logger.debug(self.GetCommRealData(code, 10))
            price = self.GetCommRealData(code, 10)

            self.recieved_dic[code] = price

            #lm.logger.debug(code, price)
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def DisconnectRealData(self, screen):
        self.ocx.dynamicCall("DisconnectRealData(QString)", screen)
        lm.logger.debug("구독해지됨")


    #=======================주문 관련 함수===========================

    def SendOrder(self,type, accno, code, amount):#시장가 매수
        try:
            #lm.logger.debug("send order")
            return self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int   , int, QString, QString)",
                                                ["test_name", "0101", accno  , type  , code   , amount, 0  , "03", ""])
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())


    #def OnReceiveTrData(self, screen, rqname, trcode, record, next):

    def OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg):
        lm.logger.debug("OnReceiveMsg %s, %s, %s, %s",sScrNo, sRQName, sTrCode, sMsg)

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFIdList):
        lm.logger.debug("OnReceiveChejanData %s, %s, %s, %s",sGubun, nItemCnt, sFIdList)

        #lm.logger.debug(self.GetChejanData(Fid))

    def GetChejanData(self, nFid):
        pass

    #==========KOA_Function() 함수======

    def SetConditionSearchFlag(self):#조건검색에 결과에 현재가 포함으로 설정
        self.ocx.dynamicCall("KOA_Functions(QString, QString)", "SetConditionSearchFlag", "AddPrice")

    #==============기타 함수==================

    def Calljango(self,accno):#잔고 요청
        self.SetInputValue("계좌번호",accno)
        self.SetInputValue("비밀번호","")
        self.SetInputValue("비밀번호입력매체구분","00")
        lm.logger.debug("잔고요청 전송됨")
        ret = self.CommRqData("잔고요청","opw00005","0","0101")
        if ret != 0 :
            lm.logger.debug("잔고 조회 오류코드 : ",ret)
        else:
            lm.logger.debug("잔고요청 성공")

    """
sRQName, // 사용자
sScreenNo, // 화면번호
sAccNo, // 계좌번호 10자리
nOrderType, // 주문유형 1: 신규매수, 2: 신규매도 3: 매수취소, 4: 매도취소, 5: 매수정정, 6: 매도정정
sCode, // 종목코드(6자리)
nQty, // 주문수량
nPrice, // 주문가격
sHogaGb, // 거래구분
          00 : 지정가
          03 : 시장가
          05 : 조건부지정가
          06 : 최유리지정가
          07 : 최우선지정가
          10 : 지정가IOC
          13 : 시장가IOC
          16 : 최유리IOC
          20 : 지정가FOK
          23 : 시장가FOK
          26 : 최유리FOK
          61 : 장전시간외종가
          62 : 시간외단일가매매
          81 : 장후시간외종
"""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.CommConnect()
    kiwoom.SetConditionSearchFlag()

    kiwoom.GetConditionLoad()
    for i in range(len(kiwoom.con_list)):
        kiwoom.SendCondition(i)

    lm.logger.debug(kiwoom.code_list)
    """
    for i in kiwoom.code_list[1] :
        kiwoom.GetPrice(i)
        time.sleep(0.5)
    """
    #kiwoom.SetRealReg("0101", ["005930", "000660"], "9001;10;16;17;302;", '0')






