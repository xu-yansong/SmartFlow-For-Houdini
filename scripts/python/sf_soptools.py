import hou
import os


# set node color by node type
class NodeColoring(object):
    _colorlist = {
        0: (1,0.725,0),
        1: (0,0.7,0),
        2: (0.5,0,1),
        3: (0.8,0.016,0.016),
        4: (0.9,0.8,0.55),
        5: (0.188,0.529,0.459),
        6: (0.8,0.8,0.8)
    }
    def __init__(self):
        super().__init__()
        self.nodelist = None
        self.init_member()
    
    def init_member(self) -> None:
        nodes = list(hou.selectedNodes())
        if not nodes:
            obj = hou.node('/obj')
            nodes = []
            nodes.append(obj)
        self.nodelist = nodes

    def setColor(self) -> None:

        for node in self.nodelist:
            subchilds = self.findNodes(node)
            for child in subchilds:
                choice = self.checkType(child)
                #根据是否bypass返回一个布尔值
                is_bypass = self.checkPass(child)
                #加颜色
                self.addColor(child,choice,is_bypass)

    #遍历指定节点下的所有节点--不迭代版本
    def findNodes(self,node):
        nodelists = []
        nodelists.append(node)
        for child in node.allSubChildren():
            nodelists.append(child)
        return nodelists
    
    #检测节点类型
    def checkType(self,node):   
        typename = node.type().name()
        if typename == 'file' or typename == 'alembic':
            return 0
        elif typename == 'null':
            return 1
        elif typename == 'object_merge':
            return 2
        elif typename == 'dopnet' or typename == 'solver':
            return 3
        elif typename == 'filecache' or typename == 'filecache_xys':
            return 4
        elif typename == 'rop_alembic' or typename == 'rop_geometry':
            return 5
        else: 
            return 6
        
    #检测节点是否被屏蔽ByPass
    def checkPass(self,node):
        try:
            isBypass = node.isBypassed()
        except:
            isBypass = 0
        if isBypass:
            return 1
        else:
            return 0
    
    #定义添加颜色的函数    
    def addColor(self,node,choice = 6,isBypass = 0):
        if not isBypass:
            color = hou.Color(self._colorlist[choice])
            node.setColor(color)            
        else:
            color = hou.Color((0,0,0))
            node.setColor(color)   

# batch import 
class BatchImport(object):
    def __init__(self):
        super().__init__()

    #获取指定文件夹的文件列表
    def getfilelists(self):
        
        path_lists = []
        geo_path = hou.ui.selectFile(title = 'select yout directory',file_type = hou.fileType.Directory)
        path_lists.append(geo_path)
        
        geo_fullpath = hou.expandString(geo_path)
        file_lists = os.listdir(geo_fullpath)
        path_lists.append(file_lists)
        
        return path_lists
    
    #导入相机文件,创建file节点读取文件
    def createfileNode(self):
        
        obj_nodes = [] 
        path_lists = self.getfilelists()
        if path_lists:
            geo_path = path_lists[0]
            
            obj = hou.node('/obj')
            scene_scale = obj.createNode('null','scene_scale')
            scene_scale.parm('scale').set(0.01)
            loader = obj.createNode('geo','setup')
            
            if len(path_lists[1]):
                merge_node = loader.createNode('merge')
            for each in path_lists[1]:        
                obj_path = geo_path + each
                obj_name = os.path.splitext(each)[0]
                extension = os.path.splitext(each)[1].lower()
                #判断文件名字里是否有cam关键字，有则直接在场景里倒入
                if 'cam' in each:        
                    if extension == '.fbx':
                        fbx_cam = hou.hipFile.importFBX(obj_path)
                        #print(fbx_cam)
                        fbx_cam[0].setFirstInput(scene_scale)
                        #
                        for child in fbx_cam[0].children():
                            if len(child.inputs())==0:
                                child.setFirstInput(fbx_cam[0].indirectInputs()[0])
                        
                    if extension == '.abc':
                        abc_cam = obj.createNode('alembicarchive',obj_name)
                        abc_cam.parm('fileName').set(obj_path)
                        abc_cam.parm('buildHierarchy').pressButton()
                        abc_cam.setFirstInput(scene_scale)
                        
                #非相机文件直接导进geometry
                else:
                    if extension == '.abc':
                        abc_obj = loader.createNode('alembic',obj_name)
                        abc_obj.parm('fileName').set(obj_path)
                        abc_obj.parm('missingfile').set(1)
                        abc_transform = abc_obj.createOutputNode('xform')
                        abc_transform.parm('scale').setExpression('ch("../../'+scene_scale.name()+'/scale")')
                        abc_null = abc_transform.createOutputNode('null','OUT_'+obj_name)
                        merge_node.setNextInput(abc_null)
                        obj_nodes.append(abc_null)
                    else:
                        ext_obj = loader.createNode('file',obj_name)
                        ext_obj.parm('file').set(obj_path)
                        ext_obj.parm('missingframe').set(1)
                        ext_transform = ext_obj.createOutputNode('xform')
                        ext_transform.parm('scale').setExpression('ch("../../'+scene_scale.name()+'/scale")')
                        ext_null = ext_transform.createOutputNode('null','OUT_'+obj_name)
                        merge_node.setNextInput(ext_null)
                        obj_nodes.append(ext_null)
            #layout节点
            obj.layoutChildren()
            loader.layoutChildren()                                        

