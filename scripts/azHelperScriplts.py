
def toggleVis():
	sel = mc.ls(sl=True)
	for s in sel:
	    visAttr = s + '.v'
	    if mc.getAttr(visAttr):
	        mc.setAttr(visAttr, 0)
	    else:
	        mc.setAttr(visAttr, 1)




def miltiCurveCvSelect
	sel = mc.ls(sl=True)

	cvList = []
	num = 10

	for c in sel:
	    spanCount = mc.getAttr(c + '.spans')
	    cvList.append(c+'.cv[:{0}]'.format(num))
	    
	mc.select(cvList)


import maya.cmds as mc

def insertSculptGeo():
    # get selection, it's shape in inMesh plug
    sel = mc.ls(sl=True)
    outGeo = sel[0]
    outGeoShape = mc.listRelatives(outGeo, s=True)[0]
    inputGeoPlug = mc.connectionInfo(outGeoShape+'.inMesh', sourceFromDestination=True)
    # duplicate and name _sculpt
    sculptGeo = mc.duplicate(outGeo, n=outGeo+'_sculpt')[0]
    sculptGeoShape = mc.listRelatives(sculptGeo, s=True)[0]
    # make connections
    mc.connectAttr(inputGeoPlug, sculptGeoShape+'.inMesh')
    mc.connectAttr(sculptGeoShape+'.outMesh', outGeoShape+'.inMesh', f=True)
    print '### Duplicated {0} as {1} and connected it back into {0} inMesh'.format(outGeo, sculptGeo)
    


import pymel.core as pc

def setStartFrameAndStates():
	'''
	Script that sets the initial states on nCloth objects in scene and sets nucleus start frame 
	to the current frame. Also adjusts playbackOptions.
	'''
    curTime = mc.currentTime(q=True)
    nuclei = mc.ls(type='nucleus')
    clothes = mc.ls(type='nCloth')
    for c in clothes:
        mc.nBase(c, e=True, stuffStart=True)
        print '## Set initial state on {0} to current frame'.format(c)
    for n in nuclei:
        mc.setAttr(n+'.startFrame', curTime)
        print '## Set startFrame on {0} to {1}'.format(n, curTime)
    mc.playbackOptions(e=True, minTime=curTime)
    mc.currentTime(curTime, u=True)

    
def clearStartFrameAndStates():
	'''
	Script that clears any initial states on nCloth objects in scene and sets nucleus start frame
	based on frames set in the preferences ctrl. Resets playbackOptions as well.
	'''
    prefCtrl = mc.ls('*:rig_preferences')[0]
    startFrame = mc.getAttr(prefCtrl+'.shotStart') - mc.getAttr(prefCtrl+'.cachePreRoll')
    nuclei = mc.ls(type='nucleus')
    clothes = mc.ls(type='nCloth')
    for c in clothes:
        mc.nBase(c, e=True, clearStart=True)
        print '## Set initial state on {0} to current frame'.format(c)
    for n in nuclei:
        mc.setAttr(n+'.startFrame', startFrame)
        print '## Set startFrame on {0} to {1}'.format(n, startFrame)
    mc.playbackOptions(e=True, minTime=startFrame)
    mc.currentTime(startFrame, u=True)    
    


import maya.cmds as mc
########    INSERT AN INTERMEDIATE SCULPT GEO AND CONNECT INTO NETWORK      ##################
def insertSculptGeo():
    # get selection, it's shape in inMesh plug
    sel = mc.ls(sl=True)
    if not sel:
        print 'nothing is selected dumb ass'
        return
    outGeo = sel[0]
    outGeoShape = mc.listRelatives(outGeo, s=True)[0]
    inputGeoPlug = mc.connectionInfo(outGeoShape+'.inMesh', sourceFromDestination=True)
    geoParent = cmds.listRelatives(outGeo, p=True)[0]
    in_deform = cmds.listConnections(outGeo + ".inMesh")[0]

    # Duplicate the geo to create the sculpt meshes
    sculpt_shape = cmds.createNode("mesh")
    sculpt_mesh = cmds.listRelatives(sculpt_shape, parent=True)[0]
    sculpt_mesh = cmds.rename(sculpt_mesh, outGeo.replace("_geo", "_sculpt"))
    sculpt_mesh = cmds.parent(sculpt_mesh, geoParent)[0]

    oldPosition = cmds.xform(outGeo, q=True, matrix=True)
    cmds.xform(sculpt_mesh, matrix=oldPosition)
    # make connections
    mc.connectAttr(inputGeoPlug, sculpt_mesh+'.inMesh')
    mc.connectAttr(sculpt_mesh+'.outMesh', outGeoShape+'.inMesh', f=True)
    print '### Duplicated {0} as {1} and connected it back into {0} inMesh'.format(outGeo, sculpt_mesh)
    


