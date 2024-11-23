import re
import json
import cv2
import os
from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
import sys

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"


def convertEXR():
    path = "X:/LJ_JiNan/FX/GL_sc01_haitun/houdini/render/GL_sc01_haitun_effect_v001.0013.exr"
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    image = image[:, :, ::-1]
    cv2.imwrite(
        "X:/LJ_JiNan/FX/GL_sc01_haitun/houdini/render/GL_sc01_haitun_effect_v001.0013.jpg",
        image)


def generateJson():

    path = "D:/OneDrive/SongWork/HoudiniLibrary"
    jspath = path + "/" + "assetdatas.json"
    assetDatas = dict()

    typeinfo = dict()
    typeinfo['VFX'] = ['Fire', 'Smoke', 'Flip', 'RBD', 'Partice']
    typeinfo['PCG'] = ['Road', 'Biome', 'Rock', 'Terrain']
    assetDatas['typeinfo'] = typeinfo
    print(assetDatas)
    # with open(jspath, "w", encoding='utf-8') as f:
    #     json.dump(assetDatas, f, indent=4)


def rwjson():
    s = "X:/Plugins/Megascans Library/Downloaded/assetsData.json"
    s1 = "X:/Plugins/Megascans Library/Downloaded/test.json"

    ff = open(s, 'r', encoding='utf-8')
    sss = json.load(ff)
    with open(s1, "w", encoding='utf-8') as f:
        json.dump(sss, f, indent=4)


class sliderDemo(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Slider Demo")

        self.initUI()

    def initUI(self):
        baselayout = QtWidgets.QHBoxLayout()
        self.setLayout(baselayout)

        self.slider1 = QtWidgets.QSlider(QtGui.Qt.Horizontal)
        #self.slider1.setFixedHeight(100)
        self.slider1.setSliderDown(True)
        baselayout.addWidget(self.slider1)


# main
if __name__ == "__main__":
    # generateJson()
    # rwjson()
    app = QtWidgets.QApplication(sys.argv)
    w = sliderDemo()
    w.show()
    sys.exit(app.exec_())
