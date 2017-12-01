import maya.cmds as mc
from pymel.core import mel 

import dnRig.utils.dnPoint2PointDeformer as p2p
import droneKaiju_sinew as dks
reload(dks)
import json
import sculpt_rig
from rig.tools.animShader.matcher import shader_wild_card_matcher
from rig.tools.animShader.shader_look import look
from rig.tools.animShader.shaders import shader_blinn
import maeRig as rig

armour_to_lattice = ["L_arm_upperArm_tentacle_small_006_geo", "L_arm_upperArm_panel_002_plate_002_001_deformed__composite_metalWhite_geo",
                    "R_arm_lowerArm_panel_002_001_deformed__composite_metalWhite_geo", ]

main_muscle_ctrls = ["L_arm_lowerArm_tentacle_big_001_mesh_sinew_ctrl", "L_arm_upperArm_tentacle_big_001_mesh_sinew_ctrl", "R_arm_lowerArm_tentacle_big_001_mesh_sinew_ctrl", "R_arm_upperArm_tentacle_big_001_mesh_sinew_ctrl", "R_pec_muscle_sinew_ctrl", "L_pec_muscle_sinew_ctrl", "L_lat_muscle_sinew_ctrl", "R_lat_muscle_sinew_ctrl", ]





def setup_muscle(lod):
    print '\nI"m watching you Alon'
    sinewMeshes = []
    groupParts = 'body_geo_skinClusterGroupParts'
    bodyShapeOrig = 'body_geoShapeOrig'
    intBodyGeoShape = dks.createIntBodyGeo(bodyShapeOrig, groupParts)
    masterCtrl = 'transformation_0_ctrl'

    # import data. list of dictionaries
    dataPath = "/jobs/MAE/rdev_droneKaiju/maya/build/scripts/droneKaiju_sinew_data.json"
    lattice_json = '/jobs/MAE/rdev_droneKaiju/maya/build/scenes/muscle_lattices_v001.json'

    with open(dataPath, "r") as f:
        data = json.load(f)
    # import tentacles to blendshape
    tentacleImport = mc.file('/jobs/MAE/rdev_droneKaiju/maya/build/scenes/cfx_sinew_tentacleBsTargets2.ma',
                        i=True, rnn=True)
    tentacleTransforms = mc.ls(tentacleImport, type='transform')
    tentacleGrp = tentacleTransforms[0]
    tentacleMeshes = tentacleTransforms[1:]
    #mc.parent(tentacleGrp, 'rig')

    # add sinew ctrl attrs to master control
    mc.addAttr(masterCtrl, ln='masterSinewCtrl', at='enum', enumName='----', k=True, )
    mc.setAttr(masterCtrl+'.masterSinewCtrl', l=True)   
    mc.addAttr(masterCtrl, ln='timeOffset', dv=2, k=True)
    mc.addAttr(masterCtrl, ln='deltaDistMult', dv=-.1, k=False)

    with open(lattice_json, "r") as f:
        latticeData = json.load(f)

    # controls display layer
    #dsl2 = mc.createDisplayLayer(n='secondaryCtrls_dsl', e=True)
    #mc.setAttr(dsl2+'.color', 31)

    #runThese = range(len(data))
    #for i in runThese[-5:]:
    for i in range(len(data)):
    #for i in range(8):
        # tentacles
        #print 'setting up ', data[i]['part']
        if data[i]['tentacle']:
            tentacleGeo = data[i]['tentacle'].replace('_mesh','_geo')
            tentacleThin = tentacleGeo.replace('_geo','_mesh_thin') 
            
            # create the whole tentacle deformation control setup
            #if mc.objExists(tentacleThin):
            cSinew = dks.Sinew(data[i], None)
            sinewMeshes.append(cSinew.mesh)
            #print 'blendshaped {} using {}'.format(cSinew.mesh, cSinew.bsNode)
            mc.connectAttr(masterCtrl+'.timeOffset', cSinew.timePMA+'.input1D[2]', f=True)

            # lattice setups for the arms
            mainNamePart = tentacleGeo.split('_tentacle')[0]
            for muscleLatticeDict in latticeData:
                # first time creating the lattice ctrl gets lattice muscle attributes 
                if muscleLatticeDict['name'] == mainNamePart and not mc.objExists(mainNamePart+'Base'):
                    latNodes = createLattice(muscleLatticeDict)
                    lattice = latNodes[0]
                    latticeGrp = latNodes[1]
                    clatGrp = createClusterOnLattice(lattice, 
                                                        muscleLatticeDict['clusterThese'], 
                                                        muscleLatticeDict['halfWeight'])
                    mc.parent([latticeGrp, clatGrp], 'rig', absolute=True)
                    mc.lattice(lattice, edit=True, geometry=cSinew.curve)
                    print 'set up lattice ', lattice
                # assigning wire curve to existing lattice
                elif muscleLatticeDict['name'] == mainNamePart:
                    #mc.editDisplayLayerMembers(dsl2, cSinew.ctrl)
                    lattice = mainNamePart + 'Lattice'
                    mc.lattice(lattice, edit=True, geometry=cSinew.curve)
                    print 'assigned {} curve to lattice {}'.format(cSinew.curve, lattice)
                    # add secondary ctrl to layer

                    for armourPiece in armour_to_lattice:
                        if muscleLatticeDict['name'] in armourPiece:
                            mc.lattice(lattice, edit=True, geometry=armourPiece)
                            print 'assigned {} geo to lattice {}'.format(armourPiece, lattice)


        # sinews
        elif data[i]['part']:
            # initialize/create the sinew class
            cSinew = dks.Sinew(data[i], intBodyGeoShape)
            sinewMeshes.append(cSinew.mesh)

            # add all sinew ctrls to secondary ctrl dsl, except for pecs and lats
            #if '_pec' not in cSinew.ctrl or '_lat' not in cSinew.ctrl:
            #    mc.editDisplayLayerMembers(dsl2, cSinew.ctrl)

            # connect master control to the individual sinews as they're created
            mc.connectAttr(masterCtrl+'.timeOffset', cSinew.timePMA+'.input1D[2]', f=True)
            # mult the power exponent
            cSinew.deltaMult = mc.createNode('multiplyDivide', n=cSinew.name+'_delta_MD')
            mc.setAttr(cSinew.deltaMult+'.operation', 1)        # multiply
            mc.connectAttr(cSinew.deltaDistMd+'.outputX', cSinew.deltaMult+'.input1X', f=True)
            mc.connectAttr(masterCtrl+'.deltaDistMult', cSinew.deltaMult+'.input2X', f=True)
            mc.connectAttr(cSinew.deltaMult+'.outputX', cSinew.deltaAnimCurve+'.input', f=True)
    


    # influence objects
    infObjs =  mc.ls('*_inf')
    setup_influence_objects(infObjs)
    for i in infObjs:
        mc.setAttr(i+'.v', 0)

    # inTransforms
    #add_in_transform()
    # Add inDeforms. NOT NEEDED BECAUSE WIRES ARE FRONT OF CHAIN DEFORMATION.
    #add_in_deform()
    
    create_and_apply_shaders_to_geo()
    #apply_shaders_to_sculptRig()
    #checkers_shader('body_sculpt')

    # cleanup
    mc.delete('targets_grp')
    mc.delete('importWrapCurves')

    print '\n-- Done droneKaiju_cfx\n'
    


