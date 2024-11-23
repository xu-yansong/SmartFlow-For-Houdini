#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : resource_manager_main.py
@Time        : 2022/10/26 19:33:47
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
import sys
import os
import hou
import time
import socket
import json
import shutil
import cv2
import numpy as np
from functools import partial
import math
import re

ICON_SIZE = hou.ui.scaledSize(30)
ERROR_ICON = hou.qt.Icon('STATUS_error', ICON_SIZE, ICON_SIZE)
WARNING_ICON = hou.qt.Icon('STATUS_error', ICON_SIZE, ICON_SIZE)
RELOAD_ICON = hou.qt.Icon('BUTTONS_reload', ICON_SIZE, ICON_SIZE)
CLEAR_ICON = hou.qt.Icon('BUTTONS_clear', ICON_SIZE, ICON_SIZE)
FILTER_ICON = hou.qt.Icon('BUTTONS_filter', ICON_SIZE, ICON_SIZE)

SIZE4 = hou.ui.scaledSize(4)
SIZE16 = hou.ui.scaledSize(16)
SIZE26 = hou.ui.scaledSize(26)
SIZE28 = hou.ui.scaledSize(28)
SIZE30 = hou.ui.scaledSize(30)
SIZE32 = hou.ui.scaledSize(32)
BTN_SIZE = SIZE16

MARGIN4 = QtCore.QMargins(4, 4, 4, 4)

ROOTFOLDER = 0
CATEGORYFOLDER = 1
TYPEFOLDER = 2


