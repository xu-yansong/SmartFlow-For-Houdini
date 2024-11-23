# -*- coding: utf-8 -*-

################################################################################
# Form generated from reading UI file 'SmartFlow_Asset_Publish.ui'
##
# Created by: Qt User Interface Compiler version 5.15.2
##
# WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):

    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setAutoFillBackground(False)
        self.horizontalLayout = QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.radioButton = QRadioButton(self.centralwidget)
        self.radioButton.setObjectName(u"radioButton")

        self.horizontalLayout.addWidget(self.radioButton)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")
        self.label.setAutoFillBackground(False)
        self.label.setStyleSheet(
            u"background-image: url(:/bg/IMG_1028(1).JPG);")

        self.horizontalLayout.addWidget(self.label)

        self.checkBox = QCheckBox(self.centralwidget)
        self.checkBox.setObjectName(u"checkBox")

        self.horizontalLayout.addWidget(self.checkBox)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 800, 23))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)

    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(
            QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.radioButton.setText(
            QCoreApplication.translate("MainWindow", u"RadioButton", None))
        self.label.setText(
            QCoreApplication.translate("MainWindow", u"TextLabel", None))
        self.checkBox.setText(
            QCoreApplication.translate("MainWindow", u"CheckBox", None))

    # retranslateUi