def setup_influence_objects(infObjs):
    # Add in deforms to the input mesh
    import pymel.core as pm
    for obj in infObjs:
        pm.mel.dnLibConnectRigs_inDeform(obj)
    

def createDiagnosticLoc(name, inAttr):
    diagnosticLoc = mc.spaceLocator(n=name+'_diagnostic')[0]
    mc.connectAttr(inAttr, diagnosticLoc+'.ty')
    return diagnosticLoc


def createLattice(muscleLatticeDict):
    # create the lattice and position it
    latNodes = mc.lattice('body_geo', dv=[2,6,2], cp=True, oc=True, foc=True, 
                                            pos=muscleLatticeDict['pos'], 
                                            ro=muscleLatticeDict['orient'], 
                                            scale=muscleLatticeDict['scale'], 
                                            n=muscleLatticeDict['name'])

    ffd = mc.rename(latNodes[0],muscleLatticeDict['name']+'_ffd')
    lattice = latNodes[1]
    base = latNodes[2]
    mc.xform(base, t=muscleLatticeDict['pos'], ws=True)
    mc.xform(base, ro=muscleLatticeDict['orient'], ws=True)
    mc.xform(base, s=muscleLatticeDict['scale'], ws=True)
    latticeGrp = mc.listRelatives(lattice, p=True)[0]
    return lattice, latticeGrp


def qcreateClusterOnLattice(lat, latPoints, halfWeight):
    lattice = lat
    # add lattice name to the list of points
    for i,p in enumerate(latPoints):
        latPoints[i] = lat + p
    for i,p in enumerate(halfWeight):
        halfWeight[i] = lat + p
    # create the cluster on the required points
    clusterNodes = mc.cluster(latPoints, n=lattice+'_cluster')
    clusterNode = clusterNodes[0]
    clusterHandle = clusterNodes[1]
    # tweak the cluster weighting
    mc.percent(clusterNode, halfWeight, v=0.5)
    # orient the cluster to the lattice 
    clusterGrp = mc.group(clusterHandle, n=clusterHandle+'_grp')
    mc.xform(clusterGrp, cpc=True)
    mc.delete(mc.orientConstraint(lattice, clusterGrp, mo=False))
    mc.connectAttr(clusterGrp+'.worldInverseMatrix[0]', clusterNode+'.bindPreMatrix')
    # setup the cluster scale axis
    mc.connectAttr(clusterHandle+'.sx', clusterHandle+'.sz')
    mc.setAttr(clusterHandle+'.sy', l=True)
    return clusterGrp
    



