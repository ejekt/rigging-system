import maya.cmds as mc
import System.blueprint as bp 
import System.utils as utils
import os

CLASS_NAME = 'SingleOrientableJoint'

TITLE = 'Single Orientable Joint'
DESCRIPTION = 'Creates a single joint with control for position and orientation. Once created (locked) the joint can only rotate. Ideal use: Wrist'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_singleOrientable.xpm'

class SingleOrientableJoint(bp.Blueprint):

	class_name = CLASS_NAME
 
	def __init__(self, sUserSpecifiedName, sHookObj, *args):
		#! thumb init doesn't work unless Finer.__init__ has a super(self)
		#! but then Finger won't work
		jointInfo = [ ['joint', [0.0,0.0,0.0]] ]
		
		super(SingleOrientableJoint, self).__init__(self.class_name, sUserSpecifiedName, jointInfo, sHookObj, *args)


	def install_custom(self, joints):
		self.createSingleJointOrientationControlAtJoint(joints[0])


	def mirror_custom(self, originalModule):
		jointName = self.jointInfo[0][0]
		originalJoint = originalModule + ':' + jointName
		newJoint = self.moduleNamespace + ':' + jointName

		originalOrientationControl = self.getSingleJointOrientationControl(originalJoint)
		newOrientationControl = self.getSingleJointOrientationControl(newJoint)

		oldRotation = mc.getAttr(originalOrientationControl+'.rotate')[0]
		mc.setAttr(newOrientationControl+'.rotate', oldRotation[0], oldRotation[2], oldRotation[2], type='double3')


	def Ui_custom(self):
		joints = self.getJoints()
		self.createRotationOrderUiControl(joints[0])



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

		jointPositions = []
		jointOrientationValues = []
		jointOrientations = []
		jointRotationOrders = []

		joint = self.getJoints()[0]

		jointPositions.append(mc.xform(joint, q=True, ws=True, t=True))
		jointOrientationControl = self.getSingleJointOrientationControl(joint)
		jointOrientationValues.append(mc.xform(jointOrientationControl, q=True, ws=True, rotation=True))
		jointOrientations = (jointOrientationValues, None)

		jointRotationOrders.append(mc.getAttr(joint+'.rotateOrder'))

		jointPreferredAngles = None
		hookObject = self.findHookObjectForLock()
		rootTransform = False

		# moduleInfo = jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)
		dModuleInfo = {}
		dModuleInfo['jointPositions'] = jointPositions					# [(xyz position)]
		dModuleInfo['jointOrientations'] = jointOrientations  			# [([xyz orientation], None)]
		dModuleInfo['jointRotationOrders'] = jointRotationOrders		# .rotateOrder value
		dModuleInfo['jointPreferredAngles'] = jointPreferredAngles		# None
		dModuleInfo['hookObject'] = hookObject 							# None
		dModuleInfo['rootTransform'] = rootTransform					# False

		return dModuleInfo

