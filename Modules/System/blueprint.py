import os
import naming as n
reload(n)
import maya.cmds as mc
import System.utils as utils
reload(utils)


class Blueprint:
	def __init__(self, sModuleName, sName, aJointInfo):
		# module namespace name initialized
		self.moduleName = sModuleName
		self.userSpecifiedName = sName

		self.moduleNamespace = self.moduleName + '__' + self.userSpecifiedName
		self.containerName = self.moduleNamespace + ":module_container"

		self.jointInfo = aJointInfo			# list of touples [('jointName', [iX,iY,iZ]), ] 


		print 'init module namespace: ', self.moduleNamespace

	# Methods intended for overriding by derived classes
	def install_custom(self, joints):
		print "install_custom() isn't implemented"


	def lockPhase1(self):
		# gather and return all required information from this modules control object
		# jointPositions = list of joint positions from the root down the hierarchy
		# jointOrientations = list of orientations or a list of axis information
		#			# these are passed as a touple: (orientations,None) or (None, axisInfo)
		# jointRotationOrder = list of joint rotation order (intger values gathered with getAttr)
		# jointPreferredAngles = a list of jiont preferred angles, optional (can pass None)
		# hookObject = self.findHookObjectForLock()
		# rootTransform = a bool, either True or False. True = T,R,S on root joint. False = R only
		# 
		# moduleInfo = (jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)
		# return moduleInfo

		return None

	# Baseclass Methods
	def install(self):
		print '\n== MODULE install class {} using namespace {}'.format(self.moduleName, self.moduleNamespace)
		# check if one already exists and increment the index if it does
		mc.namespace(setNamespace=':')
		mc.namespace(add=self.moduleNamespace)

		self.jointsGrp = mc.group(em=True, n=self.moduleNamespace+':joints_grp')
		self.hierarchyRepGrp = mc.group(em=True, n=self.moduleNamespace+':hierarchyRep_grp')
		self.orientationControlGrp = mc.group(em=True, n=self.moduleNamespace+':orientationControls_grp')
		self.moduleGrp = mc.group([self.jointsGrp, self.hierarchyRepGrp], n=self.moduleNamespace+':module_grp')


		mc.container(n=self.containerName, addNode=[self.moduleGrp], includeHierarchyBelow=True)

		mc.select(cl=True)

		# create the joints in self.jointInfo
		index = 0
		joints = []
		for joint in self.jointInfo:
			jointName = joint[0]
			jointPos = joint[1]
			parentJoint = ''
			if index > 0:			# in case this is not the root joint, select the parent joint name
				parentJoint = self.moduleNamespace+':'+self.jointInfo[index-1][0]
				mc.select(parentJoint, r=True)
			# create the joint and add it to the container
			jointName_full = mc.joint(n=self.moduleNamespace+':'+jointName, p=jointPos)
			joints.append(jointName_full)
			mc.setAttr(jointName_full+'.v', 0)
			
			utils.addNodeToContainer(self.containerName, jointName_full, ihb=True)
			mc.container(self.containerName, edit=True, publishAndBind=[jointName_full+'.rotate', jointName+'_R'])
			mc.container(self.containerName, edit=True, publishAndBind=[jointName_full+'.rotateOrder', jointName+'_RO'])

			# orient the parent joint to the newly created joint
			if index > 0:
				mc.joint(parentJoint, edit=True, orientJoint='xyz', sao='yup')


			index += 1
		mc.parent(joints[0], self.jointsGrp, absolute=True)

		# prepare the parent translation control group 
		self.initializeModuleTransforn(self.jointInfo[0][1])

		# create translation controls for the joints
		translationControls = []
		for joint in joints:
			translationControls.append(self.createTranslationControlAtJoint(joint))

		rootJoint_pCon = mc.pointConstraint(translationControls[0], joints[0], mo=False, n=joints[0]+'_pCon')
		utils.addNodeToContainer(self.containerName, rootJoint_pCon)

		# setup stretchy joint segement
		for index in range(len(joints) - 1):
			self.setupStretchyJointSegment(joints[index], joints[index+1])

		self.install_custom(joints)

		utils.forceSceneUpdate()

		# lock the container
		mc.lockNode(self.containerName, lock=True, lockUnpublished=True)


	def createTranslationControlAtJoint(self, joint):
		# import the control sphere
		posControlFile = os.environ['RIGGING_TOOL_ROOT'] + '/ControlObjects/Blueprint/translation_control.ma'
		mc.file(posControlFile, i=True)
		# go through and rename all the nodes based on the joint
		container = mc.rename('translation_control_container', joint+'_translation_control_container')
		utils.addNodeToContainer(self.containerName, container)	# add it all to this instance's container
		for node in mc.container(container, q=True, nodeList=True):
			mc.rename(node, joint+'_'+node, ignoreShape=True)
		# position the control
		control = joint+'_translation_control'
		# parent it to the initialized transform control group
		mc.parent(control, self.moduleTransform, absolute=True)
		# match the control to the joint poision
		jointPos = mc.xform(joint, q=True, ws=True, t=True)
		mc.xform(control, ws=True, absolute=True, t=jointPos)
		# publish attributes
		niceName = utils.stripLeadingNamespace(joint)[1]
		attrName = niceName + '_T'

		mc.container(container, edit=True, publishAndBind=[control+'.t', attrName])
		mc.container(self.containerName, edit=True, publishAndBind=[container+'.'+attrName, attrName])

		return control

	def getTranslationControl(self, jointName):
		return jointName + '_translation_control'

	def setupStretchyJointSegment(self, parentJoint, childJoint):
		# setup 2 joints to have an IK and stretchy joint in the segment
		parentTranslationControl = self.getTranslationControl(parentJoint)
		childTranslationControl = self.getTranslationControl(childJoint)

		pvLoc = mc.spaceLocator(n=parentTranslationControl+'pvLoc')[0]
		pvLocGrp = mc.group(pvLoc, n=pvLoc+'_pConGrp')
		mc.parent(pvLocGrp, self.moduleGrp, absolute=True)
		parentConst = mc.parentConstraint(parentTranslationControl, pvLocGrp, mo=False)[0]
		mc.setAttr(pvLoc+'.v', 0)
		mc.setAttr(pvLoc+'.ty', -0.5)



		dIkNodes = utils.basicStretchyIK(parentJoint, 
					childJoint, 
					sContainer=self.containerName, 
					bMinLengthLock=False, 
					poleVectorObj=pvLoc, 
					sScaleCorrectionAttr=None)

		ikHandle = dIkNodes['ikHandle']
		rootLoc = dIkNodes['rootLoc']
		endLoc = dIkNodes['endLoc']

		child_pCon = mc.pointConstraint(childTranslationControl, endLoc, mo=False, n=endLoc+'_pCon')[0]

		utils.addNodeToContainer(self.containerName, [pvLocGrp,child_pCon], ihb=True)

		for node in [ikHandle, rootLoc, endLoc]:
			mc.parent(node, self.jointsGrp)
			mc.setAttr(node+'.v', 0)

		self.createHierarchyRepresentation(parentJoint, childJoint)

	def createHierarchyRepresentation(self, parentJoint, childJoint):
		# run the createStretchyObject and parent to grp
		nodes = self.createStretchyObject('/ControlObjects/Blueprint/hierarchy_representation.ma',
										'hierarchy_representation_container',
										'hierarchy_representation',
										parentJoint,
										childJoint)
		constrainedGrp = nodes[2]
		mc.parent(constrainedGrp, self.hierarchyRepGrp, r=True)


	def createStretchyObject(self, objectRelativeFilePath, objectContainerName, objectName, parentJoint, childJoint):
		# import the prepared hierarchy representation geo, connect their scale and constrain to the joints
		objFile = os.environ['RIGGING_TOOL_ROOT'] +  objectRelativeFilePath
		mc.file(objFile, i=True)

		objContainer = mc.rename(objectContainerName, parentJoint+'_'+objectContainerName)
		for node in mc.container(objContainer, q=True, nodeList=True):
			mc.rename(node, parentJoint+'_'+node, ignoreShape=True)
		obj = parentJoint+'_'+objectName

		constrainedGrp = mc.group(em=True, n=obj+'_parentConstraint_grp')
		mc.parent(obj, constrainedGrp, absolute=True)

		pCon = mc.parentConstraint(parentJoint, constrainedGrp, mo=False)[0]

		mc.connectAttr(childJoint+'.tx', constrainedGrp+'.sx')
		sCon = mc.scaleConstraint(self.moduleTransform, constrainedGrp, skip=['x'], mo=False)[0]


		utils.addNodeToContainer(objContainer, [constrainedGrp, pCon, sCon], ihb=True)
		utils.addNodeToContainer(self.containerName, objContainer)

		return(objContainer, obj, constrainedGrp)

	def initializeModuleTransforn(self, rootPos):
		controlGrpFile = os.environ['RIGGING_TOOL_ROOT']+'/ControlObjects/Blueprint/controlGroup_control.ma'
		mc.file(controlGrpFile, i=True)

		self.moduleTransform = mc.rename('controlGroup_control', self.moduleNamespace+':module_transform')
		mc.xform(self.moduleTransform, ws=True, absolute=True, t=rootPos)
		utils.addNodeToContainer(self.containerName, self.moduleTransform, ihb=True)

		# setup global scaling
		mc.connectAttr(self.moduleTransform+'.sy', self.moduleTransform+'.sx')
		mc.connectAttr(self.moduleTransform+'.sy', self.moduleTransform+'.sz')

		mc.aliasAttr('globalScale', self.moduleTransform+'.sy')

		mc.container(self.containerName, e=True, publishAndBind=[self.moduleTransform+'.translate', 'module_transform_T'])
		mc.container(self.containerName, e=True, publishAndBind=[self.moduleTransform+'.rotate', 'module_transform_R'])
		mc.container(self.containerName, e=True, publishAndBind=[self.moduleTransform+'.globalScale', 'module_transform_globalScale'])

	def deleteHierarchyRepresentation(self, parentJoint):
		hierarchyContainer = parentJoint + '_hierarchy_representation_container'
		mc.delete(hierarchyContainer)

	def createOrientationControl(self, parentJoint, childJoint):
		self.deleteHierarchyRepresentation(parentJoint)
		nodes = self.createStretchyObject('/ControlObjects/Blueprint/orientation_control.ma',
											'orientation_control_container',
											'orientation_control',
											parentJoint,
											childJoint)
		orientationContainer = nodes[0]
		orientationControl = nodes[1]
		constrainedGrp = nodes[2]

		mc.parent(constrainedGrp, self.orientationControlGrp, relative=True)
		parentJoint_noNs = utils.stripAllNamespaces(parentJoint)[1]
		attrName = parentJoint_noNs + '_orientation'
		#childJoint_noNs= utils.stripAllNamespaces(child)[1]
		utils.addNodeToContainer(self.containerName, self.orientationControlGrp, ihb=True)
		mc.container(orientationContainer, e=True, publishAndBind=[orientationControl+'.rx', attrName])
		mc.container(self.containerName, e=True, publishAndBind=[orientationContainer+'.'+attrName, attrName])

		return orientationControl

	def getOrientationControl(self, sJoint):
		# based on the orientation control file used in this system 
		# concatinate jiont with "_orientation_control
		return sJoint+'_orientation_control'

	def getJoints(self):
		# returns all the joints in the module with namespace
		jointNs = self.moduleNamespace + ':'
		joints = []

		for ji in self.jointInfo:
			joints.append(jointNs + ji[0])

		return joints

	def getJointOrientation(self, sJoint, sCleanParent):
		# clean out the joints orientation and return it with a duplicated joint using the adjusted orientation
		newCleanParent = mc.duplicate(sJoint, parentOnly=True)[0]
		# this won't work if the joint is ever not a child of cleanparent, 
		# parenting will error due to the locked state of the whole blueprint
		#if not sCleanParent in mc.listRelatives(newCleanParent, parent=True):
		#	mc.parent(newCleanParent, sCleanParent, absolute=True)

		# freeze rotation on new duplicate of sJoint 
		# so that any world orientation gets saved in it's jointOrient
		mc.makeIdentity(newCleanParent, apply=True, r=True, s=False, t=False)
		# set it's rotateX to that of the orientationControl
		mc.setAttr(newCleanParent+'.rx', mc.getAttr(self.getOrientationControl(sJoint)+'.rx'))
		# freeze again to bake the orientationControl RX in to the jointOrientX
		mc.makeIdentity(newCleanParent, apply=True, r=True, s=False, t=False)

		oX = mc.getAttr(newCleanParent+'.jointOrientX')
		oY = mc.getAttr(newCleanParent+'.jointOrientY')
		oZ = mc.getAttr(newCleanParent+'.jointOrientZ')

		orientationVal = (oX, oY, oZ)

		return (orientationVal, newCleanParent)

	def lockPhase2(self, dModuleInfo):
		jointPositions = dModuleInfo['jointPositions']
		numJoints = len(jointPositions)
		# divide the dictionary module info we got from phase1 into variables 
		jointOrientations = dModuleInfo['jointOrientations']
		orientWithAxis = False
		pureOrientation = False
		if jointOrientations[0] == None:
			orientWithAxis = True
			jointOrientations = jointOrientations[1]
		else:
			pureOrientation = True
			jointOrientations = jointOrientations[0]
		numOrientations = len(jointOrientations)

		jointRotationOrder = dModuleInfo['jointRotationOrder']
		numRotationOrder = len(jointRotationOrder)

		jointPreferredAngles = dModuleInfo['jointPreferredAngles']
		numPreferredAngles = 0
		if jointPreferredAngles != None:
			numPreferredAngles = len(jointPreferredAngles)

		hookObject = dModuleInfo['hookObject']
		rootTransform = dModuleInfo['rootTransform']

		# DELETE the blueprint controls
		mc.lockNode(self.containerName, lock=False, lockUnpublished=False)
		mc.delete(self.containerName)
		mc.namespace(setNamespace=':')

		#
		print '- Gathered from lockPhase1:\n', dModuleInfo.items()
		#
		# RE-BUILD SKELETON BASED ON dModuleInfo
		jointRadius = 1
		if numJoints == 1:
			jointRadius = 1.5
		newJoints = []
		# create the joints
		for i in range(numJoints):
			newJoint = ""
			mc.select(cl=True)
			if orientWithAxis:	
				newJoint = mc.joint(n=self.moduleNamespace+':bp_'+self.jointInfo[i][0], 
									p=jointPositions[i], 
									rotationOrder='xyz',
									radius=jointRadius)		
				if i != 0:		# i=0 is root joint. So this is for children joints
								# orient the parent joint to the newly created joint
					mc.parent(newJoint, newJoints[i-1], absolute=True)
					offsetIndex = i - 1
					if offsetIndex < numOrientations:
						mc.joint(newJoints[offsetIndex], e=True, 
									oj=jointOrientations[offsetIndex][0],
									sao=jointOrientations[offsetIndex][1])
						mc.makeIdentity(newJoint, rotate=True, apply=True)
			if pureOrientation:
				if i != 0:
					mc.select(newJoints[i-1])
					jointOrientation = [0.0, 0.0, 0.0]
				if i < numOrientations:
					jointOrientation = [ jointOrientations[i][0], jointOrientations[i][1], jointOrientations[i][2]  ]
				newJoint = mc.joint(n=self.moduleNamespace+':bp_'+self.jointInfo[i][0], 
									p=jointPositions[i], 
									orientation=jointOrientation,
									rotationOrder='xyz',
									radius=jointRadius)
			newJoints.append(newJoint)

			if i < numRotationOrder:
				mc.setAttr(newJoint+'.rotateOrder', int(jointRotationOrder[i]))

			if i < numPreferredAngles:
				mc.setAttr(newJoint+'.preferredAngleX', jointPreferredAngles[i][0])
				mc.setAttr(newJoint+'.preferredAngleY', jointPreferredAngles[i][1])
				mc.setAttr(newJoint+'.preferredAngleZ', jointPreferredAngles[i][2])

			mc.setAttr(newJoint+'.segmentScaleCompensate', 0)

		bpGrp = mc.group(em=True, n=self.moduleNamespace+':bp_joints_grp')
		mc.parent(newJoints[0], bpGrp, absolute=True)
		creationPoseGrpNodes = []
		creationPoseGrpNodes = mc.duplicate(bpGrp, n=self.moduleNamespace+':creationPose_joint_grp', renameChildren=True)
		creationPoseGrp = creationPoseGrpNodes[0]

		creationPoseGrpNodes.pop(0)
		for i, node in enumerate(creationPoseGrpNodes):
			fixName = mc.rename(node, self.moduleNamespace + ':creationPose_' + self.jointInfo[i][0])
			mc.setAttr(fixName+'.v', 0)

		# SYSTEM setup for tramsformation blending
		# Creation Pose Weight network
		mc.select(bpGrp, replace=True)
		mc.addAttr(ln='controlModulesInstalled', at='bool', dv=0, k=False)
		settingsLoc = mc.spaceLocator(n=self.moduleNamespace+':SETTINGS')[0]
		mc.setAttr(settingsLoc+'.v', 0)
		mc.select(settingsLoc, replace=True)
		mc.addAttr(ln='activeModule', at='enum', en='None:', k=False)
		mc.addAttr(ln='creationPoseWeight', at='float', dv=1, k=False)

		# add and multiply node creations
		utilityNodes = []
		for i, joint in enumerate(newJoints):
			if i < (numJoints - 1) or numJoints == 1:
				# initial bp dummy rotation multiply
				# setup first addNode and dummy multiplyNode for each joint but the last 
				# nil rotations go into the addnode input, and that maps to it's repective joint rotate
				addNode = mc.shadingNode('plusMinusAverage', n=joint+'_addRotations', asUtility=True)
				mc.connectAttr(addNode+'.output3D', joint+'.rotate', f=True)
				utilityNodes.append(addNode)
				dummyRotationMultiply = mc.shadingNode('multiplyDivide', n=joint+'_multiplyDummyRotation', asUtility=True)
				mc.connectAttr(dummyRotationMultiply+'.output', addNode+'.input3D[0]', f=True)
				utilityNodes.append(dummyRotationMultiply)
			if i > 0:
				# creattion pose weight multiplies the otiginalTx value of all the joints but the first
				# that pipes into an addTxNode that connects to the respective joints tX
				originalTx = mc.getAttr(joint+'.tx')
				addTxNode = mc.shadingNode('plusMinusAverage', n=joint+'_addTx', asUtility=True)
				mc.connectAttr(addTxNode+'.output1D', joint+'.tx', f=True)
				utilityNodes.append(addTxNode)
				originalTxMultiply = mc.shadingNode('multiplyDivide', n=joint+'_multiplyOiginalTx', asUtility=True)
				mc.setAttr(originalTxMultiply+'.input1X', originalTx, lock=True)
				mc.connectAttr(settingsLoc+'.creationPoseWeight', originalTxMultiply+'.input2X', f=True)
				mc.connectAttr(originalTxMultiply+'.outputX', addTxNode+'.input1D[0]', f=True)
				utilityNodes.append(originalTxMultiply)
			else:
				if rootTransform:
					# connect creationPoseWeight to the translate
					originalTranslates = mc.getAttr(joint+'.translate')[0]
					addTranslateNode = mc.shadingNode('plusMinusAverage', n=joint+'_addOriginalTranslate', asUtility=True)
					mc.connectAttr(addTranslateNode+'.output3D', joint+'.translate', f=True)
					utilityNodes.append(addTranslateNode)

					originalTranslateMultiply = mc.shadingNode('multiplyDivide', n=joint+'_multiplyOriginalTranslate', asUtility=True)
					mc.setAttr(originalTranslateMultiply+'.input1', originalTranslates[0],originalTranslates[1],originalTranslates[2], type='double3' )
					for axis in ['X', 'Y', 'Z']:
						mc.connectAttr(settingsLoc+'.creationPoseWeight', originalTranslateMultiply+'.input2'+axis)
					mc.connectAttr(originalTranslateMultiply+'.output', addTranslateNode+'.input3D[0]', f=True)
					utilityNodes.append(originalTranslateMultiply)

					# scale
					originalScales = mc.getAttr(joint+'.scale')[0]
					addScaleNode = mc.shadingNode('plusMinusAverage', n=joint+'_addOriginalScale', asUtility=True)
					mc.connectAttr(addScaleNode+'.output3D', joint+'.scale', f=True)
					utilityNodes.append(addScaleNode)

					originalScaleMultiply = mc.shadingNode('multiplyDivide', n=joint+'_multiplyOriginalScale', asUtility=True)
					mc.setAttr(originalScaleMultiply+'.input1', originalScales[0],originalScales[1],originalScales[2], type='double3' )
					for axis in ['X', 'Y', 'Z']:
						mc.connectAttr(settingsLoc+'.creationPoseWeight', originalScaleMultiply+'.input2'+axis)
					mc.connectAttr(originalScaleMultiply+'.output', addScaleNode+'.input3D[0]', f=True)
					utilityNodes.append(originalScaleMultiply)

		bpNodes = utilityNodes
		bpNodes.append(bpGrp)
		bpNodes.append(creationPoseGrp)

		bpContainer = mc.container(n=self.moduleNamespace+':bp_container')
		utils.addNodeToContainer(bpContainer, bpNodes, ihb=True)

		moduleGrp = mc.group(em=True, name=self.moduleNamespace+':module_grp')
		mc.parent(settingsLoc, moduleGrp, absolute=True)

		# temp
		for group in [bpGrp, creationPoseGrp]:
			mc.parent(group, moduleGrp, absolute=True)
		moduleContainer = mc.container(n=self.moduleNamespace+':module_container')
		utils.addNodeToContainer(moduleContainer, [moduleGrp, settingsLoc, bpContainer], includeShapes=True)

		mc.container(moduleContainer, e=True, publishAndBind=[settingsLoc+'.activeModule', 'activeModule'])
		mc.container(moduleContainer, e=True, publishAndBind=[settingsLoc+'.creationPoseWeight', 'creationPoseWeight'])

		mc.lockNode(moduleContainer, lock=True, lockUnpublished=True)