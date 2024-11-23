#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : PySideFrameWork.py
@Time        : 2022/10/05 17:12:20
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
import sys
import smartflowui.Ui_DesignerFrameWork as uides


class myMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("mainwindow")
        self.resize(400, 300)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        # QHBoxLayout
        layout1 = QtWidgets.QVBoxLayout()
        layout.addLayout(layout1)

        testLabel = QtWidgets.QLabel("name")
        testLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        testLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                QtWidgets.QSizePolicy.Expanding)
        testLabel.setIndent(100)
        self.namelineEdit = QtWidgets.QLineEdit()
        self.namelineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)

        layout1.addWidget(testLabel)
        layout1.addWidget(self.namelineEdit)

        mainFrame = QtWidgets.QWidget()
        mainFrame.setLayout(layout)
        self.setCentralWidget(mainFrame)


class mywindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("window_test")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        # QHBoxLayout
        layout1 = QtWidgets.QVBoxLayout()
        layout.addLayout(layout1)

        testLabel = QtWidgets.QLabel("name")
        testLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        testLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                QtWidgets.QSizePolicy.Expanding)
        testLabel.setIndent(100)
        self.namelineEdit = QtWidgets.QLineEdit()
        self.namelineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)

        self.table = QtWidgets.QTableWidget()

        self.table.setRowCount(5)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ['Node', 'TypeName', 'Level', 'Is Publish'])
        nodeItem = QtWidgets.QTableWidgetItem("../node1")
        typeItem = QtWidgets.QTableWidgetItem("valar_test")
        levelItem = QtWidgets.QTableWidgetItem("1")
        publishItem = QtWidgets.QTableWidgetItem("0")

        self.table.setItem(0, 0, nodeItem)
        self.table.setItem(0, 1, typeItem)
        self.table.setItem(0, 2, levelItem)
        self.table.setItem(0, 3, publishItem)

        layout1.addWidget(testLabel)
        layout1.addWidget(self.namelineEdit)
        layout1.addWidget(self.table)

    def connectSigal(self):
        pass


class mywindowWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("mywindowWidget")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        # QHBoxLayout
        layout1 = QtWidgets.QVBoxLayout()
        layout.addLayout(layout1)

        testLabel = QtWidgets.QLabel("name")
        testLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        testLabel.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                QtWidgets.QSizePolicy.Expanding)
        testLabel.setIndent(100)
        self.namelineEdit = QtWidgets.QLineEdit()
        self.namelineEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)

        layout1.addWidget(testLabel)
        layout1.addWidget(self.namelineEdit)
        # mainFrame = QtWidgets.QWidget()
        # mainFrame.setLayout(layout)
        # self.setCentralWidget(mainFrame)


class mywindowDe(QtWidgets.QMainWindow, uides.Ui_MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setupUi(self)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    a = mywindow()
    a.show()
    # b = mywindowDe()
    # b.show()
    # c = myMainWindow()
    # c.show()
    # d = mywindowWidget()
    # d.show()
    sys.exit(app.exec_())
