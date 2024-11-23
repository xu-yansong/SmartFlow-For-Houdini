#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : rename.py
@Time        : 2024/11/20 21:31:07
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''
import os
import shutil


# rename hda
def rename_hda() -> None:
    filepath = os.path.dirname(os.path.abspath(__file__))
    otlpath = "/".join(filepath.split("\\")[:-1]) + "/otls"
    for root, dirs, files in os.walk(otlpath):
        for f in files:
            old = os.path.join(root, f)
            new_f = f.lower()
            if new_f.split("_")[0] == "dyys":
                new_f = new_f.replace("dyys", "sf")
            new = os.path.join(root, new_f)
            os.rename(old, new)

def remove_backup() -> None:
    filepath = os.path.dirname(os.path.abspath(__file__))
    otlpath = "/".join(filepath.split("\\")[:-1]) + "/otls"
    for root, dirs, files in os.walk(otlpath):
        for dir in dirs:
            if dir == "backup":
                path = os.path.join(root,dir)
                print(path)
                shutil.rmtree(path)

if __name__ == "__main__":
    # rename_hda()
    remove_backup()
