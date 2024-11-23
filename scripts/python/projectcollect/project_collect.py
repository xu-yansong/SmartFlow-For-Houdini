#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : project_collect.py
@Time        : 2022/11/13 11:13:51
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''
import json
import math
import os
import re
import shutil
import socket
import sys
import time
from functools import partial

import hou
import numpy as np
from PySide2 import QtCore, QtGui, QtWidgets

import cv2
import projectcollect.ui_rc

ICON_SIZE = hou.ui.scaledSize(30)
OK_ICON = hou.qt.Icon('TOP_status_cooked', ICON_SIZE, ICON_SIZE)
ERROR_ICON = hou.qt.Icon('STATUS_error', ICON_SIZE, ICON_SIZE)
WARNING_ICON = hou.qt.Icon('STATUS_error', ICON_SIZE, ICON_SIZE)
RELOAD_ICON = hou.qt.Icon('BUTTONS_reload', ICON_SIZE, ICON_SIZE)
CLEAR_ICON = hou.qt.Icon('BUTTONS_clear', ICON_SIZE, ICON_SIZE)
FILTER_ICON = hou.qt.Icon('BUTTONS_filter', ICON_SIZE, ICON_SIZE)
FILENOTFOUND = "filenotfound"


# houdini project info
class HoudiniPrj:
    def __init__(self):
        self.obj = hou.node("/obj")
        self.out = hou.node("/out")
        self.mat = hou.node("/mat")

        self.abcnodes = list()
        self.filenodes = list()
        self.cachenodes = list()
        self.lightnodes = list()
        self.matnodes = list()
        self.rendernodes = list()

        # self.abcinfos = list()
        # self.fileinfos = list()
        # self.cacheinfos = list()
        # self.textureinfos = list()
        # self.renderinfos = list()

        self.initAnalysisObj()

    # get file size
    def getFileSize(self, path):
        if os.path.exists(path):
            fsize = os.path.getsize(path)
            fsize = fsize/float(1024*1024)
            return str(round(fsize, 2)) + " M"
        else:
            return FILENOTFOUND

    # analysis obj node when init class instance
    def initAnalysisObj(self):
        for child in self.obj.allSubChildren(True, False):
            if child.type().name() == "alembic":
                self.abcnodes.append(child)
            elif child.type().name() == "file":
                if child.parent().type().name() == "cam":
                    continue
                self.filenodes.append(child)
            elif child.type().name() == "filecache::2.0":
                self.cachenodes.append(child)
            elif child.type().name() == "envlight":
                if child.parm("env_map").eval() != "":
                    self.lightnodes.append(child)

    # get all "file, abc" node path
    def getinputinfo(self):
        templist = list()
        for file in self.filenodes:
            info = dict()
            info['Node'] = file.path()
            info['Size'] = self.getFileSize(file.parm("file").eval())
            info['Type'] = "file"
            info['Path'] = file.parm("file").eval()
            templist.append(info)
        for file in self.abcnodes:
            info = dict()
            info['Node'] = file.path()
            info['Size'] = self.getFileSize(file.parm("fileName").eval())
            info['Type'] = "Alembic"
            info['Path'] = file.parm("fileName").eval()
            templist.append(info)
        return templist

    # get all "file cache " node path
    def getcacheinfo(self):
        templist = list()
        for file in self.cachenodes:
            info = dict()
            info['Node'] = file.path()
            info['Size'] = self.getFileSize(file.parm("sopoutput").eval())
            info['Type'] = "filecache"
            info['Path'] = file.parm("sopoutput").eval()
            templist.append(info)
        return templist

    # get all "texture" node path
    def gettextureinfo(self):
        templist = list()
        for file in self.lightnodes:
            info = dict()
            info['Node'] = file.path()
            info['Size'] = self.getFileSize(file.parm("env_map").eval())
            info['Type'] = "Env Map"
            info['Path'] = file.parm("env_map").eval()
            templist.append(info)
        return templist

    # get all "texture" node path
    def getrenderinfo(self):
        for child in self.out.allSubChildren(True, False):
            if child.type().name() == "ifd":
                self.renderseq.append(child)
        return self.renderinfos


