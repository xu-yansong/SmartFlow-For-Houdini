#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : QtOpenGL.py
@Time        : 2022/11/06 15:34:09
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets

import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import *
import os
import sys
import opengl_window


class RenderScene(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        # self.shader = None

    def initUI(self):
        # self.resize(1280, 720)
        # self.setWindowTitle("OpenGL渲染")

        # mainwidget = QtWidgets.QWidget()
        # self.setCentralWidget(mainwidget)

        # baselayout = QtWidgets.QVBoxLayout()
        # mainwidget.setLayout(baselayout)
        # self.label = QtWidgets.QLabel("first Test")
        # self.button = QtWidgets.QPushButton("sure")

        scene = opengl_window.CustomScene()

        # scene.addText("dsdsdsdsdsdsd")
        # # 添加一个路径(三叶草)
        # path = QtGui.QPainterPath()
        # r = 160
        # for i in range(3):
        #     path.cubicTo(math.cos(2*math.pi*i/3.0)*r,
        #                  math.sin(2*math.pi*i/3.0)*r,
        #                  math.cos(2*math.pi*(i+0.9)/3.0)*r,
        #                  math.sin(2*math.pi*(i+0.9)/3.0)*r, 0, 0)
        # pathItem = QtWidgets.QGraphicsPathItem()
        # pathItem.setPath(path)
        # pathItem.setPen(QtGui.QPen())
        # pathItem.setBrush(QtCore.Qt.darkGreen)
        # pathItem.setPos(160, 160)
        # scene.addItem(pathItem)

        view = QtWidgets.QGraphicsView()
        view.setScene(scene)
        self.setCentralWidget(view)
        self.resize(1280, 720)
        # baselayout.addWidget(self.label)
        # baselayout.addWidget(self.button)
        # baselayout.addWidget(self.button)
        # baselayout.addWidget(view)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = RenderScene()
    w.show()
    sys.exit(app.exec_())