def shotsculpt_setup():
    import pymel.core as pm
    # GAVIN SCRIPT
    # All the sculpt geos are done earlier in pinocchio
    # To get an updated list of things that need inDeform's (skinned geos), open
    # the latest anim300 rig and run this script.
    '''
    geos = []
    for child in mc.listRelatives('*:skinning_grp', ad=True, type='transform'):
        if child.endswith('_geo'):
            geo_shape = mc.listRelatives(child, s=True)
            if geo_shape:
                geos.append(child)
    print geos
    '''
    '''
    geos = [u'body_geo', u'L_Tooth_001_geo', u'L_Tooth_002_geo', u'L_Tooth_003_geo', u'L_Tooth_004_geo', u'L_Tooth_005_geo', u'L_Tooth_006_geo', u'L_Tooth_007_geo', u'L_Tooth_008_geo', u'L_Tooth_009_geo', u'L_Tooth_010_geo', u'L_Tooth_011_geo', u'L_Tooth_012_geo', u'L_Tooth_013_geo', u'L_Tooth_014_geo', u'L_Tooth_015_geo', u'L_Tooth_016_geo', u'L_Tooth_017_geo', u'L_Tooth_018_geo', u'L_Tooth_019_geo', u'L_Tooth_020_geo', u'L_Tooth_021_geo', u'L_Tooth_022_geo', u'L_Tooth_023_geo', u'L_Tooth_024_geo', u'L_Tooth_025_geo', u'L_Tooth_026_geo', u'L_Tooth_027_geo', u'L_Tooth_028_geo', u'L_Tooth_029_geo', u'L_Tooth_030_geo', u'L_Tooth_031_geo', u'L_Tooth_032_geo', u'L_Tooth_033_geo', u'L_Tooth_034_geo', u'L_Tooth_035_geo', u'L_Tooth_036_geo', u'L_Tooth_037_geo', u'L_Tooth_038_geo', u'L_Tooth_039_geo', u'L_Tooth_040_geo', u'L_Tooth_041_geo', u'L_Tooth_042_geo', u'L_Tooth_043_geo', u'L_Tooth_044_geo', u'L_Tooth_045_geo', u'L_Tooth_046_geo', u'L_Tooth_047_geo', u'L_Tooth_048_geo', u'L_Tooth_049_geo', u'L_Tooth_050_geo', u'L_Tooth_051_geo', u'L_Tooth_052_geo', u'L_Tooth_053_geo', u'L_Tooth_054_geo', u'L_Tooth_055_geo', u'L_Tooth_056_geo', u'L_Tooth_057_geo', u'L_Tooth_058_geo', u'L_Tooth_059_geo', u'L_Tooth_060_geo', u'L_Tooth_061_geo', u'L_Tooth_062_geo', u'L_Tooth_063_geo', u'L_Tooth_064_geo', u'L_Tooth_065_geo', u'L_Tooth_066_geo', u'L_Tooth_067_geo', u'L_Tooth_068_geo', u'L_Tooth_069_geo', u'L_Tooth_070_geo', u'L_Mouth_geo', u'L_head_helmet_panel_004_001_deformed__composite_metalWhite_geo', u'L_neck_tube_001_body_001__composite_metalBlackPipes_geo', u'L_neck_tube_001_body_002__composite_metalBlackPipes_geo', u'L_neck_tube_001_body_003__composite_metalBlackPipes_geo', u'L_neck_tube_001_body_006__composite_metalBlackPipes_geo', u'L_neck_tube_001_body_007__composite_metalBlackPipes_geo', u'L_neck_tube_002_body_004_deformed__composite_metalBlackPipes_geo', u'L_neck_tube_002_body_005_deformed__composite_metalBlackPipes_geo', u'L_neck_tube_002_body_006_deformed__composite_metalBlackPipes_geo', u'L_neck_tube_002_body_007_deformed__composite_metalBlackPipes_geo', u'L_neck_tube_003_body_001__composite_metalBlackPipes_geo', u'L_neck_tube_003_ring_001__composite_metalBlackPipes_geo', u'L_neck_tube_003_ring_002__composite_metalBlackPipes_geo', u'L_neck_tube_004_body_001__composite_metalBlackPipes_geo', u'L_neck_tube_004_piston_001__composite_metalBlackPipes_geo', u'L_neck_tube_005_body_001__composite_metalBlackPipes_geo', u'L_neck_tube_005_piston_001__composite_metalBlackPipes_geo', u'L_neck_tube_005_ring_001__composite_metalBlackPipes_geo', u'L_neck_tube_006_body_002__composite_metalBlackPipes_geo', u'L_neck_tube_006_body_002_ring__composite_metalBlackPipes_geo', u'R_neck_tube_001_body_001__composite_metalBlackPipes_geo', u'R_neck_tube_001_body_002__composite_metalBlackPipes_geo', u'R_neck_tube_001_body_003__composite_metalBlackPipes_geo', u'R_neck_tube_001_body_006__composite_metalBlackPipes_geo', u'R_neck_tube_001_body_007__composite_metalBlackPipes_geo', u'R_neck_tube_002_body_004_deformed__composite_metalBlackPipes_geo', u'R_neck_tube_002_body_005_deformed__composite_metalBlackPipes_geo', u'R_neck_tube_002_body_006_deformed__composite_metalBlackPipes_geo', u'R_neck_tube_002_body_007_deformed__composite_metalBlackPipes_geo', u'R_neck_tube_003_body_001__composite_metalBlackPipes_geo', u'R_neck_tube_003_ring_001__composite_metalBlackPipes_geo', u'R_neck_tube_003_ring_002__composite_metalBlackPipes_geo', u'R_neck_tube_004_body_001__composite_metalBlackPipes_geo', u'R_neck_tube_004_piston_001__composite_metalBlackPipes_geo', u'R_neck_tube_005_body_001__composite_metalBlackPipes_geo', u'R_neck_tube_005_piston_001__composite_metalBlackPipes_geo', u'R_neck_tube_005_ring_001__composite_metalBlackPipes_geo', u'R_neck_tube_006_body_002__composite_metalBlackPipes_geo', u'R_neck_tube_006_body_002_ring__composite_metalBlackPipes_geo', u'R_hand_tube_pipe_001_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_003_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_005_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_008_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_009_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_010_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_011_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_013_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_014_deformed__composite_metalBlack_geo', u'R_hand_tube_pipe_015_deformed__composite_metalBlack_geo', u'R_hand_tube_crossWire_001_deformed__composite_metalBlack_geo', u'R_hand_tube_crossWire_003_deformed__composite_metalBlack_geo', u'R_hand_tube_crossWire_005_deformed__composite_metalBlack_geo', u'R_Tooth_001_geo', u'R_Tooth_002_geo', u'R_Tooth_003_geo', u'R_Tooth_004_geo', u'R_Tooth_005_geo', u'R_Tooth_006_geo', u'R_Tooth_007_geo', u'R_Tooth_008_geo', u'R_Tooth_009_geo', u'R_Tooth_010_geo', u'R_Tooth_011_geo', u'R_Tooth_012_geo', u'R_Tooth_013_geo', u'R_Tooth_014_geo', u'R_Tooth_015_geo', u'R_Tooth_016_geo', u'R_Tooth_017_geo', u'R_Tooth_018_geo', u'R_Tooth_019_geo', u'R_Tooth_020_geo', u'R_Tooth_021_geo', u'R_Tooth_022_geo', u'R_Tooth_023_geo', u'R_Tooth_024_geo', u'R_Tooth_025_geo', u'R_Tooth_026_geo', u'R_Tooth_027_geo', u'R_Tooth_028_geo', u'R_Tooth_029_geo', u'R_Tooth_030_geo', u'R_Tooth_031_geo', u'R_Tooth_032_geo', u'R_Tooth_033_geo', u'R_Tooth_034_geo', u'R_Tooth_035_geo', u'R_Tooth_036_geo', u'R_Tooth_037_geo', u'R_Tooth_038_geo', u'R_Tooth_039_geo', u'R_Tooth_040_geo', u'R_Tooth_041_geo', u'R_Tooth_042_geo', u'R_Tooth_043_geo', u'R_Tooth_044_geo', u'R_Tooth_045_geo', u'R_Tooth_046_geo', u'R_Tooth_047_geo', u'R_Tooth_048_geo', u'R_Tooth_049_geo', u'R_Tooth_050_geo', u'R_Tooth_051_geo', u'R_Tooth_052_geo', u'R_Tooth_053_geo', u'R_Tooth_054_geo', u'R_Tooth_055_geo', u'R_Tooth_056_geo', u'R_Tooth_057_geo', u'R_Tooth_058_geo', u'R_Tooth_059_geo', u'R_Tooth_060_geo', u'R_Tooth_061_geo', u'R_Tooth_062_geo', u'R_Tooth_063_geo', u'R_Tooth_064_geo', u'R_Tooth_065_geo', u'R_Tooth_066_geo', u'R_Tooth_067_geo', u'R_Tooth_068_geo', u'R_Tooth_069_geo', u'R_Tooth_070_geo', u'R_Mouth_geo', u'R_head_helmet_panel_004_001_deformed__composite_metalWhite_geo', u'L_hand_tube_pipe_001_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_002_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_003_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_009_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_010_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_011_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_013_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_014_deformed__composite_metalBlack_geo', u'L_hand_tube_pipe_015_deformed__composite_metalBlack_geo', u'L_hand_tube_crossWire_001_deformed__composite_metalBlack_geo', u'L_hand_tube_crossWire_003_deformed__composite_metalBlack_geo', u'L_hand_tube_crossWire_005_deformed__composite_metalBlack_geo', u'L_leg_hip_int_block_001__composite_metalBlack_geo', u'L_leg_hip_int_block_002__composite_metalBlack_geo', u'L_leg_hip_int_block_003__composite_metalBlack_geo', u'L_leg_hip_int_ballBearing_001__composite_metalBlack_geo', u'L_leg_hip_int_ballBearing_002__composite_metalBlack_geo', u'L_leg_hip_crankshaft_cylinder_001__composite_metalBlack_geo', u'L_leg_hip_crankshaft_cylinder_002__composite_metalBlack_geo', u'L_leg_hip_crankshaft_cylinder_003__composite_metalBlack_geo', u'L_leg_hip_crankshaft_cylinder_004__composite_metalBlack_geo', u'L_leg_hip_crankshaft_cylinder_005__composite_metalBlack_geo', u'L_leg_hip_crankshaft_cylinder_006__composite_metalBlack_geo', u'L_leg_hip_tube_001__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_001__composite_metalBlack_geo', u'L_leg_hip_tubeCover_001__composite_metalBlackMid_geo', u'L_leg_hip_tube_002__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_002__composite_metalBlack_geo', u'L_leg_hip_tubeCover_002__composite_metalBlackMid_geo', u'L_leg_hip_tube_003__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_003__composite_metalBlack_geo', u'L_leg_hip_tubeCover_003__composite_metalBlackMid_geo', u'L_leg_hip_tube_004__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_004__composite_metalBlack_geo', u'L_leg_hip_tubeCover_004__composite_metalBlackMid_geo', u'L_leg_hip_tube_005__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_005__composite_metalBlack_geo', u'L_leg_hip_tubeCover_005__composite_metalBlackMid_geo', u'L_leg_hip_tube_006__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_006__composite_metalBlack_geo', u'L_leg_hip_tubeCover_006__composite_metalBlackMid_geo', u'L_leg_hip_tube_007__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCover_007__composite_metalBlackMid_geo', u'L_leg_hip_tubeCap_007__composite_metalBlack_geo', u'L_leg_hip_tube_008__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_008__composite_metalBlack_geo', u'L_leg_hip_tubeCover_008__composite_metalBlackMid_geo', u'L_leg_hip_tube_009__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCap_009__composite_metalBlack_geo', u'L_leg_hip_tubeCover_009__composite_metalBlackMid_geo', u'L_leg_hip_tube_010__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCover_010__composite_metalBlackMid_geo', u'L_leg_hip_tubeCap_010__composite_metalBlack_geo', u'L_leg_hip_tube_011__composite_metalBlackPipes_geo', u'L_leg_hip_tubeCover_011__composite_metalBlackMid_geo', u'L_leg_hip_tubeCap_011__composite_metalBlack_geo', u'R_leg_hip_int_block_001__composite_metalBlack_geo', u'R_leg_hip_int_block_002__composite_metalBlack_geo', u'R_leg_hip_int_block_003__composite_metalBlack_geo', u'R_leg_hip_int_ballBearing_001__composite_metalBlack_geo', u'R_leg_hip_int_ballBearing_002__composite_metalBlack_geo', u'R_leg_hip_crankshaft_cylinder_001__composite_metalBlack_geo', u'R_leg_hip_crankshaft_cylinder_002__composite_metalBlack_geo', u'R_leg_hip_crankshaft_cylinder_003__composite_metalBlack_geo', u'R_leg_hip_crankshaft_cylinder_004__composite_metalBlack_geo', u'R_leg_hip_crankshaft_cylinder_005__composite_metalBlack_geo', u'R_leg_hip_crankshaft_cylinder_006__composite_metalBlack_geo', u'R_leg_hip_tube_001__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_001__composite_metalBlack_geo', u'R_leg_hip_tubeCover_001__composite_metalBlackMid_geo', u'R_leg_hip_tube_002__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_002__composite_metalBlack_geo', u'R_leg_hip_tubeCover_002__composite_metalBlackMid_geo', u'R_leg_hip_tube_003__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_003__composite_metalBlack_geo', u'R_leg_hip_tubeCover_003__composite_metalBlackMid_geo', u'R_leg_hip_tube_004__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_004__composite_metalBlack_geo', u'R_leg_hip_tubeCover_004__composite_metalBlackMid_geo', u'R_leg_hip_tube_005__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_005__composite_metalBlack_geo', u'R_leg_hip_tubeCover_005__composite_metalBlackMid_geo', u'R_leg_hip_tube_006__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_006__composite_metalBlack_geo', u'R_leg_hip_tubeCover_006__composite_metalBlackMid_geo', u'R_leg_hip_tube_007__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCover_007__composite_metalBlackMid_geo', u'R_leg_hip_tubeCap_007__composite_metalBlack_geo', u'R_leg_hip_tube_008__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_008__composite_metalBlack_geo', u'R_leg_hip_tubeCover_008__composite_metalBlackMid_geo', u'R_leg_hip_tube_009__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCap_009__composite_metalBlack_geo', u'R_leg_hip_tubeCover_009__composite_metalBlackMid_geo', u'R_leg_hip_tube_010__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCover_010__composite_metalBlackMid_geo', u'R_leg_hip_tubeCap_010__composite_metalBlack_geo', u'R_leg_hip_tube_011__composite_metalBlackPipes_geo', u'R_leg_hip_tubeCover_011__composite_metalBlackMid_geo', u'R_leg_hip_tubeCap_011__composite_metalBlack_geo', u'R_leg_ankle_tentacle_big_001_geo', u'spine_004_tentacle_big_003_geo', u'spine_004_tentacle_big_004_geo', u'spine_004_tentacle_big_002_geo', u'spine_004_tentacle_big_001_geo', u'L_arm_upperArm_tentacle_big_002_geo', u'L_arm_upperArm_tentacle_big_001_geo', u'L_arm_lowerArm_tentacle_big_001_geo', u'L_arm_lowerArm_tentacle_big_002_geo', u'L_arm_upperArm_tentacle_big_003_geo', u'R_arm_upperArm_tentacle_big_002_geo', u'R_arm_upperArm_tentacle_big_001_geo', u'R_arm_lowerArm_tentacle_big_001_geo', u'R_arm_lowerArm_tentacle_big_003_geo', u'R_arm_lowerArm_tentacle_big_002_geo', u'L_leg_upperLeg_tentacle_big_001_geo', u'R_leg_upperLeg_tentacle_big_002_geo', u'L_leg_upperLeg_tentacle_big_002_geo', u'L_leg_lowerLeg_tentacle_big_003_geo', u'L_leg_lowerLeg_tentacle_big_001_geo', u'L_leg_lowerLeg_tentacle_big_002_geo', u'R_leg_lowerLeg_tentacle_big_002_geo']

    # add inDeform nodes to all the above
    for obj in geos:
        pm.mel.dnLibConnectRigs_inDeform(obj)
    print '\nDone adding in deforms'
    '''
    
    # influence objects
    infObjs =  mc.ls('*_inf')
    for i in infObjs:
        mc.setAttr(i+'.v', 0)
        mc.parent(i, 'jointHierarchy')

    # Constrain armour to joints. Temporary in place of inTransforms (which are broken).
    #constrain_geos()

    # shaders
    create_and_apply_shaders_to_geo()
    apply_shaders_to_sculptRig()
    #checkers_shader('body_sculpt')