##########################################################

# CFX HELPER GUI

##########################################################

import sys

sys.path.append('/u/jdm/tools/MPH/maya/python/')

import MPH_cfx_GUI

from MPH_cfx_GUI import *

reload(MPH_cfx_GUI)

jdm_cfxGUI()


#######################################################3
#import maya.cmds as mc
#tendril = 'pCylinder1'

def createCurveDownCenterOfUvShell(tendril):

    vert_map = {}
    for vid in range(mc.polyEvaluate(tendril, v=True)): 
        vtx = '%s.vtx[%d]' % (tendril, vid)
        pt = mc.xform(vtx, q=True, ws=True, t=True)
        uvname = mc.polyListComponentConversion(vtx, tuv=1)        
        v_coord = mc.polyEditUV(uvname, q=True)[1]
        v_coord_str = str(v_coord)[:5]
        if v_coord_str not in vert_map:
            vert_map[v_coord_str] = []
        vert_map[v_coord_str].append(pt)
    pts = []

    for v_val in sorted(vert_map.iterkeys()): 
        verts = vert_map[v_val]
        if len(verts) < 6:
            continue
        totx = 0; toty=0; totz=0
        for vx, vy, vz in verts:
            totx += vx
            toty += vy
            totz += vz

        lv = 1.0 / len(verts)
        pts.append((totx * lv, toty * lv, totz * lv))
    cur = mc.curve(d=3, p=pts, n=tendril+'_crv')

    mc.rebuildCurve(cur, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, s=22, d=3, tol=0.01)
    mc.rename(mc.listRelatives(cur, c=True, pa=True)[0], cur+'Shape')
    return cur

#createCurveDownCenterOfUvShell(tendril)

#######################################################

#########    MAKE LOCATOR AT POINT        ####################
# import sys
# sys.path.insert(0, "tools/MPH/maya/rig/python/")
# import MPHRig as rig
import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm

try:
	cmds.loadPlugin("dnRigTools") # load plugin
except:
	print ("Unable to load dnRigTools Plugin\n")

##

def createLocOnMesh( sLoc=None, sMesh=None ):
    #rig.createFollicle(name='follicle', surface='', obj='', driver='follicle', connectType='', UV=[], parent='')
    # get one item selected
    sel = getSel(iMaxSel=1)
    if sel and 'vtx' in sel[0]:
        vtx = sel[0]
        sMesh = mc.ls(vtx, o=True)[0]
    else:
        mc.error('!!! Select only one vertex.')

    if not sLoc:
        sLoc = mc.spaceLocator( name= 'loc_vtx_01' )[0]
    # snap locator to vtx position
    vPos = mc.xform(vtx, q=True, t=True, ws=True)
    mc.setAttr(sLoc+'.tx', vPos[0])
    mc.setAttr(sLoc+'.ty', vPos[1])
    mc.setAttr(sLoc+'.tz', vPos[2])
    mc.select(sMesh, r=True)
    mc.select(sLoc, add=True)
    mm.eval('dnMeshConstraint;')
    mc.select(sLoc, r=True)
    return sLoc
    
def createSculptDeformer( sParentTo=None ):
    mc.select(cl=True)
    sSculptNodes = mc.sculpt(groupWithLocator=True)
    sSculpt = sSculptNodes[1]
    sSculptGrp = mc.listRelatives(sSculpt, parent=True)[0]
    mc.xform(sSculptGrp, cp=True)
    mc.select(sSculptGrp, r=True)
    return sSculptGrp
    
def createSculptAtPoint():
    '''
    To use: select vert and run command. Then move and scale the sculpt nodes as needed, and assign members
    using Edit Deformer Membership Tool.
    '''
    sLoc = createLocOnMesh()
    sSculptGrp = createSculptDeformer()
    mc.delete(mc.parentConstraint(sLoc, sSculptGrp,  mo=False))
    mc.parent(sSculptGrp, sLoc)

