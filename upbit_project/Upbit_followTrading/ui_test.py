from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QAction,
         QTableWidget,QTableWidgetItem,QVBoxLayout, QAbstractItemView)
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(50, 50, 700, 500))


        self.tableWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tableWidget.setSelectionBehavior(QAbstractItemView.SelectRows)

        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        #self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setStretchLastSection(False)


        #self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.setShowGrid(False)

#        self.tableWidget.setStyleSheet("background-color: black; selection-background-color: #353535; border-radius: 10px")
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setRowCount(0)

        data = [["Login", "Routine", "03/05/2019", "IP Address", "Yes"], ["Login", "Routine", "03/05/2019", "IP Address", "Yes"], ["Login", "Routine", "03/05/2019", "IP Address", "Yes"]]

        j=0
        for row in data:
            self.tableWidget.insertRow(j)
            j += 1
            i = 0
            for x in row:
                item = QTableWidgetItem(x)
                #item.setForeground(QBrush(QColor(255, 255, 255)))
                #item.setFont(font)
                self.tableWidget.setSortingEnabled(False)

                if(j == 1 and i <= 4):
                    self.tableWidget.insertColumn(i)
                self.tableWidget.setItem(j-1, i, QtWidgets.QTableWidgetItem(item))

                if (i == 4):
                    self.tableWidget.setColumnHidden(i, True);
                self.tableWidget.setSortingEnabled(True)

                i += 1

        self.tableWidget.horizontalHeader().resizeSection(0, 188)
        self.tableWidget.horizontalHeader().resizeSection(1, 155)
        self.tableWidget.horizontalHeader().resizeSection(2, 250)
        self.tableWidget.horizontalHeader().resizeSection(3, 66)
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        #self.tableWidget.horizontalHeader().setStretchLastSection(True)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))



if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet('QTableView::item {border-bottom: 1px solid #d6d9dc;}')
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())