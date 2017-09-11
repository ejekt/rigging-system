import maya.cmds as mc
import System.blueprint as bp 
import Blueprint.singleOrientableJoint as singleOrientableJoint
reload(singleOrientableJoint)
import System.utils as utils
import os

CLASS_NAME = 'RootTransform'

TITLE = 'Root Transform'
DESCRIPTION = 'Creates a single joint with control for position and orientation. Once created (locked) the joint can rotate, translate and scale. Ideal use: Global control'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_rootTxfrm.xpm'

class RootTransform(singleOrientableJoint.SingleOrientableJoint):

	class_name = CLASS_NAME
 
	def __init__(self, sUserSpecifiedName, sHookObj, *args):
		#! thumb init doesn't work unless Finer.__init__ has a super(self)
		#! but then Finger won't work
		jointInfo = [ ['joint', [0.0,0.0,0.0]] ]
		
		super(RootTransform, self).__init__(self.class_name, sUserSpecifiedName, jointInfo, sHookObj, *args)


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

		dModuleInfo = singleOrientableJoint.SingleOrientableJoint.lockPhase1(self)

		dModuleInfo['rootTransform'] = True

		# moduleInfo = jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)

		return dModuleInfo

