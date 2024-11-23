import hou

class Chain(object):
    def __init__(self, node):
        self.node = node
        self.inputs = []
        
    def rop_name(self) -> str:
        return self.node.name() + '__CHAIN'
        
    def isFC(self) -> bool:
        return self.node.type().name()=='filecache::2.0'
    
    def isMerge(self) -> bool:
        return self.node.type().name() == "merge"
    
    def collect_node(self,node) -> list:
        pass


    
    def find_up(self,node):
        pass

    def find_down(self,node):
        pass

        
def directUpstreamFC(node):
    FCs = []
    for i in node.inputs():
        if i.type().name() == 'filecache':
            FCs.append(i)
        else:
            FCs.extend(directUpstreamFC(i))
    return FCs
    
def toChain(node):
    chain = Chain(node)
    chain.inputs = [toChain(i) for i in directUpstreamFC(node)]
    print(chain.inputs)
    return chain
    
def toRop(chain, rop_parent):
    r = rop_parent.node(chain.ropName())
    if not r:
        # take the case that first selected node is not filecache into consideration
        r = rop_parent.createNode('fetch' if chain.isFC() else 'merge')
        r.setName(chain.ropName())
    else:
        for i in range(len(r.inputs())):
            r.setInput(i, None)
    r.setColor(chain.node.color())
    if chain.isFC():
        r.parm('source').set(chain.node.path() + '/render')
    
    for i, input_rop in enumerate([toRop(i, rop_parent) for i in chain.inputs]):
        r.setInput(i, input_rop)
    r.moveToGoodPosition()
    return r
 
#定义主函数
def main():
    sel = hou.selectedNodes()
    if not sel:
        pass
    else:
        for node in sel:
            toRop(toChain(node), hou.node('/out'))
            
#运行主函数
#main()