def checkers_shader(geo):
    #create a shader
    material = mc.shadingNode("lambert",asShader=True, name='checkerMat')
    # a shading group
    shadingGroup = mc.sets(material, renderable=True, noSurfaceShader=True, empty=True, name='checkersSG')
    mc.connectAttr(material+'.outColor', shadingGroup+'.surfaceShader', f=True)
    # checkers
    checker = mc.shadingNode("checker",asTexture=True)
    p2d = mc.shadingNode("place2dTexture",asUtility=True)
    mc.connectAttr(p2d+'.outUV', checker+'.uv')
    mc.connectAttr(p2d+'.outUvFilterSize', checker+'.uvFilterSize')
    mc.connectAttr(checker+'.outColor', material+'.color', f=True)
    mc.setAttr(p2d+'.repeatU', 14)
    mc.setAttr(p2d+'.repeatV', 14)
    mc.setAttr(checker+'.color1', 0.9,0.9,0.9)
    mc.setAttr(checker+'.color2', 0.7,0.7,0.7)
    # assigning geo
    mc.sets(geo, e=True, forceElement=shadingGroup )

def create_and_apply_shaders_to_geo():

    # --------------------------------------------------------------------------
    # [ Add Shaders ]
    body_geos = ['body_geo', 'R_Mouth_geo', 'L_Mouth_geo', 'L_Teeth_grp', 'R_Teeth_grp']
    rig.assign_shaders(
        geos=body_geos, shader_name='skin_blinn', shader_type='blinn', 
        colour=[0.295, 0.45, 0.53])

    eye_geos = ['L_eyes_grp', 'R_eyes_grp']
    rig.assign_shaders(
        geos=eye_geos, shader_name='eyes_blinn', shader_type='blinn', 
        colour=[0.467, 0.953, 1], incandescence=[0.357, 0.357, 0.357])

    tentacle_geos = mc.ls('*tentacle*_geo')
    if tentacle_geos:
        rig.assign_shaders(
            geos=tentacle_geos, shader_name='tentacles_blinn', shader_type='blinn', 
            colour=[0.295, 0.45, 0.53])


    # [ Add Other Shaders ]
    body_geos = ['body_geo', 'R_Mouth_geo', 'L_Mouth_geo', 'L_Teeth_grp', 'R_Teeth_grp']
    for i in body_geos:
        if mc.objExists(i):
            mc.sets(i, e=True, forceElement='skin_blinnSG')    
    '''rig.assign_shaders(
        geos=body_geos, shader_name='skin_blinn', shader_type='blinn', 
        colour=[0.295, 0.45, 0.53])'''

    eye_geos = ['L_eyes_grp', 'R_eyes_grp']
    for i in eye_geos:
        if mc.objExists(i):
            mc.sets(i, e=True, forceElement='eyes_blinnSG')    
    '''rig.assign_shaders(
        geos=eye_geos, shader_name='eyes_blinn', shader_type='blinn', 
        colour=[0.467, 0.953, 1], incandescence=[0.357, 0.357, 0.357])'''

    tentacle_geos = mc.ls('*tentacle*_geo')
    for i in tentacle_geos:
        mc.sets(i, e=True, forceElement='tentacles_blinnSG')    


