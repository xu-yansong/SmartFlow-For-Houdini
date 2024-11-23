# !usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author:
@software: PyCharm
@file: SmartFlowInstall.py
@time: 2022/6/02 10:27
"""

import os
import tkinter as tk
from tkinter import messagebox
import json


class SmartFlowInstallWindow(object):
    _version = ['19.0', '19.5', '20.0', '20.5', '21.0', '21.5', '22.0', '22.5']

    def __init__(self, path, name, show_file=False) -> None:
        super().__init__()
        self.plugin_path = path
        self.plugin_name = name
        self.show_file = show_file
        self.versionlist = ""
        self.doc_paths = list()
        self.otllist = list()
        self._init_member()

    def _init_member(self):
        # init doc_path
        for version in self._version:
            docpath = os.path.expanduser('~\Documents').replace("\\", "/") + "/houdini" + version
            '''
            判断当前版本的Houdini文件夹是否存在
            ~存在则安装
            ~不存在则不安装（所以需要用户曾经启动过一次Houdini）
            # TODO 改成从注册表判断Houdini版本是否安装过更合理
            '''
            if os.path.exists(docpath):
                self.versionlist += version + ","
                jsonpath = docpath + "/packages/"
                if not os.path.exists(jsonpath):
                    os.makedirs(jsonpath)
                self.doc_paths.append(jsonpath)

        # init pathlist
        self.otllist .append("$" + self.plugin_name)
        otlfolder = self.plugin_path + "/otls/"
        if os.path.exists(otlfolder):
            for eachfolder in os.listdir(otlfolder):
                if eachfolder == "backup":
                    continue
                if eachfolder == "ThirdParty":
                    thirdparty_folder = otlfolder + "/" + eachfolder
                    if os.path.isdir(thirdparty_folder):
                        self.otllist .append("$" + self.plugin_name + "/otls/" + eachfolder)
                        for subfolder in os.listdir(thirdparty_folder):
                            if subfolder == "backup":
                                continue
                            if os.path.isdir(thirdparty_folder + "/" + subfolder):
                                self.otllist .append("$" + self.plugin_name + "/otls/" + eachfolder + "/" + subfolder)

                else:
                    if os.path.isdir(otlfolder + "/" + eachfolder):
                        self.otllist .append("$" + self.plugin_name + "/otls/" + eachfolder)

    def generate_package_json(self) -> None:
        root = tk.Tk()
        root.withdraw()
        if self.doc_paths:
            packagefile = dict()
            packagefile["recommends"] = "houdini_version >= '19.0.561'"
            packagefile["load_package_once"] = True
            pathlist = list()

            tempdict = dict()
            tempdict['method'] = "prepend"
            tempdict['value'] = "$" + self.plugin_name
            pathlist.append(tempdict)

            packagefile['path'] = pathlist
            envlist = list()
            # plugin path
            tempdict = dict()
            tempdict[self.plugin_name] = self.plugin_path
            envlist.append(tempdict)
            # otl path
            tempdict = dict()
            tempdict['HOUDINI_OTLSCAN_PATH'] = dict()
            tempdict['HOUDINI_OTLSCAN_PATH']['method'] = "prepend"
            tempdict['HOUDINI_OTLSCAN_PATH']['value'] = self.otllist
            envlist.append(tempdict)

            packagefile['env'] = envlist

            # loop install
            for doc_path in self.doc_paths:
                json_file_path = doc_path + self.plugin_name + ".json"
                with open(json_file_path, 'w') as write_f:
                    json.dump(packagefile, write_f, indent=4, ensure_ascii=False)
                if self.show_file:
                    os.startfile(json_file_path)

            messagebox.showinfo("Setup Completing", " SmartFlow Install for %s" % self.versionlist)
        else:
            messagebox.showinfo("Setup Failed", "Try To Install or Restart Houdini First")

        root.destroy()


if __name__ == '__main__':
    plugin_path = os.getcwd().replace("\\", "/")
    Plugin_name = "SmartFlowForHoudini"
    install = SmartFlowInstallWindow(plugin_path, Plugin_name)
    install.generate_package_json()

# Cd D:/SmartFlowForHoudini/installPackage
# pyinstaller -F -w -i D:/SmartFlowForHoudini/installPackage/icons/Houdini.ico SmartFlowInstall.py
