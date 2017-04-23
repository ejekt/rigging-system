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
		self.dUiElements['window']  = mc.window('bluePrintUiWindow', w=windowWidth, h=windowHeight, t='Blueprint UI',s=False)
		self.dUiElements['topLevelColumn']  = mc.columnLayout(adjustableColumn=True, columnAlign='center')
		# setup tabs
		tabHeight = 500
		self.dUiElements['tabs'] = mc.tabLayout(h=tabHeight, innerMarginWidth=5, innerMarginHeight=5)
		tabWidth = mc.tabLayout(self.dUiElements['tabs'], q=True, w=True)
		self.scrollWidth = tabWidth - 40
		# initialize the module tab with a button per module
		self.initializeModuleTab(tabHeight, tabWidth)
		mc.tabLayout(self.dUiElements['tabs'], e=True, tabLabelIndex=([1, 'Modules']))
		# draw the window
		mc.showWindow(self.dUiElements['window'])

	def initializeModuleTab(self, tabHeight, tabWidth):
		scrollHeight = tabHeight
		self.dUiElements['moduleColumn'] = mc.columnLayout(adj=True, rs=3)
		self.dUiElements['moduleFrameLayout'] = mc.frameLayout(h=scrollHeight, collapsable=False, borderVisible=False, labelVisible=False)
		self.dUiElements['moduleListScroll'] = mc.scrollLayout(hst=0)
		self.dUiElements['moduleListColumn'] = mc.columnLayout(columnWidth=self.scrollWidth, adj=True, rs=2)

		# begin list of modules and install a button for each blueprint module in the folder
		aModuleList = []
		aModuleList = utils.findAllModules('Modules/Blueprint')
		for module in aModuleList:
			self.createModuleInstallButton(module)
			mc.setParent(self.dUiElements['moduleListColumn'])
			mc.separator()
		mc.setParent(self.dUiElements['moduleColumn'])
		mc.separator()

	def createModuleInstallButton(self, module):
		# initialize a new instance of the module class and make a button to run it
		mod = __import__('Blueprint.' + module, {}, {}, [module])
		reload(mod)

		title = mod.TITLE
		desc = mod.DESCRIPTION
		icon = mod.ICON
		# create the UI button
		buttonSize = 65
		row = mc.rowLayout(numberOfColumns=2, columnWidth=([1,buttonSize]), adjustableColumn=2, columnAttach=([1, 'both', 0],[2, 'both', 5]), h=self.scrollWidth)
		self.dUiElements['moduleButton_' + module] = mc.symbolButton(w=buttonSize, h=buttonSize, image=icon, command=partial(self.installModule, module))
		textColumn = mc.columnLayout(columnAlign='center')
		mc.text(align='center', label=title) 		#  w=self.scrollWidth - buttonSize - 16
		mc.scrollField(text=desc, editable=False, wordWrap=True)
		mc.setParent(self.dUiElements['moduleListColumn'])

	def installModule(self, module, *args):
		''' base blueprint module installer '''
		# access the blueprint model class name
		# needs to create a new namespace for each installation, incrementing

		mod = __import__('Blueprint.' + module, {}, {}, [module])
		reload(mod)	
		moduleClass = getattr(mod, mod.CLASS_NAME)
		# build 
		self.partName = 'userGeneratedName'
		'''
		cNamer = n.Name( type='blueprint', mod=mod.CLASS_NAME, part=self.partName)
		cNamer.constructName()
		sBaseName = cNamer.name
		print 'BASENAME: ' + sBaseName

		# check to see if any rigging tool namespaces already exist in the scene root
		mc.namespace(setNamespace=':')
		namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
		for i in range(len(namespaces)):
			if namespaces[i].find('__') != -1:
				namespaces[i]=namespaces[i].partition('__')[2]

		if mc.namespace(exists=':%s' % sBaseName ):
			print '\t--------'+ sBaseName	+ ' ---exists'
			cNamer.idx = cNamer.getIndex() + 1
			print 'incrementing to:  ' + str(cNamer.idx)'''
		moduleInstance = moduleClass(self.partName)
		moduleInstance.install()