def apply_shaders_to_sculptRig():

    _shader = {
        "composite_metalBlackLight": {"color": [0.3, 0.3, 0.3]},
        "composite_metalBlack": {"color": [0.1, 0.1, 0.1]},
        "composite_metalWhite": {"color": [0.85, 0.85, 0.85]},
        "composite_metalCyan": {"color": [0.753, 0.85, 0.85]},
        "composite_metalBlackPipes": {"color": [0.300, 0.300, 0.300]},
        "composite_metalCyanDarken": {"color": [0.653, 0.75, 0.75]},
        "composite_metalBlackMid": {"color": [0.263, 0.251, 0.239]},
        "disney_instrMetalDarken1": {"color": [0.263, 0.251, 0.239]},
        "disney_instrMetal": {"color": [0.1, 0.1, 0.1]},
        "disney_incand_red": {"color": [0.804, 0.326, 0.326]},
        "disney_incand_cyan": {"color": [0.643, 0.922, 0.914]},
    }
    ''' Apply shader using material tags on meshes'''
    for mat, mat_val in _shader.iteritems():
        card = shader_wild_card_matcher.Wild_card_matcher('*{}*_sculpt'.format(mat))
        if not card.get_meshes():
            continue

        shader = shader_blinn.Blinn(mat)
        print shader

        for attr, val in mat_val.iteritems():
            setattr(shader, attr, val)
        jae_look = look.Look()
        jae_look.add_sublook([card], shader)
        jae_look.apply_look()


    # [ Add Other Shaders ]
    body_geos = ['body_sculpt', 'head_sculpt', 'R_Mouth_sculpt', 'L_Mouth_sculpt', 'L_Teeth_grp', 'R_Teeth_grp', 'neck_sculpt']
    body_geos = body_geos + mc.ls('*_Tooth_*_sculpt')
    body_geos = body_geos + mc.ls('flesh_*_sculpt')
    for i in body_geos:
        if mc.objExists(i):
            mc.sets(i, e=True, forceElement='skin_blinnSG')    
    '''rig.assign_shaders(
        geos=body_geos, shader_name='skin_blinn', shader_type='blinn', 
        colour=[0.295, 0.45, 0.53])'''

    eye_geos = ['L_eyes_grp', 'R_eyes_grp']
    for i in eye_geos:
        if mc.objExists(i):
            mc.sets(i, e=True, forceElement='eyes_blinnSG')    
    '''rig.assign_shaders(
        geos=eye_geos, shader_name='eyes_blinn', shader_type='blinn', 
        colour=[0.467, 0.953, 1], incandescence=[0.357, 0.357, 0.357])'''

    tentacle_geos = mc.ls('*tentacle*_sculpt')
    for i in tentacle_geos:
        mc.sets(i, e=True, forceElement='tentacles_blinnSG')    

    '''if tentacle_geos:
        rig.assign_shaders(
            geos=tentacle_geos, shader_name='tentacles_blinn', shader_type='blinn', 
            colour=[0.295, 0.45, 0.53])'''

    print 'Done applying look.\n'


