import os
import naming as n
reload(n)
import maya.cmds as mc
import System.utils as utils
reload(utils)

CLASS_NAME = 'ModuleA'

TITLE = 'Module A'
DESCRIPTION = 'Test desc for module A'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_hand.xpm'

#cNamer = n.Name(type='blueprint', mod=CLASS_NAME)

class ModuleA:
	def __init__(self, sName):
		# module namespace name initialized
		self.moduleName = CLASS_NAME
		self.userSpecifiedName = sName

		self.moduleNamespace = self.moduleName + '__' + self.userSpecifiedName
		self.containerName = self.moduleNamespace + ":module_container"

		self.jointInfo = [['root_joint', [0.0,0.0,0.0]], ['end_joint',[4.0,0.0,0.0]]]

		print 'init module namespace: ', self.moduleNamespace

	def install(self):
		print '\n== MODULE install class {} using namespace {}'.format(CLASS_NAME, self.moduleNamespace)
		# check if one already exists and increment the index if it does
		mc.namespace(setNamespace=':')
		mc.namespace(add=self.moduleNamespace)

		self.jointsGrp = mc.group(em=True, n=self.moduleNamespace+':joints_grp')
		self.moduleGrp = mc.group(self.jointsGrp, n=self.moduleNamespace+':module_grp')

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
			
			utils.addNodeToContainer(self.containerName, jointName_full, ihb=True)
			mc.container(self.containerName, edit=True, publishAndBind=[jointName_full+'.rotate', jointName+'_R'])
			mc.container(self.containerName, edit=True, publishAndBind=[jointName_full+'.rotateOrder', jointName+'_RO'])

			# orient the parent joint to the newly created joint
			if index > 0:
				mc.joint(parentJoint, edit=True, orientJoint='xyz', sao='yup')


			index += 1
		mc.parent(joints[0], self.jointsGrp, absolute=True)

		# create translation controls for the joints
		translationControls = []
		for joint in joints:
			translationControls.append(self.createTranslationControlAtJoint(joint))

		rootJoint_pCon = mc.pointConstraint(translationControls[0], joints[0], mo=False, n=joints[0]+'_pCon')
		utils.addNodeToContainer(self.containerName, rootJoint_pCon)

		# setup stretchy joint segement
		for index in range(len(joints) - 1):
			self.setupStretchyJointSegment(joints[index], joints[index+1])

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
