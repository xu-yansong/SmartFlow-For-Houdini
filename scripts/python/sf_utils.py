#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : smartflow_showHDAinexplorer.py
@Time        : 2022/10/05 17:02:31
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''

import os
import assettools
import sf_assettools
from typing import (cast, Any, Callable,Iterable, NamedTuple, Optional,
                    Sequence, TypedDict, TypeVar, Union)

from imp import reload
reload(sf_assettools)


# open hda in explorer
def openpath(path):
    # print(path)
    if os.path.exists(path):
        os.startfile(path)
    else:
        print("hda path not existing...")


# get hda path
def showhdainexplorer(node):
    hda_type = node.type().name()
    hda_def = node.type().definition()
    if hda_type == "hdaprocessor":
        outfile = node.parm('inputfile').eval()
        path, file = os.path.split(outfile)
        openpath(path)
    else:
        if sf_assettools.isInHoudiniFileSystem(hda_def):
            print("hda is original houdini asset... ")
        else:
            libpath = hda_def.libraryFilePath()
            path, file = os.path.split(libpath)
            openpath(path)



    
        
    
