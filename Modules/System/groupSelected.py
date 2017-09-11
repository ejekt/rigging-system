import maya.cmds as mc
from functools import partial
import os
import System.utils as utils

class GroupSelected:
	def __init__(self):
		self.objectsToGroup = []

	def showUI(self):
		# build the grouping GUI
		self.findSelectionToGroup()

		if len(self.objectsToGroup) == 0:
			return

		self.dUiElements = {}
		if mc.window('groupSelected_UI_window', exists=True):
			mc.deleteUI('groupSelected_UI_window')

		windowWidth = 300
		windowHeight = 150
		self.dUiElements['window'] = mc.window('groupSelected_UI_window', 
											w=windowWidth, 
											h=windowHeight, 
											t='Blueprint UI', 
											sizeable=False,)
		self.dUiElements['topLevelColumn'] = mc.columnLayout(adj=True, columnAlign='center', rs=3)
		self.dUiElements['groupName_rowColumn'] = mc.rowColumnLayout(nc=2, columnAttach=[1,'right',0], columnWidth=[(1,80), (2,windowWidth-90)])
		mc.text(label='Group Name :')
		self.dUiElements['groupName'] = mc.textField(text='group')

		mc.setParent(self.dUiElements['topLevelColumn'])

		self.dUiElements['createAt_rowColumn'] = mc.rowColumnLayout(nc=3, columnAttach=(1,'right',0), columnWidth=[(1,80),(2,windowWidth-170),(3,80)])
		# row 1
		mc.text(label='Position at :')
		mc.text(label='')
		mc.text(label='')
		# row 2
		mc.text(label='')
		self.dUiElements['createAtBtn_lastSelected'] = mc.button(l='Last Selected', c=self.createAtLastSelected)
		mc.text(label='')
		# row 3
		mc.text(label='')
		self.dUiElements['createAveragePosBtn_lastSelected'] = mc.button(l='Average Position', c=self.createAtAveragePosition)
		mc.text(label='')

		mc.setParent(self.dUiElements['topLevelColumn'])
		mc.separator()
		# final row of buttons
		columnWidth = (windowWidth/2) - 5
		self.dUiElements['buttonRowLayout'] = mc.rowLayout(nc=2, 
											columnAttach=[(1,'both',10),(2,'both',10)], 
											columnWidth=[(1,columnWidth),(2,columnWidth)],
											columnAlign=[(1,'center'),(2,'center')])
		self.dUiElements['acceptBtn'] = mc.button(l='Accept', c=self.acceptWindow)
		self.dUiElements['cancelBtn'] = mc.button(l='Cancel', c=self.cancelWindow)

		mc.showWindow(self.dUiElements['window'])

		self.createTempGroupRepresentation()
		self.createAtLastSelected()
		mc.select(self.tempGrpTransform, r=True)
		mc.setToolTo('moveSuperContext')


	def findSelectionToGroup(self):
		# filters selection to only contain module transform controls
		selectedObjects = mc.ls(sl=True, transforms=True)

		self.objectsToGroup = []
		for obj in selectedObjects:
			valid = False

			if obj.find('module_transform') != -1:
				splitString = obj.rsplit('module_transform')
				if splitString[1] == '':
					valid = True

			if valid == False and obj.find('Group__') == 0:
				valid = True

			if valid == True:
				self.objectsToGroup.append(obj)


	def createTempGroupRepresentation(self):
		controlGrpFile = os.environ['RIGGING_TOOL_ROOT'] + '/ControlObjects/Blueprint/controlGroup_control.ma'
		mc.file(controlGrpFile, i=True)

		self.tempGrpTransform = mc.rename('controlGroup_control', 'Group__tempGroupTransform__')
		mc.connectAttr(self.tempGrpTransform+'.sy', self.tempGrpTransform+'.sx')
		mc.connectAttr(self.tempGrpTransform+'.sy', self.tempGrpTransform+'.sz')

		for attr in ['sx','sz','v']:
			mc.setAttr(self.tempGrpTransform+'.'+attr, l=True, k=False)

		mc.aliasAttr('globalScale', self.tempGrpTransform+'.sy')


	def createAtLastSelected(self, *args):
		controlPos = mc.xform(self.objectsToGroup[-1], q=True, ws=True, t=True)
		mc.xform(self.tempGrpTransform, ws=True, absolute=True, t=controlPos)


	def createAtAveragePosition(self, *args):
		controlPos = [0.0,0.0,0.0]
		for obj in self.objectsToGroup:
			objPos = mc.xform(obj, q=True, ws=True, absolute=True, t=True)
			controlPos[0] += objPos[0]
			controlPos[1] += objPos[1]
			controlPos[2] += objPos[2]
		numberOfObjects = len(self.objectsToGroup)
		controlPos[0] /= numberOfObjects
		controlPos[1] /= numberOfObjects
		controlPos[2] /= numberOfObjects

		mc.xform(self.tempGrpTransform, ws=True, absolute=True, t=controlPos)


	def cancelWindow(self, *args):
		mc.deleteUI(self.dUiElements['window'])
		mc.delete(self.tempGrpTransform)


	def acceptWindow(self, *args):
		groupName = mc.textField(self.dUiElements['groupName'], q=True, text=True)
		if self.createGroup(groupName) != None:
			mc.deleteUI(self.dUiElements['window'])


	def createGroup(self, sGroupName):
		# check that group of that name doesn't exist yet
		fullGroupName = 'Group__' + sGroupName
		if mc.objExists(fullGroupName):
			mc.confirmDialog(title='Name Conflict', m='Group \''+groupName+'\' already exists', button='Accept', db='Accept')
			return None
		# rename the tempGroup to the user specified name
		groupTransform = mc.rename(self.tempGrpTransform, fullGroupName)
		groupContainer = 'group_container'
		if not mc.objExists(groupContainer):
			mc.container(n=groupContainer)

		containers = [groupContainer]
		for obj in self.objectsToGroup:
			if obj.find('Group__') == 0:
				continue

			objNamespace = utils.stripLeadingNamespace(obj)[0]
			containers.append(objNamespace+':module_container')

		for c in containers:
			mc.lockNode(c, lock=False, lockUnpublished=False)

		if len(self.objectsToGroup) != 0:
			tempGroup = mc.group(self.objectsToGroup, absolute=True)

			groupParent = mc.listRelatives(tempGroup, parent=True)

			if groupParent:
				mc.parent(groupTransform, groupParent[0], absolute=True)

			mc.parent(self.objectsToGroup, groupTransform, absolute=True)
			mc.delete(tempGroup)

		self.addGroupToContainer(groupTransform)

		for c in containers:
			mc.lockNode(c, lock=True, lockUnpublished=True)

		mc.setToolTo('moveSuperContext')
		mc.select(groupTransform, r=True)

		return groupTransform


	def addGroupToContainer(self, sGroup):
		groupContainer = 'group_container'
		utils.addNodeToContainer(groupContainer, sGroup, includeShapes=True)
		groupName = sGroup.rpartition('Group__')[2]
		mc.container(groupContainer, e=True, publishAndBind=[sGroup+'.t', groupName+'_T'])
		mc.container(groupContainer, e=True, publishAndBind=[sGroup+'.r', groupName+'_R'])
		mc.container(groupContainer, e=True, publishAndBind=[sGroup+'.globalScale', groupName+'_globalScale'])



	def createGroupAtSpecified(self, sName, sTargetGroup, sParent):
		self.createTempGroupRepresentation()

		pCon = mc.parentConstraint(sTargetGroup, self.tempGrpTransform	, mo=False)[0]
		mc.delete(pCon)

		scale = mc.getAttr(sTargetGroup+'.globalScale')
		mc.setAttr(self.tempGrpTransform	+'.globalScale', scale)

		if sParent:
			mc.parent(self.tempGrpTransform	, sParent, absolute=True)

		newGroup = self.createGroup(sName)

		return newGroup












