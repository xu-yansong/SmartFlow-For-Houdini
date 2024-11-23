import pyrr
import numpy as np
import math
from PySide2 import QtCore, QtWidgets, QtGui
import sys
import hou
py_gl_found = True

try:
    from OpenGL.GL import *
    from OpenGL.GL import shaders
    from OpenGL.arrays import *
except ImportError:
    py_gl_found = False
    QtWidgets.QMessageBox.critical(None, "Custom Graphics Scene Example",
                                   "PyOpenGL must be installed to run this example.",
                                   QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Default,
                                   QtWidgets.QMessageBox.NoButton)


def float_array(py_array):
    floats = GLfloatArray.zeros(len(py_array))
    for x in range(0, len(py_array)):
        floats[x] = py_array[x]

    return floats


label_style = "background: rgba(0,0,0,0); color: #FFFFFF; font-size: 14px"
light_label_style = "background: rgba(0,0,0,0); color: #CCCCCC; font-size: 12px"

desc_text = """This example uses a custom graphics scene to combine QWidgets with \
OpenGL rendering.
Use the left mouse button to pan and the mouse wheel to zoom."""

vertices = [-0.5, -0.5, 0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.5, -0.5, 0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
            0.5, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
            -0.5,  0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

            -0.5, -0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
            0.5, 0.5, -0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
            -0.5,  0.5, -0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

            0.5, -0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.5, 0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
            0.5, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
            0.5,  -0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

            -0.5, 0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
            -0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
            -0.5, -0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
            -0.5,  0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

            -0.5, -0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.5, -0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
            0.5, -0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
            -0.5,  -0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

            0.5, 0.5, -0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
            -0.5, 0.5, -0.5, 0.0, 1.0, 0.0, 1.0, 0.0,
            -0.5, 0.5, 0.5, 0.0, 0.0, 1.0, 1.0, 1.0,
            0.5,  0.5, 0.5, 1.0, 1.0, 1.0, 0.0, 1.0,

            ]

indices = [0, 1, 2, 2, 3, 0,
           4, 5, 6, 6, 7, 4,
           8, 9, 10, 10, 11, 8,
           12, 13, 14, 14, 15, 12,
           16, 17, 18, 18, 19, 16,
           20, 21, 22, 22, 23, 20]

vertices = np.array(vertices, dtype=np.float32)
indices = np.array(indices, dtype=np.uint32)


def updatamodel():
    nodesels = hou.selectedNodes()
    vertslist = list()
    if len(nodesels):
        node = nodesels[0]
        geo = node.geometry()
        for prim in geo.prims():
            for pt in prim.points():
                pos = pt.position()
                for x in pos:
                    vertslist.append(x)
        print(vertslist)
        print(len(vertslist)/3)
        return vertslist

    else:
        return vertices