def create_diagnostic_locators():
    moveX = 5
    # diagnostic
    blendOutAttr = cSinew.pairBlend + '.outTranslateX'
    diagnosticLoc = createDiagnosticLoc(cSinew.mesh, blendOutAttr)
    mc.setAttr(diagnosticLoc+'.tx', moveX)
    moveX += 5


def rename_sinew_ctrls():
    # HEY GAVIN!! sorry I couldn't leave the ctrls named "_gavin" 
    # <3 U
    gavins = mc.ls('*_gavin')
    ctrls = []
    for ctrl in gavins:
        ctrl = mc.rename(ctrl, ctrl.replace('_gavin', '_ctrl'))
        ctrls.append(ctrl)
    print 'added ctrls to the animControls set\n{}'.format(ctrls)
    mc.sets(ctrls, add="animControls")


def set_ctrls_priority():
    for ctrl in mc.sets("animControls", q=True):
        if ctrl not in main_muscle_ctrls and 'sinew' in ctrl:
            mc.setAttr(ctrl+'.priority', 1)



def create_sculpt_meshes():
    # sculpt on bodyGeo    
    print '\n sculpt body_geo'
    meshes = [f for f in mc.listRelatives('skinning_grp',ad=1,pa=1) if f.endswith('_geo')]

    for f in meshes:
        p = mc.listRelatives(f,p=1, pa=1)[0]
        xform = mc.createNode('transform', p=p)    
        mesh = mc.createNode('mesh', p=xform)
        xform = mc.rename(xform, f.replace('_geo','_sculpt'))
        
        inp = mc.listConnections(f+'.inMesh', sh=1, p=1)[0]
        mc.connectAttr(inp, xform+'.inMesh')
        mc.connectAttr(xform+'.outMesh', f+'.inMesh', f=1)
        mc.connectAttr('rig_preferences.cacheMode', f+'.visibility')