###-------------------------------------------------------------------------------------------

###					UNGROUPED SELECTED CLASS


class UngroupSelected:
	def __init__(self):
		selectedObjects = mc.ls(sl=True, transforms=True)
		filteredGroups = []
		for obj in selectedObjects:
			if obj.find('Group__') == 0:
				filteredGroups.append(obj)
		# no group selected just exit
		if len(filteredGroups) == 0:
			return

		groupContainer = 'group_container'
		# find any modules nested under the selected group
		modules = []
		for group in filteredGroups:
			modules.extend(self.findChildModules(group))

		# gather all module containers
		moduleContainers = [groupContainer]
		for module in modules:
			moduleContainer = module + ':module_container'
			moduleContainers.append(moduleContainer)
		# unlock each container
		for container in moduleContainers:
			mc.lockNode(container, l=False, lockUnpublished=False)
		# ungroup
		for group in filteredGroups:
			numChildren = len(mc.listRelatives(group, children=True))
			if numChildren > 1:
				mc.ungroup(group, absolute=True)
			for attr in ['t','r','globalScale']:
				mc.container(groupContainer, e=True, unbindAndUnpublish=group+'.'+attr)

			parentGroup = mc.listRelatives(group, parent=True)
			mc.delete(group)
			# for the case that a group is left empty
			if parentGroup != None:
				parentGroup = parentGroup[0]
				children = mc.listRelatives(parentGroup, children=True)
				children = mc.ls(children, transforms=True)
				if len(children) == 0:
					mc.select(parentGroup, r=True)
					UngroupSelected()

		# lock the container
		for container in moduleContainers:
			if mc.objExists(container):
				mc.lockNode(container, l=True, lockUnpublished=True)



	def findChildModules(self, sGroup):
		modules = []
		children = mc.listRelatives(sGroup, children = True)

		if children != None:
			for child in children:
				moduleNamespaceInfo = utils.stripLeadingNamespace(child)
				if moduleNamespaceInfo:
					modules.append(moduleNamespaceInfo[0])
				elif child.find('Group__') != -1:
					modules.extend(self.findChildModules(child))
		return modules
