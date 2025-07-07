import unreal
import sys
import os
import json
import time

def exportfbx2ue(asset_list):
    # asset_list =[{'path': 'C:/Users/xuyansong/Desktop/FBX/sss.fbx', 'isAni': 1, 'ue_path': '/Game/Temp/'}]
    for asset in list(asset_list):
        print(asset)
        fbx_path = asset['path']
        fbx_ani = False
        if asset['isAni']:
            fbx_ani = True
        print(fbx_ani)
        ue_path = asset['ue_path']
        # create import task 
        asset_import = unreal.AssetImportTask()
        asset_import.replace_existing = True
        asset_import.automated = True
        asset_import.destination_path = ue_path
        asset_import.filename = fbx_path
        
        # create import options
        options = unreal.FbxImportUI()
        # mesh setting
        # options.import_mesh = True
        options.auto_compute_lod_distances = False
        if fbx_ani:
            options.set_editor_property('import_as_skeletal', True)
            options.import_animations = True
            options.import_as_skeletal = True
            options.import_rigid_mesh = True
            options.create_physics_asset = True
            print(options)
            print(options.import_as_skeletal)
            options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
            # options.anim_sequence_import_data.animation_length = unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME
            options.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
            options.skeletal_mesh_import_data.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE
        else:
            options.mesh_type_to_import = unreal.FBXImportType.FBXIT_STATIC_MESH
            options.static_mesh_import_data.import_mesh_lo_ds = True
            options.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS
            options.static_mesh_import_data.vertex_color_import_option = unreal.VertexColorImportOption.REPLACE
        # material setting
        options.import_materials = False
        options.import_textures = False
        options.texture_import_data.material_search_location = unreal.MaterialSearchLocation.ALL_ASSETS

        asset_import.options = options

        print(asset_import.options)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([asset_import])

        # obj = unreal.load_asset(asset_import.imported_object_paths[0])
        # actor_location = unreal.Vector(0.0,0.0,0.0)
        # actor_rotation = unreal.Rotator(0.0,0.0,0.0)
        # unreal.EditorLevelLibrary.spawn_actor_from_object(obj, actor_location, actor_rotation)