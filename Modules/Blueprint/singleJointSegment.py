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
	def __init__(self, sUserSpecifiedName, hookObj):

		jointInfo = [['root_joint', [0.0,0.0,0.0]], ['end_joint',[4.0,0.0,0.0]]]

		#print sUserSpecifiedName

		bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo, hookObj)

	def install_custom(self, joints):
		self.orientationControl = self.createOrientationControl(joints[0], joints[1])

	def Ui_custom(self):
		mc.setParent(self.parentColumnLayout)
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
		jointRotationOrder = []

		joints = self.getJoints()

		for j in joints:
			jointPositions.append(mc.xform(j, q=True, ws=True, t=True))

		orientationInfo = self.getJointOrientation(joints[0], self.moduleNamespace+':joints_grp')
		#print 'orientationInfo ', orientationInfo
		mc.delete(orientationInfo[1])
		jointOrientationValues.append(orientationInfo[0])
		jointOrientations = (jointOrientationValues, None)

		jointRotationOrder.append(mc.getAttr(joints[0]+'.rotateOrder'))

		jointPreferredAngles = None
		hookObject = None
		rootTransform = False

		# moduleInfo = jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)
		dModuleInfo = {}
		dModuleInfo['jointPositions'] = jointPositions					# [(xyz position)]
		dModuleInfo['jointOrientations'] = jointOrientations  			# [([xyz orientation], None)]
		dModuleInfo['jointRotationOrder'] = jointRotationOrder 			# .rotateOrder value
		dModuleInfo['jointPreferredAngles'] = jointPreferredAngles		# None
		dModuleInfo['hookObject'] = hookObject 							# None
		dModuleInfo['rootTransform'] = rootTransform					# False

		return dModuleInfo

