import logging
import sys
from PyQt5 import uic
from kw import Kiwoom
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QTableWidgetItem
import log_manager as lm
from PyQt5.QtCore import *

main_ui = './ui/main.ui'
main_class = uic.loadUiType(main_ui)[0]

class MyWindow(QMainWindow, main_class): #param1 = windows : 창,  param2 = ui path

    def __init__(self):
        super().__init__()
        lm.logger.debug("window start")
        self.real = False
        self.setupUi(self)
        self.btn1.clicked.connect(self.btn1_clicked_func)
        self.btn2.clicked.connect(self.real_activate)
        self.pushButton.clicked.connect(self.order)
        self.pushButton_3.clicked.connect(self.order_sell)
        self.cbox_con.activated.connect(self.con_search)
        self.cbox_con.activated.connect(self.deactivate_real)
        self.ckbox_real.stateChanged.connect(self.real_activate)
        self.get_info()
        self.Thread1 = MyThread()
        self.Thread1.finished.connect(self.con_search)
        self.Thread1.start()
        self.con_search()

        #cell 선택 시
        self.table_con.cellClicked.connect(self.cell_cliked_func)
        pass

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

    def btn1_clicked_func(self):
        QMessageBox.information(self, 'check', 'clicked a btn')

    def btn2_clicked_func(self):
        QMessageBox.information(self, 'check', 'sec clicked a btn')

    def get_info(self):
        account_cnt = kw.GetLoginInfo("ACCOUNT_CNT")
        account_list = kw.GetLoginInfo("ACCLIST").split(';')[:-1]
        user_id = kw.GetLoginInfo("USER_ID")
        user_name = kw.GetLoginInfo("USER_NAME")
        sever = kw.GetLoginInfo("GetServerGubun")

        print(
            account_cnt,
            account_list,
            user_id,
            user_name,
            sever)

        self.name.setText(user_name)#이름 설정

        for i in account_list:
            self.cbox.addItem(i)#계좌 목록

        for i in kw.con_list:
            self.cbox_con.addItem(" ".join(i))#조건검색 목록

    @pyqtSlot()
    def con_search(self):
        combobox_list_index = self.cbox_con.currentIndex()
        if combobox_list_index == "": combobox_list_index = 0
        #print("con_search")
        #print(combobox_list_index)
        #print(kw.code_list[combobox_list_index])
        self.table_con.setRowCount(len(kw.code_list[combobox_list_index]))
        #print("len(kw.code_list[combobox_list_index])",len(kw.code_list[combobox_list_index]))
        tmp_index = 0
        for code_key in kw.code_list[combobox_list_index]:
            self.table_con.setItem(tmp_index, 0, QTableWidgetItem(code_key))
            self.table_con.setItem(tmp_index, 1, QTableWidgetItem(kw.GetMasterCodeName(code_key)))
            self.table_con.setItem(tmp_index, 2, QTableWidgetItem(kw.code_list[combobox_list_index][code_key]))
            self.table_con.setItem(tmp_index, 3, QTableWidgetItem(str(kw.GetMasterLastPrice(code_key).lstrip("0"))))
            #self.table_con.setItem(tmp_index, 4, QTableWidgetItem(str(tmp_index)))
            tmp_index += 1


    def real_activate(self):
        #print("real_activate")
        if self.ckbox_real.isChecked():
            #print(self.real)
            self.real = True
            kw.SetRealReg("0101", kw.code_list[self.cbox_con.currentIndex()].keys(), "9001;10;16;17;302;", '0')
            pass
        else:
            self.real = False
            kw.DisconnectRealData("0101")

    def deactivate_real(self):
        if self.ckbox_real.isChecked():
            self.ckbox_real.toggle()


    def order(self):
        accno = self.cbox.currentText()
        code = self.view_selec_coin_lbl.text()
        amt = self.order_amount.text()
        if amt == "":
            amt = 1

        ret = kw.SendOrder(1, accno, code, amt)

        print(ret)

    def order_sell(self):
        accno = self.cbox.currentText()
        code = self.view_selec_coin_lbl.text()#매도 테이블에서 골라야 함
        amt = self.order_amount_2.text()
        if amt == "":
            amt = 1

        ret = kw.SendOrder_sell(2, accno, code, amt)

        print(ret)


def int_format(val):
    if val[0] == '+' or val[0] == '-':
        return val[1:]
    else:
        return val

#aaaa
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtCore import QThread
import time
class MyThread(QThread):
    cnt = 0

    def __init__(self):
        super().__init__()
        finished = pyqtSignal()
    def run(self):
        while True:
            self.cnt = self.cnt + 1
            #print("running %d" % self.cnt)
            time.sleep(2)


            if kw.realcondition: #실시간 조건 변동 이벤트(편입,삭제)
                kw.realcondition = False
                myWindow.con_search(myWindow.cbox_con.currentIndex())
                self.finished.emit()
            if myWindow.real:#실시간 체크 가격 update
                for i, j in kw.recieved_dic.items():
                    #print(i, j)
                    if i in kw.code_list[myWindow.cbox_con.currentIndex()]:
                        kw.code_list[myWindow.cbox_con.currentIndex()][i] = int_format(j)
                self.finished.emit()






#aaaa



if  __name__ == "__main__":
    app = QApplication(sys.argv)
    kw = Kiwoom()
    kw.CommConnect()
    kw.SetConditionSearchFlag()
    kw.GetConditionLoad()
    for i in range(len(kw.con_list)):
        kw.SendCondition(i)
    #print(kw.code_list)

    myWindow = MyWindow()
    myWindow.show()
    app.exec_()