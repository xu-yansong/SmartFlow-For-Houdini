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
from __future__ import print_function
import sys
import os
from OpenGL.arrays import *
from OpenGL.GL import shaders
from OpenGL.GL import *
import numpy as np
import math
from PySide2 import QtCore, QtGui, QtWidgets
from openglgraphics import Ui_myglwidget
from imp import reload
reload(Ui_myglwidget)
try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except:
    pass


def float_array(py_array):
    floats = GLfloatArray.zeros(len(py_array))
    for x in range(0, len(py_array)):
        floats[x] = py_array[x]

    return floats


box_verts = [-1, 1, -1, 1, 1, 1, 1, 1, -1, -1,  1, -1, -1, 1, 1, 1, 1, 1,
             -1, 1, -1, 1, 1, -1, -1, -1, -1, 1, 1, -1, 1, -1, -1, -1, -1, -1,
             -1, 1, 1, -1, 1, -1, -1, -1, -1, -1, 1, 1, -1, -1, -1, -1, -1, 1,
             -1, 1, 1, -1, -1, 1, 1, 1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1,
             1, 1, 1, 1, -1, 1, 1, -1, -1, 1, 1, 1, 1, -1, -1, 1, 1, -1,
             -1, -1, 1, -1, -1, -1, 1, -1, -1, 1, -1, 1, -1, -1, 1, 1, -1, -1,
             ]


class CustomScene2(QtWidgets.QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.glInit = True

    def initGL(self):
        """ Initializes OpenGL resources if they have not already been created"""
        if self.glInit:
            return

        self.glInit = True

        verts = float_array(box_verts)

        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, 432, verts, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        vertex_shader = shaders.compileShader("""
            #version 150
            in vec3 v_position;

            uniform mat4 m_scale;
            uniform mat4 m_rot;
            uniform mat4 m_projection;

            void main()
            {
                mat4 mvp = m_projection * m_rot * m_scale;
                gl_Position = mvp * vec4(v_position, 1.0);
            }
            """, GL_VERTEX_SHADER)

        fragment_shader = shaders.compileShader("""
            #version 150

            uniform float f_opacity;
            void main()
            {
                gl_FragColor = vec4(0.9, 0.55, 0.3, f_opacity);
            }
            """, GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vertex_shader, fragment_shader)

        self.uniforms = {
            'm_scale': glGetUniformLocation(self.shader, 'm_scale'),
            'm_rot': glGetUniformLocation(self.shader, 'm_rot'),
            'm_projection': glGetUniformLocation(self.shader, 'm_projection'),
            'f_opacity': glGetUniformLocation(self.shader, 'f_opacity'),
        }

    def setProjection(self):
        """ Computes and sets the projection matrix based on view size/zoom"""
        aspect = float(self.width())/float(self.height())
        factor = 5 * self.zoom

        lr = 1.0 / (factor * aspect * 2.0)
        bt = 1.0 / (factor * 2.0)
        nf = 1.0 / (-1.0 - 100.0)

        ortho = [lr, 0,  0,         0,
                 0,  bt, 0,         0,
                 0,  0,  2.0 * nf,  0,
                 0,  0,  99.0 * nf, 1]
        p = float_array(ortho)

        glUniformMatrix4fv(self.uniforms["m_projection"], 1, GL_FALSE, p)

    def drawBox(self, x_scale, y_scale, z_scale, opacity):
        # Transform the box based on the view settings and scale
        ca = math.cos(0.0)
        cb = math.cos(self.xRot / 180.0 * 3.14159)
        ch = math.cos(self.yRot / 180.0 * 3.14159)

        sa = math.sin(0.0)
        sb = math.sin(self.xRot / 180.0 * 3.14159)
        sh = math.sin(self.yRot / 180.0 * 3.14159)

        r = [ch*ca,  -ch*sa*cb + sh*sb,  ch*sa*sb + sh*cb,    0.0,
             sa,     ca*cb,              -ca*sb,              0.0,
             -sh*ca, sh*sa*cb + ch*sb,   (-sh*sa*sb + ch*cb), 0.0,
             0.0,    0.0,                -3.0,                1.0]
        rot = float_array(r)

        s = [x_scale, 0.0,     0.0,     0.0,
             0.0,     y_scale, 0.0,     0.0,
             0.0,     0.0,     z_scale, 0.0,
             0.0,     0.0,     0.0,     1.0]
        scale = float_array(s)

        glUniformMatrix4fv(self.uniforms["m_scale"], 1, GL_FALSE, scale)
        glUniformMatrix4fv(self.uniforms["m_rot"], 1, GL_FALSE, rot)

        glUniform1fv(self.uniforms["f_opacity"], 1, opacity)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glEnableClientState(GL_VERTEX_ARRAY)
        glVertexPointer(3, GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES, 0, 36)

        glDisableClientState(GL_VERTEX_ARRAY)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def drawBackground(self, painter, rect):
        """ Called when the scene should render it's background. Can use GL."""

        super().drawBackground(painter, rect)
        # glClearDepth(1.0)
        self.initGL()
        # Update the label to match the size of the graphics scene

        # Clear the viewport
        QtGui.QOpenGLFunctions.glClearColor(0.2, 0.28, 0.32, 1.0)
        QtGui.QOpenGLFunctions.glClearDepth(1.0)
        QtGui.QOpenGLFunctions.glClear(
            GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Enable blending and culling
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_CULL_FACE)

        # Activate the shader for the box
        shaders.glUseProgram(self.shader)

        # Set the projection matrix
        self.setProjection()

        # Draw the boxes
        self.drawBox(0.50, 0.10, 0.25, 0.75)
        self.drawBox(0.75, 0.25, 0.75, 0.45)
        self.drawBox(1.75, 0.50, 1.75, 0.25)
        self.drawBox(2.50, 1.50, 2.50, 0.10)

        # Unbind the shader
        shaders.glUseProgram(0)

        # Restore the GL state
        glDisable(GL_BLEND)
        glDisable(GL_CULL_FACE)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.buttons() == QtCore.Qt.LeftButton:
            print(event.scenePos())


class MyGLWidget(QtWidgets.QOpenGLWidget):  # 通过子例化，实现自定义

    def __init__(self, parent=None):
        super(MyGLWidget, self).__init__(parent)

    def initializeGL(self):
        version_profile = QtGui.QOpenGLVersionProfile()
        version_profile.setVersion(2, 0)
        self.gl = self.context().versionFunctions(version_profile)
        self.gl.initializeOpenGLFunctions()

        # 设置背景色
        self.gl.glClearColor(0.2, 0.4, 0.52, 1.0)
        # 深度测试
        self.gl.glEnable(self.gl.GL_DEPTH_TEST)

    def paintGL(self):
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT |
                        self.gl.GL_DEPTH_BUFFER_BIT)
        self.gl.glLoadIdentity()

        #self.gl.glRotated(60.0, 1.0, 0.0, 0.0)
        self.gl.glBegin(self.gl.GL_TRIANGLES)
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


