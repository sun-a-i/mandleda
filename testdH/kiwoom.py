from PyQt5.QAxContainer import *
import pythoncom
import queue

class Kiwoom:
    def __init__(self):
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.login = False
        self.tr = False
        self.tr_queue = queue.Queue()

    def CommConnect(self):
        self.ocx.dynamicCall("CommConnect()")
        while self.login is False:
            pythoncom.PumpWaitingMessages()

    def OnEventConnect(self, code):
        self.login = True
        print("login is done", code)

    def GetCodeListByMarket(self, market):
        ret = self.ocx.dynamicCall("GetCodeListByMarket(QString)", market)
        codes = ret.split(';')[:-1]
        return codes

    def GetMasterCodeName(self, code):
        ret = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return ret

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
        # print(screen, rqname, trcode, record, next)
        self.tr = True

        rows = self.GetRepeatCnt(trcode, record)
        if rows == 0:
            rows = 1

        data = []
        for row in range(rows):
            date = self.GetCommData(trcode, rqname, row, "일자")
            open = self.GetCommData(trcode, rqname, row, "시가")
            high = self.GetCommData(trcode, rqname, row, "고가")
            low = self.GetCommData(trcode, rqname, row, "저가")
            close = self.GetCommData(trcode, rqname, row, "현재가")
            data.append([date, open, high, low, close])

        self.tr_queue.put((data, next))

    def GetRepeatCnt(self, trcode, record):
        data = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, record)
        return data