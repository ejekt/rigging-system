import maya.cmds as mc
import System.blueprint as bp 
reload(bp)
import System.utils as utils
reload(utils)
import os

CLASS_NAME = 'Finger'

TITLE = 'Finger'
DESCRIPTION = 'Creates 5 joints, defining a finger. Ideal use: finger'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_finger.xpm'

class Finger(bp.Blueprint):
	class_name = CLASS_NAME
	def __init__(self, sUserSpecifiedName, sHookObj):
		self.jointInfo = [ ['root_joint', [0.0,0.0,0.0]],['knuckle_1_joint', [4.0,0.0,0.0]],
						['knuckle_2_joint', [8.0,0.0,0.0]], ['knuckle_3_joint', [12.0,0.0,0.0]],
						['end_joint', [16.0,0.0,0.0]] ]
		
		super(Finger, self).__init__(self.class_name, sUserSpecifiedName, self.jointInfo, sHookObj)
		
		#bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo, sHookObj)


	def install_custom(self, joints):
		for i in range(len(joints) - 1):
			mc.setAttr(joints[i]+'.rotateOrder', 3)		#xzy
			
			# each knuckle gets a orientation representation control			
			self.createOrientationControl(joints[i], joints [i+1])

			paControl = self.createPreferredAngleRepresentation(joints[i], 
																self.getTranslationControl(joints[i]),
																bChildOrientationControl=True)
			mc.setAttr(paControl+'.axis', 3)	# set axis rotation representation to -Z

		if not self.mirrored:
			mc.setAttr(self.moduleNamespace+':module_transform.globalScale', 0.25)

	def mirror_custom(self, sOriginalModule):
		for i in range(len(self.jointInfo)-1):
			jointName = self.jointInfo[i][0]
			originalJoint = sOriginalModule+':'+jointName
			newJoint = self.moduleNamespace+':'+jointName

			originalOrientationControl = self.getOrientationControl(originalJoint)
			newOrientationControl = self.getOrientationControl(newJoint)
			mc.setAttr(newOrientationControl+'.rx', mc.getAttr(originalOrientationControl+'.rx'))

			originalPreferredAngleControl = self.getPreferredAngleControl(originalJoint)
			newPreferredAngleControl = self.getPreferredAngleControl(newJoint)
			mc.setAttr(newPreferredAngleControl+'.axis', mc.getAttr(originalPreferredAngleControl+'.axis'))	


	def Ui_custom(self):
		joints = self.getJoints()
		joints.pop()

		# fucking scriptjob silently breaks out of the code, stopping the whole method from completing

		for joint in joints:
			self.createRotationOrderUiControl(joint)

		for joint in joints:
			self.createPreferredAngleUiControl(self.getPreferredAngleControl(joint))


	def lockPhase1(self):
		# gather and return all required information from this modules control object
		# jointPositions = list of joint positions from the root down the hierarchy
		# jointOrientations = list of orientations or a list of axis information
		#			# these are passed as a touple: (orientations,None) or (None, axisInfo)
		# jointRotationOrder = list of joint rotation order (intger values gathered with getAttr)
		# jointPreferredAngles = a list of jiont preferred angles, optional (can pass None)
		# hookObject = self.findHookObjectForLock()
		# rootTransform = a bool, either True or False. True = T,R,S on root joint. False = R only
		# moduleInfo = (jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)
		# return moduleInfo

		jointPositions = []
		jointOrientationValues = []
		jointOrientations = []
		jointRotationOrders = []
		jointPreferredAngles = []

		# 
		joints = self.getJoints()

		index = 0
		cleanParent = self.moduleNamespace + ':joints_grp'
		deleteJoints = []
		for joint in joints:
			jointPositions.append(mc.xform(joint, q=True, ws=True, t=True))
			jointRotationOrders.append(mc.getAttr(joint+'.rotateOrder'))

			if index < len(joints)-1:
				# what is this?!
				orientationInfo = self.orientationControlledJoint_getOrientation(joint, cleanParent)
				jointOrientationValues.append(orientationInfo[0])
				cleanParent = orientationInfo[1]
				deleteJoints.append(cleanParent)

				jointPrefAngles = [0.0,0.0,0.0]
				axis = mc.getAttr(self.getPreferredAngleControl(joint)+'.axis')

				if axis == 0:
					jointPrefAngles[1] = 50.0
				if axis == 1:
					jointPrefAngles[1] = -50.0
				if axis == 2:
					jointPrefAngles[2] = 50.0
				if axis == 3:
					jointPrefAngles[2] = 50.0

				jointPreferredAngles.append(jointPrefAngles)
			index += 1

		jointOrientations = (jointOrientationValues, None)

		mc.delete(deleteJoints)

		hookObject = self.findHookObjectForLock()

		rootTransform = False

		# moduleInfo = jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)
		dModuleInfo = {}
		dModuleInfo['jointPositions'] = jointPositions					# [(xyz position)]
		dModuleInfo['jointOrientations'] = jointOrientations  			# [([xyz orientation], None)]
		dModuleInfo['jointRotationOrders'] = jointRotationOrders		# .rotateOrder values
		dModuleInfo['jointPreferredAngles'] = jointPreferredAngles		# None
		dModuleInfo['hookObject'] = hookObject 							# None
		dModuleInfo['rootTransform'] = rootTransform					# False

		return dModuleInfo
