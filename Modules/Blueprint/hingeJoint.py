import maya.cmds as mc
import System.blueprint as bp
import System.utils as utils
import os

CLASS_NAME = 'HingeJoint'

TITLE = 'Hinge Joint'
DESCRIPTION = 'Creates 3 joints, the middle joint acting as a hinge  joint. Ideal use: arm/lrg'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_hinge.xpm'


class HingeJoint(bp.Blueprint):

    def __init__(self, CLASS_NAME, sUserSpecifiedName, sHookObj, *args):
        # self.mirrored = False
        super(HingeJoint, self).__init__(CLASS_NAME, sUserSpecifiedName, sHookObj, *args)
        # bp.Blueprint.__init__(self, CLASS_NAME, sUserSpecifiedName, sHookObj)

        self.jointInfo = [['root_joint', [0.0, 0.0, 0.0]], ['hinge_joint', [4.0, 0.0, -1.0]],
                     ['end_joint', [8.0, 0.0, 0.0]]]


    def install_custom(self, joints, *args):
        mc.select(cl=1)
        ikJoints = []

        if not self.mirrored:
            index = 0
            for joint in self.jointInfo:
                # create a new IK joint chain on top of the module
                ikJoints.append(mc.joint(n=self.moduleNamespace+':IK_'+joint[0], p=joint[1],
                                         absolute=1, roo='xyz'))
                mc.setAttr(ikJoints[index]+'.v', 0)
                if index != 0:
                    mc.joint(ikJoints[index-1], edit=1, oj='xyz', sao='yup')
                index +=1
        else:
            # if mirrored create new joints for the IK
            rootJointName = self.jointInfo[0][0]
            tempDuplicateNodes = mc.duplicate(self.originalModule+':IK_'+rootJointName, renameChildren=1)
            # delete the end effector which will be duplicated too
            mc.delete(tempDuplicateNodes.pop())

            mirrorXY = False
            mirrorYZ = False
            mirrorXZ = False
            if self.mirrorPlane == 'XY':
                mirrorXY = True
            if self.mirrorPlane == 'YZ':
                mirrorYZ = True
            if self.mirrorPlane == 'XZ':
                mirrorXZ = True

            mirrorBehavior = False
            if self.rotationFunction == 'behavior':
                mirrorBehavior = True
            mirrorJoints = mc.mirrorJoint(tempDuplicateNodes[0],
                                          mirrorXY=mirrorXY,
                                          mirrorXZ=mirrorXZ,
                                          mirrorYZ=mirrorYZ,
                                          mirrorBehavior= mirrorBehavior)
            mc.delete(tempDuplicateNodes)
            mc.xform(mirrorJoints[0], ws=1, absolute=1,
                     t=mc.xform(self.moduleNamespace+':'+rootJointName, q=1, ws=1, t=1))
            # rename
            for i in range(3):
                jointName = self.jointInfo[i][0]
                newName = mc.rename(mirrorJoints[i], self.moduleNamespace+':IK_'+jointName)
                ikJoints.append(newName)

        # cleanup and container
        utils.addNodeToContainer(self.containerName, ikJoints)
        for joint in ikJoints:
            jointName = utils.stripAllNamespaces(joint)[1]
            mc.container(self.containerName, e=1, publishAndBind=[joint+'.rotate', jointName+'_R'])
        mc.setAttr(ikJoints[0] + '.preferredAngleY', -50.0)
        mc.setAttr(ikJoints[1] + '.preferredAngleY', 50.0)

        ## IK
        # create the actual IK nodes on the ikJoints
        ikNodes = utils.Rp_2segment_stretchy_IK(ikJoints[0], ikJoints[1], ikJoints[2], self.containerName)
        locators = (ikNodes[0], ikNodes[1], ikNodes[2])
        distanceNodes = ikNodes[3]

        # point constrain the ikJoints to the module user controls
        constraints = []
        for i in range(3):
            constraints.append(mc.pointConstraint(self.getTranslationControl(joints[i]), locators[i], mo=0)[0])
            mc.parent(locators[i], self.moduleNamespace+':module_grp', absolute=1)
            mc.setAttr(locators[i]+'.v', 0)
        utils.addNodeToContainer(self.containerName, constraints)

        # add the rotation angle representation
        scaleTarget = self.getTranslationControl(joints[1])
        paRepresentation = self.createPreferredAngleRepresentation(ikJoints[1], scaleTarget)
        mc.setAttr(paRepresentation+'.axis', lock=1)


    def Ui_custom(self):
        joints = self.getJoints()
        self.createRotationOrderUiControl(joints[0])
        self.createRotationOrderUiControl(joints[1])


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

        jointPositions = []
        jointOrientationValues = []
        jointOrientations = []
        jointRotationOrders = []
        jointPreferredAngles = []


        mc.lockNode(self.containerName, lock=0, lockUnpublished=0)
        ikHandle = self.moduleNamespace+':IK_'+self.jointInfo[0][0]+'_ikHandle'
        mc.delete(ikHandle)

        # get the positions and orientations of the joints and IK joints
        for i in range(3):
            jointName = self.jointInfo[i][0]
            ikJointName = self.moduleNamespace+':IK_'+jointName
            mc.makeIdentity(ikJointName, r=1, t=0, s=0, apply=1)

            jointPositions.append(mc.xform(ikJointName, q=1, ws=1, t=1))
            jointRotationOrders.append(mc.getAttr(self.moduleNamespace+':'+jointName+'.rotateOrder'))

            if i < 2:
                jointOrientX = mc.getAttr(ikJointName+'.jointOrientX')
                jointOrientY = mc.getAttr(ikJointName+'.jointOrientY')
                jointOrientZ = mc.getAttr(ikJointName+'.jointOrientZ')

                jointOrientationValues.append( (jointOrientX, jointOrientY, jointOrientZ))

                joint_paX = mc.getAttr(ikJointName+'.preferredAngleX')
                joint_paY = mc.getAttr(ikJointName+'.preferredAngleY')
                joint_paZ = mc.getAttr(ikJointName+'.preferredAngleZ')

                jointPreferredAngles.append( (joint_paX, joint_paY, joint_paZ))

        jointOrientations = (jointOrientationValues, None)
        hookObject = self.findHookObjectForLock()
        rootTransform = False

        # moduleInfo = jointPositions, jointOrientations, jointRotationOrder, jointPreferredAngles, hookObject, rootTransform)
        dModuleInfo = {}
        dModuleInfo['jointPositions'] = jointPositions  # [(xyz position)]
        dModuleInfo['jointOrientations'] = jointOrientations  # [([xyz orientation], None)]
        dModuleInfo['jointRotationOrders'] = jointRotationOrders  # .rotateOrder values
        dModuleInfo['jointPreferredAngles'] = jointPreferredAngles  # None
        dModuleInfo['hookObject'] = hookObject  # None
        dModuleInfo['rootTransform'] = rootTransform  # False

        return dModuleInfo