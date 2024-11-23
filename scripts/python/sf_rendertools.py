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
import sys

class MotionVectorFactory(object):
    def __init__(self):
        super().__init__()

    # get all mantra
    def get_all_mantra_nodes(self) -> list:
        mantra_lists = []
        mat = hou.node('/out')
        if len(mat.children()):
            for child in mat.children():
                if child.type().name() == 'ifd':
                    mantra_lists.append(child)
        return mantra_lists
    
    # check renderpass exists
    def check_render_layer(self,mantra) -> list:
        result = [True,True]
        num = mantra.parm('vm_numaux').eval()
        if num:
            for i in range(num):
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='mv_cam':
                    result[0] = False
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='mv_vel':
                    result[1] = False                             
        return result  
    
    # add motion vector render pass
    def add_mv_cam(self,mantra) -> None:
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('mv_cam')
        mantra.parm('allowmotionblur').set(1)
        mantra.parm('vm_imageblur').set(0)

    # add velocity render pass
    def add_mv_vel(self,mantra) -> None:
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('mv_vel')

    def add_layer(self,mantra) -> None:
        result = self.check_render_layer(mantra)
        if result[0]:
            self.add_mv_cam(mantra)
        else:
            print('{0} mv_cam layer exists...'.format(mantra.path()))
        if result[1]:
            self.add_mv_vel(mantra)
        else:
            print('{0} mv_vel layer exists...' .format(mantra.path()))

    # add layer to selected mantra nodes
    def add_mvlayer_to_mantra(self) -> None:
        nodes = hou.selectedNodes()
        if not nodes:
            nodes = self.get_all_mantra_nodes()
            print("mantra node not selected, set all ...")
        for node in nodes:
            if node.type().name() == "ifd":
                self.add_layer(node)

    #定义函数找到of的输入端
    def findOfInput(self,node):
        
        node_and_index = [None,None,1]
        hasfind = 1
        node.allowEditingOfContents(1)
        if len(node.children()):
            for child in node.children():
                if child.type().name() =='output':
                    if child.parm('contexttype').eval() == 'surface':
                        inputs = child.inputConnectors()
                        #测试打印output节点的所有输入端
    #                    print(inputs)
                        if len(inputs[1]):
                            temp = inputs[1][0]
                            inputnode = temp.inputNode()
                            inputindex = temp.outputIndex()
                            node_and_index[0] = inputnode
                            node_and_index[1] = inputindex
                            #测试打印连接到Of端口的节点和输出端口
    #                        print(inputnode)
    #                        print(inputindex)
                        else:
                            hasfind = 0
        else:
            hasfind = 0
        node_and_index[2] = hasfind               
        return node_and_index            
    
    #定义函数判断材质内是否有体积节点，返回一个布尔值。有则调用速度的时候用vel，没有则用v
    def check_volume(self,node):
        findvol = 0
        if len(node.children()):
            for child in node.children():
                typename = child.type().name()
                if typename == 'volumemodel' or typename == 'volumeshadercore' or typename == 'pyroshadercore':
                    findvol = 1
        return findvol

    #定义函数判断材质内是否已经添加了输出运动模糊的节点
    def findmv(self,node):
        findresult = [0,0]
        if len(node.children()):
            for child in node.children():
                if child.type().name() == 'parameter':
                    parmname = child.parm('parmname').eval()
                    if parmname == 'mv_cam':
                        findresult[0] = 1
                    elif parmname == 'mv_vel':
                        findresult[1] = 1
                    else:
                        pass
        return findresult   

    #定义函数创建节点
    def create_mv_node(self,of_input,node,findvol = 0,findmv_cam = 0,findmv_vel = 0):
        inputnode = of_input[0]
        inputindx = of_input[1]
        node.allowEditingOfContents(1)
        pos = inputnode.position()
        if not findmv_cam:
            
            time1 = node.createNode('constant','time1')
            time0 = node.createNode('constant','time0')    
            time1.setPosition(pos)
            time0.setPosition(pos)
            time1.move([20,-10])
            time0.move([20,-12])
            time1.parm('floatdef').set(1)
            
            getblurp1 = time1.createOutputNode('getblurP')
            getblurp0 = time0.createOutputNode('getblurP')
            tondc1 = getblurp1.createOutputNode('tondc')
            tondc0 = getblurp0.createOutputNode('tondc')
            sub = tondc1.createOutputNode('subtract')
            sub.setNextInput(tondc0)
            
            mulconstant = sub.createOutputNode('mulconst')
            mulconstant.parm('mulconst').set(100)   
            
            mul = mulconstant.createOutputNode('multiply')
            mul.setNextInput(inputnode,inputindx)
            mul.move([0,1])
            
            para_mv_cam = mul.createOutputNode('parameter')    
            para_mv_cam.parm('parmname').set('mv_cam')
            para_mv_cam.parm('parmtype').set(7)
            para_mv_cam.parm('useasparmdefiner').set(1)
            para_mv_cam.parm('exportparm').set(1)
            para_mv_cam.parm('invisible').set(1)
            para_mv_cam.setFirstInput(mul)
            
        if not findmv_vel:
            bindv = node.createNode('bind')
            bindv.setPosition(pos)
            bindv.move([20,-5])
            if findvol:
                bindv.parm('parmname').set('vel')
            else:
                bindv.parm('parmname').set('v')
            bindv.parm('parmtype').set(7)
            
            mulconst = bindv.createOutputNode('mulconst')    
            mulconst.parm('mulconst').set(0.5)
            
            trans = mulconst.createOutputNode('transform')
            trans.parm('function').set('vtransform')
            trans.parm('tospace').set('space:object')
            
            mul_vel = trans.createOutputNode('multiply')
            mul_vel.setNextInput(inputnode,inputindx)
            mul_vel.move([0,1])
            
            mv_vel = mul_vel.createOutputNode('parameter')
            mv_vel.parm('parmname').set('mv_vel')
            mv_vel.parm('parmtype').set(7)
            mv_vel.parm('useasparmdefiner').set(1)
            mv_vel.parm('exportparm').set(1)
            mv_vel.parm('invisible').set(1)
            mv_vel.setFirstInput(mul_vel)

    # add material node to material
    def create_motionvector_node(self):
        nodes = hou.selectedNodes()
        if len(nodes):
            for node in nodes:        
                of_input = self.findOfInput(node)
                #判断材质的of端口是不是有连接，没有连接则提示
                if of_input[2]:
                    #判断材质中是否包含volume的材质
                    findvol = self.check_volume(node)
                    #判断运动模糊层的输出节点是否已经存在
                    findresult = self.findmv(node)
                    if findresult[0]:
                        print('%s中已经存在mv_cam的输出节点啦~~！！' % (node.path()))
                    if findresult[1]:
                        print('%s中已经存在mv_vel的输出节点啦~~！！' % (node.path()))
                        
                    result = findresult[0] + findresult[1]
                    
                    if result != 2:
                    
                        self.create_mv_node(of_input,node,findvol,findresult[0],findresult[1])
                    
                    print('')
                    print('运动模糊层添加成功')
                else:
                    print('没有找到Of的输入端，请先检查下材质吧')
        else:
            print('没有指定材质节点，所有材质的运动模糊层都帮你加上啦~~！！！')


