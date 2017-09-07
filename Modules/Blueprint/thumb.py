import maya.cmds as mc
import System.blueprint as bp 
reload(bp)
import System.utils as utils
reload(utils)
import os
import Blueprint.finger as finger
reload(finger)

CLASS_NAME = 'Thumb'

TITLE = 'Thumb'
DESCRIPTION = 'Creates 4 joints, defining a thumb. Ideal use: thumb'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_thumb.xpm'

class Thumb(finger.Finger):
	def __init__(self, sUserSpecifiedName, sHookObj):
		super(finger, self).init()
		#! thumb init doesn't work unless Finer.__init__ has a super(self)
		#! but then Finger won't work
		jointInfo = [ ['root_joint', [0.0,0.0,0.0]],['knuckle_1_joint', [4.0,0.0,0.0]],
						['knuckle_2_joint', [8.0,0.0,0.0]], ['end_hoint', [12.0,0.0,0.0]] ]
		
		bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo, sHookObj)
