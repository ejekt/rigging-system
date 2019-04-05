# single joint segment
import maya.cmds as mc
import os

import System.blueprint as bp
reload(bp)

CLASS_NAME = 'SingleJointSegment'

TITLE = 'Single Joint Segment'
DESCRIPTION = 'Creates 2 joints, with control for 1st joint"s orientation and rotation order. Ideal for clavicle and shoulder'
ICON = os.environ["RIGGING_TOOL_ROOT"] + '/Icons/_singleJointSeg.xpm'


class SingleJointSegment(bp.Blueprint):
	def __init__(self, CLASS_NAME, sUserSpecifiedName, sHookObj, *args):
		''' blueprint module of a single joint segment pointng down X.
		It includes a translation control per joint, a stretchy IK and 
		with an orientation control between them.

	    @param sUserSpecifiedName 	- name says it all
	    @param sHookObj 				- string - name of the object to hook to
    	@procedure
		'''
		super(SingleJointSegment, self).__init__(CLASS_NAME, sUserSpecifiedName, sHookObj, *args)

		self.jointInfo = [['root_joint', [0.0,0.0,0.0]], ['end_joint',[4.0,0.0,0.0]]]

		#print sUserSpecifiedName

		# bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo, hookObj)


	def install_custom(self, joints):
		self.orientationControl = self.createOrientationControl(joints[0], joints[1])


	def Ui_custom(self):
		''' This module builds a rotation control and has a custom UI element for that.
		'''
		mc.setParent(self.parentColumnLayout)
		joints = self.getJoints()
		self.createRotationOrderUiControl(joints[0])


	def mirror_custom(self, sOriginalModule):
		''' when mirroring this module we also want to match the orientationControl RX to
		the mirrored module's orientation control.
		'''
		jointName = self.jointInfo[0][0]
		originalJoint = sOriginalModule + ':' + jointName
		newJoint = self.moduleNamespace + ':' + jointName

		originalOrientationControl = self.getOrientationControl(originalJoint)
		newOrientationControl = self.getOrientationControl(newJoint)

		mc.setAttr(newOrientationControl+'.rx', mc.getAttr(originalOrientationControl+'.rx'))


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

		joints = self.getJoints()

		for j in joints:
			jointPositions.append(mc.xform(j, q=True, ws=True, t=True))

		cleanParent = self.moduleNamespace + ':joints_grp'
		# get the orientation values and the clean parent of the joint we're getting the values for.
		orientationInfo = self.orientationControlledJoint_getOrientation(joints[0], cleanParent)

		mc.delete(orientationInfo[1])
		jointOrientationValues.append(orientationInfo[0])
		jointOrientations = (jointOrientationValues, None)

		jointRotationOrders.append(mc.getAttr(joints[0]+'.rotateOrder'))

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

