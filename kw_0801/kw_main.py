import logging
import sys
import pythoncom
import const
import log_manager as lm
import traceback
import time

from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QTableWidgetItem
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QThread


main_ui = './ui/main.ui'
main_class = uic.loadUiType(main_ui)[0]

kname_list = {}
code_list = {}

class MyWindow(QMainWindow, main_class): #param1 = windows : 창,  param2 = ui path

    def __init__(self):
        super().__init__()
        #==============키움==============================
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

        self.rd = False
        self.login = False #로그인 리시브 대기 변수
        self.condition = False #조건검색 리시브 대기 변수
        self.con_list = {}

        self.recieved_dic = {}
        self.jango = {}

        self.ocx.OnEventConnect.connect(self.OnEventConnect)
        self.ocx.OnReceiveConditionVer.connect(self.OnReceiveConditionVer)
        self.ocx.OnReceiveTrCondition.connect(self.OnReceiveTrCondition)
        self.ocx.OnReceiveTrData.connect(self.OnReceiveTrData)
        self.ocx.OnReceiveRealData.connect(self.OnReceiveRealData)
        self.ocx.OnReceiveMsg.connect(self.OnReceiveMsg)
        self.ocx.OnReceiveChejanData.connect(self.OnReceiveChejanData)
        self.ocx.OnReceiveRealCondition.connect(self.OnReceiveRealCondition)





        #===================UI=====================

        self.setupUi(self)
        # self.init()
        self.pushButton.clicked.connect(self.order)#매수
        self.pushButton_3.clicked.connect(self.order_sell)#매도
        self.con_re.clicked.connect(self.condition_refresh)#직접갱신

        self.cbox_con.activated.connect(self.update_con)

        self.cbox_con.activated.connect(self.deactivate_real)
        self.ckbox_real.stateChanged.connect(self.real_activate)



        # cell 선택 시
        self.table_con.cellClicked.connect(self.cell_cliked_func)
        self.table_maedo.cellClicked.connect(self.cell_cliked_func_2)

        self.initial()

    def initial(self):
        self.CommConnect()
        self.SetConditionSearchFlag()
        self.condition_refresh()
        self.set_info()
        #self.update_con()

        #self.load_code
    def condition_refresh(self):
        self.GetConditionLoad()
        for i in self.con_list:
            self.SendCondition(i)

    def load_code(self):
        try:
            global kname_list, code_list
            # 종목코드 불러오기
            kospi_code_list = self.GetCodeListByMarket("0")
            if len(kospi_code_list) > 0:
                for i in kospi_code_list:  # 삼성전자 : 006950
                    kname_list.update({i: self.get_master_code_name(i)})
                    code_list.update({self.get_master_code_name(i): i})
            time.sleep(1)

            kosdak_code_list = self.GetCodeListByMarket('10')
            if len(kosdak_code_list) > 0:
                for i in kosdak_code_list:
                    kname_list.update({i: self.get_master_code_name(i)})
                    code_list.update({self.get_master_code_name(i): i})

            lm.logger.debug("kospi = %s, kosdak = %s, kname_list = %s, code_list = %s", len(kospi_code_list),
                         len(kosdak_code_list),
                         len(kname_list), len(code_list))

            time.sleep(1)
        except Exception as e:
            lm.logger.debug("except")
            lm.logger.debug(lm.traceback.format_exc())




        # ===================================키움 api======================================
    def CommConnect(self):
        ptr("로그인 요청")
        try:
            ptr("로그인 요청 진행중..")
            self.ocx.dynamicCall("CommConnect()")
            ptr("로그인 요청 대기중...")
            while self.login is False:
                pythoncom.PumpWaitingMessages()
                time.sleep(1)
        except Exception as e:
            ptr("로그인 예외처리 발생")
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def OnEventConnect(self, code):
        ptr("로그인 서버 메세지 수신발생")
        if code == 0:
            self.login = True
            ptr("로그인 완료")
        else:
            ptr("로그인 에러 에러코드 :" + str(code))

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
            ptr("조건검색 목록 호출")
            er = self.ocx.dynamicCall("GetConditionLoad()")
            if er :
                ptr("조건검색 목록 호출 성공")
                while self.condition is False:
                    pythoncom.PumpWaitingMessages()
                self.condition = False
            else : ptr("조건검색 목록 호출 실패")

        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def OnReceiveConditionVer(self):  # 이게 호출
        self.condition = True
        ptr("조건검색 목록 수신 이벤트")
        self.con_list = {}
        con_str = self.ocx.dynamicCall("GetConditionNameList()").split(";")[:-1]
        if con_str == []:
            ptr("조건검색 조건이 없음!")
        else:
            for i in con_str:
                i = i.split("^")
                self.con_list[i[0]] = {} #con_list["000"] = {}
                self.con_list[i[0]]["name"] = i[1] #con_list["000"]["name"] = "1번조건식"
            ptr("수집된 조건식 : " + str(self.con_list))
        ptr("조건검색 목록 호출 완료")

    def SendCondition(self, key): #조건식에 맞는 코드 요청 함수
        self.condition = False
        try:
            ptr(str(key) + " 조건식 조회 요청")
            er = self.ocx.dynamicCall("SendCondition(QString,QString,QInt,QInt)", "0156",
                                      self.con_list[key]["name"], key, 1) # 실시간옵션. 0:조건검색만, 1:조건검색+실시간 조건검색
            if er:
                lm.logger.debug(str(key) + " 조건식 조회 요청 성공")
                while self.condition is False:
                    pythoncom.PumpWaitingMessages()
                self.condition = False
            else:
                lm.logger.debug(str(key) + " 조건식 조회 요청 실패")

        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def OnReceiveTrCondition(self, screennomb, codelist, conname, idx, next):  # 조건검색 후 받아오는 이벤트
        self.condition = True
        try:
            idx = str_format(idx)
            ptr("조건식 조회 수신 이벤트")
            ptr("조건식 이름: " + conname + ", 조건식 인덱스 : " + idx)

            tmp = codelist.split(";")[:-1]
            ret = {}
            for i in tmp:
                kv = i.split("^")
                if len(kv[0]) == 6:
                    ret[kv[0]] = kv[1].lstrip("0")
                else:
                    lm.logger.debug("종목코드 자리수 오류", kv[0], kv[1])
            # lm.logger.debug(ret)
            self.con_list[idx]["list"] = ret
            ptr("조건식 이름: " + conname + ", 조건식 인덱스 : " + idx + ", 조건검색 업데이트 완료")
            ptr(str(self.con_list))
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

    def GetTRCount(self, trcode, rqname):
        return self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

    def OnReceiveTrData(self, screen, rcname, trcode, record, next):# tr 수신 이벤트
        #lm.logger.debug("OnReceiveTrData %s, %s, %s, %s, %s", screen, rcname, trcode, record, next)
        if next == "2":
            ptr("데이터 더 있음 !! 요청 이름 : " + str(rcname))

        # lm.logger.debug(screen, rcname, trcode, record, next)
        # name = self.GetCommData(trcode, rcname, 0, "종목명")\
        # price = self.GetCommData(trcode, rcname, 0, "현재가")

        if rcname == "잔고요청":
            ptr("잔고요청 수신 발생")
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
                tmp["종목번호"] = self.GetCommData("opw00005", "잔고요청", i, "종목번호").lstrip("0")
                tmp["종목명"] = self.GetCommData("opw00005", "잔고요청", i, "종목명").lstrip("0")
                tmp["현재가"] = self.GetCommData("opw00005", "잔고요청", i, "현재가").lstrip("0")
                tmp["매입금액"] = self.GetCommData("opw00005", "잔고요청", i, "매입금액").lstrip("0")
                tmp["평가금액"] = self.GetCommData("opw00005", "잔고요청", i, "평가금액").lstrip("0")
                self.jango["종목리스트"].append(tmp)

            self.update_jango()
            ptr("잔고요청 업데이트 완료")

        elif rcname == "order":
            lm.logger.debug(screen, rcname, trcode, record, next)
            #update jango?

        elif rcname == "othertt":
            pass

        else:
            ptr("이 수신 데이터는 ?")
            lm.logger.debug(screen, rcname, trcode, record, next)


        # lm.logger.debug(name, price)

    def OnReceiveRealCondition(self, code, etype, con_name, con_idx): #테스트 필요 sendcondition에서 1로 활성화 시켜야함
        lm.logger.debug("OnReceiveRealCondition 조건검색 변동 이벤트 발생 :", code, etype, con_name, con_idx)
        if etype == 'I':  # 종목편입
            self.con_list[str_format(con_idx)]["list"][code] = None #수정 필요 하나의 가격 데이터
        elif etype == 'D':  # 종목이탈
            del self.self.con_list[str_format(con_idx)]["list"][code]
        else:
            lm.logger.debug("이건 뭐지 ? OnReceiveRealCondition")
        pass

    """
    def GetPrice(self,code):
        self.SetInputValue("종목코드", code)
        self.CommRqData("myrequest", "opt10001", 0, "0101")#ONrecieveTrdata 안에서 써야함
        return self.GetCommData(code, "myrequest", 0, "현재가")
    """


    # =======================실시간 관련 함수===========================

    def SetRealReg(self, screen, codelist, FID_list, type):

        ptr(str(self.cbox_con.currentText()[:3]) + " :실시간 등록 요청")
        codelist = ";".join(codelist)
        self.rd = False
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)",
                             screen, codelist, FID_list, type)
        while self.rd is False:
            pythoncom.PumpWaitingMessages()
        self.rd = False

    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid)
        return data

    def OnReceiveRealData(self, code, realtype, realdata): #스레드로 스트림 데이터 처리
        self.rd = True
        try:
            # lm.logger.debug(code, "리시브 이벤트 발생")
            price = self.GetCommRealData(code, 10)
            self.recieved_dic[code] = price
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())


    def DisconnectRealData(self, screen):
        self.ocx.dynamicCall("DisconnectRealData(QString)", screen)
        lm.logger.debug("실시간 구독해지됨")
        self.recieved_dic = {}

    # =======================주문 관련 함수===========================

    def SendOrder(self, type, accno, code, amount):  # 시장가 매매 TR
        try:
            # lm.logger.debug("send order")
            return self.ocx.dynamicCall(
                "SendOrder(QString, QString, QString, int, QString, int   , int, QString, QString)",
                ["order", "0101", accno, type, code, amount, 0, "03", ""])
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())


    def OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg):
        lm.logger.debug("OnReceiveMsg %s, %s, %s, %s", sScrNo, sRQName, sTrCode, sMsg)

    def OnReceiveChejanData(self, sGubun, nItemCnt, sFIdList):
        lm.logger.debug("OnReceiveChejanData %s, %s, %s, %s", sGubun, nItemCnt, sFIdList)

        # lm.logger.debug(self.GetChejanData(Fid))

    def GetChejanData(self, nFid):
        pass

    # ==========KOA_Function() 함수======

    def SetConditionSearchFlag(self):  # 조건검색에 결과에 현재가 포함으로 설정
        self.ocx.dynamicCall("KOA_Functions(QString, QString)", "SetConditionSearchFlag", "AddPrice")

    # ==============기타 함수==================

    def Calljango(self, accno):  # 잔고 요청
        self.SetInputValue("계좌번호", accno)
        self.SetInputValue("비밀번호", "")
        self.SetInputValue("비밀번호입력매체구분", "00")
        lm.logger.debug("잔고요청 전송됨")
        ret = self.CommRqData("잔고요청", "opw00005", "0", "0101")
        if ret != 0:
            lm.logger.debug("잔고 조회 오류코드 : ", ret)
        else:
            lm.logger.debug("잔고요청 성공")




