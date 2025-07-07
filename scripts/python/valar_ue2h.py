from posixpath import split
import unreal
import sys
import os
import json
import time

def exportMesh22(export_folder):
    # 检测下导出路径是否合法
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)
        unreal.log("create folder...")
    if export_folder[-1] != "/":
        export_folder += "/"

    selected = unreal.GlobalEditorUtilityBase.get_default_object().get_selected_assets()
    asset_export = unreal.AssetExportTask()
    asset_export.automated = True
    for each in selected:
        exportName = each.get_name()
        asset_export.set_editor_property("object", each)
        asset_export.set_editor_property("filename", export_folder + exportName + ".fbx")
        asset_export.options = unreal.FbxExportOption()
        result = unreal.Exporter.run_asset_export_task(asset_export)
        if result:
            unreal.log("fbx export success...")

# 获取资产依赖
def ls_dependencies(path):
    #获取资产的依赖资产
    asset_lib = unreal.EditorAssetLibrary
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    data = asset_lib.find_asset_data(path)
    options = unreal.AssetRegistryDependencyOptions()
    options.include_hard_package_references = True
    dependencies = asset_registry.get_dependencies(data.package_name, options)
    return dependencies

# 直接获取材质参数
def ls_matparamter(material):
    tex_list = []
    try:
        tex_para = material.texture_parameter_values
        for each in tex_para:
            tex_list.append(each.parameter_value)
    except:
        pass
    return tex_list

# 贴图导出
def exportTextures(export_folder,tex_to_export):

    # 检测下导出路径是否合法
    if export_folder[-1] != "/":
        export_folder += "/"
    print(tex_to_export)
    # 导出路径设置
    texfullpath = str(tex_to_export.get_path_name())
    #print(texfullpath)
    pathlist = texfullpath.split("/")
    newfullpath = ""
    #print(pathlist)
    for i in range(1,len(pathlist)-1):
        # if (i==1 and pathlist[i]=='Game'):
        #     continue
        newfullpath += pathlist[i] + "/"
    new_export_path = export_folder + newfullpath
    if not os.path.exists(new_export_path):
        os.makedirs(new_export_path)
    # tga导出设置
    tga_exporter = unreal.TextureExporterTGA()
    task = unreal.AssetExportTask()
    task.object = tex_to_export
    #print(new_export_path)
    task.filename = new_export_path + str(tex_to_export.get_name()) + ".tga"
    task.exporter = tga_exporter
    task.automated = True
    task.prompt = False
    unreal.Exporter.run_asset_export_task(task)
    # print("task_file：" , task.filename)
    return task.filename

# mesh导出
def exportMesh(export_folder,mesh_to_export):

    # 检测下导出路径是否合法
    if export_folder[-1] != "/":
        export_folder += "/"

    # 导出路径设置
    meshfullpath = mesh_to_export.get_path_name()
    pathlist = meshfullpath.split("/")
    newfullpath = ""
    for i in range(1,len(pathlist)-1):
        # if (i==1 and pathlist[i]=='Game'):
        #     continue
        newfullpath += pathlist[i] + "/"
    new_export_path = export_folder + newfullpath
    if not os.path.exists(new_export_path):
        os.makedirs(new_export_path)
    # fbx的导出配置
    # https://docs.unrealengine.com/4.26/en-US/PythonAPI/class/FbxExportOption.html?highlight=fbxexportoption#unreal.FbxExportOption
    fbx_option = unreal.FbxExportOption()
    # fbx_option.ascii = False
    fbx_option.collision = False
    # fbx_option.export_local_time = False
    # fbx_option.export_morph_targets  = False
    # fbx_option.export_preview_mesh  = False
    # fbx_option.fbx_export_compatibility  = 2013
    fbx_option.level_of_detail   = False
    # fbx_option.map_skeletal_motion_to_root   = False
    fbx_option.vertex_color = True

    # 导出配置
    # https://docs.unrealengine.com/4.26/en-US/PythonAPI/class/AssetExportTask.html
    meshname = mesh_to_export.get_name()
    task = unreal.AssetExportTask()
    task.automated = True
    task.object = mesh_to_export
    task.filename = new_export_path + meshname + ".fbx"
    task.options = fbx_option

    # 执行导出
    result = unreal.Exporter.run_asset_export_task(task)
    if result:
        unreal.log(meshname + " export success...")