# main manager
class PrjCollect(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(1400, 900)
        self.collectpath = None

        self.fileinfos = None
        self.cacheinfos = None
        self.textureinfos = None
        self.houdiniprj = HoudiniPrj()

        self.initMenber()
        self.initUI()

    # refresh
    def refreshtool(self):
        pass

    # choose collect path
    def updatescene(self):
        self.houdiniprj.initAnalysisObj()

    def choosePath(self):
        fname = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose Path")
        if fname:
            self.pathLineEdit.setText(fname)
            self.collectpath = fname

    # collect
    def makeCollect(self):
        path = self.pathLineEdit.text()
        if not os.path.exists(path):
            ok = QtWidgets.QMessageBox.warning(
                self, "warning", "当前选择的路径不存在，请提前创建...")
            return

    # collect path change
    def pathChanged(self):
        self.collectpath = self.pathLineEdit.text()

    # home to node
    def homeToNode(self, path):
        desnode = hou.node(path)
        plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)

        hou.clearAllSelected()
        desnode.setSelected(1)
        plane.homeToSelection()

    # show .hip asset in explorer
    def _showinexplorer(self, path):
        if os.path.exists(path):
            os.startfile(path)

    # _assetcell
    def _assetcell(self, label, text, infodict):
        if label != "Size":
            assetpath = infodict['Node']
            assetfolder = os.path.dirname(infodict['Path'])
            cell_frame = QtWidgets.QWidget()
            cell_layout = QtWidgets.QHBoxLayout()
            cell_layout.setContentsMargins(2, 2, 0, 0)
            cell_frame.setLayout(cell_layout)
            self._textLabel = QtWidgets.QLabel(text)
            # add to layout
            cell_layout.addWidget(self._textLabel)
            # add right click menu
            cell_frame.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

            # 定位到节点
            newscene = QtWidgets.QAction(cell_frame)
            newscene.setText("Home To Node")
            newscene.triggered.connect(partial(self.homeToNode, assetpath))
            cell_frame.addAction(newscene)

            # open
            openscene = QtWidgets.QAction(cell_frame)
            openscene.setText("Show in Explorer")
            openscene.triggered.connect(
                partial(self._showinexplorer, assetfolder))
            cell_frame.addAction(openscene)

            # mark
            markAsset = QtWidgets.QAction(cell_frame)
            markAsset.setText("Mark As Favorite")
            # markAsset.triggered.connect(partial(self._markAsFavorite, assetfolder))
            cell_frame.addAction(markAsset)
            # return
            return True, cell_frame
        else:
            if text != FILENOTFOUND:
                item = QtWidgets.QTableWidgetItem(
                    OK_ICON, text)
            else:
                item = QtWidgets.QTableWidgetItem(
                    ERROR_ICON, "missing")
            return False, item

    def updatefileTable(self, infos, widget):
        row = len(infos)
        if row:
            headerlabel = [x for x in infos[0].keys()]
            col = len(headerlabel)
            widget.clear()
            widget.setRowCount(row)
            widget.setColumnCount(col)
            widget.setHorizontalHeaderLabels(headerlabel)

            for i in range(row):
                for j in range(col):
                    label = headerlabel[j]
                    text = infos[i][headerlabel[j]]
                    ok, newcell = self._assetcell(label, text, infos[i])
                    if ok:
                        widget.setCellWidget(i, j, newcell)
                    else:
                        widget.setItem(i, j, newcell)
            widget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            widget.resizeColumnsToContents()
    # init menber

    def initMenber(self):
        self.fileinfos = self.houdiniprj.getinputinfo()
        self.cacheinfos = self.houdiniprj.getcacheinfo()
        self.textureinfos = self.houdiniprj.gettextureinfo()

    # init parameter
    def initParameter(self):
        defaultpath = os.path.dirname(hou.hipFile.path()) + "/Collect/"
        self.pathLineEdit.setText(defaultpath)
        self.updatefileTable(self.fileinfos, self.inputModelTable)
        self.updatefileTable(self.cacheinfos, self.cacheTable)
        self.updatefileTable(self.textureinfos, self.textureTable)

    # connect signals
    def connectSignals(self):
        self.refreshBtn.clicked.connect(self.refreshtool)
        self.pathBtn.clicked.connect(self.choosePath)
        self.pathLineEdit.textChanged.connect(self.pathChanged)

        self.collectBtn.clicked.connect(self.makeCollect)

    # initUI
    def initUI(self):
        self.setWindowTitle("Project Collection Tools")
        self.setWindowIcon(hou.qt.Icon("SOP_vellumio", ICON_SIZE, ICON_SIZE))
        widget = QtWidgets.QWidget()
        self.setCentralWidget(widget)
        baselayout = QtWidgets.QVBoxLayout()
        widget.setLayout(baselayout)

        # 获取菜单栏 menuBar
        bar = self.menuBar()
        # file menuBar
        file_menu = bar.addMenu('File')
        self.importassetButton = file_menu.addAction('Open')

        # Edit menuBar
        edit_menu = bar.addMenu('Edit')
        self.pluginsetting = edit_menu.addAction('setting')

        # View menuBar
        view_menu = bar.addMenu('View')
        self.reloadButton = view_menu.addAction('Reload')

        # Help menuBar
        help_menu = bar.addMenu('Help')
        self.helpmenu = help_menu.addAction('Show Help')

        # title logo
        logoLabel = QtWidgets.QLabel("Project Collection Tools")
        logoLabel.setStyleSheet(u"background-image: url(:/titlebg/Icons/importTitle.jpg);\n"
                                "color: rgb(255, 200, 100);")
        logoLabel.setFixedHeight(100)
        logoLabel.setAlignment(QtCore.Qt.AlignCenter)
        logoLabel.setFont(QtGui.QFont(u"\u5fae\u8f6f\u96c5\u9ed1", 20))
        baselayout.addWidget(logoLabel)

        # collect path
        collectlayout = QtWidgets.QHBoxLayout()
        baselayout.addLayout(collectlayout)

        pathLabel = QtWidgets.QLabel("Collect Path")
        self.pathLineEdit = QtWidgets.QLineEdit()
        self.pathLineEdit.setToolTip("the path to collect...")
        self.pathBtn = QtWidgets.QPushButton()
        self.pathBtn.setIcon(
            hou.qt.Icon('BUTTONS_chooser_folder', ICON_SIZE, ICON_SIZE))
        self.pathBtn.setFixedWidth(30)

        collectlayout.addWidget(pathLabel)
        collectlayout.addWidget(self.pathLineEdit)
        collectlayout.addWidget(self.pathBtn)

        # functio button layout
        funclayout = QtWidgets.QHBoxLayout()
        funclayout.setAlignment(QtCore.Qt.AlignLeft)
        baselayout.addLayout(funclayout)

        self.refreshBtn = QtWidgets.QPushButton("Refresh")
        self.refreshBtn.setFixedWidth(80)
        self.refreshBtn.setFixedHeight(30)
        self.refreshBtn.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        funclayout.addWidget(self.refreshBtn)

        # splitter group
        splittercontainer = QtWidgets.QSplitter(QtGui.Qt.Horizontal)
        splittercontainer.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                        QtWidgets.QSizePolicy.Preferred)
        baselayout.addWidget(splittercontainer)

        # -------------- input widget
        inputmodelwidget = QtWidgets.QWidget()
        inputmodellayout = QtWidgets.QVBoxLayout()
        inputmodelwidget.setLayout(inputmodellayout)
        splittercontainer.addWidget(inputmodelwidget)
        # label
        inputmodellabel = QtWidgets.QLabel("Input Models")
        inputmodellayout.addWidget(inputmodellabel)
        # tablewidget
        self.inputModelTable = QtWidgets.QTableWidget()
        self.inputModelTable.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.inputModelTable.resizeColumnsToContents()
        inputmodellayout.addWidget(self.inputModelTable)
        # -------------- cache widget
        cachewidget = QtWidgets.QWidget()
        cachelayout = QtWidgets.QVBoxLayout()
        cachewidget.setLayout(cachelayout)
        splittercontainer.addWidget(cachewidget)

        # label
        cachelabel = QtWidgets.QLabel("Cache")
        cachelayout.addWidget(cachelabel)
        # tablewidget
        self.cacheTable = QtWidgets.QTableWidget()
        self.cacheTable.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        self.cacheTable.resizeColumnsToContents()
        cachelayout.addWidget(self.cacheTable)

        # -------------- texture widget
        texturewidget = QtWidgets.QWidget()
        texturelayout = QtWidgets.QVBoxLayout()
        texturewidget.setLayout(texturelayout)
        splittercontainer.addWidget(texturewidget)
        # label
        texturelabel = QtWidgets.QLabel("Textures")
        texturelayout.addWidget(texturelabel)
        # tablewidget
        self.textureTable = QtWidgets.QTableWidget()
        self.textureTable = QtWidgets.QTableWidget()
        self.textureTable.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows)
        texturelayout.addWidget(self.textureTable)

        # Collecting...
        buttonlayout = QtWidgets.QHBoxLayout()
        baselayout.addSpacing(10)
        baselayout.addLayout(buttonlayout)
        horizontalSpacer = QtWidgets.QSpacerItem(
            hou.ui.scaledSize(100), 0, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Fixed)

        self.collectBtn = QtWidgets.QPushButton("Collect")
        self.collectBtn.setFixedHeight(50)
        self.collectBtn.setMinimumWidth(100)
        self.collectBtn.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                      QtWidgets.QSizePolicy.Fixed)
        buttonlayout.addItem(horizontalSpacer)
        buttonlayout.addWidget(self.collectBtn)
        # init
        self.initParameter()
        self.connectSignals()


def initWindow():
    import hou
    win = PrjCollect(hou.qt.mainWindow())
    win.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = PrjCollect()
    win.show()
    sys.exit(app.exec_())
