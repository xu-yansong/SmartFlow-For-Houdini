
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
            
            pyrosolver.allowEditingOfContents()
            for child in pyrosolver.children():
                if child.type().name() == 'pyropostprocess':
                    child.move([0,-5])
                    child.bypass(1)
                if child.type().name() == 'dopimportfield':
                    child.parm("compression").set(1)
                    child.parm("constanttol1").set(0.005)
                    child.parm("quantizetol1").set(0.005)
                    child.parm("usefp16_1").set(1)
                    
                    dopimport = child
                    iso_density = dopimport.createOutputNode("blast","iso_density")
                    iso_vel = dopimport.createOutputNode("blast","iso_vel")
                    vol_resample = iso_vel.createOutputNode("volumeresample")
                    field_merge = iso_density.createOutputNode("merge")
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
                    post = pyrosolver.path()+"/pyropostprocess1"
                    hou.node(post).setInput(0,field_merge,0)
                    out = pyrosolver.path()+"/output0"
                    hou.node(out).move([0,-5])
                    
            #Export
    #        pyrosolver.parm('conv_vdb').set(1)
    #        pyrosolver.parm('conv_doscale').set(1)
    #        pyrosolver.parm('conv_usefp16').set(1)
            
    #        attr_del.parm('primdel').set('* ^name')
    #        attr_del.parm('dtldel').set('* ^doppath ^rest2_ratio ^rest_ratio ^timescale ^varmap')
    #定义主函数
    def quik_create(self):
        nodes = hou.selectedNodes()
        if len(nodes):
            if nodes[0].type().name() == 'geo':
                self.createsparsesmoke_geo(nodes)
            else:
                self.createsparsesmoke(nodes)