class VolumeRenderFactory(object):
    def __init__(self):
        super().__init__()

    #遍历出所有的mantra节点
    def findMantra(self):
        mantra_lists = []
        mat = hou.node('/out')
        if len(mat.children()):
            for child in mat.children():
                if child.type().name() == 'ifd':
                    mantra_lists.append(child)
        return mantra_lists
        
    #定义函数判断渲染层是否已经添加
    def checkRenderPass(self,mantra):
        result = [1,1,1,1,1,1]
        num = mantra.parm('vm_numaux').eval()
        if num:
            for i in range(num):
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='my_id':
                    result[0] = 0
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='vol_Depth':
                    result[1] = 0
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='my_world_N':
                    result[2] = 0   
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='my_cam_N':
                    result[3] = 0                                
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='vol_vel':
                    result[4] = 0
                if mantra.parm('vm_variable_plane'+str(i+1)).eval()=='vol_N':
                    result[5] = 0                
        return result  
        
    #添加my_id渲染层
    def add_my_id(self,mantra):
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('my_id')

    #添加vol_Depth渲染层
    def add_vol_Depth(self,mantra):
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('vol_Depth')   

    #添加my_world_N渲染层
    def add_my_world_N(self,mantra):
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('my_world_N')  

    #添加my_cam_N渲染层
    def add_my_cam_N(self,mantra):
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('my_cam_N')    

    #添加vol_vel渲染层
    def add_vol_vel(self,mantra):
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('vol_vel')
        
    #添加vol_N渲染层
    def add_vol_N(self,mantra):
        num = mantra.parm('vm_numaux').eval()
        mantra.parm('vm_numaux').set(num+1)
        mantra.parm('vm_variable_plane'+str(num+1)).set('vol_N')

    #添加渲染层   
    def add_layer(self,lists):
        for node in lists:
            result = self.checkRenderPass(node)
            #添加my_id
            if result[0]:
                self.add_my_id(node)
                print('')
                print('%s的"my_id"分层添加成功啦~~！！' % node.name())
            else:
                print('')
                print('%s的"my_id"分层已经存在了~~！！' % node.name())
            #添加vol_Depth   
            if result[1]:
                self.add_vol_Depth(node)
                print('')
                print('%s的"vol_Depth"分层添加成功啦~~！！' % node.name())
            else:
                print('')
                print('%s的"vol_Depth"分层已经存在了~~！！' % node.name())   
            #添加my_world_N   
            if result[2]:
                self.add_my_world_N(node)
                print('')
                print('%s的"my_world_N"分层添加成功啦~~！！' % node.name())
            else:
                print('')
                print('%s的"my_world_N"分层已经存在了~~！！' % node.name())    
            #添加my_cam_N   
            if result[3]:
                self.add_my_cam_N(node)
                print('')
                print('%s的"my_cam_N"分层添加成功啦~~！！' % node.name())
            else:
                print('')
                print('%s的"my_cam_N"分层已经存在了~~！！' % node.name())                        
            #添加vol_vel   
            if result[4]:
                self.add_vol_vel(node)
                print('')
                print('%s的"vol_vel"分层添加成功啦~~！！' % node.name())
            else:
                print('')
                print('%s的"vol_vel"分层已经存在了~~！！' % node.name())  
            #添加vol_N   
            if result[5]:
                self.add_vol_N(node)
                print('')
                print('%s的"vol_N"分层添加成功啦~~！！' % node.name())
            else:
                print('')
                print('%s的"vol_N"分层已经存在了~~！！' % node.name())              
                            
    #为mantra节点添加渲染层
    def create_volume_layer(self):
        nodes = hou.selectedNodes()
        lists = []
        #晒选出选中节点的mantra节点
        for node in nodes:
            if node.type().name()=='ifd':
                lists.append(node) 
        print(lists)        
        #对选中的mantra节点添加层    
        if len(lists):
            self.add_layer(lists)                          
        else:
            lists = self.findMantra()       
            if len(lists):
                self.add_layer(lists)
                print('')
                print('没有指定mantra节点，自动把out模块下所有的mantra节点都指定了~~~！！！')
            else:
                print('')
                print('没选中mantra节点，out模块下也没发现mantra节点，检查一下吧~~~！！！')
    #定义函数找到of的输入端
    def findOfInput(self,node):
        
        node_and_index = [None,None,1]
        hasfind = 1
        node.allowEditingOfContents(1)
        if len(node.children()):
            for child in node.children():
                if child.type().name() =='output':
                    if child.parm('contexttype').eval() == 'surface':
                        inputs = child.inputConnectors()
                        #测试打印output节点的所有输入端
                        #print(inputs)
                        if len(inputs[1]):
                            temp = inputs[1][0]
                            inputnode = temp.inputNode()
                            inputindex = temp.outputIndex()
                            node_and_index[0] = inputnode
                            node_and_index[1] = inputindex
                            #测试打印连接到Of端口的节点和输出端口
    #                        print(inputnode)
    #                        print(inputindex)
                        else:
                            hasfind = 0
        else:
            hasfind = 0
        node_and_index[2] = hasfind               
        return node_and_index            
    #定义函数判断材质内是否有体积节点，返回一个布尔值。有则调用速度的时候用vel，没有则用v
    def checkVolume(self,node):
        
        findvol = 0
        if len(node.children()):
            for child in node.children():
                typename = child.type().name()
                if typename == 'volumemodel' or typename == 'volumeshadercore' or typename == 'pyroshadercore':
                    findvol = 1
        return findvol

    #定义函数判断材质内是否已经添加了输出体积分层的节点
    def findrenderpass(self,node):
        findresult = [0,0,0,0,0,0]
        if len(node.children()):
            for child in node.children():
                if child.type().name() == 'parameter':
                    parmname = child.parm('parmname').eval()
                    if parmname == 'my_id':
                        findresult[0] = 1
                    elif parmname == 'vol_Depth':
                        findresult[1] = 1
                    elif parmname == 'my_world_N':
                        findresult[2] = 1                    
                    elif parmname == 'my_cam_N':
                        findresult[3] = 1                                
                    elif parmname == 'vol_vel':
                        findresult[4] = 1                         
                    elif parmname == 'vol_N':
                        findresult[5] = 1                    
                    else:
                        pass 
                        
        return findresult                
    #定义函数创建节点
    def createVolPassNode(self,of_input,node,findresult):

        inputnode = of_input[0]
        inputindx = of_input[1]
        node.allowEditingOfContents(1)
        pos = inputnode.position()
        pos[0]+=20
        pos[1]-=10
        #创建my_id
        if not findresult[0]:
            para_vel = node.createNode('parameter')
            
            id_mul = para_vel.createOutputNode('multiply')
            id_mul.setPosition(pos)
            
            bind_vel = id_mul.createOutputNode('parameter')
            id_mul.setNextInput(inputnode,inputindx)
            
            para_vel.parm('parmname').set('my_id')
            para_vel.parm('parmtype').set(7)
            para_vel.parm('invisible').set(1)
            para_vel.setPosition(id_mul.position())
            para_vel.move([-3,0])
            
            
            bind_vel.setPosition(id_mul.position())
            bind_vel.move([4,0])
            bind_vel.parm('parmname').set('my_id')
            bind_vel.parm('parmtype').set(7)
            bind_vel.parm('useasparmdefiner').set(1)
            bind_vel.parm('exportparm').set(1)
            bind_vel.parm('invisible').set(1)
            bind_vel.setFirstInput(id_mul)     
        #创建vol_Depth   
        if not findresult[1]: 
            depth_global = node.createNode("global")
            depth_mul = node.createNode("multiply")
            depth_out = node.createNode("parameter")
        
            depth_mul.setPosition(pos)
            depth_mul.move([0,-3])
            depth_mul.setInput(0,depth_global,0)
            depth_mul.setNextInput(inputnode,inputindx)
            
            depth_global.setPosition(depth_mul.position())
            depth_global.move([-3,0])
            depth_global.parm("usemenu").set(1)
            depth_global.parm("varname").set('Pz')
            
            depth_out.setPosition(depth_mul.position())
            depth_out.move([4,0])
            depth_out.parm("parmname").set("vol_Depth")
            depth_out.parm("parmtype").set("vector")
            depth_out.parm("useasparmdefiner").set(1)
            depth_out.parm("exportparm").set(1)
            depth_out.parm("invisible").set(1)
            depth_out.setInput(0,depth_mul,0) 
            
        #创建my_world_N    
        if not findresult[2]: 
            cn_out = node.createNode("parameter")
            cn_mul = cn_out.createInputNode(0,"multiply")
            cn_ftv = cn_mul.createInputNode(0,"floattovec")
            cn_vtfx = cn_ftv.createInputNode(0,"vectofloat")
            cn_filterx = cn_vtfx.createInputNode(0,"filtershadow")
            cn_mulx = cn_filterx.createInputNode(1,"multiply")
            cn_transx = cn_mulx.createInputNode(0,"transform")
            cn_dirx = cn_transx.createInputNode(0,"constant","dirx")
            filter_distance = cn_mulx.createInputNode(1,"parameter","filer_distance")
                    
            cn_vtfy = cn_ftv.createInputNode(1,"vectofloat")
            cn_filtery = cn_vtfy.createInputNode(0,"filtershadow")
            cn_muly = cn_filtery.createInputNode(1,"multiply")
            cn_transy = cn_muly.createInputNode(0,"transform")
            cn_diry = cn_transy.createInputNode(0,"constant","dirx")
            
            cn_vtfz = cn_ftv.createInputNode(2,"vectofloat")
            cn_filterz = cn_vtfz.createInputNode(0,"filtershadow")
            cn_mulz = cn_filterz.createInputNode(1,"multiply")
            cn_transz = cn_mulz.createInputNode(0,"transform")
            cn_dirz = cn_transz.createInputNode(0,"constant","dirx")
            
            cn_mul.setPosition(pos)
            cn_mul.move([0,-14])
            cn_ftv.setPosition(cn_mul.position())
            cn_ftv.move([-3,0])
            cn_vtfx.setPosition(cn_ftv.position())
            cn_vtfx.move([-3,0])
            cn_filterx.setPosition(cn_vtfx.position())
            cn_filterx.move([-3,0])
            cn_mulx.setPosition(cn_filterx.position())
            cn_mulx.move([-3,0])
            cn_transx.setPosition(cn_mulx.position())
            cn_transx.move([-3,0])
            cn_transx.setPosition(cn_mulx.position())
            cn_transx.move([-3,0])
            cn_dirx.setPosition(cn_transx.position())
            cn_dirx.move([-3,0])
            
            cn_vtfy.setPosition(cn_ftv.position())
            cn_vtfy.move([-3,-3])
            cn_filtery.setPosition(cn_vtfy.position())
            cn_filtery.move([-3,0])
            cn_muly.setPosition(cn_filtery.position())
            cn_muly.move([-3,0])
            cn_transy.setPosition(cn_muly.position())
            cn_transy.move([-3,0])
            cn_diry.setPosition(cn_transy.position())
            cn_diry.move([-3,0])
            
            cn_vtfz.setPosition(cn_ftv.position())
            cn_vtfz.move([-3,-6])
            cn_filterz.setPosition(cn_vtfz.position())
            cn_filterz.move([-3,0])
            cn_mulz.setPosition(cn_filterz.position())
            cn_mulz.move([-3,0])
            cn_transz.setPosition(cn_mulz.position())
            cn_transz.move([-3,0])
            cn_dirz.setPosition(cn_transz.position())
            cn_dirz.move([-3,0])
            
            cn_mulx.setInput(1,filter_distance,0) 
            cn_muly.setInput(1,filter_distance,0)
            cn_mulz.setInput(1,filter_distance,0)
            cn_dirx.parm("consttype").set("vector")
            cn_dirx.parm("vectordef1").set(1)
            cn_diry.parm("consttype").set("vector")
            cn_diry.parm("vectordef2").set(1)
            cn_dirz.parm("consttype").set("vector")
            cn_dirz.parm("vectordef3").set(1)
            cn_transx.parm("function").set("vtransform")
            cn_transx.parm("fromspace").set("space:camera")
            cn_transx.parm("tospace").set("space:world")
            cn_transy.parm("function").set("vtransform")
            cn_transy.parm("fromspace").set("space:camera")
            cn_transy.parm("tospace").set("space:world")
            cn_transz.parm("function").set("vtransform")
            cn_transz.parm("fromspace").set("space:camera")
            cn_transz.parm("tospace").set("space:world")
            
            cn_out.setPosition(cn_mul.position())
            cn_out.move([4,0])
            cn_out.parm("parmname").set("my_world_N")
            cn_out.parm("parmtype").set("vector")
            cn_out.parm("useasparmdefiner").set(1)
            cn_out.parm("exportparm").set(1)
            cn_out.parm("invisible").set(1)
            cn_mul.setNextInput(inputnode,inputindx)
            cn_out.setInput(0,cn_mul,0)     
            
            filter_distance.setPosition(cn_mulx.position())
            filter_distance.move([-12,-3])
            filter_distance.parm("parmname").set("filter_distance")
            filter_distance.parm("floatdef").set(1)
        #创建my_cam_N    
        if not findresult[3]: 
            wn_out = node.createNode("parameter")
            wn_mul = wn_out.createInputNode(0,"multiply")
            wn_ftv = wn_mul.createInputNode(0,"floattovec")
            wn_vtfx = wn_ftv.createInputNode(0,"vectofloat")
            wn_filterx = wn_vtfx.createInputNode(0,"filtershadow")
            wn_mulx = wn_filterx.createInputNode(1,"multiply")
            wn_dirx = wn_mulx.createInputNode(0,"constant","dirx")
            filter_distance = wn_mulx.createInputNode(1,"parameter","filer_distance")
            
            wn_vtfy = wn_ftv.createInputNode(1,"vectofloat")
            wn_filtery = wn_vtfy.createInputNode(0,"filtershadow")
            wn_muly = wn_filtery.createInputNode(1,"multiply")
            wn_diry = wn_muly.createInputNode(0,"constant","diry")
            
            wn_vtfz = wn_ftv.createInputNode(2,"vectofloat")
            wn_filterz = wn_vtfz.createInputNode(0,"filtershadow")
            wn_mulz = wn_filterz.createInputNode(1,"multiply")
            wn_dirz = wn_mulz.createInputNode(0,"constant","dirz")
            
            wn_mul.setPosition(pos)
            wn_mul.move([0,-6])
            wn_ftv.setPosition(wn_mul.position())
            wn_ftv.move([-3,0])
            wn_vtfx.setPosition(wn_ftv.position())
            wn_vtfx.move([-3,0])
            wn_filterx.setPosition(wn_vtfx.position())
            wn_filterx.move([-3,0])
            wn_mulx.setPosition(wn_filterx.position())
            wn_mulx.move([-3,0])
            wn_dirx.setPosition(wn_mulx.position())
            wn_dirx.move([-3,0])
            filter_distance.setPosition(wn_dirx.position())
            filter_distance.move([-10,-3])
            
            wn_vtfy.setPosition(wn_ftv.position())
            wn_vtfy.move([-3,-3])
            wn_filtery.setPosition(wn_vtfy.position())
            wn_filtery.move([-3,0])
            wn_muly.setPosition(wn_filtery.position())
            wn_muly.move([-3,0])
            wn_diry.setPosition(wn_muly.position())
            wn_diry.move([-3,0])
            
            wn_vtfz.setPosition(wn_ftv.position())
            wn_vtfz.move([-3,-6])
            wn_filterz.setPosition(wn_vtfz.position())
            wn_filterz.move([-3,0])
            wn_mulz.setPosition(wn_filterz.position())
            wn_mulz.move([-3,0])
            wn_dirz.setPosition(wn_mulz.position())
            wn_dirz.move([-3,0])
            
            wn_dirx.parm("consttype").set("vector")
            wn_dirx.parm("vectordef1").set(1)
            wn_diry.parm("consttype").set("vector")
            wn_diry.parm("vectordef2").set(1)
            wn_dirz.parm("consttype").set("vector")
            wn_dirz.parm("vectordef3").set(1)
            filter_distance.parm("parmname").set("filter_distance1")
            filter_distance.parm("floatdef").set(1)
            
            wn_muly.setInput(1,filter_distance,0)
            wn_mulz.setInput(1,filter_distance,0)
            wn_out.setPosition(wn_mul.position())
            wn_out.move([4,0])
            wn_out.parm("parmname").set("my_cam_N")
            wn_out.parm("parmtype").set("vector")
            wn_out.parm("useasparmdefiner").set(1)
            wn_out.parm("exportparm").set(1)
            wn_out.parm("invisible").set(1)
            wn_mul.setNextInput(inputnode,inputindx)
            wn_out.setInput(0,wn_mul,0) 
            
        #创建vol_vel    
        if not findresult[4]: 
            vel_in = node.createNode("parameter")
            vel_mul = node.createNode("multiply")
            vel_out = node.createNode("parameter")
            
            vel_mul.setPosition(pos)
            vel_mul.move([0,2])
            vel_mul.setInput(0,vel_in,0)
            vel_mul.setNextInput(inputnode,inputindx)
            
            vel_in.setPosition(vel_mul.position())
            vel_in.move([-3,0])
            vel_in.parm("parmname").set("vel")
            vel_in.parm("parmtype").set("vector")
            vel_in.parm("invisible").set(1)
            
            vel_out.setPosition(vel_mul.position())
            vel_out.move([4,0])
            vel_out.parm("parmname").set("vol_vel")
            vel_out.parm("parmtype").set("vector")
            vel_out.parm("useasparmdefiner").set(1)
            vel_out.parm("exportparm").set(1)
            vel_out.parm("invisible").set(1)
            vel_out.setInput(0,vel_mul,0)
            
        #创建vol_N   
        if not findresult[5]: 
            myN_mul = node.createNode('multiply')
            myN_out = node.createNode("parameter")
            
            myN_mul.setPosition(pos)
            myN_mul.move([0,5])
            
            trans = myN_mul.createInputNode(0,'transform')
            normalize = trans.createInputNode(0,'normalize')
            inline = normalize.createInputNode(0,'inline')
            density = inline.createInputNode(0,'parameter','density')
            
            trans.parm('function').set('ntransform')
            trans.parm('tospace').set('space:object')
            
            inline.parm('code').set('$nor = gradient($density)*-1;')
            inline.parm('outtype1').set('vector')
            inline.parm('outname1').set('nor')
            inline.parm('outlabel1').set('$nor')
            
            density.parm('parmname').set('density')
            density.parm('floatdef').set(1)
            density.parm('invisible').set(1)
            
            myN_out.setPosition(myN_mul.position())
            myN_out.move([4,0])
            myN_out.parm("parmname").set("vol_N")
            myN_out.parm("parmtype").set("vector")
            myN_out.parm("useasparmdefiner").set(1)
            myN_out.parm("exportparm").set(1)
            myN_out.parm("invisible").set(1)
            myN_out.setInput(0,myN_mul,0)
            myN_mul.setNextInput(inputnode,inputindx)
    #定义主函数
    def create_node_to_material(self):
        nodes = hou.selectedNodes()
        if len(nodes):
            for node in nodes:        
                of_input = self.findOfInput(node)
    #            print(of_input)
                #判断材质的of端口是不是有连接，没有连接则提示
                if of_input[2]:
                    #判断材质中是否包含volume的材质
                    #findvol = checkVolume(node)
                    #判断运动体积分层的输出节点是否已经存在
                    findresult = self.findrenderpass(node)
                    #print(findresult)
                    if findresult[0]:
                        print('%s中已经存在my_id的输出节点啦~~！！' % (node.path()))
                    if findresult[1]:
                        print('%s中已经存在vol_Depth的输出节点啦~~！！' % (node.path()))
                    if findresult[1]:
                        print('%s中已经存在my_world_N的输出节点啦~~！！' % (node.path()))  
                    if findresult[1]:
                        print('%s中已经存在my_cam_N的输出节点啦~~！！' % (node.path()))                    
                    if findresult[1]:
                        print('%s中已经存在vol_vel的输出节点啦~~！！' % (node.path()))                    
                    if findresult[1]:
                        print('%s中已经存在my_N的输出节点啦~~！！' % (node.path()))                    
                            
                    result = findresult[0] + findresult[1] + findresult[2] + findresult[3] + findresult[4] + findresult[5]
                    
                    if result != 6:
                        pass
                        self.createVolPassNode(of_input,node,findresult)
                    
                    print('')
                    #print('体积分层添加成功')
                else:
                    print('没有找到Of的输入端，请先检查下材质吧')
        else:
            print('没有指定材质节点，所有材质的体积分层都帮你加上啦~~！！！')