class CustomScene(QtWidgets.QGraphicsScene):
    def __init__(self):
        """Initializes the custom graphics scene. Sets up labels and default
           values for rotation and zoom factors."""

        QtWidgets.QGraphicsScene.__init__(self)
        self.xRot = 35.0
        self.yRot = 25.0
        self.lastPos = None
        self.zoom = 1.0

        self.rotationLabel = QtWidgets.QLabel("Rotation:  [35.0, 25.0]")
        self.rotationLabel.move(10, 10)
        self.rotationLabel.setFixedWidth(200)
        self.rotationLabel.setStyleSheet(label_style)

        self.zoomLabel = QtWidgets.QLabel("Zoom factor:  [1.0]")
        self.zoomLabel.move(10, 30)
        self.zoomLabel.setFixedWidth(200)
        self.zoomLabel.setStyleSheet(label_style)

        self.descLabel = QtWidgets.QLabel(desc_text)
        self.descLabel.move(10, 200)
        self.descLabel.setStyleSheet(light_label_style)
        self.descLabel.setFixedWidth(self.width())
        self.descLabel.setAlignment(
            QtCore.Qt.AlignHCenter | QtCore.Qt.AlignBottom)

        self.resetButton = QtWidgets.QPushButton("Reset Orientation")
        self.resetButton.move(10, 70)
        self.resetButton.clicked.connect(self.reset)

        self.addWidget(self.rotationLabel)
        self.addWidget(self.zoomLabel)
        self.addWidget(self.descLabel)
        self.addWidget(self.resetButton)

        self.glInit = False
        self.shader = None

    def reset(self):
        self.xRot = 35.0
        self.yRot = 25.0
        self.zoom = 1.0
        self.rotationLabel.setText("Rotation:  [35.0, 25.0]")
        self.zoomLabel.setText("Zoom factor:  [1.0]")
        self.update()

    def wheelEvent(self, event):
        """Called when the mouse wheel is rotated. Increases or decreases
           the zoom factor based on the mouse wheel."""

        QtWidgets.QGraphicsScene.wheelEvent(self, event)

        if event.isAccepted():
            return

        self.zoom -= event.delta() / 2000.0
        if self.zoom < 0.1:
            self.zoom = 0.1

        self.zoomLabel.setText("Zoom factor:  [" + str(self.zoom) + "]")
        self.update()

    def mousePressEvent(self, event):
        """ Called when a mouse button is pressed. Stores the mouse pos."""

        QtWidgets.QGraphicsScene.mousePressEvent(self, event)

        if event.buttons() == QtCore.Qt.LeftButton:
            self.lastPos = event.scenePos()

    def mouseMoveEvent(self, event):
        """Called when the mouse moves. Rotates the viewport"""

        QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

        if event.isAccepted():
            return

        if event.buttons() == QtCore.Qt.LeftButton:
            pos = event.scenePos()
            if self.lastPos is None:
                self.lastPos = pos
            else:
                deltaX = pos.x() - self.lastPos.x()
                deltaY = pos.y() - self.lastPos.y()
                self.lastPos = pos

                self.yRot += deltaX
                self.xRot += deltaY

                if self.xRot > 90:
                    self.xRot = 90
                elif self.xRot < -90:
                    self.xRot = -90

                if self.yRot > 180:
                    self.yRot -= 360
                elif self.yRot < -180:
                    self.yRot += 360

                self.rotationLabel.setText("Rotation:  [" + str(self.xRot) +
                                           ", " + str(self.yRot) + "]")
                self.update()

    def initGL(self):
        """ Initializes OpenGL resources if they have not already been created"""
        if self.glInit:
            return

        self.glInit = True

        vertex_shader = shaders.compileShader("""
            #version 150
            layout(location = 0) in vec3 a_position;
            layout(location = 1) in vec3 a_color;
            layout(location = 2) in vec2 a_texture;

            uniform mat4 model; 
            uniform mat4 view;
            uniform mat4 projection;

            //out vec3 v_color;
            //out vec2 v_texture;
            void main()
            {
                mat4 mvp = projection * view * model;
                gl_Position = mvp * vec4(a_position, 1.0);
                //v_color = a_color;
                //v_texture = a_texture;
            }
            """, GL_VERTEX_SHADER)

        fragment_shader = shaders.compileShader("""
            #version 150
            //in vec3 v_color;
            //in vec2 v_texture;

            uniform float f_opacity;

            void main()
            {
                gl_FragColor = vec4(1.0,0.0,0.0,f_opacity);
            }
            """, GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(vertex_shader, fragment_shader)
        self.uniforms = {
            'model': glGetUniformLocation(self.shader, 'model'),
            'view': glGetUniformLocation(self.shader, 'view'),
            'projection': glGetUniformLocation(self.shader, 'projection'),
            'f_opacity': glGetUniformLocation(self.shader, 'f_opacity'),
        }

        # vert
        # box_verts = updatamodel()
        # verts = float_array(box_verts)

        # vertex buffer object
        VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes,
                     vertices, GL_STATIC_DRAW)

        # element buffer object
        EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                     indices.nbytes, indices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                              vertices.itemsize*8, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE,
                              vertices.itemsize*8, ctypes.c_void_p(vertices.itemsize * 3))

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE,
                              vertices.itemsize*8, ctypes.c_void_p(vertices.itemsize * 6))

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
        # ca = math.cos(0.0)
        # cb = math.cos(self.xRot / 180.0 * 3.14159)
        # ch = math.cos(self.yRot / 180.0 * 3.14159)

        # sa = math.sin(0.0)
        # sb = math.sin(self.xRot / 180.0 * 3.14159)
        # sh = math.sin(self.yRot / 180.0 * 3.14159)

        # r = [ch*ca,  -ch*sa*cb + sh*sb,  ch*sa*sb + sh*cb,    0.0,
        #      sa,     ca*cb,              -ca*sb,              0.0,
        #      -sh*ca, sh*sa*cb + ch*sb,   (-sh*sa*sb + ch*cb), 0.0,
        #      0.0,    0.0,                -3.0,                1.0]
        # rot = float_array(r)

        # s = [x_scale, 0.0,     0.0,     0.0,
        #      0.0,     y_scale, 0.0,     0.0,
        #      0.0,     0.0,     z_scale, 0.0,
        #      0.0,     0.0,     0.0,     1.0]
        # scale = float_array(s)

        # glUniformMatrix4fv(self.uniforms["m_scale"], 1, GL_FALSE, scale)
        # glUniformMatrix4fv(self.uniforms["m_rot"], 1, GL_FALSE, rot)

        # glUniform1fv(self.uniforms["f_opacity"], 1, opacity)

        # glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        # glEnableClientState(GL_VERTEX_ARRAY)
        # glVertexPointer(3, GL_FLOAT, 0, None)

        # glDrawArrays(GL_TRIANGLES, 0, 36)

        # glDisableClientState(GL_VERTEX_ARRAY)
        # glBindBuffer(GL_ARRAY_BUFFER, 0)
        translation = pyrr.matrix44.create_from_translation(
            pyrr.Vector3([0, 0, 0]))
        scale = pyrr.matrix44.create_from_scale(pyrr.Vector3([1, 1, 1]))
        model = pyrr.matrix44.multiply(scale, translation)
        view = pyrr.matrix44.create_from_translation(pyrr.Vector3([0, 0, -2]))
        projection = pyrr.matrix44.create_perspective_projection_matrix(
            45, 1280/720, 0.1, 100)

        glUniformMatrix4fv(self.uniforms["model"], 1, GL_FALSE, model)
        glUniformMatrix4fv(self.uniforms["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(
            self.uniforms["projection"], 1, GL_FALSE, projection)
        glUniform1fv(self.uniforms["f_opacity"], 1, opacity)

        glDrawElements(GL_TRIANGLES, len(indices), GL_UNSIGNED_INT, None)

    def drawBackground(self, painter, rect):
        """ Called when the scene should render it's background. Can use GL."""

        QtWidgets.QGraphicsScene.drawBackground(self, painter, rect)

        # PyOpenGL is needed for this example
        if not py_gl_found:
            return

        # Init GL
        self.initGL()

        # Update the label to match the size of the graphics scene
        self.descLabel.setFixedWidth(self.width())
        self.descLabel.setFixedHeight(self.height() - 230)

        # Clear the viewport
        glClearColor(0.2, 0.28, 0.32, 1.0)
        glClearDepth(1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Enable blending and culling
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glEnable(GL_CULL_FACE)

        # Activate the shader for the box
        shaders.glUseProgram(self.shader)

        # Set the projection matrix
        # self.setProjection()

        # Draw the boxes
        self.drawBox(2, 2, 2, 1)

        # Unbind the shader
        shaders.glUseProgram(0)

        # Restore the GL state
        glDisable(GL_BLEND)
        glDisable(GL_CULL_FACE)


if __name__ == "__main__":
    pass
    # app = QtWidgets.QApplication(sys.argv)
    # a = MainForm()
    # a.show()
    # sys.exit(app.exec_())
