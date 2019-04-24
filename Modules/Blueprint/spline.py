import maya.cmds as mc
import System.blueprint as bp
reload(bp)
import System.utils as utils
import os

CLASS_NAME = 'Spline'

TITLE = 'Spline'
DESCRIPTION = 'Creates an optionally interpolating joint count adjustable spline. Ideal use: spine, neck, tail'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_spline.xpm'

class Spline(bp.Blueprint):

    def __init__(self, CLASS_NAME, sUserSpecifiedName, sHookObj, numberOfJoints=None, startJointPos=None, endJointPos=None, *args):
        super(Spline, self).__init__(CLASS_NAME, sUserSpecifiedName, sHookObj, *args)

        self.jointInfo = []
        if startJointPos == None:
            startJointPos = [10.0, 0.0, 0.0]
        if endJointPos == None:
            endJointPos= [-10.0, 15.0, 0.0]

        if numberOfJoints == None:
            jointsGrp = CLASS_NAME + '_' + sUserSpecifiedName + ':joints_grp'
            if not mc.objExists(jointsGrp):
                numberOfJoints = 5      # default
            else:
                joints = utils.findJointChain(jointsGrp)
                joints.pop()
                numberOfJoints = len(joints)

        # calculate the incremented joint position
        jointIncrement = list(endJointPos)
        jointIncrement[0] -= startJointPos[0]
        jointIncrement[1] -= startJointPos[1]
        jointIncrement[2] -= startJointPos[2]

        jointIncrement[0] /= (numberOfJoints - 1)
        jointIncrement[1] /= (numberOfJoints - 1)
        jointIncrement[2] /= (numberOfJoints - 1)

        jointPos = startJointPos

        # cycle through and interpolate each joint and save the self.jointInfo
        for i in range(numberOfJoints):
            jointName = 'spline_' + str(i) + '_joint'
            self.jointInfo.append([jointName, list(jointPos)])

            jointPos[0] += jointIncrement[0]
            jointPos[1] += jointIncrement[1]
            jointPos[2] += jointIncrement[2]

        self.canBeMirrored = False

    def install_custom(self, joints, *args):
        self.setupInterpolation()


    def setupInterpolation(self, unlockContainer=False, *args):
        previousSelection = mc.ls(sl=1)

        if unlockContainer:
            mc.lockNode(self.containerName, lock=False, lockUnpublished=False)

        joints = self.getJoints()
        numberOfJoints = len(joints)

        startControl = self.getTranslationControl(joints[0])
        endControl = self.getTranslationControl(joints[numberOfJoints-1])

        # cycle through the joints between the start and end, not including start and end
        pointConstraints = []
        for i in range(1,numberOfJoints-1):
            # adjust the interpolated controls colors
            material = joints[i] + '_m_translation_control'
            mc.setAttr(material + '.colorR', 0.815)
            mc.setAttr(material + '.colorG', 0.629)
            mc.setAttr(material + '.colorB', 0.498)
            # get the weight
            translationControl = self.getTranslationControl(joints[i])
            endWeight = 0.0 + (float(i) / (numberOfJoints-1))
            startWeight = 1.0 - endWeight
            # constrain control to both the start and end
            pointConstraints.append(mc.pointConstraint(startControl, translationControl,
                                                       mo=0, weight=startWeight)[0])
            pointConstraints.append(mc.pointConstraint(endControl, translationControl,
                                                       mo=0, weight=endWeight)[0])

            for attr in ['.tx', '.ty', '.tz']:
                mc.setAttr(translationControl+attr, lock=True)

        interpolationContainer = mc.container(n=self.moduleNamespace+':interpolation_container')
        utils.addNodeToContainer(interpolationContainer, pointConstraints)
        utils.addNodeToContainer(self.containerName, interpolationContainer)

        if unlockContainer:
            mc.lockNode(self.containerName, lock=True, lockUnpublished=True)
        if len(previousSelection) > 0:
            mc.select(previousSelection, r=1)
        else:
            mc.select(cl=1)