# camera
class CameraFactory(object):
    def __init__(self):
        super().__init__()

    # get the resolution of input
    def input_res(self) -> list:
        result = hou.ui.readMultiInput(message = 'set camera resolution',input_labels = ('resx','resy'),initial_contents = ('1920','1080'))[1]
        return result
    
    # get all camera
    def get_all_camera(self) -> list:
        camlist = []
        obj = hou.node('/obj')
        for child in obj.allSubChildren():
            if child.type().name() == 'cam':
                camlist.append(child)
        return camlist
    
    # get child camera for node
    def get_camera_from_node(self,node) -> list:
        camlist = []
        if node.type().name() == 'cam':
            camlist.append(node)
        for child in node.allSubChildren():
            if child.type().name()== 'cam':
                camlist.append(child)
        return camlist

    # set camera
    def set_camera_res(self) -> None:
        res = self.input_res()
        print(res)
        camlist = self.get_all_camera()
        if camlist:
            for cam in camlist:
                cam.parm('resx').set(res[0])
                cam.parm('resy').set(res[1])
    
    # create fetch node
    def create_fetch_camera(self,camlist) -> None:
        plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        parent = plane.pwd()
        currentpos = plane.selectPosition()
        
        for cam in camlist:
            
            camname = cam.name()
            fetchNode = parent.createNode("fetch")
            camNode = parent.createNode("cam",camname)
            
            fetchNode.setPosition(currentpos)
            fetchNode.parm("fetchobjpath").set(cam.path())
            fetchNode.parm("useinputoffetched").set(1)
            fetchNode.parm("fetchsubnet").set(1)
            fetchNode.setDisplayFlag(False)
            
            camNode.setPosition(fetchNode.position())
            camNode.move([0,-1])
            camNode.parm("tx").setExpression('origin("","../'+fetchNode.name()+'/","TX")')
            camNode.parm("ty").setExpression('origin("","../'+fetchNode.name()+'/","TY")')
            camNode.parm("tz").setExpression('origin("","../'+fetchNode.name()+'/","TZ")')
            camNode.parm("rx").setExpression('origin("","../'+fetchNode.name()+'/","RX")')
            camNode.parm("ry").setExpression('origin("","../'+fetchNode.name()+'/","RY")')
            camNode.parm("rz").setExpression('origin("","../'+fetchNode.name()+'/","RZ")')
            camNode.parm("resx").set(2048)
            camNode.parm("resy").set(1152)
            camNode.parm("focal").setExpression('ch("'+cam.path()+'/focal")')
            camNode.parm("aperture").setExpression('ch("'+cam.path()+'/aperture")')
            camNode.parm("far").set(1000000)
            currentpos[0] +=2

    # fetch camera
    def fetch_camera(self) -> None:
        camlist = []
        nodes = hou.selectedNodes()
        if nodes:
            for node in nodes:
                camlist += self.get_camera_from_node(node)
            print(camlist)
            self.create_fetch_camera(camlist)

