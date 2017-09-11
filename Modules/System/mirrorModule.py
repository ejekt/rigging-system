import maya.cmds as mc
from functools import partial
import os
import System.utils as utils

class MirrorModule:
	def __init__(self):
		self.modules = []
		self.group = None
		selection = mc.ls(sl=True, transforms=True)
		if len(selection) == 0:
			return

		# get selection and decide if it's a group or individual modules
		firstSelected = selection[0]
		if firstSelected.find('Group__') == 0:
			self.group = firstSelected
			self.modules = self.findSubModules(firstSelected)
		else:
			moduleNamespaceInfo = utils.stripLeadingNamespace(firstSelected)
			if moduleNamespaceInfo != None:
				self.modules.append(moduleNamespaceInfo[0])
		tempModuleList = []
		for module in self.modules:
			if self.isModuleAMirror(module):
				mc.confirmDialog(title='Mirror Modules', m='Cannot mirror a previously mirrored module. Aborting.', icon='warning', button=['Accept'], db='Accept')
				return
			if not self.canModuleBeMirrored(module):
				print 'module \'' + module + '\' is of a module type that cannot be mirrored... skipping module'
			else:
				tempModuleList.append(module)
		self.modules = tempModuleList

		# call mirror UI
		if len(self.modules) > 0:
			self.mirrorModule_UI()


	def findSubModules(self, sGroup):
		returnModules = []
		children = mc.listRelatives(sGroup, children=True)
		children = mc.ls(children, transforms=True)

		for child in children:
			if child.find('Group__') == 0:
				returnModules.extend(self.findSubModules(child))
			else:
				namespaceInfo = utils.stripAllNamespaces(child)
				if namespaceInfo != None and namespaceInfo[1] == 'module_transform':
					module = namespaceInfo[0]
					returnModules.append(module)
		return returnModules

	def isModuleAMirror(self, sModule):
		moduleGroup = sModule + ':module_grp'
		return mc.attributeQuery('mirrorLinks', node=moduleGroup, exists=True)

	def canModuleBeMirrored(self, sModule):
		# instantiate blank modules of the one passed in order to use it's canModuleBeMirrored method
		validModuleInfo = utils.findAllModuleNames('/Modules/Blueprint')
		validModules = validModuleInfo[0]
		validModuleNames = validModuleInfo[1]
		moduleName = sModule.partition('__')[0]
		if not moduleName in validModuleNames:
			return False
		index = validModuleNames.index(moduleName)
		mod = __import__('Blueprint.'+validModules[index], {}, {}, validModules[index])
		reload(mod)

		moduleClass = getattr(mod, mod.CLASS_NAME)
		moduleInstance = moduleClass('null', None)
		# will return true or false based on the module being instantiated
		return moduleInstance.canModuleBeMirrored()

	def mirrorModule_UI(self):
		# get the user specified names of selected modules 
		self.moduleNames = []
		for module in self.modules:
			self.moduleNames.append(module.partition('__')[2])

		# get user input for applying mirror settings
		self.sameMirrorSettingsForAll = False
		if len(self.modules) > 1:
			result = mc.confirmDialog(title='Mirror Multiple Modules',
										message=str(len(self.modules))+' modules selected for mirror. \n How would you like to proceed?',
										button=['Same for All', 'Individually', 'Cancel'],
										db='Same for All',
										cancelButton='Cancel',
										dismissString='Cancel')
			if result == 'Cancel':
				return
			if result == 'Same for All':
				self.sameMirrorSettingsForAll = True

		self.dUiElements = {}
		if mc.window('mirrorModule_UI_window', exists=True):
			mc.deleteUI('mirrorModule_UI_window')

		windowWidth = 300
		windowHeight = 400
		self.dUiElements['window'] = mc.window('mirrorModule_UI_window', 
										w=windowWidth, 
										h=windowHeight, 
										title='Mirror Module',
										sizeable=False)
		self.dUiElements['scrollLayout'] = mc.scrollLayout(hst=0)
		self.dUiElements['topColumnLayout'] = mc.columnLayout(adj=True, rs=3)
		scrollWidth = windowWidth - 30
		mirrorPlane_textWidth = 70
		mirrorPlane_columnWidth = (scrollWidth - mirrorPlane_textWidth) / 3
		self.dUiElements['mirrorPlane_rowColumn'] = mc.rowColumnLayout(nc=4,
														columnAttach=(1,'right',0), 
														columnWidth=[(1,80),(2,mirrorPlane_textWidth),(3,mirrorPlane_textWidth),(4,mirrorPlane_textWidth)],)
		mc.text(label='Mirror Plane: ')
		self.dUiElements['mirrorPlane_radioCollection'] = mc.radioCollection()
		mc.radioButton('XY', label='XY', select=False)
		mc.radioButton('YZ', label='YZ', select=True)
		mc.radioButton('XZ', label='XZ', select=False)
		mc.setParent(self.dUiElements['topColumnLayout'])
		mc.separator()
		mc.text(label='Mirrored Name(s):')
		columnWidth = scrollWidth/2
		self.dUiElements['moduleName_rowColumn'] = mc.rowColumnLayout(nc=2,
														columnAttach=(1,'right',0),
														columnWidth=[(1,columnWidth),(2,columnWidth)])
		# fields to specify new module names
		for module in self.moduleNames:
			mc.text(label=module + ' >> ')
			self.dUiElements['moduleName_'+module] = mc.textField(enable=True, text=module+'_mirror')

		mc.setParent(self.dUiElements['topColumnLayout'])
		mc.separator()
		# translation and rotation plane selections for new mirrored modules
		if self.sameMirrorSettingsForAll:
			self.generateMirrorFunctionControls(None, scrollWidth)
		else:
			for module in self.moduleNames:
				mc.setParent(self.dUiElements['topColumnLayout'])
				self.generateMirrorFunctionControls(module, scrollWidth)

		mc.setParent(self.dUiElements['topColumnLayout'])
		mc.separator()

		self.dUiElements['button_row'] = mc.rowLayout(nc=2,
													columnWidth=[(1,columnWidth),(2,columnWidth)],
													columnAttach=[(1,'both',10),(2,'both',10)],
													columnAlign=[(1,'center'),(1,'center')])
		mc.button(label='Accept', c=self.acceptWindow)
		mc.button(label='Cancel', c=self.cancelWindow)

		mc.showWindow(self.dUiElements['window'])

	def generateMirrorFunctionControls(self, moduleName, scrollWidth):
		rotationRadioCollection = 'rotation_radioCollection_all'
		translationRadioCollection = 'translation_radioCollection_all'
		textLabel = 'Mirror Settings:'

		behaviorName = 'behavior__'
		orientationName = 'orientation__'
		mirroredName = 'mirrored__'
		worldSpaceName = 'worldSpace__'

		if moduleName != None:
			rotationRadioCollection = 'rotation_radioCollection_' + moduleName
			translationRadioCollection = 'translation_radioCollection_' + moduleName
			textLabel = moduleName + '  Mirror Settings:'

			behaviorName = 'behavior__' + moduleName
			orientationName = 'orientation__' + moduleName
			mirroredName = 'mirrored__' + moduleName
			worldSpaceName = 'worldSpace__' + moduleName

		mc.text(label=textLabel)
		mirrorSettings_textWidth = 80
		mirrorSettings_columnWidth = (scrollWidth - mirrorSettings_textWidth) / 2

		mc.rowColumnLayout(nc=3, 
							columnAttach=(1,'right',0), 
							columnWidth=[(1,mirrorSettings_textWidth),(2,mirrorSettings_columnWidth),(3,mirrorSettings_columnWidth)])
		mc.text(label='Rotation Mirror Function: ')
		self.dUiElements[rotationRadioCollection] = mc.radioCollection()
		mc.radioButton(behaviorName, label='Behavior', select=True)
		mc.radioButton(orientationName, label='Orientation', select=False)

		mc.text(label='Translation Mirror Function: ')
		self.dUiElements[translationRadioCollection] = mc.radioCollection()
		mc.radioButton(mirroredName, label='Mirrored', select=True)
		mc.radioButton(worldSpaceName, label='World Space', select=False)

		mc.setParent(self.dUiElements['topColumnLayout'])
		mc.text(label='')


	def acceptWindow(self, *args):
		'''
		# a moduleInfo entry = (originalModule, 
								murroredModuleName, 
								mirrorPlane, 
								rotationFunction, 
								translationFunction)
		'''
		self.moduleInfo = []
		self.mirrorPlane = mc.radioCollection(self.dUiElements['mirrorPlane_radioCollection'], q=True, select=True)
		for i in range(len(self.modules)):
			originalModule = self.modules[i]
			originalModuleName = self.moduleNames[i]
			originalModulePrefix = originalModule.partition('__')[0]

			mirroredModuleUserSpecifiedName = mc.textField(self.dUiElements['moduleName_'+originalModuleName], q=True, text=True)
			mirroredModuleName = originalModulePrefix + '__' + mirroredModuleUserSpecifiedName

			if utils.doesBpUserSpecifiedNameExist(mirroredModuleUserSpecifiedName):
				mc.confirmDialog(title='Name Conflict', 
									message='Name "' + mirroredModuleUserSpecifiedName + '" already exists.',
									button='Accept', defaultButton='Accept')
				return
			rotationFunction = ''
			translationFunction = ''

			if self.sameMirrorSettingsForAll:
				rotationFunction = mc.radioCollection(self.dUiElements['rotation_radioCollection_all'], q=True, select=True)
				translationFunction = mc.radioCollection(self.dUiElements['translation_radioCollection_all'], q=True, select=True)
			else:
				rotationFunction = mc.radioCollection(self.dUiElements['rotation_radioCollection_'+originalModuleName], q=True, select=True)
				translationFunction = mc.radioCollection(self.dUiElements['translation_radioCollection_'+originalModuleName], q=True, select=True)

			rotationFunction = rotationFunction.partition('__')[0]
			translationFunction = translationFunction.partition('__')[0]

			self.moduleInfo.append([originalModule, mirroredModuleName, self.mirrorPlane, rotationFunction, translationFunction])
		mc.deleteUI(self.dUiElements['window'])
		self.mirrorModules()


	def mirrorModules(self):
		''' Run after mirrorUI Accept button was pressed and all the checks were done,
		and intial self.moduleInfo was created. 
		By the time actual mirroring begins the self.moduleInfo will contain:
		0	[originalModule, 
		1	murroredModuleName, 
		2	mirrorPlane, 
		3	rotationFunction, 
		4	translationFunction,
		5	mirroredModule_fileName,
		6	newHookObject
		7	isConstrained
			'''
		mirrorModulesProgress = 0
		mirrorModulesProgress_UI = mc.progressWindow(title='Mirroring Module(s)', 
													status='This may take a few minutes...',
													isInterruptable=False)
		mirorModulesProgress_stage1_progress = 15
		mirorModulesProgress_stage2_progress = 70
		mirorModulesProgress_stage3_progress = 10

		# get valid modules on disk
		validModuleInfo = utils.findAllModuleNames('/Modules/Blueprint')
		validModules = validModuleInfo[0]
		validModuleNames = validModuleInfo[1]
		for module in self.moduleInfo:
			moduleName = module[0].partition('__')[0]
			# add the mirrored module file name to the moduleInfo list
			if moduleName in validModuleNames:
				index = validModuleNames.index(moduleName)
				module.append(validModules[index])

		# mirror stage 1 - gather info
		# cycle through the modules and find their hook objects, append to info
		mirrorModulesProgress_progressIncrement = mirorModulesProgress_stage1_progress/len(self.moduleInfo)
		for module in self.moduleInfo:
			# instantiate the module as a class object
			userSpecifiedName = module[0].partition('__')[2]
			mod = __import__('Blueprint.'+module[5], {},{}, [module[5]])
			reload(mod)
			moduleClass = getattr(mod, mod.CLASS_NAME)
			moduleInst = moduleClass(userSpecifiedName, None)
			# find the hook object and figure out what module it is
			hookObject = moduleInst.findHookObject()
			newHookObject = None
			hookModule = utils.stripLeadingNamespace(hookObject)[0]
			hookFound = False
			for m in self.moduleInfo:
				if hookModule == m[0]:
					hookFound = True

					if m == module:
						continue

					hookObjectName = utils.stripLeadingNamespace(hookObject)[1]
					newHookObject = m[1] + ':' + hookObjectName
			if not hookFound:
				newHookObject = hookObject
			module.append(newHookObject)
			# if the hook is constrained we want to maintain that in the mirrored as well
			hookConstrained = moduleInst.isRootConstrained()
			module.append(hookConstrained)
			# progress the progress window
			mirrorModulesProgress += mirrorModulesProgress_progressIncrement
			mc.progressWindow(mirrorModulesProgress_UI, edit=True, progress=mirrorModulesProgress)

		# mirror stage 2 - instantiate module classes for all mirrored modules
		# and run the blueprint and module's mirror method
		mirrorModulesProgress = mirorModulesProgress_stage2_progress / len(self.moduleInfo)
		for module in self.moduleInfo:
			newUserSpecifiedName = module[1].partition('__')[2]
			mod = __import__('Blueprint.'+module[5], {},{}, [module[5]])
			reload(mod)
			moduleClass = getattr(mod, mod.CLASS_NAME)
			moduleInst = moduleClass(newUserSpecifiedName, None)
			# run the blueprint mirror method
			moduleInst.mirror(module[0], module[2], module[3], module[4])

			# progress the progress window
			mirrorModulesProgress += mirrorModulesProgress_progressIncrement
			mc.progressWindow(mirrorModulesProgress_UI, edit=True, progress=mirrorModulesProgress)

		# mirror stage 3 
		# re-hook the mirrored module
		mirrorModulesProgress_progressIncrement = mirorModulesProgress_stage3_progress / len(self.moduleInfo)
		for module in self.moduleInfo:
			newUserSpecifiedName = module[1].partition('__')[2]
			mod = __import__('Blueprint.'+module[5], {},{}, [module[5]])
			reload(mod)
			moduleClass = getattr(mod, mod.CLASS_NAME)
			moduleInst = moduleClass(newUserSpecifiedName, None)

			moduleInst.rehook(module[6])
			hookConstrained = module[7]
			if hookConstrained:
				moduleInst.constrainRootToHook()
			# progress the progress window
			mirrorModulesProgress += mirrorModulesProgress_progressIncrement
			mc.progressWindow(mirrorModulesProgress_UI, edit=True, progress=mirrorModulesProgress)

		# mirroring groups
		if self.group != None:
			mc.lockNode('group_container', lock=False, lockUnpublished=False)
			groupParent = mc.listRelatives(self.group, p=True)

			if groupParent:
				groupParent = groupParent[0]

			self.processGroup(self.group, groupParent)

			mc.lockNode('group_container', lock=True, lockUnpublished=True)
			mc.select(cl=True)


		# mirroring complete
		# end the orogress window
		mc.progressWindow(mirrorModulesProgress_UI, edit=True, endProgress=True)
		utils.forceSceneUpdate()


	def processGroup(self, sGroup, sParent):
		import System.groupSelected as groupSelected
		reload(groupSelected)
		# dulpicate the passed in group, then mirror it using another group scaled in the negative
		tempGroup = mc.duplicate(sGroup, parentOnly=True, inputConnections=True)[0]
		emptyGroup = mc.group(em=True)
		mc.parent(tempGroup, emptyGroup, absolute=True)

		scaleAxis = '.sx'
		if self.mirrorPlane == 'XZ':
			scaleAxis = '.sy'
		if self.mirrorPlane == 'XY':
			scaleAxis = '.sz'

		mc.setAttr(emptyGroup+scaleAxis, -1)

		instance = groupSelected.GroupSelected()
		groupSuffix = sGroup.partition('__')[2]
		print instance
		newGroup = instance.createGroupAtSpecified(groupSuffix+'_mirror', tempGroup, sParent)

		mc.lockNode('group_container', lock=False, lockUnpublished=False)
		mc.delete(emptyGroup)

		linkedAttr = 'mirrorLinks'
		group = sGroup
		
		for moduleLink in ((group, newGroup), (newGroup, group)):
			moduleGrp = moduleLink[0] + ':module_grp'
			attrValue = moduleLink[1] + '__'

			if self.mirrorPlane == 'YZ':
				attrValue += 'X'
			if self.mirrorPlane == 'XZ':
				attrValue += 'Y'
			if self.mirrorPlane == 'XY':
				attrValue += 'Z'

			mc.select(moduleLink[0], r=True)
			mc.addAttr(dt='string', ln=linkedAttr, k=False)
			mc.setAttr(moduleLink[0]+'.'+linkedAttr, attrValue, type='string')
		mc.select(cl=True)

		children = mc.listRelatives(group, children=True)
		children = mc.ls(children, transforms=True)

		for child in children:
			if child.find('Group__') == 0:
				self.processGroup(child, newGroup)
			else:
				childNamespaces = utils.stripAllNamespaces(child)
				if childNamespaces != None and childNamespaces[1] == 'module_transform':
					for module in self.moduleInfo:
						if childNamespaces[0] == module[0]:
							moduleContainer = module[1] + ':module_container'
							mc.lockNode(moduleContainer, lock=False, lockUnpublished=False)

							moduleTransform = module[1] + ':module_transform'
							mc.parent(moduleTransform, newGroup, absolute=True)

							mc.lockNode(moduleContainer, lock=True, lockUnpublished=True)

	def cancelWindow(self, *args):
		mc.deleteUI(self.dUiElements['window'])
