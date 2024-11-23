#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File        : sf_doptools.py
@Time        : 2024/11/21 18:04:17
@Author      : xuyansong
@Version     : 1.0
@Description : None
@Software    : Visual Studio Code
'''

import vexpressionmenu
import hou

class RBDFactory(object):
    def __init__(self):
        super().__init__()

    def create_simgle_fragment(self):    
        selectNodes = hou.selectedNodes()
        if len(selectNodes):
            for node in selectNodes:
                vorNode = node.createOutputNode('voronoifracture')
                isoNode = node.createOutputNode('isooffset')
                sctterNode = isoNode.createOutputNode('scatter')
                
                vorNode.move([0,-2.5])
                vorNode.setInput(1,sctterNode,0)
                vorNode.setDisplayFlag(1)
                vorNode.setRenderFlag(1)
                
                isoNode.parm('samplediv').set(50)
                isoNode.move([0,0.5])
                
                sctterNode.parm('npts').set(100)
                sctterNode.parm('relaxpoints').set(0)
                sctterNode.parm('randomizeorder').set(0)
                sctterNode.parm('useemergencylimit').set(0)
                sctterNode.move([0,0.5])
                node.setSelected(0)

    def create_complex_fragment(self):    
        nodelist = hou.selectedNodes()
        if len(nodelist):
            for node in nodelist:
                parent = node.parent()
                fracture = parent.createNode("voronoifracture")
                scatter = parent.createNode("scatter")
                addnoise = parent.createNode("attribwrangle","add_noise")
                volume = parent.createNode("isooffset")
                uvwrap = parent.createNode("uvunwrap")
                uvtrans = parent.createNode("uvtransform")
                create_name = parent.createNode("assemble","assemble_name")
                create_pack = parent.createNode("assemble","assemble_pack")
                set_active = parent.createNode("attribwrangle","set_init")
                OUT_null = parent.createNode("null","OUT_"+node.name())
                
                volume.setNextInput(node)
                volume.setPosition(node.position())
                volume.move([1,-1])
                volume.parm("samplediv").set(50)
                
                scatter.setNextInput(volume)
                scatter.setPosition(volume.position())
                scatter.move([0,-1])
                scatter.parm("npts").set(1000)
                
                addnoise.setNextInput(scatter)
                addnoise.setPosition(scatter.position())
                addnoise.move([0,-1])
                addnoise.parm("snippet").set('vector freq = set(chv("freq"));\nvector offset = set(chv("offset"));\nfloat limit = fit(noise(@P*freq+offset),ch("minvalue"),ch("minvalue")+0.01,0,1);\n@Cd = set(limit,limit,limit);\nif(@Cd.x>0.5&&ch("del")==1)\n{\nremovepoint(0,@ptnum);\n}')
                vexpressionmenu.createSpareParmsFromChCalls(addnoise, 'snippet')
                addnoise.parm('minvalue').set(0.3)
                addnoise.parm('del').set(1)
                addnoise.parm("freqx").set(5)
                addnoise.parm("freqy").set(5)
                addnoise.parm("freqz").set(5)
                
                fracture.setNextInput(node)
                fracture.setPosition(node.position())
                fracture.move([0,-4])
                fracture.setColor(hou.Color([0.9,0.05,0.05]))
                fracture.insertInput(1,addnoise,0)
                
                uvwrap.setNextInput(fracture)
                uvwrap.setPosition(fracture.position())
                uvwrap.move([0,-1])
                uvwrap.parm("group").set("inside")
                uvwrap.parm("spacing").set(0)
                
                uvtrans.setNextInput(uvwrap)
                uvtrans.setPosition(uvwrap.position())
                uvtrans.move([0,-1])
                uvtrans.parm("group").set("inside")
                uvtrans.parm("tx").set(-1)
                
                
                create_name.setNextInput(uvtrans)
                create_name.setPosition(uvtrans.position())
                create_name.move([0,-1])
                create_name.parm("outside_group").set(node.name()+"_frac")
                create_name.parm("connect").set(1)
                
                
                create_pack.setNextInput(create_name)
                create_pack.setPosition(create_name.position())
                create_pack.move([0,-1])
                create_pack.parm("newname").set(0)  
                create_pack.parm("connect").set(1)
                create_pack.parm("pack_geo").set(1)
                
                set_active.setNextInput(create_pack)
                set_active.setPosition(create_pack.position())
                set_active.move([0,-1])
                set_active.parm("snippet").set('i@active = 1;\ni@deforming = 0;\nv@v = @v;')
                
                OUT_null.setNextInput(set_active)
                OUT_null.setPosition(set_active.position())
                OUT_null.move([0,-1])
                OUT_null.setColor(hou.Color([0.302,0.525,0.114]))
                
                OUT_null.setDisplayFlag(True)
                OUT_null.setRenderFlag(True)

    def init_rbd_network(self):
        plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        pos = plane.selectPosition()    
        node = plane.pwd()  
        
        dop = node.createNode("dopnet","rbd_sim")    
        dop.setPosition(pos)
        
        for child in dop.children():
            if child.name()=="output":
                grav = child.createInputNode(0,"gravity")
                solver = grav.createInputNode(0,"bulletrbdsolver")
                merge = solver.createInputNode(0,"merge","merge")

    def create_glue(self):
        nodeList = hou.selectedNodes()
        if len(nodeList):
            for node in nodeList:
                connect = node.createOutputNode("connectadjacentpieces")
                attwrangle = connect.createOutputNode("attribwrangle")
                null = attwrangle.createOutputNode("null")
                
                connect.parm("connecttype").set(1)
                attwrangle.parm("class").set(1)
                attwrangle.parm("snippet").set('s@constraint_name = "Glue";\ns@constraint_type = "all";')
                null.setName("OUT_Glue")

    #check the type of selected
    def checkPrimType(self,node):
        geo = node.geometry()
        pr = geo.prims()[0]
        typeName = pr.type().name()
        #print(typeName)
        if typeName == "Polygon":
            constraitName = pr.attribValue("constraint_name")
            if constraitName == "Glue":
                return 1
            if constraitName == "Pin":
                return 2
        if typeName == "PackedFragment":
            return 0
    #####def addrbd function       
    def addRbd(self,node,selNode):
        path = "../../"+selNode.name()
        packObject = node.createInputNode(100,"rbdpackedobject",selNode.name())
        packObject.parm("soppath").set(path)
    
    #####def addglue function 
    def addGlue(self,node,selNode):
        path = "../../"+selNode.name()
        inputNode = node.inputs()[0]
        constraintNode = node.createInputNode(0,"constraintnetwork")
        glueNode = constraintNode.createInputNode(1,"glueconrel")
        
        constraintNode.parm("soppath").set(path)
        constraintNode.parm("showguide").set(0)
        glueNode.parm("dataname").set("Glue")
        constraintNode.setInput(0,inputNode,0)
        
    #####def addpin function 
    def addPin(self,node,selNode):
        path = "../../"+selNode.name()
        inputNode = node.inputs()[0]
        constraintNode = node.createInputNode(0,"constraintnetwork")
        pinNode = constraintNode.createInputNode(1,"hardconrel")
    #    solverNode = constraintNode.createInputNode(2,"sopsolver")
        
        constraintNode.parm("soppath").set(path)
        constraintNode.parm("showguide").set(0)
        pinNode.parm("dataname").set("Pin")
        constraintNode.setInput(0,inputNode,0)
    
    #def what to do
    def add_top_rbd(self):
        selectNodes = list(hou.selectedNodes())
        if len(selectNodes):
            for selNode in selectNodes:
                for dopNode in selNode.parent().children():
                    if dopNode.name() == "rbd_sim":
                        for node in dopNode.children():
                            if node.name() == "output" and self.checkPrimType(selNode) == 1:
                                self.addGlue(node,selNode)
                            if node.name() == "output" and self.checkPrimType(selNode) == 2:
                                self.addPin(node,selNode)
                            if node.name() == "merge" and self.checkPrimType(selNode) == 0:
                                self.addRbd(node,selNode)

    #寻找最下游的一个节点
    def findFinal(self,node):
        if not len(node.outputs()):
            #print('最后一次啦~！%s' % node.name())
            return node
        else:
            NextNode = node.outputs()[0]
            #print('我在else里面: %s' % NextNode.name())
            return self.findFinal(NextNode)  
            
    def createCollsionNode(self,node):
        input_nodes = node.inputs()
        merge = node.createInputNode(0,'merge')
        staticSolver = merge.createInputNode(0,'staticsolver')
        staticObject = staticSolver.createInputNode(0,'groundplane')
        #node.setDisplayFlag(1)
        if len(input_nodes):
            merge.setNextInput(input_nodes[0])

    def createground(self,node):
        findoutput = False
        if not len(node.children()):
            findoutput = True
            output = node.createNode('output')
            self.createCollsionNode(output)
        else:
            for child in node.children():
                if child.type().name() == 'output':
                    findoutput = True
                    self.createCollsionNode(child)
                    break
        if not findoutput:
            for child in node.children():
                if child.isDisplayFlagSet():
                    findoutput = True
                    child = self.findFinal(child)
                    output = child.createOutputNode('output')
                    
                    self.createCollsionNode(output)   
    #定义主函数
    def add_ground(self):
        nodes = hou.selectedNodes()
        
        hasdop = 0
        if len(nodes):
            for node in nodes:
                if node.type().name()=='dopnet':
                    hasdop+=1
                    self.createground(node)
                    node.layoutChildren()
        if hasdop==0:
            print('请选择一个动力学节点~~~！！！')

    #检测选择的节点包含什么类型
    def checkNodeType(self,node):
        typename = node.geometry().prims()[0].type().name()
        if typename == 'Polygon':
            return 0
        elif typename == 'VDB':
            return 1
        else:
            return 2

    #遍历出场景中所有的动力学节点非迭代版
    def findDop(self,node):
        dopnodelists = []
        if len(node.children()):
            for child in node.allSubChildren():
                if child.type().name() == 'dopnet':
                    dopnodelists.append(child)
        return dopnodelists
            
    #创建动力学节点                
    def createStaticCollsionNode(self,node,soppath,proxyvolume,isdeforming = 1):
        input_nodes = node.inputs()
        merge = node.createInputNode(0,'merge')
        staticSolver = merge.createInputNode(0,'staticsolver')
        staticObject = staticSolver.createInputNode(0,'staticobject')
        node.setDisplayFlag(1)
        if len(input_nodes):
            merge.setNextInput(input_nodes[0])
        
        staticObject.parm('soppath').set(soppath)
        staticObject.parm('animategeo').set(isdeforming)
        staticObject.parm('letsopsinterpolate').set(1)
        staticObject.parm('mode').set(6)
        staticObject.parm('uniformvoxels').set(5)
        staticObject.parm('divsize').set(0.1)
        staticObject.parm('proxyvolume').set(proxyvolume)
        
    #定义主函数            
    def add_collision(self):        
        obj = hou.node('/obj')
        ready_add_dopnote = []
        nodes = hou.selectedNodes()
        isdeforming = 1
        soppath = ''
        proxyvolume = ''
        choices = []
        #判断选中的物体有多少个，没选和选中超过2个都相应提示
        length = len(nodes)
        if length==0:
            print('\n')
            print('当前选择为空，先选择一下你要添加为碰撞的模型吧~！')
        elif length > 2:
            print('\n')
            print('是不是选到一些没用的东西了，兄弟~！')
        else:
            for node in nodes:
                    if self.checkNodeType(node)==0:
                        soppath = node.path()
                    if self.checkNodeType(node)==1:
                        proxyvolume = node.path()
            #通过ui选出需要添加的动力学节点                                               
            doplists = self.findDop(obj)
            for dop in doplists:
                choices.append(dop.path())
            choices = tuple(choices)
            dop_selected = hou.ui.selectFromList(choices,default_choices=([0]))
            for i in dop_selected:
                ready_add_dopnote.append(doplists[i])
                
            #通过ui选择碰撞是否是运动物体
            deforming_choiceLists = ('静态物体','运动物体')
            isdeforming = hou.ui.selectFromList(deforming_choiceLists,default_choices = ([1]),exclusive = True)[0]
            #print(isdeforming)
            #路径没获取到的时候，给用户一点点提示
            if soppath == '':
                print('\n')
                print('没选碰撞的几何体，路径自己加去吧')
            if proxyvolume == '':
                print('\n')
                print('没选碰撞的VDB，路径自己加去吧')
            #对选择的动力学节点添加碰撞    
            for node in ready_add_dopnote:
                findoutput = False
                if not len(node.children()):
                    findoutput = True
                    output = node.createNode('output')
                    self.createStaticCollsionNode(output,soppath,proxyvolume,isdeforming)
                else:
                    for child in node.children():
                        if child.type().name() == 'output':
                            findoutput = True
                            self.createStaticCollsionNode(child,soppath,proxyvolume,isdeforming)
                            break
                if not findoutput:
                    for child in node.children():
                        if child.isDisplayFlagSet():
                            findoutput = True
                            child = self.findFinal(child)
                            output = child.createOutputNode('output')
                            
                            self.createStaticCollsionNode(output,soppath,proxyvolume,isdeforming)
                #重新排列节点布局
                print('%s内部的碰撞添加完成~！'% node.path())
                node.layoutChildren()  

class SparseSmokeFactory(object):
    def __init__(self):
        super().__init__()

    #获取发射源的大小
    def getbbox(self,node):
        
        geo = node.geometry()
        bbox = geo.boundingBox()
        size = bbox.sizevec()
        #print(size)
        return size
        
    #获取发射源的中心    
    def getcent(self,node):
        
        geo = node.geometry()
        bbox = geo.boundingBox()
        center = bbox.center()
        
        return center       
    #返回geo内部的渲染节点
    def getRenderNode(self,node):
    
        for child in node.children():
            if child.isDisplayFlagSet():
                renderNode = child
                
        return renderNode
        
    #创建sparse—smoke的解算系统(obj内部)
    def createsparsesmoke_geo(self,nodes):
        for node in nodes:
            #判断选中的geo内部有没有节点，没有节点则默认创建一个box
            if len(node.children()):
                #print(node)
                rendernode = self.getRenderNode(node)
            else:
                rendernode = node.createNode('box')
                
            pos = node.position()    
            #判断内部节点的大小自动匹配下精度    
            size = self.getbbox(rendernode)
            cent = self.getcent(rendernode)
            max_size = max(size[0],size[1],size[2])
            initial_res = max_size/50
            
            #在obj下创建动力学和输出节点
            parent = node.parent()        
            smoke_dop = parent.createNode('dopnet','smoke_sim')
            dopnode = self.getRenderNode(smoke_dop)
            smoke_import = parent.createNode('geo','smoke_import')
            
            node.setDisplayFlag(0)
            smoke_dop.setDisplayFlag(0)
            smoke_dop.setPosition(pos)
            smoke_dop.move([0,-1])
            smoke_import.setPosition(pos)
            smoke_import.move([0,-2])        
            
            #创建发射源需要的节点
            pyro_source = rendernode.createOutputNode('pyrosource','create_density')
            add_noise = pyro_source.createOutputNode('attribnoise','add_noise')
            rasterize = add_noise.createOutputNode('volumerasterizeattributes','rasterize')
            out_src = rasterize.createOutputNode('null','OUT_src')
            
            pyro_source.parm('mode').set(2)
            pyro_source.parm('particlesep').set(initial_res*2)
            pyro_source.parm('attributes').set(2)
            pyro_source.parm('attribute1').set('density')
            pyro_source.parm('attribute2').set('temperature')
            
            add_noise.parm('mode').set(1)
            add_noise.parm('signature').set(0)
            add_noise.parm('attribs').set('density temperature')
            add_noise.parm('animated').set(1)
            add_noise.parm('remap').set(1)
            add_noise.parm('outmin1').set(0)
            
            add_noise.parm('pdf1pos').set(0)
            add_noise.parm('pdf1value').set(1)
            add_noise.parm('pdf2pos').set(1)
            add_noise.parm('pdf2value').set(0)
            
            rasterize.parm('attributes').set('density temperature v')
            rasterize.parm('voxelsize').set(initial_res)
            rasterize.parm('densityattrib').set('')
            rasterize.parm('normalize').set(1)        
            #创建动力学的节点
            pyrosolver = dopnode.createInputNode(0,'pyrosolver_sparse','pyro_solver')
            pyro = pyrosolver.createInputNode(0,'smokeobject_sparse','pyro')
            pyro_src = pyrosolver.createInputNode(2,'volumesource')
            
            smoke_dop.layoutChildren()
            pyro.parm('divsize').set(initial_res)
            pyro.parm('tx').set(cent[0])
            pyro.parm('ty').set(cent[1])
            pyro.parm('tz').set(cent[2])
            #solving--simulation
            pyrosolver.parm('adv_vel_reflect').set(1)
            pyrosolver.parm('temperature1').set(400)
            #solving--shape
            pyrosolver.parm('dissipation').set(0.01)
            pyrosolver.parm('enable_disturbance').set(1)
            pyrosolver.parm('disturbance').set(0.5)
            #sourcing
            pyro_src.parm('soppath').set(out_src.path())
            pyro_src.parm('resizefields').set(1)
            pyro_src.parm('numvolumes').set(3)
            pyro_src.parm('volume1').set('density')
            pyro_src.parm('vfield1').set('density')
            
            pyro_src.parm('volume2').set('temperature')
            pyro_src.parm('vfield2').set('temperature')
            pyro_src.parm('voperator2').set(8)
            pyro_src.parm('accguidestr2').set(25)
            pyro_src.parm('decguidestr2').set(0)
            
            pyro_src.parm('rank3').set(1)
            pyro_src.parm('volume3').set('v')
            pyro_src.parm('vfield3').set('vel')
            #创建输出节点
            dopio = smoke_import.createNode('dopio','import_fields')
            dopio.allowEditingOfContents()
    #        post = dopio.createOutputNode('pyropostprocess','post_process')
    #        attr_del = post.createOutputNode('attribdelete','del_attr')
            cache = dopio.createOutputNode('filecache','smoke_cache')
            cache.move([0,-2])
            
            dopio.parm('doppath').set(smoke_dop.path())
            dopio.parm('dopnode').set(pyro.path())
            
            dopio.parm('fields').set(4)
            dopio.parm('fieldname1').set('density')        
            dopio.parm('visible2').set(3)
            dopio.parm('fieldname2').set('vel')        
            dopio.parm('visible3').set(3)
            dopio.parm('fieldname3').set('flame')        
            dopio.parm('visible4').set(3)
            dopio.parm('fieldname4').set('temperature')
            dopio.parm("compression").set(1)
            dopio.parm("constanttol1").set(0.005)
            dopio.parm("quantizetol1").set(0.005)
            dopio.parm("usefp16_1").set(1)
            
            dopimport = dopio.children()[0]
            iso_density = dopimport.createOutputNode("blast","iso_density")
            iso_vel = dopimport.createOutputNode("blast","iso_vel")
            vol_resample = iso_vel.createOutputNode("volumeresample")
            field_merge = iso_density.createOutputNode("merge")
            dopimport.move([0,5])
            iso_density.setPosition(dopimport.position())
            iso_density.move([0,-2])
            iso_vel.setPosition(iso_density.position())
            iso_vel.move([4,0])
            vol_resample.setPosition(iso_vel.position())
            vol_resample.move([0,-1])
            field_merge.setPosition(iso_density.position())
            field_merge.move([0,-2])
            iso_density.parm("group").set("@name=vel.*")
            iso_vel.parm("group").set("@name=vel.*")
            iso_vel.parm("negate").set(1)
            vol_resample.parm("scale").set(0.5)
            field_merge.insertInput(1,vol_resample,0)
            render = dopio.path()+"/render"
            hou.node(render).setInput(0,field_merge,0) 
            switch = dopio.path()+"/switch1"
            hou.node(switch).setInput(0,field_merge,0)        
    #        post.parm('conv_vdb').set(1)
    #        post.parm('conv_doscale').set(1)
    #        post.parm('conv_usefp16').set(1)        
    #        
    #        attr_del.parm('primdel').set('* ^name')
    #        attr_del.parm('dtldel').set('* ^doppath ^rest2_ratio ^rest_ratio ^timescale ^varmap')
            
            
    #创建sparse—smoke的解算系统(geo内部)
    def createsparsesmoke(self,nodes):

        for node in nodes:
            size = self.getbbox(node)
            max_size = max(size[0],size[1],size[2])
            initial_res = max_size/50
            #createnode
            pyro_source = node.createOutputNode('pyrosource','create_density')
            add_noise = pyro_source.createOutputNode('attribnoise','add_noise')
            rasterize = add_noise.createOutputNode('volumerasterizeattributes','rasterize')
            pyrosolver = rasterize.createOutputNode('pyrosolver','pyrosolver')
    #        attr_del = pyrosolver.createOutputNode('attribdelete','del_attr')
            cache = pyrosolver.createOutputNode('filecache','smoke_cache')
            
            pyro_source.parm('mode').set(2)
            pyro_source.parm('particlesep').set(initial_res*2)
            pyro_source.parm('attributes').set(2)
            pyro_source.parm('attribute1').set('density')
            pyro_source.parm('attribute2').set('temperature')
            
            # add_noise.parm('mode').set(1)
            # add_noise.parm('signature').set(0)
            # add_noise.parm('attribs').set('density temperature')
            # add_noise.parm('animated').set(1)
            # add_noise.parm('remap').set(1)
            # add_noise.parm('outmin1').set(0)
            
            # add_noise.parm('pdf1pos').set(0)
            # add_noise.parm('pdf1value').set(1)
            # add_noise.parm('pdf2pos').set(1)
            # add_noise.parm('pdf2value').set(0)
    #        add_noise.parm('pdf3pos').set(0.75)
    #        add_noise.parm('pdf3value').set(0)
    #        add_noise.parm('pdf4pos').set(1)
    #        add_noise.parm('pdf4value').set(1)
            
            rasterize.parm('attributes').set('density temperature v')
            rasterize.parm('voxelsize').set(initial_res)
            rasterize.parm('densityattrib').set('')
            rasterize.parm('normalize').set(1)
            #setup
            pyrosolver.parm('divsize').set(initial_res)
            #solving--simulation
            pyrosolver.parm('adv_vel_reflect').set(1)
            #solving--shape
            pyrosolver.parm('dissipation').set(0.01)
            pyrosolver.parm('enable_disturbance').set(1)
            pyrosolver.parm('disturbance').set(0.5)
            #Sourcing
            pyrosolver.parm('numsources').set(3)
            pyrosolver.parm('source_volume1').set('density')
            pyrosolver.parm('source_vfield1').set('density')
            
            pyrosolver.parm('source_volume2').set('temperature')
            pyrosolver.parm('source_vfield2').set('temperature') 
            pyrosolver.parm('source_voperator2').set(8)
            pyrosolver.parm('source_accguidestr2').set(25)
            pyrosolver.parm('source_decguidestr2').set(0)
            
            pyrosolver.parm('source_rank3').set(1)
            pyrosolver.parm('source_volume3').set('v')
            pyrosolver.parm('source_vfield3').set('vel')        
            pyrosolver.parm('source_voperator3').set(1)
            
            # pyrosolver.allowEditingOfContents()
            # for child in pyrosolver.children():
            #     if child.type().name() == 'pyropostprocess':
            #         child.move([0,-5])
            #         child.bypass(1)
            #     if child.type().name() == 'dopimportfield':
            #         child.parm("compression").set(1)
            #         child.parm("constanttol1").set(0.005)
            #         child.parm("quantizetol1").set(0.005)
            #         child.parm("usefp16_1").set(1)
                    
            #         dopimport = child
            #         iso_density = dopimport.createOutputNode("blast","iso_density")
            #         iso_vel = dopimport.createOutputNode("blast","iso_vel")
            #         vol_resample = iso_vel.createOutputNode("volumeresample")
            #         field_merge = iso_density.createOutputNode("merge")
            #         iso_density.setPosition(dopimport.position())
            #         iso_density.move([0,-2])
            #         iso_vel.setPosition(iso_density.position())
            #         iso_vel.move([4,0])
            #         vol_resample.setPosition(iso_vel.position())
            #         vol_resample.move([0,-1])
            #         field_merge.setPosition(iso_density.position())
            #         field_merge.move([0,-2])
            #         iso_density.parm("group").set("@name=vel.*")
            #         iso_vel.parm("group").set("@name=vel.*")
            #         iso_vel.parm("negate").set(1)
            #         vol_resample.parm("scale").set(0.5)
            #         field_merge.insertInput(1,vol_resample,0)
            #         post = pyrosolver.path()+"/pyropostprocess1"
            #         hou.node(post).setInput(0,field_merge,0)
            #         out = pyrosolver.path()+"/output0"
            #         hou.node(out).move([0,-5])
                    
            #Export
    #        pyrosolver.parm('conv_vdb').set(1)
    #        pyrosolver.parm('conv_doscale').set(1)
    #        pyrosolver.parm('conv_usefp16').set(1)
            
    #        attr_del.parm('primdel').set('* ^name')
    #        attr_del.parm('dtldel').set('* ^doppath ^rest2_ratio ^rest_ratio ^timescale ^varmap')
    #定义主函数
    def smoke_quik_create(self):
        nodes = hou.selectedNodes()
        if len(nodes):
            if nodes[0].type().name() == 'geo':
                self.createsparsesmoke_geo(nodes)
            else:
                self.createsparsesmoke(nodes)


