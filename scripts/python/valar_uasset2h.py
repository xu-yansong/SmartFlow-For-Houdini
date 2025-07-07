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

def ue_exportLevelObj(exportpath):
    #try:
    dirname,filename = os.path.split(os.path.abspath(__file__))
    commands = '\n'.join(
        [
            'import sys',
            'if "%s" not in sys.path:'%dirname.replace("\\","/"),
            '\tsys.path.append(r"%s")'%dirname.replace("\\","/"),
            'import valar_ue2h',
            'from importlib import reload',
            'reload(valar_ue2h)',
            'valar_ue2h.exportAssetfromLevel("%s")'%exportpath,
        ]
    )
    run_unreal_python_commands(commands)
    # except:
    #     print("not export")

def ue_exportContentObj(exportpath):
    #try:
    dirname,filename = os.path.split(os.path.abspath(__file__))
    commands = '\n'.join(
        [
            'import sys',
            'if "%s" not in sys.path:'%dirname.replace("\\","/"),
            '\tsys.path.append(r"%s")'%dirname.replace("\\","/"),
            'import valar_ue2h',
            'from importlib import reload',
            'reload(valar_ue2h)',
            'valar_ue2h.exportAssetfromContent("%s")'%exportpath,
        ]
    )
                
    try:
        run_unreal_python_commands(commands)
    except:
        print("not export")

def createHouScenefromLevel(js_path):

    plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    pos = plane.selectPosition()
    node = plane.pwd()
    # according json file load asset in houdini
    with open(js_path,'r') as f:
        levelinfo = json.load(f)

    # create mesh node
    merge = node.createNode('merge','merge')
    merge.setPosition(pos)
    merge.move([0,-4])
    merge.setRenderFlag(True)
    merge.setDisplayFlag(True)
    i = 0
    for object in levelinfo:
        name = object['actor_name']
        path = hou.text.collapseCommonVars(object['mesh_path'])
        trans = object['world_trans']
        rot = object['world_rot']
        scale = object['world_scale']
        mat_num = object['mat_num']
        mat_info = object['mat_info']
        ue_content_path = object['ue_path']
        # create file
        file = node.createNode('valar_uasset',name)
        file.parm('file').set(path)
        file.setPosition(pos)
        file.move([i*3,0])

        # set transform
        file.parm('tx').set(trans[0])
        file.parm('ty').set(trans[2])
        file.parm('tz').set(trans[1])

        file.parm('rx').set(rot[0])
        file.parm('ry').set(rot[2]*-1)
        file.parm('rz').set(rot[1])

        file.parm('sx').set(scale[0])
        file.parm('sy').set(scale[2])
        file.parm('sz').set(scale[1])

        file.parm('uepath').set(ue_content_path)
        file.parm('material_slots').set(int(mat_num))
        # create shader
        shader = file.createOutputNode('quickmaterial')
        shader.parm('mMaterialEntries').set(int(mat_num))
        for num in range(int(mat_num)):
            mat_name = mat_info[num]['mat_name']
            file.parm('slotname' + str(num+1)).set(mat_name)
            mat_group = mat_info[num]['mat_group']
            # print(mat_name)
            texs = mat_info[num]['texs']
            # if len(texs):
            #     shader.parm('materialname_'+str(num+1)).set(mat_name)
            #     shader.parm('groupselection_'+str(num+1)).set(mat_group)
            #     shader.parm('basecolor_texture_'+str(num+1)).set(hou.text.collapseCommonVars(texs[0]))
        # merge all nodes    
        merge.setNextInput(shader)
        i += 1

def createHouScenefromContent(js_path):

    exportTexture = False
    plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    pos = plane.selectPosition()
    node = plane.pwd()
    # according json file load asset in houdini
    with open(js_path,'r') as f:
        levelinfo = json.load(f)
    # create mesh node
    merge = node.createNode('merge','merge')
    merge.setPosition(pos)
    merge.move([0,-4])
    merge.setRenderFlag(True)
    merge.setDisplayFlag(True)
    i = 0
    for object in levelinfo:
        name = object['mesh_name']
        path = hou.text.collapseCommonVars(object['mesh_path'])

        mat_num = object['mat_num']
        mat_info = object['mat_info']
        ue_content_path = object['ue_path']
        # create file
        file = node.createNode('valar_uasset',name)
        file.parm('file').set(path)
        file.setPosition(pos)
        file.move([i*3,0])

        file.parm('uepath').set(ue_content_path)
        file.parm('material_slots').set(int(mat_num))
        # create shader
        shader = file.createOutputNode('quickmaterial')
        shader.parm('mMaterialEntries').set(int(mat_num))
        for num in range(int(mat_num)):
            mat_name = mat_info[num]['mat_name']
            file.parm('slotname' + str(num+1)).set(mat_name)
            mat_group = mat_info[num]['mat_group']
            # print(mat_name)
            if exportTexture:
                texs = mat_info[num]['texs']
                if len(texs):
                    shader.parm('materialname_'+str(num+1)).set(mat_name)
                    shader.parm('groupselection_'+str(num+1)).set(mat_group)
                    shader.parm('principledshader_basecolor_texture_'+str(num+1)).set(hou.text.collapseCommonVars(texs[0]))
        # merge all nodes    
        merge.setNextInput(shader)
        i += 1


def importlevelAsset():

    # check the hipfile save
    # get hip file path 
    hipfilepath = hou.hipFile.path()
    if hipfilepath == 'C:/Users/' + getpass.getuser() + "/untitled.hip":
        print('please save hipfile...')
        return 
    exportpath = ("/").join(hipfilepath.split("/")[0:-1])
    print(exportpath)
    # export the selected actors in ue level 
    ue_exportLevelObj(exportpath)

    # # get current json file 
    with open(exportpath + '/ue_info' + "/config.json",'r') as f:
        load_dict = json.load(f)
    js_path = load_dict['js_path']

    # create scene
    createHouScenefromLevel(js_path)

def importContentAsset():

    # check the hipfile save
    # get hip file path 
    hipfilepath = hou.hipFile.path()
    if hipfilepath == 'C:/Users/' + getpass.getuser() + "/untitled.hip":
        print('please save hipfile...')
        return 
    exportpath = ("/").join(hipfilepath.split("/")[0:-1])

    # export the selected actors in ue level
    try: 
        ue_exportContentObj(exportpath)
    except:
        print('ue warning,switch to ue outputlog...')
    # # get current json file 
    with open(exportpath + '/ue_info' + "/config.json",'r') as f:
        load_dict = json.load(f)
    js_path = load_dict['js_path']

    # create scene
    createHouScenefromContent(js_path)