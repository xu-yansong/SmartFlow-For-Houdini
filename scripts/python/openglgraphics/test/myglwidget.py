import Ui_myglwidget
import sys
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets


class MainWindow(QtWidgets.QMainWindow, Ui_myglwidget.Ui_MainWindow):
    def __init__(self):
        super().__init__()  # super()构造器方法返回父级的对象。
        self.setupUi(self)  # 加载ui


app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
w.show()
sys.exit(app.exec_())
