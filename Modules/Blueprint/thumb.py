import maya.cmds as mc
import System.blueprint as bp 
import System.utils as utils
import os
import Blueprint.finger as finger
reload(finger)

CLASS_NAME = 'Thumb'

TITLE = 'Thumb'
DESCRIPTION = 'Creates 4 joints, defining a thumb. Ideal use: thumb'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_thumb.xpm'

class Thumb(finger.Finger):


	def __init__(self, CLASS_NAME, sUserSpecifiedName, sHookObj, *args):

		super(Thumb, self).__init__(CLASS_NAME, sUserSpecifiedName, sHookObj, *args)

		self.jointInfo = [['root_joint', [0.0, 0.0, 0.0]], ['knuckle_1_joint', [4.0, 0.0, 0.0]],
				 ['knuckle_2_joint', [8.0, 0.0, 0.0]], ['end_hoint', [12.0, 0.0, 0.0]]]


