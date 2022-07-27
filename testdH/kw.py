import time

from PyQt5.QAxContainer import *
import pythoncom
import sys
from queue import Queue
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
import const

class Kiwoom:
    def __init__(self):
        self.received_data = Queue()
        self.rd = False
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.login = False
        self.condition = False
        self.tr = False
        self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer) #안에 ?
        self.ocx.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)#안에 ?
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.ocx.OnReceiveMsg.connect(self.OnReceiveMsg)
        self.ocx.OnReceiveChejanData.connect(self.OnReceiveChejanData)
        self.con_list = []
        self.code_list = []

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        while self.login is False:
            pythoncom.PumpWaitingMessages()

    def OnEventConnect(self, code):
        self.login = True
        print("login is done", code)

    def GetLoginInfo(self, tag):
        ret = self.ocx.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def GetConditionLoad(self):#이걸 부르면
        self.ocx.dynamicCall("GetConditionLoad()")
        while self.condition is False:
            #print("asd")
            pythoncom.PumpWaitingMessages()

    def SendConditionStop(self):
        pass


    def OnReceiveConditionVer(self): #이게 호출
        self.condition = True
        print("condition is got")
        con_str = self.ocx.dynamicCall("GetConditionNameList()").split(";")[:-1]
        self.con_list = []
        for i in con_str:
            self.con_list.append(i.split("^"))
        print(self.con_list)

    def SendCondition(self,i):
        self.condition = False
        er = self.ocx.dynamicCall("SendCondition(QString,QString,QInt,QInt)", "0156", self.con_list[i][1], int(self.con_list[i][0]), 0)
        if er:
            print("조건식 조회 성공")
        else:
            print("조건식 조회 실패")

        while self.condition is False:
            pythoncom.PumpWaitingMessages()

    def OnReceiveTrCondition(self,screennomb,codelist,conname,idx,next):
        self.condition = True
        #print(screennomb,codelist,conname,idx,next)
        ret = codelist.split(";")[:-1]
        self.code_list.append(ret)

    def GetMasterCodeName(self, code):
        ret = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return ret

    def GetMasterLastPrice(self, code):
        ret = self.ocx.dynamicCall("GetMasterLastPrice(QString)", code)
        return int(ret)
    #===tr===
    def SetInputValue(self, id, value):
        self.ocx.dynamicCall("SetInputValue(QString, QString)", id, value)

    def CommRqData(self, rqname, trcode, next, screen):
        self.tr = False
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen)
        while self.tr is False:
            pythoncom.PumpWaitingMessages()

    def GetCommData(self, trcode, rqname, index, item):
        data = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, index, item)
        return data.strip()

    def OnReceiveTrData(self, screen, rqname, trcode, record, next):
        print(screen, rqname, trcode, record, next)
        self.tr = True
        name = self.GetCommData(trcode, rqname, 0, "종목명")
        price = self.GetCommData(trcode, rqname, 0, "현재가")
        print(name, price)

    """
    def GetPrice(self,code):
        self.SetInputValue("종목코드", code)
        kiwoom.CommRqData("myrequest", "opt10001", 0, "0101")
        #return self.GetCommData(code, "myrequest", 0, "현재가")
    """

    # =======================실시간 관련 함수===========================

    def SetRealReg(self, screen, code_list, FID_list, type):
        code_list = ";".join(code_list)
        self.rd = False
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                             screen, code_list, FID_list, type)

        while self.rd is False:
            #print(0)
            pythoncom.PumpWaitingMessages()
            #print(1)

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data

    def OnReceiveRealData(self, code, realtype, realdata):
        self.rd = True
        #print(code, "리시브 이벤트 발생")
        #print(self.GetCommRealData(code, 302))
        #print(self.GetCommRealData(code, 10))
        price = self.GetCommRealData(code, 10)

        self.received_data.put(code)
        self.received_data.put(price)

    def DisconnectRealData(self, screen):
        self.ocx.dynamicCall("DisconnectRealData(QString)", screen)
        print("구독해지됨")


    #=======================주문 관련 함수===========================

    def SendOrder(self, name, scrnb, accno, ordertype, code, amount, price, hoga):
        self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString,, int, int, QString, QString)",
                             name, scrnb, accno, ordertype, code, amount, price, hoga)
        pass

    #def OnReceiveTrData(self, screen, rqname, trcode, record, next):

    def OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg):
        pass

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFIdList):
        pass

    def GetChejanData(self, nFid):
        pass

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

    """
    kiwoom.GetConditionLoad()
    for i in range(len(kiwoom.con_list)):
        kiwoom.SendCondition(i)

    for i in kiwoom.code_list[1] :
        kiwoom.GetPrice(i)
        time.sleep(0.5)
    """
    #kiwoom.SetRealReg("0101", ["005930", "000660"], "9001;10;16;17;302;", '0')






