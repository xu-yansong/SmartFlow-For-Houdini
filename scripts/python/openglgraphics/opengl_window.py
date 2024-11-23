import pyrr
import numpy as np
from PySide2 import QtCore, QtWidgets
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


vertices_temp = [-0.5, -0.5, 0.5, 1.0, 0.0, 0.0, 0.0, 0.0,
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

indices_temp = [0, 1, 2, 2, 3, 0,
                4, 5, 6, 6, 7, 4,
                8, 9, 10, 10, 11, 8,
                12, 13, 14, 14, 15, 12,
                16, 17, 18, 18, 19, 16,
                20, 21, 22, 22, 23, 20]

# vertices_temp = np.array(vertices_temp, dtype=np.float32)
# indices_temp = np.array(indices_temp, dtype=np.uint32)


def updatamodel():
    node = hou.node("/obj/render")
    rendernode = node.renderNode()
    geo = rendernode.geometry()
    vertices_temp = list()
    for point in geo.points():
        pos = point.position()
        vertices_temp += pos
        if geo.findPointAttrib("Cd"):
            color = point.attribValue("Cd")
            vertices_temp += color
        else:
            vertices_temp += [1.0, 1.0, 1.0]
        if geo.findPointAttrib("uv"):
            uv = point.attribValue("uv")
            vertices_temp += uv[:2]
        else:
            vertices_temp += [0.0, 0.0]
        if geo.findPointAttrib("N"):
            N = point.attribValue("N")
            vertices_temp += N
        else:
            vertices_temp += [0.0, 1.0, 0.0]

    indices_temp = list()
    for pr in geo.prims():
        for pt in pr.points():
            indices_temp.append(pt.number())
    # print(vertices_temp)
    return vertices_temp, indices_temp


def init_scene():
    obj = hou.node("/obj")
    childs = obj.children()
    exist = False
    for child in childs:
        if child.name() == "render":
            exist = True
            return
    if not exist:
        render = obj.createNode("geo", "render")
        sphere = render.createNode("sphere", "sphere")
        sphere.parm("type").set(1)


class CustomScene(QtWidgets.QGraphicsScene):
    def __init__(self):
        """Initializes the custom graphics scene. Sets up labels and default
           values for rotation and zoom factors."""

        QtWidgets.QGraphicsScene.__init__(self)
        self.xRot = 35.0
        self.yRot = 25.0
        self.lastPos = None
        self.zoom = 1.0
        init_scene()
        a, b = updatamodel()
        self.vertices = np.array(a, dtype=np.float32)
        self.indices = np.array(b, dtype=np.uint32)
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

        self.resetButton = QtWidgets.QPushButton("Render")
        self.resetButton.move(10, 70)
        self.resetButton.clicked.connect(self.reset)

        # self.addWidget(self.rotationLabel)
        # self.addWidget(self.zoomLabel)
        # self.addWidget(self.descLabel)
        self.addWidget(self.resetButton)

        self.glInit = False
        self.shader = None

    def reset(self):
        self.xRot = 35.0
        self.yRot = 25.0
        self.zoom = 1.0
        self.rotationLabel.setText("Rotation:  [35.0, 25.0]")
        self.zoomLabel.setText("Zoom factor:  [1.0]")
        a, b = updatamodel()
        self.vertices = np.array(a, dtype=np.float32)
        self.indices = np.array(b, dtype=np.uint32)
        # print(a)
        # print(b)
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
            self.reset()

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
            in vec3 a_position;
            in vec3 a_color;
            in vec2 a_texture;
            in vec3 a_normal;

            uniform mat4 model; 
            uniform mat4 view;
            uniform mat4 projection;

            out vec3 v_color;
            out vec2 v_texture;
            void main()
            {
                mat4 mvp = projection * view * model;
                gl_Position = mvp * vec4(a_position, 1.0);
                v_color = a_color;
                //v_color = a_normal;
                v_texture = a_texture;
            }
            """, GL_VERTEX_SHADER)

        fragment_shader = shaders.compileShader("""
            #version 150
            in vec3 v_color;
            in vec2 v_texture;

            uniform float f_opacity;

            void main()
            {
                gl_FragColor = vec4(1,0,0,f_opacity);
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

    def drawBox(self, opacity):

        translation = pyrr.matrix44.create_from_translation(
            pyrr.Vector3([0, 0, 0]))
        scale = pyrr.matrix44.create_from_scale(pyrr.Vector3([1, 1, 1]))
        model = pyrr.matrix44.multiply(scale, translation)
        view = pyrr.matrix44.create_from_translation(
            pyrr.Vector3([0, 0, -3]))
        projection = pyrr.matrix44.create_perspective_projection_matrix(
            45, 1280/720, 0.1, 100)

        glUniformMatrix4fv(self.uniforms["model"], 1, GL_FALSE, model)
        glUniformMatrix4fv(self.uniforms["view"], 1, GL_FALSE, view)
        glUniformMatrix4fv(
            self.uniforms["projection"], 1, GL_FALSE, projection)
        glUniform1fv(self.uniforms["f_opacity"], 1, opacity)

        # vertex buffer object
        VBO = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, VBO)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes,
                     self.vertices, GL_STATIC_DRAW)

        # element buffer object
        EBO = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER,
                     self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE,
                              self.vertices.itemsize*11, ctypes.c_void_p(0))

        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE,
                              self.vertices.itemsize*11, ctypes.c_void_p(self.vertices.itemsize * 3))

        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE,
                              self.vertices.itemsize*11, ctypes.c_void_p(self.vertices.itemsize * 6))

        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 3, GL_FLOAT, GL_FALSE,
                              self.vertices.itemsize*11, ctypes.c_void_p(self.vertices.itemsize * 8))

        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)

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
        glClearColor(0.0, 0.0, 0.0, 0.0)
        # glClearDepth(1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Enable blending and culling
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        # glEnable(GL_CULL_FACE)

        # Activate the shader for the box
        shaders.glUseProgram(self.shader)

        # Set the projection matrix
        # self.setProjection()

        # Draw the boxes
        self.drawBox(1)

        # Unbind the shader
        shaders.glUseProgram(0)

        # Restore the GL state
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_BLEND)
        glDisable(GL_CULL_FACE)


if __name__ == "__main__":
    pass
    # app = QtWidgets.QApplication(sys.argv)
    # a = MainForm()
    # a.show()
    # sys.exit(app.exec_())