def getSel( iMaxSel=1, bMultiSel=False ):
    sel = mc.ls(sl=True)
    if not bMultiSel:
        if len(sel) == iMaxSel:
            return sel
        else:
            mc.warning('\t !!! Wrong selection. Please select %i number of elements and re-run the tool. !!! ( %i objects were selected.)' %(iMaxSel, len(sel)))
    else:
        return sel
    
##################

#########    MAKELIST        ####################
def makeList():
    sel = mc.ls(sl=True)
    sList = '['
    for s in sel:
        sList = sList +'"'+ s + '", '
    sList = sList + ']'
    print 'list = ', sList
    
    

#########    CREATE CLOSEST POINT ON MESH LOCATORS     ####################
def createCPOM( sMesh ):

     sCloseLoc= mc.spaceLocator( name= 'loc_ToFindClosestPointFor' )[0]
     sLocOnMesh= mc.spaceLocator( name= 'loc_closestPointOnMesh' )[0]

     sCPOM= mc.createNode( 'closestPointOnMesh', name = 'geo_cpom' )

     mc.connectAttr( sCloseLoc + '.center', sCPOM + '.inPosition' )
     mc.connectAttr( sMesh + '.worldMatrix[0]', sCPOM + '.inputMatrix' )
     mc.connectAttr( sMesh + '.outMesh', sCPOM + '.inMesh' )
     mc.connectAttr( sCPOM + '.position', sLocOnMesh + '.translate' )
     return sLocOnMesh, sCPOM

#########    CREATE FOLLOW CAM        ####################
def createFollowCam(constrainTo=None):
    '''
    '''
    # create camera node tree
    sel = mc.ls(sl=True)[0]

    sCamera = mc.camera(n='followCam',centerOfInterest=5, focalLength=35, lensSqueezeRatio=True, cameraScale=True, horizontalFilmAperture=0.967717, horizontalFilmOffset=False, verticalFilmAperture=0.735238, verticalFilmOffset=False, filmFit='Fill', overscan=True, motionBlur=False, shutterAngle=144, nearClipPlane=0.1, farClipPlane=10000, orthographic=False, orthographicWidth=30, panZoomEnabled=False, horizontalPan=False, verticalPan=False, zoom=True)[0]
    sNull = mc.group(n='null_camFollow')

    # constrain the camera to something to follow
    if constrainTo:
        mc.pointConstraint(constrainTo, sNull, mo=False)
    elif sel:
        print 'constraining to' ,sel
        mc.pointConstraint(sel, sNull, mo=False)
    else:
        print '!!! createFollowCam() created the camera but didn\'t constrain it. Select an object and run it '
    mc.lookThru( sCamera, nc=1.0, fc=10000.0 )
 


import maya.cmds as mc
########    INSERT AN INTERMEDIATE SCULPT GEO AND CONNECT INTO NETWORK      ##################
def insertSculptGeo():
    # get selection, it's shape in inMesh plug
    sel = mc.ls(sl=True)
    outGeo = sel[0]
    outGeoShape = mc.listRelatives(outGeo, s=True)[0]
    inputGeoPlug = mc.connectionInfo(outGeoShape+'.inMesh', sourceFromDestination=True)
    # duplicate and name _sculpt
    sculptGeo = mc.duplicate(outGeo, n=outGeo+'_sculpt')[0]
    sculptGeoShape = mc.listRelatives(sculptGeo, s=True)[0]
    # make connections
    mc.connectAttr(inputGeoPlug, sculptGeoShape+'.inMesh')
    mc.connectAttr(sculptGeoShape+'.outMesh', outGeoShape+'.inMesh', f=True)
    print '### Duplicated {0} as {1} and connected it back into {0} inMesh'.format(outGeo, sculptGeo)
    

def toggleVis():
    sel = mc.ls(sl=True)
    for s in sel:
        visAttr = s + '.v'
        if mc.getAttr(visAttr):
            mc.setAttr(visAttr, 0)
        else:
            mc.setAttr(visAttr, 1)


def miltiCurveCvSelect():
    sel = mc.ls(sl=True)

    cvList = []
    num = 10

    for c in sel:
        spanCount = mc.getAttr(c + '.spans')
        cvList.append(c+'.cv[:{0}]'.format(num))
        
    mc.select(cvList)

########    SET AND CLEAR INITIAL STATE ON NCLOTH OBJECTS      ##################

