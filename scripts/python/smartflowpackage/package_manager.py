#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : smartflow_package_manager.py
@Time        : 2022/10/22 14:21:16
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import hou
import os


class PackageManager(QtWidgets.QFrame):

    _ICON_SIZE = 18

    def __init__(self, parent=None):
        super().__init__(parent)

        # self parameter
        self.path = None

        self.initMembers()
        self.initUI()

    def initParameters(self):
        filepath = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        self.path = "/".join(filepath.split("/")[:-3]) + "/otls/"
        self.initPackageTree()
        pass

    def initMembers(self):
        pass

    def getfolder(self, path, root):
        filelist = list()
        for each in os.listdir(path):
            file = path + "/" + each
            if os.path.isdir(file):
                child = QtWidgets.QTreeWidgetItem(root)
                child.setText(0, each)
                child.setIcon(0, hou.qt.Icon('SOP_subnet', self._ICON_SIZE, self._ICON_SIZE))
                child.setCheckState(0, QtCore.Qt.Unchecked)
                self.getfolder(file, child)

            if os.path.isfile(file):
                ext = os.path.splitext(os.path.split(file)[1])[1]
                if ext == ".hda" or ext == ".otl":
                    filelist.append(each)

        for eachfile in filelist:
            child = QtWidgets.QTreeWidgetItem(root)
            child.setText(0, eachfile)
            child.setCheckState(0, QtCore.Qt.Unchecked)
            child.setIcon(0, hou.qt.Icon('opdef:/labs::Sop/spiral::1.1?IconSVG', self._ICON_SIZE, self._ICON_SIZE))

    def initPackageTree(self):
        packageroot = QtWidgets.QTreeWidgetItem(self.tree)
        packageroot.setText(0, self.path)
        packageroot.setCheckState(0, QtCore.Qt.Unchecked)

        self.getfolder(self.path, packageroot)
        pass

    # 获取当前节点的路径
    def getpath(self, item):
        pathlist = list()
        name = item.text(0)
        pathlist.append(name)

        while item.parent() is not None:
            item = item.parent()
            pathlist.insert(0, item.text(0))
        path = "/".join(pathlist)
        return path

    # check state event
    def handleChanged(self, item, column):
        path = self.getpath(item)
        count = item.childCount()
        if item.checkState(column) == QtGui.Qt.Checked:
            # 安装
            if os.path.isfile(path):
                hou.hda.installFile(path)
                print("install hda : {}\n".format(item.text(0)))
            # 设置子目录状态
            for i in range(count):
                item.child(i).setCheckState(0, QtGui.Qt.Checked)

        if item.checkState(column) == QtGui.Qt.Unchecked:
            # 卸载
            if os.path.isfile(path):
                hou.hda.uninstallFile(path)
                print("uninstall hda : {}\n".format(item.text(0)))
            for i in range(count):
                item.child(i).setCheckState(0, QtGui.Qt.Unchecked)

    # init ui
    def initUI(self):

        # base layout
        baselayout = QtWidgets.QVBoxLayout()
        self.setLayout(baselayout)
        self.setProperty("houdiniStyle", True)

        # file system
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setColumnCount(1)
        self.tree.setHeaderLabels(["Package View"])
        # self.treeroot = QtWidgets.QTreeWidgetItem(self.tree)
        # self.treeroot.setText(0,"Package List")
        baselayout.addWidget(self.tree)

        # # 获取系统文件
        # self.model_folder = QtWidgets.QFileSystemModel()
        # self.model_folder.setRootPath(self.path)
        # #self.model_folder.setFilter(QtCore.QDir.Dirs|QtCore.QDir.NoDotAndDotDot)

        # # 创建文件列表目录
        # self.folderList = QtWidgets.QTreeView()
        # self.folderList.setModel(self.model_folder)
        # self.folderList.setRootIndex(self.model_folder.index(self.path))
        # baselayout.addWidget(self.folderList)

        # init
        self.initParameters()

        # signal
        self.tree.itemChanged.connect(self.handleChanged)
