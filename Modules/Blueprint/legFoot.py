import maya.cmds as mc
import System.blueprint as bp
import System.utils as utils
import os
import Blueprint.hingeJoint as hingeJoint

CLASS_NAME = 'LegFoot'

TITLE = 'Leg and Foot'
DESCRIPTION = 'Creates 5 joints, the first 3 acting as hip knee and ankle, the last 2 acting as ball and toe.'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_legFoot.xpm'


class LegFoot(hingeJoint.HingeJoint):

    def __init__(self, CLASS_NAME, sUserSpecifiedName, sHookObj, *args):
        super(LegFoot, self).__init__(CLASS_NAME, sUserSpecifiedName, sHookObj, *args)

        self.jointInfo = [['hip_joint', [0.0, 0.0, 0.0]], ['kneee_joint', [4.0, 0.0, -1.0]],
                     ['ankle_joint', [8.0, 0.0, 0.0]], ['ball_joint', [8.0, -9.0, 3.0]],
                     ['toe_joint', [8.0, -9.0, 6.0]]]

        # self.mirrored = False

        # bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo, sHookObj)

