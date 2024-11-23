#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : testwin.py
@Time        : 2022/11/13 22:51:00
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
import sys


class DemoWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.initUI()

    def initUI(self):
        self.setWindowTitle("Vedio")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        table = QtWidgets.QTableWidget()
        layout.addWidget(table)
        item = QtWidgets.QTableWidgetItem()
        table.


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = DemoWidget()
    win.show()
    sys.exit(app.exec_())
