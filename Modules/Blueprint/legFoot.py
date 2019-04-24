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
                     ['ankle_joint', [0.0, 0.0, 0.0]], ['ball_joint', [0.0, -9.0, 3.0]],
                     ['toe_joint', [0.0, -9.0, 6.0]]]

        # self.mirrored = False

        # bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, jointInfo, sHookObj)

    def install_custom(self, joints):
        hingeJoint.HingeJoint.install_custom(self, joints)

        ankleOrientationControl = self.createOrientationControl(joints[2], joints[3])
        ballOrientationControl = self.createOrientationControl(joints[3], joints[4])

        mc.setAttr(ankleOrientationControl+'.rotateX', 180)
        mc.setAttr(ballOrientationControl+ '.rotateX', 180)

        mc.xform(self.getTranslationControl(joints[1]), ws=1, a=1, t=[0.0, -4.0, 1.0])
        mc.xform(self.getTranslationControl(joints[2]), ws=1, a=1, t=[0.0, -8.0, 0.0])

        for i in range(len(joints)-1):
            joint = joints[i]
            rotateOrder = 3 # xzy
            if i >= 2:
                rotateOrder = 0 # xyz

            mc.setAttr(joint+'.rotateOrder', rotateOrder)


    def mirror_custom(self, originalModule):
        for i in range(2,4):
            jointName = self.jointInfo[i][0]
            originalJoint = originalModule+':'+jointName
            newJoint = self.moduleNamespace+':'+jointName

            originalOrientationControl = self.getOrientationControl(originalJoint)
            newOrientationControl = self.getOrientationControl(newJoint)
            mc.setAttr(newOrientationControl+'.rotateX', mc.getAttr(originalOrientationControl+'.rotateX'))
            print 'originalOrientationControl', mc.getAttr(originalOrientationControl+'.rotateX')
            print 'newOrientationControl', mc.getAttr(newOrientationControl+'.rotateX')


    def Ui_custom(self):
        hingeJoint.HingeJoint.Ui_custom(self)

        joints = self.getJoints()
        self.createRotationOrderUiControl(joints[2])
        self.createRotationOrderUiControl(joints[3])


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

        # moduleInfo = jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)
        # get module info from hingeJoint first
        dModuleInfo = hingeJoint.HingeJoint.lockPhase1(self)

        jointPositions = dModuleInfo['jointPositions']
        jointOrientationValues = dModuleInfo['jointOrientations'][0]
        jointRotationOrders = dModuleInfo['jointRotationOrders']
        jointPreferredAngles = []

        joints = self.getJoints()
        for i in range(3, 5):       # for ankle and ball joints
            joint = joints[i]
            jointPositions.append(mc.xform(joint, q=1, ws=1, t=1))
            jointRotationOrders.append(mc.getAttr(joint+'.ro'))

        mc.lockNode(self.containerName, lock=0, lockUnpublished=0)

        jointNameInfo = utils.stripAllNamespaces(joints[1])
        cleanParent = jointNameInfo[0] + ':IK_' + jointNameInfo[1]      # IKKnee
        deleteJoints = []
        for i in range(2,4):
            orientationInfo = self.orientationControlledJoint_getOrientation(joints[i], cleanParent)
            jointOrientationValues.append(orientationInfo[0])
            cleanParent = orientationInfo[1]
            deleteJoints.append(cleanParent)

        mc.delete(deleteJoints)

        jointPreferredAngles = None
        hookObject = self.findHookObjectForLock()
        rootTransform = False

        # dModuleInfo['jointPositions'] = jointPositions  # [(xyz position)]
        # dModuleInfo['jointOrientations'] = jointOrientations  # [([xyz orientation], None)]
        # dModuleInfo['jointRotationOrders'] = jointRotationOrders  # .rotateOrder values
        # dModuleInfo['jointPreferredAngles'] = jointPreferredAngles  # None
        # dModuleInfo['hookObject'] = hookObject  # None
        # dModuleInfo['rootTransform'] = rootTransform  # False
        #
        return dModuleInfo

