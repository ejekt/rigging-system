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
	def __init__(self, sUserSpecifiedName):
		
		jointInfo = [['root_joint', [0.0,0.0,0.0]], ['end_joint',[4.0,0.0,0.0]]]

		bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo)

	def install_custom(self, joints):
		self.createOrientationControl(joints[0], joints[1])