# project
class ProjectFactory(object):
    def __init__(self):
        super().__init__()
        

    def get_input_data(self) -> None:
        projectPath = hou.ui.selectFile(start_directory = 'E:/',title = 'please select your projectpath',file_type = hou.fileType.Directory)
        #print(projectPath)
        if projectPath[-1] != '/':
            projectPath = os.path.split(projectPath)[0]+'/'
        
        #print(projectPath)
        origin_framerange = hou.playbar.frameRange()
        origin_fps = hou.fps()
        origin_start = origin_framerange[0]
        origin_end = origin_framerange[1]
        origin_fps = origin_fps
        
        input_result = hou.ui.readMultiInput(message = 'input the shot name',
                                        title = 'input the shot name',
                                        input_labels = ('shot_name','author','startframe','endframe','fps'),
                                        buttons=('OK','Cancel'),
                                        initial_contents = ('cam_0001','xys',str(origin_start),str(origin_end),str(origin_fps)),
                                        default_choice = 0,
                                        close_choice = 1)
        input_result = list(input_result)
        input_result[0] = projectPath
        return input_result
    
    def createfolder(self) -> None:
        input_result = self.get_input_data()
        projectPath = input_result[0]
        shot_Name = input_result[1][0]
        shot_Auther = input_result[1][1]
        shot_Start = float(input_result[1][2])
        shot_End = float(input_result[1][3])
        shot_Fps = float(input_result[1][4])
        
        shot = projectPath + shot_Name
        houdini = projectPath + shot_Name + '/houdini/'
        maya = projectPath + shot_Name + '/maya/'
        comp = projectPath + shot_Name + '/comp/'
        
        cache = houdini + '/cache/'
        geo = houdini +'/geo/'
        Jpg = houdini +'/Jpg/'
        prev = houdini +'/prev/'
        render = houdini +'/render/'
        texture = houdini +'/texture/'
        
        os.mkdir(shot)
        os.mkdir(houdini)
        os.mkdir(maya)
        os.mkdir(comp)
        
        os.mkdir(cache)
        os.mkdir(geo)
        os.mkdir(Jpg)
        os.mkdir(prev)
        os.mkdir(render)
        os.mkdir(texture)
        
        nk_name = comp + shot_Name+'_comp_'+shot_Auther+'_v001.001.nk'
        nk = open(nk_name,'w')
        nk.close()
        
        hou.setFps(shot_Fps)
        hou.playbar.setFrameRange(shot_Start,shot_End)
        hou.playbar.setPlaybackRange(shot_Start,shot_End)
        hou.setFrame(shot_Start)
        hip_name = shot_Name + '_fx_' + shot_Auther + '_v001.001.hip'
        hou.hipFile.save(houdini+hip_name)

# cache
class CacheFactory(object):
    def __init__(self):
        super().__init__()