def setStartFrameAndStates():
    '''
    Script that sets the initial states on nCloth objects in scene and sets nucleus start frame 
    to the current frame. Also adjusts playbackOptions.
    '''
    curTime = mc.currentTime(q=True)
    nuclei = mc.ls(type='nucleus')
    clothes = mc.ls(type='nCloth')
    for c in clothes:
        mc.nBase(c, e=True, stuffStart=True)
        print '## Set initial state on {0} to current frame'.format(c)
    for n in nuclei:
        mc.setAttr(n+'.startFrame', curTime)
        print '## Set startFrame on {0} to {1}'.format(n, curTime)
    mc.playbackOptions(e=True, minTime=curTime)
    mc.currentTime(curTime, u=True)

    
def clearStartFrameAndStates():
    '''
    Script that clears any initial states on nCloth objects in scene and sets nucleus start frame
    based on frames set in the preferences ctrl. Resets playbackOptions as well.
    '''
    prefCtrl = mc.ls('*:rig_preferences')[0]
    startFrame = mc.getAttr(prefCtrl+'.shotStart') - mc.getAttr(prefCtrl+'.cachePreRoll')
    nuclei = mc.ls(type='nucleus')
    clothes = mc.ls(type='nCloth')
    for c in clothes:
        mc.nBase(c, e=True, clearStart=True)
        print '## Set initial state on {0} to current frame'.format(c)
    for n in nuclei:
        mc.setAttr(n+'.startFrame', startFrame)
        print '## Set startFrame on {0} to {1}'.format(n, startFrame)
    mc.playbackOptions(e=True, minTime=startFrame)
    mc.currentTime(startFrame, u=True)    
    

##########################################################
# CFX HELPER GUI
##########################################################

import sys
sys.path.append('/u/jdm/tools/MPH/maya/python/')
import MPH_cfx_GUI
from MPH_cfx_GUI import *
reload(MPH_cfx_GUI)
jdm_cfxGUI()

## shaders


# shaders
def create_shaders(colours=['red','blue','yellow']):
    for color in colours:
        shader=mc.shadingNode("lambert",asShader=True, n=color+'_shader')
        # a shading group
        shading_group= mc.sets(renderable=True,noSurfaceShader=True,empty=True, n=color+'_SG')
        #connect shader to sg surface shader
        mc.connectAttr('%s.outColor' %shader ,'%s.surfaceShader' %shading_group)
        if color == 'red':
            mc.setAttr(shader+'.color', *[1,0,0])
        if color == 'blue':
            mc.setAttr(shader+'.color', *[0,0,1])
        if color == 'yellow':
            mc.setAttr(shader+'.color', *[1,1,0])
            
### create noise(time) keyframes

import maya.cmds as mc
import maya.mel as mel

def setRandomKeyFrame(node='', attribute='', frameStart='', frameEnd='', keyStep=2, keyScale=1, seed=0):
    if not frameStart:
        frameStart = mc.playbackOptions(q=True, animationStartTime=1)
    if not frameEnd:
        frameEnd = mc.playbackOptions(q=True, animationEndTime=1)
    if not node:
        node = mc.ls(sl=True)[0]
    
    time = frameStart
    
    while time <= frameEnd:
        val = mel.eval('noise(%f)' % (time+seed)) * keyScale
        mc.setKeyframe(node, attribute=attribute, t=time, value=val, inTangentType='spline', outTangentType='spline')
        time += keyStep

# create project paths

import os
import maya.cmds as mc

sPath = '/u/alz/maya/projects'
sName = 'cacheCycler'
def createNewProjectDirs(sPath, sName):
    
    if os.path.lexists(sPath):
        mc.error('path exists already')
    
    sMakeDirPath = sPath + '/' + sName
    os.makedirs(sMakeDirPath + '/media')
    os.makedirs(sMakeDirPath + '/ui')
    os.makedirs(sMakeDirPath + '/lib')
    
createNewProjectDirs(sPath, sName)


