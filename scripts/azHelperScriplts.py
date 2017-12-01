
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