# according reference focus 
class FindFactory(object):
    def __init__(self):
        super().__init__()
    
    # get render node in geo
    def get_render_node(self,node) -> hou.node:
        if node.type().name() != "geo":
            return 
        for child in node.children():
            if child.isRenderFlagSet():
                renderNode = child
                break
            if child.isDisplayFlagSet():
                renderNode = child
        return renderNode

    # get sop material
    def get_material(self,node) -> str:
        if isinstance(node,hou.SopNode) | isinstance(node,hou.ObjNode):
            attr = None
            if node.type().name() == "geo":
                mat_path = node.parm('shop_materialpath').eval()
                render_node = self.get_render_node(node)
                attr = render_node.geometry().findPrimAttrib('shop_materialpath')
                if attr:
                    return attr.strings()[0]
                else:
                    if mat_path:
                        return mat_path
                    else:
                        print('can not find material...')
                        return
            else:
                attr = node.geometry().findPrimAttrib('shop_materialpath')
                if attr:
                    return attr.strings()[0]
                else:
                    mat_path = node.parent().parm('shop_materialpath').eval()
                    if mat_path:
                        return mat_path
                    else:
                        print('can not find material...')
                        return
        else:
            print("select a obj or sop node...")

    # get object list
    def get_object_by_material(self,material_path) -> list:
        geolist = list()
        materiallist = list()
        matchlist = list()
        obj = hou.node('/obj')
        for child in obj.allSubChildren():
            if child.type().name() == "geo":
                geolist.append(child)
            if child.type().name() == "material":
                materiallist.append(child)
        for geo in geolist:
            if geo.parm("shop_materialpath").evalAsString() == material_path:
                matchlist.append(geo)
        
        for material in materiallist:
            attr = material.geometry().findPrimAttrib('shop_materialpath')
            if material_path in attr.strings():
                matchlist.append(material)
        return matchlist

    # jump to node
    def jump_to_node(self,nodepath) -> None:
        if nodepath:
            node = hou.node(nodepath)
            pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
            parentpath = node.parent().path()
            pane.cd(parentpath)
            hou.clearAllSelected()
            pane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
            node.setSelected(1)
            pane.homeToSelection()

    # jump to material
    def jump_to_material(self) -> None:
        nodes = hou.selectedNodes()
        if nodes:
            node = nodes[0]
            matpath = self.get_material(node)
            self.jump_to_node(matpath)

    # jump to object use selected material
    def jump_to_object(self) -> None:
        nodes = hou.selectedNodes()
        node = nodes[0]
        if isinstance(node,hou.VopNode): 
            mat_geolists = self.get_object_by_material(node.path())
            thismat_geolists = list()
            for each in mat_geolists:
                thismat_geolists.append(each.path())
            geo_index = hou.ui.selectFromList(choices=thismat_geolists,default_choices=([0]),exclusive=True,)
            selected_node = thismat_geolists[geo_index[0]]
            self.jump_to_node(selected_node)

# node
class NodeFactory(object):
    def __init__(self):
        super().__init__()

    # get attribute list
    def get_attribute_list(self,node,attrib_name,attrib_type = "prim") -> list:
        geo = node.geometry()
        if attrib_type == 'prim':
            attr = geo.findPrimAttrib('shop_materialpath')
            if attr != None:
                return attr.strings()
            else:
                return

    # seperate by attribute
    def seperate_by_attribute(self,attrib_name,attrib_type) -> None:
        node = hou.selectedNodes()[0]
        atrrib_list = self.get_attribute_list(node,attrib_name)
        if atrrib_list:
            sub_node = node.createOutputNode('subnet','seperate_by_mat')
            sub_node.move([0,-1])
            sub_node.setDisplayFlag(True)
            sub_node.setRenderFlag(True)
            fectch_input = sub_node.createNode('null','fectch_input')
            fectch_input.setFirstInput(sub_node.indirectInputs()[0])        
            merge_node = sub_node.createNode('merge')
            out_node = merge_node.createOutputNode('output')
            out_node.setDisplayFlag(True)
            out_node.setRenderFlag(True)
            for each_mat in atrrib_list:
                each_mat_name = hou.node(each_mat).name()
                
                blast_name = 'iso_' + each_mat_name
                blast_node = fectch_input.createOutputNode('attribwrangle',blast_name)
                merge_node.setNextInput(blast_node)
                blast_node.parm('class').set(1)
                blast_node.parm('snippet').set('if(s@{0} != "'.format(attrib_name)+str(each_mat)+'" )\n{\nremoveprim(0,@primnum,1);\n}')
            
            blast_name = 'iso_none'
            blast_node = fectch_input.createOutputNode('attribwrangle',blast_name)
            merge_node.setNextInput(blast_node)
            blast_node.parm('class').set(1)
            blast_node.parm('snippet').set('if(s@%s != "" ){removeprim(0,@primnum,1);}' % (attrib_name,))   
            sub_node.layoutChildren()

