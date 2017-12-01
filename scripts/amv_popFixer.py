import maya.cmds as mc, maya.mel as mm

def pop_fixer(face_selection = None, smooth_iterations = 20):
    face_selection = face_selection or mc.filterExpand(sm=34)
    mesh = face_selection[0].split('.')[0]
    face0 = face_selection[0].split('[')[-1][:-1]

    inMesh = mc.listConnections(mesh+'.inMesh', sh=True, s=1,d=0,p=1)[0]

    # 1. create group
    if not mc.objExists('pop_fixer_grp'):
        mc.group(em=True, n='pop_fixer_grp')
    frame = mc.currentTime(q=True)
    xform = mc.createNode('transform', n='%s_fr%04d_f%s_flat_mesh' % (mesh, frame, face0), p='pop_fixer_grp')
    shape_name = xform.split('|')[-1]+'Shape'
    shape = mc.createNode('mesh', n=shape_name, p = xform)

    mc.connectAttr(inMesh, shape+'.inMesh')
    mc.select(xform+'.f[*]')
    mc.select([f.replace(mesh,xform) for f in face_selection], d=True)
    
    mc.delete()
    mc.refresh()
    pose = mc.duplicate(xform)[0]
    nv= mc.polyEvaluate(pose, v=1)

    pose = mc.rename(pose, xform.replace('_flat_','_pose_'))
    mc.select(xform)
    ss = mm.eval("dnSkinSmoother_create")
    mc.setAttr(ss+'.iterations',smooth_iterations)
    mc.select(pose+'.vtx[*]')
    mm.eval('ShrinkPolygonSelectionRegion')
    mc.refresh()

    w_map = [0]*nv
    for sel in mc.filterExpand(sm=31):
        name = sel.split('[')[-1]
        vt = int(name[:-1])
        w_map[vt] = 1.0

    mc.setAttr(ss+'.weightList[0].weights', size = nv)
    mc.setAttr(ss+'.weightList[0].weights[0:%d]' % (nv-1), *w_map)

    mc.select(pose, xform)
    mm.eval('CreateWrap')
    mc.select(mesh, pose)
    mc.hide(xform)
    p2p = mm.eval('dnPoint2Point')
    mc.refresh()
    mc.parent(xform, pose)
    mc.parent(xform+'Base', pose)
    mc.addAttr(pose, ln='iterations', at='long', min=0, smx=30, dv = smooth_iterations,k=1)
    mc.addAttr(pose, ln='envelope', at='float', min=0, max=1.0, dv = 1.0,k=1)
    mc.connectAttr(pose+'.iterations', ss+'.iterations')
    mc.connectAttr(pose+'.envelope', p2p+'.envelope')
    for at in ['tx','ty','tz','rx','ry','rz','sx','sy','sz']:
        mc.setAttr(pose+'.'+at, lock=True)
    mc.select(pose)
pop_fixer(face_selection = None, smooth_iterations = 40)