# import asset
class importDiaglog(QtWidgets.QDialog):

    def __init__(self,
                 parent,
                 libpath,
                 categoryindex=0,
                 typenameindex=0,
                 setdefault=False):
        super(importDiaglog, self).__init__(parent)

        self.setWindowFlags(self.windowFlags()
                            ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle(" Asset Import Setting")
        self.setWindowIcon(hou.qt.Icon('LOP_sceneimport', ICON_SIZE,
                                       ICON_SIZE))
        self.libpath = libpath
        self.config = self.libpath + "/assetdatas.json"
        self.typelists = list()
        self.categotylists = dict()
        self.setdefault = setdefault
        self.categoryindex = categoryindex
        self.typenameindex = typenameindex
        self.hippath = None
        self.thumbpath = None
        self.typename = None
        self.category = None
        self.assetname = None
        self.houdiniversion = None
        self.Author = None
        self.createData = None
        self.urlpath = None
        # init menber
        self.initmenber()
        # init ui
        self.initUI()

    # updata library json data
    def updatalibjson(self):
        pass

    # convert preview image to .jpg
    def convertJpg(self, img):
        img2 = cv2.imread(img, cv2.IMREAD_UNCHANGED)
        name, ext = os.path.splitext(img)
        jpgpath = name + ".jpg"
        if ext == ".exr":
            # im_gamma_correct = np.clip(np.power(img2, 0.45), 0, 1)
            # im_fixed = img2.fromarray(np.uint8(im_gamma_correct * 255))
            img2 *= 65535
            img2[img2 > 65535] = 65535
            # img2 = np.uint16(img2)
            img2 = np.uint16(np.power(img2, 0.5))

        cv2.imwrite(jpgpath, img2, [cv2.IMWRITE_JPEG_QUALITY, 100])
        return jpgpath

    def gettypelist(self):
        with open(self.config, "r", encoding="utf-8") as f:
            self.categotylists = json.load(f)['typeinfo']
            for key in self.categotylists.keys():
                self.typelists.append(key)

    def loadhip(self):
        fname = QtWidgets.QFileDialog.getOpenFileName(self, "Open File",
                                                      "E:/test", "*.hip")
        if fname[0]:
            self.pathlineEdit.setText(fname[0])

    # load thumbnail
    def loadThumbnail(self):

        if self.pathlineEdit.text() != None:
            path = self.pathlineEdit.text()
        else:
            path = "."
        fname = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", path,
                                                      "*")
        thumbpath = fname[0]

        if thumbpath:
            ext = os.path.splitext(os.path.basename(thumbpath))[1]
            if ext != ".jpg":
                thumbpath = self.convertJpg(thumbpath)
            self.ThumbnaillineEdit.setText(thumbpath)
            img = QtGui.QImage(thumbpath)
            img = img.scaled(self.previewlabel.width(),
                             self.previewlabel.height(),
                             QtGui.Qt.KeepAspectRatioByExpanding,
                             QtGui.Qt.SmoothTransformation)

            self.previewlabel.setPixmap(QtGui.QPixmap(img))

    # define event when file path changed
    def pathChanged(self):
        hipfilepath = self.pathlineEdit.text()
        # print(hipfilepath)
        if os.path.exists(hipfilepath):
            hipname = os.path.splitext(os.path.basename(hipfilepath))[0]
            self.namelineEdit.setText(hipname.split(".")[0])
            createData = time.ctime(os.path.getmtime(hipfilepath))
            self.createlineEdit.setText(createData)
            filebytes = hou.readFile(hipfilepath).split("\n")
            for eachline in filebytes:
                if eachline.find('_HIP_SAVEVERSION') >= 0:
                    houdiniversion = eachline.split("=")[1].strip()
                    self.verlineEdit.setText(houdiniversion)
                    break
        # updata preview labl
        self.previewlibpath()

    # name changed
    def nameChanged(self):
        # updata preview labl
        self.previewlibpath()

    # type change
    def typeChanged(self):
        typename = self.typecomboBox.currentText()
        self.categorycomboBox.clear()
        self.categorycomboBox.addItems(self.categotylists[typename])
        # updata preview labl
        self.previewlibpath()

    # category change
    def categoryChanged(self):

        self.previewlibpath()

    # preview lib path
    def previewlibpath(self):
        self.typename = self.typecomboBox.currentText()
        self.categoryname = self.categorycomboBox.currentText()
        self.assetname = self.namelineEdit.text()
        path = self.libpath + "/" + self.typename + "/" + \
            self.categoryname + "/" + self.assetname + "/"

        self.liblineEdit.setText(path)

    # import asset
    def importAsset(self):
        self.hippath = self.pathlineEdit.text()
        self.thumbpath = self.ThumbnaillineEdit.text()
        self.typename = self.typecomboBox.currentText()
        self.categoryname = self.categorycomboBox.currentText()
        self.assetname = self.namelineEdit.text()
        self.houdiniversion = self.verlineEdit.text()
        self.Author = self.authorlineEdit.text()
        self.createData = self.createlineEdit.text()
        self.urlpath = self.urllineEdit.text()

        # check hip file path
        if self.hippath == "" or self.hippath == None or not os.path.exists(
                self.hippath):
            print("current hip file not valid... re - choose please...")
            return
        # check thumbnail
        if not os.path.exists(self.thumbpath) or self.thumbpath == "":
            print("thumbnail map not valid...")
            return

        assetinfo = dict()

        assetinfo['type'] = self.typename
        assetinfo['category'] = self.categoryname
        assetinfo['Assetname'] = self.assetname
        assetinfo['houdiniversion'] = self.houdiniversion
        assetinfo['Author'] = self.Author
        assetinfo['createData'] = self.createData
        assetinfo['urlpath'] = self.urlpath

        assetpath = self.libpath + "/" + self.typename + \
            "/" + self.categoryname + "/" + self.assetname
        if os.path.exists(assetpath):
            print("Asset already exists,rename asset name first ...")
            # return
        else:
            os.makedirs(assetpath)
        # copy hipfile and thumbnail picture
        # try:
        newhippath = assetpath + "/" + self.assetname + ".hip"
        shutil.copyfile(self.hippath, newhippath)
        newthumbpath = assetpath + "/" + self.assetname + ".jpg"
        shutil.copyfile(self.thumbpath, newthumbpath)
        # except:
        #     pass
        assetinfo[
            'hippath'] = self.typename + "/" + self.categoryname + "/" + self.assetname + "/" + self.assetname + ".hip"
        assetinfo[
            'thumbpath'] = self.typename + "/" + self.categoryname + "/" + self.assetname + "/" + self.assetname + ".jpg"
        with open(assetpath + "/assetinfo.json", "w", encoding="utf-8") as f:
            json.dump(assetinfo, f, indent=4)
        # updata json
        self.updatalibjson()
        # final
        # os.startfile(assetpath)
        print('{0} import successful...'.format(self.assetname))
        self.close()

    # connect signals
    def connectSignals(self):
        self.pathbutton.clicked.connect(self.loadhip)
        self.pathlineEdit.textChanged.connect(self.pathChanged)

        self.Thumbnailbutton.clicked.connect(self.loadThumbnail)

        self.typecomboBox.currentIndexChanged.connect(self.typeChanged)
        self.categorycomboBox.currentIndexChanged.connect(self.categoryChanged)
        # asset name
        self.namelineEdit.textChanged.connect(self.nameChanged)
        # import button
        self.importButton.clicked.connect(self.importAsset)

    # init menber
    def initmenber(self):
        self.gettypelist()

    # init parameter
    def initparameter(self):
        self.authorlineEdit.setText(socket.gethostname())

        self.typecomboBox.addItems(self.typelists)
        if self.setdefault:
            self.typecomboBox.setCurrentIndex(self.categoryindex)

        typename = self.typecomboBox.currentText()
        self.categorycomboBox.clear()
        self.categorycomboBox.addItems(self.categotylists[typename])
        if self.setdefault:
            self.categorycomboBox.setCurrentIndex(self.typenameindex)

    # init UI
    def initUI(self):
        # base layout
        baselayout = QtWidgets.QVBoxLayout()
        self.setLayout(baselayout)

        headerlabel = QtWidgets.QLabel("IMPORT SETTING")
        headerlabel.setFixedHeight(80)
        baselayout.addWidget(headerlabel)
        infolayout = QtWidgets.QGridLayout()
        baselayout.addLayout(infolayout)
        # file path
        pathlabel = QtWidgets.QLabel("HIP Path ")
        self.pathlineEdit = QtWidgets.QLineEdit()
        self.pathlineEdit.setToolTip('choose the houdini file ')
        self.pathbutton = QtWidgets.QPushButton()
        self.pathbutton.setIcon(
            hou.qt.Icon('BUTTONS_chooser_folder', ICON_SIZE, ICON_SIZE))
        self.pathbutton.setFixedWidth(30)
        infolayout.addWidget(pathlabel, 0, 0)
        infolayout.addWidget(self.pathlineEdit, 0, 1)
        infolayout.addWidget(self.pathbutton, 0, 2)

        # Thumbnail
        Thumbnaillabel = QtWidgets.QLabel("Thumbnail Path ")
        self.ThumbnaillineEdit = QtWidgets.QLineEdit()
        self.ThumbnaillineEdit.setToolTip('choose the Thumbnail file ')
        self.Thumbnailbutton = QtWidgets.QPushButton()
        self.Thumbnailbutton.setIcon(
            hou.qt.Icon('BUTTONS_chooser_folder', ICON_SIZE, ICON_SIZE))
        self.Thumbnailbutton.setFixedWidth(30)

        infolayout.addWidget(Thumbnaillabel, 1, 0)
        infolayout.addWidget(self.ThumbnaillineEdit, 1, 1)
        infolayout.addWidget(self.Thumbnailbutton, 1, 2)
        # type
        typelabel = QtWidgets.QLabel("Type ")
        self.typecomboBox = QtWidgets.QComboBox()

        infolayout.addWidget(typelabel, 2, 0)
        infolayout.addWidget(self.typecomboBox, 2, 1)

        # category
        categorylabel = QtWidgets.QLabel("Category ")
        self.categorycomboBox = QtWidgets.QComboBox()

        infolayout.addWidget(categorylabel, 3, 0)
        infolayout.addWidget(self.categorycomboBox, 3, 1)
        # name
        namelabel = QtWidgets.QLabel("Asset Name ")
        self.namelineEdit = QtWidgets.QLineEdit()

        infolayout.addWidget(namelabel, 4, 0)
        infolayout.addWidget(self.namelineEdit, 4, 1)

        # version
        verlabel = QtWidgets.QLabel("Houdini Version ")
        self.verlineEdit = QtWidgets.QLineEdit("")

        infolayout.addWidget(verlabel, 5, 0)
        infolayout.addWidget(self.verlineEdit, 5, 1)

        # author
        authorlabel = QtWidgets.QLabel("Author ")
        self.authorlineEdit = QtWidgets.QLineEdit("")

        infolayout.addWidget(authorlabel, 6, 0)
        infolayout.addWidget(self.authorlineEdit, 6, 1)

        # create data
        createlabel = QtWidgets.QLabel("Created Data ")
        self.createlineEdit = QtWidgets.QLineEdit()
        infolayout.addWidget(createlabel, 7, 0)
        infolayout.addWidget(self.createlineEdit, 7, 1)

        # url path
        urllabel = QtWidgets.QLabel("Url Link")
        self.urllineEdit = QtWidgets.QLineEdit()
        infolayout.addWidget(urllabel, 8, 0)
        infolayout.addWidget(self.urllineEdit, 8, 1)

        # asset path preview
        liblabel = QtWidgets.QLabel("Lib Path Preview")
        self.liblineEdit = QtWidgets.QLabel()
        self.liblineEdit.setFocusPolicy(QtCore.Qt.NoFocus)
        infolayout.addWidget(liblabel, 9, 0)
        infolayout.addWidget(self.liblineEdit, 9, 1)

        # thumbnail label
        imgpreviewlabel = QtWidgets.QLabel("Preview ")
        self.previewlabel = QtWidgets.QLabel()
        self.previewlabel.setFixedWidth(384)  # 384
        self.previewlabel.setFixedHeight(216)  # 216
        self.previewlabel.setAlignment(QtGui.Qt.AlignCenter)

        infolayout.addWidget(imgpreviewlabel, 10, 0)
        infolayout.addWidget(self.previewlabel, 10, 1)

        # import button
        buttonlayout = QtWidgets.QHBoxLayout()
        # h_line = QtWidgets.QFrame()
        # h_line.setFrameShape(QtWidgets.QFrame.VLine)
        # h_line.setFrameShadow(QtWidgets.QFrame.Sunken)
        # baselayout.addWidget(h_line)
        baselayout.addSpacing(30)
        baselayout.addLayout(buttonlayout)

        horizontalSpacer = QtWidgets.QSpacerItem(
            hou.ui.scaledSize(100), 0, QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding)

        self.importButton = QtWidgets.QPushButton('IMPORT')
        self.importButton.setFixedHeight(50)
        self.importButton.setMinimumWidth(100)
        self.importButton.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                        QtWidgets.QSizePolicy.Expanding)

        buttonlayout.addItem(horizontalSpacer)
        buttonlayout.addWidget(self.importButton)

        baselayout.addStretch(1)
        # init
        self.initparameter()
        self.connectSignals()