# export unreal level object
def exportLevelObejct(export_folder,selected = True):

    # 检测下导出路径是否合法
    if export_folder[-1] != "/":
        export_folder += "/"
    
    # 输出结果：需要导出的mesh，场景中的actor信息，导出的json文件信息，
    result = []

    levelinfolist = []      # 场景信息
    mesh_exportlist = []    # 需要导出的资产列表
    tex_exportlist = []     # 需要导出的资产列表
    # instance of unreal class
    asset_lib = unreal.EditorAssetLibrary
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    string_lib = unreal.StringLibrary
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

    # 导出选中的
    if selected:
        actors = unreal.EditorLevelLibrary.get_selected_level_actors()
        # actors = unreal.GlobalEditorUtilityBase.get_default_object().get_selected_assets()
    for actor in actors:
        if not isinstance(actor,unreal.StaticMeshActor):
            continue
        # 当前actor的名字
        #print("actor_name: '%s'"%actor.get_name(),end = " ")
        #print("label_name: '%s'"%actor.get_actor_label(),end = " ")
        cur_component = actor.static_mesh_component
        cur_mesh = cur_component.static_mesh
        if cur_mesh not in mesh_exportlist:
            mesh_exportlist.append(cur_mesh)
        # 当前mesh的名字
        #print("mesh name : '%s'"%cur_mesh.get_name(),end=" ")

        folder_path  = actor.get_folder_path()
        if str(folder_path) != "None":
            path = str(folder_path) + "/" + str(actor.get_actor_label())
        else:
            path = actor.get_actor_label()
        #print('path : ' + path)
        # actor transform in level 
        current_trans = cur_component.get_world_location()
        current_rot = cur_component.get_world_rotation()
        current_scale = cur_component.get_world_scale()

        # actor material and textures
        materials = cur_component.get_materials()
        # print(materials)
        mat_infos = []
        mat_index = 0
        for mat in materials:
            mat_info = {}
            mat_texs = []
            # print('sdddd',mat.texture_parameter_values)
            # print('Material Name ：' + mat.get_name())
            asset_folder = unreal.Paths.get_path(mat.get_path_name())
            asset_path = mat.get_path_name() 
            #textures = ls_dependencies(asset_path)
            textures = ls_matparamter(mat)
            for tex in textures:
                tex_exportlist.append(tex)
                tex_outpath = export_folder[0:-1] + ('/').join(tex.get_path_name().split('/')[0:-1]) + "/" + tex.get_name() + '.tga'
                mat_texs.append(tex_outpath)
            mat_info['mat_name'] = str(mat.get_name())
            mat_info['mat_group'] = str(cur_mesh.get_material(mat_index).get_name()) # 记录下原本mesh的材质
            # for tex in textures:
            #     if 'EngineResources' in string_lib.conv_name_to_string(tex.get_full_name()):
            #         continue
            #     data = asset_lib.find_asset_data(tex)
            #     # 过滤非贴图资产 | 不用 `isinstance` 的方式可以不用加载资产
            #     if not issubclass(getattr(unreal, str(data.asset_class)), unreal.Texture):
            #         continue 
            #     tex_exportlist.append(data)
            #     # 把贴图路径存到json文件中
            #     mat_texs.append(export_folder[:-1] +str(data.package_path) + "/" + str(data.asset_name)+ ".tga")   
            mat_info['texs'] = mat_texs
            mat_infos.append(mat_info)
            mat_index += 1

        mesh_data = {}
        # mesh 
        mesh_data['actor_name'] = actor.get_actor_label()
        mesh_data['actor_id'] = actor.get_name()
        mesh_data['level_path'] = path
        mesh_data['mesh_name'] = cur_mesh.get_name()
        mesh_data['ue_path'] = ('/').join(cur_mesh.get_path_name().split('/')[0:-1])
        mesh_data['mesh_path'] = export_folder[0:-1] + ('/').join(cur_mesh.get_path_name().split('/')[0:-1]) + "/" + cur_mesh.get_name() + '.fbx'
        mesh_data['world_trans'] = [x for x in current_trans.to_tuple()]
        mesh_data['world_rot'] = [x for x in current_rot.to_tuple()]
        mesh_data['world_scale'] = [x for x in current_scale.to_tuple()]

        # textures
        mesh_data['mat_num'] = str(len(materials))
        mesh_data['mat_info'] = mat_infos

        levelinfolist.append(mesh_data)


    # 输出json文件
    print(levelinfolist)
    js_file = json.dumps(levelinfolist,indent=2)
    js_name = time.ctime(time.time()).replace(" ","_").replace(":","_")
    js_path = export_folder + 'ue_info/' + str(js_name) +".json"
    if not os.path.exists(export_folder + 'ue_info/'):
        os.makedirs(export_folder + 'ue_info/')
    with open(js_path,'w') as f:
        f.write(js_file)

    # 输出场景中的mesh fbx
    for mesh in mesh_exportlist:
        exportMesh(export_folder,mesh)

    # 输出场景中的贴图
    for tex in tex_exportlist:
        exportTextures(export_folder,tex)

    # 存储Houdini所需信息
    result.append(js_path)

    config_data = {}
    config_data['js_path'] = js_path
    config_file = json.dumps(config_data,indent = 2)
    config_path = export_folder + 'ue_info/' +  "config.json"
    if not os.path.exists(export_folder + 'ue_info/'):
        os.makedirs(export_folder + 'ue_info/')

    with open(config_path,'w') as f:
        f.write(config_file)     
    return result