class CustomScene2(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.initUI()
        # self.shader = None

    def initUI(self):
        self.resize(1280, 720)
        self.setWindowTitle("OpenGL渲染")

        mainwidget = QtWidgets.QWidget()
        self.setCentralWidget(mainwidget)

        baselayout = QtWidgets.QVBoxLayout()
        mainwidget.setLayout(baselayout)
        self.label = QtWidgets.QLabel("first Test")
        self.button = QtWidgets.QPushButton("sure")

        scene = MyGLWidget()

        # view = QtWidgets.QGraphicsView()
        # view.resize(500, 400)
        # view.setScene(scene)
        # self.setCentralWidget(mainwidget)
        # self.resize(1280, 720)

        baselayout.addWidget(self.label)
        baselayout.addWidget(self.button)
        baselayout.addWidget(self.button)
        baselayout.addWidget(scene)


class MyGLWidget(QtWidgets.QOpenGLWidget):  # 通过子例化，实现自定义

    def __init__(self, parent=None):
        super(MyGLWidget, self).__init__(parent)

    def initializeGL(self):
        version_profile = QtGui.QOpenGLVersionProfile()
        version_profile.setVersion(2, 0)
        self.gl = self.context().versionFunctions(version_profile)
        self.gl.initializeOpenGLFunctions()

        # 设置背景色
        self.gl.glClearColor(0.2, 0.4, 0.52, 1.0)
        # 深度测试
        self.gl.glEnable(self.gl.GL_DEPTH_TEST)

    def paintGL(self):
        self.gl.glClear(self.gl.GL_COLOR_BUFFER_BIT |
                        self.gl.GL_DEPTH_BUFFER_BIT)
        self.gl.glLoadIdentity()

        #self.gl.glRotated(60.0, 1.0, 0.0, 0.0)
        self.gl.glBegin(self.gl.GL_TRIANGLES)
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


class CustomScene(QtWidgets.QMainWindow, Ui_myglwidget.Ui_MainWindow):
    def __init__(self):
        super().__init__()  # super()构造器方法返回父级的对象。
        self.setupUi(self)  # 加载ui


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = CustomScene()
    w.show()
    sys.exit(app.exec_())
