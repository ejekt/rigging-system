import maya.cmds as mc
from functools import partial
import os
import System.utils as utils
reload(utils)

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

		if len(self.modules) > 0:
			print 'calling mirror UI'
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
		columnWidth = scrollWidth/24
		self.dUiElements['moduleName_rowColumn'] = mc.rowColumnLayout(nc=2,
														columnAttach=(1,'right',0),
														columnWidth=[(1,columnWidth),(2,columnWidth)])
		for module in self.moduleNames:
			mc.text(label=module + ' >> ')
			self.dUiElements['moduleName_'+module] = mc.textField(enable=True, text=module+'_mirror')



		mc.showWindow(self.dUiElements['window'])