def exportContentObject(export_folder,selected = True):
    # 检测下导出路径是否合法
    if export_folder[-1] != "/":
        export_folder += "/"
        
    # 为了优化导出速度，暂时不考虑导出贴图
    exportTexture = False
    # 输出结果：需要导出的mesh，场景中的actor信息，导出的json文件信息，
    result = []

    levelinfolist = []      # 场景信息
    mesh_exportlist = []    # 需要导出的资产列表
    tex_exportlist = []     # 需要导出的资产列表
    # instance of unreal class
    asset_lib = unreal.EditorAssetLibrary
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    string_lib = unreal.StringLibrary
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
# 导出选中的
    if selected:
        # actors = unreal.EditorLevelLibrary.get_selected_level_actors()
        meshes = unreal.GlobalEditorUtilityBase.get_default_object().get_selected_assets()
    for mesh in meshes:
        if not isinstance(mesh,unreal.StaticMesh):
            continue
        # 当前actor的名字
        #print("mesh_name: '%s'"%actor.get_name(),end = " ")
        if mesh not in mesh_exportlist:
            mesh_exportlist.append(mesh)
        # 当前mesh的名字
        #print("mesh name : '%s'"%cur_mesh.get_name(),end=" ")

        # folder_path  = actor.get_folder_path()
        # if str(folder_path) != "None":
        #     path = str(folder_path) + "/" + str(actor.get_actor_label())
        # else:
        #     path = actor.get_actor_label()
        #print('path : ' + path)

        # actor material and textures
        materials = mesh.static_materials
        mat_infos = []
        mat_index = 0
        # print(materials)
        for staticmat in materials:
            mat_info = {}
            mat_texs = []
            mat = staticmat.material_interface
            #textures = ls_dependencies(asset_path)
            textures = ls_matparamter(mat)
            # print(textures)
            if exportTexture:
                for tex in textures:
                    tex_exportlist.append(tex)
                    tex_outpath = export_folder[0:-1] + ('/').join(tex.get_path_name().split('/')[0:-1]) + "/" + tex.get_name() + '.tga'
                    mat_texs.append(tex_outpath)
            mat_info['mat_name'] = str(mat.get_name())
            mat_info['mat_group'] = str(mesh.get_material(mat_index).get_name()) # 记录下原本mesh的材质
            if exportTexture:
                for tex in textures:
                    if 'EngineResources' in string_lib.conv_name_to_string(tex.get_full_name()):
                        continue
                    data = asset_lib.find_asset_data(tex.get_path_name())
                    # 过滤非贴图资产 | 不用 `isinstance` 的方式可以不用加载资产
                    if not issubclass(getattr(unreal, str(data.asset_class)), unreal.Texture):
                        continue 
                    tex_exportlist.append(tex)
                    # 把贴图路径存到json文件中
                    mat_texs.append(export_folder[:-1] +str(data.package_path) + "/" + str(data.asset_name)+ ".tga")   
                mat_info['texs'] = mat_texs
            mat_infos.append(mat_info)
            mat_index += 1

        mesh_data = {}
        # mesh 
        mesh_data['mesh_name'] = mesh.get_name()
        mesh_data['ue_path'] = ('/').join(mesh.get_path_name().split('/')[0:-1])
        mesh_data['mesh_path'] = export_folder[0:-1] + ('/').join(mesh.get_path_name().split('/')[0:-1]) + "/" + mesh.get_name() + '.fbx'

        # textures
        mesh_data['mat_num'] = str(len(materials))
        mesh_data['mat_info'] = mat_infos

        levelinfolist.append(mesh_data)

    # 输出json文件
    js_file = json.dumps(levelinfolist,indent=2)
    js_name = time.ctime(time.time()).replace(" ","_").replace(":","_")
    js_path = export_folder + 'ue_info/' + str(js_name) +".json"
    if not os.path.exists(export_folder + 'ue_info/'):
        os.makedirs(export_folder + 'ue_info/')
    with open(js_path,'w') as f:
        f.write(js_file)

    # 输出场景中的mesh fbx
    for mesh in mesh_exportlist:
        exportMesh(export_folder,mesh)

    # 输出场景中的贴图

    if exportTexture:
        for tex in tex_exportlist:
            exportTextures(export_folder,tex)

    # 存储Houdini所需信息
    result.append(js_path)

    config_data = {}
    config_data['js_path'] = js_path
    config_file = json.dumps(config_data,indent = 2)
    config_path = export_folder + 'ue_info/' +  "config.json"
    if not os.path.exists(export_folder + 'ue_info/'):
        os.makedirs(export_folder + 'ue_info/')

    with open(config_path,'w') as f:
        f.write(config_file)     
    return result

def exportAssetfromContent(exportpath):
    unreal.log("**********************************************")
    unreal.log("**********************************************")
    unreal.log("**********************************************")
    exportContentObject(exportpath)

def exportAssetfromLevel(exportpath):
    unreal.log("**********************************************")
    unreal.log("**********************************************")
    unreal.log("**********************************************")
    exportLevelObejct(exportpath)  