class IdPassFactory(object):
    def __init__(self):
        super().__init__()

    #列出选中的节点的相关材质
    def findNodePath(self,node):
        mat_lists = []
        find_geo = False
        find_innerMat = True
        find_outMat = True
        mat = None
        if node.type().name() == 'geo':
            find_geo = True
            #找到geo的渲染节点，并检测是否存在材质，有材质则返回材质路径，没有材质则回到geo节点检测材质路径
            if len(node.children()):
                for child in node.children():
                    if child.isRenderFlagSet():
                        renderNode = child
                        break
                    elif child.isDisplayFlagSet():
                        renderNode = child
                mat = renderNode.geometry().findPrimAttrib('shop_materialpath')
            if mat == None:
                find_innerMat = False
                #print('没有在geo内部指定材质')
            else:
                mat_lists = mat.strings()
            #内部没找到材质，回到geo层级检测
            if not find_innerMat:
                mat = node.parm('shop_materialpath').eval()
                if mat == '':
                    find_outMat = False
                    #print('没有在geo层级指定材质')
                else:
                    mat_lists.append(mat)
                    
        return mat_lists 
        
    #测试findNodePath函数
    #nodes = hou.selectedNodes()
    #a = findNodePath(nodes)
    #print(a)
    #向材质中添加输出id的节点
    def addNodeToMat(self,mat_lists,color_value = (0,0,0)):

        export_existing = False
        collectPos = [0,0]
        for each_mat in mat_lists:
            mat_node = hou.node(each_mat)
            mat_node.allowEditingOfContents()
            #print(each_mat)
            #a.判断是够已经存在输出属性的节点 b.记录材质输出端的位置
            for each_node in mat_node.children():
                typename = each_node.type().name()
                if typename == 'parameter' or typename == 'bind':
                    if each_node.parm('parmname').eval() == 'my_id':
                        export_existing = True
                        print('材质内已经存在属性的输出节点啦~~！')
                        
                if typename == 'collect':
                    collectPos = each_node.position()
                    
            #判断之前不存在输出这个属性的节点，创建新的输出节点     
            if not export_existing:
    #            bind = mat_node.createNode('bind','bind')
                cons = mat_node.createNode('constant','Color')
                para = mat_node.createNode('parameter','MY_ID')
                
    #            bind.parm('parmname').set('my_id')
    #            bind.parm('parmtype').set(7)
    #            bind.parm('vectordef1').set(color_value[0])
    #            bind.parm('vectordef2').set(color_value[1])
    #            bind.parm('vectordef3').set(color_value[2])
                cons.parm('consttype').set(7)
                cons.parm('vectordef1').set(color_value[0])
                cons.parm('vectordef2').set(color_value[1])
                cons.parm('vectordef3').set(color_value[2])
                para.parm('parmname').set('my_id')
                para.parm('parmlabel').set('My_Id')
                para.parm('parmtype').set(7)
                para.parm('useasparmdefiner').set(1)
                para.parm('exportparm').set(1)
                para.parm('invisible').set(1)
                
                para.setColor(hou.Color(color_value))
    #            bind.setColor(hou.Color([1,0,0]))
                cons.setColor(hou.Color(color_value))
                
                cons.setPosition(collectPos)
                para.setPosition(collectPos)
                
                cons.move([5,0])
                para.move([10,0])
                para.setFirstInput(cons)
                print('材质内属性输出节点添加成功~~！！')
        return export_existing
    
    #遍历所有的mantra节点
    def findMantra(self):
        out = hou.node('/out')
        mantraLists = []
        for node in out.children():
            if node.type().name() == 'ifd':
                mantraLists.append(node)
        return mantraLists

    #判断mantra上是否已经添加了该分层，已经存在则提示用户，没有则添加
    def addrenderpass(self,list):
        for ifd in list:
            origin_num = ifd.parm('vm_numaux').eval()
            existing = False
            if origin_num:
                for i in range(origin_num):
                    if ifd.parm('vm_variable_plane'+str(i+1)).eval() == 'my_id':
                        print('my_id的分层已经在%s上存在啦，兄弟~~~！！！！' % ifd.path())
                        existing = True
                        
            if not existing:
                num = origin_num+1
                ifd.parm('vm_numaux').set(num)
                ifd.parm('vm_variable_plane'+str(num)).set('my_id')
                print('%s的my_id分层添加成功啦~~!!' % ifd.path())

    # create id node            
    def create_id_pass(self):
        nodes = hou.selectedNodes()
        length = len(nodes)
        color_valuelist = ((1,0,0),(0,1,0),(0,0,1))
        color_list = ('R','G','B')
        #选中了节点会执行....
        if length:
            for node in nodes:
                mat_lists = self.findNodePath(node)
                ##遍历到材质以后会执行...
                if len(mat_lists):
                    index = hou.ui.selectFromList(color_list,default_choices = ([0]),exclusive = True)[0]
                    color_value = color_valuelist[index]
                    matresult = self.addNodeToMat(mat_lists,color_value)
    #                if not matresult:
    #                    print('材质内属性输出节点添加成功~~！！')
    #                
    #                else:
    #                    print('材质内已经存在属性的输出节点啦~~！')
                    mantraLists = self.findMantra()
                    self.addrenderpass(mantraLists)
                ##没上材质时会执行...
                else:
                    print('选中的节点压根没加材质呀，兄弟~~!!!')
        #什么都没选会执行....        
        else:
            print('先选中你要添加渲染层的节点呀，兄弟~~！！！')