def constrain_geos():
    # Find geometry and joints to constrain geos.
    constrain_dict = rig.read_json(
        file_name='/jobs/MAE/rdev_droneKaiju/maya/build/data/droneKaiju_constrainGeo_v008.json')

    constrain_geos = constrain_dict['constrain']
    pivot_dict = constrain_dict['pivots']

    for geo, pivot in pivot_dict.iteritems():
        if mc.objExists(geo):
            mc.xform(geo, rp=pivot, sp=pivot)

    # JOINTS - CONSTRAIN DICT
    for jnt, geos in constrain_dict['constrain'].iteritems():
        for geo in geos:
            if mc.objExists(geo):
                mc.parentConstraint(jnt, geo, mo=True)
                mc.scaleConstraint(jnt, geo, mo=True)


def add_in_transform():
    # Find geometry and joints to add inTransform to.
    constrain_dict = rig.read_json(
        file_name='/jobs/MAE/rdev_droneKaiju/maya/build/data/droneKaiju_constrainGeo_v008.json')

    constrain_geos = constrain_dict['constrain']
    pivot_dict = constrain_dict['pivots']

    for geo, pivot in pivot_dict.iteritems():
        if mc.objExists(geo):
            mc.xform(geo, rp=pivot, sp=pivot)

    # JOINTS - CONSTRAIN DICT
    for jnt, geos in constrain_dict['constrain'].iteritems():
        for geo in geos:
            if mc.objExists(geo):
                mc.parentConstraint(jnt, geo, mo=True)
                mc.scaleConstraint(jnt, geo, mo=True)




    '''
    # IN TRANSFORMS - CONSTRAIN GEO LIST
    for geo in constrain_geos:
        if mc.objExists(geo):
            mel.dnLibConnectRigs_inTransform(geo)
    '''

    '''
    # IN TRANSFORMS - LIST HIERARCHY
    for transform in mc.listRelatives('importDamageArmourGeo', ad=True, type='transform'):
        if transform.endswith('_grp') or transform.endswith('_geo'):
            mel.dnLibConnectRigs_inTransform(transform)
    for transform in mc.listRelatives('importKaijuGeo', ad=True, type='transform'):
        if transform.endswith('_grp') or transform.endswith('_geo'):
            mel.dnLibConnectRigs_inTransform(transform)
    '''
    
