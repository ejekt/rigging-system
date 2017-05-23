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

		self.jointInfo = aJointInfo


		print 'init module namespace: ', self.moduleNamespace

	# Methods intended for overriding by derived classes
	def install_custom(self, joints):
		print "install_custom() isn't implemented"



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
		mc.container(orientationContainer, e=True, publishAndBind=[orientationControl+'.rx', attrName])
		mc.container(self.containerName, e=True, publishAndBind=[orientationContainer+'.'+attrName, attrName])

		return orientationControl