import maya.cmds as mc
from functools import partial

import naming as n
reload(n)
import System.utils as utils
reload(utils)


class Blueprint_UI:
	def __init__(self):
		#build the window and run initilizeModuleTab
		print 'We are in the Blueprint_UI'

		self.dUiElements = {}

		if mc.window('bluePrintUiWindow', exists=True):
			mc.deleteUI('bluePrintUiWindow')
		# setup the UI window
		windowWidth = 400
		windowHeight = 600
		self.dUiElements['window']  = mc.window('bluePrintUiWindow', 
									w=windowWidth, h=windowHeight, t='Blueprint UI',sizeable=True)
		self.dUiElements['topLevelColumn']  = mc.columnLayout(adjustableColumn=True, columnAlign='center')

		# setup tabs
		tabHeight = 500
		self.dUiElements['tabs'] = mc.tabLayout(h=tabHeight, innerMarginWidth=5, innerMarginHeight=5, w=400)
		tabWidth = mc.tabLayout(self.dUiElements['tabs'], q=True, width=True) # changed 'tabs'
		print tabWidth, ' WIDTH'
		self.scrollWidth = tabWidth - 40
		# initialize the module tab with a button per module
		self.initializeModuleTab(tabHeight, tabWidth)
		mc.tabLayout(self.dUiElements['tabs'], e=True, tabLabelIndex=([1, 'Modules']))

		# Create lock and hide buttons
		mc.setParent(self.dUiElements['topLevelColumn'])
		self.dUiElements['lockPublishColumn'] = mc.columnLayout(adj=True, columnAlign='center', rowSpacing=3)
		mc.separator()
		self.dUiElements['lockBtn'] = mc.button(label='Lock', command=self.lock)
		mc.separator()
		self.dUiElements['publishBtn'] = mc.button(label='Publish')
		mc.separator()

		# draw the window
		mc.showWindow(self.dUiElements['window'])

	def initializeModuleTab(self, tabHeight, tabWidth):
		scrollHeight = tabHeight
		self.dUiElements['moduleColumn'] = mc.columnLayout(adj=True, rs=3)
		self.dUiElements['moduleFrameLayout'] = mc.frameLayout(fn='tinyBoldLabelFont', h=300,
												collapsable=False, borderVisible=False, labelVisible=False)
		self.dUiElements['moduleListScroll'] = mc.scrollLayout(hst=0) # horizontalScrollBarThickness
		self.dUiElements['moduleListColumn'] = mc.columnLayout(columnWidth=self.scrollWidth, 
										adj=True, rs=2)

		# begin list of modules and install a button for each blueprint module in the folder
		aModuleList = []
		aModuleList = utils.findAllModules('Modules/Blueprint')
		for module in aModuleList:
			self.createModuleInstallButton(module)
			mc.setParent(self.dUiElements['moduleListColumn'])
			mc.separator()
		mc.setParent(self.dUiElements['moduleColumn'])
		# setup the module name renamer
		mc.separator()
		self.dUiElements['moduleName_row'] = mc.rowLayout(nc=2, 
											columnAttach=(1,'right',0), 
											columnWidth=[1,80], 
											adjustableColumn=2)
		mc.text(label='Module Name :')
		self.dUiElements['moduleName'] = mc.textField(enable=False, alwaysInvokeEnterCommandOnReturn=True)



		# setup the button rows
		columnWidth = (tabWidth - 20) / 3	
		mc.setParent(self.dUiElements['moduleColumn'])
		self.dUiElements['moduleButtons_rowColumn'] = mc.rowColumnLayout(numberOfColumns=3, 
										rowOffset=[(1,'both',2), (2,'both',2), (3,'both',2)],
										columnAttach=[(1,'both',3), (2,'both',2), (3,'both',3)],
										columnWidth=[(1, columnWidth), (2, columnWidth), (3, columnWidth)])
		self.dUiElements['rehookBtn'] = mc.button(en=False, label='Re-Hook')
		self.dUiElements['snapRootBtn'] = mc.button(en=False, label='Snap Root > Hook')
		self.dUiElements['constrainRootBtn'] = mc.button(en=False, label='Constrain Root > Hook')

		self.dUiElements['groupSelectedBtn'] = mc.button(en=False, label='Group Selected')
		self.dUiElements['ungroupBtn'] = mc.button(en=False, label='Ungroup')
		self.dUiElements['mirrorModuleBtn'] = mc.button(en=False, label='Mirror Module')
		mc.text(label='')
		self.dUiElements['deleteModuleBtn'] = mc.button(en=False, label='Delete')
		self.dUiElements['symmetryMoveCheckBox'] = mc.checkBox(en=True, label='Symmetry Move')

		mc.setParent(self.dUiElements['moduleColumn'])


	def createModuleInstallButton(self, module):
		# initialize a new instance of the module class and make a button to run it
		mod = __import__('Blueprint.' + module, {}, {}, [module])
		reload(mod)

		title = mod.TITLE
		desc = mod.DESCRIPTION
		icon = mod.ICON
		# create the UI button
		buttonSize = 65
		row = mc.rowLayout(numberOfColumns=2, 
						columnWidth=([1,buttonSize]), 
						adjustableColumn=2, 
						columnAttach=([1, 'both', 0],[2, 'both', 5]), 
						h=80,)
		self.dUiElements['moduleButton_' + module] = mc.symbolButton(w=buttonSize, 
													h=buttonSize, 
													image=icon, 
													command=partial(self.installModule, module))
		mc.columnLayout(columnAlign='center')
		mc.text(align='center', label=title) 		#  w=self.scrollWidth - buttonSize - 16
		mc.scrollField(text=desc, editable=False, wordWrap=True, w=300)
		mc.setParent(self.dUiElements['moduleListColumn'])

	def installModule(self, module, *args):
		''' base blueprint module installer '''
		# access the blueprint model class name
		# needs to create a new namespace for each installation, incrementing
		sBaseName = 'instance_'
		# check to see if any rigging tool namespaces already exist in the scene root
		mc.namespace(setNamespace=':')
		namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
		for i in range(len(namespaces)):
			if namespaces[i].find('__') != -1:
				namespaces[i]=namespaces[i].partition('__')[2]

		iSuffix = utils.findHighestIndex(namespaces, sBaseName) + 1
		userSpecName = sBaseName + str(iSuffix)
		# import the module being clicked and run it's install
		mod = __import__('Blueprint.' + module, {}, {}, [module])
		reload(mod)	
		moduleClass = getattr(mod, mod.CLASS_NAME)
		moduleInstance = moduleClass(userSpecName)
		moduleInstance.install()

		#moduleTransform = mod.CLASS_NAME + '__' + userSpecName + ':module_transform'
		moduleTransform = moduleInstance.moduleTransform
		mc.select(moduleTransform, r=True)
		mc.setToolTo('moveSuperContext')
	
	def lock(self, *args):
		# 
		result = mc.confirmDialog(messageAlign='center', title='Lock Blueprint', 
					message='The action of locking will convert the current blueprint modules to joints. \
							\nIt is UNDOABLE.\
							Do you wish to continue?', 
							button=['Accept','Cancel'],
							defaultButton='Cancel',
							cancelButton='Cancel',
							dismissString='Cancel', 
							icon='warning')
		if result == 'Cancel':
			print 'pressed cancel'
			return None

		moduleInfo = [] # store (module, userSpecificName) pairs
		namespaces = mc.namespaceInfo(listOnlyNamespaces=True)

		moduleNameInfo = utils.findAllModuleNames('/Modules/Blueprint')
		validModules = moduleNameInfo[0]
		validModuleNames = moduleNameInfo[1]

		for n in namespaces:
			splitString = n.partition('__')
			if splitString[1] != '':
				module = splitString[0]
				userSpecificName = splitString[2]

				if module in validModuleNames:
					index = validModuleNames.index(module)

					moduleInfo.append([validModules[index], userSpecificName])

		if len(moduleInfo) == 0:
			mc.confirmDialog(ma='center', title='Lock Blueprint',
							message='There appear to be no blueprint module instances in the scene.\
							\n Aborting lock',
							button=['Accept'],
							db='Accept',
							icon='critical')
			return None 

		moduleInstances = []
		for module in moduleInfo:
			mod = __import__('Blueprint.'+module[0], {}, {}, [module[0]])
			reload(mod)

			moduleClass = getattr(mod, mod.CLASS_NAME)
			moduleInst = moduleClass(sUserSpecifiedName=module[1])
			moduleInst.lockPhase1()






