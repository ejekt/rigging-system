
import maya.cmds as mc
import maya.mel as mm
import re
import dnRig.utils.dnPoint2PointDeformer as p2p
import random




class Sinew():
    ''' Each instance of this class setsup 1 sinew/tentacle/muscle for the droneKaiju.
    Initialization takes in a single dictionary entry (which includes data such as the name, poly faces, and joints to constrain to)
    and the intermediate geo to make the deformers deform.
    The Sinew can be one of three setups: 
    isTentacle describes any of the stand alone geos called *tentacle* on top of the armor, deformed using a wire.
    isMuscle describes non tubular areas such as the pecs and lats, deformed using a push node.
    Anything else is a tubular sinew that is part of the body_geo, deformed using a wire on a mesh cutout that's point2point back.

    All the data comes from /jobs/MAE/rdev_droneKaiju/maya/build/scripts/droneKaiju_sinew_data.json
    '''
    def __init__(self, sinewInfo, intermediateDrivenObj):
        self.isTentacle = False
        self.isMuscle = False

        self.intermediateGeoShapes = []

        if sinewInfo['tentacle']:
            # if the 'tentacle' dict key isn't None the sinew is set to isTentacle
            # basic naming is setup
            self.bodyGeo = sinewInfo['tentacle']
            self.isTentacle = True
            self.name = self.bodyGeo + '_sinew'
            self.tentacleGeo = sinewInfo['tentacle'].replace('_mesh','_geo')
            print '\nBegin init: ', self.name
        
        elif sinewInfo.has_key('muscle'):
            # only the dict entries that have a 'muscle' key are set to isMuscle
            self.isMuscle = True
            self.bodyGeo = 'body_geoShapeOrig'
            self.name = sinewInfo['part'] + '_sinew'
            print '\nBegin init: ', self.name

        else:
            self.name = sinewInfo['part'] + '_sinew' 
            print '\nBegin init: ', self.name
            self.bodyGeo = 'body_geoShapeOrig'

        self.groupParts = 'bodyGeo_skinClusterGroupParts'
        self.locs = []
        self.curves = []
        if sinewInfo.has_key('rampInfo'):
            self.rampInfo = sinewInfo['rampInfo']
        self.intBodyGeoShape = ''
        
        self.joint1 = sinewInfo['joint1']
        self.joint2 = sinewInfo['joint2']

        # point1 & 2 are each a locator that get's created between the average position of 3 verts per point.
        # 2 sets of 3 verts are stated in the json 
        self.point1 = self.constrainLocBetweenPositions(sinewInfo['point1'], keepConst=False)
        self.point2 = self.constrainLocBetweenPositions(sinewInfo['point2'], keepConst=False)
                
        # constrain center locators to the joints and create a straight line curve between them
        self.constrainToJoints()
        self.twoPointCurve = createCurveBtw2Transforms(self.point1, self.point2)
        self.twoPointCurve = mc.rename(self.twoPointCurve, self.name + '_' + self.twoPointCurve)
        
        if not self.isTentacle:
            # create the meshs
            self.mesh = self.cutOutMeshPiece(sinewInfo['faces'])[0]
            mc.setAttr(self.mesh+'.v', 0)
            # p2p the curout mesh to the intermediateDrivenObj
            self.point2point(self.mesh, intermediateDrivenObj)
            # set the curve names # these are imported from an external file in pinnochhio
            # if they don't exist they'll get created a little later
            self.curve = sinewInfo['part']+'_wrapCrv' 

        else:       # if it is a tentacle
            self.tentacleName = sinewInfo['tentacle']
            self.pieceMeshTrans = self.tentacleName.replace('_mesh','_geo')
            self.intTentacleGeoShape = None
            #self.tentacleGeo = self.pieceMeshTrans 
            self.createIntTentacleGeo()
            self.mesh = self.tentacleName 
            #self.blendshapeTentacle()
            self.curve = sinewInfo['tentacle']+'_wrapCrv' # these are imported from an external file in pinnochhio

        if not self.isMuscle:
            # create curve
            if not mc.objExists(self.curve):
                self.createCurveDownCenterOfUvShell()
            # create the wire
            self.createTendrilWireDeformer()
            self.apply_ramps(as_map=True)            

        # squash and stretch
        self.createDistanceNode()
        
        ###  fancy shit
        # all muscles get a frame cache node to check length in the future
        self.frameCacheNodeSetup()
        if self.isTentacle:
            self.createPairBlend(sinewInfo['minDist'], sinewInfo['maxDist'], sinewInfo['blend'])
            self.setKeyFrames(wireSetup=True, pushNodeSetup=False)
        elif self.isMuscle:
            self.createMusclePushNode(self.mesh)
            self.createPairBlend(sinewInfo['minDist'], sinewInfo['maxDist'], sinewInfo['blend'])
            self.setKeyFrames(pushNodeSetup=True)
        else:
            self.createPairBlend()
            self.setKeyFrames()

        self.loadDeformerWeightMap()
        self.createCircleControls()
    
        # organize
        self.nodes = [self.point1, self.point2, self.mesh, 
                    self.twoPointCurve, self.ctrl, ]
        if not self.isTentacle and not self.isMuscle:
            self.nodes.append(self.pt3d)
        self.groupNodes()


    def loadDeformerWeightMap(self):
        weightFile = '/jobs/MAE/rdev_droneKaiju/maya/build/maps/droneKaiju_cfx_sinew_weights.abc'
        if self.isTentacle:
            try:
                print 'applying deformer weights on ', self.intTentacleGeoShape
                mc.setAttr(self.intTentacleGeoShape+'.intermediateObject', 0)
                mc.wimpIO(self.wire, f=weightFile, load=True)
                mc.setAttr(self.intTentacleGeoShape+'.intermediateObject', 1)
            except:
                pass
        elif self.isMuscle:
            mc.wimpIO(self.pushNode, f=weightFile, load=True)



    def createMusclePushNode(self, mesh):
        mc.select(mesh, r=True)
        mm.eval('if (!`pluginInfo -q -loaded dnBeefCake`) {loadPlugin dnBeefCake;}')
        pushNode = mm.eval('dnPushNode_create;')
        pushNode = mc.rename(pushNode, self.name+'_dnPush')
        self.pushNode = pushNode


    def blendshapeTentacle(self):
        self.mesh = self.tentacleName 
        self.pieceMeshTrans = self.mesh.replace('_mesh','_geo')
        self.geo = self.mesh.replace('_mesh','_geo')
        targets = [self.mesh+'_thin', self.mesh+'_thick']
        self.bsNode = mc.blendShape(targets[0], targets[1], self.geo, n=self.name+'_bs')[0]


    def createDistanceNode(self):
        # distance between point1 and point2
        self.dist = mc.shadingNode('distanceBetween', asUtility=True, n=self.name+'_dist')
        mc.connectAttr(self.point1+'.t', self.dist+'.point1', f=True)
        mc.connectAttr(self.point2+'.t', self.dist+'.point2', f=True)

        # create distance delta pma node
        self.distDeltaPMA = mc.createNode('plusMinusAverage', n=self.name+'_distDelta_PMA')
        mc.setAttr(self.distDeltaPMA+'.operation', 2)    # subtract
        # connect current distance to input 1
        mc.connectAttr(self.dist+'.distance', self.distDeltaPMA+'.input1D[1]')


    def frameCacheNodeSetup(self):
        # used to calculate distance in the future
        self.fcNode = mc.createNode('frameCache', n=self.name+'_frameCache')
        mc.connectAttr(self.dist+'.distance', self.fcNode+'.stream', f=True)
        # connect future distance to input 0 of the distance delta
        mc.connectAttr(self.fcNode+'.varying', self.distDeltaPMA+'.input1D[0]')

        # add a time offset connected to time and connect to vary time
        self.timePMA = mc.createNode('plusMinusAverage', n=self.name+'_time_PMA')
        mc.connectAttr('time1.outTime', self.timePMA+'.input1D[0]')
        mc.connectAttr(self.timePMA+'.output1D',self.fcNode+'.varyTime', f=True)


    def createRangeAnimCurve(self, inPlug, outPlug, name='animCurve', *args):
        self.animCurve = mc.createNode('animCurveUU', n=self.name+'_'+name)
        print 'setting up sinew animCurveUU'
        mc.connectAttr(inPlug, self.animCurve+'.input', f=True)
        mc.connectAttr(self.animCurve+'.output', outPlug, f=True)
        return self.animCurve


    def setKeyFrames(self, wireSetup=True, pushNodeSetup=False):
        if wireSetup:
            mc.setKeyframe(self.distAnimCurve, float=-0.2, value=1.52, outTangentType='flat')
            mc.setKeyframe(self.distAnimCurve, float=0, value=1.5, outTangentType='spline')
            mc.setKeyframe(self.distAnimCurve, float=0.5, value=1.27, inTangentType='spline')
            mc.setKeyframe(self.distAnimCurve, float=1.2, value=0.5, inTangentType='flat')

        if pushNodeSetup:
            mc.setKeyframe(self.distAnimCurve, float=0, value=2, outTangentType='flat')
            mc.setKeyframe(self.distAnimCurve, float=1, value=-2, inTangentType='flat')

        mc.setKeyframe(self.deltaAnimCurve, float=-1, value=1.5, outTangentType='flat')
        mc.setKeyframe(self.deltaAnimCurve, float=-.5, value=1.1, inTangentType='spline')
        mc.setKeyframe(self.deltaAnimCurve, float=2, value=1, outTangentType='flat')


    def createPairBlend(self, minVal=0, maxVal=1, fBlend=0.8):
        # distance multiply divide in case we need one. Does nothing for now.
        distanceMd = mc.createNode('multiplyDivide', n=self.name+'_dist')
        mc.connectAttr(self.fcNode+'.varying', distanceMd+'.input1X', f=True)
        mc.setAttr(distanceMd+'.operation', 1)      # multiply
        mc.setAttr(distanceMd+'.input2X', 1)

        # remap node to take in pre saved json data and map distance to 0-1
        remapNode = mc.createNode('remapValue', n=self.name+'_remap')
        mc.connectAttr(distanceMd+'.outputX', remapNode+'.inputValue', f=True)
        mc.setAttr(remapNode+'.inputMin', minVal)      # multiply
        mc.setAttr(remapNode+'.inputMax', maxVal)
        mc.setAttr(remapNode+'.outputMin', -0.2)
        mc.setAttr(remapNode+'.outputMax', 1.2)
        self.remapNode = remapNode

        # difference in distance multiply divide to shrink the delta values to hover betewen -1 and 1
        deltaDistMd = mc.createNode('multiplyDivide', n=self.name+'_delta')
        mc.connectAttr(self.distDeltaPMA+'.output1D', deltaDistMd+'.input1X', f=True)
        mc.setAttr(deltaDistMd+'.operation', 1)     # multiply
        mc.setAttr(deltaDistMd+'.input2X', -0.1)
        self.deltaDistMd = deltaDistMd

        # create the pairBlend
        pairBlend = mc.createNode('pairBlend', n=self.name+'_pairBlend')
        blendInX1 = pairBlend + '.inTranslate1.inTranslateX1'
        blendInX2 = pairBlend + '.inTranslate2.inTranslateX2'
        mc.setAttr(pairBlend+'.weight', fBlend)
        self.pairBlend = pairBlend

        # create the animCurveUU nodes. (inPlug, outPlug, curveName)
        self.distAnimCurve = self.createRangeAnimCurve(remapNode+'.outValue',
                                                       blendInX1, 
                                                       'distAnimCurve')
        self.deltaAnimCurve = self.createRangeAnimCurve(deltaDistMd+'.outputX',
                                                        blendInX2, 
                                                        'deltaAnimCurve')
        # create the envelope multiply divide node
        envelopeMd = mc.createNode('multiplyDivide', n=self.name+'_envelopeMd')
        mc.connectAttr(pairBlend+'.outTranslate.outTranslateX', envelopeMd+'.input1X', f=True)
        mc.setAttr(envelopeMd+'.operation', 1)      # multiply
        self.envelopeMd = envelopeMd
        # create the additive offset plusMinus node
        offsetPm = mc.createNode('plusMinusAverage', n=self.name+'_offsetPlusMinus')
        mc.connectAttr(envelopeMd+'.outputX', offsetPm+'.input1D[0]', f=True)
        mc.setAttr(offsetPm+'.operation', 1)      # sum
        self.offsetPm = offsetPm
        # connect final output to the envelope
        if not self.isMuscle:
            # map the pairBlend into the wire scale
            mc.connectAttr(offsetPm+'.output1D', self.wire+'.scale[0]', f=True)
        else:
            mc.connectAttr(offsetPm+'.output1D', self.pushNode+'.amplitude', f=True)



    def createCircleControls(self):
        # create the control
        ctrlNodes = mc.circle(n=self.name+'_gavin', normal=[0,1,0])
        self.ctrl = ctrlNodes[0]
        mc.setAttr(ctrlNodes[1]+'.radius', 30)
        mc.delete(self.ctrl, ch=True)
        # constrain it
        pCon = mc.pointConstraint(['|'+self.point1, '|'+self.point2], self.ctrl, mo=False)[0]

        aCon = mc.aimConstraint(['|'+self.point1], self.ctrl, 
                                offset=[0, 0, 0], weight=1 ,aimVector=[0, 1, 0],
                                upVector=[0, 1, 0], worldUpType="object", 
                                worldUpVector=[0, 1, 0])[0]

        # add more attrs
        mc.addAttr(self.ctrl, ln='dataDisplay', at='enum', enumName='----', k=True, )

        mc.addAttr(self.ctrl, ln='currentDistance', at='double', k=True, )
        mc.addAttr(self.ctrl, ln='frameCacheDistance', at='double', k=True, )
        mc.addAttr(self.ctrl, ln='varyingTime', at='double', k=True, )
        mc.addAttr(self.ctrl, ln='timeOffset', at='double', k=True, dv=0)
        mc.addAttr(self.ctrl, ln='deltaDistMult', at='double', k=False, dv=1)
        mc.addAttr(self.ctrl, ln='remapMin', at='double', k=True, dv=1)
        mc.addAttr(self.ctrl, ln='remapMax', at='double', k=True, dv=1)
        # get pairBlend attr and add it to the ctrl
        blendVal = mc.getAttr(self.pairBlend+'.weight')
        mc.addAttr(self.ctrl, ln='blendDistAndDelta', at='double', k=True, dv=blendVal)

        mc.addAttr(self.ctrl, ln='muscleControlAttrs', at='enum', enumName='----', k=True, )  
        mc.addAttr(self.ctrl, ln='tendrilBulgeScale', at='double', k=True)
        mc.connectAttr(self.ctrl+'.tendrilBulgeScale', self.envelopeMd+'.input2X')
        mc.setAttr(self.ctrl+'.tendrilBulgeScale', 1)
        mc.addAttr(self.ctrl, ln='tendrilBulgeOffset', at='double', k=True, dv=0)
        mc.connectAttr(self.ctrl+'.tendrilBulgeOffset', self.offsetPm+'.input1D[1]')

        # add additive offset keyable attr
        
        lockAndHideAttr(self.ctrl, ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v'])

        # visualize attributes        
        mc.connectAttr(self.dist+'.distance', self.ctrl+'.currentDistance')
        mc.connectAttr(self.fcNode+'.varying', self.ctrl+'.frameCacheDistance')
        mc.connectAttr(self.timePMA+'.output1D', self.ctrl+'.varyingTime')
        # custom attributes for controlling sinew
        mc.connectAttr(self.ctrl+'.deltaDistMult', self.deltaDistMd+'.input2X')
        mc.connectAttr(self.ctrl+'.timeOffset', self.timePMA+'.input1D[1]')
        # remap min max attributes
        mc.setAttr(self.ctrl+'.remapMin', mc.getAttr(self.remapNode+'.inputMin'))
        mc.setAttr(self.ctrl+'.remapMax', mc.getAttr(self.remapNode+'.inputMax'))
        mc.connectAttr(self.ctrl+'.remapMax', self.remapNode+'.inputMax')
        mc.connectAttr(self.ctrl+'.remapMin', self.remapNode+'.inputMin')   
        mc.connectAttr(self.ctrl+'.blendDistAndDelta', self.pairBlend+'.weight')

        
        


    def point2point(self, driver, driven):
        mc.setAttr(driven+'.intermediateObject', 0)
        mc.select(cl=True)
        p2p.create(driver, driven) 
        mc.setAttr(driven+'.intermediateObject', 1)


    def constrainToJoints(self):
        pCon1 = mc.parentConstraint(self.joint1, '|'+self.point1, mo=True)
        pCon2 = mc.parentConstraint(self.joint2, '|'+self.point2, mo=True)


    def groupNodes(self):
        locsGrp = mc.group(n=self.name+'_locs_grp', em=True)
        mc.parent(self.locs, locsGrp, shape=False)
        
        topGrp = mc.group(n=self.name+'_grp', em=True)

        if self.curves:
            crvsGrp = mc.group(n=self.name+'_crvs_grp', em=True)
            mc.setAttr(crvsGrp+'.v', 0)
            mc.parent(self.curves, crvsGrp, shape=False)
            if self.isTentacle:
                # parent constrain group to mesh transform so wire works
                mc.parentConstraint(self.tentacleGeo, crvsGrp, mo=True)
                # parent deformed curve to the geo too
                #if self.intTentacleGeoShape == None:
                #mc.parent(self.curve, crvsGrp)


            mc.parent([locsGrp, crvsGrp], topGrp, shape=False)
        else:
            mc.parent([locsGrp], topGrp, shape=False)

        transforms = mc.ls(self.nodes, type='transform')
        if transforms:
            mc.parent(transforms, topGrp, shape=False)

        #mc.setAttr(topGrp+'.v', 0)
        mc.parent(topGrp, 'rig')

        

    def createLocOnCurve(self, curve, uVal=0.5):
        paramLoc = mc.paramLocator( '{}.u[{}]'.format(curve, uVal) )
        return paramLoc


    def cutOutMeshPiece(self, facesList):
        mesh = self.bodyGeo
        # format component list of the faces we want to cut out
        faceComps = [f.split('.')[-1] for f in facesList]
        # create Adam's invertComponentList node and pass it the list of face components
        invCompNode = mc.createNode('invertComponentList', n=self.name+'_invCompList')
        mc.setAttr(invCompNode+'.inComponents', len(faceComps), *faceComps, type='componentList')
        # create delete and mesh and make all the connections
        delNode = mc.createNode('deleteComponent', n=self.name+'_delComp')
        self.pieceMeshShape = mc.createNode('mesh', n=self.name+'_meshShape')
        self.pieceMeshTrans = mc.listRelatives(self.pieceMeshShape, p=True)[0]
        self.pieceMeshTrans = mc.rename(self.pieceMeshTrans, self.name+'_mesh')
        mc.connectAttr(mesh+'.outMesh', invCompNode+'.mesh', f=True)
        mc.connectAttr(mesh+'.outMesh', delNode+'.inputGeometry', f=True)
        mc.connectAttr(invCompNode+'.outComponents', delNode+'.deleteComponents', f=True)
        mc.connectAttr(delNode+'.outputGeometry', self.pieceMeshShape+'.inMesh', f=True)
        return self.pieceMeshTrans, self.pieceMeshShape


    def createCurveDownCenterOfUvShell(self):
        tendril = self.pieceMeshTrans

        vert_map = {}
        print tendril
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
        cur = mc.curve(d=3, p=pts, n=self.curve)

        mc.rebuildCurve(cur, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=1, kep=1, kt=0, s=22, d=3, tol=0.01)
        mc.rename(mc.listRelatives(cur, c=True, pa=True)[0], cur+'Shape')
        self.curve = cur
        return cur


    def createTendrilWireDeformer(self):
        print 'creating wire on {}'.format(self.curve)
        if self.isTentacle:
            if self.intTentacleGeoShape:
                # for cases where the tentacle is skinned
                mc.setAttr(self.intTentacleGeoShape+'.intermediateObject', 0)
                wire_deformer = mc.wire(self.intTentacleGeoShape, 
                                        wire=self.curve, en=1, dds=(0,200), 
                                        n=self.name+'_wire',
                                        frontOfChain=True)[0]
                mc.setAttr(self.intTentacleGeoShape+'.intermediateObject', 1)
            else:
                # for cases where the tentacle is not skinned but constrained
                wire_deformer = mc.wire(self.pieceMeshTrans, 
                                        wire=self.curve, en=1, dds=(0,200), 
                                        n=self.name+'_wire',
                                        frontOfChain=False)[0]

        else:
            # for non-tentacle sinew cases
            wire_deformer = mc.wire(self.pieceMeshTrans, 
                                    wire=self.curve, en=1, dds=(0,200), 
                                    n=self.name+'_wire',
                                    frontOfChain=True)[0]
        # find base wire curve name and rename it's shape
        baseWire = mc.listConnections(wire_deformer+'.baseWire[0]', s=True)[0]
        mc.rename(mc.listRelatives(baseWire, c=True, pa=True)[0], baseWire+'Shape')
        self.wire = wire_deformer
        self.curves.extend([self.curve, baseWire, self.wire])


    def wrapWire(self):
        mc.deformer(self.pieceMeshTrans, frontOfChain=True, type='wrap', n=self.name+'_wrap')


    def constrainLocBetweenPositions(self, verts, keepConst=True):
        createdLocs = createLocatorsAtVerts(verts)
        # generate unique number for the name of the new locator
        summ = 0
        for v in createdLocs:
            num = getLastDigits(v)
            summ = summ + num
        avgNum = num/len(verts)
        # create new locator and constrain it to be in between all verts
        avgLoc = mc.spaceLocator(n='loc_center_{}'.format(self.name))[0]
        pCon = mc.pointConstraint(createdLocs, avgLoc, mo=False)[0]
        if not keepConst:
            mc.delete(pCon)
        createdLocs.append(avgLoc)
        self.locs.extend(createdLocs)
        return avgLoc
     

    def setupSquashStretch(self):
        expVal = 1.5
        # distance between point1 and point2
        dist = mc.shadingNode('distanceBetween', asUtility=True, n=self.name+'_dist')
        mc.connectAttr(self.point1+'.t', dist+'.point1', f=True)
        mc.connectAttr(self.point2+'.t', dist+'.point2', f=True)
        # create multiply divide nodes
        scaleFactor = mc.shadingNode('multiplyDivide', asUtility=True, n=self.name+'_scaleVal_md')
        '''scalePower = mc.shadingNode('multiplyDivide', asUtility=True, n=self.name+'_scalePower_md')
        invertScalePower = mc.shadingNode('multiplyDivide', asUtility=True, n=self.name+'_invertScalePower_md')
        # setup scale factor 
        mc.setAttr(scaleFactor+'.operation', 2)
        startDist = mc.getAttr(dist+'.distance')
        mc.connectAttr(dist+'.distance', scaleFactor+'.input1X', f=True)
        mc.setAttr(scaleFactor+'.input2X', startDist)
        # setup scale to the power 
        mc.setAttr(scalePower+'.operation', 3)
        mc.connectAttr(scaleFactor+'.outputX', scalePower+'.input1X', f=True)
        mc.setAttr(scalePower+'.input2X', expVal)
        #setup invert power
        mc.setAttr(invertScalePower+'.operation', 2)
        mc.setAttr(invertScalePower+'.input1X', 1)
        mc.connectAttr(scalePower+'.outputX', invertScalePower+'.input2X', f=True)
        mc.connectAttr(invertScalePower+'.outputX', self.wire+'.scale[0]', f=True)
        self.scaleFactor = scaleFactor
        self.scalePowerMD = scalePower
        self.invertScalePowerMD = invertScalePower
        print 'Setup squash and stretch for sinew ', self.name'''



    def apply_ramps(self, as_map):
        mc.refresh()
        if self.isTentacle:
            return
        if self.rampInfo:
            pos = self.rampInfo[0]
            rot = self.rampInfo[1]
            scale = self.rampInfo[2]
        
            print 'Added ramps for %s' % self.name

            res = self.ramp_weights(pos, rot, scale, as_map)


    def ramp_weights(self, pos, rotate, scale, as_map):
        has_nodes = mc.objExists(self.name+'_proj')
        name = self.name
        ramp = self.name+'_ramp'
        pt3d = self.name+'_projectionPt3d'
        print 'Creating ramp %s' % ramp
        if has_nodes:
            return False
        if not has_nodes:
            proj = mc.shadingNode('projection', asTexture=1, n=name+'_proj')
            ramp = mc.shadingNode('ramp', asTexture=1, n=ramp)
            pt3d = mc.shadingNode('place3dTexture', asUtility=1, n=pt3d)
            mc.parent(pt3d, 'rig')
            mc.setAttr(pt3d+'.visibility', True)
            mc.connectAttr(pt3d+'.wim[0]', proj+'.pm')
            mc.connectAttr(ramp+'.outColor', proj+'.image')
            pt2d = mc.shadingNode('place2dTexture', asUtility=1, n=name+'_rampPt2d')
            mc.connectAttr(pt2d+'.outUV', ramp+'.uv')
            mc.connectAttr(pt2d+'.outUvFilterSize', ramp+'.uvFilterSize')
            mc.setAttr(pt3d+'.translate', *pos)
            mc.setAttr(pt3d+'.rotate', *rotate)
            mc.setAttr(pt3d+'.scale', *scale)
            self.pt3d = pt3d

            # set ramp colors
            mc.setAttr(ramp+'.colorEntryList[0].color', 0,0,0)
            mc.setAttr(ramp+'.colorEntryList[0].position', 0)

            mc.setAttr(ramp+'.colorEntryList[1].color', 1,1,1)
            mc.setAttr(ramp+'.colorEntryList[1].position', 0.5)

            mc.setAttr(ramp+'.colorEntryList[2].color', 0,0,0)
            mc.setAttr(ramp+'.colorEntryList[2].position', 1)

            mc.setAttr(ramp+'.type', 1)
            mc.setAttr(ramp+'.interpolation', 4)

        
        if as_map:
            samp = self.pieceMeshTrans+'_sampler'
            if not mc.objExists(samp):
                ref_mesh = [f for f in mc.listHistory(self.wire+'.input[0]') if mc.nodeType(f) == 'mesh'][0]
                samp = mc.createNode('dnWimpTextureSampler', n=self.wire+'_sampler')
                mc.connectAttr(ref_mesh+'.outMesh', samp+'.geom')
                mc.connectAttr(proj+'.outColor', samp+'.texture')
            else:
                cons = mc.listConnections(samp+'.outR.outRMulti', sh=1,p=1,c=1)
                if cons:
                    mc.disconnectAttr(*cons)
            if not self.isTentacle:
                mc.connectAttr(samp+'.outR.outRMulti', self.wire+'.weightList[0]')
            else:
                print ' need to setup the ramp to drive something other than the wire'
        
        return True


    def createIntBodyGeo(self):
        # create an intermediate mesh between the bodyShapeOrig and the skinCluster
        # DO THIS ONCE
        if not mc.objExists(self.bodyGeo+'_int'):
            self.intBodyGeoShape = mc.createNode('mesh', n=self.bodyGeo+'_int', 
                                                p=mc.listRelatives(self.bodyGeo, p=True)[0])
            inConnection = mc.listConnections(self.groupParts+'.inputGeometry', p=True)[0]
            mc.connectAttr(inConnection, self.intBodyGeoShape+'.inMesh', f=True)
            mc.connectAttr(self.intBodyGeoShape+'.outMesh', self.groupParts+'.inputGeometry', f=True)
            mc.setAttr(self.intBodyGeoShape+'.intermediateObject', 1)


    def createIntTentacleGeo(self):
        tentacleSkinCluster = self.pieceMeshTrans + '_skinCluster'
        tentacleGroupParts = self.pieceMeshTrans + '_skinClusterGroupParts'
        if not mc.objExists(tentacleSkinCluster):
            return

        if not mc.objExists(self.pieceMeshTrans+'_intermediateShape'):
            self.intTentacleGeoShape = mc.createNode('mesh', n=self.pieceMeshTrans+'_intermediateShape', 
                                                p=mc.listRelatives(self.pieceMeshTrans, p=True)[0])
            inConnection = mc.listConnections(tentacleGroupParts+'.inputGeometry', p=True)[0]
            mc.connectAttr(inConnection, self.intTentacleGeoShape+'.inMesh', f=True)
            mc.connectAttr(self.intTentacleGeoShape+'.outMesh', tentacleGroupParts+'.inputGeometry', f=True)
            mc.setAttr(self.intTentacleGeoShape+'.intermediateObject', 1)



    def createAnimCurveClamp(self):
        if self.isTentacle:
            print 'setting up tentacle animCurves and other util nodes'
            # thick case
            condition = mc.createNode('condition', n=self.name+'_condition1')
            reverseNode = mc.createNode('reverse', n=self.name+'_reverse1')
            mdNode = mc.createNode('multiplyDivide', n=self.name+'_md1')
            self.animCurve = mc.createNode('animCurveUU', n=self.name+'_animCurve1')
            # scaleFactor to reverse *-1 into condition if True and out to the animCurve1
            mc.connectAttr(self.scaleFactor+'.outputX', reverseNode+'.inputX', f=True)
            mc.connectAttr(reverseNode+'.outputX', mdNode+'.input1X', f=True)
            mc.setAttr(mdNode+'.input2X', -1)
            mc.connectAttr(self.scaleFactor+'.outputX', condition+'.firstTerm', f=True)
            mc.connectAttr(mdNode+'.outputX', condition+'.colorIfTrue.colorIfTrueR', f=True)
            mc.setAttr(condition+'.secondTerm', 1)
            mc.setAttr(condition+'.operation', 2)       # greater than
            mc.setAttr(condition+'.colorIfFalse.colorIfFalseR', 0)
            mc.connectAttr(condition+'.outColor.outColorR', self.animCurve+'.input', f=True)
            # anim curve to the BS
            mc.connectAttr(self.animCurve+'.output', self.bsNode+'.w[0]', f=True)
            mc.setKeyframe(self.animCurve, float=0, value=0, outTangentType='linear')
            mc.setKeyframe(self.animCurve, float=1, value=1.5, inTangentType='flat')
            
            # thin case
            condition = mc.createNode('condition', n=self.name+'_condition2')
            reverseNode = mc.createNode('reverse', n=self.name+'_reverse2')
            self.animCurve = mc.createNode('animCurveUU', n=self.name+'_animCurve2')
            # scaleFactor to reverse into condition if True and out to the animCurve1
            mc.connectAttr(self.scaleFactor+'.outputX', reverseNode+'.inputX', f=True)
            mc.connectAttr(reverseNode+'.outputX', condition+'.colorIfTrue.colorIfTrueR', f=True)
            mc.connectAttr(self.scaleFactor+'.outputX', condition+'.firstTerm', f=True)
            mc.setAttr(condition+'.secondTerm', 1)
            mc.setAttr(condition+'.operation', 4)       # less than
            mc.setAttr(condition+'.colorIfFalse.colorIfFalseR', 0)
            mc.connectAttr(condition+'.outColor.outColorR', self.animCurve+'.input', f=True)
            # anim curve to the BS
            mc.connectAttr(self.animCurve+'.output', self.bsNode+'.w[1]', f=True)
            mc.setKeyframe(self.animCurve, float=0, value=0, outTangentType='linear')
            mc.setKeyframe(self.animCurve, float=1, value=1.5, inTangentType='flat')

            mc.setAttr(self.wire+'.envelope', 0)

        else:
            self.animCurve = mc.createNode('animCurveUU', n=self.name+'_animCurve')
            print 'setting up sinew animCurveUU'
            mc.connectAttr(self.frameCache+'.varying', self.animCurve+'.input', f=True)
            mc.connectAttr(self.animCurve+'.output', self.wire+'.scale[0]', f=True)
            mc.setKeyframe(self.animCurve, float=0, value=0.1, outTangentType='linear')
            mc.setKeyframe(self.animCurve, float=1, value=1, inTangentType='linear')
            mc.setKeyframe(self.animCurve, float=3, value=3, inTangentType='flat')


    def createFrameCacheCondition(self):
        if not self.frameCache:
            return
        # get current connection out of the frameCache
        fcConnections = mc.listConnections(self.frameCache+'.varying', p=True, d=True, s=False)
        fcConnection = [f for f in fcConnections if not mc.nodeType(f) == 'transform'][0]

        # if future value of the invertScalePowerMD is greater than present one
        # the value going to the wire.scale should be the future one - anticipation
        self.condition = mc.createNode('condition', n=self.name+'_fcCondition')
        mc.connectAttr(self.frameCache+'.varying', self.condition+'.firstTerm')
        mc.connectAttr(self.invertScalePowerMD+'.outputX', self.condition+'.secondTerm')
        mc.setAttr(self.condition+'.operation', 2)      # greater than
        mc.connectAttr(self.invertScalePowerMD+'.outputX', self.condition+'.colorIfFalse.colorIfFalseR')
        mc.connectAttr(self.frameCache+'.varying', self.condition+'.colorIfTrue.colorIfTrueR')
        # connect condition out to the former frameCache connection
        mc.connectAttr(self.condition+'.outColor.outColorR', fcConnection, f=True)






 ############-----------------------------------------------------------------------------










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


def createIntBodyGeo(sGeoShape, sGroupParts):
    # create an intermediate mesh between the bodyShapeOrig and the skinCluster
    # DO THIS ONCE
    intGeoShape = mc.createNode('mesh', n=sGeoShape+'_int', 
                                        p=mc.listRelatives(sGeoShape, p=True)[0])
    inConnection = mc.listConnections(sGroupParts+'.inputGeometry', p=True)[0]
    mc.connectAttr(inConnection, intGeoShape+'.inMesh', f=True)
    mc.connectAttr(intGeoShape+'.outMesh', sGroupParts+'.inputGeometry', f=True)
    mc.setAttr(intGeoShape+'.intermediateObject', 1)
    return intGeoShape


def point2point(driver_shapes, driven_orig_shape, driven_out_shape):
    if len(driver_shapes) > 1:
        unite = mc.createNode('polyUnite')
        for id, m in enumerate(driver_shapes):
            mc.connectAttr(m+'.outMesh', '%s.inputPoly[%d]' % (unite, id))
            mc.connectAttr(m+'.worldMatrix[0]', '%s.inputMat[%d]' % (unite, id))
        attr = unite+'.output'
    else:
        attr = driver_shapes[0]+'.outMesh'
    p2p = mc.createNode('dnPoint2PointDeformer')
    gp = mc.createNode('groupParts')
    mc.setAttr(gp+'.inputComponents', 1, 'vtx[*]', type='componentList')
    gid = mc.createNode('groupId')

    mc.setAttr(driven_out_shape+'.intermediateObject', 0)

    mc.connectAttr(driven_orig_shape+'.outMesh', gp+'.inputGeometry')
    mc.connectAttr(gid+'.groupId', gp+'.groupId')
    mc.connectAttr(gid+'.groupId', p2p+'.input[0].groupId')
    mc.connectAttr(gp+'.outputGeometry', p2p+'.input[0].inputGeometry')
    mc.connectAttr(p2p+'.outputGeometry[0]', driven_out_shape+'.inMesh', f=True)
    mc.connectAttr(attr, p2p+'.driverMesh')
    mc.dnPoint2PointBuild(p2p, md=0.0001)

    mc.setAttr(driven_out_shape+'.intermediateObject', 1)
    print '\nCreated and connected {} to {} and {} '.format(p2p, unite, driven_out_shape)
    return p2p


def getSel( iMaxSel=1, bMultiSel=False ):
    sel = mc.ls(sl=True)
    if not bMultiSel:
        if len(sel) == iMaxSel:
            return sel
        else:
            mc.warning('\t !!! Wrong selection. Please select %i number of elements and re-run the tool. !!! ( %i objects were selected.)' %(iMaxSel, len(sel)))
    else:
        return sel


def createLocatorsAtVerts(verts):
    locatorNames = []
    for v in verts:
        num = getLastDigits(v)
        mc.select(v, r=True)
        loc = createLocOnMesh(sLoc='|loc_vtx_{}'.format(str(num)))
        locatorNames.append('|'+loc)
        mc.select(cl=True)
    return locatorNames


def createLocOnMesh( sLoc=None, sMesh=None, sel = None ):
    #sel = sel or mc.ls(sl=1)
    #rig.createFollicle(name='follicle', surface='', obj='', driver='follicle', connectType='', UV=[], parent='')
    # get one item selected
    sel = getSel(iMaxSel=1)
    if sel and 'vtx' in sel[0]:
        vtx = sel[0]
        sMesh = mc.ls(vtx, o=True)[0]
    else:
        mc.error('!!! Select only one vertex.')

    if not sLoc:
        sLoc = 'loc_vtx_01'
    
    sLoc = mc.spaceLocator( name=sLoc )[0]

    # snap locator to vtx position
    vPos = mc.xform(vtx, q=True, t=True, ws=True)
    mc.setAttr('|'+sLoc+'.tx', vPos[0])
    mc.setAttr('|'+sLoc+'.ty', vPos[1])
    mc.setAttr('|'+sLoc+'.tz', vPos[2])
    mc.select(sMesh, r=True)
    mc.select('|'+sLoc, add=True)
    mm.eval('dnMeshConstraint;')
    mc.select('|'+sLoc, r=True)
    return sLoc


def getLastDigits(sName):
    iNum = [int(s) for s in re.findall(r'\d+', sName)][-1]
    return iNum


def createCurveBtw2Transforms( posA, posB):
    # create and name the curve and it's shape
    print 'making straight curve for {} and {}'.format(posA, posB)
    crvName = 'straight_crv'
    crv = mc.curve( d=1, p=[[0,0,0],[1,0,0]], n=crvName)
    mc.rename(mc.listRelatives(crv, children=True)[0], crvName+'Shape')
    #mc.parent( crv, posA, r=1 )    
    mc.setAttr( crv+'.it', 0 )
    mc.setAttr( crv+'.overrideEnabled', 1 )
    #mc.setAttr( crv+'.overrideDisplayType', 1 )
    #locA = mc.spaceLocator( )[0]
    #locB = mc.spaceLocator( )[0]
    #mc.setAttr( locA+'.v', 0 )
    #mc.setAttr( locB+'.v', 0 )
    mc.connectAttr( posA+'.worldPosition', crv+'.controlPoints[0]' )
    mc.connectAttr( posB+'.worldPosition', crv+'.controlPoints[1]' )
    #mc.parent( locA, posA, r=1 )
    #mc.parent( locB, posB, r=1 )
    
    return crv


def rebuildCurve(crv, spans=10):
    #rebuildCurve -ch 1 -rpo 1 -rt 0 -end 1 -kr 0 -kcp 0 -kep 1 -kt 0 -s 10 -d 3 -tol 0.01 "curve1";
    newCrv = mc.rebuildCurve(crv, replaceOriginal=False, 
                        ch=True, 
                        degree=3,
                        rebuildType=0,  # 0=uniform
                        keepRange=0,    # 0=UVs[0-1]
                        keepEndPoints=True,
                        spans=spans,
                        endKnots=1,
                        keepControlPoints=0,
                        keepTangents=False, )[0]
    newCrv = '|'+mc.rename(newCrv, crv+'_rebuilt')
    return newCrv
                        

def createLocOnCurve(crv, uVal=0.5):
    paramLoc = mc.paramLocator( '{}.u[{}]'.format(crv, uVal) )
    return paramLoc



def cutOutMeshPiece(mesh, facesList, name):
    # format component list of the faces we want to cut out
    faceComps = [f.split('.')[-1] for f in facesList]
    # create Adam's invertComponentList node and pass it the list of face components
    invCompNode = mc.createNode('invertComponentList', n=name+'_invCompList')
    mc.setAttr(invCompNode+'.inComponents', len(faceComps), *faceComps, type='componentList')
    # create delete and mesh and make all the connections
    delNode = mc.createNode('deleteComponent', n=name+'_delComp')
    pieceMeshShape = mc.createNode('mesh', n=name+'_meshShape')
    pieceMeshTrans = mc.listRelatives(pieceMeshShape, p=True)[0]
    pieceMeshTrans = mc.rename(pieceMeshTrans, name+'_mesh')
    mc.connectAttr(mesh+'.outMesh', invCompNode+'.mesh', f=True)
    mc.connectAttr(mesh+'.outMesh', delNode+'.inputGeometry', f=True)
    mc.connectAttr(invCompNode+'.outComponents', delNode+'.deleteComponents', f=True)
    mc.connectAttr(delNode+'.outputGeometry', pieceMeshShape+'.inMesh', f=True)
    return pieceMeshTrans, pieceMeshShape


def saveRampProjTransforms(projNode=None):
    sel = mc.ls(sl=True)

    vT = mc.xform(projNode, q=True, t=True, ws=True)
    vR = mc.xform(projNode, q=True, ro=True, ws=True)
    vS = mc.xform(projNode, q=True, s=True, ws=True)
    
    pos = (round(vT[0],2),round(vT[1],2),round(vT[2],2))
    rot = (round(vR[0],2),round(vR[1],2),round(vR[2],2))
    sca = (round(vS[0],2),round(vS[1],2),round(vS[2],2))
    
    print [(pos), (rot), (sca)]


def createMultiplyDivide(inAttr1, inAttr2, operation, name):
    mdNode = mc.createNode('multiplyDivide', n=name)
    if '.' in inAttr1:
        mc.connectAttr(inAttr1, mdNode+'.input1X', f=True)
    else:
        mc.setAttr(mdNode+'.input1X', inAttr1)
    if '.' in inAttr2:
        mc.connectAttr(inAttr2, mdNode+'.input2X', f=True)
    else:
        mc.setAttr(mdNode+'.input2X', inAttr2)
    mc.setAttr(mdNode+'.operation', operation)


'''
##############################33         USAGE README              ##########################3
import maya.cmds as mc
import imp
qq = imp.load_source('dj', '/jobs/MAE/rdev_droneKaiju/maya/build/scripts/droneKaiju_sinew.py')

sinew = qq.Sinew(qq.data[0])
mesh = sinew.cutOutMeshPiece('body_geo', qq.data[0]['faces'])

#newCrv = mc.duplicate(sinew.curve)[0]
newCrv = qq.rebuildCurve(sinew.curve)
loc = qq.createLocOnCurve(newCrv)


'''