import maya.cmds as mc

 
def createIk(name='L_hip', solver='ikRPsolver', startJoint='', endEffector='', poleVector='', parent='', ctrl='', consType='parent', v=1):
    '''
    Create ikRP solver.

    @inParam name - string, name of ikHandle, suffix of _ikHandle will be added
    @inParam solver - string, type of ikSolver, choose between ikRPsolver or ikSCsolver
    @inParam startJoint - string, start joint for ikRP solver
    @inParam endEffector - string, end joint for ikRP solver
    @inParam poleVector - string, object used for poleVector, usually a control is given
    @inParam parent - string, parent ikHandle under this
    @inParam ctrl - string, parent constrain ik to control
    @inParam consType - string, type of constraint between ctrl and ikHandle, types are parent, point or orient
    @inParam v - int, visibility of ikHandle

    @procedure rig.createIk(name='L_hip', solver='ikRPsolver', startJoint=env[0], endEffector=env[1], poleVector='trap_poleVector_loc', parent=otherNull, ctrl='head_5_env', consType='parent', v=0)
    '''
    #Set preffered angle.
    mc.joint(startJoint, e=1, spa=1)

    ik = ''
    if solver == 'ikRPsolver':
        ik = mc.ikHandle(n=name+'_ikHandle', sj=startJoint, ee=endEffector, sol='ikRPsolver')[0]

        if poleVector:
            mc.poleVectorConstraint(poleVector, ik)
    elif solver == 'ikSCsolver':
        ik = mc.ikHandle(n=name+'_ikHandle', sj=startJoint, ee=endEffector, sol='ikSCsolver')[0]

    ikPos = mc.xform(ik, q=1, t=1, ws=1)
    ikNull = mc.group(n=ik.replace('_ikHandle', 'IkHandle_null'), em=1)
    mc.move(ikPos[0], ikPos[1], ikPos[2], ikNull, r=1)
    mc.parent(ikNull, parent)
    mc.parent(ik, ikNull)

    if ctrl is not '':
        if consType == 'parent' or consType == 'parentConstraint':
            mc.parentConstraint(ctrl, ik, mo=1)
        elif consType == 'point' or consType == 'pointConstraint':
            mc.pointConstraint(ctrl, ik, mo=1)
        elif consType == 'orient' or consType == 'orientConstraint':
            mc.orientConstraint(ctrl, ik, mo=1)

    mc.setAttr(ik+'.v', v)

    return [ik, ikNull]

def lockAndHideAttr(obj, attrs):
    '''
    Lock and hide attributes of given object.

    @inParam obj - string, object to lock attributes for
    @inParam attrs - list, attributes to lock

    @procedure rig.lockAndHideAttr(ctrl, ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v'])
    '''
    for attr in attrs:
        if mc.attributeQuery(attr, node=obj, ex=1):
            mc.setAttr(obj+'.'+attr, k=0, cb=0, l=1)
        else:
            print 'Attribute does not exist for '+obj+' - '+attr


#########SPACE_SWITCH####################
def addSpaceSwitch( ctrl, attrName, enums, slave, targets, constraintType, maintainOffset ):
    #ctrl = 'toto_ctrl'
    #attrName = 'spaceSwicth'
    #enums=['world','hand','local']
    #slave='toto_zro'
    #targets=['driver1','driver1','driver1']
    #constraintType='parentConstraint'
    #maintainOffset=1
    #rem_addSpaceSwitch( ctrl, attrName, enums, slave, targets, constraintType, maintainOffset )
    spaceOffs = []
    constraint = ''    
    
    #new name
    baseName = ctrl.replace('_ctrl', '')    
    
    #target space groups
    for i in range( len(enums) ):
        if maintainOffset == 0:
            spaceOffs.append(targets[i])
        else:
            grp = cmds.group( em=1, n= baseName + 'Space_' + enums[i] + '_null' )
            cmds.delete( cmds.parentConstraint( slave, grp ) )
            cmds.parentConstraint( targets[i], grp, mo=1 )
            spaceOffs.append(grp)

    #add constraints to targets space groups
    for t in spaceOffs:
        constraint = pm.mel.eval( constraintType+ '"' +t+ '" "' +slave+'"' )
    attrs = cmds.listAttr( constraint, ud=1 )
    constraint = constraint[0]   
    
    #enum attribute
    enumFlat = ':'.join(enums)
    if cmds.objExists(ctrl+'.'+attrName):
        cmds.warning('"'+ctrl+'.'+attrName+'" exist, using the exitant one, check if attribute match you\'re expecting')
        cmds.addAttr( ctrl+'.'+attrName, e=1, enumName=enumFlat )
    else:
        cmds.addAttr( ctrl, ln= attrName, at='enum', k=1, en= enumFlat )
    
    #connect enum attrs to constraint targets
    for i in range( len(enums) ):
        for j in range( len(enums) ):
            val = 0
            if i == j:
                val = 1
            cmds.setDrivenKeyframe( constraint+ '.' +attrs[j], cd=ctrl+ '.' +attrName , dv=i, v=val )
            
    return spaceOffs  



