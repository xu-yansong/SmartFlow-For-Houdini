import Ui_myglwidget

from PySide2 import QtCore, QtGui, QtWidgets
from OpenGL.GL import shaders
from OpenGL.GL import *


class MyGLWidget(QtWidgets.QOpenGLWidget):  # 通过子例化，实现自定义

    def __init__(self, parent=None):
        super(MyGLWidget, self).__init__(parent)

    def initializeGL(self):
        version_profile = QtGui.QOpenGLVersionProfile()
        version_profile.setVersion(2, 0)
        self.gl = self.context().versionFunctions(version_profile)
        self.gl.initializeOpenGLFunctions()

        # 设置背景色
        QtGui.QOpenGLFunctions.glClearColor(0.2, 0.4, 0.52, 1.0)
        # 深度测试
        QtGui.QOpenGLFunctions.glEnable(self.gl.GL_DEPTH_TEST)

    def paintGL(self):
        QtGui.QOpenGLFunctions.glClear(0.0, 0.0, 0.0, 0.0)
        QtGui.QOpenGLFunctions.glLoadIdentity()

        #self.gl.glRotated(60.0, 1.0, 0.0, 0.0)
        self.gl.glBegin(GL_TRIANGLES)
        self.gl.glColor3d(1.0, 0.0, 0.0)
        self.gl.glVertex3d(0.0, 1.0, 0.0)
        self.gl.glColor3d(0.0, 1.0, 0.0)
        self.gl.glVertex3d(-1.0, -1.0, 0.0)
        self.gl.glColor3d(0.0, 0.0, 1.0)
        self.gl.glVertex3d(1.0, -1.0, 0.0)
        self.gl.glEnd()

        self.gl.glBegin(self.gl.GL_LINES)
        self.gl.glVertex3d(-1.5, -1.5, 0)
        self.gl.glVertex3d(1.5, 1.5, 0)
        self.gl.glEnd()

    def resizeGL(self, width, height):

        side = min(width, height)
        if side < 0:
            return

        # 视口
        self.gl.glViewport((width - side) // 2,
                           (height - side) // 2, side, side)
        self.gl.glMatrixMode(self.gl.GL_PROJECTION)
        self.gl.glLoadIdentity()
        # 正交投射
        self.gl.glOrtho(-1.5, 1.5, -1.5, 1.5, -10, 10)
        self.gl.glMatrixMode(self.gl.GL_MODELVIEW)
