import logging
import sys
from PyQt5 import uic
from kw import Kiwoom
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QTableWidgetItem
import log_manager as lm

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
        self.cbox_con.activated.connect(self.con_search)
        self.cbox_con.activated.connect(self.deactivate_real)
        self.ckbox_real.stateChanged.connect(self.real_activate)
        self.get_info()
        self.Thread1 = MyThread()
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

    def con_search(self, i = 0):
        #print(kw.code_list[i])
        self.table_con.setRowCount(len(kw.code_list[i]))

        for j in range(len(kw.code_list[i])):
            self.table_con.setItem(j, 0, QTableWidgetItem(kw.code_list[i][j]))
            self.table_con.setItem(j, 1, QTableWidgetItem(kw.GetMasterCodeName(kw.code_list[i][j])))
            self.table_con.setItem(j, 2, None)
            self.table_con.setItem(j, 3, QTableWidgetItem(str(kw.GetMasterLastPrice(kw.code_list[i][j]))))

    def real_activate(self):
        #print("real_activate")
        if self.ckbox_real.isChecked():
            #print(self.real)
            self.real = True
            kw.SetRealReg("0101", kw.code_list[self.cbox_con.currentIndex()], "9001;10;16;17;302;", '0')
            pass
        else:
            self.real = False
            kw.DisconnectRealData("0101")

    def deactivate_real(self):
        if self.ckbox_real.isChecked():
            self.ckbox_real.toggle()

    def set_code_to_table(self, code, price):
        try:
            #print("set_code_to_table")
            for i in range(len(kw.code_list[self.cbox_con.currentIndex()])):
                #print(i)
                if code == kw.code_list[self.cbox_con.currentIndex()][i]:
                    #print("found")
                    self.table_con.setItem(i, 2, QTableWidgetItem(str(price)))
                    self.table_con.update()

        except Exception as e:
            lm.logger.debug(e)
            lm.logger.debug(lm.traceback.format_exc())



#aaaa
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QThread
import time
class MyThread(QThread):
    cnt = 0

    def __init__(self):
        super().__init__()
    def run(self):
        while True:
            self.cnt = self.cnt + 1
            #print("running %d" % self.cnt)
            time.sleep(0.5)
            #print(kw.coin_price_list)

            if kw.realcondition: #실시간 조건 변동 이벤트
                kw.realcondition = False
                myWindow.con_search(myWindow.cbox_con.currentIndex())

            if myWindow.real:
                try:
                    for i, j in kw.coin_price_list.items():
                        print(i, j)
                        myWindow.set_code_to_table(i, j)

                except:
                    print("error")
                    pass






#aaaa



if  __name__ == "__main__":
    app = QApplication(sys.argv)
    kw = Kiwoom()
    kw.CommConnect()
    kw.GetConditionLoad()
    for i in range(len(kw.con_list)):
        kw.SendCondition(i)
    #print(kw.code_list)

    myWindow = MyWindow()
    myWindow.show()
    app.exec_()