# main manager
class ResManager(QtWidgets.QMainWindow):

    _Default_Catagory = {
        "typeinfo": {
            "VFX": ["Explosion", "Fire", "Flip", "Smoke", "Particle", "RBD"],
            "PCG": ["Biome", "Road", "Rock", "Terrain"],
            "Render": ["Water", "Particle", "Pyro", "Cloud"]
        }
    }
    _instance = None
    _init_flag = True

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kw)
            return cls._instance

    def __init__(self, parent=None):
        if self._init_flag:
            super(ResManager, self).__init__(parent)
            self.resize(1280, 720)
            self.libPath = ""
            self.categorypath = ""
            self.assetDatajson = ""
            self.iconscale = 0.75
            self.categotylists = dict()
            self.tableroot = None
            self.initmenber()
            self.initUI()
            self._init_flag = False

    # generate config json file
    def generateconfig(self, path, value, select=True):
        if select:
            ok = QtWidgets.QMessageBox.warning(
                self, "Warning", "首次配置需要指定一个仓库路径",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.Yes)
            if ok == QtWidgets.QMessageBox.Yes:
                libpath = QtWidgets.QFileDialog.getExistingDirectory(
                    self, "Select Your Library Path...")
            else:
                libpath = value
        else:
            libpath = value

        if libpath:
            config = dict()
            config['path'] = libpath
            if not os.path.exists(os.path.dirname(path)):
                os.mkdir(os.path.dirname(path))
            with open(path, "w", encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return libpath
        return None

    # init library
    def initlibrary(self):
        configpath = hou.homeHoudiniDirectory() + "/smartflow/config.json"
        if not os.path.exists(configpath):
            libpath = self.generateconfig(configpath, None)
            if libpath:
                self.libPath = libpath
        else:
            try:
                with open(configpath, "r", encoding='utf-8') as f:
                    libpath = json.load(f)['path']
                    if os.path.exists(libpath):
                        self.libPath = libpath
            except:
                path = self.generateconfig(configpath, None)
                if path:
                    self.libPath = path
        return self.libPath

    # get file category from os
    def getCategory(self):
        try:
            with open(self.assetDatajson, "r", encoding="utf-8") as f:
                self.categotylists = json.load(f)['typeinfo']
            return True
        except:
            QtWidgets.QMessageBox.warning(self, "警告", "未找到配位文件，使用工具自带分类...")
            self.reloadPlugin()
            return False

    # set categoty
    def setCategory(self):

        self.tableOfContent.clear()
        self.tableroot = QtWidgets.QTreeWidgetItem(self.tableOfContent)
        self.tableroot.setText(0, "Home")
        self.tableOfContent.setCurrentItem(self.tableroot)

        res = self.getCategory()
        if res:
            for each in self.categotylists.keys():
                child = QtWidgets.QTreeWidgetItem(self.tableroot)
                child.setText(0, each)
                for each2 in self.categotylists[each]:
                    child2 = QtWidgets.QTreeWidgetItem(child)
                    child2.setText(0, each2)
            self.tableOfContent.expandAll()

    # load config
    def loadconfig(self):
        self.libpathlineedit.setText(self.libPath)
        self.assetDatajson = self.libPath + "/" + "assetdatas.json"
        self.setCategory()

        assetlists = self.getassetlist(self.libPath, ROOTFOLDER, None)
        self.displayAsset(assetlists)

    # importasset
    def importAsset(self):
        if os.path.exists(self.libPath):
            item = self.tableOfContent.currentItem()
            if item.parent() == None or item.parent().parent() == None:
                w = importDiaglog(hou.qt.mainWindow(), self.libPath)
                w.show()
            else:
                categoryname = item.parent().text(0)
                typename = item.text(0)

                with open(self.assetDatajson, "r", encoding="utf-8") as f:
                    datas = json.load(f)['typeinfo']
                keys = [x for x in datas.keys()]
                categoryindex = keys.index(categoryname)
                typeindex = datas[categoryname].index(typename)
                w = importDiaglog(hou.qt.mainWindow(), self.libPath,
                                  categoryindex, typeindex, True)
                w.show()
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "未正确配仓库路径...")

    # reload plugin
    def reloadPlugin(self):
        currentlib = self.libpathlineedit.text()
        if not os.path.exists(currentlib):
            QtWidgets.QMessageBox.warning(self, "警告", "当前指定的仓库路径不存在...")
            self.tableOfContent.clear()
            self.filetable.clear()
            return
        configpath = hou.homeHoudiniDirectory() + "/smartflow/config.json"
        with open(configpath, "r", encoding='utf-8') as f:
            libpath = json.load(f)['path']
        self.libPath = libpath
        self.libpathlineedit.setText(libpath)

        self.libpathchanged()

    # open plugin setting
    def openpluginsetting(self):
        print("TODO")

    def openhelp(self):
        print("TODO")

    def sortdata(self, data):
        newdata = dict()
        for key in sorted(data.keys()):
            newdata[key] = data[key]
        return newdata

    # add Category
    def addCategory(self):

        currentitem = self.tableOfContent.currentItem()
        with open(self.assetDatajson, "r", encoding="utf-8") as f:
            assetdata = json.load(f)
            typeinfo = assetdata['typeinfo']
        if currentitem.parent() == None:
            text, ok = QtWidgets.QInputDialog.getText(self, '新增分类', '类名')
            if ok and text:
                if text not in typeinfo.keys():
                    # child = QtWidgets.QTreeWidgetItem(currentitem)
                    # child.setText(0, text)
                    typeinfo[text] = list()
                    assetdata['typeinfo'] = self.sortdata(typeinfo)
                    with open(self.assetDatajson, "w", encoding="utf-8") as f:
                        json.dump(assetdata, f, indent=4)
                    print("Add Categoty Success...")
                    self.setCategory()
                else:
                    QtWidgets.QMessageBox.warning(self, "警告", "类型已存在...")

        elif currentitem.parent().parent() == None:
            categoryname = currentitem.text(0)
            text, ok = QtWidgets.QInputDialog.getText(self, '新增分组', '组名')
            if ok and text:
                if text not in typeinfo[categoryname]:
                    # child = QtWidgets.QTreeWidgetItem(currentitem)
                    # child.setText(0, text)
                    typeinfo[categoryname].append(text)
                    typeinfo[categoryname] = sorted(typeinfo[categoryname])
                    with open(self.assetDatajson, "w", encoding="utf-8") as f:
                        json.dump(assetdata, f, indent=4)
                    print("Add Type Success...")
                    self.setCategory()
                else:
                    QtWidgets.QMessageBox.warning(self, "警告", "分组已存在...")
        else:

            # QtWidgets.QMessageBox.warning(self, "警告",
            #                               "子目录不支持继续细分，请选择上层文件结构...")
            self.importAsset()

    # delete category
    def deleteCategory(self):
        currentitem = self.tableOfContent.currentItem()
        with open(self.assetDatajson, "r", encoding="utf-8") as f:
            assetdata = json.load(f)
            typeinfo = assetdata['typeinfo']
        if currentitem.parent() == None:
            QtWidgets.QMessageBox.critical(self, "提示", "根目录无法删除...")
        # category
        elif currentitem.parent().parent() == None:
            assetpath = self.libPath + "/" + self.getRoot(currentitem)
            categoryname = currentitem.text(0)
            if len(typeinfo[categoryname]) == 0:
                ok = QtWidgets.QMessageBox.warning(
                    self, "确认删除", "该操作很危险，你想好了吗",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.Yes)
                if ok:
                    currentitem.parent().removeChild(currentitem)
                    typeinfo.pop(categoryname)
                    with open(self.assetDatajson, "w", encoding="utf-8") as f:
                        json.dump(assetdata, f, indent=4)
                    if os.path.exists(assetpath):
                        try:
                            os.rmdir(assetpath)
                        except:
                            os.startfile(assetpath)
                            QtWidgets.QMessageBox.warning(
                                self, "提示", "文件夹内有其他资源，请手动清理...")
            else:
                QtWidgets.QMessageBox.critical(self, "提示",
                                               "该类别下存在未删除资源，禁止删除...")
                # type
        elif currentitem.parent().parent().parent() == None:
            assetpath = self.libPath + "/" + self.getRoot(currentitem)
            categoryname = currentitem.parent().text(0)
            typename = currentitem.text(0)
            if os.path.exists(assetpath):
                if len(os.listdir(assetpath)) == 0:
                    ok = QtWidgets.QMessageBox.warning(
                        self, "确认删除", "该操作很危险，你想好了吗",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                        QtWidgets.QMessageBox.Yes)
                    if ok == QtWidgets.QMessageBox.Yes:
                        currentitem.parent().removeChild(currentitem)
                        os.rmdir(assetpath)
                        typeinfo[categoryname].remove(typename)
                        with open(self.assetDatajson, "w",
                                  encoding="utf-8") as f:
                            json.dump(assetdata, f, indent=4)
                else:
                    QtWidgets.QMessageBox.critical(self, "提示",
                                                   "该分组下存在未删除资源，禁止删除...")
            else:
                ok = QtWidgets.QMessageBox.warning(
                    self, "确认删除", "该操作很危险，你想好了吗",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.Yes)
                if ok == QtWidgets.QMessageBox.Yes:
                    currentitem.parent().removeChild(currentitem)
                    typeinfo[categoryname].remove(typename)
                    with open(self.assetDatajson, "w", encoding="utf-8") as f:
                        json.dump(assetdata, f, indent=4)

    # open category
    def openCategory(self):
        item = self.tableOfContent.currentItem()

        relpath = self.getRoot(item)
        path = self.libPath
        if relpath:
            path = self.libPath + "/" + relpath
        try:
            os.startfile(path)
        except:
            os.startfile(self.libPath)

    #  category right click menu
    def treeWidgetItem_menu(self, pos):
        item = self.tableOfContent.currentItem()
        rightclickedpos = self.tableOfContent.itemAt(pos)
        if item != None and rightclickedpos != None:
            if item.parent() == None:
                RootMenu = QtWidgets.QMenu()
                RootMenu.addAction(QtWidgets.QAction(u'添加类别', self))
                RootMenu.addAction(QtWidgets.QAction(u'打开目录', self))
                RootMenu.triggered[QtWidgets.QAction].connect(
                    self.processtrigger)
                RootMenu.exec_(QtGui.QCursor.pos())
            elif item.parent().parent() == None:
                categoryMenu = QtWidgets.QMenu()
                categoryMenu.addAction(QtWidgets.QAction(u'添加分组', self))
                categoryMenu.addAction(QtWidgets.QAction(u'打开目录', self))
                categoryMenu.addAction(QtWidgets.QAction(u'删除此类别', self))
                categoryMenu.triggered[QtWidgets.QAction].connect(
                    self.processtrigger)
                categoryMenu.exec_(QtGui.QCursor.pos())
            elif item.parent().parent().parent() == None:
                TypeMenu = QtWidgets.QMenu()
                TypeMenu.addAction(QtWidgets.QAction(u'添加资产', self))
                TypeMenu.addAction(QtWidgets.QAction(u'打开目录', self))
                TypeMenu.addAction(QtWidgets.QAction(u'删除此分组', self))
                TypeMenu.triggered[QtWidgets.QAction].connect(
                    self.processtrigger)
                TypeMenu.exec_(QtGui.QCursor.pos())

    def processtrigger(self, action):
        if action.text() == "添加类别" or action.text() == "添加分组" or action.text(
        ) == "添加资产":
            self.addCategory()
        elif action.text() == "删除此类别" or action.text() == "删除此分组":
            self.deleteCategory()
        elif action.text() == "打开目录":
            self.openCategory()

    # get the item path
    def getRoot(self, item):
        pathlist = list()
        name = item.text(0)
        pathlist.append(name)
        if item.parent() == None:
            return None
        while item.parent().parent() != None:
            item = item.parent()
            pathlist.insert(0, item.text(0))
        path = "/".join(pathlist)

        return path

    # import .hip asset as new hip
    def _importhip(self, assetpath):
        hou.hipFile.load(assetpath)

    # merge .hip asset
    def _mergehip(self, assetpath):
        hou.hipFile.merge(assetpath)

    # show .hip asset in explorer
    def _showinexplorer(self, path):
        os.startfile(path)

    # mark as favorite
    def _markAsFavorite(self, path):
        print("TODO...")

    # _assetcell
    def _assetcell(self, path, name):
        assetfolder = path
        assetpath = path + "/" + name + ".hip"
        thumbpath = path + "/" + name + ".jpg"
        cell_frame = QtWidgets.QWidget()
        cell_layout = QtWidgets.QVBoxLayout()
        cell_layout.setContentsMargins(2, 2, 0, 0)
        cell_frame.setLayout(cell_layout)
        #  thumb label
        self._thumblabel = QtWidgets.QLabel()
        self._thumblabel.setFixedHeight(192 * 1.5 * self.iconscale)
        self._thumblabel.setFixedHeight(108 * 1.5 * self.iconscale)
        self._thumblabel.setAlignment(QtGui.Qt.AlignCenter)
        img = QtGui.QImage(thumbpath)
        img = img.scaled(192 * 1.5 * self.iconscale,
                         108 * 1.5 * self.iconscale,
                         QtGui.Qt.KeepAspectRatioByExpanding,
                         QtGui.Qt.SmoothTransformation)
        self._thumblabel.setPixmap(QtGui.QPixmap(img))
        # text label
        self._hiplabel = QtWidgets.QLabel(name + ".hip")
        self._hiplabel.setAlignment(QtCore.Qt.AlignCenter)
        self._path = QtWidgets.QLabel(path)
        self._path.setVisible(False)

        # add to layout
        cell_layout.addWidget(self._thumblabel)
        cell_layout.addWidget(self._hiplabel, QtCore.Qt.AlignBottom)
        cell_layout.addWidget(self._path)
        # add right click menu
        cell_frame.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        # new
        newscene = QtWidgets.QAction(cell_frame)
        newscene.setText("Import As New Scene")
        newscene.triggered.connect(partial(self._importhip, assetpath))
        cell_frame.addAction(newscene)

        # merge
        mergescene = QtWidgets.QAction(cell_frame)
        mergescene.setText("Merge To Current Scene")
        mergescene.triggered.connect(partial(self._mergehip, assetpath))
        cell_frame.addAction(mergescene)

        # open
        openscene = QtWidgets.QAction(cell_frame)
        openscene.setText("Show in Explorer")
        openscene.triggered.connect(partial(self._showinexplorer, assetfolder))
        cell_frame.addAction(openscene)

        # mark
        markAsset = QtWidgets.QAction(cell_frame)
        markAsset.setText("Mark As Favorite")
        markAsset.triggered.connect(partial(self._markAsFavorite, assetfolder))
        cell_frame.addAction(markAsset)
        # return
        return cell_frame

    # get asset list
    def getassetlist(self, path, foldertype, filter=None):
        assetlists = list()
        if foldertype == ROOTFOLDER:
            for eachtype in self.categotylists.keys():
                for eachcategory in self.categotylists[eachtype]:
                    assetfolder = path + "/" + eachtype + "/" + eachcategory
                    if os.path.exists(assetfolder):
                        templists = os.listdir(assetfolder)
                        for each in templists:
                            if type(filter) != str:
                                assetlists.append(assetfolder + "/" + each)
                            else:
                                try:
                                    res = re.search(filter, each, re.I)
                                    if res:
                                        assetlists.append(assetfolder + "/" +
                                                          each)
                                except:
                                    assetlists.append(assetfolder + "/" + each)
        elif foldertype == CATEGORYFOLDER:
            typename = path.split("/")[-1]
            for eachcategory in self.categotylists[typename]:
                assetfolder = path + "/" + eachcategory
                if os.path.exists(assetfolder):
                    templists = os.listdir(assetfolder)
                    for each in templists:
                        if type(filter) != str:
                            assetlists.append(assetfolder + "/" + each)
                        else:
                            try:
                                res = re.search(filter, each, re.I)
                                if res:
                                    assetlists.append(assetfolder + "/" + each)
                            except:
                                assetlists.append(assetfolder + "/" + each)
        else:
            if os.path.exists(path):
                templists = os.listdir(path)
                for each in templists:
                    if type(filter) != str:
                        assetlists.append(path + "/" + each)
                    else:
                        try:
                            res = re.search(filter, each, re.I)
                            if res:
                                assetlists.append(path + "/" + each)
                        except:
                            assetlists.append(assetfolder + "/" + each)
        return assetlists

    # display hipfile in content
    def displayAsset(self, intput_assetlist):
        self.filetable.setRowCount(0)
        self.filetable.setColumnCount(0)

        assetlist = intput_assetlist
        sqrt = math.sqrt(len(assetlist))
        # print(sqrt)
        if sqrt % 1 >= 0.5:
            x = math.ceil(sqrt) + 1
            y = math.floor(sqrt)
        else:
            x = math.ceil(sqrt)
            y = math.floor(sqrt)
        # print(x, y)
        self.filetable.setColumnCount(x)
        self.filetable.setRowCount(y)
        i = 0
        for assetpath in assetlist:
            assetname = assetpath.split("/")[-1]
            self.filetable.setColumnWidth(i % x, 192 * 1.5 * self.iconscale)
            self.filetable.setRowHeight(i / x, 138 * 1.5 * self.iconscale)
            newcell = self._assetcell(assetpath, assetname)
            self.filetable.setCellWidget(i / x, i % x, newcell)
            i += 1

    # categoty change event
    def refreshTable(self):
        filter = self.filter.text()
        item = self.tableOfContent.currentItem()
        foldertype = TYPEFOLDER
        if item.parent() == None:
            assetpath = self.libPath
            foldertype = ROOTFOLDER
        elif item.parent().parent() == None:
            self.categorypath = self.libPath + "/" + item.text(0)
            assetpath = self.libPath + "/" + self.getRoot(item)
            foldertype = CATEGORYFOLDER
        else:
            self.categorypath = self.libPath + "/" + item.text(0)
            assetpath = self.libPath + "/" + self.getRoot(item)
        # refresh categotylists
        self.getCategory()
        assetlists = self.getassetlist(assetpath, foldertype, filter)
        self.displayAsset(assetlists)

    # choose library path
    def choosepath(self):
        fname = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Open Library Path")
        if fname:
            self.libpathlineedit.setText(fname)

    # lib changed
    def libpathchanged(self):

        self.tableOfContent.clear()
        self.filetable.clear()
        self.filetable.setColumnCount(0)

        self.tableroot = QtWidgets.QTreeWidgetItem(self.tableOfContent)
        self.tableroot.setText(0, "Home")
        self.tableOfContent.setCurrentItem(self.tableroot)

        self.libPath = self.libpathlineedit.text()
        # overwrite config path
        configpath = hou.homeHoudiniDirectory() + "/smartflow/config.json"
        self.generateconfig(configpath, self.libPath, False)

        # check assetdata.json，if not exists，create by default
        self.assetDatajson = self.libPath + "/" + "assetdatas.json"
        # print(self.assetDatajson)
        if not os.path.exists(self.assetDatajson):
            QtWidgets.QMessageBox.information(self, "提示",
                                              "欢迎使用新的仓库地址，已按默认配置生成分类...")
            with open(self.assetDatajson, "w", encoding='utf-8') as f:
                json.dump(self._Default_Catagory, f, indent=4)
        self.setCategory()

    # filter
    def filterChanged(self):
        self.refreshTable()

    def scaleicon(self, index):
        if index == 0 and self.iconscale <= 1.5:
            self.iconscale += 0.1
        if index == 1 and self.iconscale >= 0.5:
            self.iconscale -= 0.1
        if index == 2:
            self.iconscale = 0.75

        self.refreshTable()

    # open url
    def openUrl(self, q):
        print(q)
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(q))

    # display asset info
    def assetclick(self, row, col):
        _cell = self.filetable.cellWidget(row, col)
        if _cell:
            assetpath = _cell.findChildren(QtWidgets.QLabel)[2].text()
            with open(assetpath + "/assetinfo.json", "r") as f:
                info = json.load(f)
                self.verinfo_lineEdit.setText(info['houdiniversion'])
                self.author_lineEdit.setText(info['Author'])
                self.createdata_lineEdit.setText(info['createData'])
                if 'urlpath' in info.keys():
                    url = "<a href='" + info['urlpath'] + "'<b>" + info[
                        'urlpath'] + "</b></a>"
                    self.urlpath.setText(url)
                    self.urlpath.setOpenExternalLinks(True)
                else:
                    self.urlpath.setOpenExternalLinks(False)
                    self.urlpath.setText("")

    # connect signals
    def connectSignals(self):
        # menubar
        self.importassetButton.triggered.connect(self.importAsset)
        self.reloadButton.triggered.connect(self.reloadPlugin)
        self.pluginsetting.triggered.connect(self.openpluginsetting)
        self.helpmenu.triggered.connect(self.openhelp)
        # library path
        self.libbutton.clicked.connect(self.choosepath)
        self.libpathlineedit.textChanged.connect(self.libpathchanged)

        # left widget --- table of content
        self.addCategoryButton.clicked.connect(self.addCategory)
        self.deleteCategoryButton.clicked.connect(self.deleteCategory)
        self.openCategoryButton.clicked.connect(self.openCategory)
        self.tableOfContent.clicked.connect(self.refreshTable)
        self.tableOfContent.setContextMenuPolicy(QtGui.Qt.CustomContextMenu)
        self.tableOfContent.customContextMenuRequested.connect(
            self.treeWidgetItem_menu)
        # right widget --- filetable
        self.filetable.cellClicked.connect(self.assetclick)
        self.filter.textChanged.connect(self.filterChanged)
        # self.urlpath.linkActivated.connect(self.openUrl)

        # icon scale
        self.scaleupbutton.clicked.connect(partial(self.scaleicon, 0))
        self.scaledownbutton.clicked.connect(partial(self.scaleicon, 1))
        self.scaleresetbutton.clicked.connect(partial(self.scaleicon, 2))

    # init menber
    def initmenber(self):
        self.initlibrary()

    # init paramter
    def initparameter(self):
        self.loadconfig()

    # init UI
    def initUI(self):
        # set title name
        self.setWindowTitle("Houdini HipFile Manager")
        self.setWindowIcon(QtGui.QIcon("./Icons/take.png"))
        # self.resize(800, 600)

        # 获取菜单栏 menuBar
        bar = self.menuBar()
        # file menuBar
        file_menu = bar.addMenu('File')
        self.importassetButton = file_menu.addAction('import Asset')

        # Edit menuBar
        edit_menu = bar.addMenu('Edit')
        self.pluginsetting = edit_menu.addAction('setting')

        # View menuBar
        view_menu = bar.addMenu('View')
        self.reloadButton = view_menu.addAction('Reload')

        # Help menuBar
        help_menu = bar.addMenu('Help')
        self.helpmenu = help_menu.addAction('Show Help')

        # 工具栏 ToolBar
        # tb_file = self.addToolBar('Open')
        # new = QtWidgets.QAction(hou.qt.Icon('take.png', ICON_SIZE, ICON_SIZE),
        #                         "new", self)
        # tb_file.addAction(new)

        # exit = QtWidgets.QAction(hou.qt.Icon('exit.png', ICON_SIZE, ICON_SIZE),
        #                          "exit", self)
        # tb_file.addAction(exit)
        # tb_file.setToolButtonStyle(QtGui.Qt.ToolButtonTextUnderIcon)

        # base layout
        # 直接加布局的时候是不显示的，必须嵌套一个widget
        baselayout = QtWidgets.QVBoxLayout()
        baselayout.setSpacing(SIZE4)
        baselayout.setContentsMargins(MARGIN4)
        # central widget
        widget = QtWidgets.QWidget()
        widget.setLayout(baselayout)
        self.setCentralWidget(widget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        widget.setSizePolicy(sizePolicy)

        # library path
        liblayout = QtWidgets.QHBoxLayout()
        liblabel = QtWidgets.QLabel("LibraryPath")
        self.libpathlineedit = QtWidgets.QLineEdit()
        self.libpathlineedit.setToolTip("pick your library folder")
        self.libpathlineedit.setFocusPolicy(QtGui.Qt.NoFocus)
        self.libbutton = QtWidgets.QPushButton()
        self.libbutton.setIcon(
            hou.qt.Icon("BUTTONS_chooser_folder", ICON_SIZE, ICON_SIZE))

        liblayout.addWidget(liblabel)
        liblayout.addWidget(self.libpathlineedit)
        liblayout.addWidget(self.libbutton)
        baselayout.addLayout(liblayout)

        # global splitter group
        splittercontainer = QtWidgets.QSplitter(QtGui.Qt.Horizontal)
        splittercontainer.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                        QtWidgets.QSizePolicy.Preferred)
        baselayout.addWidget(splittercontainer)
        # left menu all file
        leftlayout = QtWidgets.QVBoxLayout()
        leftwidget = QtWidgets.QWidget()
        leftwidget.setLayout(leftlayout)
        leftwidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                 QtWidgets.QSizePolicy.Preferred)
        splittercontainer.addWidget(leftwidget)

        # left splitter group
        tableSplitter = QtWidgets.QSplitter(QtGui.Qt.Vertical)
        tableSplitter.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                    QtWidgets.QSizePolicy.Preferred)

        upleftlayout = QtWidgets.QVBoxLayout()
        upleftwidget = QtWidgets.QWidget()
        upleftwidget.setLayout(upleftlayout)
        tableSplitter.addWidget(upleftwidget)

        leftlayout.addWidget(tableSplitter)
        # add delete type button
        buttonlayout = QtWidgets.QHBoxLayout()
        # add button
        self.addCategoryButton = QtWidgets.QPushButton()
        self.addCategoryButton.setIcon(
            hou.qt.Icon('VOP_add', ICON_SIZE, ICON_SIZE))
        self.addCategoryButton.setFixedWidth(20)
        # delete button
        self.deleteCategoryButton = QtWidgets.QPushButton()
        self.deleteCategoryButton.setIcon(
            hou.qt.Icon('VOP_subtract', ICON_SIZE, ICON_SIZE))
        self.deleteCategoryButton.setFixedWidth(20)
        # open button
        self.openCategoryButton = QtWidgets.QPushButton()
        self.openCategoryButton.setIcon(
            hou.qt.Icon('BUTTONS_chooser_folder', ICON_SIZE, ICON_SIZE))
        self.openCategoryButton.setFixedWidth(20)

        buttonlayout.setAlignment(QtCore.Qt.AlignLeft)
        buttonlayout.addWidget(self.addCategoryButton)
        buttonlayout.addWidget(self.deleteCategoryButton)
        buttonlayout.addWidget(self.openCategoryButton)
        upleftlayout.addLayout(buttonlayout)

        # table of content
        self.tableOfContent = QtWidgets.QTreeWidget()
        self.tableOfContent.setColumnCount(1)
        # self.tableOfContent.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
        #                                   QtWidgets.QSizePolicy.Expanding)
        self.tableOfContent.setHeaderLabel("File Library")
        self.tableroot = QtWidgets.QTreeWidgetItem(self.tableOfContent)
        self.tableroot.setText(0, "Home")
        self.tableOfContent.setCurrentItem(self.tableroot)
        upleftlayout.addWidget(self.tableOfContent)
        # self.tableOfContent.setColumnWidth(100, 120)

        # down widget
        downleftlayout = QtWidgets.QVBoxLayout()
        downleftwidget = QtWidgets.QWidget()
        downleftwidget.setLayout(downleftlayout)
        tableSplitter.addWidget(downleftwidget)
        tableSplitter.setStretchFactor(0, 3)
        tableSplitter.setStretchFactor(1, 1)
        # left menu fovarite file
        self.markContent = QtWidgets.QTreeWidget()
        self.markContent.setColumnCount(1)
        self.markContent.setHeaderLabel("Favorite File")
        downleftlayout.addWidget(self.markContent)

        # right content
        rightlayout = QtWidgets.QVBoxLayout()
        rightwidget = QtWidgets.QWidget()
        rightwidget.setLayout(rightlayout)
        rightwidget.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                  QtWidgets.QSizePolicy.Preferred)
        splittercontainer.addWidget(rightwidget)
        splittercontainer.setStretchFactor(0, 1)
        splittercontainer.setStretchFactor(1, 4)
        # filter colume
        filterlayout = QtWidgets.QHBoxLayout()
        filterlabel = QtWidgets.QLabel('Filter')
        self.filter = QtWidgets.QLineEdit()
        filterlayout.addWidget(filterlabel)
        filterlayout.addWidget(self.filter)
        rightlayout.addLayout(filterlayout)

        # icon scrollbar
        sliderlayout = QtWidgets.QHBoxLayout()
        sliderlayout.setAlignment(QtCore.Qt.AlignLeft)

        self.scaleupbutton = QtWidgets.QPushButton()
        self.scaleupbutton.setFixedSize(25, 25)
        self.scaleupbutton.setIcon(
            hou.qt.Icon('scroll_up.png', ICON_SIZE, ICON_SIZE))
        self.scaleupbutton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                         QtWidgets.QSizePolicy.Fixed)

        self.scaledownbutton = QtWidgets.QPushButton()
        self.scaledownbutton.setFixedSize(25, 25)
        self.scaledownbutton.setIcon(
            hou.qt.Icon('scroll_down.png', ICON_SIZE, ICON_SIZE))
        self.scaledownbutton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                           QtWidgets.QSizePolicy.Fixed)

        self.scaleresetbutton = QtWidgets.QPushButton()
        self.scaleresetbutton.setFixedSize(25, 25)
        self.scaleresetbutton.setIcon(
            hou.qt.Icon('scroll_reset2.png', ICON_SIZE, ICON_SIZE))
        self.scaleresetbutton.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                            QtWidgets.QSizePolicy.Fixed)

        sliderlayout.addWidget(self.scaleupbutton)
        sliderlayout.addWidget(self.scaledownbutton)
        sliderlayout.addWidget(self.scaleresetbutton)
        rightlayout.addLayout(sliderlayout)
        # hipfile
        self.filetable = QtWidgets.QTableWidget()
        self.filetable.horizontalHeader().setVisible(False)
        self.filetable.verticalHeader().setVisible(False)
        # self.filetable.setIconSize(QtCore.QSize(300, 200))
        self.filetable.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        # add menu
        # self.filetable.setContextMenuPolicy(QtGui.Qt.CustomContextMenu)
        # self.filetable.customContextMenuRequested.connect(self.generateMenu)

        rightlayout.addWidget(self.filetable)
        # hip info
        infolayout = QtWidgets.QGridLayout()
        infolayout.setAlignment(QtGui.Qt.AlignLeft)
        rightlayout.addLayout(infolayout)

        verinfo_label = QtWidgets.QLabel("Version : ")
        verinfo_label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                    QtWidgets.QSizePolicy.Fixed)
        self.verinfo_lineEdit = QtWidgets.QLabel()
        self.verinfo_lineEdit.setAlignment(QtGui.Qt.AlignLeft)
        infolayout.addWidget(verinfo_label, 0, 0)
        infolayout.addWidget(self.verinfo_lineEdit, 0, 1)

        author_label = QtWidgets.QLabel('Author : ')
        self.author_lineEdit = QtWidgets.QLabel()
        infolayout.addWidget(author_label, 1, 0)
        infolayout.addWidget(self.author_lineEdit, 1, 1)

        createdata_label = QtWidgets.QLabel("Create Data : ")
        self.createdata_lineEdit = QtWidgets.QLabel()
        infolayout.addWidget(createdata_label, 2, 0)
        infolayout.addWidget(self.createdata_lineEdit, 2, 1)

        Url_label = QtWidgets.QLabel("Url : ")
        # Url_label.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
        #                         QtWidgets.QSizePolicy.Fixed)
        self.urlpath = QtWidgets.QLabel()
        self.urlpath.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                   QtWidgets.QSizePolicy.Fixed)
        # self.urlpath.setAlignment(QtGui.Qt.AlignLeft)
        # self.urlpath.setAlignment(QtGui.Qt.AlignCenter)
        self.urlpath.setStyleSheet(
            "color: rgb(0, 170, 0);background-color: rgb(78, 186, 54)")
        infolayout.addWidget(Url_label, 3, 0)
        infolayout.addWidget(self.urlpath, 3, 1)
        # init
        self.initparameter()
        self.connectSignals()


def initWindow():
    import hou
    win = ResManager(hou.qt.mainWindow())
    win.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = ResManager()
    win.show()
    sys.exit(app.exec_())
