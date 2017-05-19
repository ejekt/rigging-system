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

		mc.container(n=self.containerName, addNode=[self.moduleGrp], ihb=True)

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
			mc.container(self.containerName, edit=True, addNode=jointName_full)
			mc.container(self.containerName, edit=True, publishAndBind=[jointName_full+'.rotate', jointName+'_R'])
			mc.container(self.containerName, edit=True, publishAndBind=[jointName_full+'.rotateOrder', jointName+'_rotateOrder'])

			# orient the parent joint to the newly created joint
			if index > 0:
				mc.joint(parentJoint, edit=True, orientJoint='xyz', sao='yup')


			index += 1
		mc.parent(joints[0], self.jointsGrp, absolute=True)
		mc.lockNode(self.containerName, lock=True, lockUnpublished=True)
