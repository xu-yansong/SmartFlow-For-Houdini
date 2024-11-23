# !usr/bin/env python
# -*- coding: GBK -*-
"""
@author: T5610ws
@software: PyCharm
@file: smartflow_path.py
@time: 2022/10/2 12:33
"""
import hou
import os
import sys
import os.path
import assettools

from PySide2 import QtCore, QtGui, QtWidgets


class HDAPublish(QtWidgets.QDialog):
    def __init__(self, parent, node, newasset=True):
        super(HDAPublish, self).__init__(parent)

        self.newasset = newasset
        self.node = node
        self.type_name = node.type().name()

        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("Publish Assets")
        self.buildUI()
        self.resize(self.minimumSizeHint())

    def buildUI(self):

        checkbox_width = hou.ui.scaledSize(25)
        label_width = hou.ui.scaledSize(75)
        label_ident = hou.ui.scaledSize(10)
        parm_width = hou.ui.scaledSize(150)
        row_height = checkbox_width
        button_spacer_width = hou.ui.scaledSize(200)

        # BASE LAYOUT ----------------------------
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        gbcolumn_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(gbcolumn_layout)

        # SIMPLE FOLDER - Name Construction ----------------------------
        name_gb_box = QtWidgets.QGroupBox("Name Construction")
        gbcolumn_layout.addWidget(name_gb_box)
        name_gb_layout = QtWidgets.QGridLayout()
        name_gb_box.setLayout(name_gb_layout)
        # Type Name
        type_name_label = QtWidgets.QLabel("Type Name")
        type_name_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        type_name_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        type_name_label.setIndent(label_ident)
        self.type_name_edit = QtWidgets.QLineEdit(self.type_name)
        self.type_name_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        name_gb_layout.addWidget(type_name_label, 0, 1)
        name_gb_layout.addWidget(self.type_name_edit, 0, 2)

        tooltip_text = "The base name of the asset, describes the node's purpose"
        type_name_label.setToolTip(tooltip_text)
        self.type_name_edit.setToolTip(tooltip_text)

        # Branch
        self.namespace_branch_enable_checkbox = QtWidgets.QCheckBox()
        self.namespace_branch_enable_checkbox.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
        self.namespace_branch_enable_checkbox.setChecked(False)

        namespace_branch_label = QtWidgets.QLabel("Branch")
        namespace_branch_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        namespace_branch_label.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)
        namespace_branch_label.setIndent(label_ident)

        self.namespace_branch_edit = QtWidgets.QComboBox(self)
        self.namespace_branch_edit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.namespace_branch_edit.setEditable(True)

        name_gb_layout.addWidget(self.namespace_branch_enable_checkbox, 2, 0)
        name_gb_layout.addWidget(namespace_branch_label, 2, 1)
        name_gb_layout.addWidget(self.namespace_branch_edit, 2, 2)

        tooltip_text = "Adds a \"branch\" name to the namespace to distinguish assets in different parts of the development cycle"
        self.namespace_branch_enable_checkbox.setToolTip(tooltip_text)
        namespace_branch_label.setToolTip(tooltip_text)
        self.namespace_branch_edit.setToolTip(tooltip_text)
        # Asset Name Preview
        previewname_label = QtWidgets.QLabel("Preview")
        previewname_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        previewname_label.setIndent(label_ident)

        self.asset_name_preview = QtWidgets.QLabel()
        self.asset_name_preview.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)

        name_gb_layout.addWidget(previewname_label, 4, 1)
        name_gb_layout.addWidget(self.asset_name_preview, 4, 2)

        # Properties
        name_gb_layout.setColumnMinimumWidth(0, checkbox_width)
        name_gb_layout.setColumnMinimumWidth(1, label_width)
        name_gb_layout.setColumnMinimumWidth(2, parm_width)

        name_gb_layout.setRowMinimumHeight(0, row_height)
        name_gb_layout.setRowMinimumHeight(1, row_height)
        name_gb_layout.setRowMinimumHeight(2, row_height)
        name_gb_layout.setRowMinimumHeight(3, row_height)
        name_gb_layout.setRowMinimumHeight(4, row_height)

        name_gb_layout.setRowStretch(5, 2)
# open hda in explorer


def openpath(path):
    # print(path)
    if os.path.exists(path):
        os.startfile(path)
    else:
        print("hda path no existing...")


# get hda path
def showhdainexplorer(node):
    hda_type = node.type().name()
    hda_def = node.type().definition()
    if hda_type == "hdaprocessor":
        outfile = node.parm('inputfile').eval()
        path, file = os.path.split(outfile)
        openpath(path)
    else:
        if assettools.isInHoudiniFileSystem(hda_def):
            print("hda is original houdini asset... ")
        else:
            # try:
            libpath = hda_def.libraryFilePath()
            name = node.type().name()
            a = HDAPublish(hou.qt.mainWindow(), node)
            a.show()

            name_components = hda_def.nodeType().nameComponents()
            user = name_components[1]
            global_ver = name_components[3]
            # print(name_components)
            # print(user)
            # label = node.type().label()
           # print(name)
            tool_submenus = assettools.getToolSubmenus(hda_def)
            print(tool_submenus)
            all = assettools.getAllToolSubmenus(node_type_category='Sop')
            # print(all)
            # menu = node.type().menu
            path, file = os.path.split(libpath)
            # openpath(path)
        # except:
        #     print("hda is not custom type ...")
