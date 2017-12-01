import maya.cmds as mc

GRP = 'cloth_grp'
def _get_next_free(node, attr):
    """ Used to get the next available connect plug from a networked array plug
    """
    for i in range(0, 10000000):
        cons = mc.listConnections('%s.%s[%d]' % (node, attr, i))
        if cons == None:
            return i
    return None
    
def connect_to_nucleus( nbase, nucleus):
    """ Connect the provided nBase node to the provided nucleus. 
    """
    
    is_passive = mc.nodeType(nbase) in ['nRigid']
    
    if is_passive:
        elem = _get_next_free(nucleus, 'inputPassive')
        mc.connectAttr('%s.currentState' % nbase, 
            '%s.inputPassive[%d]' % (nucleus, elem))
        mc.connectAttr('%s.startState' % nbase, 
            '%s.inputPassiveStart[%d]'  % (nucleus, elem))
    else:
        elem = _get_next_free(nucleus, 'inputActive')
        mc.connectAttr('%s.currentState' % nbase, 
                '%s.inputActive[%d]' % (nucleus, elem))
        mc.connectAttr('%s.startState' % nbase, 
                '%s.inputActiveStart[%d]' % (nucleus, elem))
  
        elem = _get_next_free(nucleus, 'outputObjects')
        mc.connectAttr('%s.outputObjects[%d]' % (nucleus, elem), \
                                            '%s.nextState' % nbase)
    mc.connectAttr('%s.startFrame' % nucleus, 
                '%s.startFrame' % nbase, f=True)
    mc.connectAttr('time1.outTime', '%s.currentTime' % nbase, f=True)

def make_cloth(mesh, is_rigid, inp):

    name = mesh.split(':')[-1].replace('_geo','')
    name += 'Rigid_mesh' if is_rigid else 'Sim_mesh'  
        
    if mc.objExists(GRP+'|'+name):
        return
    #xform = mc.createNode('transform', n=name, p=GRP)
    #shape = mc.createNode('mesh', n=name+'Shape', p=xform)
    dup = mc.duplicate(mesh)
    dup = mc.parent(dup, GRP)
    xform = mc.rename(dup, name)
    shape = mc.listRelatives(xform, c=1, pa=1)[0]
    mc.sets(xform, fe='initialShadingGroup')
    mc.parentConstraint(mesh, xform, mo=False)
    #mc.setAttr(shape+'.io', True)
    
    dtype = 'nRigid' if is_rigid else 'nCloth'
    cloth_name = mesh.split(':')[-1].replace('_geo','') + '_' + dtype
    cloth = mc.createNode(dtype, n=cloth_name+'Shape', p=xform)
    

    if inp:
        mc.connectAttr(inp[0], shape+'.inMesh')
    else:
        mc.connectAttr(mesh+'.outMesh', shape+'.inMesh')
        mc.dgeval(shape+'.outMesh')
        mc.disconnectAttr(mesh+'.outMesh', shape+'.inMesh')
    if not is_rigid:
        mc.setAttr(cloth+'.localSpaceOutput', 1)
        mc.connectAttr(cloth+'.outputMesh', mesh+'.inMesh', f=True)

    mc.connectAttr(shape+'.worldMesh[0]', cloth+'.inputMesh')
    connect_to_nucleus( cloth, GRP+'|nucleus')
    return cloth
    
def apply_cloth(sel = None):
    sel = sel or mc.ls(sl=1)
    if not mc.objExists(GRP):
        mc.group(em=True, n=GRP)
        nucleus = mc.createNode('nucleus', n = 'nucleus', p=GRP)
        mc.connectAttr('time1.outTime', nucleus+'.currentTime')
        
    for mesh in sel:
        inp = mc.listConnections(mesh+'.inMesh', sh=True, p=True)
        make_cloth(mesh, False, inp)
        rigid = make_cloth(mesh, True, inp)
        mc.setAttr(rigid+'.collide', False)
        #mc.hide(xform)
apply_cloth()
