import sys
from PyQt5 import uic
from kw import Kiwoom
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel, QTableWidgetItem

main_ui = './ui/main.ui'
main_class = uic.loadUiType(main_ui)[0]

class MyWindow(QMainWindow, main_class): #param1 = windows : 창,  param2 = ui path

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btn1.clicked.connect(self.btn1_clicked_func)
        self.btn2.clicked.connect(self.con_search)
        self.cbox_con.activated.connect(self.con_search)
        self.get_info()


        pass

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

    def con_search(self, i):
        #print(kw.code_list[i])
        self.table_con.setRowCount(len(kw.code_list[i]))

        for j in range(len(kw.code_list[i])):
            self.table_con.setItem(j, 0, QTableWidgetItem(kw.code_list[i][j]))
            self.table_con.setItem(j, 1, QTableWidgetItem(kw.GetMasterCodeName(kw.code_list[i][j])))
            self.table_con.setItem(j, 3, QTableWidgetItem(str(kw.GetMasterLastPrice(kw.code_list[i][j]))))




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