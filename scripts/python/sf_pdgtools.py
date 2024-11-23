#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : sf_rendertools.py
@Time        : 2024/11/21 18:04:17
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''

import hou
import pdg

import os
import sys
import pdg
import hou


def getabspath(node, path):
    pdgnode = node.getPDGNode()
    abspath = pdgnode.scheduler.localizePath(path)
    return abspath


def createPDGDebugFile(node):
    try:
        inputlists = list()
        item = pdg.workItem()
        inputfilelists = item.attribArray("inputpath")
        outfilelists = item.attribArray("outputpath")
        optype = item.attribValue('operatortype').split("/")[-1]
        if optype == "":
            hdapath = item.attribValue('hda')[0]
            optype = hou.hda.definitionsInFile(hdapath)[0].nodeType().name()
            print(optype)
        for inputfile in inputfilelists:
            path = getabspath(node, inputfile)
            inputlists.append(path)
        name = node.name()
        index = item.index
        obj = hou.node("/obj")
        geo = obj.createNode("geo", name + "_" + str(index))
        hda = geo.createNode(optype)
        for each in inputlists:
            file = geo.createNode("file")
            file.parm("file").set(each)
            hda.setNextInput(file)
        index = 0
        for each in outfilelists:
            null = geo.createNode("null")
            null.setInput(0, hda, index)
            index += 1
        geo.layoutChildren()

    except:
        print("debug file create failure...")


def showOutputInExplorer(node):
    try:
        if node.type().name() == "topnet":
            node = node.displayNode()

        pdgnode = node.getPDGNode()
        item = pdg.workItem()
        outpath = pdgnode.scheduler.localizePath(
            item.attribValue("outputpath"))
        path, file = os.path.split(outpath)
        if os.path.exists(path):
            os.startfile(path)
        else:
            print("path not existing,cook node first...")
    except:
        print("select PDG workitem first...")


def outquickpreview(node):
    obj = hou.node("/obj")
    node = hou.node('/obj/PDG_View')
    if node != None:
        node.destroy()
    node = obj.createNode("geo", "PDG_View")
    input0 = node.createNode("file", "input_0")
    input0.parm('file').set("`@pdg_output.0`")

    input1 = node.createNode("file", "input_1")
    input1.parm('file').set("`@pdg_output.1`")
    input1.move([3, 0])

    input2 = node.createNode("file", "input_2")
    input2.parm('file').set("`@pdg_output.2`")
    input2.move([6, 0])

    input3 = node.createNode("file", "input_3")
    input3.parm('file').set("`@pdg_output.3`")
    input3.move([9, 0])
