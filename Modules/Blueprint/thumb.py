import maya.cmds as mc
import System.blueprint as bp 
import System.utils as utils
import os
import Blueprint.finger as finger

CLASS_NAME = 'Thumb'

TITLE = 'Thumb'
DESCRIPTION = 'Creates 4 joints, defining a thumb. Ideal use: thumb'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_thumb.xpm'

class Thumb(finger.Finger):

	class_name = CLASS_NAME


	#!! sUserSpecifiedName doesn't get passed on correctly. The namespace becomes className__className

 
	def __init__(self, sUserSpecifiedName, sHookObj, *args):
		#! thumb init doesn't work unless Finer.__init__ has a super(self)
		#! but then Finger won't work
		jointInfo = [ ['root_joint', [0.0,0.0,0.0]],['knuckle_1_joint', [4.0,0.0,0.0]],
						['knuckle_2_joint', [8.0,0.0,0.0]], ['end_hoint', [12.0,0.0,0.0]] ]
		
		super(Thumb, self).__init__(self.class_name, sUserSpecifiedName, jointInfo, sHookObj, *args)

		#bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo, sHookObj)