class QuikShader():
    def __init__(self):
        super().__init__()

    #定义函数，根据指定的类型名称返回属于该名称的所有材质预设
    def getGalleries(self,node_typename = 'materialbuilder',keyword_pattern = 'Mantra'):   
        galLists = []
        
        node_type = hou.nodeType(hou.vopNodeTypeCategory(),node_typename)
        galLists = list(hou.galleries.galleryEntries(keyword_pattern = keyword_pattern,node_type = node_type))
        return galLists
        
    #测试
    #lists = getGalleries()
    #for each in lists:
    #    print(each)
    #定义选择材质的界面并返回选择的材质类型的名字
    def showMatUi(self,):
        type_choices = ('materialbuilder','principledshader','pyroshader')
        type_index = hou.ui.selectFromList(choices = type_choices,default_choices = ([0]),exclusive = True)[0]
        node_typename = type_choices[type_index]
        return node_typename

    #定义选择预设的界面并返回选择的预设类型的名字
    def showGalUi(self,matlists):

        gal_choices = []
        for each in matlists:
            gal_choices.append(each.name())
        
        gal_index = hou.ui.selectFromList(choices=gal_choices,default_choices = ([0]),exclusive = True)[0]    
        mat_gal = matlists[gal_index] 
        return mat_gal

    #获取当前鼠标的位置和当前面板的父集
    def getMousePos(self):
        
        mouseInfo = []
        plane = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
        pos = plane.selectPosition()
        parent = plane.pwd()
        
        mouseInfo.append(pos)
        mouseInfo.append(parent)
        return mouseInfo

    #创建材质节点    
    def createNode(self,node,node_typename,mat_gal,isgeo = 0):

        mat = hou.node('/mat') 
        if isgeo:                    
            material_mat = mat.createNode(node_type_name = node_typename,node_name = mat_gal.name())
            mat_gal.applyToNode(material_mat)
            path = material_mat.path()
            node.parm('shop_materialpath').set(path)
        if not isgeo:
            mouseInfo = self.getMousePos()        
            material_sop = mouseInfo[1].createNode('material')        
            material_mat = mat.createNode(node_type_name = node_typename,node_name = mat_gal.name())
            mat_gal.applyToNode(material_mat)
            path = material_mat.path()
            material_sop.setFirstInput(node)
            material_sop.setPosition(mouseInfo[0])
            material_sop.parm('shop_materialpath1').set(path)
            material_sop.setDisplayFlag(1)
            material_sop.setRenderFlag(1)
        mat.layoutChildren()       
    #定义主函数
    def create_shader(self):

        nodes = hou.selectedNodes()   
        #为了不混淆操作，只给一个节点去添加材质
        if len(nodes):
        
            node = nodes[0]
            node_typename = self.showMatUi()      
            matlists = self.getGalleries(node_typename = node_typename)    
            mat_gal = self.showGalUi(matlists)
                    
            if node.type().name() == 'geo':
                self.createNode(node = node,node_typename = node_typename,mat_gal = mat_gal,isgeo = 1)
            else:
                self.createNode(node = node,node_typename = node_typename,mat_gal = mat_gal,isgeo = 0)
        else:
            print('至少选择一个sop节点或者geo节点~~！！')                    