#==========================================UI FUNCTION ====================================================
#==========================================================================================================
#==========================================================================================================
#==========================================================================================================


    """
    cell selected fuction
    """
    def cell_cliked_func(self):
        try:
            num = self.table_con.currentRow()
            select_code = self.table_con.item(num, 0).text()

            self.view_selec_coin_lbl.setText(select_code)

        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def cell_cliked_func_2(self):
        try:
            num = self.table_maedo.currentRow()
            select_code = self.table_maedo.item(num, 0).text()

            self.view_selec_coin_lbl.setText(select_code)

        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

    def btn1_clicked_func(self):
        QMessageBox.information(self, 'check', 'clicked a btn')

    def btn2_clicked_func(self):
        self.update_jango()

    def set_info(self):
        account_cnt = self.GetLoginInfo("ACCOUNT_CNT")
        account_list = self.GetLoginInfo("ACCLIST").split(';')[:-1]
        user_id = self.GetLoginInfo("USER_ID")
        user_name = self.GetLoginInfo("USER_NAME")
        sever = self.GetLoginInfo("GetServerGubun")

        self.name.setText(user_name)  # 이름 설정

        lm.logger.debug("기본 데이터 수집 완료 계좌 수 : %s, 계좌 번호 %s,  유저 아이디 : %s, 유저 이름 %s, %s",
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

    @pyqtSlot()
    def update_con(self):
        try:
            combobox_list_index = self.cbox_con.currentText()[:3]
        except:
            ptr("콤보박스 리스트 인덱스 없음 !")
            combobox_list_index = ""

        self.table_con.setRowCount(len(self.con_list[combobox_list_index]["list"]))

        tmp_index = 0
        for code_key in self.con_list[combobox_list_index]["list"]:
            self.table_con.setItem(tmp_index, 0, QTableWidgetItem(code_key))
            self.table_con.setItem(tmp_index, 1, QTableWidgetItem(self.GetMasterCodeName(code_key)))
            self.table_con.setItem(tmp_index, 2, QTableWidgetItem(self.con_list[combobox_list_index]["list"][code_key]))
            self.table_con.setItem(tmp_index, 3, QTableWidgetItem(str(self.GetMasterLastPrice(code_key).lstrip("0"))))
            #self.table_con.setItem(tmp_index, 4, QTableWidgetItem(str(tmp_index)))
            tmp_index += 1


    def real_activate(self): #실시간 체크 시 등록/등록 해지
        combobox_list_index = self.cbox_con.currentText()[:3]

        if self.ckbox_real.isChecked():
            self.SetRealReg("0101", self.con_list[combobox_list_index]["list"].keys(), "9001;10;16;17;302;", '0')
        else:
            self.DisconnectRealData("0101")

    def deactivate_real(self): #체크돼있는데 조건검색 변경시 전의 실시간을 등록 해지 후 새로운 조건검색 인덱스로 실시간 등록
        combobox_list_index = self.cbox_con.currentText()[:3]
        if self.ckbox_real.isChecked():
            self.DisconnectRealData("0101")
            self.SetRealReg("0101", self.con_list[combobox_list_index]["list"].keys(), "9001;10;16;17;302;", '0')




    def order(self):
        try:
            accno = self.account_list.currentText()
            code = self.view_selec_coin_lbl.text()
            amt = self.order_amount.text()
            if amt == "":
                amt = 1

            ret = self.SendOrder(1, accno, code, amt)

            lm.logger.debug(ret)
        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())


    def order_sell(self):
        accno = self.account_list.currentText()
        code = self.view_selec_coin_lbl.text()#매도 테이블에서 골라야 함
        amt = self.order_amount_2.text()
        if amt == "":
            amt = 1

        ret = self.SendOrder(2, accno, code, amt)

        lm.logger.debug(ret)


    def update_jango(self):
        try:
            self.table_jango.setItem(0,0,QTableWidgetItem(self.jango["예수금"]))
            self.table_jango.setItem(1,0,QTableWidgetItem(self.jango["예수금D+1"]))
            self.table_jango.setItem(2,0,QTableWidgetItem(self.jango["예수금D+2"]))
            self.table_jango.setItem(3,0,QTableWidgetItem(self.jango["출금가능금액"]))
            self.table_jango.setItem(4,0,QTableWidgetItem(self.jango["주식매수총액"]))
            self.table_jango.setItem(5,0,QTableWidgetItem(self.jango["평가금액합계"]))
            self.table_jango.setItem(6,0,QTableWidgetItem(self.jango["미수확보금"]))
            self.table_jango.setItem(7,0,QTableWidgetItem(self.jango["현금미수금"]))

            self.table_maedo.setRowCount(len(self.jango["종목리스트"]))
            for i in range(len(self.jango["종목리스트"])):
                self.table_maedo.setItem(i, 0, QTableWidgetItem(self.jango["종목리스트"][i]["종목번호"]))
                self.table_maedo.setItem(i, 1, QTableWidgetItem(self.jango["종목리스트"][i]["종목명"]))
                self.table_maedo.setItem(i, 2, QTableWidgetItem(self.jango["종목리스트"][i]["현재가"]))
                self.table_maedo.setItem(i, 3, QTableWidgetItem(self.jango["종목리스트"][i]["매입금액"]))
                self.table_maedo.setItem(i, 4, QTableWidgetItem(self.jango["종목리스트"][i]["평가금액"]))

        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())

        #lm.logger.debug(self.jango)


class MyThread(QThread):
    def __init__(self):
        super().__init__()
        finished = pyqtSignal()

    def run(self):
        while True:
            if self.ckbox_real.isChecked():#실시간 체크 가격 update
                combobox_list_index = self.cbox_con.currentText()[:3]
                for i, j in self.recieved_dic.items():
                    if i in self.con_list[combobox_list_index]["list"]:
                        self.con_list[combobox_list_index]["list"][i] = int_format(j)
                self.finished.emit()

            time.sleep(1)


def ptr(val): #debug msg
    return lm.logger.debug(val)


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
        lm.logger.debug("예외가 발생했습니다. %s", e)
        lm.logger.debug(lm.traceback.format_exc())



if  __name__ == "__main__":
    lm.logger.debug("window start")
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()







