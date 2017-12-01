import re

import maya.cmds as mc
import maya.mel as mm
from pymel.core import mel

import shaderTools
from rem_createFollicleOnMesh import rem_createFollicleOnMesh


def handScale():
	'''
	add a scaling control to the hands of a standard digidouble
	'''
	for s in ['L','R']:
		mc.addAttr(s + '_arm_mainIk_ctrl',ln='handScale',at='double',k=1,dv=1)
		#md = mc.createNode('multiplyDivide',n=s + '_handScale_MD')
		#mc.connectAttr(s + '_arm_mainIk_ctrl.handScale',md + '.input1X')
		for a in ['sx','sy','sz']:
			mc.connectAttr(s + '_arm_mainIk_ctrl.handScale',s + '_arm_wrist_env.' + a)
			mc.setAttr(s + '_arm_mainIkOffset_ctrl.' + a,k=1,l=0,cb=1)
			mc.connectAttr(s + '_arm_mainIk_ctrl.handScale',s + '_arm_mainIkOffset_ctrl.' + a)

		for jnt in mc.listRelatives(s + '_arm_wrist_env',ad=1,type='joint'):
			mc.setAttr(jnt + '.segmentScaleCompensate',0)


def headScale():
	'''
	add a scaling contorl to the head of a standard digi
	'''
	ctrl = 'head_mainIk_ctrl'
	mc.addAttr(ctrl,at='double',ln='headScale',k=1,min=0,dv=1)

	for targ in [u'eye_right_env', u'eye_left_env', u'head_6_env','head_headConstruction_null']:
		for a in ['sx','sy','sz']:
			if mc.objExists(targ + '.' + a)	:
				mc.connectAttr(ctrl + '.headScale',targ + '.' + a)

	mc.setAttr('head_jaw1_env.segmentScaleCompensate',0)


def shaders(jsonFile='',mode='import'):
	if mode == 'export':
		nodes = [
			node for node in mc.ls()
			if re.match(".*?(_geo$|_mesh$)", node)
		]
		data = shaderTools.getObjectCentric(target=nodes)
		shaderTools.write(jsonFile, data)

	elif mode == 'import':
		data = shaderTools.read(jsonFile)
		shaderTools.apply(data)


def dynamicAE():
	mc.sets(em=1,n='picker_flow')
	mc.sets(em=1,n='bipedAnimSpace_script')
	mc.addAttr('bipedAnimSpace_script','bipedAnimSpace_script',dt='string',ln='melEval')
	mc.setAttr("bipedAnimSpace_script.melEval","dnLibPicker; dnLibPicker_bipedAnimSpaceFrame(\"dynamicAe\")",type='string')
	mc.sets('bipedAnimSpace_script',n='bipedAnimSpace_frame')
	mc.sets('bipedAnimSpace_frame',add='picker_flow')
	mc.sets(em=1,n='bipedPicker_script')
	mc.addAttr('bipedPicker_script',dt='string',ln='melEval')
	mc.setAttr("bipedPicker_script.melEval","dnLibPicker; picker_archetypeMan(\"dynamicAe\")",type='string')
	mc.sets('bipedPicker_script',n='bipedPicker_frame')
	mc.sets('bipedPicker_frame',add='picker_flow')
	mc.sets('picker_flow',add='rig_column')


def exportSkel(targFile):
	"""
	Export the skeleton on build of the body rig so that it is available for costume rigs

	"""
	base = "base_global_transform"

	# Duplicate the base and reparent it at world level
	root = mc.duplicate(base)[0]
	root = mc.parent(root, world=True)
	root = mc.rename(root,base)

	# Delete broken ikHandles and constraints
	deleteMe = []
	for check in mc.listRelatives(root, ad=True, fullPath=True):

		if check.endswith('_ikHandle'):
			deleteMe.append(check)

		if check.endswith('_eff'):
			deleteMe.append(check)

		if mc.objectType(check) == 'pointConstraint':
			deleteMe.append(check)

		if mc.objectType(check) == 'orientConstraint':
			deleteMe.append(check)

		if mc.objectType(check) == 'aimConstraint':
			deleteMe.append(check)

		if mc.objectType(check) == 'parentConstraint':
			deleteMe.append(check)

	mc.delete(deleteMe)

	# Export to the file
	mc.select(root)
	mc.file(targFile, f=True, typ='mayaBinary', exportSelected=True)

	# Cleanup
	mc.delete(root)

	# Add an out transform for the base_global_transform
	mel.dnLibConnectRigs_outTransform("base_global_transform")


def importSkel(targFile):
	"""
	Imports the joint hierarchy from the given file.

	"""
	nodes = mc.file(
		targFile, i=True, type='mayaBinary', mergeNamespacesOnClash=False,
		renamingPrefix='envJonts', preserveReferences=True,
		loadReferenceDepth='all', returnNewNodes=True
	)

	# Disable the segmentScaleCompensate
	joints = mc.ls(nodes, type="joint")
	for joint in joints:
		try:
			mc.setAttr(joint + ".segmentScaleCompensate", 0)
		except RuntimeError:
			pass

	# Parent to the rig
	mc.parent('base_global_transform','jointHierarchy')

	# Add an in transform to the base_global_transform
	mel.dnLibConnectRigs_inTransform("base_global_transform")


def attachMeshControls(pfx, target_geo, attach_geo, ctrls, skin_mesh=None, scale_base="base_global_transform"):
	"""
	Attached mesh controls in the opposite way to createFrontOfChainDeform.
	The current target_geo will be duplicated an renamed to _foc_mesh.
	The foc_mesh is the one that should have the skeleton skin weights.

	The target_geo will then be skinned to the given controls.

	Attach_geo is the mesh that the controls will be constrained to. Ideally
	a lower resoultion mesh that matches the skinning of the _foc_mesh.

	If a list of skin_mesh geomtry is provided, this meshes will also be
	skinned to the controls. Use this as reference for weight painting.

	Run this function before skinning.

	"""
	if not skin_mesh:
		skin_mesh = []

	# Create the zero_jnt if it doesn't already exist
	zero_jnt = "zero_jnt"
	if not mc.objExists(zero_jnt):
		print ('ZERO JOINT CREATED.')
		mc.select(clear=True)
		zero = mc.createNode('joint',n=zero_jnt)
		mc.parent(zero,'base_global_transform')
	else:
		print ('ZERO JOINT EXISTS.')

	mc.setAttr(zero_jnt + ".inheritsTransform", False)

	# Duplicate each geo node and create blendshape the new mesh into the original
	for geo in target_geo:
		foc_mesh = mc.duplicate(geo, name=re.sub("_geo$", "_foc_mesh", geo))[0]
		mc.blendShape(foc_mesh, geo, name=re.sub("_geo$", "_focBlendShape", geo), weight=[0, 1])

		mc.hide(foc_mesh)

	# Mesh constrain the controls to the attach geo, connect the ctrl to the joint
	# and then skin the joints along with the zero_jnt to
	# the geometry and reference geometry.
	joints = [zero_jnt]

	# Mesh constrain the controls to the attach geo
	polygons = []
	for ctrl in ctrls:
		offset = re.sub("_ctrl$", "_offset", ctrl)
		offset_name = offset.rsplit("_", 1)[0]

		# Follicle constraint
		parent = mc.listRelatives(offset, parent=True)

		# Create a polygon plane to provide nice uvsfor the follicle.
		poly = mc.polyPlane( ch=0, o=1, w=0.01, h=0.01, sw=1, sh=1, n=offset_name + "_folliclePoly")[0]
		offset_position = mc.xform(offset, q=True, translation=True, ws=True)

		if parent:
			poly = mc.parent(poly, parent[0])[0]
		mc.xform(poly, translation=offset_position, ws=True)
		polygons.append(poly)

		# Create the follicle
		follicle = rem_createFollicleOnMesh([[0.5,0.5]], poly, side="", name=offset_name)[0]
		if parent:
			follicle = mc.parent(follicle, parent[0])[0]

		# Scale constrain the follicle to the scale_base
		mc.scaleConstraint(scale_base, follicle, maintainOffset=True)

		# Parent and scale constrain the offset to the follicle
		mc.parentConstraint(follicle, offset, maintainOffset=True)
		mc.scaleConstraint(follicle, offset, maintainOffset=True)

		# Hide them
		mc.hide([follicle, poly])

		# Connect the ctrl to the joint
		joint = re.sub("_ctrl$", "_jnt", ctrl)
		mc.connectAttr(ctrl + ".translate", joint + ".translate")
		mc.connectAttr(ctrl + ".rotate", joint + ".rotate")

		joints.append(joint)

	# Wrap the polygons to the attach_geo
	exisiting_wrap_nodes = set(mc.ls(type="wrap"))

	mc.select(polygons, attach_geo)
	mel.CreateWrap()

	# Find the newly created wrap nodes
	wrap_nodes = list(set(mc.ls(type="wrap")).difference(exisiting_wrap_nodes))

	# Configure each wrap node
	for wrap_node in wrap_nodes:
		mc.setAttr(wrap_node + ".exclusiveBind", True)
		mc.setAttr(wrap_node + ".falloffMode", 1)

	# Skin the geometry to the joints.
	# Also skin any reference geometry
	nodes_to_skin = target_geo[:]
	nodes_to_skin.extend(skin_mesh)

	for node in nodes_to_skin:
		# Create a new skin cluster to the controls
		mc.skinCluster(
			joints, node, toSelectedBones=True, name="{0}_skinCluster".format(node)
		)

	# Set up the bind pre matrix for each skin cluster the joint is connected to.
	for joint in joints:
		offset = re.sub("_jnt$", "_offset", joint)
		bindPreMatrixSkinCluster({joint: offset})


def bindPreMatrixSkinCluster(envDict):
	'''
	Stole this from The Gavmachine.

	Sets up a bindPreMatrix for an existing skinCluster. Pass it the ctrl/offset/object that controls the joint, this will plug it's worldMatrix
	into the skinCluster bindPreMatrix so that moving the offset wont deform the geometry.

	@inParam envDict - dictionary, key = joint, value = Object driving the joint, for instance a ctrl offset or follicle the joint is parented under.

	@procedure rig.bindPreMatrixSkinCluster({'tongue_001_env':'tongue_001_follicle', 'tongue_002_env':'tongue_002_follicle'})
	'''

	for env, offset in envDict.iteritems():
		if mc.objExists(env):
			if mc.objExists(offset):
				connections = mc.listConnections(env, p=1, t='skinCluster')

				if connections:
					for connection in connections:
						if '.matrix[' in connection:
							items = connection.split('.')
							skinCluster = items[0]
							index = re.findall('\d+', items[1])[0]

							if mc.isConnected(offset+'.worldInverseMatrix[0]', skinCluster+'.bindPreMatrix['+index+']'):
								print offset+'.worldInverseMatrix[0] is already connected to '+skinCluster+'.bindPreMatrix['+index+']'
							else:
								mc.connectAttr(offset+'.worldInverseMatrix[0]', skinCluster+'.bindPreMatrix['+index+']')
				else:
					print 'No skinCluster found for '+env+'.'
			else:
				print offset+' wasn\'t found, skipping '+env+'.'
		else:
			print env+' wasn\'t found, skipping joint.'


def extractHead(targ='body_geo',output='face_mesh'):
	'''
	using generic man as a ref, extract the head

	'''
	# prepend target geo
	v = mc.polyEvaluate(targ,v=1)

	faces = []
	# lod300
	if v == 33874:
		faces = [
			'.f[0:7407]', '.f[7428:7471]', '.f[7476:8171]', '.f[8208:8227]',
			'.f[8244:8427]', '.f[8432:8449]', '.f[8452:8453]', '.f[8457:8458]',
			'.f[8460:8461]', '.f[8465:8466]', '.f[8470:8471]', '.f[8480:8491]',
			'.f[8493:8494]', '.f[8497:8498]', '.f[8501:8502]', '.f[8504:8579]',
			'.f[8594:8603]', '.f[8608:8611]', '.f[8618:8619]', '.f[8628:8629]',
			'.f[8636:8651]', '.f[8668:8672]', '.f[8675:8680]', '.f[8683:8699]',
			'.f[8701:8702]', '.f[8704:8709]', '.f[8712:8715]', '.f[8717:8718]',
			'.f[8720:8843]', '.f[10164:10563]', '.f[10712:10831]', '.f[11152:11203]',
			'.f[11468:11823]', '.f[12076:12315]', '.f[16812:24343]', '.f[24364:24407]',
			'.f[24412:25107]', '.f[25144:25163]', '.f[25180:25363]', '.f[25368:25384]',
			'.f[25387:25388]', '.f[25391]', '.f[25394:25396]', '.f[25399]',
			'.f[25402:25403]', '.f[25405:25406]', '.f[25416:25427]', '.f[25430:25431]',
			'.f[25434:25435]', '.f[25438:25515]', '.f[25529:25530]', '.f[25532:25539]',
			'.f[25544:25547]', '.f[25553:25554]', '.f[25564]', '.f[25567]',
			'.f[25572:25587]', '.f[25604:25609]', '.f[25612:25617]', '.f[25620:25635]',
			'.f[25638:25644]', '.f[25647:25651]', '.f[25654:25779]', '.f[27100:27499]',
			'.f[27648:27767]', '.f[28088:28139]', '.f[28404:28759]', '.f[29012:29251]',
			'.f[33748:33871]'
		]
	# lod400
	elif v == 135490:
		faces = [u'.f[0:29631]', u'.f[29712:29887]', u'.f[29904:32687]', u'.f[32832:32911]', u'.f[32976:33711]', u'.f[33728:33887]', u'.f[33920:34319]', u'.f[34368:34415]', u'.f[34432:34447]', u'.f[34464:34479]', u'.f[34512:34527]', u'.f[34544:34607]', u'.f[34672:35375]', u'.f[40656:42255]', u'.f[42848:43327]', u'.f[44608:44815]', u'.f[45872:47295]', u'.f[48304:49263]', u'.f[67248:97375]', u'.f[97456:97631]', u'.f[97648:100431]', u'.f[100576:100655]', u'.f[100720:101455]', u'.f[101472:101631]', u'.f[101664:102063]', u'.f[102112:102159]', u'.f[102176:102191]', u'.f[102208:102223]', u'.f[102256:102271]', u'.f[102288:102351]', u'.f[102416:103119]', u'.f[108400:109999]', u'.f[110592:111071]', u'.f[112352:112559]', u'.f[113616:115039]', u'.f[116048:117007]', u'.f[134992:135487]']
		#polySmooth  -mth 0 -dv 1 -bnr 1 -c 1 -kb 1 -ksb 1 -khe 0 -kt 1 -kmb 1 -suv 1 -peh 0 -sl 1 -dpe 1 -ps 0.1 -ro 1 -ch 1 body_skn_geo;

	out = mc.duplicate(targ,n=output)[0]

	bodyFaces = [out + x for x in faces]
	mc.delete(bodyFaces)

	return(out)


def buildWireRig(curve,thickness=(0.25),bindParams=[0.0,1.0],jntSuffix = '_jnt',skinJoints=[],divisions=0,nurbs=0):
	'''
	Take an input nurbs curve and build a stretchy spline IK for it.

	At the end you probably want to wrap the input curve to the mesh

	assumes the last token of the nurbs curve is stripped off to form the naming basis for other stuff
	@author adnt
	@param curve: the target nurbs curve
	@param thickness: the thickness of the output bind surface mesh. Ideally this is close to the same thickness as your target render geo, but it doesn't really make a difference.
	@param bindParams: the number of spans on the bind mesh passed as a list of params between 0.0 and 1.0
	@param jntSuffix: the suffix of the output joints on the splineIK. I started with _env but this made those joints included in standard pinocchio skinClusters which was annoying
	@param skinJoints: a list of joints to skin the bind surface to.

	'''

	if(mc.pluginInfo('closestPointOnCurve',q=1,l=1)== 0):
		mc.loadPlugin('closestPointOnCurve')

	# TODO rebuild the input curve to 0-1 parametrization before starting?
	mainGrp = mc.group(em=1,n=curve.replace(curve.split('_')[-1],'rigGrp'))

	jnts = []
	cpos = mc.createNode('closestPointOnCurve')
	shape = mc.listRelatives(curve,s=1)[0]
	mc.connectAttr(shape + '.worldSpace[0]',cpos + '.inCurve')
	for i in range(len(mc.ls(curve + '.cv[*]',fl=1))):
		i = str(i)
		pos = mc.xform(curve + '.cv[' + i + ']',t=1,ws=1,q=1)
		mc.setAttr(cpos + '.inPosition',pos[0],pos[1],pos[2],type='double3')
		res = mc.getAttr(cpos + '.position')[0]

		# build a joint chain along the curve
		jnts.append(mc.joint(p=[res[0],res[1],res[2]],n=curve + 'Ik' + i + jntSuffix))
		if len(jnts) > 1:
			mc.joint(jnts[-2],e=1,oj='xyz',sao='yup')

	ik = mc.ikHandle(sol='ikSplineSolver',ccv=False,sj=jnts[0],ee=jnts[-1],c=curve,n=curve.replace(curve.split('_')[-1],'ikHandle'))
	mc.delete(cpos)

	# create a one degree curve that wraps the spline IK
	poci = mc.createNode('pointOnCurveInfo')
	mc.connectAttr(shape + '.worldSpace[0]', poci + '.inputCurve')
	mc.setAttr(poci + '.turnOnPercentage', 1)

	# create a 1 degree surface that will be used to skin the ikCurve
	curveKnots = []
	for param in bindParams:
		mc.setAttr(poci + '.parameter',param)
		curveKnots.append(mc.getAttr(poci + '.position')[0])
		#start = mc.xform(jnts[0],q=1,ws=1,t=1)
		#end = mc.xform(jnts[-1],q=1,ws=1,t=1)

	# take the 1 degree curve and offset curves on either side of it that can be lofted to create the bind surface
	bindCurve = mc.curve(d=1,p=curveKnots,n=curve.replace(curve.split('_')[-1],'bindCurve'))

	aCurve = mc.offsetCurve(bindCurve,ch=1, rn=0, cb=2, st=1, cl=1, cr =0, distance=thickness * 0.5, tol =0.01, sd=5,ugn=0)
	bCurve = mc.offsetCurve(bindCurve,ch=1, rn=0, cb=2, st=1, cl=1, cr =0, distance=thickness * -0.5, tol =0.01, sd=5,ugn=0)

	mc.delete(poci)
	bindLoft = mc.loft(aCurve,bCurve,n=curve.replace(curve.split('_')[-1],'bindSurface_nurbs'),ch=nurbs,po=0,d=1,u=1,c=0,ar=1,ss=1,rn=0,rsn=1)[0]
	bindSurface = mc.nurbsToPoly(bindLoft,n=curve.replace(curve.split('_')[-1],'bindSurface'), mnd=1,ch=0,f=3,pt=0,pc=200,chr=0.9,ft=0.01,mel=0.001,d=0.1,ut=1,un=3,vt=1,vn=3,uch=0,ucr=0,cht=0.2,es=0,ntr=0,mrt=0,uss=1)[0]
	# normalise UVs
	mc.polyNormalizeUV(bindSurface,normalizeType=1,preserveAspectRatio=0)
	#loft -ch 1 -u 1 -c 0 -ar 1 -d 1 -ss 1 -rn 0 -po 1 -rsn true "offsetNurbsCurve1_1" "offsetNurbsCurve2_1";

	if not nurbs:
		mc.delete(bindLoft)
	mc.delete(aCurve,bCurve,bindCurve)

	# calculate a stretchy solution

	# TODO connect this to global scale
	cInfo = mc.createNode('curveInfo',n=curve.replace(curve.split('_')[-1],'curveInfo'))
	mc.connectAttr(shape + '.worldSpace[0]', cInfo + '.inputCurve')
	length = mc.getAttr(cInfo + '.arcLength')

	md = mc.createNode('multiplyDivide',n=curve.replace(curve.split('_')[-1],'stretchyMult'))
	mc.setAttr(md + '.input2X',length)
	mc.connectAttr(cInfo + '.arcLength',md + '.input1X')
	mc.setAttr(md + '.operation',2)
	#globalScale = mc.createNode('multiplyDivide',n=curve.replace('_nurbs','_globalScaleMult'))
	for jnt in jnts:
		mc.connectAttr(md + '.outputX',jnt + '.sx')

	# skin the bindSurface automatically if we supply some joints
	if skinJoints:
		mc.skinCluster(bindSurface,skinJoints,tsb=1,n=bindSurface + '_skinCluster')

	# cleanup
	mc.parent(jnts[0],curve,ik[0],bindSurface,mainGrp)

	# wrap input curve to mesh
	wrap = mc.duplicate(bindSurface,n=bindSurface.replace('_bindSurface','_wrapSurface'))[0]
	mc.select(wrap,bindSurface,r=1)
	deformer = mel.dnPoint2Point()
	mc.polySmooth(wrap,dv=divisions,kb=0)

	mc.select(curve,r=1)
	#mc.select(bindSurface,add=1)
	mc.select(wrap,add=1)
	mm.eval('CreateWrap()')

	return(mainGrp)


def setControlColor(ctrl,color,primary=1):
	# red = 13
	for shape in mc.listRelatives(ctrl,s=1):
		con = mc.listConnections(shape + '.overrideColor',p=1,s=1,d=0)
		if con:
			mc.disconnectAttr(con[0],shape + '.overrideColor')

		mc.setAttr(shape + '.overrideColor',color)

	if (primary):
		mc.setAttr(ctrl + '.priority',0)



##############################################################################33
##############################################################################33
##############################################################################33
## gtRig

#  Author:     Gavin Thomas
#  Email:      gmt@dneg.com   gavin_thomas_@hotmail.co.uk
#  Version:    2.0
#  Date:       25/08/2015
#  Description:   Contains rigging utils for day to day rigging tasks to make my life easier!
#  Documentation:  
#  Requires:      
#  Notes:
#  History:
#  To Do:
#
#  import sys
#  sys.path.append('/hosts/katevale/user_data/scripts/gtRig/')
#


import maya.cmds as mc
import maya.mel as mm
import pymel.core as pm
import maya.OpenMaya as om

import sys
import re

import itertools
import modelling.shader_grabber as shader_grabber


#  Order of Categories
#  -------------------

#  [ JOINTS ]
#  [ IK HANDLES ]
#  [ SKINNING ]
#  [ DNWIMP ]

#  [ DEFORMERS ]
#  [ BLENDSHAPES ]
#  [ CONSTRAINTS ]

#  [ LOCATORS ]
#  [ TRANSFORMS ]
#  [ NODES ]
#  [ FOLLICLES ]
#  [ RIBBON ]

#  [ GEOMETRY ]
#  [ SURFACE ]
#  [ CURVES ]
#  [ SHADERS ]

#  [ CONTROLS ]
#  [ ATTRIBUTES ]

#  [ ANIMATION ]
#  [ CLOTH ]
#  [ SHOTSCULPT ]

#  [ FACE RIG ]
#  [ MUSCLES ]
#  [ MODULES ]
#  [ PYTHON ]

#  [ OTHER ]




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#----------------- ========[ JOINTS ]======== ---------------#
#------------------------------------------------------------#

def exportSkel(targFile, root='', removeJoints=[], removeRoot=0, renameRoot='', renameBaseGlobalTransform=0):
    '''
    Exports a skeleton. Mostly used for costume rigs, we export a clean skeleton from the bodyRig and import it for the costume. The costume doesn't need to get built with
    controls or an identical rig. The joints will follow the bodyRig joints when the rigs are connected.

    @param targFile - string, file to export skeleton to
    @param root - string, root of joints. If none given, it will find the root by itself!
    @param removeJoints - list, joints to remove before exporting
    @param removeRoot - int, removes the root from the export (parents all children under world and exports that)
    @param renameRoot - string, renames root to given name
    @param renameBaseGlobalTransform - int, if on it renames the base_global_transform to base_global_temp for parenting purposes

    @procedure rig.exportSkel('/jobs/INVERT/rdev_gentlemansfish/maya/scenes/gentlemans_envJoints_v001.mb')
    '''
    env = ''
    if not root:
        if mc.objExists('jointHierarchy'):
            root = mc.listRelatives('base_global_transform', c=1, type='joint')[0]
        else:
            root = mc.listRelatives('base_envJoints_null', c=1, type='joint')[0]

    if mc.objExists(root):
        #Duplicate joint chain, reparent to world.
        env = mc.duplicate(root)[0]
        env = mc.parent(env, w=1)
        env = mc.rename(env, root)
    else:
        mc.error('Root joint '+root+' does not exist!')

    #List all decendants of joint chain and add anything to a delete list if it's a constraint or ikHandle.
    deleteMe = []
    for check in mc.listRelatives(env,ad=1,f=1):        
        if check.endswith('_cluster') or check.endswith('_clusterHandle') or mc.objectType(check) == 'clusterHandle' or check.endswith('_curve') or check.endswith('_ikHandle') or check.endswith('_eff') or mc.objectType(check) == 'pointConstraint' or mc.objectType(check) == 'orientConstraint' or mc.objectType(check) == 'aimConstraint' or mc.objectType(check) == 'parentConstraint' or mc.objectType(check) == 'scaleConstraint' or mc.objectType(check) == 'poleVectorConstraint':
            deleteMe.append(check)  
        else:
            mc.setAttr(check+'.v', 1)  


    mc.setAttr(env+'.v', 1)  

    #Delete everything in the delete list.
    mc.delete(deleteMe)

    if removeJoints:
        removeObjs = []
        for obj in removeJoints:
            objs = mc.ls(obj, l=1)
            if len(objs) > 0:
                for o in objs:
                    removeObjs.append(o)

        joints = []
        rootLen = len(root)
        for joint in removeObjs:
            returnList = mc.ls(joint, l=1)
            for obj in returnList:
                #print obj
                if obj[0:(rootLen+1)] == '|'+root:
                    joints.append(obj)
                    print 'Deleted '+obj

        #print joints
        if len(joints) > 0:
            mc.delete(joints)

    if renameRoot:
        env = mc.rename(env, renameRoot)

    if renameBaseGlobalTransform:
        for check in mc.listRelatives(env,ad=1,f=1):  
            if check.endswith('base_global_transform'):
                mc.rename(check, 'base_global_temp')


    for joint in mc.listRelatives(env,ad=1,f=1):
        attrsCB = mc.listAttr(joint, cb=1)
        attrsL= mc.listAttr(joint, l=1)

        if attrsCB:
            unlockAttr(obj=joint, attrs=attrsCB)

        if attrsL:
            unlockAttr(obj=joint, attrs=attrsL)


    #Export the file and then delete the duplicate joints.
    if removeRoot:
        children = []
        for child in mc.listRelatives(env, c=1, f=1):
            obj = mc.parent(child, w=1)[0]
            children.append(obj)

        mc.select(children, r=1)
    else:    
        mc.select(env, r=1)

    mc.file(targFile, f=1, type='mayaBinary', es=1)
    mc.delete(env)

    if removeRoot:
        mc.delete(children)

    print 'Skeleton successfully exported!!\n'+targFile





def importSkel(targFile='', root='base_global_transform', parent='jointHierarchy'):
    '''
    Imports a skeleton. Mostly used for costume rigs, we export a clean skeleton from the bodyRig and import it for the costume. The costume doesn't need to get built with
    controls or an identical rig. The joints will follow the bodyRig joints when the rigs are connected.

    @inParam targFile - string, file to export skeleton to
    @inParam root - string, root of joints to parent under joints null. Usually base_global_transform or spine_pelvis_env which is the default.
    @inParam parent - string, parent of root

    @procedure rig.importSkel(targFile='/jobs/INVERT/rdev_gentlemansFish/maya/scenes/models/gentlemans_envJoints_v001.mb', parent='base_global_transform')
    '''
    #Import the file.
    if mc.file(targFile, q=1, ex=1):
        mc.file(targFile, i=1)
    else:
        print targFile+' does not exist!'
    
    if mc.objExists(root):
        #Parent the root under the joints null.
        if mc.objExists(parent):
            if mc.listRelatives(root, p=1)[0] != parent:
                mc.parent(root, parent)
        else:
            print parent+' does not exist!! @importSkel'
            mc.parent(root, 'jointHierarchy')
    else:
        print 'Root joint not found - '+root

    print 'Skeleton successfully imported!!\n'+targFile




def returnAllDescendants(obj='', typesToRemove=[], objToRemove=[]):
    '''
    Returns a list of all descendants for given object. Useful for jointHierarchy adding to a set for example.

    @inParam obj - string, object to find all descendants for
    @inParam typesToRemove - list, object types to remove from children e.g. cluster, curve
    @inParam objToRemove - list, specific obj to remove

    @procedure rig.returnAllDescendants(obj='jointHierarchy', typesToRemove=['cluster', 'curve', 'geo', 'mesh', 'nurbs', 'ikHandle', 'eff', 'pointConstraint', 'orientConstraint', 'aimConstraint', 'parentConstraint', 'scaleConstraint', 'poleVectorConstraint'], objToRemove=['*_000_env'])[0]
    
    @returns returnList and removedItems
    '''
    #List all decendants.
    objs = mc.listRelatives(obj, ad=1, s=0, f=1)
    removeList = []
    for child in objs:
        if typesToRemove:
            if 'cluster' in typesToRemove:
                if child.endswith('_cluster') or child.endswith('_clusterHandle') or mc.objectType(child) == 'clusterHandle':
                    removeList.append(child)
            if 'curve' in typesToRemove:
                if child.endswith('_curve'):
                    removeList.append(child)
            if 'ikHandle' in typesToRemove:
                if child.endswith('_ikHandle'):
                    removeList.append(child)
            if 'eff' in typesToRemove:
                if child.endswith('_eff'):
                    removeList.append(child)
            if 'pointConstraint' in typesToRemove:
                if mc.objectType(child) == 'pointConstraint':
                    removeList.append(child)
            if 'orientConstraint' in typesToRemove:
                if mc.objectType(child) == 'orientConstraint':
                    removeList.append(child)
            if 'aimConstraint' in typesToRemove:
                if mc.objectType(child) == 'aimConstraint':
                    removeList.append(child)
            if 'parentConstraint' in typesToRemove:
                if mc.objectType(child) == 'parentConstraint':
                    removeList.append(child)                
            if 'scaleConstraint' in typesToRemove:
                if mc.objectType(child) == 'scaleConstraint':
                    removeList.append(child)
            if 'poleVectorConstraint' in typesToRemove:
                if mc.objectType(child) == 'poleVectorConstraint':
                    removeList.append(child)
            if 'geo' in typesToRemove:
                if child.endswith('_geo'):
                    removeList.append(child)
            if 'mesh' in typesToRemove:
                if child.endswith('_mesh'):
                    removeList.append(child)
            if 'nurbs' in typesToRemove:
                if child.endswith('_nurbs'):
                    removeList.append(child)

    if objToRemove:
        for o in objToRemove:
            objects = mc.ls(o, l=1)
            if objects:
                for ob in objects:
                    removeList.append(ob)



    returnList = [o for o in objs if o not in removeList]
    return [returnList, removeList]



def stripObject(env=''):
    '''
    Strip object of constraints, ikHandles.

    @inParam env - string, joint root to strip all descendants

    @procedure rig.stripObject(env='L_foreleg_hip_env')
    '''
    #List all decendants of the joint chain and add anything to a delete list if it's a constraint or ikHandle.
    deleteMe = []
    for check in mc.listRelatives(env,ad=1,f=1):        
        if check.endswith('_ikHandle') or check.endswith('_eff') or mc.objectType(check) == 'pointConstraint' or mc.objectType(check) == 'orientConstraint' or mc.objectType(check) == 'aimConstraint' or mc.objectType(check) == 'parentConstraint' or mc.objectType(check) == 'scaleConstraint':
            deleteMe.append(check)                                                                        

    #Delete everything in the delete list.
    mc.delete(deleteMe)



def copyRigGuide(guides=[], guideOrig='', guideNew='', side=''):
    '''
    Copies translation, rotation, scale and radius values from one guide to another. Useful if you've got 6 butterfly legs for example.

    @inParam guides - list, which guide joints to copy
    @inParam guideOrig - string, original guide to copy from
    @inParam guideNew - string, new guide to copy to
    @inParam side - string, side of guide L_, R_ or nothing for mid

    @procedure rig.copyRigGuide(guides=['hip', 'knee', 'ankle', 'foot', 'toe', 'heel', 'toeRoll', 'soleInner', 'soleOuter'], guideOrig='leg', guideNew='foreleg', side='L_')
    '''
    for guide in guides:
        guideOrig = side+guideOrig+'_'+guide+'_rigGuide'
        guideNew = side+guideNew+'_'+guide+'_rigGuide'

        trans = mc.xform(guideOrig, q=1, ws=1, t=1)
        rot = mc.xform(guideOrig, q=1, ws=1, ro=1)
        rad = mc.getAttr(guideOrig+'.radius')

        mc.move(trans[0], trans[1], trans[2], guideNew, ws=1)
        mc.rotate(rot[0], rot[1], rot[2], guideNew, ws=1)
        mc.setAttr(guideNew+'.radius', rad)



def createJoint(name='joint', snapToObj='', pos=[0,0,0], rot=[0,0,0], radius=1.0, parent='', ctrl='', const='parentConstraint', scaleConst=0, v=1):
    '''
    Creates joints! You can pass it an object so it will snap to that position and rotation. Alternatively give it a pos and rot value. Parent the joint under the given 
    parent flag and constrain or parent (cons) under the given ctrl or object given.

    @inParam name - string, name of joint
    @inParam snapToObj - string, object to snap joint to and copy rotation values. If object is not given, this proc will use the pos and rot flags
    @inParam pos - list, position values to move joint to. If object given, this will ignored
    @inParam rot - list, rotation values to rotate joint. If object given, this will ignored
    @inParam radius - float, radius of joint
    @inParam parent - string, parent object to parent the joint under
    @inParam ctrl - string, object or ctrl to control the joint. Used with const flag.
    @inParam const - string, constrain or parent the joint to given ctrl. Options are parent, point, orient (constaint).
    @inParam scaleConst - string, if 0, the joint will not be scale constrained to the ctrl, if it's 1 it will.
    @inParam v - int, visibility of joint 

    @procedure rig.createJoint(name=env, snapToObj=loc, radius=0.25, parent=parent, ctrl=ctrl, const='parentConstraint')
    '''
    if mc.objExists(name):
        mc.error(name+' already exists. @inParam name: createJoint')
        name = name+'DUPLICATENAME'

    mc.select(cl=1)
    joint = mc.joint(n=name, p=pos)
    mc.setAttr(joint+'.radius', radius)
    mc.rotate(rot[0], rot[1], rot[2], joint, r=1)

    if parent:
        if mc.objExists(parent):
            mc.parent(joint, parent)
        else:
            print parent+' does not exist!'

    if snapToObj:
        if mc.objExists(snapToObj):
            if mc.objectType(snapToObj) == 'joint':
                if parent == snapToObj:
                    mc.setAttr(joint+'.jointOrientX', 0)  
                    mc.setAttr(joint+'.jointOrientY', 0) 
                    mc.setAttr(joint+'.jointOrientZ', 0)  
                else:
                    jointOrient = [mc.getAttr(snapToObj+'.jointOrientX'), mc.getAttr(snapToObj+'.jointOrientY'), mc.getAttr(snapToObj+'.jointOrientZ')]
                    mc.setAttr(joint+'.jointOrientX', jointOrient[0])
                    mc.setAttr(joint+'.jointOrientY', jointOrient[1])
                    mc.setAttr(joint+'.jointOrientZ', jointOrient[2])
            
            if '.vtx[' in snapToObj:
                vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                mc.move(vtxPos[0], vtxPos[1], vtxPos[2], joint, r=1)
            else:
                mc.delete(mc.parentConstraint(snapToObj, joint)[0])
        else:
            print snapToObj+' does not exist!'+joint+' not snapped to '+snapToObj


    if ctrl:
        if mc.objExists(ctrl):
            if const == 'parentConstraint':
                mc.parentConstraint(ctrl, joint, mo=1)
            elif const == 'pointConstraint':
                mc.pointConstraint(ctrl, joint, mo=1)
            elif const == 'orientConstraint':
                mc.orientConstraint(ctrl, joint, mo=1)

            if scaleConst == 1:
                mc.scaleConstraint(ctrl, joint, mo=1)
        else:
            print ctrl+' does not exist! Nothing constrained to joint.'

    mc.setAttr(joint+'.v', v)

    return joint



def createPlacementJoints(rootLoc='loc', parent='spine_5_env', consToEnv=1):
    '''
    Create joints from placement locators. Will create a joint with the same name, position and rotation as the locator. Works with locator hierarchy,
    only pass the root loc name. It will skip creating joints for locators with AIM or root in the name (Sub Ultron aim constraint pistons).

    @inParam rootLoc - list, locator to create joints from. If locators are in a hierarchy, just pass the root loc
    @inParam parent - string, which object the root joint will be parented under
    @consToEnv consToEnv - int, constrain locator to new joint or not (0,1)

    @procedure rig.createPlacementJoints(side+'_neckPiston_001_loc', 'spine_5_env', consToEnv=1)
    '''
    locs = []
    envs = []
    locChildren = mc.listRelatives(rootLoc, ad=1, type='transform')
    if locChildren:
        locs.extend(locChildren)
    locs.append(rootLoc)

    for loc in locs:
        if loc.endswith('_loc') and 'AIM' not in loc and 'root' not in loc:
            locPos = mc.xform(loc, q=1, t=1, ws=1)
            locRot = mc.xform(loc, q=1, ro=1, ws=1)

            mc.select(cl=1)
            env = mc.joint(n=loc.replace('_loc', '_env'), p=(locPos[0], locPos[1], locPos[2]))
            mc.rotate(locRot[0], locRot[1], locRot[2], env, r=1)

            envs.append(env)    

    for env in envs:
        loc = env.replace('_env', '_loc')

        parentEnv = mc.listRelatives(loc, p=1)[0].replace('_loc', '_env')
        if loc == rootLoc:
            parentEnv = parent
        elif 'root_loc' in mc.listRelatives(loc, p=1)[0]:
            #If there is another root locator in the hierarchy.
            parentEnv = mc.listRelatives(loc.replace('_loc', '_root_loc'), p=1)[0].replace('_loc', '_env')
        mc.parent(env, parentEnv)

        if consToEnv == 1:
            mc.parentConstraint(loc, env, mo=1)
        elif consToEnv == 2:
            mc.orientConstraint(loc, env, mo=1)

    envs.reverse()
    return envs



def disconnectLockInfluenceWeights(envs=[]):
    '''
    When rigs are connected, the joints lockInfluenceWeights are connected. This disconnects them.

    @inParam envs - list, which joints to disconnect

    @procedure rig.disconnectLockInfluenceWeights()
    '''
    #If no joints given, list all joints.
    if not envs:
        envs = mc.ls('*_env')
    
    for env in envs:
        source = []

        #For each joint, find the source connection to the joint if the attribue lockInfluenceWeights exist.
        if mc.attributeQuery('lockInfluenceWeights', node=env, ex=1):
            source = mc.listConnections(env+'.lockInfluenceWeights', d=0, s=1)

        #If connection exists, disconnect it.
        if source:
            mc.disconnectAttr(source[0]+'.lockInfluenceWeights', env+'.lockInfluenceWeights')




def setDisplayType(objs=[], dispType=0):
    '''
    Sets the display type of given objects. Useful for example with the costume rig joints as they all get set to reference and I want to select them so switch to normal.

    @inParam objs - list, objects to set the display type
    @inParam dispType - int, 0:normal, 1:template, 2:reference

    @procedure rig.setDisplayType(objs=['*_env'], dispType=0)
    '''
    if objs:
        objects = []
        for obj in objs:
            geoList = mc.ls(obj)
            for geo in geoList:
                objects.append(geo)

        for obj in objects:
            mc.setAttr(obj+'.overrideDisplayType', dispType)
    else:
        print 'No objects given. @inParam objs - setDisplayType()'




def setupRadialAimJoints(joints=[], centerObj='', parent='', ctrl=''):
    '''
        Useful for eyelid joints to follow the curvature of an eyeball. Given a center joint (center of eyeball), the joints will be rotated from the center pivot by a center 
        joint created for each joint, using an ikSC created. You can use the driver flag to drive the locator, e.g. a curve or ctrl

        @inParam joints - list, joints to setup radial aim for
        @inParam centerObj - string, define center position the joints will rotate from and aim towards. Pass it an object at the center of the eye for example
        @inParam parent - string, parent of centerJoints created. If none given, it will find the parent of joint it creates a center joint for
        @inParam ctrl - list, object that will control the ikSC created

        @procedure rig.setupRadialAimJoints(joints=[joints], centerObj=eyeballLoc, parent=rigGroup, ctrl=ctrl)
    '''
    centerJoints = []
    locs = []
    for joint in joints:
        if parent:
            if not mc.objExists(parent):
                print parent+' does not exist! @inParam parent'
        else:
            parent = mc.listRelatives(joint, p=1)[0]

        #Create a joint and snap it to the center joint
        centerJoint = createJoint(name=joint.replace('_env', 'Center_jnt'), snapToObj=centerObj, radius=0.2, parent=parent)
        mc.parent(joint, centerJoint)
        centerJoints.append(centerJoint)

        #Orient the center joint to aim at the child
        mc.joint(centerJoint, e=1, oj='xyz', secondaryAxisOrient='yup', ch=1, zso=1)

        #Create ikSC.
        createIk(name=joint.replace('_env', '_ik'), solver='ikSCsolver', startJoint=centerJoint, endEffector=joint, parent=parent, ctrl=ctrl, consType='point', v=0)
        mc.orientConstraint(ctrl, joint, mo=1)

    return centerJoints



def jointHierarchy(joints=[]):
    '''
    Selects and returns all descendants of a joint hierarchy but only joints, no constraints. Useful for adding influences to a skinCluster. Either give joint name or works on selection.

    @inParam joints - list, list of joints to select descendants for.
    
    @procedure rig.jointHierarchy(joints=[])
    '''
    if not joints:
        objects = mc.ls(sl=1)
        for obj in objects:
            if mc.objectType(obj) == 'joint':
                joints.append(obj)
            else:
                print obj+' not a joint!'

    allJoints = joints
    for joint in joints:
        children = mc.listRelatives(joint, ad=1, type='transform')
        for child in children:
            if mc.objectType(child) == 'joint':
                allJoints.append(child)

    if allJoints:
        mc.select(allJoints, r=1)
        return allJoints
    else:
        print 'No joints selected!!'
        
def addStretchyClav(side, mid = True, tip = True):
    '''
    Adds mid and tip joints to the clavicle.

    @inParam side - string, side
    @inParam mid - boolean, mid joint creation
    @inParam tip - boolean, tip joint creation

    @procedure rig.addStretchyClav(side='L')
    '''    
    if mid == True:
        midClavJnt = N.Namer(side = side, mod=None, desc='clavicleMid', func='env', idx=1)
        mc.createNode ('joint', n= midClavJnt.name, p=side+'_arm_clavicle_env')
        #Label the joint
        mc.setAttr (midClavJnt.name+'.type', 18)
        mc.setAttr (midClavJnt.name+'.otherType', midClavJnt.desc+'_%03d'%(midClavJnt.idx), type='string')    
        if midClavJnt.side == 'L':
            mc.setAttr (midClavJnt.name+'.side', 1)    
        if midClavJnt.side == 'R':
            mc.setAttr (midClavJnt.name+'.side', 2)
        #Constraint to mid point of clavical length
        mc.pointConstraint (side+'_arm_clavicle_env', side+'_arm_shoulder_env', midClavJnt.name)
    if tip == True:
        tipClavJnt = N.Namer(side = side, mod=None, desc='clavicleTip', func='env', idx=1)
        mc.createNode ('joint', n= tipClavJnt.name, p=side+'_arm_clavicle_env')
        #Label the joint
        mc.setAttr (tipClavJnt.name+'.type', 18)
        mc.setAttr (tipClavJnt.name+'.otherType', tipClavJnt.desc+'_%03d'%(tipClavJnt.idx), type='string')    
        if tipClavJnt.side == 'L':
            mc.setAttr (midClavJnt.name+'.side', 1)    
        if tipClavJnt.side == 'R':
            mc.setAttr (midClavJnt.name+'.side', 2)
        #Constraint to mid point of clavical length
        mc.pointConstraint (side+'_arm_shoulder_env', tipClavJnt.name)



#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#--------------- ========[ IK HANDLES ]======== -------------#
#------------------------------------------------------------#


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


def setupAdvancedIkTwist(ik='', worldUpType='objectUp', upAxis='posY', worldUpObject='', worldUpObjCons=''):
    '''
    Setup advanced ik twist for given ik.

    @inParam ik - string, name of ikHandle to setup twist for
    @inParam worldUpType - string, type of world up, for now only objectUp works
    @inParam upAxis - string, up axis for ikHandle solver, options are: posY, negY, closestY, posZ, negZ, closestZ
    @inParam worldUpObject - string, world up object, object defines the world up vector
    @inParam worldUpObjCons - string, constrain worldUpObject to this

    @procedure rig.setupAdvancedIkTwist(ik=ik[0], worldUpType='objectUp', upAxis='posY', worldUpObject=worldUpLoc, worldUpObjCons=joint)
    '''
    if mc.objExists(ik):
        mc.setAttr(ik+'.dTwistControlEnable', 1)
        #To be extended so it works with flag worldUpType
        mc.setAttr(ik+'.dWorldUpType', 1)

        if upAxis == 'negY':
            mc.setAttr(ik+'.dWorldUpAxis', 1)
        elif upAxis == 'closestY':
            mc.setAttr(ik+'.dWorldUpAxis', 2)
        elif upAxis == 'posZ':
            mc.setAttr(ik+'.dWorldUpAxis', 3)
        elif upAxis == 'negZ':
            mc.setAttr(ik+'.dWorldUpAxis', 4)
        elif upAxis == 'closestZ':
            mc.setAttr(ik+'.dWorldUpAxis', 5)
        else:
            mc.setAttr(ik+'.dWorldUpAxis', 0)

        if mc.objExists(worldUpObject):
            mc.connectAttr(worldUpObject+'.worldMatrix[0]', ik+'.dWorldUpMatrix')
        else:
            print 'World up object doesnt exist -'+worldUpObject

        if worldUpObjCons:
            if mc.objExists(worldUpObjCons):
                mc.parentConstraint(worldUpObjCons, worldUpObject, mo=1)
                mc.scaleConstraint(worldUpObjCons, worldUpObject, mo=1)
            else:
                print 'World up constraint object doesnt exist -'+worldUpObjCons
    else:
        print 'Ik handle does not exist - '+ik



def createIkHinge(name='L_hip', solver='ikRPsolver', loc1='', loc2='', loc3='', radius=1, poleVector='', jointParent='', ikParent='', jointCtrl='', jointConsType='parent', ikCtrl='', ikConsType='parent', v=1):
    '''
    Create joint chain and ikRP/ikSC solver from placements.

    @inParam name - string, prefix of ikHandle created
    @inParam solver - string, type of ikSolver, choose between ikRPsolver or ikSCsolver
    @inParam loc1 - string, position of root joint in chain. Pass it a transform object such as a locator.
    @inParam loc2 - string, position of middle joint in joint chain. Pass it a transform object such as a locator.
    @inParam loc3 - string, position of end joint in chain. Pass it a transform object such as a locator.
    @inParam radius - float, radius of joint
    @inParam poleVector - string, object used for poleVector, usually a control is given
    @inParam jointParent - string, parent of root joint created
    @inParam ikParent - string, parent ikHandle created
    @inParam jointCtrl - string, constrain the root joint to this object, used in conjunction with the jointConsType flag
    @inParam jointConsType - string, constrain the root joint to the object in the jointCtrl flag, types are parent, point or orient
    @inParam ikCtrl - string, constrain the ikHandle to this object, used in conjunction with the ikConsType flag
    @inParam ikConsType - string, constrain the ikHandle to the object in the ikCtrl flag, types are parent, point or orient
    @inParam v - int, visibility of ikHandle

    @procedure rig.createIkHinge(name='L_hip', solver='ikRPsolver', loc1='', loc2='', loc3='', radius=1, poleVector='', jointParent='', ikParent='', jointCtrl='', ikCtrl='', v=0)
    '''
    if loc1.endswith('_loc'):
        env1Name = loc1.replace('_loc', '_env')
    else:
        env1Name = name+'_001_env'

    if loc2.endswith('_loc'):
        env2Name = loc2.replace('_loc', '_env')
    else:
        env2Name = name+'_002_env'

    if loc3.endswith('_loc'):
        env3Name = loc3.replace('_loc', '_env')
    else:
        env3Name = name+'_003_env'

    env1 = createJoint(name=env1Name, snapToObj=loc1, radius=radius, parent=jointParent, ctrl=jointCtrl, const=jointConsType)
    env2 = createJoint(name=env2Name, snapToObj=loc2, radius=radius, parent=env1)
    env3 = createJoint(name=env3Name, snapToObj=loc3, radius=radius, parent=env2)

    mc.parent(env2, env3, w=1)
    for env in [env1, env2, env3]:
        mc.setAttr(env+'.rx', 0)
        mc.setAttr(env+'.ry', 0)
        mc.setAttr(env+'.rz', 0)
    
    mc.parent(env2, env1)
    mc.parent(env3, env2)
    mc.joint(env1, e=1, oj='xyz', secondaryAxisOrient='yup', ch=1, zso=1)
    mc.joint(env1, e=1, spa=1, ch=1)

    ikHandle = createIk(name=name, solver='ikRPsolver', startJoint=env1, endEffector=env3, poleVector=poleVector, parent=ikParent, ctrl=ikCtrl, consType=ikConsType, v=v)[0]

    return [env1, env2, env3, ikHandle]  





#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#------------ ========[ SKINNING ]======== ------------#
#------------------------------------------------------#

def smoothWeights(repeat=2, envs=[]):
    '''
    Smooth skin weights multiple times on all skinned joints or a given list. When using this method, make sure you're in
    painting skin weights mode and also using the smooth brush.

    @inParam repeat - int, number of times to smooth weights per joint
    @inParam envs - list, joints to smooth weights for. If none given, all joints will be smooth skinned. If a * or ? is found in an item within the list, it will list the item, e.g. mc.ls('tail_*_env')

    @procedure rig.smoothWeights(repeat=3, envs=['tail*_env'])
    '''

    mm.eval('artAttrPaintOperation artAttrSkinPaintCtx Smooth')

    smoothEnvs = []
    if not envs:
        smoothEnvs = mc.ls('*_env')
    else:
        for env in envs:
            if '*' in env or '?' in env:
                newEnvs = mc.ls(env)
                for newEnv in newEnvs:
                    smoothEnvs.append(newEnv)

    for i in range(repeat):
        for env in smoothEnvs:
            mm.eval('artSkinInflListChanging '+env+' 1')
            mm.eval('artSkinInflListChanged artAttrSkinPaintCtx')
            mm.eval('artAttrSkinPaintCtx -e -clear `currentCtx`')




def renameSkinCluster(geo=[], prefix='', suffix='_skinCluster'):
    '''
    Rename the skinCluster's for given geometry, or if no geometry given, for all skinClusters within the scene. Rename to the
    standard Dneg naming convention or to the naming convention specified by the parameters - prefix + geo + suffix
    Useful for when you bind multiple meshes to joints. Standard naming convention is geo+'_skinCluster'.

    @inParam geo - string, suffix of new skinCluster

    @procedure rig.renameSkinCluster(geo=['costume_grp'], prefix='importCostume_')
    '''

    #If no geo list given, find all geometry within the scene.
    geometry = geo
    if not geometry:
        geometry = mc.ls('*_geo')

    geoNoSkin = []
    geoCorSkin = []

    #For each geo check it exists.
    for geo in geometry:
        if mc.objExists(geo):
            #If object in list is a group, find it's descendants.
            if not mc.listRelatives(geo, s=1):
                for obj in mc.listRelatives(geo, ad=True, type='transform'):
                    #Find the geo's skinCluster if it has one.
                    skinCluster = mm.eval('findRelatedSkinCluster("'+obj+'")')

                    #If geo has a skinCluster, check it has the correct naming convention.
                    if skinCluster:
                        if skinCluster != prefix+obj+suffix:
                            #Rename the skinCluster to the correct naming convention.
                            mc.rename(skinCluster, prefix+obj+suffix)
                            print 'Skincluster renamed for '+obj+' - '+prefix+obj+suffix
                        else:
                            geoCorSkin.append(obj)
                    else:
                        geoNoSkin.append(obj)
            else:
                #Find the geo's skinCluster if it has one.
                skinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')

                #If geo has a skinCluster, check it has the correct naming convention.
                if skinCluster:
                    if skinCluster != prefix+geo+suffix:
                        #Rename the skinCluster to the correct naming convention.
                        mc.rename(skinCluster, prefix+geo+suffix)
                        print 'Skincluster renamed for '+geo+' - '+prefix+geo+suffix
                    else:
                        geoCorSkin.append(geo)
                else:
                    geoNoSkin.append(geo)
        else:
            print geo+' does not exist.'

    for geo in geoCorSkin:
        skinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')
        print 'SkinCluster already correct name for '+geo+' - '+skinCluster

    for geo in geoNoSkin:
        print 'No skinCluster found for '+geo



def dnRigSkinAs(sourceGeo, targetGeo):
    '''
    Use Dnegs dnRig_skinAs function to skin target geometries with the same weights as the source geo. Target geometry must not
    have an existing skinCluster. The command creates a new skinCluster and uses maya's copySkinWeights command. I usually use
    an influence association of Label and One to One so check you have the correct settings before running this procedure.  

    @inParam sourceGeo - string, geometry to skin from
    @inParam targetGeo - list, geometry to skin to

    @procedure rig.dnRigSkinAs('trousers_geo', ['trouserButton_grp'])
    '''

    #If the source geometry exists, look for a skinCluster. If either don't exist, print an error message.
    if mc.objExists(sourceGeo):
        if mm.eval('findRelatedSkinCluster("'+sourceGeo+'")'):
            #For each target geo, check it exists.
            for geo in targetGeo:
                if mc.objExists(geo):
                    #If target geo is of type mesh.
                    if mc.listRelatives(geo, s=1):
                        #Select target then source geometry and run the mel command dnRig_skinAs.
                        mc.select(geo, sourceGeo, r=1)
                        mm.eval('dnRig_skinAs')

                        #Rename the skinCluster to the Dneg naming convention.
                        skinCluster = mc.rename(mm.eval('findRelatedSkinCluster("'+geo+'")'), geo+'_skinCluster')
                        print sourceGeo+' weights copied to '+geo
                    else:
                        #Check if geo is a group, list all the descendants.
                        for obj in mc.listRelatives(geo, ad=True, type='transform'):
                            #If descendant is type mesh, continue.
                            if mc.listRelatives(obj, s=1):
                                #Check if geometry has an existing skinCluster.
                                if mm.eval('findRelatedSkinCluster("'+obj+'")'):
                                    #If geometry has an existing skinCluster, delete it.
                                    skinCluster = mm.eval('findRelatedSkinCluster("'+obj+'")')
                                    mc.delete(skinCluster)
                                    print skinCluster+' deleted from '+obj

                                #Select target then source geometry and run the mel command dnRig_skinAs.
                                mc.select(obj, sourceGeo, r=1)
                                mm.eval('dnRig_skinAs')
                                #Rename the skinCluster to the Dneg naming convention.
                                skinClusterName = mm.eval('findRelatedSkinCluster("'+obj+'")')
                                mc.rename(skinClusterName, obj+'_skinCluster')
                else:
                    print geo+' does not exist, dnRig_skinAs not run.'
        else:
            print sourceGeo+' does not have a skinCluster, can\'t copy weights to target geo.'
    else:
        print sourceGeo+' does not exist.'



def mirrorSkinWeights(geos, mirrorAxis='YZ'):
    '''
    Mirror skin weights on list of geometry. If geo starts with L_ or R_, it will find the opposite geo and mirror, else it will
    mirror accross itself e.g. body_geo.

    @inParam geos - list, geometry to mirror skin weights
    @inParam mirrorAxis - string, axis to mirror

    @procedure rig.mirrorSkinWeights(['L_trim01_geo', 'L_trim02_geo', 'L_trim03_geo'], 'YZ')
    '''
    geometry = []
    for geo in geos:
        if not mc.listRelatives(geo, s=1):
            objs = mc.listRelatives(geo, ad=True, type='transform')
            for obj in objs:
                if obj.endswith('_geo'):
                    geometry.append(obj)
        else:
            geometry.append(geo)

    for geo in geometry:
        mirrorGeo = geo
        if geo[0:2] == 'L_':
            mirrorGeo = geo.replace('L_', 'R_')
        elif geo[0:2] == 'R_':
            mirrorGeo = geo.replace('R_', 'L_')

        if not mc.objExists(mirrorGeo):
            print geo+' - Could not find opposite geo (Left or Right).'
        else:
            sourceSkinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')
            mirrorSkinCluster = mm.eval('findRelatedSkinCluster("'+mirrorGeo+'")')

            if sourceSkinCluster == '':
                print geo+' has no skinCluster, weights not mirrored to '+mirrorGeo+'.'
                if mirrorSkinCluster == '':
                    print mirrorGeo+' also has no skinCluster, weights not mirrored from '+geo+'.'
            elif mirrorSkinCluster == '':
                print mirrorGeo+' has no skinCluster, weights not mirrored from '+geo+'.'
            else:
                mc.copySkinWeights(ss=sourceSkinCluster, ds=mirrorSkinCluster, mirrorMode=mirrorAxis, surfaceAssociation='closestPoint', influenceAssociation=['label', 'oneToOne'])
                print 'Mirrored weights from '+geo+' to '+mirrorGeo


def copySkinOneToMany(source, destGeo=[], deleteSkin=1, removeUnInf=1, copyType='closestPoint'):
    '''
    Copy weights from one source object to many objects. Great for bolts on a big piece of metal for example.

    @inParam geos - list, geometry to mirror skin weights
    @inParam deleteSkin - int, flag to delete skinCluster and create a new one. Useful if number of influences are different, 1 = Create new, 0 = Don't.
    @inParam removeUnInf - int, flag to delete unused influences, 1 = yes, 0 = no.
    @inParam copyType - string, copy skin weights surface association. Types are closestPoint, rayCast, closestComponent, uvSpace

    @procedure rig.copySkinOneToMany('body_geo', destGeo=['jacket_button_grp'], copyType='closestPoint')
    '''
    noSkinCluster = []
    geoSkin = []

    if not destGeo:
        destGeo = mc.ls('*_geo')
        #If source geo doesn't contain a namespace, remove it from destination geo.
        if not ':' in source and '_geo' in source:
            destGeo.remove(source)

    for geo in destGeo:
        if '*' in geo:
            destGeo.remove(geo)
            addGeo = mc.ls(geo)

            for g in addGeo:
                destGeo.append(g)

    if mc.objExists(source):
        sourceSkinCluster = mm.eval('findRelatedSkinCluster("'+source+'")')

        if sourceSkinCluster:
            for geo in destGeo:
                if not mc.listRelatives(geo, s=1):
                    objs = mc.listRelatives(geo, ad=True, type='transform')
                    for obj in objs:
                        if obj.endswith('_geo'):
                            destSkinCluster = mm.eval('findRelatedSkinCluster("'+obj+'")')

                            if destSkinCluster:
                                if deleteSkin:
                                    #If deleteSkin flag is on, delete the skinCluster and create a new one with all joints assigned.
                                    mc.delete(destSkinCluster)
                                    envs = mc.ls('*_env')
                                    mc.skinCluster(obj, envs, tsb=True, n=destSkinCluster)

                                if copyType == 'uvSpace':
                                    mc.copySkinWeights(ss=sourceSkinCluster, ds=destSkinCluster, noMirror=1, surfaceAssociation='closestPoint', influenceAssociation=['label', 'oneToOne'])
                                else:
                                    mc.copySkinWeights(ss=sourceSkinCluster, ds=destSkinCluster, noMirror=1, surfaceAssociation=copyType, influenceAssociation=['label', 'oneToOne'])

                                geoSkin.append(obj)
                                print 'Weights copied from '+source+' to '+obj
                            else:
                                noSkinCluster.append(obj)
                else:  
                    if mc.objExists(geo):
                        destSkinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')

                        if destSkinCluster:
                            if deleteSkin:
                                #If deleteSkin flag is on, delete the skinCluster and create a new one with all joints assigned.
                                mc.delete(destSkinCluster)
                                envs = mc.ls('*_env')
                                mc.skinCluster(geo, envs, tsb=True, n=destSkinCluster)

                            #If skincluster found, copy the weights.
                            if copyType == 'uvSpace':
                                mc.copySkinWeights(ss=sourceSkinCluster, ds=destSkinCluster, noMirror=1, surfaceAssociation='closestPoint', influenceAssociation=['label', 'oneToOne'])
                            else:
                                mc.copySkinWeights(ss=sourceSkinCluster, ds=destSkinCluster, noMirror=1, surfaceAssociation=copyType, influenceAssociation=['label', 'oneToOne'])
                            print 'Weights copied from '+source+' to '+geo

                            geoSkin.append(geo)
                        else:
                            noSkinCluster.append(geo)
                    else:
                        print geo+' does not exist. Weights not copied.'
        else:
            print source+' does not have a skinCluster. Weights not copied.'
    else:
        print source+' does not exist.'

    print '#---------------------[ COPY SKIN WEIGHTS COMPLETED ]---------------------#'

    #Print the list of geo that doesn't exist.
    print '\n\n#---------------------[ WEIGHTS NOT COPIED ]---------------------#\nThe following geo does not contain a skincluster, weights were not copied.\n'
    for geo in noSkinCluster:
        print geo
    print '\n#---------------------[ WEIGHTS NOT COPIED ]---------------------#'



    if removeUnInf:
        #List all geometry, find if it has a skinCluster and run the removeUnusedInfluences command.
        mc.select(geoSkin, r=1)
        mm.eval('removeUnusedInfluences')
        mc.select(cl=True)

        print '#---------------------[ REMOVED UNUSED INFLUENCES ]---------------------#'



def copySkinFromPubRig(namespace, geos=[], copyType='closestPoint'):
    '''
    Copy weights from a published rig to a rig getting built (no namespace).

    @inParam namespace - string, published rig namespace
    @inParam geos - list, geoemtry to copy skin weights to
    @inParam copyType - string, copy skin weights surface association. Types are closestPoint, rayCast, closestComponent, uvSpace

    @procedure rig.copySkinFromPubRig('SUBULTa01', geos=[], copyType='closestPoint')
    '''

    if namespace[-1] != ':':
        namespace = namespace+':'

    #If no geo list provided, search for all geo.
    if not geos:
        geos = mc.ls('*_geo')

    #Create list of geo that doesn't exist so I can print nice list at end.
    geoNotExist = []

    for geo in geos:
        if not mc.listRelatives(geo, s=1):
            objs = mc.listRelatives(geo, ad=True, type='transform')
            for obj in objs:
                if obj.endswith('_geo'):
                    if mc.objExists(namespace+obj):
                        pubSkinCluster = mm.eval('findRelatedSkinCluster("'+namespace+obj+'")')
                        geoSkinCluster = mm.eval('findRelatedSkinCluster("'+obj+'")')

                        if not pubSkinCluster:
                            print namespace+obj+' does not have a skinCluster!'
                        elif not geoSkinCluster:
                            print obj+' does not have a skinCluster!'
                        else:
                            if copyType == 'uvSpace':
                                mc.copySkinWeights(ss=pubSkinCluster, ds=geoSkinCluster, noMirror=1, surfaceAssociation='closestPoint', influenceAssociation=['label', 'oneToOne'])                          
                            else:
                                mc.copySkinWeights(ss=pubSkinCluster, ds=geoSkinCluster, noMirror=1, surfaceAssociation=copyType, influenceAssociation=['label', 'oneToOne'])
                            print 'Weights copied for '+obj
                    else:
                        geoNotExist.append(namespace+obj)
        else:
            if mc.objExists(namespace+geo):
                pubSkinCluster = mm.eval('findRelatedSkinCluster("'+namespace+geo+'")')
                geoSkinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')

                if not pubSkinCluster:
                    print namespace+geo+' does not have a skinCluster!'
                elif not geoSkinCluster:
                    print geo+' does not have a skinCluster!'
                else:
                    if copyType == 'uvSpace':
                        mc.copySkinWeights(ss=pubSkinCluster, ds=geoSkinCluster, noMirror=1, surfaceAssociation='closestPoint', influenceAssociation=['label', 'oneToOne'])                          
                    else:
                        mc.copySkinWeights(ss=pubSkinCluster, ds=geoSkinCluster, noMirror=1, surfaceAssociation=copyType, influenceAssociation=['label', 'oneToOne'])
                    print 'Weights copied for '+geo
            else:
                geoNotExist.append(namespace+geo)

    #Print the list of geo that doesn't exist.
    print '\n\n#---------------------[ WEIGHTS NOT COPIED ]---------------------#\nThe following geo does not exist, weights were not copied.\n'
    for geo in geoNotExist:
        print geo
    print '\n#---------------------[ WEIGHTS NOT COPIED ]---------------------#'



def copySkinToSkin(geos=[], suffix='_1', mirrorAxis='YZ', copyType='closestPoint', createSkin=1):
    '''
    Copy weights from one hierarchy to another (no namespace). The hierarchy to copy weights from must have a suffix in order not to have name clashes.
    It shall rename the skinClusters of the original duplicate hierarchy. An example of this use is the costume model updated with higher res or becomes
    a different size and the costume scene I was skinning with becomes obsolete and I haven't published it. I can import the new model, add a suffix to
    the original and run this procedure.

    @inParam geos - list, geoemtry to copy skin weights to
    @inParam suffix - string, suffix of original duplicate hierarchy to copy weights from
    @inParam mirrorAxis - string, axis to mirror
    @inParam copyType - string, copy skin weights surface association. Types are closestPoint, rayCast, closestComponent, uvSpace
    @inParam createSkin - int, if no skinCluster is found on geo to copy weights to, a skinCluster will be created

    @procedure rig.copySkinToSkin(['importCostume'], suffix='_1', copyType='closestPoint', createSkin=1)
    '''

    #If no geo list provided, search for all geo.
    if not geos:
        geos = mc.ls('*_geo')

    #Create list of geo that doesn't exist so I can print nice list at end.
    geoNotExist = []
    origGeoNotExist = []

    for geo in geos:
        if not mc.listRelatives(geo, s=1):
            objs = mc.listRelatives(geo, ad=True, type='transform')
            for obj in objs:
                if obj.endswith('_geo'):
                    origGeo = obj+suffix

                    if mc.objExists(obj):
                        if mc.objExists(origGeo):
                            origSkinCluster = mm.eval('findRelatedSkinCluster("'+origGeo+'")')
                            geoSkinCluster = mm.eval('findRelatedSkinCluster("'+obj+'")')

                            if not origSkinCluster:
                                print origGeo+' does not have a skinCluster!'
                            elif not geoSkinCluster:
                                if createSkin:
                                    origSkinCluster = dnRigSkinAs(origGeo, [obj])
                                    print obj+' does not have a skinCluster - created skincluster!'
                                else:
                                    print obj+' does not have a skinCluster!'
                            else:
                                if copyType == 'uvSpace':
                                    mc.copySkinWeights(ss=origSkinCluster, ds=geoSkinCluster, mirrorMode=mirrorAxis, surfaceAssociation='closestPoint', uvSpace=['map1', 'map1'], influenceAssociation=['label', 'oneToOne'])                          
                                else:
                                    mc.copySkinWeights(ss=origSkinCluster, ds=geoSkinCluster, mirrorMode=mirrorAxis, surfaceAssociation=copyType, influenceAssociation=['label', 'oneToOne'])
                                print 'Weights copied for '+obj
                        else:
                            origGeoNotExist.append(origGeo)
                    else:
                        geoNotExist.append(obj)
        else:
            if mc.objExists(geo):
                origGeo = geo+suffix
                if mc.objExists(origGeo):
                    origSkinCluster = mm.eval('findRelatedSkinCluster("'+origGeo+'")')
                    geoSkinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')

                    if not origSkinCluster:
                        print origGeo+' does not have a skinCluster!'
                    elif not geoSkinCluster:
                        if createSkin:
                            origSkinCluster = dnRigSkinAs(origGeo, [geo])
                            print geo+' does not have a skinCluster - created skincluster!'
                        else:
                            print geo+' does not have a skinCluster!'
                    else:
                        mc.copySkinWeights(ss=origSkinCluster, ds=geoSkinCluster, mirrorMode=mirrorAxis, surfaceAssociation=copyType, influenceAssociation=['label', 'oneToOne'])
                        print 'Weights copied for '+geo
                else:
                    origGeoNotExist.append(origGeo)
            else:
                geoNotExist.append(geo)

    #Print the list of geo that doesn't exist.
    print '\n\n#---------------------[ WEIGHTS NOT COPIED ]---------------------#\nThe following geo does not exist, weights were not copied.\n'
    for geo in geoNotExist:
        print geo
    for origGeo in origGeoNotExist:
        print origGeo
    print '\n#---------------------[ WEIGHTS NOT COPIED ]---------------------#'



def skinGeometry(dictionary={}, prefix=''):
    '''
    Skin geometry to joints.

    @inParam dictionary - dictionary, of geo and joints. Key is geometry or a group, value is a list of joints to skin to. If joint or geo begin with '_' it will find L to R etc. 
    @inParam prefix - string, skincluster prefix name, for example importCostume_

    @procedure rig.skinGeometry(dictionary={'_pect_grp':['_pectPiston_root_env', '_pectPiston_end_env']}, prefix='importCostume_')
    '''
    skinClusters = []

    for geometry, joints in dictionary.iteritems():
        #check if it is L/R objects
        if geometry[0] == '_':
            for s in ['L', 'R']:
                geos = []
                geoShort = []
                envs = []
                grp = s + geometry
                count = 0

                if mc.objExists( grp ):
                    if geometry[-4:] == '_grp':
                        objs = mc.listRelatives(grp, ad=True, type = 'transform', f=1)
                        for obj in objs:
                            if obj[-4:] == '_geo':
                                geos.append(obj)
                                geoShort.append(obj.rsplit('|')[-1])
                    else:
                        geos.append( grp )
                        geoShort.append(grp)
                    for geo in geos:
                        #If no joints given, list all joints.
                        if not joints:
                            envs = mc.ls('*_env')
                        else:
                            for jnt in joints:
                                # if it is L/R joints
                                if jnt[0] == '_':
                                    envs.append( s + jnt)
                                else:
                                    envs.append( jnt )

                        skinCluster = mc.skinCluster( geo, envs, tsb=True, n= prefix+geoShort[count] + '_skinCluster')[0]
                        skinClusters.append(skinCluster)

                        count = count + 1
        else:
            geos = []
            envs = []
            geoShort = []
            count = 0
            grp = geometry

            if mc.objExists( geometry ):
                if geometry[-4:] == '_grp':
                    objs = mc.listRelatives(geometry, ad=True, type = 'transform', f=1)
                    for obj in objs:
                         if obj[-4:] == '_geo':
                              geos.append(obj)
                              geoShort.append(obj.rsplit('|')[-1])
                else:
                    geos.append( geometry )
                    geoShort.append(grp)
                for geo in geos:
                    #If no joints given, list all joints.
                    if not joints:
                        envs = mc.ls('*_env')
                    else:
                        for jnt in joints:
                            # if it is L/R joints
                            if jnt[0] == '_':
                                for s in ['L', 'R']:
                                    envs.append( s + jnt)
                            else:
                                envs.append( jnt )

                    skinCluster = mc.skinCluster( geo, envs, tsb=True, n= prefix+geoShort[count] + '_skinCluster')[0]
                    skinClusters.append(skinCluster)

                    count = count + 1

    return skinClusters



def bindPreMatrixSkinCluster(envDict):
    '''
    Sets up a bindPreMatrix for an existing skinCluster. Pass it the ctrl/offset/object that controls the joint, this will plug it's worldMatrix
    into the skinCluster bindPreMatrix so that moving the offset wont deform the geometry.

    @inParam envDict - dictionary, key = joint, value = Object driving the joint, for instance a ctrl offset or follicle the joint is parented under.

    @procedure rig.bindPreMatrixSkinCluster({'tongue_001_env':'tongue_001_follicle', 'tongue_002_env':'tongue_002_follicle'})
    '''

    for env, offset in envDict.iteritems():
        if mc.objExists(env):
            if mc.objExists(offset):
                connections = mc.listConnections(env, p=1, t='skinCluster')

                if connections:
                    for connection in connections:
                        if '.matrix[' in connection:
                            items = connection.split('.')
                            skinCluster = items[0]
                            index = re.findall('\d+', items[1])[0]

                            if mc.isConnected(offset+'.worldInverseMatrix[0]', skinCluster+'.bindPreMatrix['+index+']'):
                                print offset+'.worldInverseMatrix[0] is already connected to '+skinCluster+'.bindPreMatrix['+index+']'
                            else:
                                mc.connectAttr(offset+'.worldInverseMatrix[0]', skinCluster+'.bindPreMatrix['+index+']')
                else:
                    print 'No skinCluster found for '+env+'.'
            else:
                print offset+' wasn\'t found, skipping '+env+'.'
        else:
            print env+' wasn\'t found, skipping joint.'



def skinInfluenceCleanup():
    '''
    Remove unused influences.

    @procedure rig.skinInfluenceCleanup()
    '''
    #List all geometry, find if it has a skinCluster and run the removeUnusedInfluences command.
    geos = mc.ls('*_geo')
    for geo in geos:
        if mm.eval('findRelatedSkinCluster("' + geo + '")'):
            mc.select( geo, r=True )
            mm.eval('removeUnusedInfluences')
            mc.select( cl=True )


def saveSkinWeights(weightsFile='', op='save', geos=[]):
    '''
    Save or load skin weights.

    @inParam weightsFile - string, name of skin file
    @inParam op - string, operation of wimp statement either save or load
    @inParam geos - list, geometry to save skin weights, you can pass a parent null and it will find all the descendants geometry

    @procedure rig.saveSkinWeights('/jobs/INVERT/rdev_sailor/maya/weights/firstMate_costumeAnim_skinWeights_v001.wmp', op='sv', geos=['proxyMeshes_null'])
    '''
    
    #List of geo that have no skinCluster. Print list at end. Wimp string that will be used in the wimp mel command.
    geoNoSkin = []
    geoSkinned = []
    wimpString = ''
    operation = ''

    #If no geo given, list all geo.
    if not geos:
        geos = mc.ls('*_geo')

    #Check operation is correct
    if op == 'save' or op == 'sv':
        operation = 'sv'
    elif op == 'load' or op == 'ld':
        operation = 'ld'
    else:
        print op+' is not a valid operation, choose either save/sv or load/ld.'

    #If file given does not end with the wimp file extention, add it.
    if weightsFile[-4:] != '.wmp':
        weightsFile = weightsFile+'.wmp'

    #If weights file exists and we're trying to save, print warning.
    if op == 'save' or op == 'sv':
        if mc.file(weightsFile, q=1, ex=1):
            mc.error('WEIGHTS NOT SAVED, FILE ALREADY EXISTS - '+weightsFile)


    #List of geo
    geoSkin = []
    #For each geo given.
    for geometry in geos:
        #Find out if a group of objects was given (null), if so find all the pieces of geo under it.
        if mc.listRelatives(geometry, ad=True, type='transform'):
            geoList = []
            for geo in mc.listRelatives(geometry, ad=True, type='transform'):
                if mc.listRelatives(geo, s=1):
                    geoList.append(geo)
            geoSkin.append(geoList)
        else:
            geoSkin.append(geometry)


    #If a group of objects was given, it will iterate through all the descendants, else this for loop will only run once for given geo.
    for geo in geoSkin:
        #For each each, find skinCluster
        skinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')

        if not skinCluster:
            #If no skincluster exists, add geo to the print statement at the end.
            geoNoSkin.append(geo)
        else:
            geoShape = mc.listRelatives(geo, s=1)[0]

            #Prepare wimpString
            if geo == geoSkin[-1]:
                print geo
                wimpString = wimpString+skinCluster+'@'+geoShape
            else:
                wimpString = wimpString+skinCluster+'@'+geoShape+', '
            print wimpString
            geoSkinned.append(geo)

    #Save or load wimpFile.
    mm.eval('wimpIO -f "'+weightsFile+'" -'+operation+' "'+wimpString+'"')
    print 'wimpIO -f "'+weightsFile+'" -'+operation+' "'+wimpString+'"'

    #Print geo not skinned.
    for geo in geoSkinned:
        skinCluster = mm.eval('findRelatedSkinCluster("'+geo+'")')
        print 'Geometry skinCluster '+operation+'ed for '+geo+' - '+skinCluster

    #Print geo not skinned.
    for geo in geoNoSkin:
        print 'No skinCluster found for '+geo



#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#-------------- ========[ DNWIMP ]======== ------------#
#------------------------------------------------------#

def createWimpPaintNodeAndPaintMesh(name='', geo='', wimpMaps=[], mirror=1, parentWimp='', parentPaintMesh='', parentBlendShapeHolder=''):
    '''
        Creates a wimp paint node, wimp layer and paint mesh. Use the mirror attr to mirror a map painted. This is used to split up a blendshape into L and R sides 
        using wimp maps. 

        @inParam name - string, name for everything created
        @inParam geo - string, type of guideline to create, 0:Y axis with bottom of guidline on origin  1:Y axis with centre on origin 
        @inParam wimpMaps - list, list of maps to create for the wimpPaint node
        @inParam mirror - int, if 1 it will mirror the wimp map, 0 it wont
        @inParam parentWimp - string, parent of the wimpPaint node created 
        @inParam parentPaintMesh - string, parent of the paint mesh created 
        @inParam parentBlendShapeHolder - string, parent of the blendShapeHolder created (a locator with an attribute that is the input to the wimpMult node). So if the locator.attr = 0, the wimp map is multiplied by 0 so it's off

        @procedure rig.createWimpPaintNodeAndPaintMesh(name='lipCornerPuller', geo=target, wimpMaps=['lipCornerPuller'], mirror=1, parentWimp=otherNull, parentPaintMesh=meshGroup, parentBlendShapeHolder=rigGroup)
    '''
    #Create a paint mesh and ref mesh for the wimpPaint node
    refMesh = mc.duplicate(geo, n=name+'_ref_mesh')[0]
    mc.setAttr(refMesh+'.intermediateObject', 1)  

    paintMesh = mc.duplicate(geo, n=name+'_paint_mesh')[0]
    paintMeshShape = mc.listRelatives(paintMesh,s=True)[0]
    mc.setAttr(paintMesh+'.v', 0)

    #Create the wimpPaint node and connect the paintMesh to it.
    wimpPaint = mc.createNode('dnWimpPaint', n=name+'_dnWimpPaint')
    wimpPaintTransform=mc.rename(mc.listRelatives(wimpPaint, p=True)[0], name+'_transform')
    mc.connectAttr(paintMeshShape+'.worldMesh', wimpPaint+'.geom')

    #Parent the wimpPaint node
    if mc.objExists(parentWimp):
        mc.parent(wimpPaintTransform, parentWimp)
    else:
        print parentWimp+' does not exist!'

    #Create a zero map for the wimpPaint node and set the map weights to zero.
    mc.aliasAttr('zero', wimpPaint+'.map[0]')
    for a in range(len(mc.ls(geo+'.vtx[*]', fl=True))):      
        mc.setAttr(wimpPaint+'.internalMapList[0].mapWeights['+str(a)+']', 0.0)

    #Create the wimpLayer to merge mirrored wimp maps if mirror flag is on. Turn the layer operation to screen.
    #NOTE IF YOUR PINOCCHIO SESSION HAS ERRORED HERE >>> YOU HAVE TO SEARCH FOR *_dnWimpLayer IN THE SCENE AND GO TO THE ATTRIBUTE EDITOR AND CLICK THE CREATE NEW 
    #LAYER BUTTON. I DONT KNOW THE COMMAND.
    wimpLayer=mc.createNode('dnWimpLayer', n=name+'_dnWimpLayer')
    #mm.eval('AEdnWimpLayerNewLayer(\"'+wimpLayer+'\")');
    for i in range(0,len(wimpMaps)*2):
        mc.setAttr(wimpLayer+'.layer['+str(i)+'].layerOperation', 9)

    #Connect the wimpPaint zero map to the layer.
    mc.connectAttr(wimpPaint+'.zero', wimpLayer+'.input')

    #If mirror is on, mirror the maps created on the wimpPaint node
    sides = ['']
    if mirror:
        sides = ['L_', 'R_']

    c = -1
    for side in sides:
        startCount = c + 1

        #Create a locator to hold an attribute. This attribute will usually be 0-1 and be plugged into a wimp mult node to define how the wimp map is driven
        #i.e. if the attr is 1, the wimpMap will be white and on, if the attr is 0 - the wimpMap will be multiplied by zero so be off. 
        blendShapeHolder = rig.createLoc(name=side+name+'_blendShapesHolder', parent=parentBlendShapeHolder, v=0)
        rig.lockAndHideAttr(blendShapeHolder, ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v'])

        #For each wimpMap to be created
        for c, wimpMap in enumerate(wimpMaps): 
            i = c + startCount
            #Add the attribute
            attr = rig.addDoubleAttr(ctrl=blendShapeHolder, attr=wimpMap, min=0, max=3, dv=0)
      
            #Create the map on the wimpPaint node.
            if side == 'L_' or mirror == 0:
                mm.eval('dnWimpPaint_newMap(\"'+wimpPaint+'\");')
                numMaps = len(mc.listAttr(wimpPaint+'.map[*]'))        
                mc.aliasAttr (wimpMap, wimpPaint+'.map['+str(numMaps-1)+']')

            #Create a wimpMult node and connect the blendShapeHolder attribute to it.
            wimpMult = mc.createNode('dnWimpMultC', n=side+wimpMap+'_mult')    
            if side == 'L_' or mirror == 0:
                mc.connectAttr(wimpPaint+'.'+wimpMap, wimpMult+'.input')
            mc.connectAttr(blendShapeHolder+'.'+wimpMap, wimpMult+'.mult')
            #Connect the wimpMult node to the wimpLayer
            mc.connectAttr(wimpMult+'.output', (wimpLayer+'.layer['+str(i)+'].layerIn'))

            #If mirror flag is on
            if mirror == 1:    
                if side == 'R_':
                    #Create a wimpMirror node to mirror the map
                    wimpMirror = mc.createNode('dnWimpMirror', n=side+wimpMap+'_wimpMirror')
                    mc.setAttr(wimpMirror+'.direction', 2)
                    mc.setAttr(wimpMirror+'.plane', 0)

                    #Connect the refMesh to it
                    refMeshShape = mc.listRelatives(refMesh, s=True)[0]
                    mc.connectAttr(refMeshShape+'.outMesh', wimpMirror+'.refGeo')

                    #Connect the wimpPaint node to the wimpMirror and the wimpMirror the the 
                    mc.connectAttr(wimpPaint+'.'+wimpMap, wimpMirror+'.input')
                    mc.connectAttr(wimpMirror+'.output', wimpMult+'.input')

    #Rename the wimpPaint node
    mc.rename (name+"_dnWimpPaint", name + "_dnWimpPaintShape")
    mc.rename (name+"_transform", name + "_dnWimpPaint")

    return wimpLayer



def saveDeformerMap(node='sail_wave', mode='load', wimpMap=''):
    '''
    Save a deformer map using wimpIO.

    @inParam node - string, name of deformer or name of deformer map (such as a paint node)
    @inParam mode - string, mode of operation - load or save
    @inParam wimpMap - string, wimp map to save or load weights onto. Must end with file ext .wmp
    
    @procedure rig.saveDeformerMap(nodes=['sail_wave'], mode='load', wimpMap='/jobs/INVERT/rdev_wonder/maya/weights/sailWave_weights_v001.wmp')

    @notes command to save paint node weights - mc.wimpIO("midMastMidYard_wave_paint, foreMast_sailC_geo_foreMastLowYard_wave_paint", f="/jobs/INVERT/rdev_wonder/maya/weights/sailWave_weights_v001.wmp", save=1)
    '''
    
    if mc.file(wimpMap, q=1, ex=1):
        if mode == 'load':
            mc.wimpIO(node, f=wimpMap, load=1)
        elif mode == 'save':
            mc.wimpIO(node, f=wimpMap, save=1)
    else:
        print 'Wimp file does not exist - '+wimpMap




def copyDeformerWeightsToNewGeo(deformer='', map='', geoShape='', deformerNew='', mapNew='', geoShapeNew='', space='objectSpace'):
    '''
    Copies deformer weights from one geo to another. The geometry doesn't have to be the same topology.

    @inParam deformer - string, deformer to copy weights from
    @inParam map - string, map of deformer to copy weights from
    @inParam geoShape - string, geo shape deformer is on
    @inParam deformerNew - string, deformer to copy weights to
    @inParam mapNew - string, map of deformer to copy weights to
    @inParam geoShapeNew - string, geo shape deformerNew is on
    @inParam space - string, space to copy weights in, choices are objectSpace
    
    @procedure rig.copyDeformerWeightsToNewGeo(deformer='jumper_001_cluster', map='weights', geoShape='jumper_geoShape', deformerNew='cluster1', mapNew='weights', geoShapeNew='jumper_meshShape')
    '''
    if map:
        mm.eval('wimpIO -t "'+space+'" -cp "'+deformer+'.'+map+'@'+geoShape+' to '+deformerNew+'.'+mapNew+'@'+geoShapeNew+'"')
        print deformer+'.'+map+' copied to '+deformerNew+'.'+mapNew
    else:
        mm.eval('wimpIO -t "'+space+'" -cp "'+deformer+'@'+geoShape+' to '+deformerNew+'@'+geoShapeNew+'"')
        print deformer+' weights copied to '+deformerNew





def copyPaintNodeWeights(geo, paintNode, newGeo, newPaintNode, wimpFile):
    '''
    Copy paint node weights from one node to another, geometry must have same topology.

    @inParam geo - string, name of geometry associated with paint node
    @inParam paintNode - string, paint node to copy weights from
    @inParam newGeo - string, name of new geometry associated with paint node
    @inParam newPaintNode - string, paint node to copy weights to
    @inParam wimpFile - string, wimp map to load weights onto. Must end with file ext .wmp
    
    @procedure rig.saveDeformerMap(nodes=['sail_wave'], mode='load', wimpMap='/jobs/INVERT/rdev_wonder/maya/weights/sailWave_weights_v001.wmp')

    @notes command to save paint node weights - mc.wimpIO("midMastMidYard_wave_paint, foreMast_sailC_geo_foreMastLowYard_wave_paint", f="/jobs/INVERT/rdev_wonder/maya/weights/sailWave_weights_v001.wmp", save=1)
           geo = 'mainMast_sailB_geo'
           newGeo = 'mainMast_sailA_geo'
           ctrl = 'midMastUpYard'
           paintNode(geo, geo+'_midMastMidYard_wave_paint', newGeo, newGeo+'_'+ctrl+'_wave_paint', '/jobs/INVERT/rdev_wonder/maya/weights/edgeSail_waveWeights_v001.wmp')


    '''
    mc.rename(geo, geo+'1')
    mc.rename(paintNode, paintNode+'1')

    mc.rename(newGeo, geo)
    mc.rename(newPaintNode, paintNode)

    mc.wimpIO(paintNode, f=wimpFile, load=1)

    mc.rename(geo, newGeo)
    mc.rename(paintNode, newPaintNode)

    mc.rename(geo+'1', geo)
    mc.rename(paintNode+'1', paintNode)




def mirrorDeformerWeights(geoShape='', deformerWeight='', mirrorDeformerWeight='', mirrorAxis=''):
    '''
    Mirror deformer weights using dnWimpPaint and dnWimpMirror nodes and transfer to different deformer if needed.

    @inParam geoShape - string, name of geometry associated with paint node
    @inParam deformerWeight - string, deformer and weights to mirror weights
    @inParam mirrorDeformerWeight - string, deformer and weights to transfer mirrored weights to
    @inParam mirrorAxis - string, axis to mirror weights on

    @procedure rig.mirrorDeformerWeights(geoShape='body_geoShape', deformerWeight='L_bellyCollision_dnSkinSmoother.weights', mirrorDeformerWeight='R_bellyCollision_dnSkinSmoother.weights')
    '''
    deformer = deformerWeight.split('.')[0]
    mirrorDeformer = mirrorDeformerWeight.split('.')[0]

    dnWimpPaint = mc.createNode('dnWimpPaint')
    mc.connectAttr(geoShape+'.outMesh', dnWimpPaint+'.geom')

    dnWimpMirror = mc.createNode('dnWimpMirror')
    mc.connectAttr(geoShape+'.worldMesh[0]', dnWimpMirror+'.refGeo')
    mc.setAttr(dnWimpMirror+'.direction', 2)
    mc.connectAttr(dnWimpPaint+'.outWimpMap[0]', dnWimpMirror+'.input')
    mc.select(cl=1)

    '''
    mc.setAttr(deformer+'.envelope', 0)
    mc.setAttr(mirrorDeformer+'.envelope', 0)
    mm.eval('wimpIO -t "objectSpace" -cp "'+deformerWeight+'@'+geoShape+' to '+dnWimpPaint+'.map[0]"')
    mc.select(cl=1)
    mc.dgdirty(allPlugs=1)

    mm.eval('wimpIO -t "objectSpace" -cp "'+dnWimpMirror+'.out@'+geoShape+' to '+mirrorDeformerWeight+'@'+geoShape+'"')
    mc.select(cl=1)
    mc.dgdirty(allPlugs=1)

    mc.setAttr(deformer+'.envelope', 1)
    mc.setAttr(mirrorDeformer+'.envelope', 1)
    '''

    print 'wimpIO -t "objectSpace" -cp "'+deformerWeight+'@'+geoShape+' to '+dnWimpPaint+'.map[0]"'
    print 'wimpIO -t "objectSpace" -cp "'+dnWimpMirror+'.out@'+geoShape+' to '+mirrorDeformerWeight+'@'+geoShape+'"'


    '''
    if mc.objExists(dnWimpMirror):
        mc.delete(dnWimpMirror)
    if mc.objExists(dnWimpPaint):
        mc.delete(dnWimpPaint)

    print 'Successfully copied weights from '+deformerWeight+' to '+mirrorDeformerWeight
    '''






















































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#---------------- ========[ DEFORMERS ]======== -------------#
#------------------------------------------------------------#


def nonLinearDeformer(type='wave', name='wave_deformer', geometry=[], wimpMap='', paintNode=0, parent='', snapToObj='', pos=[], rot=[], scale=[], defDict={}, ctrl='', ctrlAttr={}, defOrder='default', consTo='', consType='parent', v=1):
    '''
    Create a nonLinear deformer for given geometry, with a wimp paint map so that you can paint the deformer map.

    @inParam type - string, type of nonLinear deformer to create. Choose between 'bend', 'flare', 'sine', 'squash', 'twist', 'wave'
    @inParam name - string, name of deformer
    @inParam geometry - list, geometry to create nonLinear deformer on
    @inParam wimpMap - string, wimp map for deformer, must be of type .wmp
    @inParam paintNode - int, by default a dnWimpPaint node will be created to paint weights for the deformer. If 0 it wont be created.
    @inParam parent - string, object to parent deformer handle under
    @inParam snapToObj - string, object to snap deformer handle to and copy rotation values. If object is not given, this proc will use the trans and rot flags
    @inParam trans - list, translate coordinates for nonLinear deformer handle (make sure they are worldspace) - [0,0,0]
    @inParam rot - list, rotation coordinates for nonLinear deformer handle (make sure they are worldspace) - [0,0,0]
    @inParam scale - list, scale values for nonLinear deformer handle - [1,1,1]
    @inParam defDict - dictionary, dictionary of deformer attributes and values e.g. defDict = {'wavelenth':2.5, 'offset':0.5}. This procedure will set these values for the deformer attributes.  
    @inParam ctrl - string, name of control. The procedure will look for the same attribute names as the deformer and connect them. If ctrlAttr flag is defined, this flag will be obsolete
    @inParam ctrlAttr - dict, dictionary to define attributes from a ctrl to connect to attributes on the nonLinear deformer. If this flag is defined, it will overwrite the ctrl flag above. Specify the control attribute as the key, and attribute on the nonLinear deformer as the value e.g. ctrlAttr = {'mast_ctrl.wave':'envelope'}
    @inParam defOrder - string, deformation order of deformer. Choices are default, before, after, split, parallel
    @inParam consTo - string, object to constrain deformer handle to. If left blank, it wont get constrained
    @inParam consType - string, used with consTo flag. Type of constraint between consTo object and deformer handle, types are parent, point or orient
    @inParam v - int, visibility flag, 0 - off, 1 - on

    @return [node, handle]

    @procedure rig.nonLinearDeformer(type='wave', name='wave_deformer', geometry=['sail1_geo', 'sail2_geo'], wimpMap='/jobs/skinWeights_v001.wmp', parent=otherNull, snapToObj='snap_loc', defDict={'wavelength':2.5, 'amplitude':0.3}, ctrlAttr={'ctrl.wave':'envelope'}, defOrder='before', consTo='tail_base_ctrl', consType='parent')

    @notes command to save paint node weights - mc.wimpIO("midMastMidYard_wave_paint, foreMast_sailC_geo_foreMastLowYard_wave_paint", f="/jobs/INVERT/rdev_wonder/maya/weights/sailWave_weights_v001.wmp", save=1)
    '''
    if not geometry:
        print 'No geometry given to create nonLinear deformer on'
    else:
        geos = []
        for geo in geometry:
            if mc.objExists(geo):
                geos.append(geo)
            else:
                print 'Geometry does not exist, no deformer added to '+geo

        if defOrder == 'default':
            deformer = mc.nonLinear(geos, n=name, type=type, ds=0)
        elif defOrder == 'before':
            deformer = mc.nonLinear(geos, n=name, type=type, ds=0, before=1)
        elif defOrder == 'after':
            deformer = mc.nonLinear(geos, n=name, type=type, ds=0, after=1)
        elif defOrder == 'split':
            deformer = mc.nonLinear(geos, n=name, type=type, ds=0, split=1)
        elif defOrder == 'parallel':
            deformer = mc.nonLinear(geos, n=name, type=type, ds=0, parallel=1)
        else:
            print defOrder+' deformation order does not exist! Choices are default, before, after, split or parallel.'

        deformer[0] = mc.rename(deformer[0], name)
        deformer[1] = mc.rename(deformer[1], name+'Handle')

        if mc.objExists(parent):
            mc.parent(deformer[1], parent)
        else:
            print 'Parent object does not exist - '+parent


        if snapToObj:
            if mc.objExists(snapToObj):
                if '.vtx[' in snapToObj:
                    vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                    mc.move(vtxPos[0], vtxPos[1], vtxPos[2], deformer[1], r=1)
                else:
                    mc.delete(mc.parentConstraint(snapToObj, deformer[1]))
            else:
                print snapToObj+' does not exist!'+deformer[1]+' not snapped to'+snapToObj
        else:
            if pos:
                mc.move(pos[0],pos[1],pos[2], deformer[1], ws=1)
            if rot:
                mc.rotate(rot[0],rot[1],rot[2], deformer[1], ws=1)
            if scale:
                mc.scale(scale[0],scale[1],scale[2], deformer[1], ws=1)
        

        for attribute,value in defDict.iteritems():
            if mc.attributeQuery(attribute, node=deformer[0], ex=1):
                mc.setAttr(deformer[0]+'.'+attribute, value)
            else:
                print 'Attribute does not exist for '+deformer[0]+' - '+attribute

        if ctrlAttr:
            for ctrlA,attr in ctrlAttr.iteritems():
                if mc.objExists(ctrlA):
                    if mc.objExists(deformer[0]+'.'+attr):
                        mc.connectAttr(ctrlA, deformer[0]+'.'+attr, f=1)
                    else:
                        print deformer[0]+'.'+attr +' does not exist - ctrlAttr flag'   
                else:
                    print ctrlA +' does not exist - ctrlAttr flag'                
        elif ctrl:
            if mc.objExists(ctrl):
                defAttrs = mc.listAttr(deformer[0], k=1)
                for attr in defAttrs:      
                    if mc.attributeQuery(attr, node=ctrl, ex=1):
                        mc.connectAttr(ctrl+'.'+attr, deformer[0]+'.'+attr, f=1)
            else:
                print ctrl+' object does not exist! - ctrl flag'

        if consTo:
            if mc.objExists(consTo):
                if consType == 'parent' or consType == 'parentConstraint':
                    mc.parentConstraint(consTo, deformer[1], mo=1)
                elif consType == 'point' or consType == 'pointConstraint':
                    mc.pointConstraint(consTo, deformer[1], mo=1)
                elif consType == 'orient' or consType == 'orientConstraint':
                    mc.orientConstraint(consTo, deformer[1], mo=1)

                mc.scaleConstraint(consTo, deformer[1], mo=1)
            else:
                print consTo+' object to constrain deformer handle to does not exist'


        if paintNode:
            for index, geo in enumerate(geos):
                paintNode = mc.createNode('dnWimpPaint')
                paintNode = mc.rename(paintNode, geo+'_'+name+'_paint')
                paintTransform = mc.rename('transform1', geo+'_'+name+'_paintTransform')

                if mc.objExists(parent):
                    mc.parent(paintTransform, parent)

                mc.connectAttr(geo+'.outMesh', paintNode+'.geo')
                mm.eval('dnWimpPaint_newMap(\"'+paintNode+'\");')
                mc.connectAttr(paintNode+'.outMulti[0]', deformer[0]+'.weightList['+str(index)+']')
            
                if wimpMap:
                    if mc.file(wimpMap, q=1, ex=1):
                        print wimpMap
                        mc.wimpIO(paintNode, f=wimpMap, load=1)
                    else:
                        print 'Wimp file does not exist - '+wimpMap

        if v!=1:
            mc.setAttr(deformer[1]+'.v', 0)

        return deformer


def wireDeformer(name='wire', curve='', geo=[], baseParent='', crossingEffect=0.0, tension=1.0, localInfluence=0.0, rotation=0.0, dropoffDistance=10.0, scale=1.0, groupWithBase=0):
    '''
    Creates a wire deformer for geo using curve given

    @inParam name - string, name for wire deformer
    @inParam curve - string, curve to be used as wire deformer
    @inParam geo  - list, geometry to create wire deformer for
    @inParam baseParent - string, parent of base wire curve created
    @inParam crossingEffect  - float, set the amount of convolution effect. Varies from fully convolved at 0 to a simple additive effect at 1 
    @inParam tension  - float, set tension value of wire
    @inParam localInfluence  - float, set the local control a wire has with respect to other wires irrespective of whether it is deforming the surface. Varies from no local effect at 0 to full local control at 1
    @inParam rotation  - float, rotation flag of wire
    @inParam dropoffDistance  - float, dropoff distance of wire
    @inParam scale  - float, scale attribute for wire deformer
    @inParam groupWithBase  - int, group the wire deforer with the base curve created 

    @procedure rig.wireDeformer(name='', curve='', geo=[], baseParent='', dropoffDistance=10.0, scale=1.0)
    '''    
    if not mc.objExists(curve):
        print curve+' does not exist! @inParam curve'

    wire = mc.wire(geo, w=curve, n=name, crossingEffect=crossingEffect, localInfluence=localInfluence, dropoffDistance=(0, dropoffDistance), groupWithBase=groupWithBase)[0]
    wireSet = mc.listConnections(wire, destination=True, type='objectSet')[0]
    mc.rename(wireSet, name+'_set')

    wireBaseConnect = mc.connectionInfo(wire+'.baseWire[0]', sourceFromDestination=True)
    wireBaseShape = wireBaseConnect.replace('.worldSpace[0]', '')
    wireBase = mc.listRelatives(wireBaseShape, parent=True)[0]

    mc.setAttr(wire+'.tension', tension)  
    mc.setAttr(wire+'.rotation', rotation)
    mc.setAttr(wire+'.scale[0]', scale)  
  
    if baseParent:
        if mc.objExists(baseParent):
            if not mc.listRelatives(wireBase, parent=1)[0] == baseParent:
                mc.parent(wireBase, baseParent)
        else:
            print baseParent+' does not exist! @inParam baseParent' 
    
    #Cleans intermediate shapes from wireBase
    for relative in mc.listRelatives(wireBase):
        if mc.getAttr(relative+'.intermediateObject') == 1:
            mc.delete(relative)

    return [wire, wireBase]


def wrapTarget (sWrapMesh, sTarget, sTargetParent ='', sBaseParent = 'wrapBase_grp', bMayaWrap = False, bRelative = True, bExclusiveBind=True, bShareRefMesh=False, sRefMesh='refMesh_mesh',bShareWrapNode=False,sWrapName='',iIdx=1, bDisconnectTargetInMesh=False):
    '''
        Wraps an object using either dnWrap or Maya Wrap. Returns the wrap deformer node and base mesh. Can also add new objects to existing dnWrap

        @inParam sWrapMesh - string, wrap mesh
        @inParam sTarget - string, target geo
        @inParam sBaseParent  - string, base mesh parent
        @inParam bMayaWrap - boolean, use dnWrap otherwise use classic Maya Wrap
        @inParam bRelative - boolean, wrap is relative mode)
        @inParam bExclusiveBind - boolean, if true switch exclusiveBind on for the wrap
        @inParam bShareRefMesh - boolean, if false connect the wrap base shape (reference) to the wrap referenceMesh attribute
        @inParam sRefMesh - string, connect mesh given to wrap referenceMesh attribute

        @procedure rig.wrapTarget ('wrap_mesh','sail_geo',bMayaWrap=False)
    '''
    if sTargetParent:
        mc.parent (sTarget, sTargetParent)
    mc.select (sTarget, r=True)
    mc.select (sWrapMesh, add=True)
    if bMayaWrap == False:        
        if bShareWrapNode == False:         
            #Create dnWrap if bMayaWrap is False and bShareWrapNode is False
            sWrapNode = mm.eval ('dnWrap')                    
            sWrapName = mc.rename (sWrapNode, sWrapMesh+'_'+sTarget+'_dnWrap')
            #Search for the wrap base mesh.
            sWrapBaseShapeOutput = mc.connectionInfo(sWrapName+'.referenceMesh',sourceFromDestination=True)
            sWrapBaseShape = sWrapBaseShapeOutput.split('.')[0]
            sWrapBase = mc.listRelatives (sWrapBaseShape, parent=True)[0]
            sWrapBaseName = mc.rename (sWrapBase, sWrapMesh+'_'+sTarget+'_RefMesh')
            if bRelative == True:
                mc.connectAttr (sWrapMesh+'Shape.outMesh', sWrapName+'.driverMesh', f=True)
                if bShareRefMesh == False:            
                    mc.connectAttr (sWrapBaseName+'Shape.outMesh', sWrapName+'.referenceMesh', f=True)
                else:
                    mc.connectAttr (sRefMesh+'Shape.outMesh', sWrapName+'.referenceMesh', f=True)
                    mc.delete (sWrapBaseName)
        else:
            #If bShareWrapNode is True
            #geo_orig, geo = duplicate_orig(sTarget)
            geo_orig, geo = cloth_rig_builder.helpers.duplicate_orig(sTarget)
            group_id = mc.createNode('groupId', n='%s_%s_grpId' % (sWrapName, sTarget))
            group_parts = mc.createNode('groupParts', n='%s_%s_grpPrts' % (sWrapName, sTarget))
            mc.setAttr(group_parts+'.ic', 1, "vtx[*]", type='componentList')
            mc.connectAttr( group_id+'.groupId',group_parts+'.groupId')
            mc.connectAttr( geo_orig+'.outMesh',group_parts+'.inputGeometry')
            mc.connectAttr( group_id+'.groupId',sWrapName+'.input[%d].groupId' % iIdx)
            mc.connectAttr( group_parts+'.outputGeometry',sWrapName+'.input[%d].inputGeometry' % iIdx)
            mc.connectAttr( sWrapName+'.outputGeometry[%d]' % iIdx, geo+'.inMesh', f=True)    
            #Search for the wrap base mesh. BLAH 
            sWrapBaseShapeOutput = mc.connectionInfo(sWrapName+'.referenceMesh',sourceFromDestination=True)
            sWrapBaseShape = sWrapBaseShapeOutput.split('.')[0]
            sWrapBase = mc.listRelatives (sWrapBaseShape, parent=True)[0]
            sWrapBaseName = sWrapBase[0]                  
    else:
        #Create maya wrap if bMayaWrap is True
        sTargetShape = mc.listRelatives (sTarget)[0]                
        mc.CreateWrap()
        #Search for the wrap deformer node.
        sWrapNodeAttr = mc.connectionInfo(sTargetShape+'.inMesh',sourceFromDestination=True)
        sWrapNode = sWrapNodeAttr.split('.')[0]
        sWrapName = mc.rename (sWrapNode, sWrapMesh+'_'+sTarget+'_wrap')
        if bExclusiveBind==True:
            mc.setAttr (sWrapName+'.exclusiveBind', 1)
        #Search for the wrap base mesh.
        sWrapBaseShapeOutput = mc.connectionInfo(sWrapName+'.basePoints[0]',sourceFromDestination=True)
        sWrapBaseShape = sWrapBaseShapeOutput.split('.')[0]
        sWrapBaseName = mc.listRelatives (sWrapBaseShape, parent=True)[0]                            
    if not mc.objExists (sBaseParent):
        mc.createNode ('transform',n=sBaseParent)
    if bShareWrapNode == False:         
        if mc.objExists (sWrapBaseName):        
            mc.parent (sWrapBaseName, sBaseParent)
    #Search for wrap set and rename it.
    sWrapSet = mc.listConnections (sWrapName, destination=True, type='objectSet')  
    mc.rename (sWrapSet[0], sWrapMesh+sTarget+'_wrapSet')                  

    if bDisconnectTargetInMesh == True:
        sInMesh = sTarget+'ShapeOrig.inMesh'
        sOutMesh = mc.connectionInfo(sInMesh, sourceFromDestination=True)
        mc.disconnectAttr (sOutMesh, sInMesh)
    
    return [sWrapName,sWrapBaseName]

def createCluster(geos=[], name='a_cluster', relative=1, parent='', snapToObj='', pos=[], rot=[], scale=[], wimpMap='', v=0):
    '''
    Create a cluster deformer on given geo.

    @inParam geos - list, geometry, curve CV's, vertices or objects to apply cluster to
    @inParam name - string, cluster name
    @inParam relative - int, make cluster relative (you can move its parent without affecting the cluster) by using bindPreMatrix
    @inParam parent - string, parent the clusterHandle or cluster offset to this
    @inParam snapToObj - string, object or vertex to snap cluster offset to. 
    @inParam pos - list, translate coordinates for cluster offset
    @inParam rot - list, rotation coordinates for cluster offset
    @inParam scale - list, scale values for cluster offset
    @inParam wimpMap - string, wimp map for deformer, must be of type .wmp
    @inParam v - int, set visibility of clusterHandle

    @procedure rig.createCluster(geos=['rope_geo'], name='rope_cluster', relative=1, parent='parent_offset', snapToObj=loc)
    '''
    #Check which geo exists.
    geo = []
    for g in geos:
        if mc.objExists(g):
            geo.append(g)
        else:
            print 'Object does not exist to apply cluster to - '+g

    #Create cluster on given geo.
    cluster = mc.cluster(geo, n=name)
    clusterHandle = cluster[1]

    #If offset name is given, create the cluster offset and find the cluster transforms.
    offset = mc.group(n=name.replace('_cluster', 'Cluster_offset'), em=1)
    mc.delete(mc.parentConstraint(clusterHandle, offset))
    mc.makeIdentity(offset, apply=1, t=1, r=1, s=1, n=0)
    mc.parent(clusterHandle, offset, a=0)

    if relative:
        mc.connectAttr(offset+'.worldInverseMatrix[0]', cluster[0]+'.bindPreMatrix')

    if snapToObj:
        if mc.objExists(snapToObj):
            if '.vtx[' in snapToObj:
                vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                mc.move(vtxPos[0], vtxPos[1], vtxPos[2], offset, r=1)
            else:
                mc.delete(mc.parentConstraint(snapToObj, offset))
        else:
            print snapToObj+' does not exist!'+offset+' not snapped to'+snapToObj
    
    #Move and rotate it differently because offset has had transforms frozen.
    if pos:
        loc = createLoc(name='loc', pos=pos, v=0)
        mc.delete(mc.pointConstraint(loc, offset))
        mc.delete(loc)
    if rot:
        loc = createLoc(name='loc', rot=rot, v=0)
        mc.delete(mc.orientConstraint(loc, offset))
        mc.delete(loc)
    if scale:
        mc.scale(scale[0],scale[1],scale[2], offset, ws=1)


    #Check if parent given.
    if parent:
        if mc.objExists(parent):
            #If parent exists, parent offset under parent.
            mc.parent(offset, parent)
        else:
            print 'Parent does not exist - '+parent

    #Check if wimpMap is given.
    if wimpMap:
        if mc.file(wimpMap, q=1, ex=1):
            #If wimp map exists, load the map.
            mc.wimpIO(node, f=wimpMap, load=1)
        else:
            print 'Wimp file does not exist - '+wimpMap

    clusterSet = mc.listConnections(cluster[0], destination=True, type='objectSet')[0]
    mc.rename(clusterSet, cluster[0]+'_clusterSet')  

    mc.setAttr(clusterHandle+'.v', v)

    return (clusterHandle, cluster[0], offset, clusterSet)




def createSculptDeformer(geos=[], name='sculpt', snapToObj='', trans=[], rot=[], scale=[], parent='', maxDisp=0.1, dropoffDistance=1.0, defOrder='default', consTo='', consType='parent', v=0):
    '''
    Create a sculpt deformer on given geo.

    @inParam geos - list, geometry to apply sculpt deformer to
    @inParam name - string, sculpt name 
    @inParam snapToObj - string, object or vertex to snap sculpt to. 
    @inParam trans - list, translate coordinates for sculpt 
    @inParam rot - list, rotation coordinates for sculpt 
    @inParam scale - list, scale values of sculpt 
    @inParam parent - string, parent the sculpt to this
    @inParam maxDisp - float, defines the maximum amount the sculpt object may move a point on an object which it is deforming
    @inParam dropoffDistance - float, specifies the distance from the surface of the sculpt object at which the sculpt object produces no deformation effect
    @inParam defOrder - string, deformation order of deformer. Choices are default, before, after, split, parallel
    @inParam consTo - string, object to constrain deformer handle to. If left blank, it wont get constrained
    @inParam consType - string, used with consTo flag. Type of constraint between consTo object and deformer handle, types are parent, point or orient
    @inParam v - int, visibility of sculpt

    @procedure rig.createSculptDeformer(geos=['head_geo'], name='L_eye_sculpt', snapToObj='L_eye_env', scale=[0.3,0.3,0.3], parent='parent_offset', maxDisp=0.1, dropoffDistance=1)
    '''
    
    if not geos:
        print 'No geometry given to create sculpt deformer on'
    else:
        for geo in geos:
            if not mc.objExists(geo):
                print 'Geometry does not exist '+geo

        if defOrder == 'default':
            sculpt = mc.sculpt(geos, n=name, mxd=maxDisp, dds=dropoffDistance)
        elif defOrder == 'before':
            sculpt = mc.sculpt(geos, n=name, mxd=maxDisp, dds=dropoffDistance)
        elif defOrder == 'after':
            sculpt = mc.sculpt(geos, n=name, mxd=maxDisp, dds=dropoffDistance)
        elif defOrder == 'split':
            sculpt = mc.sculpt(geos, n=name, mxd=maxDisp, dds=dropoffDistance)
        elif defOrder == 'parallel':
            sculpt = mc.sculpt(geos, n=name, mxd=maxDisp, dds=dropoffDistance)
        else:
            print defOrder+' deformation order does not exist! Choices are default, before, after, split or parallel.'

        mc.parent(sculpt[2], sculpt[1])

        nameString = name.split('_')    
        suffix = len(nameString[-1])
        sculpt[1] = mc.rename(sculpt[1], name[:-suffix]+'sculptor')

        if mc.objExists(parent):
            mc.parent(sculpt[1], parent)
        else:
            print 'Parent object does not exist - '+parent


        if snapToObj:
            if mc.objExists(snapToObj):
                if '.vtx[' in snapToObj:
                    vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                    mc.move(vtxPos[0], vtxPos[1], vtxPos[2], sculpt[1], r=1)
                else:
                    mc.delete(mc.parentConstraint(snapToObj, sculpt[1]))
            else:
                print snapToObj+' does not exist!'+sculpt[1]+' not snapped to'+snapToObj
        
        if trans:
            mc.move(trans[0],trans[1],trans[2], sculpt[1], ws=1)
        if rot:
            mc.rotate(rot[0],rot[1],rot[2], sculpt[1], ws=1)
        if scale:
            mc.scale(scale[0],scale[1],scale[2], sculpt[1], ws=1)
        

        if consTo:
            if mc.objExists(consTo):
                if consType == 'parent' or consType == 'parentConstraint':
                    mc.parentConstraint(consTo, sculpt[1], mo=1)
                elif consType == 'point' or consType == 'pointConstraint':
                    mc.pointConstraint(consTo, sculpt[1], mo=1)
                elif consType == 'orient' or consType == 'orientConstraint':
                    mc.orientConstraint(consTo, sculpt[1], mo=1)

                mc.scaleConstraint(consTo, sculpt[1], mo=1)
            else:
                print consTo+' object to constrain sculpt to does not exist'

        if v!=1:
            mc.setAttr(sculpt[1]+'.v', 0)

        sculptSet = mc.listConnections(sculpt, destination=1, type='objectSet')[0]
        mc.rename(sculptSet, name+'_sculptSet') 

        return sculpt




def createDnWrap(geos=[], obj='', name=''):
    '''
    Creates a dnWrap from obj to geo.

    @inParam geos - list, geo wrapped to obj
    @inParam obj - string, obj geo will be wrapped to
    @inParam name - string, name of dnWrap

    @procedure rig.createDnWrap(geos=['L_eye_geo'], obj='head_geo')
    '''
    if not mc.objExists(obj):
        mc.error(obj+' does not exist! @inParam obj: createDnWrap')

    for geo in geos:
        if mc.objExists(geo):
            mc.select(geo, obj, r=1)
            dnWrap = mm.eval('dnWrap')

            if name:
                mc.rename(dnWrap, name)
            else:
                mc.rename(dnWrap, geo+'_dnWrap')
        else:
            print geo+' does not exist! @inParam geos: createDnWrap'

    mc.select(cl=1)

    return dnWrap




def createTransformGeometryNode(inputGeo='', outputGeo='', name=''):
    '''
    Create a transform geometry node. Often used for cloth rigs because we need the geometry in worldSpace, an example of it's use is if some gemetry is 
    parentConstrained to something. When we cache it the geometry still contains those transforms and if we outMesh to inMesh, the resulting geo will not
    be in the correct worldSpace. Transform geometry acts almost like a cluster where it transforms the vertices.

    @inParam inputGeo - string, name of input geometry which has transforms that will be an input to the transformGeometry node
    @inParam outputGeo - string, name of output geometry transformGeometry node will be applied to 
    @inParam name - name of transformGeometry node created

    @procedure rig.createTransformGeometryNode(inputGeo='L_eye_mesh', outputGeo='L_eye_geo', name='L_eye_transformGeometry')
    '''       
    if mc.objectExists(inputGeo):
        print inputGeo+' does not exist! @inParam inputGeo: createTransformGeometryNode'

    if not mc.objectExists(outputGeo):
        print outputGeo+' does not exist! @inParam outputGeo: createTransformGeometryNode'

    if not name:
        name = inputGeo.replace('_geo', '_transformGeometry')

    transformNode = mc.createNode('transformGeometry', n=name)
    mc.connectAttr(inputGeo+'.worldMatrix[0]', transformNode+'.transform')
    mc.connectAttr(inputGeo+'.outMesh', transformNode+'.inputGeometry')    

    outputGeoShape = mc.listRelatives(outputGeo, s=1)[0]
    mc.connectAttr(transformNode+'.outputGeometry', outputGeoShape+'.inMesh')

    return transformNode




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#----------- ========[ BLENDSHAPES ]======== ----------#
#------------------------------------------------------#
def setupCorrective(targets=[], corrective='', blendShape='', geo='', deltaParent='', targetDrivers=[]):
    '''
        Setup a corrective shape by creating a delta between given targets (see notes below).

        @inParam targets - list, corrective shape target names, if none given, it will work out the targets based on the name of the corrective flag
        @inParam corrective - string, corrective blendshape
        @inParam blendShape - string, name of blendshape node
        @inParam geo - string, name of geometry the blendshape is applied to
        @inParam deltaParent - string, parent of delta bs that will be created usually same parent of targets, if none given it will be parented where the corrective is
        @inParam targetDrivers - list, driver attribute of target. The delta target created will be driven by this attribute. Usually the delta will be driven by value of the targets,
                                however some targets are always switched on like the lipCornerPuller_bs because it's driven differently to other targets - the weightMap is multiplied 
                                by a wimpMult node which comes off and on, driven by a blendShape holder attribute. So instead of driving the delta value by the target values, use this 
                                flag to give it an attribute that drives the target value, e.g. the blendshape holder attribute.

        @procedure rig.setupCorrective(corrective='lipPuckerer_lipPursing_bs', blendShape='head_dnBlendShape', geo='head_geo')
    
        @notes
        A - lipCornerPuller
        B - upperLipRaiser
        Corrective blendshape
        Delta - difference between corrective and the 2 shapes combined (combo)

        Combo = A + B
        Delta = Corrective - Combo

        The delta becomes a blendshape that comes on based on the lowest value of either blendshape.
    '''    
    if not targets:
        names = corrective.replace('_bs', '')
        names = names.split('_')
        for name in names:
            targets.append(name+'_bs')

    for target in targets:
        if not mc.objExists(blendShape+'.'+target):
            print target+' does not exist! @inParam targets'

    if not mc.objExists(corrective):
        print corrective+' does not exist! @inParam corrective' 
       
    if not mc.objExists(blendShape):
        print blendShape+' does not exist! @inParam blendShape'

    if not mc.objExists(geo):
        print geo+' does not exist! @inParam geo'

    if targetDrivers:
        for targetDriver in targetDrivers:
            if not mc.objExists(targetDriver):
                print targetDriver+' does not exist! @inParam targetDrivers'


    for target in targets: 
        if not mc.objExists(blendShape+'.'+target):
            print blendShape+'.'+target+' does not exist!'

        connection = mc.listConnections(blendShape+'.'+target, source=1, destination=0, p=1)
        if connection:
            mc.setAttr(connection[0], 1)
        else:
            mc.setAttr(blendShape+'.'+target, 1)

    combo = mc.duplicate(geo, n=corrective.replace('_bs', '_combo_bs'))[0]

    for target in targets:  
        connection = mc.listConnections(blendShape+'.'+target, source=1, destination=0, p=1)
        if connection:
            mc.setAttr(connection[0], 0)
        else:
            mc.setAttr(blendShape+'.'+target, 0)

    mm.eval('dnBlendShape -addTarget -name "'+combo+'" "'+blendShape+'" "'+combo+'"')
    mc.setAttr(blendShape+'.'+combo, -1)
    mc.setAttr(blendShape+'.'+corrective, 1)

    delta = mc.duplicate(geo, n=corrective.replace('_bs', '_delta_bs'))[0]
    if deltaParent:
        if mc.objExists(deltaParent):
            mc.parent(delta, deltaParent)
        else:
            print deltaParent+' does not exist! @inParam deltaParent'
    else:
        deltaParent = mc.listRelatives(corrective, p=1)[0]
        mc.parent(delta, deltaParent)

    mc.setAttr(blendShape+'.'+combo, 0)
    mc.setAttr(blendShape+'.'+corrective, 0)
    mm.eval('dnBlendShape -removeTarget -name "'+combo+'" "'+blendShape+'" "'+combo+'"')
    mc.delete(combo)
    mm.eval('dnBlendShape -removeTarget -name "'+corrective+'" "'+blendShape+'" "'+corrective+'"')

    mm.eval('dnBlendShape -addTarget -name "'+delta+'" "'+blendShape+'" "'+delta+'"')

    if len(targets) == 2:
        deltaCond = mc.createNode('condition', n=delta.replace('_bs', '_condition'))

        if targetDrivers:
            mc.connectAttr(blendShape+'.'+targetDriver[0], deltaCond+'.firstTerm')
            mc.connectAttr(blendShape+'.'+targetDriver[0], deltaCond+'.colorIfTrueR')
            mc.connectAttr(blendShape+'.'+targetDriver[1], deltaCond+'.secondTerm')
            mc.connectAttr(blendShape+'.'+targetDriver[1], deltaCond+'.colorIfFalseR')
        else:
            mc.connectAttr(blendShape+'.'+targets[0], deltaCond+'.firstTerm')
            mc.connectAttr(blendShape+'.'+targets[0], deltaCond+'.colorIfTrueR')
            mc.connectAttr(blendShape+'.'+targets[1], deltaCond+'.secondTerm')
            mc.connectAttr(blendShape+'.'+targets[1], deltaCond+'.colorIfFalseR')
        mc.setAttr(deltaCond+'.operation', 4)
        mc.connectAttr(deltaCond+'.outColorR', blendShape+'.'+delta)

    mc.setAttr(delta+'.v', 0)




def createDnBlendShape(targets=[], geo='', ref='', name='name_dnBlendShape', mode=2, attr='', inBetween={}):
    '''
    Creates a dnBlendshape.

    @inParam targets - list, target geo for blendshape
    @inParam geo - string, geo to apply dnBlendshape to
    @inParam ref - string, name of reference shape to be used
    @inParam name - string, name of dnBlendshape
    @inParam mode - int, dnBlendshape mode, 0 - world, 1 - local, 2 - tangent
    @inParam attr - string, control attribute to connect to dnBlendshape target envelope
    @inParam inBetween - dictionary, define target and inBetween shapes to add as inBetweens, also define the inBetween position e.g. {'jawOpen_bs':[['jawOpen_25_bs', 0.25], ['jawOpen_50_bs', 0.5], ['jawOpen_75_bs', 0.75]]}

    @procedure rig.createDnBlendShape(targets=[bshp], geo=geo, ref=bsRef, name=geo+'_dnBlendShape', attr=bshpAttr, mode=1)
    '''
    mc.select(targets, geo, r=1)
    dnBlendShape = mm.eval('dnBlendShape')[0]
    dnBlendShape = mc.rename(dnBlendShape, name)
    mc.select(cl=1)

    if ref:
        refMeshShape = mc.connectionInfo(dnBlendShape+'.inputRefMesh[0].refMesh', sourceFromDestination=1)
        refMeshShape = refMeshShape.split('.')[0]

        refShape = mc.listRelatives(ref, s=1)[0]
        if refMeshShape != refShape:
            mc.delete(refMeshShape)
            mc.connectAttr(refShape+'.worldMesh[0]', dnBlendShape+'.inputRefMesh[0].refMesh')
    else:
        refMeshShape = mc.connectionInfo(dnBlendShape+'.inputRefMesh[0].refMesh', sourceFromDestination=1)
        refMeshShape = refMeshShape.split('.')[0]
        refMeshShape = mc.rename(refMeshShape, dnBlendShape+'ReferenceShape')

    for target in targets:
        mc.setAttr(dnBlendShape+'.'+target, 1)
        mc.setAttr(dnBlendShape+'.deformationSpace', mode)

        if attr:
            mc.connectAttr(attr, dnBlendShape+'.'+target)

    if inBetween:
        for target,inBetweens in inBetween.iteritems():
            for inBetweenBs in inBetweens:
                mm.eval('dnBlendShape -addTarget -name "'+inBetweenBs[0]+'" -inBetween -target "'+target+'" -position '+inBetweenBs[1]+' '+dnBlendShape+' "'+inBetweenBs[0]+'"')


    return dnBlendShape




def mirrorBlendShape(targets=[], geo=''):
    '''
    Mirrors a blendshape from L to R or R to L.

    @inParam targets - list, target geo for blendshape
    @inParam geo - string, geo to apply dnBlendshape to
    
    @procedure rig.mirrorBlendShape(targets=[bshp], geo='body_geo')

    @ToDo - Make deleting wrap ref not include wrap ref meshes with connections
    '''
    mirrorBshps = []
                

    for target in targets:
        if not mc.listRelatives(target, s=1):
            for obj in mc.listRelatives(target, ad=True, type='transform'):
                if mc.listRelatives(obj, s=1):
                    targets.append(obj)
            targets.remove(target)


    if not mc.objExists(geo):
        print geo +' does not exist! @inParam geo - mirrorBlendShape'
    else:
        for target in targets:
            if not mc.objExists(target):
                targets.remove(target)
                print target +' does not exist! @inParam targets - mirrorBlendShape'
            else:
                trans = getTransforms(obj=target, attrType='getAttr')
                setTransforms(obj=target, t=[0,0,0], r=[0,0,0])

                baseGeo = mc.duplicate(geo, n='base_geo')[0]
                mc.select(target, baseGeo, r=1)
                dnBlendShape = mm.eval('dnBlendShape')[0]
                mc.setAttr(baseGeo+'.sx', -1)

                mc.select(geo, baseGeo, r=1)
                wrap = mm.eval('dnWrap')
                mc.setAttr(dnBlendShape+'.'+target, 1)


                if target[0:2] == 'L_':
                    mirrorBs = mc.duplicate(geo, n=target.replace('L_', 'R_'))[0]
                elif target[0:2] == 'R_':
                    mirrorBs = mc.duplicate(geo, n=target.replace('R_', 'L_'))[0]
                else:
                    mirrorBs = mc.duplicate(geo)[0]

                mc.setAttr(wrap+'.envelope', 0)
                mc.delete(wrap, baseGeo)

                mirrorBshps.append(mirrorBs)

                setTransforms(obj=target, t=trans['t'], r=trans['r'])
                setTransforms(obj=mirrorBs, t=trans['t'], r=trans['r'])

    wrapNodesToDelete = mc.ls('dnWrap*RefMesh*')
    if wrapNodesToDelete:
        mc.delete(wrapNodesToDelete)

    for mirrorBs in mirrorBshps:
        print mirrorBs+' generated successfully!!'

    print '#----------[ Mirror Blendshapes Completed ]----------#'

    return mirrorBshps



def updateBlendShapesToNewModel(oldGeo='', newGeo='', targets=[], deleteOldTargets=0):
    '''
    Use this procedure to update blendshapes from oldGeo to newGeo, great if there is a model update for example.

    @inParam oldGeo - string, old geometry that the targets were created from
    @inParam newGeo - string, new geometry the targets need to match to
    @inParam targets - list, blendshapes to update to newGeo
    @inParam deleteOldTargets - int, deletes old target if set to 1

    @procedure rig.updateBlendShapesToNewModel(oldGeo='body_geoOLD', newGeo='body_geo', targets=['muscle_blendshapes_grp'], deleteOldTargets=1)
    '''

    if mc.objExists(oldGeo):
        if mc.objExists(newGeo):
            blendShape = mc.blendShape(newGeo, oldGeo, n='update_blendShape')[0]
            mc.setAttr(blendShape+'.'+newGeo, 1)

            for target in targets:
                if not mc.listRelatives(target, s=1):
                    targets.remove(target)

                    for targ in mc.listRelatives(target, c=1):
                        if mc.listRelatives(targ, s=1):
                            targets.append(targ)

            targetsUpdated = []
            for i,target in enumerate(targets):
                if mc.objExists(target):
                    mc.blendShape(blendShape, e=1, t=(oldGeo, i+1, target, 1), tc=0)
                    mc.setAttr(blendShape+'.'+target, 1)

                    oldGeoPolyCount = mc.polyEvaluate(oldGeo, f=1)
                    targetGeoPolyCount = mc.polyEvaluate(target, f=1)

                    targetOld = mc.rename(target, target+'OLD')

                    if oldGeoPolyCount == targetGeoPolyCount:
                        target = mc.duplicate(oldGeo, n=target)[0]

                        targetOldPos = mc.xform(targetOld, q=1, ws=1, t=1)
                        targetOldRot = mc.xform(targetOld, q=1, ws=1, ro=1)
                        mc.move(targetOldPos[0], targetOldPos[1], targetOldPos[2], target, ws=1)
                        mc.rotate(targetOldRot[0], targetOldRot[1], targetOldRot[2], target, ws=1)

                        mc.setAttr(blendShape+'.'+target, 0)

                        if mc.listRelatives(targetOld, p=1):
                            mc.parent(target, mc.listRelatives(targetOld, p=1)[0])
                    else:
                        target = mc.duplicate(targetOld, n=target)[0]

                        inBetweenTarget = mc.duplicate(oldGeo, n=target+'inBetween')[0]
                        mc.setAttr(blendShape+'.'+target, 0)

                        inBetweenBlendShape = mc.blendShape(inBetweenTarget, target, n=target+'_inbetween_blendShape', tc=0)[0]
                        mc.setAttr(inBetweenBlendShape+'.'+inBetweenTarget, 1)
                        mc.delete(target, ch=1)

                        mc.delete(inBetweenTarget)

                    targetShape = mc.listRelatives(target, s=1)[0]
                    if mc.objExists(targetShape+'Orig'):
                        mc.delete(targetShape+'Orig')

                    if deleteOldTargets:
                        mc.delete(targetOld)


                    targetsUpdated.append(target)
                else:
                    print target+' does not exist! @inParam targets - updateBlendShapesToNewModel()' 

            mc.setAttr(blendShape+'.envelope', 0)
            mc.delete(blendShape)

            print '\n---------[ The Following Blendshapes Updated Successfully! ]-----------'
            for target in targetsUpdated:
                print target+' updated!'

            #return targetsUpdated
        else:
            print newGeo+' does not exist! @inParam newGeo - updateBlendShapesToNewModel()' 
    else:
        print oldGeo+' does not exist! @inParam oldGeo - updateBlendShapesToNewModel()'

      


def BSpiritCorrectiveShape():
    '''
    This creates a first iput blendshape from a shape created after a skinCluster. Imagine a knee rotating, and you create a shape after the skinCluster. 
    The blendshape doesn't work as well after the blendshape as it does before due to rotations. So to create the shape at the bind pose before the skinCluster:
    Pose the rig, turn off all deformations except for skinCluster. Duplicate the geo and create sculpt. Then pose rig back to bind pose. Select the blendshape 
    vertices, then select the bind pose rig (with skincluster) and run this.

    @procedure rig.BSpiritCorrectiveShape()
    '''
    mm.eval('source "/hosts/katevale/user_data/scripts/gtRig/extractDelta.mel"')
    mm.eval('BSpiritCorrectiveShape()')


























































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#-------------- ========[ CONSTRAINTS ]======== -------------#
#------------------------------------------------------------#

def constrainGeometry(dictionary, scaleCons=1):
    '''
    Parent and scale constraint list of geometry (value) to joint (key) of dictionary.

    @inParam dictionary - dict, key is usually joint, value list of geometry or groups to constrain
    @inParam scaleCons - int, if true apply a scaleConstraint, if false it wont

    @procedure rig.constrainGeometry(consDict)
               consDict= {'_arm_wrist_env': ['_forearmWrist_grp', '_hand_grp'],
                          '_digit_thumb_loc': ['_thumbFinger01_grp']}
    '''

    #Parent and scale constrain the geo to joints. Iterate through dictionary.
    for env, geos in dictionary.iteritems():
        #Iterate through list of geometry.
        for geo in geos:
            #If joint (key) begins with an underscore, we will constrain for left and right joints by adding a prefix.
            if env[0] == '_':
                for side in ['L', 'R']:
                    joint = side+env

                    #Check if the joint exists.
                    if mc.objExists(joint):
                        #If geo starts with an underscore, also add the side prefix for left and right.
                        if geo[0] == '_':
                            geo = side+geo

                        #If geo exists, constrain it.
                        if mc.objExists(geo):
                            #Parent and scale constraint geo to joint.  
                            mc.parentConstraint(joint, geo, mo=True)
                            if scaleCons == 1:
                                mc.scaleConstraint(joint, geo, mo=True)    
                        else:
                            print geo+' does not exist (added side prefix)! Not constrained to '+joint
                    else:
                        print joint+' does not exist (added side prefix)!'
            else:
                #Check if the joint exists.
                if mc.objExists(env):
                    #If geo starts with an underscore, also add a side prefix for left and right.
                    if geo[0] == '_':
                        for side in ['L', 'R']:
                            geo = side+geo

                            #If geo exists, constrain it.
                            if mc.objExists(geo):
                                #Parent and scale constraint geo to joint.
                                mc.parentConstraint(env, geo, mo=True)
                                if scaleCons == 1:
                                    mc.scaleConstraint(env, geo, mo=True)
                            else:
                                print geo+' does not exist (added side prefix)! Not constrained to '+env
                    else:
                        #If geo exists, constrain it.
                        if mc.objExists(geo):
                            #Parent and scale constraint geo to joint.
                            mc.parentConstraint(env, geo, mo=True)
                            if scaleCons == 1:
                                mc.scaleConstraint(env, geo, mo=True)
                        else:
                            print geo+' does not exist (added side prefix)! Not constrained to '+env
                else:
                    print env+' does not exist (added side prefix)!'



def meshConstraint(mesh='jacket_geo', objs=['button_001_loc'], geoFlag=1, skipRot=0):
    '''
    Creates a dnMeshConstraint from mesh to object.

    @inParam mesh - string, geo to apply dnMeshConstraint from
    @inParam objs - list, list of objects to apply dnMeshConstraint from mesh to obj
    @inParam geoFlag - int, if running postScript without geometry, use this flag to skip proc
    @inParam skipRot - int, skip dnMeshConstraint rotation value if on

    @procedure rig.meshConstraint(mesh='jacket_geo', objs=['button_001_geo'], skipRot=0)
    '''
    if geoFlag == 1:
        for obj in objs:
            mc.select(mesh, obj, r=1)

            if skipRot == 1:
                mm.eval('dnMeshConstraint -sr')
            else:
                mm.eval('dnMeshConstraint')



























































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#--------------- ========[ LOCATORS ]======== ---------------#
#------------------------------------------------------------#


def createLoc(name='loc', pos=[], rot=[], scale=[1,1,1], snapToObj='', parent='', v=1, dispType=0, attrsToLock=[], setAttr=0):
    '''
    Create a spaceLocator.

    @inParam name - string, name of locator to be created
    @inParam pos - list, position of locator
    @inParam rot - list, rotation of locator
    @inParam scale - list, scale of locator
    @inParam snapToObj - string, if object given it will snap to it
    @inParam parent - string, parent locator uder this object
    @inParam v - int, set visibility of locator
    @inParam dispType - int, display type of locator, 0-normal 1-template 2-reference
    @inParam attrsToLock - list, attributes of loc to lock
    @inParam setAttr - int, if 1 will set the position and rotation values as cb, not as relative.

    @procedure rig.createLoc(name='loc', snapToObj='cane_ctrl', parent='', scale=[0.2,0.2,0.2], v=0)
    '''
    loc = mc.spaceLocator(n=name)[0]

    if snapToObj:
        if mc.objExists(snapToObj):
            if '.vtx[' in snapToObj:
                vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                mc.move(vtxPos[0], vtxPos[1], vtxPos[2], loc, r=1)
            else:
                mc.delete(mc.parentConstraint(snapToObj, loc))
        else:
            print snapToObj+' does not exist! Could not snap object.'
    
    if pos:
        if setAttr:
            mc.setAttr(loc+'.tx', pos[0])
            mc.setAttr(loc+'.ty', pos[1])
            mc.setAttr(loc+'.tz', pos[2])
        else:
            mc.move(pos[0], pos[1], pos[2], loc, r=1)
    if rot:
        if setAttr:
            mc.setAttr(loc+'.rx', rot[0])
            mc.setAttr(loc+'.ry', rot[1])
            mc.setAttr(loc+'.rz', rot[2])
        else:
            mc.rotate(rot[0], rot[1], rot[2], loc, r=1)

    mc.setAttr(loc+'.localScaleX', scale[0])
    mc.setAttr(loc+'.localScaleY', scale[1])
    mc.setAttr(loc+'.localScaleZ', scale[2])

    if parent:
        mc.parent(loc, parent)

        if setAttr:
            mc.setAttr(loc+'.tx', pos[0])
            mc.setAttr(loc+'.ty', pos[1])
            mc.setAttr(loc+'.tz', pos[2])

            mc.setAttr(loc+'.rx', rot[0])
            mc.setAttr(loc+'.ry', rot[1])
            mc.setAttr(loc+'.rz', rot[2])

    if dispType == 1:
        mc.setAttr(loc+'.overrideEnabled', 1)
        mc.setAttr(loc+'.overrideDisplayType', 1)
    elif dispType == 2:
        mc.setAttr(loc+'.overrideEnabled', 1)
        mc.setAttr(loc+'.overrideDisplayType', 2)

    mc.setAttr(loc+'.v', v)

    if attrsToLock:
        lockAndHideAttr(loc, attrsToLock)

    return loc





#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#-------------- ========[ TRANSFORMS ]======== --------------#
#------------------------------------------------------------#

def createOffset(obj='', name='offset', stack=0, stackNames=[], parent='', snapToObj='', pos=[], rot=[], scale=[], parentObjOrder='before'):
    '''
    Creates a group above a given transform (obj) and parents the transform under the group. 

    @inParam obj - string, object to create offset group for. If none given, it will create an empty offset.
    @inParam name - string, name of offset group, if none given, it will create a smart name based upon the obj flag e.g. head_ctrl ---> headCtrl_offset
    @inParam stack - int, number of additional offset groups, so if stack=1, it will create 2 offsets
    @inParam stackNames - list, if stack groups are created (using stack flag), you can override the name using this flag. Only give the suffix, so ctrl.replace('_ctrl', stackNames) - e.g. stackNames='Zero_offset'
    @inParam parent - string, offset will be parented under this, if none given, it will automatically be parented under the object parent
    @inParam snapToObj - string, object to snap joint to and copy rotation values. If object is not given, this proc will use the pos and rot flags
    @inParam pos - list, position of control
    @inParam rot - list, rotation of control
    @inParam scale - list, scale of control
    @inParam parentObjOrder - string, parent the object given before or after moving the offset, options are 'before' or 'after'

    @procedure ctrl, ctrlOffset, ctrlStackOffset, ctrlOffsets = rig.createOffset(obj='head_ctrl', stack=1, stackNames=['Zero_offset'], parent='spine_ctrl', snapToObj=loc)
    '''
    offsets = []
    for i in range(stack+1):  
        if i == 0:
            if obj:
                objSplit = obj.split('_')
                num = len(objSplit[-1])
                groupName = obj[:-(num+1)]
                groupName = groupName + objSplit[-1].capitalize() + '_offset'
            else:
                groupName = name
        else:
            #If additional offset groups are created (stack>0)
            if stackNames:
                if i > len(stackNames):
                    if obj:
                        print 'Not enough stack names given must be same amount as stack- '+str(stack)
                        objSplit = obj.split('_')
                        num = len(objSplit[-1])
                        groupName = obj[:-(num+1)]
                        groupName = groupName + objSplit[-1].capitalize() + str(i) + '_offset'
                    else:
                        groupName = name+str(i)
                else:
                    if obj:
                        objSplit = obj.split('_')
                        num = len(objSplit[-1])
                        groupName = obj[:-(num+1)]
                        groupName = groupName + stackNames[i-1]
                    else:
                        groupName = stackNames[i-1]
            else:
                groupName = name+str(i)

        offset = mc.group(n=groupName, em=1)
        offsets.append(offset)

    for i,offset in enumerate(offsets):
        if i != 0:
            mc.parent(offsets[i], offsets[i-1])
        elif parent:
            if mc.objExists(parent):
                mc.parent(offset, parent)
            else:
                print parent+' does not exist, offset not parented!!'
        else:
            objParent = mc.listRelatives(obj, p=1)
            if objParent:
                mc.parent(offset, objParent[0])

    if parentObjOrder != 'after':
        if obj:
            if mc.objExists(obj):
                mc.parent(obj, offsets[-1])
            else:
                print obj+' does not exist!'

    if snapToObj:
        if mc.objExists(snapToObj):
            if '.vtx[' in snapToObj:
                vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                mc.move(vtxPos[0], vtxPos[1], vtxPos[2], offsets[0], r=1)
            else:
                mc.delete(mc.parentConstraint(snapToObj, offsets[0]))
        else:
            print snapToObj+' does not exist! '+offsets[0]+' not snapped to'+snapToObj + '@inParam snapToObj  def createOffset'
    else:
        mc.delete(mc.parentConstraint(obj, offsets[0]))

    if pos:
        mc.move(pos[0],pos[1],pos[2], offsets[0], ws=1)
    if rot:
        mc.rotate(rot[0],rot[1],rot[2], offsets[0], ws=1)
    if scale:
        mc.scale(scale[0],scale[1],scale[2], offsets[0], ws=1)

    if parentObjOrder == 'after':
        if obj:
            if mc.objExists(obj):
                mc.parent(obj, offsets[-1])
            else:
                print obj+' does not exist!'

    return offsets




def mirrorTransform(objects=[], side=1, axis='Y'):
    '''
    Mirror objects accross given axis. If side flag on, it will search for the opposite side object. Mostly used to mirror locators.

    @inParam objects - list, objects to be mirrored
    @inParam objects - list, objects to be mirrored
    @inParam axis - string, axis to mirror

    @procedure rig.mirrorTransform(objects=locs, side=1, axis='Y')
    '''
    if not objects:
        objects = mc.ls(sl=1)

    for obj in objects:
        if mc.objExists(obj):
            transform = getTransforms(obj=obj, attrType='getAttr')
            if side:
                if obj[0:2] == 'L_':
                    obj = obj.replace('L_', 'R_')
                elif obj[0:2] == 'R_':
                    obj = obj.replace('R_', 'L_')

            if mc.objExists(obj):
                if axis == 'Y' or axis == 'y':
                    mc.setAttr(obj+'.tx', (transform['t'][0]*-1))
                    mc.setAttr(obj+'.ty', transform['t'][1])
                    mc.setAttr(obj+'.tz', transform['t'][2])
                    mc.setAttr(obj+'.rx', transform['r'][0])
                    mc.setAttr(obj+'.ry', (transform['r'][1]*-1))
                    mc.setAttr(obj+'.rz', (transform['r'][2]*-1))
                elif axis == 'Z' or axis == 'z':
                    mc.setAttr(obj+'.tx', transform['t'][0])
                    mc.setAttr(obj+'.ty', transform['t'][1])
                    mc.setAttr(obj+'.tz', (transform['t'][2]*-1))
                    mc.setAttr(obj+'.rx', (transform['r'][0]*-1))
                    mc.setAttr(obj+'.ry', (transform['r'][1]*-1))
                    mc.setAttr(obj+'.rz', transform['r'][2])
                elif axis == 'X' or axis == 'x':
                    mc.setAttr(obj+'.tx', transform['t'][0])
                    mc.setAttr(obj+'.ty', (transform['t'][1]*-1))
                    mc.setAttr(obj+'.tz', transform['t'][2])
                    mc.setAttr(obj+'.rx', (transform['r'][0]*-1))
                    mc.setAttr(obj+'.ry', transform['r'][1])
                    mc.setAttr(obj+'.rz', (transform['r'][2]*-1))
                else:
                    print 'Mirror didn\'t happen. Please give axis as one of the following X,x,Y,y,Z,z'
            else:
                print 'Didn\'t find mirrored object '+obj
        else:
            print obj+' doesn\'t exist!'



def copyTransforms(sourceObj=[], destObj=[], attrType='world'):
    '''
    Copies translation, rotation, and scale values from one or multiple objects to another. If sourceObjects is just one object, it will copy to multiple dest objs.

    @inParam sourceObj - list, source objects to get transforms from
    @inParam destObj - list, destination objects to apply transforms to
    @inParam attrType - string, type of transform to apply. Chose between absolute, world or getAttr

    @procedure rig.copyTransforms(sourceObj=['petal01_plc_null'], destObj=['petal03_main_rigGuide'])
    '''
    for sourceObj,destObj in itertools.izip_longest(sourceObj, destObj, fillvalue=sourceObj[0]):      
        trans, rot, scale = ([] for i in range(3))

        if attrType is 'getAttr':
            for axis in ['x','y','z']:
                trans.append(mc.getAttr(sourceObj+'.t'+axis))
                rot.append(mc.getAttr(sourceObj+'.r'+axis))
                scale.append(mc.getAttr(sourceObj+'.s'+axis))
        elif attrType is 'absolute':
            trans = mc.xform(sourceObj, q=1, a=1, t=1)
            rot = mc.xform(sourceObj, q=1, a=1, ro=1)
            scale = mc.xform(sourceObj, q=1, a=1, s=1)
        elif attrType is 'world':
            trans = mc.xform(sourceObj, q=1, ws=1, t=1)
            rot = mc.xform(sourceObj, q=1, ws=1, ro=1)
            scale = mc.xform(sourceObj, q=1, ws=1, s=1)
        else:
            mc.error('attrType should be one of the following: getAttr, absolute or world')

        rad = ''
        if mc.attributeQuery('radius', node=sourceObj, ex=1) and mc.attributeQuery('radius', node=destObj, ex=1):
            rad = mc.getAttr(sourceObj+'.radius')

        for axis in ['x','y','z']:
            mc.setAttr(destObj+'.tx', trans[0])
            mc.setAttr(destObj+'.ty', trans[1])
            mc.setAttr(destObj+'.tz', trans[2])
            mc.setAttr(destObj+'.rx', rot[0])
            mc.setAttr(destObj+'.ry', rot[1])
            mc.setAttr(destObj+'.rz', rot[2])
            mc.setAttr(destObj+'.sx', scale[0])
            mc.setAttr(destObj+'.sy', scale[1])
            mc.setAttr(destObj+'.sz', scale[2])

        if mc.attributeQuery('radius', node=sourceObj, ex=1) and mc.attributeQuery('radius', node=destObj, ex=1):
            mc.setAttr(destObj+'.radius', rad)



def getTransforms(obj, attrType='world'):
    '''
    Returns translation, rotation, and scale values of an object.

    @inParam object - string, object to find transforms from
    @inParam attrType - string, type of transform to apply. Chose between absolute, world, getAttr or rp (rotate pivot)

    @procedure rig.getTransforms(obj='petal_geo', attrType='getAttr')
    '''
    transDict = {'t':[],
                 'r':[],
                 's':[]}

    if attrType is 'getAttr':
        for axis in ['x','y','z']:
            transDict['t'].append(mc.getAttr(obj+'.t'+axis))
            transDict['r'].append(mc.getAttr(obj+'.r'+axis))
            transDict['s'].append(mc.getAttr(obj+'.s'+axis))
    elif attrType is 'absolute':
        transDict['t'] = mc.xform(obj, q=1, a=1, t=1)
        transDict['r'] = mc.xform(obj, q=1, a=1, ro=1)
        transDict['s'] = mc.xform(obj, q=1, a=1, s=1)
    elif attrType is 'world':
        transDict['t'] = mc.xform(obj, q=1, ws=1, t=1)
        transDict['r'] = mc.xform(obj, q=1, ws=1, ro=1)
        transDict['s'] = mc.xform(obj, q=1, ws=1, s=1)
    elif attrType is 'rp' or attrType is 'rotatePivot':
        transDict['t'] = mc.xform(obj, q=1, rp=1)
    else:
        mc.error('attrType should be one of the following: getAttr, absolute, world or rp (rotatePivot)')

    return transDict



def setTransforms(obj, t=[], r=[], s=[], ls=[]):
    '''
    Sets transformation values of an object.

    @inParam obj - string, object to set transforms to
    @inParam t - list, translation values to set
    @inParam r - list, rotation values to set
    @inParam s - list, scale values to set
    @inParam ls - list, local scale values to set (for locators)

    @procedure rig.setTransforms(obj='petal_loc', t=[0,0,0], r=[0,0,0], s=[1,1,1])
    '''
    if t:
        if not mc.getAttr(obj+'.tx', lock=1):  
            mc.setAttr(obj+'.tx', t[0])
        if not mc.getAttr(obj+'.ty', lock=1):  
            mc.setAttr(obj+'.ty', t[1])
        if not mc.getAttr(obj+'.tz', lock=1):  
            mc.setAttr(obj+'.tz', t[2])
    if r:
        if not mc.getAttr(obj+'.rx', lock=1):  
            mc.setAttr(obj+'.rx', r[0])
        if not mc.getAttr(obj+'.ry', lock=1):  
            mc.setAttr(obj+'.ry', r[1])
        if not mc.getAttr(obj+'.rz', lock=1):  
            mc.setAttr(obj+'.rz', r[2])
    if s:
        if not mc.getAttr(obj+'.sx', lock=1):  
            mc.setAttr(obj+'.sx', s[0])
        if not mc.getAttr(obj+'.sy', lock=1):  
            mc.setAttr(obj+'.sy', s[1])
        if not mc.getAttr(obj+'.sz', lock=1):  
            mc.setAttr(obj+'.sz', s[2])
    if ls:
        if not mc.getAttr(obj+'.localScaleX', lock=1):  
            mc.setAttr(obj+'.localScaleX', ls[0])
        if not mc.getAttr(obj+'.localScaleY', lock=1):  
            mc.setAttr(obj+'.localScaleY', ls[1])
        if not mc.getAttr(obj+'.localScaleZ', lock=1):  
            mc.setAttr(obj+'.localScaleZ', ls[2])


def setTransformLimits(obj, transform=[], value=[0,0,0,0]):
    '''
    Sets transform limit values for the trasnforms given of an object (usually a ctrl). The first two values of the values parameter are the min and max values.
    The last two are the enable transformLimits value (check box in channel box). For example, if ty=[0,1,0,1] - the minimum transform is set to 0, max is 1, but
    only the max transform limit is enabled, so the object can still have a negative ty value.

    @inParam obj - string, object to set transform limits for
    @inParam transform - list, list of transforms to set transform limit for e.g. [tx,ry,sz]
    @inParam value - list, values for the tranformLimits command - [min, max, enableMin, enableMax]

    @procedure rig.setTransformLimits(obj='sneerUp_ctrl', transform=['tx'], value=[0,0.12,1,1])
    '''
    
    for t in transform:
        if t == 'tx':
            mc.transformLimits(obj, tx=[value[0],value[1]], etx=(value[2],value[3]))
        if t == 'ty':
            mc.transformLimits(obj, ty=[value[0],value[1]], ety=(value[2],value[3]))
        if t == 'tz':
            mc.transformLimits(obj, tz=[value[0],value[1]], etz=(value[2],value[3]))
        if t == 'rx':
            mc.transformLimits(obj, rx=[value[0],value[1]], erx=(value[2],value[3]))
        if t == 'ry':
            mc.transformLimits(obj, ry=[value[0],value[1]], ery=(value[2],value[3]))
        if t == 'rz':
            mc.transformLimits(obj, rz=[value[0],value[1]], erz=(value[2],value[3]))
        if t == 'sx':
            mc.transformLimits(obj, sx=[value[0],value[1]], esx=(value[2],value[3]))
        if t == 'sy':
            mc.transformLimits(obj, sy=[value[0],value[1]], esy=(value[2],value[3]))
        if t == 'sz':
            mc.transformLimits(obj, sz=[value[0],value[1]], esz=(value[2],value[3]))




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#---------------- ========[ NODES ]======== ---------------#
#------------------------------------------------------------#

def createMultiplexValue(name, selector, valueIn, valueOutAttr):
    '''
    Creates a dnMultiplexValue node. Usually used for switches, for instance spaceswitching.
    This node has 2 inputs, selector and valueIn. The many outputs can connect to what you like. The value of valueIn is passed to the output index chosen by
    the selector. If selector is not an integer value, linearly weighted percentages of the valueIn input are passed to the two output indices closest to the
    selector value. e.g. if selector is 1.4, 60% of valueIn is passed through to valueOut1, and 40% of valueIn is passed through to valueOut2.

    @inParam name - string, name of the dnMultiplexValue node
    @inParam selector - string, selector value, pass it an object attribute/output usually an enum attribute, 0 ---> valueOut[0],  1 ---> valueOut[1]
    @inParam valueIn - float, the value that will be passed to the selected valueOut[]
    @inParam valueOutAttr - list, list of object attributes the valueOut[] of the dnMultiplexValue will connect to. Make sure the list is in correct order
    
    @procedure rig.createMultiplexValue(name='sail_dnMultiplexValue', selector='ctrl.spaceSwitch', valueIn=1, valueOutAttr=['offset_parentConstraint1.sail_ctrlW0', 'offset_parentConstraint1.worldSpace_nullW1'])
    '''
    #Create dnMultiplex node, connect the selector and set the valueIn.
    multiplexNode = mc.createNode('dnMultiplexValue', n=name)
    mc.connectAttr(selector, multiplexNode+'.selector')
    mc.setAttr(multiplexNode+'.valueIn', valueIn)

    #Connect the outValues to the object attribute in valueOutAttr.
    for i,attr in enumerate(valueOutAttr):
        #Split up the object and attribute.
        attrSplit = attr.split('.')
        if mc.attributeQuery(attrSplit[1], node=attrSplit[0], ex=1):
            #If the object attribute exists, connect the valueOut to it.
            mc.connectAttr(multiplexNode+'.valueOut['+str(i)+']', attr)




def createConditionNode(firstTerm, secondTerm, colorIfTrue, colorIfFalse, name='awesome_condNode', operation='equal', output='', reverse=''):
    '''
    Create a condition node. 

    @inParam name - string, name of condition node
    @inParam operation - string, operation of condition node, choices are 'equal', 'notEqual', 'greaterThan', 'greaterOrEqual', 'lessThan', 'lessOrEqual'
    @inParam output - string, attribute to connect condition node output to
    @inParam reverse - string, if reverse attribute given, a reverse node will be created for the output and connected to this atrribute
    @inParam firstTerm - string/float, first term attribute of condition node
    @inParam secondTerm - string/float, second term attribute of condition node
    @inParam colorIfTrue - string/float, colour if true attribute of condition node
    @inParam colorIfFalse - string/float, colour if false attribute of condition node

    @procedure rig.createConditionNode(name='inTransform_condNode', firstTerm='enterprise_connect_inTransform.tx', secondTerm=0, operation='notEqual', colorIfTrue=1, colorIfFalse=0, output=parentConstraint+'.enterprise_connect_inTransformW0', reverse=parentConstraint+'.path_root_inTransformW1')
    '''

    condNode = mc.createNode('condition', n=name)

    if type(firstTerm) is str:
        mc.connectAttr(firstTerm, condNode+'.firstTerm')
    else:
        mc.setAttr(condNode+'.firstTerm', firstTerm)

    if type(secondTerm) is str:
        mc.connectAttr(secondTerm, condNode+'.secondTerm')
    else:
        mc.setAttr(condNode+'.secondTerm', secondTerm)

    if type(colorIfTrue) is str:
        mc.connectAttr(colorIfTrue, condNode+'.colorIfTrueR')
    else:
        mc.setAttr(condNode+'.colorIfTrueR', colorIfTrue)

    if type(colorIfFalse) is str:
        mc.connectAttr(colorIfFalse, condNode+'.colorIfFalseR')
    else:
        mc.setAttr(condNode+'.colorIfFalseR', colorIfFalse)

    op = 0
    if operation == 'notEqual':
        op = 1
    elif operation == 'greaterThan':
        op = 2
    elif operation == 'greaterOrEqual':
        op = 3
    elif operation == 'lessThan':
        op = 4
    elif operation == 'lessOrEqual':
        op = 5
    mc.setAttr(condNode+'.operation', op)


    if output:
        if mc.objExists(output):
            mc.connectAttr(condNode+'.outColorR', output)
        else:
            print output+' does not exist! @output createConditionNode'
    
    if reverse:
        if mc.objExists(reverse):
            reverseNode = mc.shadingNode('reverse', asUtility=1, n=condNode+'_reverse')
            mc.connectAttr(condNode+'.outColorR', reverseNode+'.inputX')
            mc.connectAttr(reverseNode+'.outputX', reverse)
        else:
            print reverse+' does not exist! @reverse createConditionNode'

    return condNode





def createNegPosSwitch(attr='', outputPos='', outputNeg=''):
    '''
    Creates a negative positive switch and provides two outputs. For example the control attribute provided has a minimum -1 and max 1, the attribute can control one 
    output between 0 to 1 and another output between -1 to 0 but will always provide a positive value, i.e if the ctrl attribute is -0.5, it will output 0.5 to the second 
    output but 0 to the first. An example of this being used is an eye dilation attribute controlling 2 blendshapes, one is dilated the other contracted. 

    @inParam attr - string, attribute to control switch
    @inParam outputPos - string, connect output positive value to this
    @inParam outputNeg - string, connect output negative value to this
    
    @procedure rig.createNegPosSwitch(attr=bshpAttr, outputPos=eyeWidenBshp, outputNeg=eyeDilateBshp)
    '''
    attrName = attr.split('.')[1]

    posCondNode = mc.createNode('condition', n=attrName+'_pos_condition')
    mc.connectAttr(attr, posCondNode+'.firstTerm')
    mc.setAttr(posCondNode+'.operation', 2)
    mc.connectAttr(attr, posCondNode+'.colorIfTrueR')
    mc.connectAttr(posCondNode+'.outColorR', outputPos)
    mc.setAttr(posCondNode+'.colorIfFalseR', 0)


    multNode = mc.shadingNode('multiplyDivide', asUtility=1, n=attrName+'_neg_mult')
    mc.connectAttr(attr, multNode+'.input1X')
    mc.setAttr(multNode+'.input2X', -1)

    negCondNode = mc.createNode('condition', n=attrName+'_neg_condition')
    mc.connectAttr(attr, negCondNode+'.firstTerm')
    mc.setAttr(negCondNode+'.operation', 4)
    mc.connectAttr(multNode+'.outputX', negCondNode+'.colorIfTrueR')
    mc.connectAttr(negCondNode+'.outColorR', outputNeg)
    mc.setAttr(negCondNode+'.colorIfFalseR', 0)



def createDnMathOps(name='', operation=0, floatIn=[], angleIn=[]):
    '''
    Adds a dnMathOp node and connects it to an offset parent of the controller for auto movement. Default is set to sine wave

    @inParam name - string, name of dnMathsOps node
    @inParam operation - int, type of math operation: 0-sin, 1-cos, 2-tan, 3-asin, 4-acos, 5-atan, 6-sqrt, 7-exp, 8-ln, 9-log2, 10-log10, 11-pow, 12-normalise, 13-hypot, 14-atanz, 15-modules, 16-abs
    @inParam floatIn - list, float x,y,z value of dnMathsOps node
    @inParam angleIn - list, angle a,b,c value of dnMathsOps node

    @procedure rig.createDnMathOps(name='noise_dnMathOps', operation=0, floatIn=[0,0,0], angleIn=[0,0,0])
    '''    
    mathNode = mc.createNode('dnMathOps', n=name)
    mc.setAttr(mathNode+'.operation', operation)

    mc.setAttr(mathNode+'.inFloatX', floatIn[0])
    mc.setAttr(mathNode+'.inFloatY', floatIn[1])
    mc.setAttr(mathNode+'.inFloatZ', floatIn[2])

    mc.setAttr(mathNode+'.inAngleA', angleIn[0])
    mc.setAttr(mathNode+'.inAngleB', angleIn[1])
    mc.setAttr(mathNode+'.inAngleC', angleIn[2])

    return mathNode



def createRemapNode(name='', inputValue='', position=[], value=[], interp=[1,1,1,1,1,1,1], outputAttr=''):
    '''
    Creates a remap node.

    @inParam name - string, name of remap node
    @inParam inputValue - string, input value of remap node
    @inParam position - list, selected position value of remap node
    @inParam value - list, selected value of remap node
    @inParam interp - list, interpolation value of remap node 0 - None, 1 - Linear, 2 - Smooth, 3 - Spline
    @inParam outputAttr - string, object attribute to connect output of remapNode to

    @procedure rig.createRemapNode(name='sail_remapValue', inputValue=ctrl+'.tx', position=[0,1], value=[0,1], outputAttr='sail_ctrl.attr')
    '''
    remapValue = mc.shadingNode('remapValue', asUtility=1, n=name)
    mc.connectAttr(inputValue, remapValue+'.inputValue')

    for i,pos in enumerate(position):
        mc.setAttr(remapValue+'.value['+str(i)+'].value_Position', pos)
        mc.setAttr(remapValue+'.value['+str(i)+'].value_FloatValue', value[i])
        mc.setAttr(remapValue+'.value['+str(i)+'].value_Interp', interp[i])

    if outputAttr:
        if mc.objExists(outputAttr):
            mc.connectAttr(remapValue+'.outValue', outputAttr)
        else:
            print outputAttr+' does not exist! @outputAttr: createRemapNode'

    return [remapValue, remapValue+'.outValue']
                


def createDistance(name='', obj1='', obj2='', parent=''):
    '''
    Create a distance node between two objects and connects scale of rig from the base_global_ctrl to it.

    @inParam name - string, name of distance node
    @inParam obj1 - string, first object
    @inParam obj2 - string, second object
    @inParam parent - string, parent distance node under this

    @procedure rig.createDistance(name='leg_distance', obj1='dist_001_loc', obj2='dist_002_loc', parent=otherNull)
    '''
    mc.distanceDimension(obj1, obj2)
    distance = mc.rename('distanceDimension1', name)+'Shape'
    distanceValue = mc.getAttr(distance+'.distance')
    mc.parent(name, parent)

    scaleDistNode = mc.shadingNode('multiplyDivide', asUtility=1, n=name+'_scale_multNode')
    mc.setAttr(scaleDistNode+'.operation', 2)
    mc.connectAttr(distance+'.distance', scaleDistNode+'.input1X')
    mc.connectAttr('base_global_ctrl.sx', scaleDistNode+'.input2X')

    return [scaleDistNode+'.outputX', distanceValue]




def addMath (sCtrl,tAttr, sFrequency=1,sAmplitude=1,sOffset=0, bConnectMult=True, sFrequencyMult=None, sAmplitudeMult=None):
    '''
        Adds a dnMathOp node and connects it to an offset parent of the controller for auto movement. Default is set to sine wave

        @inParam sCtrl - string, name of controller
        @inParam tAttr - tuple, attribues that will have auto movement
        @inParam sFrequency - string, frequency value scales wavelength
        @inParam sAmplitude - string, amplitude value
        @inParam sOffset - string, offset value                

        @procedure rig.addMath ('yardArmBot_main_ctrl',['rotateY','rotateX'],sAmplitude=3,sOffset=2)  
    '''    
    sCtrlName = sCtrl.replace('_ctrl','')
    #Insert Offset node
    sCtrlParent = mc.listRelatives (sCtrl,parent=True)[0]
    sOffsetParent = mc.createNode ('transform',n=sCtrlName+'Math_Offset')
    mc.parent (sOffsetParent,sCtrlParent,r=True)
    mc.parent (sCtrl,sOffsetParent,r=True)
    #Add Math Attrs to the control
    addEnumAttr(sCtrl, 'autoMovement', '-------------:------------:', dv = 0, k=0, nn='Auto Move')
    mc.addAttr(sCtrl, ln='autoFrequency', at='double', dv=sFrequency, k=True)
    mc.addAttr(sCtrl, ln='autoAmplitude', at='double', dv=sAmplitude, k=True)
    mc.addAttr(sCtrl, ln='autoOffset', at='double', dv=sOffset, k=True)              
    #Create nodes
    sMathNode = mc.createNode ('dnMathOps',n=sCtrlName+'_dnMathOps')
    sFreqNode = mc.createNode ('multiplyDivide', n=sCtrlName+'_frequency_MD')
    sAmplitudeNode = mc.createNode ('multiplyDivide', n=sCtrlName+'_amplitude_MD')
    sOffsetNode = mc.createNode ('plusMinusAverage', n=sCtrlName+'_offset_PMA')
    #Connection    
    mc.connectAttr ('time1.outTime', sOffsetNode+'.input1D[0]',f=True)
    mc.connectAttr (sCtrl+'.autoOffset', sOffsetNode+'.input1D[1]',f=True)  
    mc.connectAttr (sOffsetNode+'.output1D', sFreqNode+'.input1X',f=True)
    mc.connectAttr (sCtrl+'.autoFrequency', sFreqNode+'.input2X',f=True)
    mc.connectAttr (sFreqNode+'.outputX', sMathNode+'.inAngleA',f=True)
    mc.connectAttr (sMathNode+'.outFloatX', sAmplitudeNode+'.input1X',f=True)  
    mc.connectAttr (sCtrl+'.autoAmplitude', sAmplitudeNode+'.input2X',f=True)
    for sAttr in tAttr:
        mc.connectAttr (sAmplitudeNode+'.outputX', sOffsetParent+'.'+sAttr)      
    #Create Another multiplier if math needs to be connected to overall control        
    if bConnectMult == True:
        #Amplitude
        sAmplitudeMultNode = mc.createNode ('multiplyDivide', n=sCtrlName+'_amplitudeMult_MD')
        mc.connectAttr (sAmplitudeMult, sAmplitudeMultNode+'.input1X',f=True)
        mc.connectAttr (sCtrl+'.autoAmplitude', sAmplitudeMultNode+'.input2X',f=True)
        mc.connectAttr (sAmplitudeMultNode+'.outputX', sAmplitudeNode+'.input2X',f=True)        
        #Frequency
        sFrequencyMultNode = mc.createNode ('multiplyDivide', n=sCtrlName+'_frequencyMult_MD')            
        mc.connectAttr (sFrequencyMult, sFrequencyMultNode+'.input1X',f=True)
        mc.connectAttr (sCtrl+'.autoFrequency', sFrequencyMultNode+'.input2X',f=True)
        mc.connectAttr (sFrequencyMultNode+'.outputX', sFreqNode+'.input2X',f=True)          
    return (sMathNode)



def deleteUnknownNodes():
    '''
    Deletes unknown nodes in the scene, mainly used for outsourcing rigs.

    @procedure rig.deleteUnknownNodes()
    '''
    turtle = mc.ls('*Turtle*')
    for node in turtle:
        print 'DELETING ... ', node
        mc.lockNode(node, lock = 0)
        mc.delete(node)

    for node in mc.ls(type='unknown'):
        print 'DELETING ... ', node
        mc.lockNode(node, lock = 0)
        mc.delete(node)






#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#--------------- ========[ FOLLICLES ]======== --------------#
#------------------------------------------------------------#

def createFollicle(name='follicle', surface='', obj='', driver='follicle', connectType='', UV=[], parent='', skipRotate=False, scaleObj='', shapeVis=True):
    '''
    Create a follicle on geometry or surface.

    @inParam name - string, name of follicle
    @inParam surface - string, geometry or nurbs surface to create follicle for
    @inParam obj - string, the follicle will be positioned at the closest point to the object. Using this obj you can also connect to the follicle using the connectType and driver flags. If this flag is used, UV flag becomes obsolete
    @inParam driver - string, if obj given, the driver flag is used to determine the driver relationship between follicle and obj. Options are 'follicle' (or same variable name as name), 'object' (or the same variable as in obj flag) or 'none'. The connectType flag is used in conjunction with this  
    @inParam connectType - string, if obj given and the driver flag is set to follicle, use this flag to determine the type of connection between the follicle and obj. Options are 'parent', 'parentConstraint', 'pointConstraint', 'point', 'connection'
    @inParam UV - list, if no obj given, you can use the UV flag to specify the position of the follicle manually
    @inParam parent - string, parent follicle under this. Be careful this parent object has no transform values
    @inParam skipRotate - boolean, if true, the follicle wont rotate
    @inParam scaleObj - string, scale constraint the follicle to this object
    @inParam shapeVis - boolean, visibility of follicle

    @procedure rig.createFollicle(name='', surface='', obj=ctrlOffset, driver='follicle', connectType='parent', parent=rigGroup)
    '''    
    if not mc.objExists(surface):
        print surface+' does not exist! @inParam surface'

    if obj and not mc.objExists(obj):
        print obj+' does not exist! @inParam obj'

    surfaceShape = ''
    surfaceOut = 'local'
    follicleIn = 'inputSurface'
    if mc.objectType(surface) == 'mesh':
        surfaceShape = surface
        surface = mc.listRelatives(surfaceShape, p=1)[0]

        surfaceOut = 'outMesh'
        follicleIn = 'inputMesh'
    else:
        surfaceShape = mc.listRelatives(surface, s=1)[0]

    follicleShape = mc.createNode('follicle', n=name+'Shape')
    follicle = mc.listRelatives(follicleShape, p=1)[0]
            
    mc.connectAttr(surfaceShape+'.worldMatrix', follicle+'.inputWorldMatrix')
    mc.connectAttr(surfaceShape+'.'+surfaceOut, follicle+'.'+follicleIn)
    mc.connectAttr(follicleShape+'.outTranslate', follicle+'.translate')
    if skipRotate==False:
        mc.connectAttr(follicleShape+'.outRotate', follicle+'.rotate')
    
    closestPointOnSurface = ''
    if obj:
        if mc.nodeType(surface) == 'transform':
            closestPointOnSurface = mc.createNode('closestPointOnMesh', n=name+'_closestPointOnMesh')
            mc.connectAttr(surfaceShape+'.worldMesh[0]', closestPointOnSurface+'.inMesh')
        else:
            closestPointOnSurface = mc.createNode('closestPointOnSurface', n=name+'_closestPointOnSurface')
            mc.connectAttr(surfaceShape+'.worldSpace', closestPointOnSurface+'.inputSurface')
        
        mc.connectAttr(surfaceShape+'.worldMatrix[0]', closestPointOnSurface+'.inputMatrix')

        decomposeMatrix = mc.createNode('decomposeMatrix', n=name+'_decomposeMatrix')
        mc.connectAttr(obj+'.worldMatrix[0]', decomposeMatrix+'.inputMatrix')
        mc.connectAttr(decomposeMatrix+'.outputTranslate', closestPointOnSurface+'.inPosition')

        mc.connectAttr(closestPointOnSurface+'.parameterU', follicleShape+'.parameterU', f=1)
        mc.connectAttr(closestPointOnSurface+'.parameterV', follicleShape+'.parameterV', f=1)


        if driver == 'follicle' or driver == name:
            mc.disconnectAttr(closestPointOnSurface+'.parameterU', follicleShape+'.parameterU')
            mc.disconnectAttr(closestPointOnSurface+'.parameterV', follicleShape+'.parameterV')
            mc.delete(closestPointOnSurface, decomposeMatrix)

            if connectType == 'parent':
                mc.parent(obj, follicle)
            elif connectType == 'parentConstraint':
                mc.parentConstraint(follicle, obj, mo=1)
            elif connectType == 'pointConstraint' or connectType == 'point':
                mc.pointConstraint(follicle, obj, mo=1)
            elif connectType == 'connection':
                mc.connectAttr(follicle+'.translate', obj+'.translate')
                mc.connectAttr(follicle+'.rotate', obj+'.rotate')
            else:
                print connectType+' is not valid! @inParam connectType Options are "parent", "parentConstraint", "pointConstraint", "point", "connection"'
        elif driver == 'none':
            mc.disconnectAttr(closestPointOnSurface+'.parameterU', follicleShape+'.parameterU')
            mc.disconnectAttr(closestPointOnSurface+'.parameterV', follicleShape+'.parameterV')
            mc.delete(closestPointOnSurface, decomposeMatrix)
        elif driver != 'object' and driver != obj:
            print driver+' is not valid! @inParam driver Options are "follicle", "object" (or the same variable as in obj flag) or "none"'
    elif UV:
        mc.setAttr(follicle+'.parameterU', UV[0])
        mc.setAttr(follicle+'.parameterV', UV[1])
    
    if parent:
        if mc.objExists(parent):
            mc.parent(follicle, parent)
        else:
            print parent+' does not exist! @inParam parent'

    if scaleObj and mc.objExists(scaleObj):
        mc.connectAttr(scaleObj+'.scale', follicle+'.scale')

    mc.setAttr(follicleShape+'.v', shapeVis)

    return [follicle, follicleShape]   







#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#---------------- ========[ RIBBON ]======== ----------------#
#------------------------------------------------------------#

def createRibbon(name='L_upperArm', numJoints=5, width=10, startJoint='', endJoint='', transformGrpJoint='', twistJoint='', twist='pos', masterCtrlType=8, ctrlType=25, masterCtrlColour=14, ctrlColour=16, rotMasterCtrl=[0,0,0], rotCtrl=[0,0,0], masterCtrlScale=[1,1,1], ctrlScale=[1,1,1], rotTransGrp=[], hideStartEndCtrl=True, parent='', jointParent='', v=1):
    '''
    Create a procedural ribbon for bendy arms, legs, tentacles, trunk etc. Should be used in conjunction with twist extractor or dnegs twist joints (see rigging 
    notes). Num joints should be the same as the number of twist joints in the rig, for example 5 for upper arm as there are 5 twist joints in the arm. The ribbon 
    creates twist, volume and wave controls as well as secondary controls you can move along the surface for more control (hidden by default - use the 
    *_mid_ctrl.secondaryCtrlVis attr).

    @inParam name - string, prefix of ribbon to create
    @inParam numJoints - int, number of joints to create. Usually number is equal to amount of twist joints
    @inParam width - int, width of nurbs surface created
    @inParam startJoint - string, start joint/object to constrain the start of the ribbon to
    @inParam endJoint - string, end joint/object to constrain the end of the ribbon to
    @inParam transformGrpJoint - string, object to parent constrain main transformGrp to. If none given, it will constrain to the start joint.
    @inParam twistJoint - string, name of twist joint and rotation or twist attribute. This value will be plugged into the secondary ribbon controls rx value so that it behaves exactly like the joints it's riding on top of 
    @inParam twist - string, choose between pos (+) or neg (-). This is for the secondary control twist (rotation in x), it needs to match the twist joints for example L_arm_upperTwist3Vol_env. It may rotate in X in positive, but for the R side it may be negative rotation. Use this flag to determine the rotation.
    @inParam masterCtrlType - int, master control shape type (see createCtrl for more info)
    @inParam ctrlType - int, secondary control shape type (see createCtrl for more info)
    @inParam masterCtrlColour - int, master control colour (see createCtrl for more info)
    @inParam ctrlColour - int, control colour (see createCtrl for more info)
    @inParam rotMasterCtrl - string, rotate master ctrls (start, mid and end)
    @inParam rotCtrl - string, rotate secondary ctrls
    @inParam masterCtrlScale - int, master control scale
    @inParam ctrlScale - int, control scale
    @inParam rotTransGrp - list, the main transform group of the ribbon will probably be constrained to the startJoint. However, you need to make sure the transform group is oriented correctly. Imagine the ribbon is flat on the ground, the +x should be facing away from the ribbon on the x axis, y should be facing up in y and z facing negative z. Use this list to rotate the transform group correctly.
    @inParam hideStartEndCtrl - boolean, hide the start and end master controls if true. These often wont be used and are just constrained to the start and end joint
    @inParam parent - string, parent of ribbon
    @inParam jointParent - string, parent of joint created. If none given it will be parented under the secondary control.
    @inParam v - string, visibility of ribbon

    @procedure rig.createRibbon(name='L_upperArm', numJoints=5, width=10, startJoint='L_arm_upperTwist1Vol_env', endJoint='L_arm_upperTwist5Vol_env', twistJoint='L_arm_upperTwist1VolReadTwist_jnt.rx', twist='pos', masterCtrlType=8, ctrlType=25, masterCtrlColour=14, ctrlColour=16, rotMasterCtrl=[0,0,0], rotCtrl=[0,0,0], masterCtrlScale=[0.75,0.75,0.75], ctrlScale=[0.7,0.7,0.7], rotTransGrp=[90,0,0], hideStartEndCtrl=True, parent='rig', v=1)
    '''
    if not name.endswith('_'):
        name = name+'_'

    #Delete existing ribbon if it exists
    if mc.objExists(name+'transform_grp'): 
        mc.delete(name+'transform_grp', name+'noTransform_grp')
        for node in ['multiplier_mpd', 'volume_sum_pma', 'twist_multNode']:
            objs = mc.ls(name+'*'+node+'*')
            if objs:    
                for obj in objs:    mc.delete(obj)

    #Gather information
    topPoint = (width/2)
    endPoint = (width/2*-1) 

    #Create the main groups
    grpMaster = mc.group(em=True, name=(name + 'ribbon_grp'))
    grpNoTransform = mc.group(em=True, name=(name + 'noTransform_grp'), parent=grpMaster)
    grpTransform = mc.group(em=True, name=(name + 'transform_grp'), parent=grpMaster)
    grpCtrl = mc.group(em=True, name=(name + 'ctrl_grp'), parent=grpTransform)
    grpSurface = mc.group(em=True, name=(name + 'surface_grp'), parent=grpTransform)
    grpSurfaces = mc.group(em=True, name=(name + 'surfaces_grp'), parent=grpNoTransform)
    grpDeformers = mc.group(em=True, name=(name + 'deformer_grp'), parent=grpNoTransform)
    grpFollMain = mc.group(em=True, name=(name + 'follicles_skin_grp'), parent=grpNoTransform)
    grpFollVolume = mc.group(em=True, name=(name + 'follicles_volume_grp'), parent=grpNoTransform)
    grpCluster = mc.group(em=True, name=(name + 'cluster_grp'), parent=grpNoTransform)
    grpMisc = mc.group(em=True, name=(name + 'misc_grp'), parent=grpNoTransform)

    if parent and mc.objExists(parent): mc.parent(grpMaster, parent)

    #Create a NURBS-plane to use as a base
    tmpPlane = mc.nurbsPlane(axis=(0,1,0), width=width, lengthRatio=(1.0 / width), u=numJoints, v=1, degree=3, ch=0)[0]
    #Create the NURBS-planes to use in the setup
    geoPlane = mc.duplicate(tmpPlane, name=(name + 'surface'))
    geoPlaneTwist = mc.duplicate(tmpPlane, name=(name + 'twist_blnd_surface'))
    geoPlaneSine = mc.duplicate(tmpPlane, name=(name + 'sine_blnd_surface'))
    geoPlaneWire = mc.duplicate(tmpPlane, name=(name + 'wire_blnd_surface'))
    geoPlaneVolume = mc.duplicate(tmpPlane, name=(name + 'volume_surface'))
    #Offset the volume-plane
    mc.setAttr((geoPlaneVolume[0] + '.translateZ'), -0.5)
    #Delete the base surface
    mc.delete(tmpPlane)

    #Create the controllers
    ctrlStart = createCtrl(ctrl=name+'start_ctrl', ctrlType=masterCtrlType, colour=masterCtrlColour, pos=[topPoint,0,0], rotCtrl=rotMasterCtrl, scale=masterCtrlScale, attrsToLock=['sx','sy','sz','v'], freezeOffset=1)[0]
    ctrlMid = createCtrl(ctrl=name+'mid_ctrl', ctrlType=masterCtrlType, colour=masterCtrlColour, pos=[0,0,0], rotCtrl=rotMasterCtrl, scale=masterCtrlScale, attrsToLock=['rx','ry','rz','sx','sy','sz','v'], freezeOffset=1)[0]
    ctrlEnd = createCtrl(ctrl=name+'end_ctrl', ctrlType=masterCtrlType, colour=masterCtrlColour, pos=[endPoint,0,0], rotCtrl=rotMasterCtrl, scale=masterCtrlScale, attrsToLock=['sx','sy','sz','v'], freezeOffset=1)[0]

    ctrlStartGrp = mc.listRelatives(ctrlStart, p=1)[0]
    ctrlMidGrp = mc.listRelatives(ctrlMid, p=1)[0]
    ctrlEndGrp = mc.listRelatives(ctrlEnd, p=1)[0]

    #PointConstraint the midCtrl between the top/end
    midConst = mc.pointConstraint(ctrlStart, ctrlEnd, ctrlMidGrp)

    #Add attributes: Twist/Roll attributes
    for ctrl in [ctrlStart, ctrlMid, ctrlEnd]:
        addEnumAttr(ctrl=ctrl, attr='twistSep', nn='--------------', enumName='Twist', dv=0, k=1, cb=1, l=True)

    for ctrl in [ctrlStart, ctrlEnd]:
        addDoubleAttr(ctrl=ctrl, attr='twist', dv=0)
        addDoubleAttr(ctrl=ctrl, attr='twistOffset', dv=0)
        addDoubleAttr(ctrl=ctrl, attr='affectToMid', min=0, max=10, dv=10)
    addDoubleAttr(ctrl=ctrlMid, attr='roll', dv=0)
    addDoubleAttr(ctrl=ctrlMid, attr='rollOffset', dv=0)
    #Add attributes: Volume attributes
    addEnumAttr(ctrl=ctrlMid, attr='volumeSep', nn='--------------', enumName='Volume', dv=0, k=1, cb=1, l=True)
    addDoubleAttr(ctrl=ctrlMid, attr='volume', min=-1, max=1, dv=0)
    addDoubleAttr(ctrl=ctrlMid, attr='volumeMultiplier', min=1, dv=3)
    addDoubleAttr(ctrl=ctrlMid, attr='startDropoff', min=0, max=1, dv=1)
    addDoubleAttr(ctrl=ctrlMid, attr='endDropoff', min=0, max=1, dv=1)
    addDoubleAttr(ctrl=ctrlMid, attr='volumeScale', min=endPoint*0.9, max=topPoint*2, dv=0)
    addDoubleAttr(ctrl=ctrlMid, attr='volumePosition', min=endPoint, max=topPoint, dv=0)
    #Add attributes: Sine attributes
    addEnumAttr(ctrl=ctrlMid, attr='sineSep', nn='--------------', enumName='Sine:', dv=0, k=1, cb=1, l=True)
    addDoubleAttr(ctrl=ctrlMid, attr='amplitude', dv=0)
    addDoubleAttr(ctrl=ctrlMid, attr='offset', dv=0)
    addDoubleAttr(ctrl=ctrlMid, attr='twist', dv=0)
    addDoubleAttr(ctrl=ctrlMid, attr='sineLength', min=0.1, dv=2)
    #Add attributes: Extra attributes
    addEnumAttr(ctrl=ctrlMid, attr='extraSep', nn='--------------', enumName='Extra', dv=0, k=1, cb=1, l=True)
    ctrlVisAttr = addEnumAttr(ctrl=ctrlMid, attr='secondaryControls', enumName='Off:On:', dv=0, k=0, cb=1)

    #Create deformers: Twist deformer, Sine deformer, Squash deformer
    twistDef = nonLinearDeformer(type='twist', name=geoPlaneTwist[0], geometry=[geoPlaneTwist[0]], parent=grpDeformers, rot=[0,0,90], defDict={'lowBound':-1, 'highBound':1})
    sineDef = nonLinearDeformer(type='sine', name=geoPlaneSine[0], geometry=[geoPlaneSine[0]], parent=grpDeformers, rot=[0,0,90], defDict={'lowBound':-1, 'highBound':1, 'dropoff':1})
    squashDef = nonLinearDeformer(type='squash', name=geoPlaneVolume[0], geometry=[geoPlaneVolume[0]], parent=grpDeformers, rot=[0,0,90], defDict={'lowBound':-1, 'highBound':1})

    #Create deformers: Wire deformer
    deformCrv = mc.curve(p=[(topPoint,0,0),(0,0,0),(endPoint,0,0)], degree=2)
    deformCrv = mc.rename(deformCrv, (name + 'ribbon_wire_crv'))
    wireDef = mc.wire(geoPlaneWire, dds=(0,15), wire=deformCrv)
    wireDef[0] = mc.rename(wireDef[0], (geoPlaneWire[0] + '_wire'))
    #Create deformers: Clusters
    clsTop = mc.cluster((deformCrv + '.cv[0:1]'), relative=1)
    clsMid = mc.cluster((deformCrv + '.cv[1]'), relative=1)
    clsEnd = mc.cluster((deformCrv + '.cv[1:2]'), relative=1)
    clsTop[0] = mc.rename(clsTop[0], (ctrlStart + '_top_cluster'))
    clsTop[1] = mc.rename(clsTop[1], (ctrlStart + '_top_clusterHandle'))
    clsMid[0] = mc.rename(clsMid[0], (ctrlMid + '_mid_cluster'))
    clsMid[1] = mc.rename(clsMid[1], (ctrlMid + '_mid_clusterHandle'))
    clsEnd[0] = mc.rename(clsEnd[0], (ctrlEnd + '_end_cluster'))
    clsEnd[1] = mc.rename(clsEnd[1], (ctrlEnd + '_end_clusterHandle'))
    mc.setAttr((mc.listRelatives(clsTop[1], type='shape')[0] + '.originX'), topPoint)
    mc.setAttr((mc.listRelatives(clsEnd[1], type='shape')[0] + '.originX'), endPoint)
    mc.xform(clsTop[1], ws=True, rp=(topPoint,0,0))
    mc.xform(clsTop[1], ws=True, sp=(topPoint,0,0))
    mc.xform(clsEnd[1], ws=True, rp=(endPoint,0,0))
    mc.xform(clsEnd[1], ws=True, sp=(endPoint,0,0))

    mc.percent(clsTop[0], (deformCrv + '.cv[1]'), v=0.5)
    mc.percent(clsEnd[0], (deformCrv + '.cv[1]'), v=0.5)
    posTopPma = mc.shadingNode('plusMinusAverage', asUtility=1, name = (name + 'top_ctrl_pos_pma'))
    mc.connectAttr((ctrlStart + '.translate'), (posTopPma + '.input3D[0]'))
    mc.connectAttr((ctrlStartGrp + '.translate'), (posTopPma + '.input3D[1]'))
    posEndPma = mc.shadingNode('plusMinusAverage', asUtility=1, name = (name + 'end_ctrl_pos_pma'))
    mc.connectAttr((ctrlEnd + '.translate'), (posEndPma + '.input3D[0]'))
    mc.connectAttr((ctrlEndGrp + '.translate'), (posEndPma + '.input3D[1]'))
    mc.connectAttr((posTopPma + '.output3D'), (clsTop[1] + '.translate'))
    mc.connectAttr((ctrlMid + '.translate'), (clsMid[1] + '.translate'))
    mc.connectAttr((posEndPma + '.output3D'), (clsEnd[1] + '.translate'))
    #Create deformers: Blendshape
    blndDef = mc.blendShape(geoPlaneWire[0], geoPlaneTwist[0], geoPlaneSine[0], geoPlane[0], name=(name + 'blendShape'),weight=[(0,1),(1,1),(2,1)])

    #Twist deformer: Sum the twist and the roll
    sumTopPma = mc.shadingNode('plusMinusAverage', asUtility=1, name = (name + 'twist_top_sum_pma'))
    mc.connectAttr((ctrlStart + '.twist'), (sumTopPma + '.input1D[0]'))
    mc.connectAttr((ctrlStart + '.twistOffset'), (sumTopPma + '.input1D[1]'))
    mc.connectAttr((ctrlMid + '.roll'), (sumTopPma + '.input1D[2]'))
    mc.connectAttr((ctrlMid + '.rollOffset'), (sumTopPma + '.input1D[3]'))
    mc.connectAttr((sumTopPma + '.output1D'), (twistDef[0] + '.startAngle'))
    sumEndPma = mc.shadingNode('plusMinusAverage', asUtility=1, name = (name + 'twist_low_sum_pma'))
    mc.connectAttr((ctrlEnd + '.twist'), (sumEndPma + '.input1D[0]'))
    mc.connectAttr((ctrlEnd + '.twistOffset'), (sumEndPma + '.input1D[1]'))
    mc.connectAttr((ctrlMid + '.roll'), (sumEndPma + '.input1D[2]'))
    mc.connectAttr((ctrlMid + '.rollOffset'), (sumEndPma + '.input1D[3]'))
    mc.connectAttr((sumEndPma + '.output1D'), (twistDef[0] + '.endAngle'))
    #Twist deformer: Set up the affect of the deformer
    topAffMdl = mc.shadingNode('multDoubleLinear', asUtility=1, name = (name + 'twist_top_affect_mdl'))
    mc.setAttr((topAffMdl + '.input1'), -0.1)
    mc.connectAttr((ctrlStart + '.affectToMid'), (topAffMdl + '.input2'))
    mc.connectAttr((topAffMdl + '.output'), (twistDef[0] + '.lowBound'))
    endAffMdl = mc.shadingNode('multDoubleLinear', asUtility=1, name = (name + 'twist_end_affect_mdl'))
    mc.setAttr((endAffMdl + '.input1'), 0.1)
    mc.connectAttr((ctrlEnd + '.affectToMid'), (endAffMdl + '.input2'))
    mc.connectAttr((endAffMdl + '.output'), (twistDef[0] + '.highBound'))

    #Squash deformer: Set up the connections for the volume control
    volumeRevfMdl = mc.shadingNode('multDoubleLinear', asUtility=1, name = (name + 'volume_reverse_mdl'))
    mc.setAttr((volumeRevfMdl + '.input1'), -1)
    mc.connectAttr((ctrlMid + '.volume'), (volumeRevfMdl + '.input2'))
    mc.connectAttr((volumeRevfMdl + '.output'), (squashDef[0] + '.factor'))
    mc.connectAttr((ctrlMid + '.startDropoff'), (squashDef[0] + '.startSmoothness'))
    mc.connectAttr((ctrlMid + '.endDropoff'), (squashDef[0] + '.endSmoothness'))
    mc.connectAttr((ctrlMid + '.volumePosition'), (squashDef[1] + '.translateX'))
    #Squash deformer: Set up the volume scaling
    sumScalePma = mc.shadingNode('plusMinusAverage', asUtility=1, name = (name + 'volume_scale_sum_pma'))
    mc.setAttr((sumScalePma + '.input1D[0]'), topPoint)
    mc.connectAttr((ctrlMid + '.volumeScale'), (sumScalePma + '.input1D[1]'))
    mc.connectAttr((sumScalePma + '.output1D'), (squashDef[1] + '.scaleY'))

    #Sine deformer: Set up the connections for the sine
    mc.connectAttr((ctrlMid + '.amplitude'), (sineDef[0] + '.amplitude'))
    mc.connectAttr((ctrlMid + '.offset'), (sineDef[0] + '.offset'))
    mc.connectAttr((ctrlMid + '.twist'), (sineDef[1] + '.rotateY'))
    mc.connectAttr((ctrlMid + '.sineLength'), (sineDef[0] + '.wavelength'))

    #Cleanup: Hierarchy
    mc.parent(geoPlaneWire[0], geoPlaneTwist[0], geoPlaneSine[0], geoPlaneVolume[0], grpSurfaces)
    mc.parent(clsTop[1], clsMid[1], clsEnd[1], grpCluster)
    mc.parent(ctrlStartGrp, ctrlMidGrp, ctrlEndGrp, grpCtrl)
    mc.parent(geoPlane[0], grpSurface)
    mc.parent(deformCrv, (mc.listConnections(wireDef[0] + '.baseWire[0]')[0]), grpMisc)
    #Cleanup: Visibility
    mc.hide(grpSurface, grpSurfaces, grpDeformers, grpFollVolume, grpCluster, grpMisc)
    
    for x in mc.listConnections(ctrlMid):
        mc.setAttr((x + '.isHistoricallyInteresting'), 0)
    
    for y in mc.listConnections(x):
        mc.setAttr((y + '.isHistoricallyInteresting'), 0)
    

    if not jointParent or not mc.objExists(jointParent):    
        parent = 1

    #Create follicles: The main-surface and the volume-surface
    value = (1/(float(numJoints)-1))
    for x in range(0, numJoints):
        #Declare a variable for the current index
        num = str(x + 1)
        #Get the normalized position of where to place the current follicle
        uVal = (1-(x*value))
        #Create a follicle for the bind-plane and the volume-plane
        follicleS = createFollicle(name=name+num+'_follicle', surface=geoPlane[0], UV=[uVal, 0.5], parent=grpFollMain, scaleObj=grpTransform, shapeVis=0)
        follicleV = createFollicle(name=name+num+'_volume_follicle', surface=geoPlaneVolume[0], UV=[uVal, 0], parent=grpFollVolume, shapeVis=0)

        #Create a joint, controller and a group for the current skin-follicle
        mc.select(clear=True)
        follicleCtrl = createCtrl(ctrl=name+num+'_ctrl', ctrlType=ctrlType, colour=ctrlColour, snapToObj=follicleS[0], rotCtrl=rotCtrl, scale=ctrlScale, parent=follicleS[0], attrsToLock=['sx','sy','sz','v'], ctrlVis=ctrlVisAttr)
        
        if parent: 
            jointParent = follicleCtrl[0]

        follicleJoint =createJoint(name=name+num+'_env', snapToObj=follicleCtrl[0], radius=1, parent=jointParent, v=0)
        if jointParent != follicleCtrl[0]:
            mc.parentConstraint(follicleCtrl[0], follicleJoint, mo=1)
            mc.scaleConstraint(follicleCtrl[0], follicleJoint, mo=1)

        uAttr = addDoubleAttr(ctrl=follicleCtrl[0], attr='uValue', min=0, max=1, dv=uVal)
        mc.connectAttr(uAttr, follicleS[0]+'.parameterU')
        mc.connectAttr(uAttr, follicleV[0]+'.parameterU')

        #Make the connections for the volume
        multMpd = mc.shadingNode('multiplyDivide', asUtility=1, name = (name + num + '_multiplier_mpd'))
        mc.connectAttr((ctrlMid + '.volumeMultiplier'), (multMpd + '.input1Z'))
        mc.connectAttr((follicleV[0] + '.translate'), (multMpd + '.input2'))
        sumPma = mc.shadingNode('plusMinusAverage', asUtility=1, name = (name + num + '_volume_sum_pma'))
        mc.connectAttr((multMpd + '.outputZ'), (sumPma + '.input1D[0]'))
        mc.setAttr((sumPma + '.input1D[1]'), 1)
        mc.connectAttr((sumPma + '.output1D'), (follicleCtrl[1] + '.scaleY'))
        mc.connectAttr((sumPma + '.output1D'), (follicleCtrl[1] + '.scaleZ'))

    #Connect ribbon to start and end joints
    if startJoint and mc.objExists(startJoint):
        if transformGrpJoint:   mc.delete(mc.parentConstraint(transformGrpJoint, grpTransform))
        else:   mc.delete(mc.parentConstraint(startJoint, grpTransform))
        
        if rotTransGrp:
            mc.rotate(rotTransGrp[0],rotTransGrp[1],rotTransGrp[2], grpTransform, r=1, os=1)
        mc.parentConstraint(startJoint, grpTransform, mo=1)
        mc.scaleConstraint(startJoint, grpTransform, mo=1)

        #mc.parentConstraint(startJoint, ctrlStartGrp)
        mc.parentConstraint(startJoint, ctrlStart)

        if endJoint and mc.objExists(endJoint):
            #mc.parentConstraint(endJoint, ctrlEndGrp)
            mc.parentConstraint(endJoint, ctrlEnd)

        if twistJoint and mc.objExists(twistJoint):
            for x in range(0, numJoints):
                #Declare a variable for the current index
                num = str(x + 1)

                mult = 1
                if twist == 'neg' or twist == '-' or twist == 'negative':   mult=-1
                
                #Work out the twist multiplier value based on the joint and if the twist is positive or negative based on the flag.
                twistMult = (x*value)*mult

                twistMultNode = mc.shadingNode('multiplyDivide', asUtility=1, name =name+num+'_twist_multNode')
                mc.connectAttr(twistJoint, twistMultNode+'.input1X')
                mc.setAttr(twistMultNode+'.input2X', twistMult)
                mc.connectAttr(twistMultNode+'.outputX', name+num+'Ctrl_offset.rx')

    for ctrl in [ctrlStart, ctrlEnd]:
        lockAndHideAttr(ctrl, ['tx','ty','tz','rx','ry','rz'])
        if hideStartEndCtrl:    mc.connectAttr(ctrlVisAttr, ctrl+'.lodVisibility')


    mc.setAttr(grpMaster+'.v', v)























































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#---------------- ========[ GEOMETRY ]======== --------------#
#------------------------------------------------------------#

def selectVerticesInOrder(vertices=[], geo=''):
    '''
    Selects vertices given in list order

    @inParam vertices - list, vertices to select in order of list given. You can give it a list of integers and use the geo flag, or give it the full string geo.vtx[0] name 
    @inParam geo - string, if only vertex numbers given, this flag can be used to give geometry name 

    @procedure rig.selectVerticesInOrder(vertices=['head_geo.vtx[0]', 'head_geo.vtx[1]', 'head_geo.vtx[2]'])
    '''
    mc.selectPref(trackSelectionOrder=1)
    mc.select(cl=1)
    for vertex in vertices:
        if isinstance(vertex, int):
            if geo:
                if mc.objExists(geo+'.vtx['+str(vertex)+']'):
                    mc.select(geo+'.vtx['+str(vertex)+']', add=1)
                else:
                    print geo+'.vtx['+str(vertex)+'] does not exist!'
            else:
                print 'Must provide geo flag if giving vertex id'
        elif '.vtx' in vertex:
            if mc.objExists(vertex):
                mc.select(vertex, add=1)
            else:
                print vertex+' does not exist! @inParam vertices'
        else:
            print 'Vertex naming not correct. Provide something like this: vertices=[\'head_geo.vtx[0]\', \'head_geo.vtx[1]\', \'head_geo.vtx[2]\'] or vertices=[0,1,2]'

    vtxs = mc.ls(orderedSelection=1)
    mc.selectPref(trackSelectionOrder=0)

    return vtxs
      
 

def duplicateClean(geo='', name='', parent=''):
    '''
    Duplicates geometry but deletes intermediate shapes such as Orig shapes.

    @inParam geo - string, geometry to duplicate
    @inParam name - string, name of duplicate geo created

    @procedure rig.duplicateClean(geo='L_eye_geo', name='L_eye_bs')
    '''
    if mc.objExists(geo):
        if not name:
            name = geo.replace('_geo', '_duplicate')

        name = mc.duplicate(geo, n=name)[0]
        if parent:
            mc.parent (name,parent)
        geoShapes = mc.listRelatives(name, type='shape', f=True)
        if geoShapes:
            for shape in geoShapes:
                if mc.getAttr(shape+'.intermediateObject') == True:
                    mc.delete(shape)  
        constraints = mc.listRelatives (name, type='constraint', f=True)  
        if constraints:
            for constraint in constraints:
                mc.delete (constraint)          
    else:
        print geo+' does not exist! @inParam geo: duplicateClean'
    return name    




def getClosestObj(source, objs):
    '''
    Finds and returns the closest object to given source object.

    @inParam source - string, object geo will be used against to find closest geo
    @inParam objs - list, objects used in search for closest object

    @procedure rig.getClosestObj(source='random_loc', objs=['sphere_*_geo'])
    '''
    closestObj = ''
    if mc.objExists(source):
        objs = mc.ls(objs) or []
        if objs:
            #Loading the nearestPointOnMesh plugin (if not loaded already):
            if not mc.pluginInfo('nearestPointOnMesh', q=1, loaded=1):
                mc.loadPlugin( 'nearestPointOnMesh' )

            #Creating a temporary nearestPointOnMesh node:
            npom = mc.createNode('nearestPointOnMesh')
            position = mc.xform(source, q=1, worldSpace=1, rotatePivot=1)
            mc.setAttr( npom + '.inPosition', position[0], position[1], position[2] )
            biggestLength = 999999999.999
            for obj in objs:
                mc.connectAttr( geo + '.worldMesh[0]', npom + '.inMesh', force=1)
                closestPos = mc.getAttr( npom + '.position' )[0]
                length = om.MVector( closestPos[0]-position[0], closestPos[1]-position[1], closestPos[2]-position[2] ).length()
                if length < biggestLength:
                    biggestLength = length
                    closestObj = geo

            mc.delete( npom )
        else:
            mc.warning( str(objs) + ' doesn\'t exist.' )
    else:
        mc.warning( '"' + obj + '" doesn\'t exist.' )

    return closestObj



#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#---------------- ========[ SURFACE ]======== ---------------#
#------------------------------------------------------------#

def connectObjToSurface(surface='', objs=[], driver=[]):
    '''
    Connect objects to a surface by creating a closestPointOnSurface node for each object.

    @inParam surface - string, surface to connect objects to
    @inParam objs - list, objects to connect to the surface
    @inParam driver - list, if driver is specified, it will drive the corresponding obj by connecting it's position to the inPosition attribute of the pointOnSurfaceInfo

    @procedure rig.connectObjToSurface(surface=surface, objs=[joints], driver=[ctrls])
    '''
    surfaceShape = mc.listRelatives(surface, f=1, s=1)[0]

    for i,obj in enumerate(objs):
        closestPointOnSurface = mc.createNode('closestPointOnSurface', n=obj+'_closestPointOnSurface')
        mc.connectAttr(surface+'.worldSpace', closestPointOnSurface+'.inputSurface')
        
        pointOnSurfaceNode = mc.createNode('pointOnSurfaceInfo', n=obj+'_pointOnSurfaceInfo')
        mc.connectAttr(surface+'.worldSpace', pointOnSurfaceNode+'.inputSurface')

        if driver:
            if mc.objExists(driver[i]):
                decomposeMatrix = mc.createNode('decomposeMatrix', n=driver[i]+'_decomposeMatrix')
                mc.connectAttr(driver[i]+'.worldMatrix[0]', decomposeMatrix+'.inputMatrix')
                mc.connectAttr(decomposeMatrix+'.outputTranslate', closestPointOnSurface+'.inPosition')

                mc.connectAttr(closestPointOnSurface+'.parameterU', pointOnSurfaceNode+'.parameterU')
                mc.connectAttr(closestPointOnSurface+'.parameterV', pointOnSurfaceNode+'.parameterV')
            else:
                print driver[i]+' does not exist! @inParam driver'
        else:     
            objPos = mc.xform(obj, q=1, ws=1, t=1)  
            mc.setAttr(closestPointOnSurface+'.inPosition', objPos)

            surfaceParameterU = mc.getAttr(closestPointOnSurface+'.parameterU')
            surfaceParameterV = mc.getAttr(closestPointOnSurface+'.parameterV')
        
            mc.setAttr(pointOnSurfaceNode+'.parameterU', surfaceParameterU)
            mc.setAttr(pointOnSurfaceNode+'.parameterV', surfaceParameterV)

            mc.delete(closestPointOnSurface)

        mc.connectAttr(pointOnSurfaceNode+'.position', obj+'.translate')





#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#----------------- ========[ CURVES ]======== ---------------#
#------------------------------------------------------------#

def createCurve(name='a_curve', cvPos=[(0,0,0), (1,1,1)], bezier=0, degree=3, fitBSpline=0, rebuildCurve=0, rebuildCurveDegree=3, rebuildCurveReplaceOrig=0, parent='', clusterCurve=0, v=0):
    '''
    Creates a curve.

    @inParam name - string, name of ikHandle to setup twist for
    @inParam cvPos - list, position of curve cv's. You can pass it vertex id (make sure the vertices are in the correct order), objects (such as locators) or the actual transform values. Please give the following syntax Vertex ID: ['head_geo.vtx[0]', 'head_geo.vtx[1]'], Object: [loc1, loc2], Transform: [(0,0,0), (1,1,1)]
    @inParam bezier - int, create as a bezier curve if 1
    @inParam degree - int, the degree of the curve
    @inParam fitBSpline - int, create fitBSpline curve if 1
    @inParam rebuildCurve - int, rebuild the curve if 1
    @inParam rebuildCurveDegree - int, if rebuild curve on, rebuild with this degree
    @inParam rebuildCurveReplaceOrig - int, if rebuild curve on, replace original curve on or off
    @inParam parent - string, parent curve under this
    @inParam createCluster - string, parent curve under this
    @inParam v - int, visibility of curve

    @procedure rig.createCurve(name='curve', cvPos=vertices)
    '''
    cvs = []
    cvNames = []
    clusterHandles = []
    clusterOffsets = []
    fitBSplineCurve = ''
    rebuiltCurve = ''

    for i,cv in enumerate(cvPos):
        if isinstance(cv, int):
            cvs[i] = cv
        elif mc.objExists(cv):
            if mc.objectType(cv) == 'mesh' or mc.objectType(cv) == 'transform':
                cvTrans = mc.xform(cv, q=1, ws=1, t=1)
                cvs.append((cvTrans[0], cvTrans[1], cvTrans[2]))
        else:
            print cv+' is not a valid cvPos'

    curve = mc.curve(n=name, bez=bezier, d=degree, p=cvs)
    curveShape = mc.rename(mc.listRelatives(curve, s=1)[0], curve+'Shape')

    if fitBSpline:
        fitBSplineCurve = mc.fitBspline(curve, n=name.replace('_curve', '_fitBspline_curve'), ch=1, tol=0.01)[0]

    if rebuildCurve:
        rebuiltCurve = mc.rebuildCurve(curve, n=curve.replace('_curve', 'Rebuilt_curve'), d=rebuildCurveDegree, ch=1, rpo=rebuildCurveReplaceOrig)[0]

    if parent:
        if mc.objExists(parent):
            mc.parent(curve, parent)

            if fitBSpline:
                mc.parent(fitBSplineCurve, parent)
                mc.setAttr(fitBSplineCurve+'.v', v)
            if rebuiltCurve:
                mc.parent(rebuiltCurve, parent)
                mc.setAttr(rebuiltCurve+'.v', v)
        else:
            print parent+' does not exist! @inParam parent'

    mc.xform(curve, cp=1)    

    if clusterCurve:
        for i in range(0, len(cvPos)):
            clusterHandle, cluster, clusterOffset, clusterSet = createCluster(geos=[curve+'.cv['+str(i)+']'], name=curve.replace('_curve','Curve_'+str(i)+'_cluster'), parent=parent)
            clusterHandles.append(clusterHandle)
            clusterOffsets.append(clusterOffset)
 
    mc.setAttr(curve+'.v', v)

    return(curve, rebuiltCurve, fitBSplineCurve, clusterHandles, clusterOffsets)



def connectObjToCurve(curve='', objs=[], driver=[], motionPath=1, motionPathU='', upVecCurve=''):
    '''
    Connect objects to a curve by creating either a motion path or closestPointOnCurveInfo node for each object.

    @inParam curve - string, curve to connect objects to
    @inParam objs - list, objects to connect to the curve
    @inParam driver - list, if driver is specified, it will drive the corresponding obj by connecting it's position to the inPosition attribute of the pointOnCurveInfo or U parameter of the motionPath
    @inParam motionPath - int, create motionPath node if true, pointOnCurveInfo if false
    @inParam motionPathU - string, attribute to control U value of motion path
    @inParam upVecCurve - string, if a curve is given, a locator will be motion pathed to it and used as the upVector for the obj

    @procedure rig.connectObjToCurve(curve=curve, objs=[locs], motionPath=1, motionPathU=curveAttr, upVecCurve=upVecCurve)
    '''
    curveShape = mc.listRelatives(curve, f=1, s=1)[0]

    for i,obj in enumerate(objs):
        closestPointOnCurve = mc.createNode('nearestPointOnCurve', n=obj+'_nearestPointOnCurve')
        mc.connectAttr(curve+'.worldSpace', closestPointOnCurve+'.inputCurve')

        pointOnCurveNode = mc.createNode('pointOnCurveInfo', n=obj+'_pointOnCurveInfo')
        mc.connectAttr(curve+'.worldSpace', pointOnCurveNode+'.inputCurve')

        if motionPath:
            motionPath = mc.createNode('motionPath', n=obj+'_motionPath')
            mc.connectAttr(curveShape+'.worldSpace[0]', motionPath+'.geometryPath', f=1)
            mc.connectAttr(motionPath+'.allCoordinates', obj+'.translate', f=1)
            mc.setAttr(motionPath+'.follow', 1)
            mc.setAttr(motionPath+'.fractionMode', 1)

            if driver:
                decomposeMatrix = mc.createNode('decomposeMatrix', n=driver[i]+'_decomposeMatrix')
                mc.connectAttr(driver[i]+'.worldMatrix[0]', decomposeMatrix+'.inputMatrix')
                mc.connectAttr(decomposeMatrix+'.outputTranslate', closestPointOnCurve+'.inPosition')
                mc.connectAttr(closestPointOnCurve+'.parameter', motionPath+'.uValue')
            elif motionPathU:
                mc.connectAttr(motionPathU, motionPath+'.uValue')
            else:
                mc.setAttr(motionPath+'.uValue', 0)

            mc.delete(pointOnCurveNode)


            if upVecCurve:
                if mc.objExists(upVecCurve):
                    parent = mc.listRelatives(obj, parent=1)[0]
                    upVecCurveShape = mc.listRelatives(upVecCurve, f=1, s=1)[0]
                    upVecLoc = createLoc(name=upVecCurve+'_loc', parent=parent, scale=[80,80,80], v=0)

                    motionPathUpVec = mc.createNode('motionPath', n=obj+'_upVec_motionPath')
                    mc.connectAttr(upVecCurveShape+'.worldSpace[0]', motionPathUpVec+'.geometryPath', f=1)
                    mc.connectAttr(motionPathUpVec+'.allCoordinates', upVecLoc+'.translate', f=1)
                    mc.setAttr(motionPathUpVec+'.follow', 1)
                    mc.setAttr(motionPathUpVec+'.fractionMode', 1)

                    mc.connectAttr(motionPathU, motionPathUpVec+'.uValue')


                    mc.setAttr(motionPath+'.worldUpType', 1)
                    mc.connectAttr(upVecLoc+'.worldMatrix[0]', motionPath+'.worldUpMatrix')

            return motionPath
        else:
            if driver:
                if mc.objExists(driver[i]):
                    decomposeMatrix = mc.createNode('decomposeMatrix', n=driver[i]+'_decomposeMatrix')
                    mc.connectAttr(driver[i]+'.worldMatrix[0]', decomposeMatrix+'.inputMatrix')
                    mc.connectAttr(decomposeMatrix+'.outputTranslate', closestPointOnCurve+'.inPosition')

                    mc.connectAttr(closestPointOnCurve+'.parameter', pointOnCurveNode+'.parameter')
                else:
                    print driver[i]+' does not exist! @inParam driver'
            else:
                objPos = mc.xform(obj, q=1, ws=1, t=1)
                mc.setAttr(closestPointOnCurve+'.inPositionX', objPos[0])
                mc.setAttr(closestPointOnCurve+'.inPositionY', objPos[1])
                mc.setAttr(closestPointOnCurve+'.inPositionZ', objPos[2])

                curveParameter = mc.getAttr(closestPointOnCurve+'.parameter')
                mc.setAttr(pointOnCurveNode+'.parameter', curveParameter)

                mc.delete(closestPointOnCurve)
            
            mc.connectAttr(pointOnCurveNode+'.position', obj+'.translate')

            return pointOnCurveNode






def createRopeCtrl (sCurve, fCtrlScale = 1.0, sBaseParent = 'cluster_grp', sHullGrp = 'hullCluster_grp', sCtrlParent='', bStartEndCtrl=False,  bDetailCtrl=True, bExtraCtrl= False, bRebuildCrv=True, iStackValue=1):
    ctrlDict = {'StartCluster':[], 'MidStartCluster':[], 'MidCluster':[], 'MidEndCluster':[], 'EndCluster':[],
                'StartCtrl':[], 'MidStartCtrl':[], 'MidCtrl':[], 'MidEndCtrl':[], 'EndCtrl':[]}
    sCurveName = sCurve.replace('_crv','')
    if bRebuildCrv==True: 
        bMo=False
    else:
        bMo=True     
    #Create start/end clusters.
    sStartCluster = mc.cluster (sCurve+'.cv[0]', n=sCurveName+'Start_Cluster')    
    if bRebuildCrv  == True:    
        sEndCluster = mc.cluster (sCurve+'.cv[1]', n=sCurveName+'End_Cluster')
    else:
        sEndCluster = mc.cluster (sCurve+'.cv[4]', n=sCurveName+'End_Cluster')
    if not mc.objExists (sBaseParent):
        mc.createNode ('transform',n=sBaseParent, p=otherNull)
    if not mc.objExists (sHullGrp):
        mc.createNode ('transform',n=sHullGrp, p=sBaseParent)                 
    mc.parent (sStartCluster[1], sHullGrp)
    mc.parent (sEndCluster[1], sHullGrp)
    ctrlDict['StartCluster'] = sStartCluster
    ctrlDict['EndCluster'] = sEndCluster            
    #Create Primary clusters   
    if bStartEndCtrl == True:
        sStartTransforms = rig.getTransforms (sStartCluster[1],attrType='rp')
        sStartPos = sStartTransforms['t']
        sEndTransforms = rig.getTransforms (sEndCluster[1],attrType='rp')
        sEndPos = sEndTransforms['t']                        
        sStartCtrl = rig.createCtrl(ctrl=sCurveName+'Start_ctrl', ctrlType=12, pos=sStartPos, rot=[0,0,0], scale=[fCtrlScale,fCtrlScale,fCtrlScale], parent=sCtrlParent,colour=6,iStack=iStackValue)       
        sEndCtrl = rig.createCtrl(ctrl=sCurveName+'End_ctrl', ctrlType=12, pos=sEndPos, rot=[0,0,0], scale=[fCtrlScale,fCtrlScale,fCtrlScale], parent=sCtrlParent,colour=6,iStack=iStackValue)    
        mc.pointConstraint (sStartCtrl[0], sStartCluster[1])
        mc.pointConstraint (sEndCtrl[0], sEndCluster[1])
        ctrlDict['StartCtrl'] = sStartCtrl
        ctrlDict['EndCtrl'] = sEndCtrl
        rig.lockAndHideAttr(sStartCtrl[0], ['sx','sy','sz','visibility']) 
        rig.lockAndHideAttr(sEndCtrl[0], ['sx','sy','sz','visibility'])               
    # Rebuild curve. Do this to a linear curve before creating secondary and tertiary controls    
    if bRebuildCrv  == True:
        if bExtraCtrl == False:
            sBSplineCrv = mc.rebuildCurve (sCurve, ch=True, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=2, d=3, tol=0.01)
        if bExtraCtrl == True:
            sBSplineCrv = mc.rebuildCurve (sCurve, ch=True, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=8, d=3, tol=0.01)                      
        mc.rename (sBSplineCrv[1], sCurve+'_rebuildCurve')                 
    # Unlike start/end clusters, these clusters are relative
    if bRebuildCrv  == True:
        if bExtraCtrl == False:                 
            sMidStartCluster = mc.cluster (sCurve+'.cv[1]', n=sCurve+'MidStart_Cluster',rel=True)
            sMidCluster = mc.cluster (sCurve+'.cv[2]', n=sCurve+'Mid_Cluster',rel=True)
            sMidEndCluster = mc.cluster (sCurve+'.cv[3]', n=sCurve+'MidEnd_Cluster',rel=True)
        if bExtraCtrl == True:   
            sMidStartCluster = mc.cluster (sCurve+'.cv[3]', n=sCurve+'MidStart_Cluster',rel=True)
            sMidCluster = mc.cluster (sCurve+'.cv[5]', n=sCurve+'Mid_Cluster',rel=True)
            sMidEndCluster = mc.cluster (sCurve+'.cv[7]', n=sCurve+'MidEnd_Cluster',rel=True)
            #Create Extra Clusters
            sExtraStartCluster = mc.cluster (sCurve+'.cv[1]', n=sCurve+'ExtraStart_Cluster',rel=True)                                         
            sExtraStartACluster = mc.cluster (sCurve+'.cv[2]', n=sCurve+'ExtraStartA_Cluster',rel=True)
            sExtraStartBCluster = mc.cluster (sCurve+'.cv[4]', n=sCurve+'ExtraStartB_Cluster',rel=True)
            sExtraEndBCluster = mc.cluster (sCurve+'.cv[6]', n=sCurve+'ExtraEndB_Cluster',rel=True)
            sExtraEndACluster = mc.cluster (sCurve+'.cv[8]', n=sCurve+'ExtraEndA_Cluster',rel=True)  
            sExtraEndCluster = mc.cluster (sCurve+'.cv[9]', n=sCurve+'ExtraEnd_Cluster',rel=True)                                
            #Get Transforms of Extra Clusters
            sExtraStartTransforms = rig.getTransforms (sExtraStartCluster[1],attrType='rp')
            sExtraStartPos = sExtraStartTransforms['t']                
            sExtraStartATransforms = rig.getTransforms (sExtraStartACluster[1],attrType='rp')
            sExtraStartAPos = sExtraStartATransforms['t']
            sExtraStartBTransforms = rig.getTransforms (sExtraStartBCluster[1],attrType='rp')
            sExtraStartBPos = sExtraStartBTransforms['t']
            sExtraEndATransforms = rig.getTransforms (sExtraEndACluster[1],attrType='rp')
            sExtraEndAPos = sExtraEndATransforms['t']
            sExtraEndBTransforms = rig.getTransforms (sExtraEndBCluster[1],attrType='rp')
            sExtraEndBPos = sExtraEndBTransforms['t']
            sExtraEndTransforms = rig.getTransforms (sExtraEndCluster[1],attrType='rp')
            sExtraEndPos = sExtraEndTransforms['t']                
            # parent extra clusterhandles to transform with the same rotate pivot
            sExtraStartClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraStart_Cluster_Offset')
            mc.move (sExtraStartPos[0],sExtraStartPos[1],sExtraStartPos[2],sExtraStartClusterOffset)
            mc.makeIdentity(sExtraStartClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraStartCluster[1], sExtraStartClusterOffset)
            mc.parent (sExtraStartClusterOffset, sBaseParent)
            sExtraStartAClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraStartA_Cluster_Offset')
            mc.move (sExtraStartAPos[0],sExtraStartAPos[1],sExtraStartAPos[2],sExtraStartAClusterOffset)
            mc.makeIdentity(sExtraStartAClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraStartACluster[1], sExtraStartAClusterOffset)
            mc.parent (sExtraStartAClusterOffset, sBaseParent)
            sExtraStartBClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraStartB_Cluster_Offset')
            mc.move (sExtraStartBPos[0],sExtraStartBPos[1],sExtraStartBPos[2],sExtraStartBClusterOffset)
            mc.makeIdentity(sExtraStartBClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraStartBCluster[1], sExtraStartBClusterOffset)  
            mc.parent (sExtraStartBClusterOffset, sBaseParent)          
            sExtraEndAClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraEndA_Cluster_Offset')
            mc.move (sExtraEndAPos[0],sExtraEndAPos[1],sExtraEndAPos[2],sExtraEndAClusterOffset)
            mc.makeIdentity(sExtraEndAClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraEndACluster[1], sExtraEndAClusterOffset)
            mc.parent (sExtraEndAClusterOffset, sBaseParent)           
            sExtraEndBClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraEndB_Cluster_Offset')
            mc.move (sExtraEndBPos[0],sExtraEndBPos[1],sExtraEndBPos[2],sExtraEndBClusterOffset)
            mc.makeIdentity(sExtraEndBClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraEndBCluster[1], sExtraEndBClusterOffset)  
            mc.parent (sExtraEndBClusterOffset, sBaseParent)
            sExtraEndClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraEnd_Cluster_Offset')
            mc.move (sExtraEndPos[0],sExtraEndPos[1],sExtraEndPos[2],sExtraEndClusterOffset)
            mc.makeIdentity(sExtraEndClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraEndCluster[1], sExtraEndClusterOffset)  
            mc.parent (sExtraEndClusterOffset, sBaseParent)                                     
    else:
        sMidStartCluster = mc.cluster (sCurve+'.cv[1]', n=sCurve+'MidStart_Cluster',rel=False)
        sMidCluster = mc.cluster (sCurve+'.cv[2]', n=sCurve+'Mid_Cluster',rel=False)
        sMidEndCluster = mc.cluster (sCurve+'.cv[3]', n=sCurve+'MidEnd_Cluster',rel=False)
    sMidTransforms = rig.getTransforms (sMidCluster[1],attrType='rp')
    sMidPos = sMidTransforms['t']
    sMidEndTransforms = rig.getTransforms (sMidEndCluster[1],attrType='rp')
    sMidEndPos = sMidEndTransforms['t']
    sMidStartTransforms = rig.getTransforms (sMidStartCluster[1],attrType='rp')
    sMidStartPos = sMidStartTransforms['t']
    # parent clusterhandles to transform with the same rotate pivot
    sMidStartClusterOffset = mc.createNode ('transform',n=sCurve+'MidStartCluster_Offset')
    mc.move (sMidStartPos[0],sMidStartPos[1],sMidStartPos[2],sMidStartClusterOffset)
    mc.makeIdentity(sMidStartClusterOffset,apply=True, translate=True, rotate=True, scale=True )

    sMidClusterOffset = mc.createNode ('transform',n=sCurve+'MidCluster_Offset')
    mc.move (sMidPos[0],sMidPos[1],sMidPos[2],sMidClusterOffset)
    mc.makeIdentity(sMidClusterOffset,apply=True, translate=True, rotate=True, scale=True )  

    sMidEndClusterOffset = mc.createNode ('transform',n=sCurve+'MidEndCluster_Offset')          
    mc.move (sMidEndPos[0],sMidEndPos[1],sMidEndPos[2],sMidEndClusterOffset)
    mc.makeIdentity(sMidEndClusterOffset,apply=True, translate=True, rotate=True, scale=True ) 
                                             
    mc.parent (sMidStartCluster[1], sMidStartClusterOffset)
    mc.parent (sMidCluster[1], sMidClusterOffset)
    mc.parent (sMidEndCluster[1], sMidEndClusterOffset)
    mc.parent (sMidStartClusterOffset,sBaseParent)
    mc.parent (sMidClusterOffset,sBaseParent)
    mc.parent (sMidEndClusterOffset,sBaseParent)

    #Create Mid Ctrl
    sMidCtrl = rig.createCtrl(ctrl=sCurveName+'Mid_ctrl', ctrlType=12, pos=sMidPos, rot=[0,0,0], scale=[fCtrlScale,fCtrlScale,fCtrlScale], parent=sCtrlParent,iStack=iStackValue,colour=6)       
    mc.pointConstraint (sMidCtrl[1], sMidClusterOffset,mo=True)
    mc.pointConstraint (sMidCtrl[0], sMidCluster[1],mo=True)        
    sMidRefNull = mc.createNode ('transform',n=sCurveName+'Mid_refNull', p=sMidCtrl[1])
    mc.parentConstraint (sMidCtrl[0], sMidRefNull)    
    mc.pointConstraint (sStartCluster[1],sEndCluster[1], sMidCtrl[1], mo=bMo)             
    ctrlDict['MidCluster'] = sMidCluster
    ctrlDict['MidCtrl'] = sMidCtrl                   
    rig.lockAndHideAttr(sMidCtrl[0], ['sx','sy','sz','visibility']) 
    if bDetailCtrl == True:         
        #Mid Start Ctrl
        sMidStartCtrl = rig.createCtrl(ctrl=sCurveName+'MidStart_ctrl', ctrlType=12, pos=sMidStartPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)          
        mc.pointConstraint (sStartCluster[1],sMidCtrl[1], sMidStartCtrl[1], mo=bMo) 
        mc.pointConstraint (sStartCluster[1],sMidCtrl[0], sCurveName+'MidStartStack1_offset', mo=bMo)        
        mc.pointConstraint (sMidStartCtrl[1], sMidStartClusterOffset)
        mc.pointConstraint (sMidStartCtrl[0], sMidStartCluster[1])
        ctrlDict['MidStartCluster'] = sMidStartCluster
        ctrlDict['MidStartCtrl'] = sMidStartCtrl                            
        #Mid End Ctrl
        sMidEndCtrl = rig.createCtrl(ctrl=sCurveName+'MidEnd_ctrl', ctrlType=12, pos=sMidEndPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)                       
        mc.pointConstraint (sEndCluster[1],sMidCtrl[1], sMidEndCtrl[1], mo=bMo) 
        mc.pointConstraint (sEndCluster[1],sMidCtrl[0], sCurveName+'MidEndStack1_offset', mo=bMo)   
        mc.pointConstraint (sMidEndCtrl[1], sMidEndClusterOffset)
        mc.pointConstraint (sMidEndCtrl[0], sMidEndCluster[1])                                     
        ctrlDict['MidEndCluster'] = sMidEndCluster
        ctrlDict['MidEndCtrl'] = sMidEndCtrl 
        if bExtraCtrl == True:              
            sExtraStartACtrl = rig.createCtrl(ctrl=sCurveName+'ExtraStartA_ctrl', ctrlType=12, pos=sExtraStartAPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)    
            mc.pointConstraint (sStartCluster[1], sMidStartCtrl[1],sExtraStartACtrl[1], mo=bMo)   
            mc.pointConstraint (sStartCluster[1], sMidStartCtrl[0], sCurveName+'ExtraStartAStack1_offset', mo=bMo)              
            mc.pointConstraint (sExtraStartACtrl[1], sExtraStartAClusterOffset)
            mc.pointConstraint (sExtraStartACtrl[0], sExtraStartACluster[1])
            sExtraStartBCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraStartB_ctrl', ctrlType=12, pos=sExtraStartBPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sMidCtrl[1], sMidStartCtrl[1],sExtraStartBCtrl[1], mo=bMo)   
            mc.pointConstraint (sMidCtrl[0], sMidStartCtrl[0], sCurveName+'ExtraStartBStack1_offset', mo=bMo)                 
            mc.pointConstraint (sExtraStartBCtrl[1], sExtraStartBClusterOffset)
            mc.pointConstraint (sExtraStartBCtrl[0], sExtraStartBCluster[1])         
            sExtraEndACtrl = rig.createCtrl(ctrl=sCurveName+'ExtraEndA_ctrl', ctrlType=12, pos=sExtraEndAPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sEndCluster[1], sMidEndCtrl[1],sExtraEndACtrl[1], mo=bMo)   
            mc.pointConstraint (sEndCluster[1], sMidEndCtrl[0], sCurveName+'ExtraEndAStack1_offset', mo=bMo)               
            mc.pointConstraint (sExtraEndACtrl[1], sExtraEndAClusterOffset)
            mc.pointConstraint (sExtraEndACtrl[0], sExtraEndACluster[1])
            sExtraEndBCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraEndB_ctrl', ctrlType=12, pos=sExtraEndBPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sMidCtrl[1], sMidEndCtrl[1],sExtraEndBCtrl[1], mo=bMo)   
            mc.pointConstraint (sMidCtrl[0], sMidEndCtrl[0], sCurveName+'ExtraEndBStack1_offset', mo=bMo)                
            mc.pointConstraint (sExtraEndBCtrl[1], sExtraEndBClusterOffset)
            mc.pointConstraint (sExtraEndBCtrl[0], sExtraEndBCluster[1])  
            sExtraStartCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraStart_ctrl', ctrlType=12, pos=sExtraStartPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sStartCluster[1], sExtraStartACtrl[1],sExtraStartCtrl[1], mo=bMo)   
            mc.pointConstraint (sStartCluster[1], sExtraStartACtrl[0], sCurveName+'ExtraStartStack1_offset', mo=bMo)             
            mc.pointConstraint (sExtraStartCtrl[1], sExtraStartClusterOffset)
            mc.pointConstraint (sExtraStartCtrl[0], sExtraStartCluster[1])
            sExtraEndCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraEnd_ctrl', ctrlType=12, pos=sExtraEndPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)      
            mc.pointConstraint (sEndCluster[1], sExtraEndACtrl[1],sExtraEndCtrl[1], mo=bMo)   
            mc.pointConstraint (sEndCluster[1], sExtraEndACtrl[0], sCurveName+'ExtraEndStack1_offset', mo=bMo)                   
            mc.pointConstraint (sExtraEndCtrl[1], sExtraEndClusterOffset)
            mc.pointConstraint (sExtraEndCtrl[0], sExtraEndCluster[1])

    return (ctrlDict)   









#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#---------------- ========[ SHADERS ]======== ---------------#
#------------------------------------------------------------#

def importShaders(shaderFile='', importNS='shaderNetworkImport'):
    '''
    Imports shaders using the shader grabber tool. Pass it the shader file name, usually a SCNS file and it will assign all shaders based on the shader group names.

    @param shaderFile - string, name of file to import shaders
    @param importNS - string, namespace given to imported shder network

    @procedure rig.importShaders(shaderFile='/jobs/INVERT/3D/ITEM/character/alice/costume/SCNS/lookdev_postvis/SCNS_character-alice-costume-lookdev-postvis-v002/SCNS_character-alice-costume-lookdev-postvis-v002.mb')
    '''
    ainfo = shader_grabber.AssignmentInfo(import_ns=importNS)
    ainfo.import_file(file_name=shaderFile)



def assignShaders(geos=[], shaderName='lambert2', shaderType='lambert', colour=[0.5,0.5,0.5], transparency=[0,0,0], ambientColor=[0,0,0], incandescence=[0,0,0], shaderGroup=1):
    '''
    Assigns a shader to a list of geometry. If the shader name given does not exist, it will create a new shader.

    @param geos - list, geometry to assign shader to
    @param shaderName - string, name of shader
    @param shaderType - string, type of shader
    @param colour - list, colour value
    @param transparency - list, transparency value
    @param ambientColor - list, ambient colour value
    @param incandescence - list, incandescence value
    @param shaderGroup - if 1, it will create a SG 

    @procedure rig.assignShaders(geos=['importGeo'], shaderName='geo_lambert', shaderType='lambert')
    '''
    if not geos:
        geos = mc.ls('*_geo')

    if mc.objExists(shaderName):
        if shaderGroup:
            SG = mc.sets(shaderName, renderable=1, noSurfaceShader=1, em=1, name=shaderName+'SG')

            if shaderName == 'lambert1':
                SG = 'initialShadingGroup'

        for geo in geos:
            if shaderGroup:
                mc.sets(geo,fe=SG)

            mc.setAttr(shaderName+'.color', colour[0],colour[1],colour[2],type='double3')
            mc.setAttr(shaderName+'.transparency', transparency[0],transparency[1],transparency[2], type='double3')
            mc.setAttr(shaderName+'.ambientColor', ambientColor[0],ambientColor[1],ambientColor[2], type='double3')
            mc.setAttr(shaderName+'.incandescence', incandescence[0],incandescence[1],incandescence[2], type='double3')
    else:
        shader = createShaders(name=shaderName, shaderType=shaderType, colour=colour, transparency=transparency, ambientColor=ambientColor, incandescence=incandescence, shaderGroup=shaderGroup)

        #Assign the shader to the geometry.
        if shaderGroup:
            for geo in geos:
                if mc.objExists(geo):
                    mc.sets(geo,fe=shader[0])
                else:
                    print 'Object doesn\'t exist - '+geo

    return shaderName



def createShaders(name='lambert2', shaderType='lambert', colour=[0.5,0.5,0.5], transparency=[0,0,0], ambientColor=[0,0,0], incandescence=[0,0,0], shaderGroup=1):
    '''
    Creates a shader, often used with assignShaders.

    @param name - string, name of shader
    @param shaderType - string, type of shader
    @param colour - list, colour value
    @param transparency - list, transparency value
    @param ambientColor - list, ambient colour value
    @param incandescence - list, incandescence value
    @param shaderGroup - if 1, it will create a SG 

    @procedure rig.createShaders(name='geo_lambert', shaderType='lambert', colour=[0.5,0.5,0.5], transparency=[0,0,0], ambientColor=[0,0,0], incandescence=[0,0,0])
    '''
    shader = mc.shadingNode(shaderType,asShader=1,n=(name))
    shader = mc.rename(shader, name)

    SG = ''
    if shaderGroup:
        SG = mc.sets(shader,renderable=1,noSurfaceShader=1,em=1,name = name + 'SG')
        mc.connectAttr(shader+'.outColor',SG + '.surfaceShader',f=1)

    mc.setAttr(shader + '.color', colour[0],colour[1],colour[2],type='double3')
    mc.setAttr(shader+'.transparency', transparency[0],transparency[1],transparency[2], type='double3')
    mc.setAttr(shader+'.ambientColor', ambientColor[0],ambientColor[1],ambientColor[2], type='double3')
    mc.setAttr(shader+'.incandescence', incandescence[0],incandescence[1],incandescence[2], type='double3')

    return(SG,shader)



def createFileTextureShader(geos=[], name='', fileName='', shaderGroup='', udimsU=1, udimsV=1):
    '''
    Creates a file texture node and connects to a newly created lambert shader which connects to a SG if given.

    @param geos - list, geo to add file texture shader to
    @param name - string, name of file texture node and shader created. 
    @param fileName - string, shader file 
    @param shaderGroup - if geo has shaderGroup, the lambert will be assigned to this shaderGroup
    @param udimsU - int, set udims U
    @param udimsV - int, set udims V

    @procedure rig.createFileTextureShader(name='L_eye', fileName='/jobs/FLAT/ASSET/character/flatStanley/unflat/ivy/texs/T_character_flatStanley-unflat_default_alt0_RGB_1_lodDefault-v002/T_character_flatStanley-unflat_default_alt0_RGB_1_lodDefault.atlas.tif', shaderGroup='eyesInnerSG', udimsU=1, udimsV=1)
    '''
    if mc.objExists(name+'_place2dTexture'):
        mc.delete(name+'_place2dTexture')
    if mc.objExists(name+'_file'):
        mc.delete(name+'_file')
    if mc.objExists(name+'_lambert'):
        mc.delete(name+'_lambert')

    texture = mc.createNode('place2dTexture', name=name+'_place2dTexture')
    fileNode = mc.createNode('file', name=name+'_file')

    mc.setAttr(texture+'.coverageU', udimsU)
    mc.setAttr(texture+'.coverageV', udimsV)

    attrs = ['coverage','mirrorU','mirrorV','noiseUV','offset','repeatUV','rotateFrame','rotateUV','stagger','translateFrame','vertexCameraOne','vertexUvOne','vertexUvTwo','vertexUvThree','wrapU','wrapV']
    for attr in attrs:
        mc.connectAttr(texture+'.'+attr, fileNode+'.'+attr)
    #mc.connectAttr(texture+'.outUV', fileNode+'.uvCoord')
    mc.connectAttr(texture+'.outUV', fileNode+'.uv')
    mc.connectAttr(texture+'.outUvFilterSize', fileNode+'.uvFilterSize')
    mc.setAttr(fileNode+'.fileTextureName', fileName, type='string')

    #shader = createShaders(name=name+'_lambert', shaderType='lambert')[1]
    shader = assignShaders(geos=[], shaderName=name)

    if shaderGroup:
        if mc.objExists(shaderGroup):
            mc.connectAttr(shader+'.outColor', shaderGroup+'.surfaceShader')
        else:
            print 'Shading group '+shaderGroup+' does not exist!'

    if not geos:
        geos = mc.ls('*_geo')

    mc.connectAttr(fileNode+'.outColor', shader+'.color')

    return(shader, texture, fileNode)





















































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#--------------- ========[ CONTROLS ]======== ---------------#
#------------------------------------------------------------#

def makeIcon(ctrl='object_ctrl', ctrlType=12, colour=6):
    '''
    Creates a nurbs curve shape (ctrl).

    @inParam ctrl - string, name of control
    @inParam ctrlType - int, shape to create
    @inParam colour - int, colour of control

    @ToDo add controls from /hosts/katevale/user_data/scripts/kfShapeCreator.mel

    @procedure rig.makeIcon(ctrl='petal_ctrl', ctrlType=12, colour=6)

    Ctrl Shape
    ------------------------
    1:  Square
    2:  Arrow 3 point
    3:  Star 8 point
    4:  Star 4 point
    5:  Diamond 3 axis
    6:  Diamond 3 axis positive axis extended
    7:  XYZ 3 axis
    8:  Pentagram
    9:  Star 5 point
    10: Star 5 point not crossing
    11: Arrow
    12: Cube
    13: Triangle
    14: Lollipop
    15: Lollipop upside down backwards offset  
    16: Lollipop upside down forwards offset  
    17: Lollipop arrow
    18: Lollipop square
    19: Drop
    20: Drop X axis
    21: Rectangle curved
    22: Plug
    23: T
    24: Hexagon ball
    25: Circle


    Colour
    ------------------------
    0:  Grey (default light)
    1:  Black
    2:  Grey (mid)
    3:  Grey (lightest)
    4:  Red (purpley, dark)
   *5:  Blue (dark)
  **6:  Blue
   *7:  Green (dark)
    8:  Purple
   *9:  Magenta
    10: Brown
    11: Brown (dark)
    12: Brown (orange)
  **13: Red
  **14: Green
  **15: Blue (unsaturated)
  **16: White
    17: Yellow
   *18: Blue (cyan)
    19: Green (cyan)
    20: Pink
    21: Pink (skin)
    22: Yellow (light)
    23: Green (olive, blue)
    24: Brown (wood, tan)
    25: Yellow (mustard)
  **26: Green (unsaturated)
    27: Green (blue)
    28: Blue (grey, cyan)
   *29: Blue (grey)
   *30: Purple Light
    31: Indigo
    '''
    if colour >= 32:
        colour = 17

    #Square
    if ctrlType == 1:
        ctrl = mc.curve(d=1, n=ctrl, p=[(1,-1,0), (1,1,0), (-1,1,0), (-1,-1,0), (1,-1,0)], k=[0,1,2,3,4])
    #Arrow 3 points
    elif ctrlType == 2:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0,0), (4,0,0), (2,1,0)], k=[0,1,2])
    #Eight point star
    elif ctrlType == 3:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,-2,0), (-1.5,1.5,0), (2,0,0), (-1.5,-1.5,0), (0,2,0), (1.5,-1.5,0), (-2,0,0), (1.5,1.5,0), (0,-2,0)], k=[0,1,2,3,4,5,6,7,8])
    #Four point star
    elif ctrlType == 4:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,-1,0), (0.2,-0.2,0), (1,0,0), (0.2,0.2,0), (0,1,0), (-0.2,0.2,0), (-1,0,0), (-0.2,-0.2,0), (0,-1,0)], k=[0,1,2,3,4,5,6,7,8])
    #Three axis diamond
    elif ctrlType == 5:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-1,0,0), (0,-1,0), (1,0,0), (0,1,0), (-1,0,0), (0,0,-1), (1,0,0), (0,0,1), (-1,0,0), (0,0,-1), (0,1,0), (0,0,1), (0,-1,0), (0,0,-1)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13])
    #Three axis diamond positive axis longer
    elif ctrlType == 6:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-1,0,0), (0,-1,0), (2,0,0), (0,2,0), (-1,0,0), (0,0,-1), (2,0,0), (0,0,2), (-1,0,0), (0,0,-1), (0,2,0), (0,0,2), (0,-1,0), (0,0,-1)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13])
    #Three axis xyz icon
    elif ctrlType == 7:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-0.333,2,0), (0,1.666,0), (0.333,2,0), (0,1.666,0), (0,0,0), (1.333,0,0), (2,0.666,0), (1.666,0.333,0), (1.333,0.666,0), (2,0,0), (1.666,0.333,0), (1.333,0,0), (0,0,0), (0,0,2), (0,0.666,1.333), (0,0.666,2)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    #Pentagram
    elif ctrlType == 8:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,1.3,0), (0,0.4,1.24), (0,-1.05,0.77), (0,-1.05,-0.77), (0,0.4,-1.24), (0,1.3,0)], k=[0,1,2,3,4,5])
    #Five point star
    elif ctrlType == 9:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0.4,-1.24), (0,0.4,1.24), (0,-1.05,-0.76), (0,1.3,0), (0,-1.05,0.76), (0,0.4,-1.24)], k=[0,1,2,3,4,5])
    #Five point star not crossing
    elif ctrlType == 10:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,1.3,0), (0,0.53,0.38), (0,0.4,1.24), (0,-0.2,0.62), (0,-1.05,0.76), (0,-0.65,0), (0,-1.05,-0.76), (0,-0.2,-0.62), (0,0.4,-1.24), (0,0.53,-0.38), (0,1.3,0)], k=[0,1,2,3,4,5,6,7,8,9,10])
    #Arrow
    elif ctrlType == 11:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-3,0,-1), (-3,0,1), (1.37,0,0.62), (1,0,1.43), (3,0,0), (1,0,-1.43), (1.37,0,-0.62), (-3,0,-1)], k=[0,1,2,3,4,5,6,7])
    #Cube
    elif ctrlType == 12:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-1,-1,1), (1,-1,1), (1,1,1), (1,1,-1), (1,-1,-1), (-1,-1,-1), (-1,1,-1), (-1,1,1), (1,1,1), (1,-1,1), (1,-1,-1), (1,1,-1), (-1,1,-1), (-1,-1,-1), (-1,-1,1), (-1,1,1)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    #Triangle
    elif ctrlType == 13:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0,0), (2,0,0), (0,1,0), (0,0,0)], k=[0,1,2,3])
    #Lollipop
    elif ctrlType == 14:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0,0), (0,1.5,0), (0.1913417162,1.538060234,0), (0.3535533906,1.646446609,0), (0.4619397663,1.808658284,0), (0.5,2,0), (0.4619397663,2.191341716,0), (0.3535533906,2.353553391,0), (0.1913417162,2.461939766,0), (0,2.5,0), (-0.1913417162,2.461939766,0), (-0.3535533906,2.353553391,0), (-0.4619397663,2.191341716,0), (-0.5,2,0), (-0.4619397663,1.808658284,0), (-0.3535533906,1.646446609,0), (-0.1913417162,1.538060234,0), (0,1.5,0)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17])
    #Lollipop upside down backwards
    elif ctrlType == 15:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0,0), (-4,0,0), (-4,-1.5,0), (-4.191341716,-1.538060234,0), (-4.353553391,-1.646446609,0), (-4.461939766,-1.808658284,0), (-4.5,-2,0), (-4.461939766,-2.191341716,0), (-4.353553391,-2.353553391,0), (-4.191341716,-2.461939766,0), (-4,-2.5,0), (-3.808658284,-2.461939766,0), (-3.646446609,-2.353553391,0), (-3.538060234,-2.191341716,0), (-3.5,-2,0), (-3.538060234,-1.808658284,0), (-3.646446609,-1.646446609,0), (-3.808658284,-1.538060234,0), (-4,-1.5,0)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18])
    #Lollipop upside down
    elif ctrlType == 16:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0,0), (4,0,0), (4,-1.5,0), (4.191341716,-1.538060234,0), (4.353553391,-1.646446609,0), (4.461939766,-1.808658284,0), (4.5,-2,0), (4.461939766,-2.191341716,0), (4.353553391,-2.353553391,0), (4.191341716,-2.461939766,0), (4,-2.5,0), (3.808658284,-2.461939766,0), (3.646446609,-2.353553391,0), (3.538060234,-2.191341716,0), (3.5,-2,0), (3.538060234,-1.808658284,0), (3.646446609,-1.646446609,0), (3.808658284,-1.538060234,0), (4,-1.5,0)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18])
    #Lollipop arrow
    elif ctrlType == 17:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0,0), (0,2,0), (2,2,0), (-1,3,0), (-1,2,0), (0,2,0)], k=[0,1,2,3,4,5])
    #Lollipop Square
    elif ctrlType == 18:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,0,0), (0,1,0), (1,1,0), (1,3,0), (-1,3,0), (-1,1,0), (0,1,0)], k=[0,1,2,3,4,5,6])
    #Drop vert
    elif ctrlType == 19:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0.05357412757,0.1071036246,4.489411397), (-1.728064208,0.2251810969,4.489411398), (-0.05357412757,0.1071036246,4.489411397), (-0.1514676002,-1.4262584,4.489411398), (-0.1071037673,-0.1071039099,4.489411399), (-4.564014401,-0.1514677429,4.4894114), (0.1071037673,-0.1071039099,4.489411399), (0.1514676002,-1.426258402,4.489411398)], k=[0,1,2,3,4,5,6,7])
        mc.closeCurve(ctrl, ps=0, rpo=1, bb=0.5, bki=0, p=0.1)
    #Drop pos x
    elif ctrlType == 20:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0.0734547679,0.03875521624,4.489411397), (-1.185154907,0.1038805864,4.489411397), (-0.0734547679,0.07345462528,4.489411397), (-0.103880729,-1.426258406,4.489411398), (-0.0734547679,-0.07345491053,4.489411399), (-3.130129099,-0.1038808716,4.4894114), (0.0734547679,-0.0387803711,4.489411399), (0.1564712864,-1.426258407,4.489411398)], k=[0,1,2,3,4,5,6,7])
        mc.closeCurve(ctrl, ps=0, rpo=1, bb=0.5, bki=0, p=0.1)
    #Rectangle round edge
    elif ctrlType == 21:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0.3266558791,0.1981452508,0.04705711754), (-7.938781689,0.1897857708,0.04704798392), (-0.3266558791,0.1981452508,0.04705711754), (-0.3472524803,0.04121067774,0.04688564992), (-0.3266558791,-0.1157238953,0.0467141823), (-1.372902367,-0.1073644153,0.04672331591), (0.3266558791,-0.1157238953,0.0467141823), (0.3472524803,0.04121067774,0.04688564992)], k=[0,1,2,3,4,5,6,7])
        mc.closeCurve(ctrl, ps=0, rpo=1, bb=0.5, bki=0, p=0.1)
    #Plug
    elif ctrlType == 22:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-0.1278499647,0.02107834227,0), (0.0001095230931,0.02107834227,0), (0.03095587985,0.09253907028,0), (0.06180223661,0.09253907028,0), (0.06180223661,0.06169271352,0), (0.129183973,0.06169271352,0), (0.129183973,0.03084635676,0), (0.06180223661,0.03084635676,0), (0.06180223661,-0.03084635676,0), (0.129183973,-0.03084635676,0), (0.129183973,-0.06169271352,0), (0.06180223661,-0.06169271352,0), (0.06180223661,-0.09253907028,0), (0.03095587985,-0.09253907028,0), (0.0001095230931,-0.02107834227,0), (-0.1278499647,-0.02107834227,0)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
    #T
    elif ctrlType == 23:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-0.25,-1,0), (0.25,-1,0), (0.25,0.56,0), (0.8,0.56,0), (0.8,1,0), (-0.8,1,0), (-0.8,0.56,0), (-0.25,0.56,0), (-0.25,-1,0)], k=[0,1,2,3,4,5,6,7,8])
    #Hexagon Ball
    elif ctrlType == 24:
        ctrl = mc.curve(d=1, n=ctrl, p=[(0,1,0), (0,0.5,-0.866025), (0,-0.5,-0.866026), (0,-1,0), (0,-0.5,0.866025), (0,0.5,0.866025), (0,1,0), (0.866025,0.5,0), (0.866025,-0.5,0), (0,-1,0), (-0.866026,-0.5,0), (-0.866025,0.5,0), (0,1,0), (0.866025,0.5,0), (0.856939,0,-0.0044503), (0.866025,0,0.5), (0,0,1), (-0.866025,0,0.5), (-0.866026,0,-0.5), (0,0,-1), (0.866025,0,-0.5), (0.866025,0,0.5)], k=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21])
    #Circle Y
    elif ctrlType == 25:
        ctrl = mc.circle(c=(0, 0, 0), nr=(0,1,0), sw=360, r= 1, d=3, ut=0, tol=0.01, s=8, ch=0, n=ctrl)[0]
    #Circle Z    
    elif ctrlType == 26:
        ctrl = mc.circle(c=(0, 0, 0), nr=(0,0,1), sw=360, r= 1, d=3, ut=0, tol=0.01, s=8, ch=0, n=ctrl)[0]
    #Circle X         
    elif ctrlType == 27:
        ctrl = mc.circle(c=(0, 0, 0), nr=(1,0,0), sw=360, r= 1, d=3, ut=0, tol=0.01, s=8, ch=0, n=ctrl)[0]
    elif ctrlType == 28:
        ctrl = mc.curve(d=1, n=ctrl, p=[(-0.5,1,0), (0.5,1,0), (1,0.5,0), (1,-0.5,0), (0.5,-1,0), (-0.5,-1,0), (-1,-0.5,0), (-1,0.5,0), (-0.5,1,0)], k=[0,1,2,3,4,5,6,7,8])

    #No valid number given - create locator and print message
    else:
        ctrl = mc.spaceLocator(n=ctrl)[0]
        print('Invalid number passed. Options are between 1-28, locator created instead.');

    ctrlShape = mc.listRelatives(ctrl, s=1)
    for shape in ctrlShape:
        mc.setAttr(shape+'.overrideEnabled', 1)
        mc.setAttr(shape+'.overrideColor', colour)
        mc.rename(shape, (ctrl+'Shape'))

    return ctrl



def createCtrl(ctrl='object_ctrl', ctrlType=12, snapToObj='', tempParentSnap=0, pos=[0,0,0], rot=[0,0,0], scale=[1,1,1], scaleOffset=[], rotCtrl=[], parent='', consTo='', consType='parent', colour=15, iStack=0, stackNames=[], ctrlVis='', attrsToLock=[], v=1, freezeOffset=False):
    '''
    Create a control object and it's offset.

    @inParam ctrl - string, name of control, make sure it ends with _ctrl
    @inParam ctrlType - int, control shape to create, check makeIcon() above for types of shape
    @inParam snapToObj - string, object to snap joint to and copy rotation values. If object is not given, this proc will use the pos and rot flags
    @inParam tempParentSnap - int, default off. If using snapToObj AND pos flag, use this flag to change behaviour of pos flag to temporarily parent ctrl under snapToObj, then setAttr for positions instead of move -r. Then unparent from snapToObj.
    @inParam pos - list, position of control offset. If snapToObj used, this can also be used to edit the position
    @inParam rot - list, rotation of control offset. If snapToObj used, this can also be used to edit the rotation
    @inParam scale - list, scale of control
    @inParam scaleOffset - list, scales offset of control. 
    @inParam rotCtrl - list, rotation of control
    @inParam parent - string, parent object of the control offset
    @inParam consTo - string, object to constrain ctrl offset to. If left blank, it wont get constrained
    @inParam consType - string, used with consTo flag. Type of constraint between consTo object and ctrl offset, types are parent, point or orient
    @inParam colour - int, colour of control
    @inParam iStack - int, number of additional offset groups
    @inParam stackNames - list, if stack groups are created (using iStack flag), you can override the name using this flag. Only give the suffix, so ctrl.replace('_ctrl', stackNames) - e.g. stackNames='Zero_offset'
    @inParam ctrlVis - string, connect the ctrlVis to this attribute for example rig_preferences.secondaryControls
    @inParam attrsToLock - list, attributes of ctrl to lock
    @inParam v - boolean, visibility of ctrl
    @inParam freezeOffset - boolean, if true freeze transforms of first offet

    @procedure rig.createCtrl(ctrl='object_ctrl', ctrlType=12, colour=15, snapToObj=loc, scale=[1,1,1], parent='', ctrlVis='rig_preferences.secondaryControls', attrsToLock=['tx','ty','tz','rx','ry','rz','sx','sy','sz','v'])

    Ctrl Shape
    ------------------------
  **1:  Square
    2:  Arrow 3 point
   *3:  Star 8 point
   *4:  Star 4 point
  **5:  Diamond 3 axis
    6:  Diamond 3 axis positive axis extended
    7:  XYZ 3 axis
  **8:  Pentagram
   *9:  Star 5 point
  **10: Star 5 point not crossing
  **11: Arrow
  **12: Cube
    13: Triangle
    14: Lollipop
    15: Lollipop upside down backwards offset  
    16: Lollipop upside down forwards offset  
    17: Lollipop arrow
   *18: Lollipop square
    19: Drop
    20: Drop X axis
    21: Rectangle curved
    22: Plug
    23: T
  **24: Hexagon ball
  **25: Circle X
  **26: Circle Y
  **27: Circle Z
  **28: Octagon


    Colour
    ------------------------
    0:  Grey (default light)
    1:  Black
    2:  Grey (mid)
    3:  Grey (lightest)
    4:  Red (purpley, dark)
   *5:  Blue (dark)
  **6:  Blue
   *7:  Green (dark)
    8:  Purple
   *9:  Magenta
    10: Brown
    11: Brown (dark)
    12: Brown (orange)
  **13: Red
  **14: Green
  **15: Blue (unsaturated)
  **16: White
    17: Yellow
   *18: Blue (cyan)
    19: Green (cyan)
    20: Pink
    21: Pink (skin)
    22: Yellow (light)
    23: Green (olive, blue)
    24: Brown (wood, tan)
    25: Yellow (mustard)
  **26: Green (unsaturated)
    27: Green (blue)
    28: Blue (grey, cyan)
   *29: Blue (grey)
   *30: Purple Light
    31: Indigo
    '''

    ctrlOffset = mc.group(n=ctrl.replace('_ctrl', 'Ctrl_offset'), em=1)
    if scaleOffset:
        mc.scale(scaleOffset[0], scaleOffset[1], scaleOffset[2], ctrlOffset, cp=1)

    makeIcon(ctrl=ctrl, ctrlType=ctrlType, colour=colour)
    if rotCtrl:
        mc.rotate(rotCtrl[0], rotCtrl[1], rotCtrl[2], ctrl, r=1)
    mc.scale(scale[0], scale[1], scale[2], ctrl, cp=1)
    mc.parent(ctrl, ctrlOffset)
    mc.makeIdentity(ctrl, apply=1, t=1, r=1, s=1, n=0)

    sStack = ''
    stackOffset = []
    #List of all offsets including the main offset
    ctrlOffsets = [ctrlOffset]

    if iStack > 0:
        for i in range (1, iStack+1):
            if stackNames:
                if i > len(stackNames):
                    print 'Not enough stack names given - must be same amount as iStack'
                    sStack = mc.group(ctrl, n=ctrl.replace('_ctrl', 'Stack%i_offset'%i))
                else:
                    sStack = mc.group(ctrl, n=ctrl.replace('_ctrl', stackNames[i-1]))
            else:
                sStack = mc.group(ctrl, n=ctrl.replace('_ctrl', 'Stack%i_offset'%i))

            stackOffset.append(sStack)
            ctrlOffsets.append(sStack)

    if snapToObj:
        if mc.objExists(snapToObj):
            if '.vtx[' in snapToObj:
                vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                mc.move(vtxPos[0], vtxPos[1], vtxPos[2], ctrlOffset, r=1)
            else:
                mc.delete(mc.parentConstraint(snapToObj, ctrlOffset))

            if pos:
                if tempParentSnap:
                    mc.parent(ctrlOffset, snapToObj)
                    mc.setAttr(ctrlOffset+'.tx', pos[0])
                    mc.setAttr(ctrlOffset+'.ty', pos[1])
                    mc.setAttr(ctrlOffset+'.tz', pos[2])
                    mc.parent(ctrlOffset, w=1)
                else:
                    mc.move(pos[0], pos[1], pos[2], ctrlOffset, r=1)
            if rot:
                if tempParentSnap:
                    mc.parent(ctrlOffset, snapToObj)
                    mc.setAttr(ctrlOffset+'.rx', rot[0])
                    mc.setAttr(ctrlOffset+'.ry', rot[1])
                    mc.setAttr(ctrlOffset+'.rz', rot[2])
                    mc.parent(ctrlOffset, w=1)
                else:
                    mc.rotate(rot[0], rot[1], rot[2], ctrlOffset, r=1)
        else:
            print snapToObj+' does not exist! Cannot snap ctrl offset '+ctrlOffset+' to object.'
    else:
        mc.move(pos[0], pos[1], pos[2], ctrlOffset, r=1)
        mc.rotate(rot[0], rot[1], rot[2], ctrlOffset, r=1)

    if parent:
        if mc.objExists(parent):
            mc.parent(ctrlOffset, parent)
        else:
            print parent+' does not exist! - parent'

    #Freeze transforms of offet
    if freezeOffset:
        mc.makeIdentity(ctrlOffset, apply=1, t=1, r=1, s=1, n=0)

    if consTo:
        if mc.objExists(consTo):
            if consType == 'parent' or consType == 'parentConstraint':
                mc.parentConstraint(consTo, ctrlOffset, mo=1)
            elif consType == 'point' or consType == 'pointConstraint':
                mc.pointConstraint(consTo, ctrlOffset, mo=1)
            elif consType == 'orient' or consType == 'orientConstraint':
                mc.orientConstraint(consTo, ctrlOffset, mo=1)

            mc.scaleConstraint(consTo, ctrlOffset, mo=1)
        else:
            print consTo+' object to constrain control offset to does not exist. @inParam consTo - createCtrl()'


    colourCtrl(ctrls=[ctrl], colour=colour)
    mc.setAttr(ctrl+'.v', v)

    if ctrlVis:
        if mc.objExists(ctrlVis):
            mc.connectAttr(ctrlVis, ctrl+'.v')
        else:
            print ctrlVis+' does not exist, visibility not connected!'


    ctrlVisAttr = addEnumAttr(ctrl, attr='ctrlVis', enumName='Off:On:', dv=1, k=0, cb=1)
    ctrlShapes = mc.listRelatives(ctrl, s=1)
    for ctrlShape in ctrlShapes:
        mc.connectAttr(ctrlVisAttr, ctrlShape+'.overrideVisibility')


    if mc.objExists('animControls'):
        mc.sets(ctrl, add='animControls')
    
    if attrsToLock:
        lockAndHideAttr(ctrl, attrsToLock)

    return [ctrl, ctrlOffset, stackOffset, ctrlOffsets]




def colourCtrl(ctrls=[], colour=1):
    '''
    Colour controls.  

    @inParam ctrls - list, controls to colour
    @inParam colour - int, colour of control

    @procedure rig.colourCtrl(ctrls=['stem_main2_ctrl'], colour=29)

    0:  Grey (default light)
    1:  Black
    2:  Grey (mid)
    3:  Grey (lightest)
    4:  Red (purpley, dark)
   *5:  Blue (dark)
  **6:  Blue
   *7:  Green (dark)
    8:  Purple
   *9:  Magenta
    10: Brown
    11: Brown (dark)
    12: Brown (orange)
  **13: Red
  **14: Green
  **15: Blue (unsaturated)
  **16: White
    17: Yellow
   *18: Blue (cyan)
    19: Green (cyan)
    20: Pink
    21: Pink (skin)
    22: Yellow (light)
    23: Green (olive, blue)
    24: Brown (wood, tan)
    25: Yellow (mustard)
  **26: Green (unsaturated)
    27: Green (blue)
    28: Blue (grey, cyan)
   *29: Blue (grey)
   *30: Purple Light
    31: Indigo
    '''
    #If no controls given, list all controls.
    if not ctrls:
        ctrls = mc.ls('*_ctrl')

    for ctrl in ctrls:
        #For each control, get control shape and colour control.
        ctrlShape = mc.listRelatives(ctrl, s=1)
        for shape in ctrlShape:
            connections = mc.listConnections(shape+'.overrideColor', d=1, p=1, s=1)
            if connections:
                mc.disconnectAttr(connections[0], shape+'.overrideColor')

            mc.setAttr(shape+'.overrideEnabled', 1)
            mc.setAttr(shape+'.overrideColor', colour)


def scaleCtrls(ctrls='*Finger*Fk_ctrl', scale=[0.5,0.5,0.5]):
    '''
    Scale controls. Mainly used for finger controls.

    @inParam ctrls - string, search string for controls
    @inParam scale - list, scale value for controls
    
    @procedure rig.scaleCtrls(ctrls='*Finger*Fk_ctrl', scale=[0.5,0.5,0.5])
    '''
    for ctrl in mc.ls(ctrls):
        pivot = mc.xform(ctrl, q=1, rp=1, ws=1)
        mc.scale(scale[0], scale[1], scale[2], ctrl+'Shape.cv[0:100]', pivot=pivot)



def createCtrlGuideSquare(name='ctrl_guideBox', guideType='square', pos='bottomLeft', scale=[1,1], mirror=0, ctrlOffset='ctrl_offset'):
    '''
        Create a ctrl guide box. It will be a visible indication of where the ctrl can be pulled.

        @inParam name - string, guide box name
        @inParam guideType - string, type of guide box created - square, rectangle, largeSquare
        @inParam pos - string, position ctrl will be in the guide box created. Options for guide type square - [bottomLeft, bottomRight, topLeft, topRight], guide type rectangle - [centreLeft, centreRight], guide type largeSquare - [centre]
        @inParam scale - list, scale of guide box in X and Y
        @inParam mirror - int, default off. If 1, the right hand side ctrl offset is rotated 180 in Y in object space
        @inParam ctrlOffset - string, offset of ctrl, we will snap this guide box to the ctrl offset and parent it's shape under it

        @procedure rig.createCtrlGuideSquare(name='ctrl_guideBox', guideType='square', pos='bottomLeft', scale=[1,1], mirror=0, ctrlOffset='ctrl_offset')
    '''
    if guideType == 'square':
        if pos == 'bottomRight':
            guide = mc.curve(d =1, p =[(0,0,0), (-1,0,0),(-1,1,0), (0,1,0), (0,0,0)], k=[0,1,2,3,4], n=name)
        elif pos == 'topLeft':
            guide = mc.curve(d =1, p =[(0,0,0), (1,0,0),(1,-1,0), (0,-1,0), (0,0,0)], k=[0,1,2,3,4], n=name)
        elif pos == 'topRight':
            guide = mc.curve(d =1, p =[(0,0,0), (-1,0,0),(-1,-1,0), (0,-1,0), (0,0,0)], k=[0,1,2,3,4], n=name)
        else:
            guide = mc.curve(d =1, p =[(0,0,0), (1,0,0),(1,1,0), (0,1,0), (0,0,0)], k=[0,1,2,3,4], n=name)
    elif guideType == 'rectangle':
        if pos == 'centreRight':
            guide = mc.curve(d =1, p =[(0,-1,0), (-1,-1,0),(-1,1,0), (0,1,0), (0,-1,0)], k=[0,1,2,3,4], n=name)
        else:
            guide = mc.curve(d =1, p =[(0,-1,0), (1,-1,0),(1,1,0), (0,1,0), (0,-1,0)], k=[0,1,2,3,4], n=name)
    else:
        guide = mc.curve(d =1, p =[(-1,-1,0), (1,-1,0),(1,1,0), (-1,1,0), (-1,-1,0)], k=[0,1,2,3,4], n=name)

    mc.setAttr(guide+'.sx', scale[0])
    mc.setAttr(guide+'.sy', scale[1])

    mc.select(guide, r=1)
    mm.eval('FreezeTransformations;')
    guideShape = mc.listRelatives(guide)
    guideShape = mc.rename(guideShape, guide+'Shape')
    mc.setAttr(guideShape+'.template', 1)
    
    mc.delete(mc.parentConstraint(ctrlOffset, guide))
    mc.parent(guideShape, ctrlOffset, s=1, r=1)
    mc.delete(guide)

    if mirror:
        if ctrlOffset[0:2] == 'R_':
            mc.rotate(0,180,0, ctrlOffset, r=1, os=1)


def createCtrlToLocalJoint(ctrl='object_ctrl', jointName='', ctrlType=25, snapToObj='', pos=[0,0,0], rot=[0,0,0], scale=[1,1,1], rotCtrl=[0,0,0], ctrlParent='', colour=15, ctrlVis='', attrsToLock=[], jointParent=''):
    '''
        Creates a ctrl that transforms a joint in local space (stay's at origin)

        @inParam ctrl - string, name of control, must have suffix _ctrl
        @inParam jointName - string, name of joint created if you want to override the automatic naming of the joint
        @inParam ctrlType - int, control shape to create, check makeIcon() above for types of shape
        @inParam snapToObj - string, object to snap joint to and copy rotation values. If object is not given, this proc will use the pos and rot flags
        @inParam pos - list, position of control offset
        @inParam rot - list, rotation of control offset
        @inParam scale - list, scale of control
        @inParam rotCtrl - list, rotation of control
        @inParam ctrlParent - string, parent object of the control offset
        @inParam colour - int, colour of control
        @inParam ctrlVis - string, connect the ctrlVis to this attribute for example rig_preferences.secondaryControls
        @inParam attrsToLock - list, attributes of ctrl to lock
        @inParam jointParent - string, jointParent

        @procedure rig.createCtrlToLocalJoint(ctrl='object_ctrl', ctrlType=25, snapToObj=loc, scale=[1,1,1], ctrlParent=ctrlGroup, colour=15, attrsToLock=['rx','ry','rz','sx','sy','sz','v'], jointParent=envGroup)
    '''
    if not ctrl.endswith('_ctrl'):
        ctrl=ctrl+'_ctrl'

    ctrlReturn = createCtrl(ctrl=ctrl, ctrlType=ctrlType, snapToObj=snapToObj, pos=pos, rot=rot, scale=scale, rotCtrl=rotCtrl, parent=ctrlParent, colour=colour, iStack=1, stackNames=['ZeroCtrl_offset'], ctrlVis=ctrlVis, attrsToLock=attrsToLock)
    ctrl = ctrlReturn[0]
    ctrlOffset = ctrlReturn[3]

    if not jointName:
        jointName = ctrl.replace('_ctrl', '_env')

    joint = createJoint(name=jointName, radius=0.5)
    jointOffset = createOffset(obj=joint, stack=1, stackNames=['ZeroJnt_offset'], parent=jointParent, snapToObj=ctrl)

    mc.connectAttr (ctrl+'.translate', joint+'.translate', f=1)
    mc.connectAttr (ctrl+'.rotate', joint+'.rotate', f=1)
    mc.connectAttr (ctrl+'.scale', joint+'.scale', f=1)

    mc.connectAttr(ctrlOffset[1]+'.translate', jointOffset[1]+'.translate', f=1)
    mc.connectAttr(ctrlOffset[1]+'.rotate', jointOffset[1]+'.rotate', f=1)
    mc.connectAttr(ctrlOffset[1]+'.scale', jointOffset[1]+'.scale', f=1)
    mc.sets(ctrl, add='animControls')
    return(ctrl, joint, ctrlOffset, jointOffset)



def createCtrlGuideLine(name='ctrl_guideline', typeOfGuide=1, snapToObj='', pos=[0,0,0], rot=[0,0,0], scale=[1,1,1], transform=''):
    '''
        Creates a ctrl guideline. This is just a templated line which shows the limitations of the ctrl translation.

        @inParam name - string, name of ctrl guideline
        @inParam typeOfGuide - int, type of guideline to create, 
                                    0:T shape - Y axis with bottom of guidline on origin
                                    1:T shape - Y axis with centre on origin
                                    2:Rectangle - Y axis with bottom of guidline on origin
                                    3:Rectangle - Y axis with centre on origin
                                    4:Rectangle Twice Long - Y axis with bottom of guidline on origin
                                    5:Rectangle Twice Long - Y axis with centre on origin
        @inParam snapToObj - string, object to snap joint to and copy rotation values. If snapToObj is not given, this proc will use the pos and rot flags
        @inParam pos - list, position of control offset
        @inParam rot - list, rotation of control offset
        @inParam scale - list, scale of control
        @inParam transform - string, new transform of guideline Shape. If this is provided, the shape will snap to a given transform and be parented under it.

        @procedure rig.createCtrlGuideLine(name='ctrl_guideline', typeOfGuide=1, scale=[1,1,1], transform=transform)
    '''
    #Create the guideline
    if typeOfGuide == 0:
        guide = mc.curve(d=1, p =[(-0.15, 1, 0), (0.15, 1, 0),(0, 1, 0), (0, 0, 0), (0.15, 0, 0), (-0.15, 0, 0), (0, 0, 0)], k=[0, 1, 2, 3, 4, 5, 6], n=name)
    elif typeOfGuide == 1:
        guide = mc.curve(d=1, p =[(-0.15, 0.5, 0), (0.15, 0.5, 0),(0, 0.5, 0), (0, -0.5, 0), (0.15, -0.5, 0), (-0.15, -0.5, 0), (0, -0.5, 0)], k=[0, 1, 2, 3, 4, 5, 6], n=name)
    elif typeOfGuide == 2:
        guide = mc.curve(d=1, p =[(0.1, 0, 0), (0.1, 1, 0), (-0.1, 1, 0), (-0.1, 0, 0), (0.1, 0, 0)], k=[0, 1, 2, 3, 4], n=name)
    elif typeOfGuide == 3:
        guide = mc.curve(d=1, p =[(0.1, -0.5, 0), (0.1, 0.5, 0), (-0.1, 0.5, 0), (-0.1, -0.5, 0), (0.1, -0.5, 0)], k=[0, 1, 2, 3, 4], n=name)
    elif typeOfGuide == 4:
        guide = mc.curve(d=1, p =[(0.1, 0, 0), (0.1, 2, 0), (-0.1, 2, 0), (-0.1, 0, 0), (0.1, 0, 0)], k=[0, 1, 2, 3, 4], n=name)
    elif typeOfGuide == 5:
        guide = mc.curve(d=1, p =[(0.1, -1, 0), (0.1, 1, 0), (-0.1, 1, 0), (-0.1, -1, 0), (0.1, -1, 0)], k=[0, 1, 2, 3, 4], n=name)
            
    #Scale guideline
    mc.scale(scale[0],scale[1],scale[2], guide, ws=1)
    
    #Freeze transforms of guideline
    mc.makeIdentity(guide, apply=1, t=1, r=1, s=1, n=0)

    #Rename guideline shape to nice name.
    shape = mc.listRelatives(guide)
    shape = mc.rename(shape, guide+'Shape')

    #Template guideline
    mc.setAttr(shape+'.template', 1)

    if transform:
        mc.parent(shape, transform, s=1, r=1)
        mc.delete(guide)
    elif snapToObj:
        if mc.objExists(snapToObj):
            if '.vtx[' in snapToObj:
                vtxPos = mc.xform(snapToObj, q=1, t=1, ws=1)
                mc.move(vtxPos[0], vtxPos[1], vtxPos[2], guide, r=1)
            else:
                mc.delete(mc.parentConstraint(snapToObj, guide))
        else:
            print snapToObj+' does not exist! Cannot snap ctrl offset '+guide+' to object.'
    else:
        mc.move(pos[0], pos[1], pos[2], guide, r=1)
        mc.rotate(rot[0], rot[1], rot[2], guide, r=1)




def addPivotToCtrl(ctrl='cane_ctrl', ctrlColour=26):
    '''
    Creates a pivot ctrl for the ctrl specified. You can translate the pivot control which affects the rotate pivot of the control. We also create a modify group under the
    ctrl so that any joint affected by the control doesn't get affected with pivot control.

    @inParam ctrl - string, ctrl to add pivot control for
    @inParam ctrlColour - int, colour of ctrl

    @procedure rig.addPivotToCtrl(ctrl='cane_ctrl', ctrlColour=26)
    '''
    #Creates a modify group, a group that is parented underneath the given ctrl or object and takes all of it's constraints or connections. Any children of the object
    #will be parented under this. This allows the pivot ctrl to control the rotate pivot of the ctrl.
    modifyGrp = createModifyGrp(ctrl)

    #Create pivot ctrl  
    pivot = mc.curve( d=1, p=[ (0.0409709, 0.49978, 0.0409709), (0.0409709, 0.49978, -0.0409709), (-0.0409709, 0.49978, -0.0409709), (-0.0409709, 0.49978, 0.0409709), (0.0409709, 0.49978, 0.0409709), (0.0111978, 0.0111978, 0.0111978), (0.0111978, 0.0111978, -0.0111978), (0.0409709, 0.49978, -0.0409709), (-0.0409709, 0.49978, -0.0409709), (-0.0111978, 0.0111978, -0.0111978), (-0.0111978, 0.0111978, 0.0111978), (-0.0409709, 0.49978, 0.0409709), (-0.0111978, 0.0111978, 0.0111978), (-0.0408581, 0.0408581, 0.49978), (0.0408581, 0.0408581, 0.49978), (0.0408581, -0.0408581, 0.49978), (-0.0408581, -0.0408581, 0.49978), (-0.0408581, 0.0408581, 0.49978), (-0.0111978, 0.0111978, 0.0111978), (0.0111978, 0.0111978, 0.0111978), (0.0408581, 0.0408581, 0.49978), (0.0408581, -0.0408581, 0.49978), (0.0111978, -0.0111978, 0.0111978), (-0.0111978, -0.0111978, 0.0111978), (-0.0408581, -0.0408581, 0.49978), (-0.0111978, -0.0111978, 0.0111978), (-0.040837, -0.49978, 0.040837), (0.040837, -0.49978, 0.040837), (0.040837, -0.49978, -0.040837), (-0.040837, -0.49978, -0.040837), (-0.040837, -0.49978, 0.040837), (-0.0111978, -0.0111978, 0.0111978), (-0.0111978, -0.0111978, -0.0111978), (-0.040837, -0.49978, -0.040837), (0.040837, -0.49978, -0.040837), (0.0111978, -0.0111978, -0.0111978), (0.0111978, -0.0111978, 0.0111978), (0.040837, -0.49978, 0.040837), (0.0111978, -0.0111978, 0.0111978), (0.49978, -0.0355771, 0.0355771), (0.49978, 0.0355771, 0.0355771), (0.49978, 0.0355771, -0.035577), (0.49978, -0.0355771, -0.035577), (0.49978, -0.0355771, 0.0355771), (0.0111978, -0.0111978, 0.0111978), (0.0111978, -0.0111978, -0.0111978), (0.49978, -0.0355771, -0.035577), (0.49978, 0.0355771, -0.035577), (0.0111978, 0.0111978, -0.0111978), (0.0111978, 0.0111978, 0.0111978), (0.49978, 0.0355771, 0.0355771), (0.0111978, 0.0111978, 0.0111978), (-0.0111978, 0.0111978, 0.0111978), (-0.49978, 0.0356443, 0.0356443), (-0.49978, -0.0356443, 0.0356443), (-0.49978, -0.0356443, -0.0356443), (-0.49978, 0.0356443, -0.0356443), (-0.49978, 0.0356443, 0.0356443), (-0.0111978, 0.0111978, 0.0111978), (-0.0111978, 0.0111978, -0.0111978), (-0.49978, 0.0356443, -0.0356443), (-0.49978, -0.0356443, -0.0356443), (-0.0111978, -0.0111978, -0.0111978), (-0.0111978, -0.0111978, 0.0111978), (-0.49978, -0.0356443, 0.0356443), (-0.0111978, -0.0111978, 0.0111978), (-0.0111978, -0.0111978, -0.0111978), (-0.0407955, -0.0407955, -0.49978), (-0.0407955, 0.0407955, -0.49978), (0.0407955, 0.0407955, -0.49978), (0.0407955, -0.0407955, -0.49978), (-0.0407955, -0.0407955, -0.49978), (-0.0111978, -0.0111978, -0.0111978), (0.0111978, -0.0111978, -0.0111978), (0.0407955, -0.0407955, -0.49978), (0.0407955, 0.0407955, -0.49978), (0.0111978, 0.0111978, -0.0111978), (-0.0111978, 0.0111978, -0.0111978), (-0.0407955, 0.0407955, -0.49978), (-0.0407955, 0.0407955, -0.49978), (-0.0111978, 0.0111978, -0.0111978), (-0.0111978, -0.0111978, -0.0111978), (-0.0111978, -0.0111978, 0.0111978), (-0.0111978, 0.0111978, 0.0111978), (0.0111978, 0.0111978, 0.0111978), (0.0111978, -0.0111978, 0.0111978), (0.0111978, -0.0111978, -0.0111978), (0.0111978, 0.0111978, -0.0111978) ] )
    pivotShape = mc.listRelatives( pivot, s=1 )
    name = ctrl.replace('_ctrl', 'Pivot_ctrl' )    
    shapeName = ctrl.replace('_ctrl', 'Pivot_ctrlShape' )    
    pivotCtrl = pm.mel.eval( 'dnLibControl_makeIk(dnLibShape_circleAxes(("'+name+'"), <<0,0,1>>, 1.0), 1, "")' )
    pivotCtrlShape = mc.listRelatives( pivotCtrl[1], f=1, s=1 )
    mc.parent( pivotShape, pivotCtrl[1], r=1, s=1 )
    mc.delete( pivotCtrlShape )
    mc.setAttr( pivotShape[0]+'.drawOverride.overrideColor', l=0 )
    mc.setAttr( pivotShape[0]+'.drawOverride.overrideColor', 17 )
    pivotShape[0] = mc.rename( pivotShape[0], shapeName )
    
    #Add vis attr
    pivotVis = addEnumAttr(ctrl, attr='pivotVisibility', enumName='Off:On:', dv=1, k=1, cb=1)
    mc.connectAttr( pivotVis, pivotShape[0]+'.v' )
    
    #Setup so it works with scale. This will only work if the scale value doesn't change on the ctrl itself.
    #If I plug the translate of the pivot ctrl directly into the ctrl's rotate pivot, scaling of the hierarchy doesn't get taken into account because it's a direct connection.
    #I create a multMatrix and multiply the rotate pivot ctrl's world matrix with the inverseMatrix of the ctrl - but still taking into account the scale of the hierarchy.
    #To do this I create a locator parented under the ctrl and scale it by 1/Ctrl's world scale. I plug the pivot ctrl world matrix into the multMatrix first, and then plug the
    #locator's inverseMatrix into the multMatrix's second plug. Remember the locator is scaled so the inverseMatrix will be affected. Finally I use a decompose matrix after
    #the mult matrix and plug the outputTranslate into the ctrl's rotate pivot.
    ctrlParent = mc.listRelatives(ctrl, p=1)[0]

    '''
    ctrlScale = getTransforms(obj=ctrl, attrType='world')
    scaleLoc = createLoc(name=ctrl.replace('_ctrl', 'ScalePivot_loc'), snapToObj=ctrl, parent=ctrl, v=0)
    setTransforms(obj=scaleLoc, s=[(1/ctrlScale['s'][0]), (1/ctrlScale['s'][1]), (1/ctrlScale['s'][2])])

    multMatrix = mc.createNode('multMatrix', n=ctrl+'_multMatrix')
    mc.connectAttr(pivotCtrl[1]+'.worldMatrix[0]', multMatrix+'.matrixIn[0]')
    mc.connectAttr(scaleLoc+'.worldInverseMatrix[0]', multMatrix+'.matrixIn[1]')

    decomposeMatrix = mc.createNode('decomposeMatrix', n=ctrl+'_decomposeMatrix')
    mc.connectAttr(multMatrix+'.matrixSum', decomposeMatrix+'.inputMatrix')

    mc.connectAttr(decomposeMatrix+'.outputTranslate', ctrl+'.rotatePivot', f=1)
    '''

    mc.connectAttr(pivotCtrl[1]+'.translate', ctrl+'.rotatePivot', f=1)

    mc.parent( pivotCtrl[1], ctrl, r=1 )
    mc.delete( pivot, pivotCtrl[0] )


    colourCtrl(ctrls=[pivotCtrl[1]], colour=ctrlColour)

    #Clean up pivot ctrl

    lockAndHideAttr(pivotCtrl[1], ['rx','ry','rz','sx','sy','sz'])
    unlockAttr(obj=pivotCtrl[1], attrs=['v'])

    returnInfos = [pivotCtrl[1]]
    returnInfos.append(modifyGrp)
    return returnInfos




def createModifyGrp(ctrl):
    '''
    Creates a modify group, a group that is parented underneath the given ctrl or object and takes all of it's constraints or connections. Any children of the object
    will be parented under this. This is in conjunction with addPivotToCtrl. This allows the pivot ctrl to control the rotate pivot of the ctrl.

    @inParam ctrl - string, ctrl to create modify group for

    @procedure rig.createModifyGrp(ctrl='cane_main1_ctrl')
    '''

    #Create a mod group
    relativeGroups = mc.listRelatives( ctrl, typ='transform' )
    mod = mc.group( em=1, n=ctrl.replace('_ctrl', 'Mod_grp') )
    mc.parent( mod, ctrl, r=1 )
    
    #Parent and constraint all obj to Mod group
    if not type(relativeGroups).__name__ == 'NoneType':
        mc.parent( relativeGroups, mod )
    allConnections = mc.listConnections(ctrl, c=1, d=1, p=1, s=1)
    for i in range(0,len(allConnections),2):
        s = allConnections[i]
        d = allConnections[i+1]
        if not s.split('.')[-1] in str( mc.listAttr(ctrl,ud=1) ):
            if mc.isConnected( s, d ):
                mc.disconnectAttr( s, d )
            mc.connectAttr( mod+'.'+s.split('.')[-1], d, f=1 )
    return mod



def changeModuleCtrlShape(ctrl='', newCtrlType=11):
    '''
    Creates a modify group, a group that is parented underneath the given ctrl or object and takes all of it's constraints or connections. Any children of the object
    will be parented under this. This is in conjunction with addPivotToCtrl. This allows the pivot ctrl to control the rotate pivot of the ctrl.

    @inParam ctrl - string, ctrl to create modify group for

    @procedure rig.createModifyGrp(ctrl='cane_main1_ctrl')
    '''    

    print 'TODO'


#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#--------------- ========[ ATTRIBUTES ]======== -------------#
#------------------------------------------------------------#

def lockAndHideAttr(obj='', attrs=[]):
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


def unlockAttr(obj='', attrs=[]):
    '''
    Unlock and show attributes of given object.

    @inParam obj - string, object to unlock attributes for
    @inParam attrs - list, attributes to unlock

    @procedure rig.unlockAttr(obj=ctrl, attrs=['tx','ty','tz','rx','ry','rz','sx','sy','sz','v'])
    '''
    for attr in attrs:
        if mc.attributeQuery(attr, node=obj, ex=1):
            mc.setAttr(obj+'.'+attr, e=1, cb=1)
            mc.setAttr(obj+'.'+attr, e=1, k=1)
            mc.setAttr(obj+'.'+attr, e=1, l=0)
        else:
            print 'Attribute does not exist for '+obj+' - '+attr


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


def addEnumAttr(ctrl='', attr='', enumName='', nn='', dv=0, k=1, cb=1, l=False):
    '''
    Adds enum attribute to object.

    @inParam ctrl - string, object to add attribute to
    @inParam attr - string, name of attribute
    @inParam enumName - string, names of switches
    @inParam nn - string, nice name of attribute
    @inParam dv - float, default value value of attribute
    @inParam k - int, attribute is keyable if on
    @inParam cb - int, attribute appears in cb if on
    @inParam l - boolean, lock attr if true

    @procedure rig.addEnumAttr(ctrl=ctrl, attr='waveVis', enumName='Off:On:', dv=0, k=1, cb=1)
    '''
    if nn == '':
        mc.addAttr(ctrl, ln=attr, at='enum', enumName=enumName, dv=dv)
    else:
        mc.addAttr(ctrl, ln=attr, nn=nn, at='enum', enumName=enumName, dv=dv)

    if cb:
        mc.setAttr(ctrl+'.'+attr, e=1, cb=1)
    if k:
        mc.setAttr(ctrl+'.'+attr, e=1, k=1)
    if l:
        mc.setAttr(ctrl+'.'+attr, l=1)

    return ctrl+'.'+attr


def addStringAttr(ctrl='', attr='', string='', nn=''):
    '''
    Adds string attribute to object.

    @inParam ctrl - string, object to add attribute to
    @inParam attr - string, name of attribute
    @inParam string - string, attribute string value
    @inParam nn - string, nice name of attribute

    @procedure rig.addStringAttr(ctrl, attr='notes', string='This awesome note')
    '''
    if nn == '':
        mc.addAttr(ctrl, ln=attr, dt='string')
    else:
        mc.addAttr(ctrl, ln=attr, nn=nn, dt='string')

    mc.setAttr(ctrl+'.'+attr, string, type='string')
    return ctrl+'.'+attr


def templateSwitch(attr='mast_ctrl.ropeVis', geos=[]):
    '''
    Creates a template switch, usually used so that geoemtry isn't cached if it's not visible. If templated, geo wont be cached. 

    @inParam attr - string, ctrl attribute name to connect switch to
    @inParam geos - list, list of geometry to apply template to
    
    @procedure rig.templateSwitch(attr='mast_ctrl.ropeVis', geos=['flag_geo'])
    '''
    #Create reverse node so that when visibility is on, it's not templated, and the opposite for when vis is off.
    reverseNode = mc.shadingNode('reverse', asUtility=1, n=attr.split('.')[1]+'_reverse')
    mc.connectAttr(attr, reverseNode+'.inputX')

    #Connect the reverse node to visibility and the switch attribute to template.
    #Connect reverse node to geometry template switch and the visibility attribute to the visibility flag.
    node = attr.split('.')[0]
    attribute = attr.split('.')[1]
    if mc.attributeQuery(attribute, node=node, ex=1):
        if geos:
            for geo in geos:
                if mc.objExists(geo):
                    mc.connectAttr(reverseNode+'.outputX', geo+'.template')
                    mc.connectAttr(attr, geo+'.v')
                else:
                    print 'templateSwitch(), @inParam geos: '+geo+' does not exist!'
        else:
            print 'templateSwitch(), @inParam geos: No geo given'
    else:
        print 'templateSwitch(), @inParam attr: '+attr+' does not exist!'

    return reverseNode



def createReverseSwitch(attr='', drivenAttr=[], name=''):
    '''
    Creates a reverse switch for a given attribute. Useful for parent constraints for example where one is On the the other Off. 
    The attr will drive the two driven attributes that are given. The first drivenAttr will have a straight connection to the attr, the second drivenAttr will have 
    a reverseNode plugged into it.

    @inParam attr - string, attribute to drive the drivenAttr (obj.attr)
    @inParam drivenAttr - list, two driven attributes, the second will reversed. You can pass it a list or string.
    
    @procedure rig.createReverseSwitch(attr=followEyeAttr, drivenAttr=[orientConstraint+'.'+obj+'W0', orientConstraint+'.'+obj+'W1'])
    '''
    #Create reverse node for the second drivenAttr
    if name:
        reverseNode = mc.shadingNode('reverse', asUtility=1, n=name)
    else:    
        reverseNode = mc.shadingNode('reverse', asUtility=1, n=attr.split('.')[1]+'_reverse')
    mc.connectAttr(attr, reverseNode+'.inputX')


    if type(drivenAttr[0]) is list:
        for drivenAttribute in drivenAttr[0]:
            mc.connectAttr(attr, drivenAttribute)
    else:
        mc.connectAttr(attr, drivenAttr[0])

    if type(drivenAttr[1]) is list:
        for drivenAttribute in drivenAttr[1]:
            mc.connectAttr(reverseNode+'.outputX', drivenAttribute)
    else:
        mc.connectAttr(reverseNode+'.outputX', drivenAttr[1])

    return reverseNode


def connectObjAttrs(sourceObj='', destObj='', attrs=[]):
    '''
    Connect the attributes sepcified from the source object to the destination object.

    @inParam sourceObj - string, source object
    @inParam destObj - string, destination object 
    @inParam attrs - list, attributes to connect

    @procedure rig.connectObjAttrs(sourceObj='L_hand_ctrl', destObj='R_hand_ctrl', attrs=['tx','ty','tz','rx','ry','rz','sx','sy','sz','v'])
    '''
    for attr in attrs:
        if mc.attributeQuery(attr, node=sourceObj, ex=1):
            if mc.attributeQuery(attr, node=destObj, ex=1):
                mc.connectAttr(sourceObj+'.'+attr, destObj+'.'+attr, f=1)
            else:
                print 'Attribute does not exist for '+destObj+' - '+attr
        else:
            print 'Attribute does not exist for '+sourceObj+' - '+attr


def copyCtrlAttr (source,target):
    '''
    Copies all user defined attrs from source to target. 
    Set the lock, keyable and channel box visibility of default attrs.

    @inParam source - string, object to copy attributes from
    @inParam target - string, object to copy attributes to

    @procedure rig.copyCtrlAttr('L_arm_mainIk_ctrl','L_arm_mainIkNew_001_ctrl')
    '''
    defaultAttrs = ['tx','ty','tz','rx','ry','rz','sx','sy','sz','v','rotateOrder']
    for a in defaultAttrs:
        cbValue = mc.getAttr(source+'.'+a,cb=True)
        if cbValue == True:
            mc.setAttr (target+'.'+a,cb=True)
        lock = mc.getAttr(source+'.'+a,lock=True)
        if lock == True:
            mc.setAttr (target+'.'+a, lock=True)
        keyValue= mc.getAttr(source+'.'+a,  k=True)
        if keyValue == False:
            mc.setAttr (target+'.'+a, k=False)
        if a == 'rotateOrder':
            defaultValue = mc.getAttr (source+'.'+a)
            mc.setAttr (target+'.'+a,defaultValue)
    udAttrs = mc.listAttr (source, ud=True)
    for a in udAttrs:
        keyValue= mc.attributeQuery(a, node = source, k=True)
        attrType= mc.attributeQuery(a, node = source, at=True) 
        if attrType =='typed':
            typedString = mc.getAttr (source+'.'+a)
            mc.addAttr (target, ln=a, dt='string', k=keyValue) 
            mc.setAttr (target+'.'+a, typedString, type='string')
        elif attrType == 'compound':
            children= mc.attributeQuery(a, node = source, nc=True)[0] 
            mc.addAttr (target, ln=a, at=attrType, nc=children, k=keyValue)   
        elif attrType == 'enum':
            enumList = mc.attributeQuery(a, node = source, le=True)[0]
            mc.addAttr (target, ln=a, at=attrType, enumName=enumList, k=keyValue)             
        else:
            mc.addAttr (target, ln=a, at=attrType, k=keyValue)   
            if  mc.attributeQuery(a, node = source, minExists=True)==True:
                bMin= mc.attributeQuery(a, node = source, min=True)[0]
                mc.addAttr (target+'.'+a, e=True, minValue = bMin)
            if  mc.attributeQuery(a, node = source, maxExists=True)==True:   
                bMax= mc.attributeQuery(a, node = source, max=True)[0]      
                mc.addAttr (target+'.'+a, e=True, maxValue = bMax)
        if not attrType == 'compound':
            if not attrType == 'message':
                attrValue = mc.getAttr (source+'.'+a)
                print type (attrValue)
                if isinstance(attrValue, (int, long, float, complex)) ==True:
                    mc.setAttr (target+'.'+a, attrValue)
                defaultValue = mc.attributeQuery(a, node = source, ld=True)
                if defaultValue:
                    mc.addAttr (target+'.'+a, e=True, dv = defaultValue[0])



def addWindAttrs (sCtrl):
    '''
        Adds standard wind attrs to a controller and the necessary nodes. Ready for attachment to a cacheFile

        @inParam sCtrl - string, name of controller              

        @procedure rig.addWindAttrs ('wind_ctrl')  
    '''    
    addEnumAttr(sCtrl, 'windAttrs', '-------------:------------:', 0, nn='Wind Attributes',k=0, cb=1)  
    #Wind Intensity####################################################
    mc.addAttr(sCtrl, ln='windIntensity', at='double', dv=0, min=0, k=True)
    sWindIntensityOut = sCtrl+'.windIntensity'
    #Wind Speed######################################################
    mc.addAttr(sCtrl, ln='windSpeed', at='double', dv=1,min=0.1, k=True)  
    sWindSpeedMD = mc.createNode ('multiplyDivide',n=sCtrl+'_windSpeedMD')
    mc.connectAttr (sCtrl+'.windSpeed',sWindSpeedMD+'.input2X',f=True)
    mc.setAttr (sWindSpeedMD+'.input1X',1)
    mc.setAttr (sWindSpeedMD+'.operation', 2)
    sWindSpeedOut = sWindSpeedMD+'.outputX'
    #Wind Offset#######################################################
    mc.addAttr(sCtrl, ln='windOffset', at='double', dv=1, k=True)
    sWindOffsetOut = sCtrl+'.windOffset'
    #Time Ramp#########################################################
    sTimeRampOverride = addEnumAttr(sCtrl, attr='timeRampOverride', enumName='Off:On:', dv=0, k=0, cb=1)        
    mc.addAttr(sCtrl, ln='timeRampFrame', at='double', dv=1, k=True)
    sTimeRampCND = mc.createNode ('condition', n=sCtrl+'_timeRampCND')
    mc.connectAttr (sTimeRampOverride, sTimeRampCND+'.firstTerm',f=True)    
    mc.setAttr (sTimeRampCND+'.secondTerm', 1)
    mc.connectAttr ('time1.outTime', sTimeRampCND+'.colorIfFalseR',f=True)
    mc.connectAttr (sCtrl+'.timeRampFrame', sTimeRampCND+'.colorIfTrueR',f=True)
    sTimeRampOut = sTimeRampCND+'.outColorR'
    #Wind Reverse####################################################
    sWindReverseOut = addEnumAttr(sCtrl, attr='windReverse', enumName='Off:On:', dv=0, k=0, cb=1)      

    return (sWindIntensityOut, sWindSpeedOut, sWindOffsetOut,sTimeRampOut,sWindReverseOut)   




















































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#----------- ========[ ANIMATION ]======== ------------#
#------------------------------------------------------#

def setDrivenKey(driver='', driven='', driverValue=[0,1], drivenValue=[0,1], itt='linear', ott='linear'):  
    '''
    Set driven key using driver and driven attributes.

    @inParam driver - string, driver attribute e.g. driver_ctrl.attr
    @inParam driven - string, driven attribute e.g. driven_ctrl.attr
    @inParam driverValue - list, driver attribute values, can provide any number of values. This value will drive the corresponding driven attribute
    @inParam drivenValue - list, driven attribute values, can provide any number of values. This value will be driven by the corresponding driver attribute
    @inParam itt - string, inTangentType of key: 'spline,' 'linear,' 'fast,' 'slow,' 'flat,' 'step,' 'stepnext,' 'fixed,' 'clamped,' 'plateau' and 'auto'
    @inParam ott - string, outTangentType of key: 'spline,' 'linear,' 'fast,' 'slow,' 'flat,' 'step,' 'stepnext,' 'fixed,' 'clamped,' 'plateau' and 'auto'

    @procedure rig.setDrivenKey(driver=driverCtrlAttr, driven=drivenCtrlAttr, driverValue=[0,1], drivenValue=[0,1], itt='linear', ott='linear')
    '''    
    for i in range(len(driverValue)):
        mc.setAttr(driver, driverValue[i])
        mc.setAttr(driven, drivenValue[i])
        mc.setDrivenKeyframe(driven, currentDriver=driver, itt=itt, ott=ott)
    
    driverCtrl = driver.split('.')
    defaultValue = mc.attributeQuery(driverCtrl[1], node=driverCtrl[0], ld=1)[0]
    mc.setAttr(driver, defaultValue)





#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#------------- ========[ CLOTH ]======== -------------#
#------------------------------------------------------#
def createNCloth(geo='', world=0):
    '''
    Create nCloth on given geo.

    @inParam geo - string, geo to create nCloth for
    @inParam world - boolean, either create nCloth in local space or world space, default is local space

    @procedure rig.createNCloth(geo='coat_geo')
    '''    
    mc.select(geo, r=1)
    if world == 0:
        nClothShape = mm.eval('createNCloth 0')
    else:
        nClothShape = mm.eval('createNCloth 1')

    #Rename intermediate shape to OrigShape
    geoShape =  mc.listRelatives(geo, type='shape')
    if geoShape:
        for shape in geoShape:
            if mc.getAttr(shape+'.intermediateObject') == 1:
                origShape = shape.replace('Shape','OrigShape')
                mc.rename(shape, origShape)

    nCloth = mc.listRelatives(nClothShape[0], parent=1)[0]
    nCloth = mc.rename(nCloth, geo.replace('_mesh','_cloth'))

    #Search for the output Mesh
    ouputCloth = mc.connectionInfo(nCloth+'Shape.outputMesh', destinationFromSource=1)[0]
    ouputCloth = ouputCloth.split('.')[0]
    ouputCloth = mc.rename(ouputCloth, geo+'Shape')

    return (nCloth, ouputCloth)





def pop_fixer(face_selection = None, smooth_iterations = 20):
    '''
    Fixes pops in deforming mesh. Excellent for nCloth.

    @inParam faces - list, geo faces to smooth pop for
    @inParam smoothIterations - int, number of smooth interations

    @procedure rig.pop_fixer()
    '''  
    face_selection = face_selection or mc.filterExpand(sm=34)
    mesh = face_selection[0].split('.')[0]
    inMesh = mc.listConnections(mesh+'.inMesh', sh=True, s=1,d=0,p=1)[0]
    # 1. create group
    if not mc.objExists('pop_fixer_grp'):
        mc.group(em=True, n='pop_fixer_grp')
    frame = mc.currentTime(q=True)
    xform = mc.createNode('transform', n='%s_fr_%04d_flat_mesh' % (mesh, frame), p='pop_fixer_grp')
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






#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#----------- ========[ SHOTSCULPT ]======== -----------#
#------------------------------------------------------#


def createShotSculptGeo(geos=[]):
    '''
    Create shotsculpt geo for geometry given and tag as inDeform, place them in a layer, colour them.

    @inParam geos - list, geometry to create shotsculpt geo and inDeform for

    @procedure rig.createShotSculptGeo()
    '''  
    if geos == []:
        geos = mc.ls('*_geo')

    sculptGrps = []
    sculptMeshes = []
    for node in geos:
        obj = mc.duplicate(node, n=node.replace('_geo', '_sculpt'))
        parentGrp = mc.listRelatives(obj[0], parent=True)
        sculptGrp = 'Sculpts_grp'
        if parentGrp:
            sculptGrp = parentGrp[0].rsplit('_',1)[0]+'_sculpts_null'
            if not mc.objExists(sculptGrp):
                mc.createNode('transform', n=sculptGrp, p=parentGrp[0])
                sculptGrps.append(sculptGrp)
        elif not mc.objExists(sculptGrp):
            mc.createNode('transform', n=sculptGrp)
            sculptGrps.append(sculptGrp)
        obj = mc.parent(obj, sculptGrp)[0]
        mc.connectAttr(obj+'.outMesh', node+'.inMesh')
        sculptMeshes.append(obj)

    #Add inDeform tag for all sculpt geo
    mc.select(sculptMeshes,r=1)
    mm.eval('dnLibConnectRigs_multiInDeform(`ls -sl -type "transform" "*_sculpt"`);')

    #Create and assign a sculpt shader
    shader = mc.shadingNode("blinn", asShader=True, name='sculpt_shader')
    mc.setAttr(shader+'.color', 0.510, 0.199, 0.484)
    mc.setAttr(shader+'.specularColor', 0.122, 0.122, 0.122)
    mc.setAttr(shader+'.eccentricity', 0.300)

    mc.select(mc.ls("*_sculpt"))
    mc.hyperShade(assign="sculpt_shader")

    #Create layers
    mc.select(cl = 1)
    sculptLayer = 'sculptGeo_layer'
    mc.createDisplayLayer(name = sculptLayer)
    mc.setAttr(sculptLayer+'.color', 8)
    mc.setAttr(sculptLayer+'.visibility', 0)
    for sculptGrp in sculptGrps:
        mc.editDisplayLayerMembers(sculptLayer, sculptGrp, noRecurse=1)

    #Render Layer:
    renderLayer = 'renderGeo_layer'
    mc.createDisplayLayer(name = renderLayer)
    mc.setAttr(renderLayer+'.displayType', 2)
    for geo in allGeo:
        mc.editDisplayLayerMembers(renderLayer, geo, noRecurse=1)

    #Hide other meshes if they exist
    meshes = mc.ls('*_mesh')
    for mesh in meshes:
        mc.hide(mesh)





























































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#------------ ========[ FACE RIG ]======== ------------#
#------------------------------------------------------#

def setupLayer(name='layer', geos=[], transformMesh=''):
    '''
        Creates the hierarchy and geometry used for the layer rig e.g. squashAndStretch or blendShapes layer. It also creates the layer root joint.
        Every layer has the following groups created parented under the layer group:
        Mesh Group - Contains all geoemetry for the layer. 
        Env Group - Contains all joints for the layer. 
        Ctrl Group - Contains all controls for the layer. 
        Rig Group - Contains all rigging junk for the layer, ikHandles, deformers etc. 

        @inParam name - string, name of the layer to setup
        @inParam geos - list, geoemetry to duplicate and create deformations for the layer. Make sure it ends with _geo!! If none given, it searches for all geo. 
        @inParam transformMesh - string, name of the meshTransformOutput mesh. This is usually a file import in the pinocchio session. This proxy mesh of the face geo is used for to transform the controls so they move with the mesh correctly as it deforms.

        @procedure rig.setupLayer(name='blendShapes', transformMesh='meshTransformOutput')
    '''
    #Create layer groups
    layerGroup = mc.group(em= 1, n=name+'_grp')
    meshGroup = mc.group(em=1, n=name+'_mesh_grp')
    envGroup = mc.group(em=1, n=name+'_env_grp')
    ctrlGroup = mc.group(em=1, n=name+'_ctrl_grp')
    rigGroup = mc.group(em=1, n=name+'_rig_grp')

    mc.parent(layerGroup, 'rig')
    mc.parent(meshGroup,envGroup,ctrlGroup,rigGroup, layerGroup)

    #If no geometry list given, find all geo. If geometry is given, check it exists.
    if geos:
        for geo in geos:
            if not mc.objExists(geo):
                print geo+' does not exist!'
                geos.remove(geo)
    else:
        geos = mc.ls('*_geo')

    #Duplicate the geometry and rename it to the layer name. All rigging in this layer will happen on this geometry.
    layerGeos = [mc.duplicate(g, n=g.replace('_geo', '_'+name))[0] for g in geos]
    mc.parent(layerGeos, meshGroup)

    #Check transform mesh exists, and then duplicate it and rename it to the layer.
    if mc.objExists(transformMesh):
        layerTransformMesh = mc.duplicate(transformMesh, n=name+'_'+transformMesh)[0]
        mc.parent(layerTransformMesh, rigGroup)
    else:
        print transformMesh+' does not exist!'
        layerTransformMesh = transformMesh

    #Create layer root joint
    mc.select(cl=1)
    rootJoint = mc.joint(p=(0,0,0), n=name+'_root_env')
    mc.parent(rootJoint, envGroup)

    #Cleanup
    for group in [meshGroup, envGroup, rigGroup]:
        mc.setAttr(group+'.v', 0)

    return(layerGroup, meshGroup, envGroup, ctrlGroup, rigGroup, layerGeos, layerTransformMesh, rootJoint)




def squashAndStretch(geos=[], name='squashAndStretch', locs=[], deformerParent='', ctrlParent=''): 
    '''
        Create squash and stretch rig for given geometry. Creates a twist, squash, front and back bend deformers to create a nice squash and stretch control. 

        @inParam geos - list, geometry to apply squash and stretch to
        @inParam name - string, prefix name of the control created and squash and stretch deformers - e.g. squashAndStretch
        @inParam locs - list, two placement locators names, the first given should be where the deformers will be placed. The second locator will be where the ctrl is created
        @inParam deformerParent - string, parent nonLinear deformers created under given parent
        @inParam ctrlParent - string, parent ctrl under given parent

        @procedure rig.squashAndStretch(geos=[geo], name='squashAndStretch', locs=['squashAndStretch_001_loc', 'squashAndStretch_002_loc'], deformerParent='squashAndStretch_env_grp', ctrlParent='squashAndStretch_ctrl_grp')
    '''
    #Creating deformers
    twist = rig.nonLinearDeformer(type='twist', name=name+'_twist', geometry=geos, paintNode=0, parent=deformerParent, snapToObj=locs[0], defDict={'lowBound':0, 'highBound':1})
    squash = rig.nonLinearDeformer(type='squash', name=name+'_squash', geometry=geos, paintNode=0, parent=deformerParent, snapToObj=locs[0], defDict={'lowBound':0, 'highBound':2})
    sideBend = rig.nonLinearDeformer(type='bend', name=name+'_side_bend', geometry=geos, paintNode=0, parent=deformerParent, snapToObj=locs[0], defDict={'lowBound':0, 'highBound':2})
    frontBend = rig.nonLinearDeformer(type='bend', name=name+'_front_bend', geometry=geos, paintNode=0, parent=deformerParent, snapToObj=locs[0], defDict={'lowBound':0, 'highBound':2})

    #Rotate bend deformers
    mc.setAttr(sideBend[1]+'.ry', 0)
    mc.setAttr(frontBend[1]+'.ry', 90)

    #Create the animation ctrl, move it to the second locator given
    ctrl = mc.circle(c=[0,0,0], nr=[0,1,0], sw=360, r=1, d=3, ut=0, tol=0.01, s=8, ch=0, n=name+'_ctrl')[0]  
    ctrlOffset = rig.createOffset(obj=ctrl, parent=ctrlParent)
    mc.delete(mc.parentConstraint(locs[1], ctrlOffset))
    rig.colourCtrl(ctrls=[ctrl], colour=16)

    #Add attributes to the ctrls
    squashAttr = rig.addDoubleAttr(ctrl=ctrl, attr='squashMultiplier', dv=3)
    sideBendAttr = rig.addDoubleAttr(ctrl=ctrl, attr='sideBendMultiplier', dv=0.05)
    frontBendAttr = rig.addDoubleAttr(ctrl=ctrl, attr='frontBendMultiplier', dv=-0.05)

    #Create mult nodes to multiply the control translation with the multiplier attributes.
    multDivNode = mc.createNode('multiplyDivide', n=name+'_squasAndStretch_multiplyDivide')
    doubleLinear = mc.createNode('multDoubleLinear', n=name+'_squasAndStretch_doubleLinear')
    mc.setAttr(doubleLinear+'.input2', -1)
    mc.setAttr(multDivNode+'.operation', 2)

    mc.connectAttr(ctrl+'.tx', multDivNode+'.input1X')
    mc.connectAttr(ctrl+'.ty', multDivNode+'.input1Y')
    mc.connectAttr(ctrl+'.tz', multDivNode+'.input1Z')

    mc.connectAttr(squashAttr, multDivNode+'.input2Y')
    mc.connectAttr(sideBendAttr, multDivNode+'.input2X')
    mc.connectAttr(frontBendAttr, multDivNode+'.input2Z')

    mc.connectAttr(multDivNode+'.outputX', sideBend[0]+'.curvature')
    mc.connectAttr(multDivNode+'.outputZ', frontBend[0]+'.curvature')
    mc.connectAttr(multDivNode+'.outputY', squash[0]+'.factor')
    mc.connectAttr(ctrl+'.ry', doubleLinear+'.input1')
    mc.connectAttr(doubleLinear+'.output', twist[0]+'.endAngle')

    #Cleanup
    rig.lockAndHideAttr(ctrl, ['rx','rz','sx','sy','sz'])

    nonLinears = [twist[1], sideBend[1], frontBend[1], squash[1]]
    #mc.parent(sideBend[1], frontBend[1], twist[1], squash[1], ctrlOffset)    
    return(ctrl, ctrlOffset, nonLinears)




def bakeTargetShapes(bs='', targetGeo=''):
    '''
        Bake target blendshapes for target geometry from face geo with existing blendshapes. Useful when we transfer facial blendshapes from one character to another.
        An example would be Alice's face geo with the blendshape node containing all of her existing face shapes as 'bs'. A new character (Sailor) we want to
        bake the blendshapes onto will be 'targetGeo'. The 'targetGeo' will be connected to Alice's face geo via a blendshape or wrap (if different topology - lod300/lod400).
        The procedure goes through all the blendshapes and switches them on, one by one and bakes the new target blendshapes for the targetGeo.

        @inParam bs - string, blendshape node with all the face shape targets
        @inParam targetGeo - string, target geometry that blendshapes will be baked from (this should be connected to the head geometry that has the existing face shapes via blendshape or wrap)
        
        @procedure rig.bakeTargetShapes(bs='blendShape1', targetGeo='alice_head_300')
    '''
    sel = mc.ls(sl=1)
    if targetGeo == '' or bs == '':
        if len(sel) > 0:
            if mc.objectType(sel[0]) == 'dnBlendShape' or mc.objectType(sel[0]) == 'blendShape':
                bs = sel[0]
            if mc.objectType(sel[0]) == 'transform' or mc.objectType(sel[0]) == 'transform':
                shape = mc.listRelatives(sel[0], shapes=1)[0]
                if shape:
                    targetGeo = sel[0]            
        if len(sel) > 1:  
            if mc.objectType(sel[1]) == 'dnBlendShape' or mc.objectType(sel[1]) == 'blendShape':
                bs = sel[1]
            if mc.objectType(sel[1]) == 'transform' or mc.objectType(sel[1]) == 'transform':
                shape = mc.listRelatives(sel[1], shapes=1)[1]
                if shape:
                    targetGeo = sel[1]

        objNotExist = []
        if not mc.objExists(bs):
            objNotExist.append('Please make sure you have selected the existing blendshape node you want to bake to another character head - none was found selected!!')

        if not mc.objExists(targetGeo):
            objNotExist.append('Please make sure you have selected the target head geo - none was found selected!!')

        if objNotExist:
            print '\n#-------------------------------------------------------------------------------------------------#'
            for obj in objNotExist:
                print obj
            print '#-------------------------------------------------------------------------------------------------#'
            mc.error('Please check the script editor, blendshape or head target geo not selected.')
    else:
        objNotExist = []
        if not mc.objExists(bs):
            objNotExist.append(bs+' does not exist. Blendshape Node - the existing face blendshapes node on the head geo.')

        if not mc.objExists(targetGeo):
            objNotExist.append(targetGeo+' does not exist. Target Geo - a new character we want to bake the blendshapes onto.')

        if objNotExist:
            print '\n#-------------------------------------------------------------------------------------------------#'
            for obj in objNotExist:
                print obj
            print '#-------------------------------------------------------------------------------------------------#'
            mc.error('Please check the script editor, blendshape or head target geo not found.')

    print '##### WARNING - Targets will keep their current values and be propegated down to the new targets created'
    print '##### Targets for '+bs+' getting baked. Make sure there is a connection (blendshape or wrap) between the head geo and '+targetGeo
    print '##### head_geo target will be renamed to neutral_bs, else make sure your neutral bs is called neutral_bs'


    targetNull = 'target_grp'    
    if mc.objExists(targetNull):
        origTargetNull = mc.rename(targetNull, 'target_grp_ORIG')
        for geo in mc.listRelatives(origTargetNull, ad=True, type='transform', f=1):
            if mc.listRelatives(geo, s=1)[0]:
                geoName = geo.split('|')[-1]
                mc.rename(geo, geoName+'_ORIG')
        print '##### Found other targets in scene, renamed them with suffix _ORIG'
    
    targetNull = mc.group(n=targetNull, em=1)


    targets = []
    connections = mc.listConnections(bs, source=1, p=1, t='shape')
    if len(connections) > 0:
        for con in connections:
            if '.worldMesh' in con and not 'ReferenceShape.worldMesh' in con:
                target = con.split('.')[0]
                target = target.replace('Shape', '')
                targets.append(target)
    else:
        mc.error('Blendshape inputs broken, check the '+bs+' is working!!')

    if not targets:
        print 'Blendshape inputs broken, check the '+bs+' is working!!'
    else:
        for target in targets:
            bsValue = mc.getAttr(bs+'.'+target)
            if bsValue == 0:
                mc.setAttr(bs+'.'+target, 1)

            targetNew = mc.duplicate(targetGeo, n=target)[0]
            mc.parent(targetNew, targetNull)
            targetNew = mc.rename(targetNew, target)
            
            if bsValue == 0:
                mc.setAttr(bs+'.'+target, 0)

            mc.select(targetNew, r=1)
            mc.polyNormalPerVertex(ufn=1)
            mc.select(cl=1)
            
            print 'Successfully baked '+target

        for target in targets:
            if target == 'head_geo':
                print('##### '+target+' created and renamed to neutral_bs.')
                mc.rename(targetNull+'|'+target, 'neutral_bs')

        print '#--------------[ Targets for '+bs+' baked successfully!! ]--------------#'

def create_facial_attrs (ctrl, trans_shapes=[('',''),('','')], combo_shapes=[('',''),('','')], trans_wrinkle_shapes=[('',''),('','')], combo_wrinkle_shapes=[('',''),('','')], 
rot_shapes = [('',''),('','')], push_shapes= ('',''), scale_factor=.1, x_scale=1, y_scale=1, z_scale=1, draw_guide=True, wrinkle=True, loc=True, lockLimit=True):
    '''
    #Example:create_facial_attrs ('L_lipCorner_ctrl',trans_shapes=[('top','bot'),('left','right')], combo_shapes = [('topLeft','topRight'),('botLeft','botRight')], 
    rot_shapes = [('rotUp','rotDown'),('rotLeft','rotRight')], push_shapes= ['pushOut','pushIn'], 
    x_scale=1, y_scale=1, z_scale=1, wrinkle=True, trans_wrinkle_shapes=[('topWrinkle','botWrinkle'),('leftWrinkle','rightWrinkle')], 
    combo_wrinkle_shapes = [('topLeftWrinkle','topRightWrinkle'),('botLeftWrinkle','botRightWrinkle')],)
    '''
    def addDisplayAttr (ctrl, attr, keyable=False):
        mc.addAttr(ctrl, ln=attr, at='double', min=0, dv=0, k=keyable)
        if keyable == False:
            mc.setAttr (ctrl+'.'+attr, cb=True)  
    def connectShapeAttr (input, ctrl, attr):
        mc.connectAttr (input, ctrl+'.'+attr)
        mc.setAttr (ctrl+'.'+attr, lock=True)
    def addWrinkleMath (input, ctrl, attr):
        '''        
        #dnMathOps for wrinkle to be driven non linearly
        math_node = mc.createNode ('dnMathOps', n=ctrl+'_'+attr+'Wrinkle_dnMathOps') 
        #Set to pow function
        mc.setAttr (math_node+'.operation', 11)
        #Exponent Default 2 = Exponential,  set to 1 = Linear                         
        mc.connectAttr (ctrl+'.wrinkleExponent',math_node+'.inFloatY')
        mc.connectAttr (input, math_node+'.inFloatX')
        return math_node
        '''
        #Multiply against itself for exponent power of 2
        wrinkleExp_MD = mc.createNode ('multiplyDivide', n=ctrl+'_'+attr+'WrinkleExp_multiplyDivide')
        mc.connectAttr (input, wrinkleExp_MD+'.input1X')
        mc.connectAttr (input, wrinkleExp_MD+'.input2X')
        wrinkleExp_blend = mc.createNode ('blendColors', n=ctrl+'_'+attr+'WrinkleExp_blendColors')
        wrinkleExp_setRange = mc.createNode ('setRange', n=ctrl+'_'+attr+'WrinkleExp_setRange') 
        #Remap wrinkle Exponent from 1-2 to 0-1 for blender
        mc.connectAttr (ctrl+'.wrinkleExponent', wrinkleExp_setRange+'.valueX')
        mc.setAttr (wrinkleExp_setRange+'.oldMinX', 1)
        mc.setAttr (wrinkleExp_setRange+'.oldMaxX', 2)
        mc.setAttr (wrinkleExp_setRange+'.minX', 0)
        mc.setAttr (wrinkleExp_setRange+'.maxX', 1)  
        #Connect to blender
        mc.connectAttr (wrinkleExp_setRange+'.outValueX', wrinkleExp_blend+'.blender')
        mc.connectAttr (input, wrinkleExp_blend+'.color2R')
        mc.connectAttr (wrinkleExp_MD+'.outputX', wrinkleExp_blend+'.color1R')   
        return wrinkleExp_blend

    def connectWrinkle (input, ctrl, attr, wAttr='', math = True, combo=False):
        if wAttr:
            wrinkle_MD = mc.createNode ('multiplyDivide', n=ctrl+'_'+attr+'Wrinkle_multiplyDivide')
            wrinkle_PMA = mc.createNode ('plusMinusAverage', n=ctrl+'_'+attr+'Wrinkle_plusMinusAverage')
            mc.connectAttr (ctrl+'.add_'+wAttr, wrinkle_PMA+'.input1D[0]')
            mc.connectAttr (ctrl+'.wrinkle', wrinkle_MD+'.input2X')
            mc.connectAttr (wrinkle_MD+'.outputX', wrinkle_PMA+'.input1D[1]')
            mc.connectAttr (wrinkle_PMA+'.output1D',  ctrl+'.'+wAttr)
            if math == True: 
                math_node = addWrinkleMath (input, ctrl, attr)                         
                if combo == True:
                    wrinkleCombo_MD = mc.createNode ('multiplyDivide', n=ctrl+'_'+attr+'WrinkleCombo_multiplyDivide')
                    mc.connectAttr (math_node+'.outputR', wrinkleCombo_MD+'.input1X')
                    mc.connectAttr (wrinkleCombo_MD+'.outputX', wrinkle_MD+'.input1X') 
                else:
                    mc.connectAttr (math_node+'.outputR', wrinkle_MD+'.input1X')
            else:
                 mc.connectAttr (input, wrinkle_MD+'.input1X')                       
            mc.setAttr (ctrl+'.'+wAttr, lock=True)
            if math == True:
                if combo == True:
                    return wrinkleCombo_MD

    #create control loc
    ctrl_parent = mc.listRelatives (ctrl, p=True)[0]
    if loc == True:
        ctrl_loc = mc.createNode ('transform', n=ctrl.replace('ctrl','loc'), p=ctrl_parent)
        mc.parentConstraint (ctrl, ctrl_loc)
    else:
        ctrl_loc = ctrl 
    #Set Names
    top_shape = trans_shapes[0][0]
    bot_shape = trans_shapes[0][1]
    left_shape = trans_shapes[1][0]
    right_shape = trans_shapes[1][1]
    rot_top_shape = rot_shapes[0][0]
    rot_bot_shape = rot_shapes[0][1]
    rot_left_shape = rot_shapes[1][0]
    rot_right_shape = rot_shapes[1][1]
    top_left_shape = combo_shapes[0][0]
    top_right_shape = combo_shapes[0][1]
    bot_left_shape = combo_shapes[1][0]
    bot_right_shape = combo_shapes[1][1]
    push_out_shape = push_shapes[0]
    push_in_shape = push_shapes[1]
    top_wrinkle_shape = trans_wrinkle_shapes[0][0]
    bot_wrinkle_shape = trans_wrinkle_shapes[0][1]
    left_wrinkle_shape = trans_wrinkle_shapes[1][0]
    right_wrinkle_shape = trans_wrinkle_shapes[1][1]    
    top_left_wrinkle_shape = combo_wrinkle_shapes[0][0]
    top_right_wrinkle_shape = combo_wrinkle_shapes[0][1]
    bot_left_wrinkle_shape = combo_wrinkle_shapes[1][0]
    bot_right_wrinkle_shape = combo_wrinkle_shapes[1][1]    
    empty = ('','')
    if wrinkle == True:
        mc.addAttr (ctrl, ln='wrinkle', at='double', min=0, dv=1.25, k=True)
        mc.addAttr (ctrl, ln='wrinkleExponent', at='double',dv=2, k=True, min=1,max=2)
    #Add Scale Factor attribute
    mc.addAttr (ctrl, ln='scaleFactor', at='double', dv=scale_factor, k=False)
    mc.setAttr (ctrl+'.scaleFactor', cb=True, lock=True)   
    if not x_scale == 1:
        mc.addAttr (ctrl, ln='xScale', at='double', dv=x_scale, k=False)
        mc.setAttr (ctrl+'.xScale', cb=True, lock=True)      
    if not y_scale == 1:
        mc.addAttr (ctrl, ln='yScale', at='double', dv=y_scale, k=False)
        mc.setAttr (ctrl+'.yScale', cb=True, lock=True)
    if not z_scale == 1:
        mc.addAttr (ctrl, ln='zScale', at='double', dv=z_scale, k=False)
        mc.setAttr (ctrl+'.zScale', cb=True, lock=True)    
    #Turn all transform Limits on. Set to 0 by default
    if lockLimit == True:
        mc.transformLimits (ctrl, etx=(True, True), ety=(True, True),etz=(True, True), erx=(True, True), ery=(True, True),erz=(True, True), tx=(0, 0), ty=(0, 0), tz=(0, 0),rx=(0, 0), ry=(0, 0), rz=(0, 0)) 
    #Trans Shapes####################################################################################
    top_limit = 0.1*scale_factor
    bot_limit = -0.1*scale_factor
    left_limit = -0.1*scale_factor
    right_limit = 0.1*scale_factor
    if not trans_shapes ==[empty,empty]:
        #If there are shapes in top,bot
        for shape in trans_shapes[0]:
            if shape:
                addDisplayAttr (ctrl,shape)
                #Set Transform limit based on trans_shapes available.
                if top_shape:    
                    top_limit = 1.0*scale_factor * y_scale
                    if lockLimit == True:      
                        mc.setAttr (ctrl+'.maxTransLimit.maxTransYLimit',top_limit)       
                if bot_shape:
                    bot_limit = -1.0*scale_factor * y_scale
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.minTransLimit.minTransYLimit',bot_limit)                                                           
        if trans_shapes[0] == empty:
            if lockLimit == True:
                lockAndHideAttr(ctrl, ['ty'])
        #If there are shapes in left,right
        for shape in trans_shapes[1]:
            if shape:
                addDisplayAttr (ctrl,shape)                   
                if left_shape:
                    left_limit = -1.0*scale_factor * x_scale              
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.minTransLimit.minTransXLimit',left_limit)              
                if  right_shape:
                    right_limit = 1.0*scale_factor * x_scale
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.maxTransLimit.maxTransXLimit',right_limit)
        if trans_shapes[1] == empty:
            if lockLimit == True:
                lockAndHideAttr(ctrl, ['tx'])
        for i in [0,1]:
            for shape in trans_wrinkle_shapes[i]:
                if shape:
                    addDisplayAttr (ctrl,'add_'+shape, keyable=True) 
                    addDisplayAttr (ctrl,shape)


    #Set Range for translateY       
    top_bot_setRange = mc.createNode ('setRange', n=ctrl+'_topBot_setRange')  
    mc.connectAttr (ctrl_loc+'.translateY', top_bot_setRange+'.valueX')
    mc.connectAttr (ctrl_loc+'.translateY', top_bot_setRange+'.valueY')       
    mc.setAttr (top_bot_setRange+'.oldMaxX', top_limit)
    mc.setAttr (top_bot_setRange+'.oldMinY', bot_limit)       
    mc.setAttr (top_bot_setRange+'.maxX', 1)
    mc.setAttr (top_bot_setRange+'.minY', 1)
    #Set Range for translateX
    left_right_setRange = mc.createNode ('setRange', n=ctrl+'_leftRight_setRange')  
    mc.connectAttr (ctrl_loc+'.translateX', left_right_setRange+'.valueX')
    mc.connectAttr (ctrl_loc+'.translateX', left_right_setRange+'.valueY')       
    mc.setAttr (left_right_setRange+'.oldMaxX', right_limit)
    mc.setAttr (left_right_setRange+'.oldMinY', left_limit)       
    mc.setAttr (left_right_setRange+'.maxX', 1)
    mc.setAttr (left_right_setRange+'.minY', 1)    
    if combo_shapes==[empty,empty]:  
        #Easy math for trans shapes non combo shapes
        #top / bot
        if top_shape:  
            connectShapeAttr (top_bot_setRange+'.outValueX', ctrl, top_shape)
            connectWrinkle (top_bot_setRange+'.outValueX', ctrl, top_shape, top_wrinkle_shape)                   
        if bot_shape:
            connectShapeAttr (top_bot_setRange+'.outValueY', ctrl, bot_shape)
            connectWrinkle (top_bot_setRange+'.outValueY', ctrl, bot_shape, bot_wrinkle_shape)               
        #left / right         
        if right_shape:
            connectShapeAttr (left_right_setRange+'.outValueX', ctrl, right_shape)
            connectWrinkle (left_right_setRange+'.outValueX', ctrl, right_shape, right_wrinkle_shape)                         
        if left_shape:
            connectShapeAttr (left_right_setRange+'.outValueY', ctrl, left_shape)
            connectWrinkle (left_right_setRange+'.outValueY', ctrl, left_shape, left_wrinkle_shape)               
    else:
        #Combo Shapes ###############################################################################################################
        #Add Attr for combo shapes
        for i in [0,1]:
            for shape in combo_shapes[i]:
                if shape:
                    addDisplayAttr (ctrl,shape)
        for i in [0,1]:
            for shape in combo_wrinkle_shapes[i]:
                if shape: 
                    addDisplayAttr (ctrl,'add_'+shape, keyable=True)                    
                    addDisplayAttr (ctrl,shape)


        #multiplyDivide Node for Combo shapes   
        bot_left_right_MD = mc.createNode ('multiplyDivide', n=ctrl+'_botLeftRight_multiplyDivide')       
        top_left_right_MD = mc.createNode ('multiplyDivide', n=ctrl+'_topLeftRight_multiplyDivide')                    
        top_bot_MD = mc.createNode ('multiplyDivide', n=ctrl+'_topBot_multiplyDivide') 
        left_right_MD = mc.createNode ('multiplyDivide', n=ctrl+'_leftRight_multiplyDivide')                             
        if top_left_shape:
            mc.connectAttr (left_right_setRange+'.outValueY',top_left_right_MD+'.input1X')
            mc.connectAttr (top_bot_setRange+'.outValueX',top_left_right_MD+'.input2X')
            connectShapeAttr (top_left_right_MD+'.outputX', ctrl, top_left_shape) 
            if wrinkle == True:  
                if top_left_wrinkle_shape: 
                    wrinkleCombo_MD = connectWrinkle (top_left_right_MD+'.outputX', ctrl, top_left_shape, wAttr=top_left_wrinkle_shape, math=False, combo=True)
            top_limit = 1.0*scale_factor * y_scale    
            if lockLimit == True:
                mc.setAttr (ctrl+'.maxTransLimit.maxTransYLimit',top_limit) 
            left_limit = -1.0*scale_factor * x_scale              
            if lockLimit == True:
                mc.setAttr (ctrl+'.minTransLimit.minTransXLimit',left_limit)                  
        if top_right_shape:
            mc.connectAttr (left_right_setRange+'.outValueX',top_left_right_MD+'.input1Y')         
            mc.connectAttr (top_bot_setRange+'.outValueX',top_left_right_MD+'.input2Y')
            connectShapeAttr (top_left_right_MD+'.outputY', ctrl, top_right_shape)
            if wrinkle == True:  
                if top_right_wrinkle_shape: 
                    wrinkleCombo_MD = connectWrinkle (top_left_right_MD+'.outputY', ctrl, top_right_shape, wAttr=top_right_wrinkle_shape, math=False, combo=True)
            top_limit = 1.0*scale_factor * y_scale      
            if lockLimit == True:
                mc.setAttr (ctrl+'.maxTransLimit.maxTransYLimit',top_limit)
            right_limit = 1.0*scale_factor * x_scale  
            if lockLimit == True:
                mc.setAttr (ctrl+'.maxTransLimit.maxTransXLimit',right_limit)                                                 
        if bot_left_shape:
            mc.connectAttr (left_right_setRange+'.outValueY',bot_left_right_MD+'.input1X')         
            mc.connectAttr (top_bot_setRange+'.outValueY',bot_left_right_MD+'.input2X')
            connectShapeAttr (bot_left_right_MD+'.outputX', ctrl, bot_left_shape)
            if wrinkle == True:  
                if bot_left_wrinkle_shape: 
                    wrinkleCombo_MD = connectWrinkle (bot_left_right_MD+'.outputX', ctrl, bot_left_shape, wAttr=bot_left_wrinkle_shape, math=False, combo=True)                      
            bot_limit = -1.0*scale_factor * y_scale    
            if lockLimit == True:
                mc.setAttr (ctrl+'.minTransLimit.minTransYLimit',bot_limit)
            left_limit = -1.0*scale_factor * x_scale                 
            if lockLimit == True:
                mc.setAttr (ctrl+'.minTransLimit.minTransXLimit',left_limit)                                           
        if bot_right_shape:
            mc.connectAttr (left_right_setRange+'.outValueX',bot_left_right_MD+'.input1Y')         
            mc.connectAttr (top_bot_setRange+'.outValueY',bot_left_right_MD+'.input2Y')
            connectShapeAttr (bot_left_right_MD+'.outputY', ctrl, bot_right_shape)
            if wrinkle == True:  
                if bot_right_wrinkle_shape: 
                    wrinkleCombo_MD = connectWrinkle (bot_left_right_MD+'.outputY', ctrl, bot_right_shape, wAttr=bot_right_wrinkle_shape, math=False, combo=True)                              
            bot_limit = -1.0*scale_factor * y_scale 
            if lockLimit == True:
                mc.setAttr (ctrl+'.minTransLimit.minTransYLimit',bot_limit)
            right_limit = 1.0*scale_factor * x_scale  
            if lockLimit == True:
                mc.setAttr (ctrl+'.maxTransLimit.maxTransXLimit',right_limit)                        
        if not trans_shapes==[empty,empty]:
            #reverse node for translateX Combo
            left_right_reverse = mc.createNode ('reverse', n=ctrl+'_leftRight_reverse')  
            mc.connectAttr (left_right_setRange+'.outValueX', left_right_reverse+'.inputX')
            mc.connectAttr (left_right_setRange+'.outValueY', left_right_reverse+'.inputY')         
            #reverse node for translateY Combo
            top_bot_reverse = mc.createNode ('reverse', n=ctrl+'_topBot_reverse')
            mc.connectAttr (top_bot_setRange+'.outValueX', top_bot_reverse+'.inputX')
            mc.connectAttr (top_bot_setRange+'.outValueY', top_bot_reverse+'.inputY')              
            #condition Node for translateX Combo
            left_right_condition = mc.createNode ('condition', n=ctrl+'_leftRight_condition')
            mc.setAttr (left_right_condition+'.operation', 2)
            mc.connectAttr (ctrl_loc+'.translateX', left_right_condition+'.firstTerm')
            mc.connectAttr (left_right_reverse+'.outputX', left_right_condition+'.colorIfTrueR')
            mc.connectAttr (left_right_reverse+'.outputY', left_right_condition+'.colorIfFalseR')               
            #condition Node for translateY Combo
            top_bot_condition = mc.createNode ('condition', n=ctrl+'_topbot_condition')
            mc.setAttr (top_bot_condition+'.operation', 2)       
            mc.connectAttr (ctrl_loc+'.translateY', top_bot_condition+'.firstTerm')
            mc.connectAttr (top_bot_reverse+'.outputX', top_bot_condition+'.colorIfTrueR')
            mc.connectAttr (top_bot_reverse+'.outputY', top_bot_condition+'.colorIfFalseR')                        
            if top_shape:  
                mc.connectAttr (top_bot_setRange+'.outValueX', top_bot_MD+'.input1X')
                mc.connectAttr (left_right_condition+'.outColorR', top_bot_MD+'.input2X')
                connectShapeAttr (top_bot_MD+'.outputX', ctrl, top_shape) 
                if wrinkle == True:  
                    if top_wrinkle_shape: 
                        wrinkleCombo_MD = connectWrinkle (top_bot_setRange+'.outValueX', ctrl, top_shape, wAttr=top_wrinkle_shape, combo=True)
                        mc.connectAttr (left_right_condition+'.outColorR', wrinkleCombo_MD+'.input2X')                                             
            if bot_shape:
                mc.connectAttr (top_bot_setRange+'.outValueY', top_bot_MD+'.input1Y')
                mc.connectAttr (left_right_condition+'.outColorR', top_bot_MD+'.input2Y')
                connectShapeAttr (top_bot_MD+'.outputY', ctrl, bot_shape)       
                if wrinkle == True:  
                    if bot_wrinkle_shape: 
                        wrinkleCombo_MD = connectWrinkle (top_bot_setRange+'.outValueY', ctrl, bot_shape, wAttr=bot_wrinkle_shape, combo=True)
                        mc.connectAttr (left_right_condition+'.outColorR', wrinkleCombo_MD+'.input2X')                                         
            if right_shape:
                mc.connectAttr (left_right_setRange+'.outValueX', left_right_MD+'.input1X')
                mc.connectAttr (top_bot_condition+'.outColorR', left_right_MD+'.input2X')
                connectShapeAttr (left_right_MD+'.outputX', ctrl, right_shape)       
                if wrinkle == True:  
                    if right_wrinkle_shape: 
                        wrinkleCombo_MD = connectWrinkle (left_right_setRange+'.outValueX', ctrl, right_shape, wAttr=right_wrinkle_shape, combo=True)
                        mc.connectAttr (top_bot_condition+'.outColorR', wrinkleCombo_MD+'.input2X')                                     
            if left_shape:
                mc.connectAttr (left_right_setRange+'.outValueY', left_right_MD+'.input1Y')
                mc.connectAttr (top_bot_condition+'.outColorR', left_right_MD+'.input2Y')
                connectShapeAttr (left_right_MD+'.outputY', ctrl, left_shape)                  
                if wrinkle == True:  
                    if left_wrinkle_shape: 
                        wrinkleCombo_MD = connectWrinkle (left_right_setRange+'.outValueY', ctrl, left_shape, wAttr=left_wrinkle_shape, combo=True)
                        mc.connectAttr (top_bot_condition+'.outColorR', wrinkleCombo_MD+'.input2X')                
                     
    #Rot Shapes########################################################################################
    if not rot_shapes[0] == empty:                               
        for shape in rot_shapes[0]:
            if shape:
                addDisplayAttr (ctrl,shape)
                if rot_top_shape:
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.minRotLimit.minRotXLimit',-90)  
                if rot_bot_shape:
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.maxRotLimit.maxRotXLimit',90)                               
        rot_top_bot_setRange = mc.createNode ('setRange', n=ctrl+'_rotTopBot_setRange')  
        mc.connectAttr (ctrl_loc+'.rotateX', rot_top_bot_setRange+'.valueX')
        mc.connectAttr (ctrl_loc+'.rotateX', rot_top_bot_setRange+'.valueY')       
        mc.setAttr (rot_top_bot_setRange+'.oldMaxX', 90)
        mc.setAttr (rot_top_bot_setRange+'.oldMinY', -90)       
        mc.setAttr (rot_top_bot_setRange+'.maxX', 1)
        mc.setAttr (rot_top_bot_setRange+'.minY', 1)
        if rot_top_shape:
            connectShapeAttr (rot_top_bot_setRange+'.outValueY', ctrl, rot_top_shape)         
        if rot_bot_shape:
            connectShapeAttr (rot_top_bot_setRange+'.outValueX', ctrl, rot_bot_shape)
    else:
        if lockLimit == True:
            lockAndHideAttr(ctrl, ['rx'])                   
    if not rot_shapes[1] == empty:                       
        for shape in rot_shapes[1]:
            if shape:
                addDisplayAttr (ctrl,shape)
                if rot_left_shape:
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.minRotLimit.minRotYLimit',-90)  
                if rot_right_shape:
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.maxRotLimit.maxRotYLimit',90)
        rot_left_right_setRange = mc.createNode ('setRange', n=ctrl+'_rotLeftRight_setRange')  
        mc.connectAttr (ctrl_loc+'.rotateY', rot_left_right_setRange+'.valueX')
        mc.connectAttr (ctrl_loc+'.rotateY', rot_left_right_setRange+'.valueY')       
        mc.setAttr (rot_left_right_setRange+'.oldMaxX', 90)
        mc.setAttr (rot_left_right_setRange+'.oldMinY', -90)       
        mc.setAttr (rot_left_right_setRange+'.maxX', 1)
        mc.setAttr (rot_left_right_setRange+'.minY', 1)
        if rot_left_shape:
            connectShapeAttr (rot_left_right_setRange+'.outValueY', ctrl, rot_left_shape)          
        if rot_right_shape:
            connectShapeAttr (rot_left_right_setRange+'.outValueX', ctrl, rot_right_shape)                                                                        
    else:
        if lockLimit == True:
            lockAndHideAttr(ctrl, ['ry'])
    #Push Shapes########################################################################################           
    if not push_shapes == empty:                               
        push_out_limit = 0
        push_in_limit = 0
        for shape in push_shapes:
            if shape:
                addDisplayAttr (ctrl,shape)
                if push_out_shape:
                    push_out_limit = 1.0*scale_factor  * z_scale       
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.maxTransLimit.maxTransZLimit',push_out_limit)    
                if push_in_shape:
                    push_in_limit = -1.0*scale_factor * z_scale       
                    if lockLimit == True:
                        mc.setAttr (ctrl+'.minTransLimit.minTransZLimit',push_in_limit)                                   
        push_setRange = mc.createNode ('setRange', n=ctrl+'_push_setRange')  
        mc.connectAttr (ctrl_loc+'.translateZ', push_setRange+'.valueX')
        mc.connectAttr (ctrl_loc+'.translateZ', push_setRange+'.valueY')       
        mc.setAttr (push_setRange+'.oldMaxX', push_out_limit)
        mc.setAttr (push_setRange+'.oldMinY', push_in_limit)       
        mc.setAttr (push_setRange+'.maxX', 1)
        mc.setAttr (push_setRange+'.minY', 1)   
        if push_out_shape:
            connectShapeAttr (push_setRange+'.outValueX', ctrl, push_out_shape)         
        if push_in_shape:
            connectShapeAttr (push_setRange+'.outValueY', ctrl, push_in_shape)
    else:
        if lockLimit == True:
            lockAndHideAttr(ctrl, ['tz']) 
    #Create Guide######################################################################################## 
    if draw_guide == True:
        guide = mc.curve(d =1, p =[(left_limit,bot_limit,0), (left_limit,top_limit,0),(right_limit,top_limit,0), (right_limit,bot_limit,0), (left_limit,bot_limit,0)], k=[0,1,2,3,4], n=ctrl.replace('ctrl','guide'))
        guide_shape = mc.listRelatives(guide)
        guide_shape = mc.rename(guide_shape, guide+'Shape')
        mc.setAttr(guide_shape+'.template', 1)
        mc.parent (guide, ctrl_parent, r = True)          
    #Temp lock translate Z
    if lockLimit == True:
        lockAndHideAttr(ctrl, ['rz','sx','sy','sz'])





def bakeShapes(dictionary, geo, organize=True, shapesGroup ='refMesh_grp'):
    '''
        Parent and scale constraint list of geometry (value) to joint (key) of dictionary.

        @inParam dictionary - dict, key is morphTarget, controller and action
        @inParam geo - string, face shape to bake out.
        @inParam organize - boolean, will parent shapes and spread them out.
        @inParam shapesGroup - string, shape group.        
        
        @procedure rig.bakeShapes (shapesDict, 'head_broadSkin')
                    shapesDict = {'mouthStretch_100_bs':['mouth_jaw_ctrl','rx',30],
                    'jawDrop_100_bs':['mouth_jaw_ctrl','rx',15]}
    '''
    if not mc.objExists (shapesGroup):
        mc.createNode ('transform',n=shapesGroup) 
    tPos = 0    

    for key, value in dictionary.iteritems():
        morphTarget = key[0]
        ctrl = key[1]
        for attr in value:
            mc.setAttr(ctrl+'.'+attr[0], attr[1])
        duplicateClean (geo, morphTarget)
        unlockAttr(morphTarget, attrs=['tx','ty','tz','rx','ry','rz','sx','sy','sz'])     
        mc.parent (morphTarget, shapesGroup)
        #Rest to Zero      
        for attr in value:
            mc.setAttr(ctrl+'.'+attr[0], 0)  
        print 'duplicate '+morphTarget
        if organize == True:
            tPos += 3
            mc.setAttr (morphTarget+'.tx',tPos)
         
    '''    
    shapesDict = {('mouthStretch_100_ref','mouth_jaw_old'):[('rx',30)],
    ('jawDrop_100_ref','mouth_jaw_oldCtrl'):[('rx',15)],
    ('jawThrust_100_ref','mouth_jaw_oldCtrl'):[('tz',.1)],
    ('L_cheekRaiser_100_ref','L_cheek_main_ctrl'):[('ty',0.05)],
    ('R_cheekRaiser_100_ref','R_cheek_main_ctrl'):[('ty',0.05)],
    ('L_jawSideways_100_ref','mouth_jaw_oldCtrl'):[('ry',10)],
    ('R_jawSideways_100_ref','mouth_jaw_oldCtrl'):[('ry',-10)],
    ('L_lipStretcher_100_ref','L_mouth_corner_ctrl'):[('tx',.5)],
    ('R_lipStretcher_100_ref','R_mouth_corner_ctrl'):[('tx',.5)],
    ('L_lipStretcher_50_ref','L_mouth_corner_ctrl'):[('tx',.25)],
    ('R_lipStretcher_50_ref','R_mouth_corner_ctrl'):[('tx',.25)],
    ('L_lipCornerPuller_100_ref','L_mouth_corner_ctrl'):[('ty',.25)],
    ('R_lipCornerPuller_100_ref','R_mouth_corner_ctrl'):[('ty',.25)],
    ('L_lipCornerDepressor_100_ref','L_mouth_corner_ctrl'):[('ty',-.25)],
    ('R_lipCornerDepressor_100_ref','R_mouth_corner_ctrl'):[('ty',-.25)],
    ('L_lipPursing_100_ref','L_mouth_corner_ctrl'):[('tx',-.5)],
    ('R_lipPursing_100_ref','R_mouth_corner_ctrl'):[('tx',-.5)],
    ('L_upperLipRaiser_100_ref','L_mouth_upperLip_ctrl'):[('ty',.5)],
    ('R_upperLipRaiser_100_ref','R_mouth_upperLip_ctrl'):[('ty',.5)],
    ('L_upperLipDepressor_100_ref','L_mouth_upperLip_ctrl'):[('ty',-.5)],
    ('R_upperLipDepressor_100_ref','R_mouth_upperLip_ctrl'):[('ty',-.5)],
    ('L_lowerLipDepressor_100_ref','L_mouth_lowerLip_ctrl'):[('ty',-.5)],
    ('R_lowerLipDepressor_100_ref','R_mouth_lowerLip_ctrl'):[('ty',-.5)],
    ('L_lowerLipRaiser_100_ref','L_mouth_lowerLip_ctrl'):[('ty',.5)],
    ('R_lowerLipRaiser_100_ref','R_mouth_lowerLip_ctrl'):[('ty',.5)],
    ('L_lipCornerDepressor_lipStretcher_100_ref','L_mouth_corner_ctrl'):[('tx',.5),('ty',-.375)],
    ('R_lipCornerDepressor_lipStretcher_100_ref','R_mouth_corner_ctrl'):[('tx',.5),('ty',-.375)],
    ('L_lipCornerDepressor_lipPursing_100_ref','L_mouth_corner_ctrl'):[('tx',-.5),('ty',-.375)],
    ('R_lipCornerDepressor_lipPursing_100_ref','R_mouth_corner_ctrl'):[('tx',-.5),('ty',-.375)],
    ('L_lipCornerPuller_lipStretcher_100_ref','L_mouth_corner_ctrl'):[('tx',.5),('ty',.375)],
    ('R_lipCornerPuller_lipStretcher_100_ref','R_mouth_corner_ctrl'):[('tx',.5),('ty',.375)],
    ('L_lipCornerPuller_lipPursing_100_ref','L_mouth_corner_ctrl'):[('tx',-.5),('ty',.375)],
    ('R_lipCornerPuller_lipPursing_100_ref','R_mouth_corner_ctrl'):[('tx',-.5),('ty',.375)],
    ('L_outerBrowRaiser_100_ref','L_brows_temple_ctrl'):[('ty',.07)],
    ('R_outerBrowRaiser_100_ref','R_brows_temple_ctrl'):[('ty',.07)],
    ('L_outerBrowLowerer_100_ref','L_brows_temple_ctrl'):[('ty',-.07)],
    ('R_outerBrowLowerer_100_ref','R_brows_temple_ctrl'):[('ty',-.07)],  
    ('L_innerBrowRaiser_100_ref','L_brows_mid_ctrl'):[('ty',.07)],
    ('R_innerBrowRaiser_100_ref','R_brows_mid_ctrl'):[('ty',.07)],
    ('L_innerEyebrowLowerer_100_ref','L_brows_mid_ctrl'):[('ty',-.07)],
    ('R_innerEyebrowLowerer_100_ref','R_brows_mid_ctrl'):[('ty',-.07)],
    ('L_eyebrowGatherer_100_ref','L_brows_mid_ctrl'):[('tx',-.07)],
    ('R_eyebrowGatherer_100_ref','R_brows_mid_ctrl'):[('tx',.07)],
    ('L_innerBrowRaiserrew_eyebrowGatherer_100_ref','L_brows_mid_ctrl'):[('tx',-.07),('ty',.07)],
    ('R_innerBrowRaiser_eyebrowGatherer_100_ref','R_brows_mid_ctrl'):[('tx',.07),('ty',.07)],
    ('L_innerEyebrowLowerer_eyebrowGatherer_100_ref','L_brows_mid_ctrl'):[('tx',-.07),('ty',-.07)],
    ('R_innerEyebrowLowerer_eyebrowGatherer_100_ref','R_brows_mid_ctrl'):[('tx',.07),('ty',-.07)],
    ('top_lipFunneler_100_ref','mouth_upperLip_ctrl'):[('rx',-45)],
    ('top_lipsTowardsEachOther_100_ref','mouth_upperLip_ctrl'):[('rx',45)],
    ('bot_lipFunneler_100_ref','mouth_lowerLip_ctrl'):[('rx',45)],
    ('bot_lipsTowardsEachOther_100_ref','mouth_lowerLip_ctrl'):[('rx',-45)],
    ('chinRaiser_100_ref','mouth_chin_ctrl'):[('ty',1)]}

    for s in ['L','R']:
        mc.setAttr (s+'_cheekRaiser_0_ctrl.followLipCtrl', 0)
    if mc.objExists ('face_actionUnits_blendShape') == True:
        mc.delete ('face_actionUnits_blendShape')
    if mc.objExists ('refMesh_grp') == True:
        mc.delete ('refMesh_grp')
    bakeShapes (shapesDict, 'face_broadSkin')     
    '''




def connectCtrl (slaveCtrl, masterCtrl, bOperation, dValue, negative=False, transX = True):
    follow = rig.addDoubleAttr(ctrl=slaveCtrl, attr='followLipCtrl', min=0, max=1, dv=dValue)

    if not bOperation == None:
        #Condition for translate if only one follows one direction in Y
        cond = mc.createNode ('condition', n = side+'_'+slave+'Follow_cond')
        mc.connectAttr (masterCtrl+'.translateY', cond+'.firstTerm')
        mc.connectAttr (masterCtrl+'.translateY', cond+'.colorIfTrueR')
        if bOperation == 'greaterThan':
            mc.setAttr (cond+'.operation', 2)
        if bOperation == 'lessThan':
            mc.setAttr (cond+'.operation', 4)        
        mc.setAttr (cond+'.colorIfFalseR', 0)
    if transX == True:
        #Setrange on translate X lipPursing
        setRange = mc.createNode ('setRange', n = side+'_'+slave+'Follow_setRange')
        mc.connectAttr (masterCtrl+'.translateX', setRange+'.valueX')  
        mc.setAttr (setRange+'.maxX', 1)  
        mc.setAttr (setRange+'.oldMinX', -mc.getAttr (masterCtrl+'.scaleFactor'))  
        mc.setAttr (setRange+'.oldMaxX', mc.getAttr (masterCtrl+'.scaleFactor'))   
        #Connect to followLip attr
        MDXFollow = mc.createNode ('multiplyDivide', n = side+'_'+slave+'Follow_X_MD')
        mc.connectAttr (setRange+'.outValueX', MDXFollow+'.input1X')  
        if not bOperation == None:
            mc.connectAttr (cond+'.outColorR', MDXFollow+'.input2X')
        else:
            mc.connectAttr (masterCtrl+'.translateY', MDXFollow+'.input2X')
    #Connect to followLip attr
    MDFollow = mc.createNode ('multiplyDivide', n = side+'_'+slave+'Follow_MD')
    if transX == True:
        mc.connectAttr (MDXFollow+'.outputX', MDFollow+'.input2X')
    else:
        if not bOperation == None:        
            mc.connectAttr (cond+'.outColorR', MDFollow+'.input2X')  
        else:
            mc.connectAttr (masterCtrl+'.translateY', MDFollow+'.input2X')    
    mc.connectAttr (follow, MDFollow+'.input1X')
    # Take into account scale factor
    MD = mc.createNode ('multiplyDivide',  n = side+'_'+slave+'Follow_scaleFactor_MD')
    mc.connectAttr (MDFollow+'.outputX', MD+'.input1X')
    mc.connectAttr (MDFollow+'.outputX', MD+'.input1Y')
    if mc.attributeQuery('yScale', node=masterCtrl, ex=1):
        scaleFactor = mc.getAttr (slaveCtrl+'.scaleFactor') / (mc.getAttr (masterCtrl+'.scaleFactor') *  mc.getAttr (masterCtrl+'.yScale'))
    else:
        scaleFactor = 1 / (mc.getAttr (masterCtrl+'.scaleFactor') / mc.getAttr (slaveCtrl+'.scaleFactor'))                   
    mc.setAttr (MD+'.input2X', scaleFactor)  
    mc.setAttr (MD+'.input2Y', -scaleFactor)
    if bOperation == None:  
        mc.setAttr (MD+'.input2Z', -mc.getAttr (slaveCtrl+'.scaleFactor'))

    #Connect to slave control offset  
    slaveParent = mc.listRelatives(slaveCtrl, p = True)[0]
    offset = mc.createNode ('transform', n = side+'_'+slave+'Follow', p=slaveParent)
    mc.delete (mc.parentConstraint (slaveParent, offset))
    mc.parent (slaveCtrl,offset)
    mc.connectAttr (MD+'.outputX', offset+'.translateY')
    # Refactor translate limits on slave control
    PMAMaxY = mc.createNode ('plusMinusAverage', n= side+'_'+slave+'FollowMaxY_PMA')
    PMAMinY = mc.createNode ('plusMinusAverage', n= side+'_'+slave+'FollowMinY_PMA')    
    mc.setAttr (PMAMaxY+'.operation', 2) 
    mc.setAttr (PMAMinY+'.operation', 1)               
    if negative == True:
        MDNeg = mc.createNode ('multiplyDivide',  n = side+'_'+slave+'_scaleFactorNeg_MD')
        mc.connectAttr (slaveCtrl+'.scaleFactor', MDNeg+'.input1X')
        mc.setAttr (MDNeg+'.input2X', -1)
        mc.connectAttr (MDNeg+'.outputX', PMAMaxY+'.input1D[0]')
        mc.connectAttr (PMAMaxY+'.output1D', slaveCtrl+'.minTransYLimit')
        #mc.connectAttr (MD+'.outputY', slaveCtrl+'.maxTransYLimit')     
        mc.connectAttr (MD+'.outputY', PMAMinY+'.input1D[0]')   
        mc.connectAttr (PMAMinY+'.output1D', slaveCtrl+'.maxTransYLimit')

    else:
        mc.connectAttr (slaveCtrl+'.scaleFactor', PMAMaxY+'.input1D[0]')
        mc.connectAttr (PMAMaxY+'.output1D', slaveCtrl+'.maxTransYLimit')
        #mc.connectAttr (MD+'.outputY', slaveCtrl+'.minTransYLimit') 
        mc.connectAttr (MD+'.outputY', PMAMinY+'.input1D[0]') 
        mc.connectAttr (PMAMinY+'.output1D', slaveCtrl+'.minTransYLimit') 
    mc.connectAttr (MD+'.outputX', PMAMaxY+'.input1D[1]')
    mc.connectAttr (MD+'.input2Z', PMAMinY+'.input1D[1]')






def animateTargets(bs='blendShape1', frameLength=4, startFrame=1, tangentType='flat'):
    '''
        Quickly animate all blendshape targets on for playblasting and showing production. Each target will have 5 frames of animation from off to on by default.

        @inParam bs - string, blendshape node name
        @inParam frameLength - int, length of frame range per target. So if 5, at frame 0 the target is off, at frame 5 it's on
        @inParam startFrame - int, frame to start animation from
        @inParam tangentType - string, tangent type of anim curve, choose between auto, spline, clamped, linear, flat, step, plateau
        
        @procedure rig.animateTargets(bs='blendShape1', frameLength=4, startFrame=1)
    '''
    sel = mc.ls(sl=1)
    if bs == '':
        if len(sel) > 0:
            for item in sel:
                if mc.objectType(item) == 'dnBlendShape' or mc.objectType(item) == 'blendShape':
                    bs = sel[0]

        if not mc.objExists(bs):
            mc.error(bs+' does not exist. Please select a blendshape!')
    else:
        if not mc.objExists(bs):
            if len(sel) > 0:
                for item in sel:
                    if mc.objectType(item) == 'dnBlendShape' or mc.objectType(item) == 'blendShape':
                        bs = sel[0]

                if not mc.objExists(bs):
                    mc.error(bs+' does not exist. Please select a blendshape!')


    targets = []
    connections = mc.listConnections(bs, source=1, p=1, t='shape')
    if len(connections) > 0:
        for con in connections:
            if '.worldMesh' in con and not 'ReferenceShape.worldMesh' in con:
                target = con.split('.')[0]
                target = target.replace('Shape', '')

                if mc.objExists(bs+'.'+target):
                    flag = 0
                    for targ in targets:
                        if target == targ:  flag = 1

                    if flag != 1:
                        targets.append(target)
    else:
        mc.error('Blendshape inputs broken, check the '+bs+' is working!!')


    #Delete existing animation on targets if there is any.
    for obj in mc.ls(bs+'*'):
        if mc.objectType(obj) == 'animCurveTU':
            mc.delete(obj)


    if tangentType != 'auto' and tangentType != 'spline' and tangentType != 'clamped' and tangentType != 'linear' and tangentType != 'flat' and tangentType != 'step' and tangentType != 'plateau':
        tangentType = 'flat'
        print 'Anim curve tangent type changed to flat, please choose auto, spline, clamped, linear, flat, step, plateau'


    if not targets:
        print 'Blendshape inputs broken, check the '+bs+' is working!!'
    else:
        time = startFrame

        for target in targets:
            mc.currentTime(time)

            mc.setAttr(bs+'.'+target, 0)
            mc.setKeyframe(bs+'.'+target, itt=tangentType, ott=tangentType)

            mc.currentTime(time+frameLength)
            mc.setAttr(bs+'.'+target, 1)
            mc.setKeyframe(bs+'.'+target, itt=tangentType, ott=tangentType)

            mc.currentTime(time+frameLength+1)
            mc.setAttr(bs+'.'+target, 0)
            mc.setKeyframe(bs+'.'+target, itt=tangentType, ott=tangentType)

            time = time+frameLength+1

    print '#--------------[ Targets animated Successfully ]--------------#'


def eyeLidRig(eyeballJnt, side, radius, ctrl, attr, createHelper=True, wideOpen=-0.2, blinkCompression=2, addEmotion=True):
    '''
    Expecting attr input values to be 
    -0.2 : wideOpen
    0 : default
    1 : blink
    1.5 : blinkCompression 
    '''
    parts = ['Upper','Lower']
    columns = ['inner','mid','outer']
    returnList =[]
    mc.addAttr(ctrl, ln='blinkLine', at='double',dv=0, k=True )
    blinkLineAttr = ctrl+'.blinkLine'
    mc.addAttr(ctrl, ln='wideOpen', at='double',dv=wideOpen, k=True )
    wideOpenAttr = ctrl+'.wideOpen'  
    eyelidMasterGrp = mc.createNode ('transform', n=side+'_eyelid_grp',p=eyeballJnt)    
    def createLid (column): 
        eyelidGrp = mc.createNode ('transform', n=side+'_'+column+'Eyelid_grp',p=eyelidMasterGrp)   
        setRange = mc.createNode ('setRange', n=side+'_'+column+'EyeLidBlink_setRange')
        mc.connectAttr (attr, setRange+'.valueX')
        mc.connectAttr (attr, setRange+'.valueY')    
        mc.setAttr (setRange+'.oldMaxX', 1)
        mc.setAttr (setRange+'.oldMaxY', 1)
        if createHelper == True:
            setRangeHelper = mc.createNode ('setRange', n=side+'_'+column+'EyeLidBlinkHelper_setRange')
            mc.connectAttr (attr, setRangeHelper+'.valueX')
            mc.connectAttr (attr, setRangeHelper+'.valueY')
            #Disallow lower lid to open wide
            mc.setAttr (setRangeHelper+'.oldMaxX', 1)
            mc.setAttr (setRangeHelper+'.oldMaxY', 1)
        for part in parts:
            mc.addAttr(ctrl, ln=column+part+'LidOpen', at='double',dv=0, k=True )
            lidOpenAttr = ctrl+'.'+column+part+'LidOpen'
            returnList.append(lidOpenAttr)
            LidBase = mc.createNode ('joint',n=side+'_'+column+part+'LidBase_env', p=eyelidGrp)
            LidTip = mc.createNode ('joint',n=side+'_'+column+part+'LidTip_env', p=LidBase)
            mc.setAttr (LidTip+'.translateZ', radius)
            if part == 'Upper':
                setRangeAttr = 'X'
                upperLidOpenAttr = lidOpenAttr
                #Wide open only happens on upper lid###############################################
                wideOpenCond = mc.createNode ('condition', n=side+'_'+column+'wideOpen_condition') 
                mc.connectAttr (attr, wideOpenCond+'.firstTerm')
                #is less than
                mc.setAttr (wideOpenCond+'.operation', 4)
                mc.connectAttr (setRange+'.outValue'+setRangeAttr, wideOpenCond+'.colorIfFalseR')
                #Create wideOpen setRange
                wideOpenSetRange = mc.createNode ('setRange', n=side+'_'+column+'WideOpen_setRange')
                mc.connectAttr (attr, wideOpenSetRange+'.valueX') 
                mc.connectAttr (wideOpenAttr, wideOpenSetRange+'.oldMinX')
                mc.connectAttr (lidOpenAttr, wideOpenSetRange+'.maxX')  
                wideOpenMD = mc.createNode ('multiplyDivide', n=side+'_'+column+'WideOpen_multiplyDivide') 
                mc.connectAttr (lidOpenAttr, wideOpenMD+'.input1X')
                mc.connectAttr (wideOpenAttr, wideOpenMD+'.input2X') 
                wideOpenPMA = mc.createNode ('plusMinusAverage', n=side+'_'+column+'WideOpen_plusMinusAverage')
                mc.connectAttr (lidOpenAttr, wideOpenPMA+'.input1D[0]')
                mc.connectAttr (wideOpenMD+'.outputX', wideOpenPMA+'.input1D[1]')
                mc.setAttr (wideOpenPMA+'.operation',2)
                mc.connectAttr (wideOpenPMA+'.output1D', wideOpenSetRange+'.minX') 
                mc.connectAttr (wideOpenSetRange+'.outValueX', wideOpenCond+'.colorIfTrueR') 
                mc.connectAttr (wideOpenCond+'.outColorR', LidBase+'.rotateX')                                      
            if part == 'Lower': 
                setRangeAttr = 'Y'
                lowerLidOpenAttr = lidOpenAttr
                mc.connectAttr (setRange+'.outValue'+setRangeAttr, LidBase+'.rotateX')                
            mc.connectAttr (lidOpenAttr, setRange+'.min'+setRangeAttr)
            mc.connectAttr (blinkLineAttr, setRange+'.max'+setRangeAttr)
            if createHelper == True:
                helperLidBase = mc.createNode ('joint',n=side+'_'+column+part+'LidHelperBase_env', p=eyelidGrp)
                helperLidTip = mc.createNode ('joint',n=side+'_'+column+part+'LidHelperTip_env', p=helperLidBase)  
                mc.setAttr (helperLidTip+'.translateZ', radius)
                #UpperLid Multiplier. Default open is 25% higher. Closes at half the rate.  
                MDHelper = mc.createNode ('multiplyDivide', n=side+'_'+column+part+'LidHelper_multiplyDivide')
                mc.setAttr (MDHelper+'.input2X',1.25)            
                mc.setAttr (MDHelper+'.input2Y',0.5)
                mc.connectAttr (lidOpenAttr, MDHelper+'.input1X')
                mc.connectAttr (lidOpenAttr, MDHelper+'.input1Y')
                # Add the half rate to the blink line setting.
                PMAHelper = mc.createNode ('plusMinusAverage', n=side+'_'+column+part+'LidHelper_plusMinusAverage')
                mc.connectAttr (MDHelper+'.outputY', PMAHelper+'.input1D[0]')
                mc.connectAttr (blinkLineAttr, PMAHelper+'.input1D[1]')
                mc.connectAttr (PMAHelper+'.output1D', setRangeHelper+'.max'+setRangeAttr)
                mc.connectAttr (MDHelper+'.outputX', setRangeHelper+'.min'+setRangeAttr)
                #Set Max blink to overblink 
                mc.setAttr (setRangeHelper+'.oldMax'+setRangeAttr, blinkCompression)
                if part =='Upper':
                    mc.connectAttr (attr, wideOpenSetRange+'.valueY')
                    mc.connectAttr (wideOpenAttr, wideOpenSetRange+'.oldMinY')
                    mc.connectAttr (MDHelper+'.outputX', wideOpenSetRange+'.maxY')
                    mc.connectAttr (MDHelper+'.outputX', wideOpenMD+'.input1Y')
                    mc.connectAttr (wideOpenAttr, wideOpenMD+'.input2Y')
                    wideOpenPMAHelper = mc.createNode ('plusMinusAverage', n=side+'_'+column+'WideOpenHelper_plusMinusAverage')
                    mc.connectAttr (MDHelper+'.outputX', wideOpenPMAHelper+'.input1D[0]')
                    mc.connectAttr (wideOpenMD+'.outputX', wideOpenPMAHelper+'.input1D[1]')
                    mc.setAttr (wideOpenPMAHelper+'.operation',2)
                    mc.connectAttr (wideOpenPMAHelper+'.output1D', wideOpenSetRange+'.minY')  
                    mc.connectAttr (wideOpenSetRange+'.outValueY', wideOpenCond+'.colorIfTrueG') 
                    mc.connectAttr (setRangeHelper+'.outValue'+setRangeAttr, wideOpenCond+'.colorIfFalseG')
                    mc.connectAttr (wideOpenCond+'.outColorG', helperLidBase+'.rotateX') 
                if part =='Lower':
                    mc.connectAttr (setRangeHelper+'.outValue'+setRangeAttr,helperLidBase+'.rotateX')
        return (upperLidOpenAttr,lowerLidOpenAttr) 
    if addEmotion == True:
        #One attr for sad and mad. Sad: -1, Mad: 1 
        mc.addAttr(ctrl, ln='sadMad', at='double',dv=0, min = -1, max=1, k=True )
        emotionAttr = ctrl+'.sadMad'
        emotionMD = mc.createNode ('multiplyDivide', n=side+'_emotion_multiplyDivide') 
        mc.connectAttr (emotionAttr, emotionMD+'.input1X')           
        mc.setAttr (emotionMD+'.input2X', 10) 
        mc.connectAttr (emotionAttr, emotionMD+'.input1Y')           
        mc.setAttr (emotionMD+'.input2Y', 7)  
        #Emotion will be applied to only inner and mid joints                
        for column in columns[0:2]:  
            #Create lid joints            
            (upperLidOpenAttr, lowerLidOpenAttr)= createLid (column)   
            emotionBlinkLinePMA = mc.createNode ('plusMinusAverage', n=side+'_blinkLine'+column+'Emotion_plusMinusAverage')
            mc.connectAttr (blinkLineAttr, emotionBlinkLinePMA+'.input1D[0]')
            if column == 'inner':
                mdAttr='X'
            if column == 'mid':
                mdAttr='Y'                       
            mc.connectAttr (emotionMD+'.output'+mdAttr, emotionBlinkLinePMA+'.input1D[1]')                
            mc.connectAttr (emotionBlinkLinePMA+'.output1D', side+'_'+column+'EyeLidBlink_setRange.maxX',f=True) 
            mc.connectAttr (emotionBlinkLinePMA+'.output1D', side+'_'+column+'EyeLidBlink_setRange.maxY',f=True)             
            for part in parts:
                emotionPMA = mc.createNode ('plusMinusAverage', n=side+'_'+column+part+'Emotion_plusMinusAverage')  
                mc.connectAttr (emotionMD+'.output'+mdAttr, emotionPMA+'.input1D[0]') 
                if part =='Upper':       
                    mc.connectAttr (upperLidOpenAttr, emotionPMA+'.input1D[1]')
                    setRangeAttr = 'X' 
                    if column == 'inner':
                        mc.connectAttr (emotionPMA+'.output1D', side+'_innerWideOpen_multiplyDivide.input1X',f=True)
                        mc.connectAttr (emotionPMA+'.output1D', side+'_innerWideOpen_plusMinusAverage.input1D[0]',f=True) 
                        mc.connectAttr (emotionPMA+'.output1D', side+'_innerWideOpen_setRange.maxX',f=True) 
                    if column == 'mid':    
                        mc.connectAttr (emotionPMA+'.output1D', side+'_midWideOpen_multiplyDivide.input1X',f=True)
                        mc.connectAttr (emotionPMA+'.output1D', side+'_midWideOpen_plusMinusAverage.input1D[0]',f=True) 
                        mc.connectAttr (emotionPMA+'.output1D', side+'_midWideOpen_setRange.maxX',f=True) 
                if part =='Lower':    
                    mc.connectAttr (lowerLidOpenAttr, emotionPMA+'.input1D[1]')
                    setRangeAttr = 'Y'  
                mc.connectAttr (emotionPMA+'.output1D',side+'_'+column+'EyeLidBlink_setRange.min'+setRangeAttr,f=True) 
                if createHelper==True:
                    emotionPMAHelper = mc.createNode ('plusMinusAverage', n=side+'_'+column+part+'EmotionHelper_plusMinusAverage')
                    mc.connectAttr (emotionMD+'.output'+mdAttr, emotionPMAHelper+'.input1D[0]')                                            
                    mc.connectAttr (side+'_'+column+part+'LidHelper_multiplyDivide.outputX', emotionPMAHelper+'.input1D[1]')                        
                    mc.connectAttr (emotionPMAHelper+'.output1D',side+'_'+column+'EyeLidBlinkHelper_setRange.min'+setRangeAttr,f=True)             
                    mc.connectAttr (emotionBlinkLinePMA+'.output1D', side+'_'+column+part+'LidHelper_plusMinusAverage.input1D[1]',f=True)   
                    if part =='Upper':
                        if column == 'inner':
                            wideOpenEmotionPMA = mc.createNode ('plusMinusAverage', n=side+'_'+column+'UpperEmotionWideOpenHelper_plusMinusAverage')
                            mc.connectAttr (side+'_innerUpperLidHelper_multiplyDivide.outputX', wideOpenEmotionPMA+'.input1D[0]',f=True)
                            mc.connectAttr (emotionMD+'.output'+mdAttr, wideOpenEmotionPMA+'.input1D[1]',f=True)
                            mc.connectAttr (wideOpenEmotionPMA+'.output1D', side+'_innerWideOpen_setRange.maxY',f=True)
                        if column == 'mid':
                            wideOpenEmotionPMA = mc.createNode ('plusMinusAverage', n=side+'_'+column+'UpperEmotionWideOpenHelper_plusMinusAverage')  
                            mc.connectAttr (side+'_midUpperLidHelper_multiplyDivide.outputX', wideOpenEmotionPMA+'.input1D[0]',f=True)
                            mc.connectAttr (emotionMD+'.output'+mdAttr, wideOpenEmotionPMA+'.input1D[1]',f=True)
                            mc.connectAttr (wideOpenEmotionPMA+'.output1D', side+'_midWideOpen_setRange.maxY',f=True)
                    
        #Outer Lid
        createLid (columns[2])
    else:
        createLid ('mid')
    return returnList





#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------#
#------------- ========[ MUSCLES ]======== ------------#
#------------------------------------------------------#


def createMuscleSpline(curve='', numJoints=3, originPlug='', insertionPlug='', mirror=1, name='muscle', ctrlScale=0.25, jointRadius=1, ctrlType=12, length=3, masterCtrl='master_cSpline_ctrl', tangentLength=1, jiggle=1, jiggleXYZ=[1,0.25,1], jiggleImpact=0.5, jiggleImpactStart=1000, jiggleImpactStop=0.001, cycle=12, rest=24, deleteOrig=1, parentGrp='', masterCtrlParent='spine_mainIk_ctrl', globalCtrl='base_global_ctrl', ctrlVis='rig_preferences.secondaryControls', createCSplineNode=1, lowLodMode=0):
    '''
    Creates a cMuscle spline, which has procedural jiggle. Either create cSpline by giving it a linear 2 CV curve or none at all.

    @inParam curve - string, linear curve to create spline for. It will create the spline based on the first and last cv. PLEASE name it with suffix _curve e.g. bicep_curve
    @inParam numJoints - int, number of joints created on spline, if 1, it will be created in middle of spline
    @inParam originPlug - string, usually a joint. Origin ctrl will be parentConstrained to this
    @inParam insertionPlug - string, usually a joint. Insertion ctrl will be parentConstrained to this
    @inParam mirror - int, mirror from side to side. Creates a separate muscle spline. 1 - Yes, 0 - No.
    @inParam name - string, name of muscle spline. If curve provided, it will take the name of the curve.
    @inParam ctrlScale - float, scale of ctrls created
    @inParam jointRadius - float, radius of joints created 
    @inParam ctrlType - int, type of ctrl shape to create. 12 = cube, 25 = circle
    @inParam length - float, if no curve is given, this flag is used to determine length of spline created
    @inParam masterCtrl - string, if master ctrl is given, it's jiggle attributes will be connected to the inBetween ctrl jiggle attributes by a mult node. If none given, a master ctrl will be automatically created and connected.
    @inParam tangentLength - float, look of curve tangent 
    @inParam jiggle - list, value of jiggle
    @inParam jiggleXYZ - list, amount of jiggle on x, y, z
    @inParam jiggleImpact - float, jiggle impact value
    @inParam jiggleImpactStart - float, jiggle impact value
    @inParam jiggleImpactStop - float, jiggle impact stop value
    @inParam cycle - float, cycle value, used in conjunction with rest
    @inParam rest - float, rest value, used in conjunction with cycle
    @inParam deleteOrig - int, if on, it will delete an existing muscleSpline node if it finds one
    @inParam parentGrp - string, parent cSpline group under this
    @inParam masterCtrlParent - string, parent of masterCtrl
    @inParam globalCtrl - string, the joints and control offsets will be scale constrained to this
    @inParam ctrlVis - string, connect the ctrlVis to this attribute for example rig_preferences.secondaryControls
    @inParam createCSplineNode - int, by default on. If 0, no cSpline node is created only the joints and controls. This is so that we can use the same joints and skinning for different lods of the rig, even lower lods that shouldn't have jiggle but should be able to transfer animation.
    @inParam lowLodMode - int, by default off. If 1, the joints and constraints will be deleted, cleans up everything to leave only the ctrls. Good for lower lods.

    @procedure rig.createMuscleSpline(curve='bicep_curve', numJoints=3, originPlug='L_arm_shoulder_env', insertionPlug='L_arm_lowerTwist1Vol_env', mirror=1, ctrlScale=0.1, jointRadius=1, ctrlType=12, tangentLength=1, jiggle=1, jiggleXYZ=[1,0.25,1], jiggleImpact=0.5, jiggleImpactStart=1000, jiggleImpactStop=0.001, cycle=4, rest=12, parentGrp=otherNull, masterCtrlParent='spine_mainIk_ctrl', createCSplineNode=1)
    '''
    #---------------------[ Setup ]---------------------#
    #Load maya muscle plugin
    if not mc.pluginInfo('MayaMuscle.so', q=1, l=1):
        mc.loadPlugin('MayaMuscle.so')
        print 'Maya Muscle plugin loaded.'

    #If mirror flag is on (1) to create a mirrored cSpline, search for L_ and R_ in the curve name. If none found print an error message.
    sides = ['']
    if mirror:
        if curve:
            if curve[0:2] == 'L_':
                name = curve[2:]
                sides = ['L_', 'R_']
            elif curve[0:2] == 'R_':
                name = curve[2:]
                sides = ['R_', 'L_']
            else:
                #Cannot find L or R in name so mirror is set to off.
                mirror = 0
                print 'createMuscleSpline(), @inParam mirror: Prefix of curve or name does not begin with L_ or R_ so not mirrored'
        else:
            if name[0:2] == 'L_':
                name = name[2:]
                sides = ['L_', 'R_']
            elif name[0:2] == 'R_':
                name = name[2:]
                sides = ['R_', 'L_']
            else:
                #Cannot find L or R in name so mirror is set to off.
                mirror = 0
                print 'createMuscleSpline(), @inParam mirror: Prefix of curve or name does not begin with L_ or R_ so not mirrored'

    

    #---------------------[ Master Ctrl ]---------------------#
    #Create a master control to control all of the cSpline jiggle attributes. This will act as a multiplier.
    if not mc.objExists(masterCtrl):
        masterCtrl = createCtrl(ctrl='master_cSpline_ctrl', ctrlType=24, pos=[-1.3,4.3,2.9], scale=[0.28,0.28,0.28], parent=masterCtrlParent, attrsToLock=['tx','ty','tz','rx','ry','rz','sx','sy','sz','v'])[0]

        addDoubleAttr(ctrl=masterCtrl, attr='jiggle', min=-10000, max=10000, dv=1)
        addDoubleAttr(ctrl=masterCtrl, attr='jiggleImpact', min=-10000, max=10000, dv=0.5)
        addDoubleAttr(ctrl=masterCtrl, attr='jiggleImpactStart', min=-10000, max=10000, dv=1000)
        addDoubleAttr(ctrl=masterCtrl, attr='jiggleImpactStop', min=-10000, max=10000, dv=0.001)
        addDoubleAttr(ctrl=masterCtrl, attr='cycle', min=-10000, max=10000, dv=6)
        addDoubleAttr(ctrl=masterCtrl, attr='rest', min=-10000, max=10000, dv=12)

    #There are some multNodes created down below. Create multNode list so that if createCSpline node is off, at the end of this proc I will delete them as they wont be needed.
    masterMultNodes = []


    #---------------------[ Sides ]---------------------#
    #Colour of control.
    colourCtrl = 6
    #Return attributes.
    cMuscleSplines = []
    inBetweenCtrls = []
    orientCons = []
    joints = []

    for side in sides:
        print '#------------------#'
        #Get name prefix used for objects 
        name = side+name

        #If curve variable given, get name that will be used and mirror curve if mirror variable is 1.
        if curve:
            #Check curve object exists, if not error.
            if mc.objExists(curve):
                #Freeze transforms of curve and change pivot to origin.
                mc.makeIdentity(curve, apply=1, t=1, r=1, s=1, n=0)
                mc.move(0,0,0, curve+'.scalePivot', curve+'.rotatePivot')

                #If mirror is 1, mirror the curve.
                if mirror:
                    #If side is first in list, mirror the curve. 
                    if sides.index(side) == 0:
                        #If mirrored curve found, delete it and mirror. 
                        mirrorCurve = curve.replace(curve[0:2], sides[1])
                        if mc.objExists(mirrorCurve):
                            mc.delete(mirrorCurve)

                        #Duplicate the curve, scale in X by -1 and freeze transforms.
                        mc.duplicate(curve, n=mirrorCurve)
                        mc.setAttr(mirrorCurve+'.sx', -1)
                        mc.makeIdentity(mirrorCurve, apply=1, t=1, r=1, s=1, n=0)
                    else:
                        #Badly written - curve name doesn't change?
                        curve = curve.replace(curve[0:2], sides[1])

                #Get name from curve.
                if curve[-6:] == '_curve':
                    name = curve.replace('_curve', '')
                elif curve[-4:] == '_crv':
                    name = curve.replace('_crv', '')
                else:
                    name = curve
                    print 'createMuscleSpline(), @inParam curve: Please name your curve with suffix _curve e.g. bicep_curve'
            else:
                #Print error if curve doesn't exist.
                curve = ''
                mc.error('createMuscleSpline(), @inParam curve: Curve doesnt exist!')


        #Try to find if name+cMuscleSpline group already exists.
        print 'Creating '+name+'_cMuscleSpline'
        if mc.objExists(name+'_cMuscleSpline_grp'):
            #If it exists, delete it if deleteOrig variable is 1.
            if deleteOrig:
                #Delete group and any joints.
                mc.delete(name+'_cMuscleSpline_grp')

                joints = mc.ls(name+'_*_env')
                mc.delete(joints)
            else:
                #If deleteOrig variable is off, increment the name number.
                i = 0
                while mc.objExists(name+str(i)+'_cMuscleSpline_grp'):
                    i = i+1

                name = name+str(i)

        #Create groups for cSpline.
        masterGrp = mc.group(n=name+'_cMuscleSpline_grp', em=1, p=parentGrp)
        envGrp = mc.group(n=name+'_joint_grp', em=1, p=masterGrp)
        ctrlGrp = mc.group(n=name+'_ctrl_grp', em=1, p=masterGrp)


        #---------------------[ cMuscleSpline Node ]---------------------#
        #Create cMuscleSpline node, rename it and parent under the master group. 
        cMuscleSplineShape = mc.createNode('cMuscleSpline', n=name+'_cMuscleSpline')
        cMuscleSplineShape = mc.rename(name+'_cMuscleSpline', name+'_cMuscleSplineShape')
        cMuscleSpline = mc.listRelatives(cMuscleSplineShape, p=1)[0]
        cMuscleSpline = mc.rename(cMuscleSpline, name+'_cMuscleSpline')
        mc.parent(cMuscleSpline, masterGrp)
        cMuscleSplines.append(cMuscleSpline)

        #Connect the time to the inTime attribute of the cSplineShape. Add a few attributes that don't get created but should have, not sure why.
        mc.connectAttr('time1.outTime', cMuscleSplineShape+'.inTime')
        addDoubleAttr(ctrl=cMuscleSplineShape, attr='curLen', min=-1000, max=1000, dv=2)
        addDoubleAttr(ctrl=cMuscleSplineShape, attr='pctSquash', min=-1000, max=1000, dv=0)
        addDoubleAttr(ctrl=cMuscleSplineShape, attr='pctStretch', min=-1000, max=1000, dv=0)
        mc.connectAttr(cMuscleSplineShape+'.outLen', cMuscleSplineShape+'.curLen')
        mc.connectAttr(cMuscleSplineShape+'.outPctSquash', cMuscleSplineShape+'.pctSquash')
        mc.connectAttr(cMuscleSplineShape+'.outPctStretch', cMuscleSplineShape+'.pctStretch')

        #Set some cSpline attributes.
        mc.setAttr(cMuscleSplineShape+'.lenDefault', 2)
        mc.setAttr(cMuscleSplineShape+'.lenSquash', 1)
        mc.setAttr(cMuscleSplineShape+'.lenStretch', 4)

        #Create a blendColours node and connect the cSpline up axis to it. This will be used for the upVector.
        blendColours = mc.shadingNode('blendColors', asUtility=1, n=name+'_blendColors')
        mc.connectAttr(cMuscleSplineShape+'.upAxis', blendColours+'.blender')
        mc.setAttr(blendColours+'.color1R', 0)
        mc.setAttr(blendColours+'.color1G', 0)
        mc.setAttr(blendColours+'.color1B', 1)
        mc.setAttr(blendColours+'.color2R', 1)
        mc.setAttr(blendColours+'.color2G', 0)
        mc.setAttr(blendColours+'.color2B', 0)



        #---------------------[ Joints ]---------------------#
        #Work out the position of the joints along the cSpline based on number of joints.
        jointPosMult = 1
        if numJoints != 1:
            jointPosMult = 1/float(numJoints-1)

        #Create joints along the cSpline curve. 
        for i in range(numJoints):
            #Create joint. 
            envNum = '%03d' % i
            env = createJoint(name=name+'_'+envNum+'_env', radius=jointRadius, parent='jointHierarchy')
            joints.append(env)

            #Work out position of joint along uValue of cSpline
            pos = 0.5
            if numJoints != 1:
                pos = jointPosMult * i

            #Add uValue attribute to control
            envUValue = addDoubleAttr(ctrl=env, attr='uValue', min=0, max=1, dv=pos)

            #Connect the cSpline node outTranslate and outRotate attributes to the joints translation and rotation
            mc.connectAttr(cMuscleSplineShape+'.outputData['+str(i)+'].outTranslate', env+'.t')
            mc.connectAttr(cMuscleSplineShape+'.outputData['+str(i)+'].outRotate', env+'.r')

            #Connect the uValue and rotateOrder of the joint to the cSpline node
            mc.connectAttr(env+'.uValue', cMuscleSplineShape+'.readData['+str(i)+'].readU')
            mc.connectAttr(env+'.rotateOrder', cMuscleSplineShape+'.readData['+str(i)+'].readRotOrder')

            #Set the side of the joint
            if env[0:2] == 'L_':
                mc.setAttr(env+'.side', 1)
            elif env[0:2] == 'R_':
                mc.setAttr(env+'.side', 2)

            #Set joint variables
            otherType = env[2:-4]
            mc.setAttr(env+'.type', 18)
            mc.setAttr(env+'.otherType', otherType, type='string')

            #If global control exists scale constraint the joint to it
            if mc.objExists(globalCtrl):
                mc.scaleConstraint(globalCtrl, env, mo=1)



        #---------------------[ Curve ]---------------------#
        #Set the origin and insertion position, if no curve given, set insertion pos in Y to the length variable. If curve given, work out length and then set it.
        originPos = [0,0,0]
        insertionPos = [0,length,0]

        #Work out number of controls (origin and insertion have to be created)
        numCtrls = numJoints
        if numCtrls == 1:
            numCtrls = 3
        #Distance used in position of ctrl created
        distance = [0,length/(numCtrls-1),0]

        #If curve given, Find the origin and insertion position (start and end of curve). Find distance and length.
        if curve:
            insertionCV = mc.getAttr(curve+'.spans')
            originPos = mc.xform(curve+'.cv[0]', q=1, ws=1, t=1)
            insertionPos = mc.xform(curve+'.cv['+str(insertionCV)+']', q=1, ws=1, t=1)
            distance = [((insertionPos[0]-originPos[0])/(numCtrls-1)), ((insertionPos[1]-originPos[1])/(numCtrls-1)), ((insertionPos[2]-originPos[2])/(numCtrls-1))]

            length = mc.arclen(curve)



        #---------------------[ Ctrls ]---------------------#
        ctrls = []
        originCtrl = []
        insertionCtrl = []
        #Create origin and insertion controls.
        for i,ctrlName in enumerate(['origin', 'insertion']):
            #Work out colour of ctrl
            if side == ['L_']:
                colourCtrl = 18
            elif side == ['R_']:
                colourCtrl = 21

            #Create control.
            ctrl, ctrlOffset, ctrlStackOffset, ctrlOffsets = createCtrl(ctrl=name+'_'+ctrlName+'_ctrl', ctrlType=ctrlType, pos=[0,0,0], scale=[ctrlScale,ctrlScale,ctrlScale], iStack=1, stackNames=[], parent=ctrlGrp, attrsToLock=['sx','sy','sz','v'])
            
            #Add jiggle attributes to control.
            tangentLengthAttr = addDoubleAttr(ctrl=ctrl, attr='tangentLength', min=0, max=5, dv=1)
            jiggleAttr = addDoubleAttr(ctrl=ctrl, attr='jiggle', min=-10000, max=10000, dv=0)
            jiggleXAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleX', min=-10000, max=10000, dv=0)
            jiggleYAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleY', min=-10000, max=10000, dv=0)
            jiggleZAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleZ', min=-10000, max=10000, dv=0)
            jiggleImpactAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleImpact', min=-10000, max=10000, dv=0)
            jiggleImpactStartAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleImpactStart', min=-10000, max=10000, dv=jiggleImpactStart)
            jiggleImpactStopAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleImpactStop', min=-10000, max=10000, dv=jiggleImpactStop)
            cycleAttr = addDoubleAttr(ctrl=ctrl, attr='cycle', min=1, max=10000, dv=cycle)
            restAttr = addDoubleAttr(ctrl=ctrl, attr='rest', min=1, max=10000, dv=rest)

            if ctrlName == 'origin':
                #Move ctrl to position. Connect ctrl worldMatrix to the cSpline matrix.
                mc.move(originPos[0], originPos[1], originPos[2], ctrlOffsets[0], r=1)
                mc.connectAttr(ctrl+'.worldMatrix[0]', cMuscleSplineShape+'.controlData[0].insertMatrix')
                originCtrl.append(ctrl)
                originCtrl.append(ctrlOffsets)

                #Add the name of the joint to the control.
                if numJoints != 1:
                    addStringAttr(ctrl, attr='joint', string=name+'_000_env')

                ctrls.append(ctrl)
            else:
                #Move ctrl to position. Connect ctrl worldMatrix to the cSpline matrix.
                mc.move(insertionPos[0], insertionPos[1], insertionPos[2], ctrlOffsets[0], r=1)
                mc.connectAttr(ctrl+'.worldMatrix[0]', cMuscleSplineShape+'.controlData['+str(numCtrls-1)+'].insertMatrix')
                insertionCtrl.append(ctrl)
                insertionCtrl.append(ctrlOffsets)

                #Add the name of the joint to the control.
                if numJoints != 1:
                    envTag = ('%03d' % (numCtrls-1))
                    addStringAttr(ctrl, attr='joint', string=name+'_'+envTag+'_env')

            #Scale constraint ctrl to globalCtrl if it exists.
            if mc.objExists(globalCtrl):
                mc.scaleConstraint(globalCtrl, ctrlOffset, mo=1)

            #Turn off visibility of origin and insertion controls.
            if numJoints == 1:
                mc.setAttr(ctrl+'.overrideEnabled', 1)
                mc.setAttr(ctrl+'.overrideVisibility', 0)

            
        #Aim origin and insertion controls the right way and delete the constraint.
        aimConsOrigin = mc.aimConstraint(originCtrl[0], insertionCtrl[1][0], aim=[0,-1,0], u=[1,0,0])[0]
        mc.delete(aimConsOrigin)
        aimConsInsertion = mc.aimConstraint(insertionCtrl[0], originCtrl[1][0], aim=[0,1,0], u=[1,0,0])[0]
        mc.delete(aimConsInsertion)

        #Parent constrain origin control to plug if given i.e. joint.
        if originPlug:
            if mc.objExists(originPlug):
                mc.parentConstraint(originPlug, originCtrl[1][0], mo=1)
            else:
                print 'createMuscleSpline(), @inParam originPlug: originPlug does not exist!'

        #Parent constrain insertion control to plug if given i.e. joint.
        if insertionPlug:
            if mc.objExists(insertionPlug):
                mc.parentConstraint(insertionPlug, insertionCtrl[1][0], mo=1)
            else:
                print 'createMuscleSpline(), @inParam insertionPlug: insertionPlug does not exist!'


        #Colour of ctrl.
        if side == ['R_']:
            colourCtrl = 13

        #Create inBetween controls (ones that will jiggle). Work out its position and number of inbetween controls.
        numInbetweenCtrls = numCtrls - 2
        ctrlPosMult = 1/float(numCtrls-1)
        for i in range(numInbetweenCtrls):
            #Work out ctrl position and ctrl number.
            ctrlPos = (ctrlPosMult * (i+1)) * length
            ctrlNum = '%03d' % (i+1)

            #Create control. Aim it correctly and then delete the constraint.
            ctrl, ctrlOffset, ctrlStackOffset, ctrlOffsets = createCtrl(ctrl=name+'_'+ctrlNum+'_ctrl', ctrlType=ctrlType, pos=[(distance[0]*(i+1))+originPos[0], (distance[1]*(i+1))+originPos[1], (distance[2]*(i+1))+originPos[2]], scale=[ctrlScale,ctrlScale,ctrlScale], iStack=1, stackNames=['_zero_offset'], parent=ctrlGrp, attrsToLock=['sx','sy','sz','v'])
            aimCons = mc.aimConstraint(originCtrl[0], ctrlOffsets[0], aim=[0,-1,0], u=[1,0,0])[0]
            mc.delete(aimCons)

            #Add joint name to ctrl as an attribute.
            if numJoints == 1:
                addStringAttr(ctrl, attr='joint', string=name+'_000_env')
            else:
                addStringAttr(ctrl, attr='joint', string=name+'_'+ctrlNum+'_env')
            ctrls.append(ctrl)
            inBetweenCtrls.append(ctrl)

            #Reorder control offset down. Connect the control worldMatrix to the cSpline.
            mc.reorder(ctrlOffsets[0], relative=-1)
            mc.connectAttr(ctrl+'.worldMatrix[0]', cMuscleSplineShape+'.controlData['+str(i+1)+'].insertMatrix')

            #Add jiggle attributes to the ctrl. 
            tangentLengthAttr = addDoubleAttr(ctrl=ctrl, attr='tangentLength', min=0, max=5, dv=tangentLength)
            jiggleAttr = addDoubleAttr(ctrl=ctrl, attr='jiggle', min=-10000, max=10000, dv=jiggle)
            jiggleXAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleX', min=-10000, max=10000, dv=jiggleXYZ[0])
            jiggleYAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleY', min=-10000, max=10000, dv=jiggleXYZ[1])
            jiggleZAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleZ', min=-10000, max=10000, dv=jiggleXYZ[2])
            jiggleImpactAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleImpact', min=-10000, max=10000, dv=jiggleImpact)
            jiggleImpactStartAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleImpactStart', min=-10000, max=10000, dv=jiggleImpactStart)
            jiggleImpactStopAttr = addDoubleAttr(ctrl=ctrl, attr='jiggleImpactStop', min=-10000, max=10000, dv=jiggleImpactStop)
            cycleAttr = addDoubleAttr(ctrl=ctrl, attr='cycle', min=1, max=10000, dv=cycle)
            restAttr = addDoubleAttr(ctrl=ctrl, attr='rest', min=1, max=10000, dv=rest)

            #Connect the attributes to the cSpline relevent attribute. 
            for attr in ['tangentLength', 'jiggleX', 'jiggleY', 'jiggleZ']:
                mc.connectAttr(ctrl+'.'+attr, cMuscleSplineShape+'.controlData['+str(i+1)+'].'+attr)
                
            #Connect the master control jiggle attributes to a multiply divide node. Connect the ctrl jiggle attributes to the multiply node and then connect
            #the output of the multiply node to the cSpline. The ctrl attributes are usually set to 1, and the master ctrl will be the actual value. 
            for attr in ['jiggle', 'jiggleImpact', 'jiggleImpactStart', 'jiggleImpactStop', 'cycle', 'rest']:
                multNode = mc.shadingNode('multiplyDivide', asUtility=1, n=ctrl+'_'+attr+'_multNode')
                mc.connectAttr(ctrl+'.'+attr, multNode+'.input1X')
                mc.connectAttr(masterCtrl+'.'+attr, multNode+'.input2X')
                mc.connectAttr(multNode+'.outputX', cMuscleSplineShape+'.controlData['+str(i+1)+'].'+attr)

                #Master ctrl attr will multiply with ctrl attr so keep this as 1.
                mc.setAttr(ctrl+'.'+attr, 1)

                masterMultNodes.append(multNode)
        

            #Create origin and insertion control offsets for orient and aim constraints. 
            originOffset = createOffset(name=name+'_aimOrigin_'+str(i+1)+'_offset', stack=1, stackNames=[name+'_aimOriginZero_'+str(i+1)+'_offset'], parent=ctrlOffsets[0], snapToObj=ctrlOffsets[0])
            insertionOffset = createOffset(name=name+'_aimInsertion_'+str(i+1)+'_offset', stack=1, stackNames=[name+'_aimInsertionZero_'+str(i+1)+'_offset'], parent=ctrlOffsets[0], snapToObj=ctrlOffsets[0])

            #Work out constraint value, for example if there is 1 inbetween ctrl the value will be 0.5, if there are 2, 0.33 and 0.66 etc.
            ctrlConsMult = (ctrlPosMult * (i+1))

            #Constrain the ctrl offset to the origin and insertion control.
            pointCons = mc.pointConstraint(originCtrl[0], insertionCtrl[0], ctrlOffsets[1])[0]
            mc.setAttr(pointCons+'.'+originCtrl[0]+'W0', (1-ctrlConsMult))
            mc.setAttr(pointCons+'.'+insertionCtrl[0]+'W1', ctrlConsMult)
            orientCon = mc.orientConstraint(originOffset[1], insertionOffset[1], ctrlOffsets[1], mo=1)[0]
            mc.setAttr(orientCon+'.interpType', 2)
            mc.setAttr(orientCon+'.'+originOffset[1]+'W0', (1-ctrlConsMult))
            mc.setAttr(orientCon+'.'+insertionOffset[1]+'W1', ctrlConsMult)
            #Sometimes the orient constraint gimbal locks is insertion and origin rotate too much. Might want to delete them and constrain directly to a joint.
            orientCons.append(orientCon)

            #Constrain the origin offset to the origin and insertion control. Aim constraint the origin offset to the origin ctrl. 
            pointCons = mc.pointConstraint(originCtrl[0], insertionCtrl[0], originOffset[1])[0]
            mc.setAttr(pointCons+'.'+originCtrl[0]+'W0', (1-ctrlConsMult))
            mc.setAttr(pointCons+'.'+insertionCtrl[0]+'W1', ctrlConsMult)

            aimCons = mc.aimConstraint(originCtrl[0], originOffset[1], aim=[0,-1,0], u=[1,0,0], wut='objectRotation', wuo=originCtrl[0], mo=1)[0]
            mc.connectAttr(blendColours+'.output', aimCons+'.upVector')
            mc.connectAttr(blendColours+'.output', aimCons+'.worldUpVector')

            #Constrain the insertion offset to the origin and insertion control. Aim constraint the insertion offset to the insertion ctrl. 
            pointCons = mc.pointConstraint(originCtrl[0], insertionCtrl[0], insertionOffset[1])[0]
            mc.setAttr(pointCons+'.'+originCtrl[0]+'W0', (1-ctrlConsMult))
            mc.setAttr(pointCons+'.'+insertionCtrl[0]+'W1', ctrlConsMult)

            #Aim constrain the insertion offset to the insertion control.
            aimCons = mc.aimConstraint(insertionCtrl[0], insertionOffset[1], aim=[0,1,0], u=[1,0,0], wut='objectRotation', wuo=insertionCtrl[0], mo=1)[0]
            mc.connectAttr(blendColours+'.output', aimCons+'.upVector')
            mc.connectAttr(blendColours+'.output', aimCons+'.worldUpVector')

            #Scale constraint ctrl offset to global control if it exists.
            if mc.objExists(globalCtrl):
                mc.scaleConstraint(globalCtrl, ctrlOffset, mo=1)

        ctrls.append(insertionCtrl[0])

        #Connect control visibility switch to ctrlShape vis.
        for ctrl in ctrls:
            ctrlShape = mc.listRelatives(ctrl, s=1)[0]

            if ctrlVis:
                if mc.objExists(ctrlVis):
                    mc.connectAttr(ctrlVis, ctrlShape+'.lodVisibility')
                else:
                    print 'createMuscleSpline(), @inParam ctrlVis: ctrlVis attribute does not exist!'

        #If createCSplineNode is off, delete the cSpline node. Parent constrain the relevant joint to the ctrl.
        if createCSplineNode == 0:
            mc.delete(cMuscleSpline, blendColours)
            for node in masterMultNodes:
                if mc.objExists(node):
                    mc.delete(node)

            for ctrl in ctrls:
                if mc.attributeQuery('joint', node=ctrl, ex=1):
                    joint = mc.getAttr(ctrl+'.joint')
                    mc.parentConstraint(ctrl, joint, mo=1)

        #Low lod mode is for lower lod rigs which may not want the jiggle computation but still need the ctrls for animation purposes. So delete the cSpline node 
        #and delete extra things like the joints.
        if lowLodMode:
            if createCSplineNode == 1:
                mc.delete(cMuscleSpline, blendColours)
                for node in masterMultNodes:
                    if mc.objExists(node):
                        mc.delete(node)

            for ctrl in ctrls:
                mc.parent(ctrl, masterGrp) 
            mc.delete(ctrlGrp, envGrp)

            for joint in joints:
                if mc.objExists(joint):
                    mc.delete(joint)



        print '[ Successfully created '+name+'_cMuscleSpline ]'


    mc.select(cl=1)

    #Return all cSpline nodes, controls and orient constraints because I found in some poses there was flipping so deleted the orient constraints in a postScript 
    #and aimed a
    return cMuscleSplines, masterCtrl, inBetweenCtrls, orientCons









#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#----------------- ========[ MODULES ]======== --------------#
#------------------------------------------------------------#

def dualPoleVectorLeg(hipEnv='', hipEnvParent='', legCtrl='', poleVecCtrls=[], aimVector=[-1,0,0], upVector=[0,0,-1]):
    '''
    Create a dual pole vector leg. This is for legs with 2 knee type joints - for example a butterfly or insect.

    @inParam hipEnv - string, hip joint to duplicate (root leg joint)
    @inParam hipEnvParent - string, hip joint will be parentConstrained to this object (joint or ctrl)
    @inParam legCtrl - string, main ik leg control
    @inParam poleVecCtrls - list, poleVector controls for the knee and ankle poleVectors, knee first, then ankle
    @inParam aimVector - list, aimVector of upper knee joint (which axis does it point down to the second knee)
    @inParam upVector - list, upVector of upper knee aimVector
    
    @procedure rig.dualPoleVectorLeg(hipEnv='L_midleg_hip_env', hipEnvParent='L_foreleg_hip_ctrl', legCtrl='L_midleg_mainIk_ctrl', poleVecCtrls=['L_midleg_poleVectorIk_ctrl', 'L_midleg_ankleIk_ctrl'], aimVector=[-1,0,0], upVector=[0,0,-1])
    '''
    if not hipEnv:
        print 'No hip joint given!'

    env = ''
    rigNull = ''
    if mc.objExists(hipEnv):
        mainEnvs, upEnvs, lowEnvs, outputEnvs = ([] for i in range(4))
        for chain in ['ikMain', 'ikUp', 'ikLow', 'ik']:
            rootJnt = mc.duplicate(hipEnv)[0]
            rootJntSN = rootJnt.split('|')[-1]
            suffix = rootJntSN.split('_')[-1]
            if suffix[-1].isdigit():
                suffix = suffix[:-1]


            rigNull = rootJnt.split('_')[0]+'_'+rootJnt.split('_')[1]+'_rig_null'
            mc.parent(rootJnt, rigNull)
            stripObject(rootJnt)

            if 'ikMain' in chain:
                rootJntSN = rootJntSN.replace('_'+rootJntSN.split('_')[-1], '_ikMain_'+suffix)
                rootJnt = mc.rename(rootJnt, rootJntSN)
            elif 'ikUp' in chain:
                rootJntSN = rootJntSN.replace('_'+rootJntSN.split('_')[-1], '_ikUp_'+suffix)
                rootJnt = mc.rename(rootJnt, rootJntSN)
            elif 'ikLow' in chain:
                rootJntSN = rootJntSN.replace('_'+rootJntSN.split('_')[-1], '_ikLow_'+suffix)
                rootJnt = mc.rename(rootJnt, rootJntSN)
            elif 'ik' in chain:
                rootJntSN = rootJntSN.replace('_'+rootJntSN.split('_')[-1], '_ik_'+suffix)
                rootJnt = mc.rename(rootJnt, rootJntSN)


            jnts = mc.listRelatives(rootJnt, ad=1,f=1)
            for jnt in jnts:
                jntSN = jnt.split('|')[-1]
                suffix = jntSN.split('_')[-1]

                if 'ikMain' in chain:
                    jntSN = jntSN.replace('_'+suffix, '_ikMain_'+suffix)
                    mc.rename(jnt, jntSN)
                    mainEnvs.append(jntSN)
                elif 'ikUp' in chain:
                    jntSN = jntSN.replace('_'+suffix, '_ikUp_'+suffix)
                    mc.rename(jnt, jntSN)
                    upEnvs.append(jntSN)
                elif 'ikLow' in chain:
                    jntSN = jntSN.replace('_'+suffix, '_ikLow_'+suffix)
                    mc.rename(jnt, jntSN)
                    lowEnvs.append(jntSN)
                elif 'ik' in chain:
                    jntSN = jntSN.replace('_'+suffix, '_ik_'+suffix)
                    mc.rename(jnt, jntSN)
                    outputEnvs.append(jntSN)

            if 'ikMain' in chain:    
                mainEnvs.append(rootJntSN)
                mainEnvs = mainEnvs[::-1]
            if 'ikUp' in chain:    
                upEnvs.append(rootJntSN)
                upEnvs = upEnvs[::-1]
            if 'ikLow' in chain:    
                lowEnvs.append(rootJntSN)
                lowEnvs = lowEnvs[::-1]
            if 'ik' in chain:    
                outputEnvs.append(rootJntSN)
                outputEnvs = outputEnvs[::-1]

        for env in mainEnvs:    mc.joint(mainEnvs[0], e=1, spa=1, ch=1)
        for env in upEnvs:    mc.joint(upEnvs[0], e=1, spa=1, ch=1)
        for env in lowEnvs:    mc.joint(lowEnvs[0], e=1, spa=1, ch=1)
        for env in outputEnvs:    mc.joint(outputEnvs[0], e=1, spa=1, ch=1)


        kneeAimLoc = createLoc(name=upEnvs[1].replace('_'+suffix,'_aimUpLoc'), pos=[0,0,0], rot=[0,0,0], scale=[1,1,1], parent=lowEnvs[1], v=0)
        setTransforms(obj=kneeAimLoc, t=[0,0,1], r=[0,0,0], ls=[0.02,0.02,0.02])

        mainIk = createIk(name=mainEnvs[0].replace('_'+suffix,''), solver='ikSCsolver', startJoint=mainEnvs[0], endEffector=mainEnvs[3], parent=rigNull, ctrl=legCtrl, consType='point', v=0)
        upIk = createIk(name=upEnvs[0].replace('_'+suffix,''), solver='ikRPsolver', startJoint=upEnvs[0], endEffector=upEnvs[2], poleVector=poleVecCtrls[0], parent=rigNull, ctrl=mainEnvs[2], v=0)
        lowIk = createIk(name=lowEnvs[0].replace('_'+suffix,''), solver='ikRPsolver', startJoint=lowEnvs[1], endEffector=lowEnvs[3], poleVector=poleVecCtrls[1], parent=rigNull, ctrl=mainEnvs[3], v=0)
        
        mc.parentConstraint(hipEnvParent, mainEnvs[0], mo=1)
        mc.parentConstraint(hipEnvParent, upEnvs[0], mo=1)

        mc.parentConstraint(upEnvs[0], outputEnvs[0], mo=1)
        mc.parentConstraint(lowEnvs[2], outputEnvs[2], mo=1)
        mc.parentConstraint(lowEnvs[3], outputEnvs[3], mo=1)

        mc.pointConstraint(upEnvs[1], outputEnvs[1], mo=1)
        mc.aimConstraint(lowEnvs[2], outputEnvs[1], aim=aimVector, u=upVector, wut='object', wuo=kneeAimLoc, mo=1)

        mc.parentConstraint(upEnvs[0], lowEnvs[0], mo=1)


        mc.setAttr(mainEnvs[0]+'.v', 0)
        mc.setAttr(upEnvs[0]+'.v', 0)
        mc.setAttr(lowEnvs[0]+'.v', 0)
        mc.setAttr(outputEnvs[0]+'.v', 0)

        return outputEnvs
    else:
        mc.error('Hip joint does not exists - '+hipEnv)


def bakeBlendShapes (sourceMesh, targetMesh, smooth=False):
    '''
    Sets the Quadruped Fk leg control rotations values to zero by setting the ctrl parent groups with those rotations.
    @inParam sourceMesh - string, name of source mesh
    @inParam targetMesh - string, name of target mesh to bake all blendshape targets to.
    @procedure  rig.bakeBlendShapes (sourceMesh='aliceHead_geo', targetMesh='kirkHead_geo')
    '''
    targetShapes = mc.listRelatives ('blendshapes_grp', ad=True, type='shape')
    for t in targetShapes:
        target = mc.listRelatives (t,p=True)[0]
        if smooth == True:
            smoothNode = mc.polySmooth (target, dv=1) 
        bs = mc.blendShape (target, targetMesh, sourceMesh, w=[(0, 1), (1, 1)])[0]
        rig.duplicateClean (sourceMesh, name = target, parent = 'new_blendshapes_grp')
        mc.delete (bs)
        if smooth == True:
            mc.delete (smoothNode)
        print 'baking '+target



def quadrupedFkCtrlRotationFix(module='L_midleg'):
    '''
    Sets the Quadruped Fk leg control rotations values to zero by setting the ctrl parent groups with those rotations.

    @inParam module - string, name of quadruped leg module to fix fk rotations for.
    
    @procedure rig.quadrupedFkCtrlRotationFix(module='L_foreleg')
    '''  

    if mc.objExists(module+'_hipFk_ctrl'):
        ctrls = [module+'_hipFk_ctrl', module+'_kneeFk_ctrl', module+'_ankleFk_ctrl', module+'_tarsalFk_ctrl']
        for ctrl in ctrls:
            trans = getTransforms(obj=ctrl, attrType='getAttr')
            setTransforms(obj=ctrl, r=[0,0,0])

            offset = ctrl.replace('_ctrl', 'ControlParent_grp')
            if ctrl == module+'_hipFk_ctrl':
                offsetTrans = getTransforms(obj=offset, attrType='getAttr')
                mc.disconnectAttr(module+'_inheritParentRotation_reverse.outputX', module+'_fkHipControlParent_orientConstraint.'+module+'_hipControlCogPlugOffset_grpW0')
                mc.delete(module+'_fkHipControlParent_orientConstraint')

                rx = trans['r'][0] + offsetTrans['r'][0]
                ry = trans['r'][1] + offsetTrans['r'][1]
                rz = trans['r'][2] + offsetTrans['r'][2]
                if offset[0:1] == 'R':
                    rx = trans['r'][0] + offsetTrans['r'][0]
                    ry = (trans['r'][1]*-1) + offsetTrans['r'][1]
                    rz = (trans['r'][2]*-1) + offsetTrans['r'][2]

                setTransforms(obj=offset, r=[rx,ry,rz])
                
                orientCons = mc.orientConstraint(module+'_hipControlCogPlugOffset_grp', module+'_hipControlParent_grp', offset, n=module+'_fkHipControlParent_orientConstraint', mo=1)[0]
                mc.connectAttr(module+'_inheritParentRotation_reverse.outputX',  orientCons+'.'+module+'_hipControlCogPlugOffset_grpW0')
                mc.connectAttr(module+'_hipFk_ctrl.inheritParentRotation',  orientCons+'.'+module+'_hipControlParent_grpW1')
            else:
                setTransforms(obj=offset, r=trans['r'])
    else:
        print(module+' does not exist. Please check this is a Quadruped leg module.')



def copySurfaceCVs(surface=''):
    '''
    Copies a rig guide surface cv positions and returns and prints the cv positions as a dictionary. Use with copySurface() below. 
    Mouth module fails if you import anything, so I needed to copy the placement cv positions.

    @inParam surface - string, name of surface to copy CVs for
    
    @procedure      dict = copySurfaceCV(surface='mouth_surface_rigGuide')
    ''' 
    cvDict = {}
    for i in range(0, 11):
        for j in range(0, 7):
            cv = surface+'.cv['+str(i)+']['+str(j)+']'
            cvDict[cv] = mc.xform(cv, q=1, ws=1, t=1)

    print cvDict
    return cvDict



def copySurface(cvDict={}, surface=''):
    '''
    Copies a rig guide surface cv positions by giving it a dictionary of cv positions. Use with copySurfaceCVs() above. 
    Mouth module fails if you import anything, so I needed to copy the placement cv positions.

    @inParam surface - string, name of surface
    
    @procedure     copySurface(cvDict=dict, surface='mouth_surface_rigGuide')
    ''' 
    for i in range(0, 11):
        for j in range(0, 7):
            cv = surface+'.cv['+str(i)+']['+str(j)+']'
            cvPos = cvDict[cv]
            mc.move(cvPos[0], cvPos[1], cvPos[2], cv, ws=1)



def mirrorCtrlShapes(ctrls=[], mirror='L'):
    '''
    Mirrors ctrl shapes. Used for control array control for example because the rotation is messed up when you mirror the controls it isn't correct.

    @inParam ctrls - list, name of controls to mirror for example L_ctrl will mirror to R_ctrl if mirror flag is L
    @inParam mirror - string, which side to mirror from

    @procedure rig.mirrorCtrlShapes(ctrls=[], mirror='L')
    ''' 
    if not ctrls:
        ctrls = mc.ls(mirror+'_*_ctrl')

    for ctrl in ctrls:
        ctrlShapes = mc.listRelatives(ctrl, s=1)
        if ctrlShapes:
            for ctrlShape in ctrlShapes:
                if ctrlShape[0:2] == 'L_':
                    oppCtrlShape = ctrlShape.replace('L_', 'R_')
                elif ctrlShape[0:2] == 'R_':
                    oppCtrlShape = ctrlShape.replace('R_', 'L_')
                elif ctrlShape[0:2] == 'T_':
                    oppCtrlShape = ctrlShape.replace('T_', 'B_')
                elif ctrlShape[0:2] == 'B_':
                    oppCtrlShape = ctrlShape.replace('B_', 'T_')

                numCVs = (mc.getAttr(ctrlShape+'.spans')) + (mc.getAttr(ctrlShape+'.degree'))
                for i in range(0, numCVs):
                    cvPos = mc.xform(ctrlShape+'.cv['+str(i)+']', q=1, t=1, ws=1)
                    mc.move((cvPos[0]*-1), cvPos[1], cvPos[2], oppCtrlShape+'.cv['+str(i)+']', ws=1)

                print ctrlShape+' mirrored to '+oppCtrlShape



def dynamicAE(rigType='biped'):
    '''
    Creates muppet template for the dynamic attribute editor. Works with Pinocchio 5.

    @inParam rigType - string, type of rig - choices are biped or quadruped

    @procedure rig.dynamicAE(rigType='biped')     
    ''' 
    if rigType == 'biped':
        name = 'Man'
    elif rigType == 'quadruped':
        name = 'Quadruped'

    mc.sets(em=1, n='picker_flow')
    mc.sets(em=1, n=rigType+'AnimSpace_script')    
    mc.addAttr(rigType+'AnimSpace_script', rigType+'AnimSpace_script', dt='string', ln='melEval')    
    mc.setAttr(rigType+"AnimSpace_script.melEval", "dnLibPicker; dnLibPicker_"+rigType+"AnimSpaceFrame(\"dynamicAe\")", type='string')
    mc.sets(rigType+'AnimSpace_script', n=rigType+'AnimSpace_frame')
    mc.sets(rigType+'AnimSpace_frame', add='picker_flow')
    mc.sets(em=1, n=rigType+'Picker_script')
    mc.addAttr(rigType+'Picker_script', dt='string', ln='melEval')  
    mc.setAttr(rigType+"Picker_script.melEval", "dnLibPicker; picker_archetype"+name+"(\"dynamicAe\")", type='string')
    mc.sets(rigType+'Picker_script', n=rigType+'Picker_frame')
    mc.sets(rigType+'Picker_frame', add='picker_flow')
    mc.sets('picker_flow', add='rig_column')




#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#------------------ ========[ PYTHON ]======== --------------#
#------------------------------------------------------------#

def createListFromSel(hier=0):
    '''
    Create and print a python list from selected objects. Saves time writing it out all the time.

    @inParam hier - string, if hierarchy is on, it will return a list of all descendants but not constraints or ikHandles etc.
    
    @procedure rig.createListFromSel(hier=1)
    '''
    objs = mc.ls(sl=1)

    listObjs = []
    for obj in objs:
        listObjs.append(obj)

        if hier == 1:
            for obj in mc.listRelatives(obj, ad=True, type='transform'):
                if not obj.endswith('_ikHandle') and not obj.endswith('_eff') and not mc.objectType(obj) == 'pointConstraint' and not mc.objectType(obj) == 'orientConstraint' and not mc.objectType(obj) == 'aimConstraint' and not mc.objectType(obj) == 'parentConstraint':
                    listObjs.append(obj)

    print listObjs
    return listObjs





























































#-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------#
#----------------- ========[ OTHER ]======== ----------------#
#------------------------------------------------------------#


def headAndNeckExtraSetup(otherNull='base_other_null'):
    '''
    Create head world space switch, added to head_mainIk_ctrl. Also creates a head_tiltIkOffset_ctrl.

    @inParam otherNull - string, specifies the null to put junk into (I call this the base_other_null). If none already exists, it will create one.
    
    @procedure rig.headAndNeckExtraSetup(otherNull='base_other_null')
    '''
    if not mc.objExists(otherNull):
        otherNull = mc.group(n='base_other_null', em=1, p='bodyRig')
        mc.setAttr(otherNull+'.v', 0)

    # ---------------- Setup neck tilt offset control ---------------- #
    #Delete existing parent constraint to offset and then parent constrain the offset to the spine 5 joint.
    mc.delete('head_tiltIk_offset_parentConstraint1')

    #Create a neck tilt offset control and parent it under the offset.
    ctrl = mm.eval('dnLibShape_wedge "head_tiltIkOffset_ctrl" 0.1 ')
    mm.eval('dnLibControl_makeIk("head_tiltIkOffset_ctrl", 0, "")')
    mm.eval('dnLibControl_makeSecondary("head_tiltIkOffset_ctrl")')
    childs = mc.listRelatives( 'head_tiltIk_offset', c=True )
    mc.parent( ctrl, 'head_tiltIk_offset')
    mc.makeIdentity( ctrl )

    mc.parentConstraint('spine_chestMixedSpace_null', 'head_tiltIk_offset', mo=1)
    mc.disconnectAttr('head_tiltIk_offset_parentConstraint1.constraintTranslateX', 'head_tiltIk_offset.tx')
    mc.disconnectAttr('head_tiltIk_offset_parentConstraint1.constraintTranslateY', 'head_tiltIk_offset.ty')
    mc.disconnectAttr('head_tiltIk_offset_parentConstraint1.constraintTranslateZ', 'head_tiltIk_offset.tz')

    
    #Reparent the children of the offset and existing neck tilt ctrl to the new tilt offset control.
    for child in childs:
        if not mc.nodeType( child ) == 'parentConstraint':
            mc.parent( child, 'head_tiltIkOffset_ctrl')
    
    #Duplicate head_1_env for head_1_base_env. Parent constrain the base joint to the tilt offset control.
    mc.duplicate('head_1_env', po=True, n= 'head_1Base_env')
    mc.parentConstraint('head_tiltIkOffset_ctrl', 'head_1Base_env')
    mc.parentConstraint( 'head_tiltIkOffset_ctrl', 'head_neckRoot_null', mo=True)



    # ---------------- Create world space switching for head control ---------------- #
    #Create base other null for bits and pieces.
    headOtherNull = mc.group(n='head_other_null', em=1, p=otherNull)
    mc.scaleConstraint('base_global_ctrl', headOtherNull, mo=1)

    #Create world space head null that is point constrained to spine 5 joint.
    worldHeadNull = mc.group(n='worldHeadSpace_null', em=1, p=headOtherNull)
    headPos = mc.xform('spine_5_env', q=1, t=1, ws=1)
    mc.move(headPos[0], headPos[1], headPos[2], worldHeadNull, r=1)
    mc.pointConstraint('spine_5_env', worldHeadNull, mo=1)

    #Edit the animation space attribute for the head control and add the world. Parent constrain the head ctrl offset to the world.
    mc.addAttr('head_mainIk_ctrl.animationSpace', e=1, enumName='head_global:spine_chestIkOffset:spine_mainIkOffset:head_tiltIk:head_world:')
    mc.parentConstraint(worldHeadNull, 'head_mainIk_offset', mo=1)
    mc.connectAttr('head_mainIk_ctrl_dnMultiPlexValue.valueOut[4]', 'head_mainIk_offset_parentConstraint1.'+worldHeadNull+'W4')


    mc.sets(ctrl, add='allAnimControls')
    mc.sets(ctrl, add='head_animControls_set')



#### Jim's Rope rig ######################################################################################################

import invertRig as rig
# Group node for the all the rope controls
sRopeCtrlGrp = mc.createNode ('transform', n='ropeCtrl_grp')
# Group node for the rope rig.
otherNull = mc.createNode ('transform', n='base_other_null')
 
def createRopeCtrl (sCurve, fCtrlScale = 1.0, sBaseParent = 'cluster_grp', sHullGrp = 'hullCluster_grp', sCtrlParent = sRopeCtrlGrp, bStartEndCtrl=False,  bDetailCtrl=True, bExtraCtrl= False, bRebuildCrv=True, iStackValue=1):
    ctrlDict = {'StartCluster':[], 'MidStartCluster':[], 'MidCluster':[], 'MidEndCluster':[], 'EndCluster':[],
                'StartCtrl':[], 'MidStartCtrl':[], 'MidCtrl':[], 'MidEndCtrl':[], 'EndCtrl':[]}
    sCurveName = sCurve.replace('_crv','')
    if bRebuildCrv==True:
        bMo=False
    else:
        bMo=True    
    #Create start/end clusters.
    sStartCluster = mc.cluster (sCurve+'.cv[0]', n=sCurveName+'Start_Cluster')   
    if bRebuildCrv  == True:   
        sEndCluster = mc.cluster (sCurve+'.cv[1]', n=sCurveName+'End_Cluster')
    else:
        sEndCluster = mc.cluster (sCurve+'.cv[4]', n=sCurveName+'End_Cluster')
    if not mc.objExists (sBaseParent):
        mc.createNode ('transform',n=sBaseParent, p=otherNull)
    if not mc.objExists (sHullGrp):
        mc.createNode ('transform',n=sHullGrp, p=sBaseParent)                
    mc.parent (sStartCluster[1], sHullGrp)
    mc.parent (sEndCluster[1], sHullGrp)
    ctrlDict['StartCluster'] = sStartCluster
    ctrlDict['EndCluster'] = sEndCluster           
    #Create Primary clusters  
    if bStartEndCtrl == True:
        sStartTransforms = rig.getTransforms (sStartCluster[1],attrType='rp')
        sStartPos = sStartTransforms['t']
        sEndTransforms = rig.getTransforms (sEndCluster[1],attrType='rp')
        sEndPos = sEndTransforms['t']                       
        sStartCtrl = rig.createCtrl(ctrl=sCurveName+'Start_ctrl', ctrlType=12, pos=sStartPos, rot=[0,0,0], scale=[fCtrlScale,fCtrlScale,fCtrlScale], parent=sCtrlParent,colour=6,iStack=iStackValue)      
        sEndCtrl = rig.createCtrl(ctrl=sCurveName+'End_ctrl', ctrlType=12, pos=sEndPos, rot=[0,0,0], scale=[fCtrlScale,fCtrlScale,fCtrlScale], parent=sCtrlParent,colour=6,iStack=iStackValue)   
        mc.pointConstraint (sStartCtrl[0], sStartCluster[1])
        mc.pointConstraint (sEndCtrl[0], sEndCluster[1])
        ctrlDict['StartCtrl'] = sStartCtrl
        ctrlDict['EndCtrl'] = sEndCtrl
        rig.lockAndHideAttr(sStartCtrl[0], ['sx','sy','sz','visibility'])
        rig.lockAndHideAttr(sEndCtrl[0], ['sx','sy','sz','visibility'])              
    # Rebuild curve. Do this to a linear curve before creating secondary and tertiary controls   
    if bRebuildCrv  == True:
        if bExtraCtrl == False:
            sBSplineCrv = mc.rebuildCurve (sCurve, ch=True, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=2, d=3, tol=0.01)
        if bExtraCtrl == True:
            sBSplineCrv = mc.rebuildCurve (sCurve, ch=True, rpo=True, rt=False, end=True, kr=False, kcp=False, kep=True, kt=False, s=8, d=3, tol=0.01)                     
        mc.rename (sBSplineCrv[1], sCurve+'_rebuildCurve')                
    # Unlike start/end clusters, these clusters are relative
    if bRebuildCrv  == True:
        if bExtraCtrl == False:                
            sMidStartCluster = mc.cluster (sCurve+'.cv[1]', n=sCurve+'MidStart_Cluster',rel=True)
            sMidCluster = mc.cluster (sCurve+'.cv[2]', n=sCurve+'Mid_Cluster',rel=True)
            sMidEndCluster = mc.cluster (sCurve+'.cv[3]', n=sCurve+'MidEnd_Cluster',rel=True)
        if bExtraCtrl == True:  
            sMidStartCluster = mc.cluster (sCurve+'.cv[3]', n=sCurve+'MidStart_Cluster',rel=True)
            sMidCluster = mc.cluster (sCurve+'.cv[5]', n=sCurve+'Mid_Cluster',rel=True)
            sMidEndCluster = mc.cluster (sCurve+'.cv[7]', n=sCurve+'MidEnd_Cluster',rel=True)
            #Create Extra Clusters
            sExtraStartCluster = mc.cluster (sCurve+'.cv[1]', n=sCurve+'ExtraStart_Cluster',rel=True)                                        
            sExtraStartACluster = mc.cluster (sCurve+'.cv[2]', n=sCurve+'ExtraStartA_Cluster',rel=True)
            sExtraStartBCluster = mc.cluster (sCurve+'.cv[4]', n=sCurve+'ExtraStartB_Cluster',rel=True)
            sExtraEndBCluster = mc.cluster (sCurve+'.cv[6]', n=sCurve+'ExtraEndB_Cluster',rel=True)
            sExtraEndACluster = mc.cluster (sCurve+'.cv[8]', n=sCurve+'ExtraEndA_Cluster',rel=True) 
            sExtraEndCluster = mc.cluster (sCurve+'.cv[9]', n=sCurve+'ExtraEnd_Cluster',rel=True)                               
            #Get Transforms of Extra Clusters
            sExtraStartTransforms = rig.getTransforms (sExtraStartCluster[1],attrType='rp')
            sExtraStartPos = sExtraStartTransforms['t']               
            sExtraStartATransforms = rig.getTransforms (sExtraStartACluster[1],attrType='rp')
            sExtraStartAPos = sExtraStartATransforms['t']
            sExtraStartBTransforms = rig.getTransforms (sExtraStartBCluster[1],attrType='rp')
            sExtraStartBPos = sExtraStartBTransforms['t']
            sExtraEndATransforms = rig.getTransforms (sExtraEndACluster[1],attrType='rp')
            sExtraEndAPos = sExtraEndATransforms['t']
            sExtraEndBTransforms = rig.getTransforms (sExtraEndBCluster[1],attrType='rp')
            sExtraEndBPos = sExtraEndBTransforms['t']
            sExtraEndTransforms = rig.getTransforms (sExtraEndCluster[1],attrType='rp')
            sExtraEndPos = sExtraEndTransforms['t']               
            # parent extra clusterhandles to transform with the same rotate pivot
            sExtraStartClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraStart_Cluster_Offset')
            mc.move (sExtraStartPos[0],sExtraStartPos[1],sExtraStartPos[2],sExtraStartClusterOffset)
            mc.makeIdentity(sExtraStartClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraStartCluster[1], sExtraStartClusterOffset)
            mc.parent (sExtraStartClusterOffset, sBaseParent)
            sExtraStartAClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraStartA_Cluster_Offset')
            mc.move (sExtraStartAPos[0],sExtraStartAPos[1],sExtraStartAPos[2],sExtraStartAClusterOffset)
            mc.makeIdentity(sExtraStartAClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraStartACluster[1], sExtraStartAClusterOffset)
            mc.parent (sExtraStartAClusterOffset, sBaseParent)
            sExtraStartBClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraStartB_Cluster_Offset')
            mc.move (sExtraStartBPos[0],sExtraStartBPos[1],sExtraStartBPos[2],sExtraStartBClusterOffset)
            mc.makeIdentity(sExtraStartBClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraStartBCluster[1], sExtraStartBClusterOffset) 
            mc.parent (sExtraStartBClusterOffset, sBaseParent)         
            sExtraEndAClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraEndA_Cluster_Offset')
            mc.move (sExtraEndAPos[0],sExtraEndAPos[1],sExtraEndAPos[2],sExtraEndAClusterOffset)
            mc.makeIdentity(sExtraEndAClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraEndACluster[1], sExtraEndAClusterOffset)
            mc.parent (sExtraEndAClusterOffset, sBaseParent)          
            sExtraEndBClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraEndB_Cluster_Offset')
            mc.move (sExtraEndBPos[0],sExtraEndBPos[1],sExtraEndBPos[2],sExtraEndBClusterOffset)
            mc.makeIdentity(sExtraEndBClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraEndBCluster[1], sExtraEndBClusterOffset) 
            mc.parent (sExtraEndBClusterOffset, sBaseParent)
            sExtraEndClusterOffset = mc.createNode ('transform',n=sCurve+'ExtraEnd_Cluster_Offset')
            mc.move (sExtraEndPos[0],sExtraEndPos[1],sExtraEndPos[2],sExtraEndClusterOffset)
            mc.makeIdentity(sExtraEndClusterOffset,apply=True, translate=True, rotate=True, scale=True )
            mc.parent (sExtraEndCluster[1], sExtraEndClusterOffset) 
            mc.parent (sExtraEndClusterOffset, sBaseParent)                                    
    else:
        sMidStartCluster = mc.cluster (sCurve+'.cv[1]', n=sCurve+'MidStart_Cluster',rel=False)
        sMidCluster = mc.cluster (sCurve+'.cv[2]', n=sCurve+'Mid_Cluster',rel=False)
        sMidEndCluster = mc.cluster (sCurve+'.cv[3]', n=sCurve+'MidEnd_Cluster',rel=False)
    sMidTransforms = rig.getTransforms (sMidCluster[1],attrType='rp')
    sMidPos = sMidTransforms['t']
    sMidEndTransforms = rig.getTransforms (sMidEndCluster[1],attrType='rp')
    sMidEndPos = sMidEndTransforms['t']
    sMidStartTransforms = rig.getTransforms (sMidStartCluster[1],attrType='rp')
    sMidStartPos = sMidStartTransforms['t']
    # parent clusterhandles to transform with the same rotate pivot
    sMidStartClusterOffset = mc.createNode ('transform',n=sCurve+'MidStartCluster_Offset')
    mc.move (sMidStartPos[0],sMidStartPos[1],sMidStartPos[2],sMidStartClusterOffset)
    mc.makeIdentity(sMidStartClusterOffset,apply=True, translate=True, rotate=True, scale=True )
    sMidClusterOffset = mc.createNode ('transform',n=sCurve+'MidCluster_Offset')
    mc.move (sMidPos[0],sMidPos[1],sMidPos[2],sMidClusterOffset)
    mc.makeIdentity(sMidClusterOffset,apply=True, translate=True, rotate=True, scale=True ) 
    sMidEndClusterOffset = mc.createNode ('transform',n=sCurve+'MidEndCluster_Offset')         
    mc.move (sMidEndPos[0],sMidEndPos[1],sMidEndPos[2],sMidEndClusterOffset)
    mc.makeIdentity(sMidEndClusterOffset,apply=True, translate=True, rotate=True, scale=True )
                                              
    mc.parent (sMidStartCluster[1], sMidStartClusterOffset)
    mc.parent (sMidCluster[1], sMidClusterOffset)
    mc.parent (sMidEndCluster[1], sMidEndClusterOffset)
    mc.parent (sMidStartClusterOffset,sBaseParent)
    mc.parent (sMidClusterOffset,sBaseParent)
    mc.parent (sMidEndClusterOffset,sBaseParent)
    #Create Mid Ctrl
    sMidCtrl = rig.createCtrl(ctrl=sCurveName+'Mid_ctrl', ctrlType=12, pos=sMidPos, rot=[0,0,0], scale=[fCtrlScale,fCtrlScale,fCtrlScale], parent=sCtrlParent,iStack=iStackValue,colour=6)      
    mc.pointConstraint (sMidCtrl[1], sMidClusterOffset,mo=True)
    mc.pointConstraint (sMidCtrl[0], sMidCluster[1],mo=True)       
    sMidRefNull = mc.createNode ('transform',n=sCurveName+'Mid_refNull', p=sMidCtrl[1])
    mc.parentConstraint (sMidCtrl[0], sMidRefNull)   
    mc.pointConstraint (sStartCluster[1],sEndCluster[1], sMidCtrl[1], mo=bMo)            
    ctrlDict['MidCluster'] = sMidCluster
    ctrlDict['MidCtrl'] = sMidCtrl                  
    rig.lockAndHideAttr(sMidCtrl[0], ['sx','sy','sz','visibility'])
    if bDetailCtrl == True:        
        #Mid Start Ctrl
        sMidStartCtrl = rig.createCtrl(ctrl=sCurveName+'MidStart_ctrl', ctrlType=12, pos=sMidStartPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)         
        mc.pointConstraint (sStartCluster[1],sMidCtrl[1], sMidStartCtrl[1], mo=bMo)
        mc.pointConstraint (sStartCluster[1],sMidCtrl[0], sCurveName+'MidStartStack1_offset', mo=bMo)       
        mc.pointConstraint (sMidStartCtrl[1], sMidStartClusterOffset)
        mc.pointConstraint (sMidStartCtrl[0], sMidStartCluster[1])
        ctrlDict['MidStartCluster'] = sMidStartCluster
        ctrlDict['MidStartCtrl'] = sMidStartCtrl                           
        #Mid End Ctrl
        sMidEndCtrl = rig.createCtrl(ctrl=sCurveName+'MidEnd_ctrl', ctrlType=12, pos=sMidEndPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)                      
        mc.pointConstraint (sEndCluster[1],sMidCtrl[1], sMidEndCtrl[1], mo=bMo)
        mc.pointConstraint (sEndCluster[1],sMidCtrl[0], sCurveName+'MidEndStack1_offset', mo=bMo)  
        mc.pointConstraint (sMidEndCtrl[1], sMidEndClusterOffset)
        mc.pointConstraint (sMidEndCtrl[0], sMidEndCluster[1])                                    
        ctrlDict['MidEndCluster'] = sMidEndCluster
        ctrlDict['MidEndCtrl'] = sMidEndCtrl
        if bExtraCtrl == True:             
            sExtraStartACtrl = rig.createCtrl(ctrl=sCurveName+'ExtraStartA_ctrl', ctrlType=12, pos=sExtraStartAPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)   
            mc.pointConstraint (sStartCluster[1], sMidStartCtrl[1],sExtraStartACtrl[1], mo=bMo)  
            mc.pointConstraint (sStartCluster[1], sMidStartCtrl[0], sCurveName+'ExtraStartAStack1_offset', mo=bMo)             
            mc.pointConstraint (sExtraStartACtrl[1], sExtraStartAClusterOffset)
            mc.pointConstraint (sExtraStartACtrl[0], sExtraStartACluster[1])
            sExtraStartBCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraStartB_ctrl', ctrlType=12, pos=sExtraStartBPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sMidCtrl[1], sMidStartCtrl[1],sExtraStartBCtrl[1], mo=bMo)  
            mc.pointConstraint (sMidCtrl[0], sMidStartCtrl[0], sCurveName+'ExtraStartBStack1_offset', mo=bMo)                
            mc.pointConstraint (sExtraStartBCtrl[1], sExtraStartBClusterOffset)
            mc.pointConstraint (sExtraStartBCtrl[0], sExtraStartBCluster[1])        
            sExtraEndACtrl = rig.createCtrl(ctrl=sCurveName+'ExtraEndA_ctrl', ctrlType=12, pos=sExtraEndAPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sEndCluster[1], sMidEndCtrl[1],sExtraEndACtrl[1], mo=bMo)  
            mc.pointConstraint (sEndCluster[1], sMidEndCtrl[0], sCurveName+'ExtraEndAStack1_offset', mo=bMo)              
            mc.pointConstraint (sExtraEndACtrl[1], sExtraEndAClusterOffset)
            mc.pointConstraint (sExtraEndACtrl[0], sExtraEndACluster[1])
            sExtraEndBCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraEndB_ctrl', ctrlType=12, pos=sExtraEndBPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sMidCtrl[1], sMidEndCtrl[1],sExtraEndBCtrl[1], mo=bMo)  
            mc.pointConstraint (sMidCtrl[0], sMidEndCtrl[0], sCurveName+'ExtraEndBStack1_offset', mo=bMo)               
            mc.pointConstraint (sExtraEndBCtrl[1], sExtraEndBClusterOffset)
            mc.pointConstraint (sExtraEndBCtrl[0], sExtraEndBCluster[1]) 
            sExtraStartCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraStart_ctrl', ctrlType=12, pos=sExtraStartPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)
            mc.pointConstraint (sStartCluster[1], sExtraStartACtrl[1],sExtraStartCtrl[1], mo=bMo)  
            mc.pointConstraint (sStartCluster[1], sExtraStartACtrl[0], sCurveName+'ExtraStartStack1_offset', mo=bMo)            
            mc.pointConstraint (sExtraStartCtrl[1], sExtraStartClusterOffset)
            mc.pointConstraint (sExtraStartCtrl[0], sExtraStartCluster[1])
            sExtraEndCtrl = rig.createCtrl(ctrl=sCurveName+'ExtraEnd_ctrl', ctrlType=12, pos=sExtraEndPos, rot=[0,0,0], scale=[fCtrlScale/2.0,fCtrlScale/2.0,fCtrlScale/2.0], parent=sCtrlParent, iStack=iStackValue)     
            mc.pointConstraint (sEndCluster[1], sExtraEndACtrl[1],sExtraEndCtrl[1], mo=bMo)  
            mc.pointConstraint (sEndCluster[1], sExtraEndACtrl[0], sCurveName+'ExtraEndStack1_offset', mo=bMo)                  
            mc.pointConstraint (sExtraEndCtrl[1], sExtraEndClusterOffset)
            mc.pointConstraint (sExtraEndCtrl[0], sExtraEndCluster[1])
    return (ctrlDict)