'''
def add_in_deform():
    for transform in mc.listRelatives('skinning_grp', ad=True, type='transform'):
        if transform.endswith('_geo') or transform.endswith('_mesh'):
            mel.dnLibConnectRigs_inDeform(transform)
'''


##      FOR SAVING OUT LATTICE DATA:
# use: /jobs/MAE/rdev_droneKaiju/maya/build/scenes/cfx_muscle_latticePlacements.ma


import maya.cmds as mc
import json
lattice_file = '/jobs/MAE/rdev_droneKaiju/maya/build/scenes/muscle_lattices_v001.json'

def write_json( filepath, json_data):
    ''' write any data to json filepath
    '''
    with open(filepath, 'w') as f:
        return f.write(json.dumps(json_data, sort_keys=True, 
                    indent=4, separators=(',', ': ')))

def record_pivots():
    locs = []
    
    pivs = mc.listRelatives('lattices_grp', c=True)
    for piv in pivs:
        name = piv.replace('_lat_grp','') 
        pos = mc.xform(piv, q=True, ws=True, piv=True)[:3]
        orient = mc.xform(piv, q=True, ws=True, ro=True)
        lattice = name + '_lattice'
        scale = mc.xform(lattice, q=True, ws=True, s=True)
        if 'lowerArm' in name:
            clusterThese = [".pt[0:1][1][0]", ".pt[0][2][0]", ".pt[0:1][1][1]", ".pt[0][2][1]", ".pt[1][2][0]", ".pt[0][3][0:1]", ".pt[1][3][0]", ".pt[1][2:3][1]", ".pt[0:1][4][0]" ]
        else:
            clusterThese = [".pt[0:1][2:4][1]", ".pt[0:1][1:2][0]" ]

        locs.append(dict(name = name,
                        pos = pos,
                        orient = orient,
                        scale = scale,
                        clusterThese = clusterThese))
    write_json(lattice_file, locs)
    print locs
    