# set all file node missing parm to "no geometry"
def set_file_to_nogeometry():
    obj = hou.node('/obj')
    childs = obj.allSubChildren()
    nodelists = []
    for child in childs:
        typename = child.type().name()
        if (typename == 'file' or typename == 'filecache' or typename == 'dopio'):
            isError = child.parm('missingframe').eval()
            if not isError:
                nodelists.append(child)
    if nodelists:
        for node in nodelists:
            #print(node.path())
            node.parm('missingframe').set(1)

# copy node path
def copy_node():

    nodeGrp = hou.selectedNodes()
    path_info = []
    file = open("path.txt","w")
    
    for eachnode in nodeGrp:
        currentpath = eachnode.path()
        path_info.append(currentpath)
    nodepaths = path_info
    for eachpath in nodepaths:
        file.write(eachpath)
        file.write("\n")
    file.close()

# paste node path
def paste_node():
    
    plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    currentpos = plane.selectPosition()
    currentNode = plane.pwd()
    
    pastefile = open("path.txt","r")
    lineList = pastefile.readlines()
    numline = len(lineList)
    pastefile.close()
    
    mergeNode = currentNode.createNode("merge")
    mergeNode.setPosition(currentpos)
    mergeNode.move([0,-4])
        
    for num in range(numline):
        null_name = lineList[num].split("/")[-1][0:-1]
        merge_name ="objmer_"+lineList[num].split("/")[-1][0:-1]
        objmergenode = currentNode.createNode("object_merge",merge_name)    
        
        current_node = hou.node(lineList[num][0:-1])
        path = objmergenode.relativePathTo(current_node)
        objmergenode.parm("objpath1").set(path)
        objmergenode.parm("xformtype").set(1)
        objmergenode.setPosition(currentpos)
        
        null = objmergenode.createOutputNode("null",null_name)
        newcolor = hou.Color([0.65,0.1,0.1])
        null.setColor(newcolor)
        mergeNode.setNextInput(null)
        currentpos[0]+=3
        
    mergeNode.setDisplayFlag(True)
    mergeNode.setRenderFlag(True)

#定义主函数
def merge_node():
    nodes = hou.selectedNodes() 
    if nodes:
        plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        parent = plane.pwd()
        currentpos = plane.selectPosition()
        
        merge = parent.createNode('merge')
        merge.setPosition(currentpos)
        
        merge.setDisplayFlag(True)
        merge.setTemplateFlag(True)
        merge.setRenderFlag(True)
        
        for node in nodes:
            merge.setNextInput(node)       

#  pop node to obj 
def promote_render():
    selNodes = hou.selectedNodes()
    obj = hou.node('/obj')
    if selNodes:
        for node in selNodes:
            geo = obj.createNode('geo',node.name())
            geo.parm('geo_velocityblur').set(1)
            objmerge = geo.createNode('object_merge')    
            path = objmerge.relativePathTo(node)        
            objmerge.parm('objpath1').set(path)
            objmerge.parm('xformtype').set(1)

def quik_find():
    nodes = hou.selectedNodes()
    if nodes:
        node = nodes[0]
        if node.type().name() == "object_merge":
            despath = node.parm("objpath1").eval()
            desnode = hou.node(hou.text.abspath(despath,node.path()))
            plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
            
            hou.clearAllSelected()
            desnode.setSelected(1)
            plane.homeToSelection()
        else:
            print("选中的节点需要是objmerge类型------")

