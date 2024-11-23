#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : kt_assettools.py
@Time        : 2024/01/04 09:36:52
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''
import hou
import os
import re
import json
import assettools
from typing import (cast, Any, Callable,Iterable, NamedTuple, Optional,
                    Sequence, TypedDict, TypeVar, Union)


def isInHoudiniFileSystem(definition):
    if definition.libraryFilePath().startswith(hou.text.expandString('$HFS')):
        return True


def isVersionedDefinition(definition):
    """ Returns if the definition is version in the format: major.minor

        :param defintion: the HDADefition by hou.node.type().definition()
    """

    name_components = definition.nodeType().nameComponents()
    user = name_components[1]
    global_ver = name_components[3]

    if "." in global_ver:
        return True


def isVHDA(node):
    if not node.canCreateDigitalAsset():
        definition = node.type().definition()
        if definition:
            return isVersionedDefinition(definition)
    return False


def isHDA(node):
    if not node.canCreateDigitalAsset():
        definition = node.type().definition()
        if definition:
            return True
    return False


def getToolSubmenus(hda_def):
    """ Returns the tab submenu entries of this node.
        Note: A node could be placed in multipe entries at once.

        :param defintion: the HDADefition by hou.node.type().definition()
    """

    import xml.etree.ElementTree as ET
    if hda_def.hasSection('Tools.shelf'):
        sections = hda_def.sections()
        ts_section = sections['Tools.shelf'].contents()
        try:
            root = ET.fromstring(ts_section)
        except ET.ParseError:
            return None
        tool = root[0]
        submenus = tool.findall('toolSubmenu')
        if submenus:
            tool_submenus = []
            for submenu in submenus:
                if submenu is not None:
                    text = submenu.text
                    if text:
                        tool_submenus.append(submenu.text)
            if tool_submenus:
                return tool_submenus
            else:
                return None
        else:
            return None
    else:
        return None

class HDAFactory():
    def __init__(self,otlpath):
        super().__init__()
        self.otlpath = otlpath

    # rename Label & Submenu
    def run(self) -> None:
        def_list = self.get_all_definition()
        for defn in def_list:
            # rename submenu
            old_submenu = self.get_submenu(defn)
            new_submenu = old_submenu.replace("Dyys VFX","Smart Flow").replace("Digital Assets","Smart Flow").replace("Dyys PCG","Smart Flow")
            self.set_submenu(defn,new_submenu)

            # rename Label
            old_label = defn.description()
            new_lable = old_label.replace("Dyys","SF")

            # append Prefix
            if old_label[:2] != "SF":
                new_lable = "SF " + old_label
            defn.setDescription(new_lable)

    # get all hda
    def get_all_hda(self) -> list:
        hdalist = list()
        for root,dirs,files in os.walk(self.otlpath):
            for file in files:
                name,extension = os.path.splitext(file)
                if extension != ".hda" and extension != ".otl":
                    continue
                if "backup" in root or "ThirdParty" in root:
                    continue
                hdalist.append(os.path.join(root,file))
        return hdalist

    # get all definition
    def get_all_definition(self) -> list:
        hdalist = self.get_all_hda()
        def_list = list()
        for hda in hdalist:
            hou.hda.installFile(hda)
            def_list += hou.hda.definitionsInFile(hda)
        return def_list

    # get submenu
    def get_submenu(self,defn) -> Optional[str]:
        return assettools.assetTabSubMenu(defn)
    
    # set submenu
    def set_submenu(self,defn,menu_name) -> None:
        return assettools.setTabSubMenu(defn,menu_name)