def addDoubleAttr(ctrl='', attr='', nn='', min=-10000, max=10000, dv=0, k=1, cb=1, l=False):
    '''
    Adds double attribute to object.

    @inParam ctrl - string, object to add attribute to
    @inParam attr - string, name of attribute
    @inParam nn - string, nice name of attribute
    @inParam min - float, minimum value of attribute
    @inParam max - float, maximum value of attribute
    @inParam dv - float, default value value of attribute
    @inParam k - int, attribute is keyable if on
    @inParam cb - int, attribute appears in cb if on
    @inParam l - boolean, lock attr if true

    @procedure rig.addDoubleAttr(ctrl=ctrl, attr='offset', min=0, max=1, dv=0)
    '''
    if nn == '':
        mc.addAttr(ctrl, ln=attr, at='double', min=min, max=max, dv=dv)
    else:
        mc.addAttr(ctrl, ln=attr, nn=nn, at='double', min=min, max=max, dv=dv)

    if cb:
        mc.setAttr(ctrl+'.'+attr, e=1, cb=1)
    if k:
        mc.setAttr(ctrl+'.'+attr, e=1, k=1)
    if l:
        mc.setAttr(ctrl+'.'+attr, l=1)

    return ctrl+'.'+attr


import maya.cmds as mc
########    INSERT AN INTERMEDIATE SCULPT GEO AND CONNECT INTO NETWORK      ##################
def insertSculptGeo():
    # get selection, it's shape in inMesh plug
    sel = mc.ls(sl=True)
    if not sel:
        print 'nothing is selected dumb ass'
        return
    outGeo = sel[0]
    outGeoShape = mc.listRelatives(outGeo, s=True)[0]
    inputGeoPlug = mc.connectionInfo(outGeoShape+'.inMesh', sourceFromDestination=True)
    geoParent = cmds.listRelatives(outGeo, p=True)[0]
    in_deform = cmds.listConnections(outGeo + ".inMesh")[0]

    # Duplicate the geo to create the sculpt meshes
    sculpt_shape = cmds.createNode("mesh")
    sculpt_mesh = cmds.listRelatives(sculpt_shape, parent=True)[0]
    sculpt_mesh = cmds.rename(sculpt_mesh, outGeo.replace("_geo", "_sculpt"))
    sculpt_mesh = cmds.parent(sculpt_mesh, geoParent)[0]

    oldPosition = cmds.xform(outGeo, q=True, matrix=True)
    cmds.xform(sculpt_mesh, matrix=oldPosition)
    # make connections
    mc.connectAttr(inputGeoPlug, sculpt_mesh+'.inMesh')
    mc.connectAttr(sculpt_mesh+'.outMesh', outGeoShape+'.inMesh', f=True)
    print '### Duplicated {0} as {1} and connected it back into {0} inMesh'.format(outGeo, sculpt_mesh)
    



# collect what to turn off
drones = ['droneKaijuSkin01:', 'droneKaijuSkin02:', 'droneKaijuSkin03:']
turnOffP2P = []
turnOffNx = []
for drone in drones:
    allOutputs = mc.ls(drone+'*output')
    turnOffOutputs = []
    for o in allOutputs:
        if 'skinSim' in o or 'pipesSim' in o:
            print o, '- don"t use this'
            continue
        turnOffOutputs.append(o)
    print turnOffOutputs
    children = mc.listRelatives(turnOffOutputs, c=True)     # output meshes
    # collect point2point deformers
    for c in children:
        turnOffP2P.append(mc.listConnections(c+'Shape', t='dnPoint2PointDeformer' )[0])

# collect nuclei to turn off
allNx = mc.ls(type='nucleus')
for n in allNx:
    if 'skin' in n or 'pipes' in n:
        print n, '- don"t use this'
        continue
    turnOffNx.append(n)

# turn shit off
for p2p in turnOffP2P:
    mc.setAttr(p2p+'.envelope', 0)
for nx in turnOffNx:
    mc.setAttr(nx+'.enable', 0)
    
