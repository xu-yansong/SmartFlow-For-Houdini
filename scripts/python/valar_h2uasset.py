# -*- coding : utf-8 -*-
from imp import reload
import os
import os.path
import sys
import time
import remote_execution as remote
import hou
import json
import getpass

def run_unreal_python_commands(commands, failed_connection_attempts=0):
    """
    This function finds the open unreal editor with remote connection enabled, and sends it python commands.
    """
    remote_exec = remote.RemoteExecution()
    remote_exec.start()
    # wait a tenth of a second before attempting to connect
    time.sleep(0.1)

    # Execution modes (these must match the names given to LexToString for EPythonCommandExecutionMode in IPythonScriptPlugin.h)
    MODE_EXEC_FILE = 'ExecuteFile'  # Execute the Python command as a file. This allows you to execute either a literal Python script containing multiple statements, or a file with optional arguments
    MODE_EXEC_STATEMENT = 'ExecuteStatement'  # Execute the Python command as a single statement. This will execute a single statement and print the result. This mode cannot run files
    MODE_EVAL_STATEMENT = 'EvaluateStatement'  # Evaluate the Python command as a single statement. This will evaluate a single statement and return the result. This mode cannot run files
    exec_mode = MODE_EXEC_FILE

    try:
        # try to connect to an editor
        # for node in remote_exec.remote_nodes:
        #     remote_exec.open_command_connection(node.get("node_id"))
        remote_exec.open_command_connection(remote_exec.remote_nodes)
        if remote_exec.has_command_connection():
            # run the import commands and save the response in the global unreal_response variable
            global unreal_response
            unreal_response = remote_exec.run_command(commands, exec_mode=exec_mode)
            if unreal_response['success'] == True:
                return unreal_response['result']

        # otherwise make an other attempt to connect to the engine
        else:
            if failed_connection_attempts < 500:
                run_unreal_python_commands(remote_exec, commands, failed_connection_attempts + 1)
            else:
                remote_exec.stop()
                print("Could not find an open Unreal Editor instance!")

    # shutdown the connection
    finally:
        remote_exec.stop()

def export2ue(asset_list):
    #try:
    dirname,filename = os.path.split(os.path.abspath(__file__))
    commands = '\n'.join(
        [
            'import sys',
            'if "%s" not in sys.path:'%dirname.replace("\\","/"),
            '\tsys.path.append(r"%s")'%dirname.replace("\\","/"),
            'import h2ue',
            'from importlib import reload',
            'reload(h2ue)',
            'h2ue.exportfbx2ue({0})'.format(asset_list),
        ]
    )
    run_unreal_python_commands(commands)
    # except:
    #     print("not export")

def getRopInfo(node):
    asset_info = {}

    h_path = node.parm('sopoutput').eval()
    ue_attr = node.inputs()[0].geometry().findGlobalAttrib('ue_path')
    if node.parent().parm('custom_ue_path').evalAsInt() or ue_attr == None:
        ue_path = node.parent().parm('assetpath').eval()
    else:
        ue_path = ue_attr.strings()[0]
    
    asset_info['path'] = h_path
    asset_info['ue_path'] = ue_path
    asset_info['isAni'] = node.parm('trange').evalAsInt()
    return asset_info
    
def x20_run(node):

    # check the hipfile save
    # get hip file path 
    hipfilepath = hou.hipFile.path()
    if hipfilepath == 'C:/Users/' + getpass.getuser() + "/untitled.hip":
        print('please save hipfile...')
        return 
    exportpath = ("/").join(hipfilepath.split("/")[0:-1])

    # store the ropnode and fbx info need to import ue
    rop_list = []
    asset_list = []

    rop_ani = hou.node(node.path() + "/rop_ani")
    rop_ani_info = getRopInfo(rop_ani)

    rop_first = hou.node(node.path() + "/rop_first")
    rop_first_info = getRopInfo(rop_first)

    rop_last = hou.node(node.path() + "/rop_last")
    rop_last_info = getRopInfo(rop_last)

    rop_static = hou.node(node.path() + "/rop_static")
    rop_static_info = getRopInfo(rop_static)

    rop_list.append(rop_ani)
    rop_list.append(rop_first)
    rop_list.append(rop_last)
    rop_list.append(rop_static)

    asset_list.append(rop_ani_info)
    asset_list.append(rop_first_info)
    asset_list.append(rop_last_info)
    asset_list.append(rop_static_info)

    # print(rop_list)
    # print(asset_list)
    # # render fbx
    for rop in rop_list:
        rop.parm('execute').pressButton()

    # import asset to UE
    export2ue(asset_list)

