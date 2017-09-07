import maya.cmds as mc
from functools import partial

import naming as n
reload(n)
import System.utils as utils
reload(utils)


class Blueprint_UI:
	def __init__(self):
		self.moduleInstance = None

		self.deleteSymmetryMoveExpressions()

		#build the window and run initilizeModuleTab
		self.dUiElements = {}

		if mc.window('bluePrintUiWindow', exists=True):
			mc.deleteUI('bluePrintUiWindow')
		# setup the UI window
		windowWidth = 400
		windowHeight = 300 # 600
		self.dUiElements['window']  = mc.window('bluePrintUiWindow', 
									w=windowWidth, h=windowHeight, t='Blueprint UI',sizeable=False)
		self.dUiElements['topLevelColumn']  = mc.columnLayout(adjustableColumn=True, columnAlign='center')

		# setup tabs
		tabHeight = 600
		self.dUiElements['tabs'] = mc.tabLayout(h=tabHeight, 
								innerMarginWidth=5, 
								innerMarginHeight=5, 
								w=400) 	# had to set width otherwise had a value of 100
		tabWidth = mc.tabLayout(self.dUiElements['tabs'], q=True, width=True) 
		#print tabWidth, ' WIDTH'
		self.scrollWidth = tabWidth - 40
		# initialize the module tab with a button per module
		self.initializeModuleTab(tabHeight, tabWidth)
		mc.tabLayout(self.dUiElements['tabs'], e=True, tabLabelIndex=([1, 'Modules']))

		# Create lock and hide buttons
		mc.text(label='-----------\n WIWUENCWEUINWEFNDSJN')
		mc.setParent(self.dUiElements['topLevelColumn'])
		self.dUiElements['lockPublishColumn'] = mc.columnLayout(adj=True, columnAlign='center', rowSpacing=3)
		self.dUiElements['lockBtn'] = mc.button(label='Lock', command=self.lock)
		mc.separator()
		self.dUiElements['publishBtn'] = mc.button(label='Publish')
		mc.separator()

		# draw the window
		mc.showWindow(self.dUiElements['window'])

		# create listener script job
		self.createScriptJob()

	#
	#		UI
	#
	def initializeModuleTab(self, tabHeight, tabWidth):
		bespokeScrollHeight = 120
		scrollHeight = tabHeight - bespokeScrollHeight
		self.dUiElements['moduleColumn'] = mc.columnLayout(adj=True, rs=3)
		self.dUiElements['moduleFrameLayout'] = mc.frameLayout(h=250,
												collapsable=False, 
												borderVisible=False, 
												labelVisible=False)
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
		self.dUiElements['moduleName'] = mc.textField(enable=False, 
										alwaysInvokeEnterCommandOnReturn=True,
										enterCommand=self.renameModule)



		# setup the button rows
		columnWidth = (tabWidth - 20) / 3	
		mc.setParent(self.dUiElements['moduleColumn'])
		self.dUiElements['moduleButtons_rowColumn'] = mc.rowColumnLayout(numberOfColumns=3, 
										rowOffset=[(1,'both',2), (2,'both',2), (3,'both',2)],
										columnAttach=[(1,'both',3), (2,'both',2), (3,'both',3)],
										columnWidth=[(1, columnWidth), (2, columnWidth), (3, columnWidth)])
		# row1
		self.dUiElements['rehookBtn'] = mc.button(en=False, label='Re-Hook', 
							c=self.rehookModule_setup)
		self.dUiElements['snapRootBtn'] = mc.button(en=False, label='Snap Root > Hook', 
							c=self.snapRootToHook)
		self.dUiElements['constrainRootBtn'] = mc.button(en=False, label='Constrain Root > Hook', 
							c=self.constrainRootToHook)
		# row2
		self.dUiElements['groupSelectedBtn'] = mc.button(en=True, label='Group Selected',
							c=self.groupSelected)
		self.dUiElements['ungroupBtn'] = mc.button(en=False, label='Ungroup',
							c=self.ungroupSelected)
		self.dUiElements['mirrorModuleBtn'] = mc.button(en=False, label='Mirror Module',
							c=self.mirrorSelection)
		# row3
		mc.text(label='')
		self.dUiElements['deleteModuleBtn'] = mc.button(en=False, label='Delete')
		self.dUiElements['symmetryMoveCheckBox'] = mc.checkBox(en=True, label='Symmetry Move',
															onCommand=self.setupSymmetryMoveExpressions_checkBox,
															offCommand=self.deleteSymmetryMoveExpressions,)

		# framework for module specific controls
		mc.setParent(self.dUiElements['moduleColumn'])
		mc.separator()
		self.dUiElements['moduleSpecificRowColumnLayout'] = mc.rowColumnLayout(nr=1, 
										rowAttach=[1,'both',0],
										rowHeight=[1,bespokeScrollHeight],)
		self.dUiElements['moduleSpecificScroll'] = mc.scrollLayout(hst=0)
		self.dUiElements['moduleSpecificColumn'] = mc.columnLayout(columnWidth=self.scrollWidth,
										columnAttach=['both',5], 
										rs=2)

		mc.text(label='This is\n MODULE SPECIFIC TERRITORY')
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


	# 		call to install any module
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

		# get hook object or None
		hookObj = self.findHookObjFromSelection()

		# import the module being clicked and run it's install
		mod = __import__('Blueprint.' + module, {}, {}, [module])
		reload(mod)	
		moduleClass = getattr(mod, mod.CLASS_NAME)
		moduleInstance = moduleClass(userSpecName, hookObj)
		moduleInstance.install()

		#moduleTransform = mod.CLASS_NAME + '__' + userSpecName + ':module_transform'
		moduleTransform = moduleInstance.moduleTransform
		mc.select(moduleTransform, r=True)
		mc.setToolTo('moveSuperContext')



	def lock(self, *args):
		# Get user confirmation to continue lock method
		result = mc.confirmDialog(messageAlign='center', title='Lock Blueprint', 
					message='The action of locking will convert the current blueprint modules to joints. \
							\nIt is UNDOABLE.\
							Do you wish to continue?', 
							button=['Accept','Cancel'],
							defaultButton='Cancel',
							cancelButton='Cancel',
							dismissString='Cancel', 
							icon='warning')
		if result != 'Accept':
			return

		self.deleteSymmetryMoveExpressions()
		mc.checkBox(self.dUiElements['symmetryMoveCheckBox'], e=True, v=False)			

		# Gather all modules in directory
		moduleInfo = [] # store (module, userSpecificName) pairs
		moduleNameInfo = utils.findAllModuleNames('/Modules/Blueprint')
		validModules = moduleNameInfo[0]
		validModuleNames = moduleNameInfo[1]
		# collect namespace info of existing modules in the scene
		namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
		for n in namespaces:
			splitString = n.partition('__')			# only blueprint modules have double underscore
			if splitString[1] != '':
				module = splitString[0]
				userSpecificName = splitString[2]

				if module in validModuleNames:
					index = validModuleNames.index(module)

					moduleInfo.append([validModules[index], userSpecificName])
		# If there are no blueprint modules inform user and exit lock method
		if len(moduleInfo) == 0:
			mc.confirmDialog(ma='center', title='Lock Blueprint',
							message='There appear to be no blueprint module instances in the scene.\
							\n Aborting lock',
							button=['Accept'],
							db='Accept',
							icon='critical')
			return None 
		# START LOCK
		# LOCK PHASE 1
		moduleInstances = []
		for module in moduleInfo:
			# module will hold a ['moduleClassName', userSpecifiedName]
			mod = __import__('Blueprint.'+module[0], {}, {}, [module[0]])
			reload(mod)

			cModuleClass = getattr(mod, mod.CLASS_NAME)
			cModuleInst = cModuleClass(module[1], None)		# (sUserSpecifiedName, hookObj)
			dModuleInfo = cModuleInst.lockPhase1()
			moduleInstances.append( (cModuleInst, dModuleInfo) )

		# LOCK PHASE 2
		for module in moduleInstances:
			module[0].lockPhase2(module[1])
		# delete group nodes and containers if they exist
		groupContainer = 'group_container'
		if mc.objExists(groupContainer):
			mc.lockNode(groupContainer, lock=False, lockUnpublished=False)
			mc.delete(groupContainer)
		# LOCK PHASE 3
		for module in moduleInstances:
			hookObject = module[1]['hookObject']
			module[0].lockPhase3(hookObject)





	# SCRIPTJOB EVERYTIME SELECTION CHANGES
	def createScriptJob(self):
		# create the scriptJob which specifies the command to run every time selection changes
		self.jobNum = mc.scriptJob(event=['SelectionChanged', 
									self.modifySelected], 
									runOnce=True, 
									parent=self.dUiElements['window'])
		print 'created SCRIPTJOB {}'.format(self.jobNum)


	def deleteScriptJob(self):
		# kill the scriptJob 
		mc.scriptJob(kill=self.jobNum)


	def modifySelected(self, *args):
		# script job that fires whenever a selection is changed
		# method to allow changes to a SINGLE selected module at a time using the GUI
		controlEnable = False
		userSpecifiedName = ''

		if mc.checkBox(self.dUiElements['symmetryMoveCheckBox'], q=True, v=True):
			self.deleteSymmetryMoveExpressions()
			self.setupSymmetryMoveExpressions()

		selectedNodes = mc.ls(sl=True)
		if len(selectedNodes) <= 1:
			# clear out variables if selection 1 or less
			self.moduleInstance = None
			selectedModuleNamespace = None
			currentModuleFile = None
			# deactivate the ungroup button
			mc.button(self.dUiElements['ungroupBtn'], e=True, enable=False)
			mc.button(self.dUiElements['mirrorModuleBtn'], e=True, enable=False)
			mc.button(self.dUiElements['groupSelectedBtn'], e=True, enable=False)

			if len(selectedNodes) == 1:
				# actual work is done only if selection is 1 item
				lastSelected = selectedNodes[0]
				# activate ungroup button if selection is a group__
				if lastSelected.find('Group__') == 0:
					mc.button(self.dUiElements['ungroupBtn'], e=True, enable=True)
					mc.button(self.dUiElements['mirrorModuleBtn'], e=True, enable=True, l='Mirror Group')
					mc.button(self.dUiElements['groupSelectedBtn'], e=True, enable=True)

				namespaceAndNode = utils.stripLeadingNamespace(lastSelected)
				if namespaceAndNode != None:
					# split off the namespace and collect valid modules
					namespace = namespaceAndNode[0]

					moduleNameInfo = utils.findAllModuleNames('/Modules/Blueprint')
					validModules = moduleNameInfo[0]
					validModuleNames = moduleNameInfo[1]

					for i, moduleName in enumerate(validModuleNames):
						# compare valid modules and see if the selected namespace is a module or not
						moduleNameincSuffix = moduleName + '__'
						if namespace.find(moduleNameincSuffix) == 0:
							currentModuleFile = validModules[i]
							selectedModuleNamespace = namespace
							break

			constrainCommand = self.constrainRootToHook
			constrainLabel = 'Constrain Root > Hook'

			if selectedModuleNamespace:
				# if one object is selected and it's a valid module this code will run
				# instance the module, and enable the UI buttons and name text field
				controlEnable = True
				userSpecifiedName = selectedModuleNamespace.partition('__')[2]

				mod = __import__('Blueprint.' + currentModuleFile, {}, {}, [currentModuleFile])
				reload(mod)

				moduleClass = getattr(mod, mod.CLASS_NAME)
				self.moduleInstance = moduleClass(userSpecifiedName, None)
				
				mc.button(self.dUiElements['mirrorModuleBtn'], e=True, enable=True, l='Mirror Module')
				mc.button(self.dUiElements['groupSelectedBtn'], e=True, enable=controlEnable)

				if self.moduleInstance.isRootConstrained():
					constrainCommand = self.unConstrainRootFromHook
					constrainLabel = 'Unconstrain Root'


			# enable (if a valid single module is selected) or disable UI elements
			mc.button(self.dUiElements['rehookBtn'], e=True, enable=controlEnable)
			#mc.button(self.dUiElements['groupSelectedBtn'], e=True, enable=controlEnable)
			mc.button(self.dUiElements['constrainRootBtn'], e=True, enable=controlEnable, 
										c=constrainCommand, label=constrainLabel)
			mc.button(self.dUiElements['deleteModuleBtn'], e=True, enable=controlEnable, c=self.deleteModule)
			mc.button(self.dUiElements['snapRootBtn'], e=True, enable=controlEnable, c=self.snapRootToHook)

			mc.textField(self.dUiElements['moduleName'], e=True, enable=controlEnable, text=userSpecifiedName)
			
		if userSpecifiedName:
			self.createModuleSpecificUi()

		self.createScriptJob()




	# GENERIC MODULE TOOLS
	def createModuleSpecificUi(self):
		existingUi = mc.columnLayout(self.dUiElements['moduleSpecificColumn'], q=True, childArray=True)
		if existingUi:
			mc.deleteUI(existingUi)

		mc.setParent(self.dUiElements['moduleSpecificColumn'])

		# this is where the individual module instances call their Ui
		if self.moduleInstance:
			self.moduleInstance.Ui(self, self.dUiElements['moduleSpecificColumn'])


	def deleteModule(self, *args):
		symmetryMove = mc.checkBox(self.dUiElements['symmetryMoveCheckBox'], q=True, v=True)			
		if symmetryMove:
			self.deleteSymmetryMoveExpressions()

		self.moduleInstance.delete()
		mc.select(cl=True)

		if symmetryMove:
			self.setupSymmetryMoveExpressions_checkBox()


	def renameModule(self, *args):
		newName = mc.textField(self.dUiElements['moduleName'], q=True, text=True)

		symmetryMove = mc.checkBox(self.dUiElements['symmetryMoveCheckBox'], q=True, v=True)			
		if symmetryMove:
			self.deleteSymmetryMoveExpressions()

		self.moduleInstance.renameModuleInstance(newName)

		if symmetryMove:
			self.setupSymmetryMoveExpressions_checkBox()

		previousSelection = mc.ls(sl=True)

		if len(previousSelection) > 0:
			mc.select(previousSelection, r=True)
		else:
			mc.select(cl=True)


	# HOOK TOOLS
	def findHookObjFromSelection(self, *args):
		selected = mc.ls(sl=True, transforms=True)
		numSelected = len(selected)
		hookObj = None
		if numSelected != 0:
			hookObj = selected[numSelected - 1]
		return hookObj

	def rehookModule_setup(self, *args):
		# gets called by the gui re-hook button
		print '\n# Start Rehook setup'
		selectedNodes = mc.ls(sl=True, transforms=True)
		if len(selectedNodes) == 2:
			# if 2 objects are selected find the hook object from selected and run instance.rehook()
			newHook = self.findHookObjFromSelection()
			self.moduleInstance.rehook(newHook)
			self.createScriptJob()
		else:
			# if anything but 2 are selected, prompt user for a new selection
			self.deleteScriptJob()
			currentSelection = mc.ls(sl=True)
			mc.headsUpMessage('Please select the translation control you wish to re-hook to.\n Clear selection to un-hook')
			# run rehookModule_callback() as soon as the selection changes
			mc.scriptJob(event=['SelectionChanged', 
						partial(self.rehookModule_callback, currentSelection)], 
						runOnce=True)

	def rehookModule_callback(self, currentSelection):
		# called if selection is not 2
		newHook = self.findHookObjFromSelection()
		self.moduleInstance.rehook(newHook)
		# reset to the previous selection if possible
		try:
			mc.select(currentSelection, r=True)
		except:
			pass
		self.createScriptJob()

	def snapRootToHook(self, *args):

		self.moduleInstance.snapRootToHook()

	def constrainRootToHook(self, *args):

		self.moduleInstance.constrainRootToHook()
		# toggle button to unconstrain
		mc.button(self.dUiElements['constrainRootBtn'], e=True, label='Unconstrain Root',
					c=self.unConstrainRootFromHook)

	def unConstrainRootFromHook(self, *args):

		self.moduleInstance.unConstrainRootFromHook()
		mc.button(self.dUiElements['constrainRootBtn'], e=True, label='Constrain Root > Root',
					c=self.constrainRootToHook)



	# GROUPING AND UNGROUPING
	def groupSelected(self, *args):
		# initialize a GroupSelected class to handle all the grouping functionality
		import System.groupSelected as groupSelected
		reload(groupSelected)

		groupSelected.GroupSelected().showUI()


	def ungroupSelected(self, *args):
		# initialize a UngroupSepected class to handle all the ungrouping functionality
		import System.groupSelected as groupSelected
		reload(groupSelected)

		groupSelected.UngroupSelected()



	# MIRRORING
	def mirrorSelection(self, *args):
		# initialize a MirrorModule class to handle all the mirroring and mirrored nodes
		import System.mirrorModule as mirrorModule
		reload(mirrorModule)

		mirrorModule.MirrorModule()



	# SYMMETRY MOVE
	def setupSymmetryMoveExpressions_checkBox(self, *args):
		# wrapper to delete script job before setting up the summetry move
		self.deleteScriptJob()
		self.setupSymmetryMoveExpressions()
		self.createScriptJob()


	def setupSymmetryMoveExpressions(self, *args):
		mc.namespace(setNamespace=':')
		sel = mc.ls(sl=True, transforms=True)
		# create the container and all the needed symmetry nodes
		expressionContainer = mc.container(n='symmetryMove_container')
		if len(sel) == 0:
			print

		linkedObjs = []
		for obj in sel:
			if obj in linkedObjs:
				continue
			# gather mirrorInfo and run setupSymmetryMoveForObject
			# for the case of a group being symmetry moved
			if obj.find('Group__') == 0:
				if mc.attributeQuery('mirrorLinks', n=obj, exists=True):
					mirrorLinks = mc.getAttr(obj+'.mirrorLinks')
					mirrorInfo = mirrorLinks.rpartition('__')
					mirrorObj = mirrorInfo[0]
					mirrorAxis = mirrorInfo[2]
					linkedObjs.append(mirrorObj)

					self.setupSymmetryMoveForObject(obj, mirrorObj, mirrorAxis, 
													bTranslation=True, bOrientation=True, bGlobalScale=True)

			else:
				objNamespaceInfo = utils.stripLeadingNamespace(obj)
				if objNamespaceInfo != None:
					# check for the mirrorLinks
					if mc.attributeQuery('mirrorLinks', n=objNamespaceInfo[0]+':module_grp', exists=True):
						mirrorLinks = mc.getAttr(objNamespaceInfo[0]+':module_grp.mirrorLinks')
						moduleInfo = mirrorLinks.rpartition('__')
						module = moduleInfo[0]
						axis = moduleInfo[2]

						if objNamespaceInfo[1].find('translation_control') != -1:
							# when symmetry moving translation controls
							mirrorObj = module + ':' + objNamespaceInfo[1]
							linkedObjs.append(mirrorObj)
							self.setupSymmetryMoveForObject(obj, mirrorObj, axis, 
													bTranslation=True, bOrientation=False, bGlobalScale=False)
						elif objNamespaceInfo[1].find('module_transform') == 0:
							# when symmetry moving module controls. t,r,s all true
							mirrorObj = module + ':module_transform'
							linkedObjs.append(mirrorObj)
							self.setupSymmetryMoveForObject(obj, mirrorObj, axis, 
													bTranslation=True, bOrientation=True, bGlobalScale=True)
						elif objNamespaceInfo[1].find('orientation_control') != -1:
							# when symmetry moving orientation control drive with expression
							mirrorObj = module + ':' + objNamespaceInfo[1]
							linkedObjs.append(mirrorObj)
							expressionString = mirrorObj + '.rx = ' + obj + '.rx;\n'
							expression = mc.expression(n=mirrorObj+'_symmetryMoveExpression', string=expressionString)
							utils.addNodeToContainer(expressionContainer, expression)
						elif objNamespaceInfo[1].find('singleJointOrientation_control') != -1:
							mirrorObj = module + ':' + objNamespaceInfo[1]
							linkedObjs.append(mirrorObj)
							expressionString = mirrorObj + '.rx = ' + obj + '.rx;\n'
							expressionString += mirrorObj + '.ry = ' + obj + '.ry;\n'
							expressionString += mirrorObj + '.rz = ' + obj + '.rz;\n'
							expression = mc.expression(n=mirrorObj+'_symmetryMoveExpression', string=expressionString)
							utils.addNodeToContainer(expressionContainer, expression)

		# force evaluate the nodes so they behave as expected
		# causes the script job to re-fire 
		mc.dgdirty( sel )

		mc.lockNode(expressionContainer, lock=True)
		mc.select(sel, r=True)


	def setupSymmetryMoveForObject(self, sObj, sMirrorObj, sMirrorAxis, bTranslation, bOrientation, bGlobalScale):
		# duplicate selected object, parent to an empty group
		duplicateObj = mc.duplicate(sObj, parentOnly=True, inputConnections=True, n=sObj+'_mirrorHelper')[0]
		emptyGroup = mc.group(em=True, n=sObj+'_emptyInvert_grp')
		mc.parent(duplicateObj, emptyGroup, absolute=True)
		# scale in -1 across the mirrorAxis
		scaleAttr = '.scale' + sMirrorAxis
		mc.setAttr(emptyGroup+scaleAttr, -1)

		# construct the symmetry move mel expression
		# it queries the object t,r,s and maps it to the dulpicate object attrs
		expressionString = ''
		expressionString += 'namespace -setNamespace ":";\n'
		if bTranslation:
			expressionString += '$worldSpacePos = `xform -q -ws -translation ' + sObj + '`;\n'
		if bOrientation:
			expressionString += '$worldSpaceOrient = `xform -q -ws -rotation ' + sObj + '`;\n'
		attrs = []
		if bTranslation:
			attrs.extend(['.tx','.ty','.tz'])
		if bOrientation:
			attrs.extend(['.rx','.ry','.rz'])
		for attr in attrs:
			expressionString += duplicateObj+attr + ' = ' + sObj+attr + ';\n'
		i=0
		for axis in ['X','Y','Z']:
			if bTranslation:
				expressionString += duplicateObj+'.translate'+axis + ' = $worldSpacePos['+str(i)+'];\n'
			if bOrientation:
				expressionString += duplicateObj+'.rotate'+axis + ' = $worldSpaceOrient['+str(i)+'];\n'
			i += 1
		
		# create the expression 
		expression = mc.expression(n=duplicateObj+'_symmetryMoveExpression', string=expressionString)

		#print 'now trying to constrain {} \tto\t {}'.format(sMirrorObj, duplicateObj)
		# constrain the actual mirrored object to the duplicate object
		constraint = ''
		if bTranslation and bOrientation:
			constraint = mc.parentConstraint(duplicateObj, sMirrorObj, mo=False, n=sMirrorObj+'_symmetryMoveConstraint')[0]
		elif bTranslation:
			constraint = mc.pointConstraint(duplicateObj, sMirrorObj, mo=False, n=sMirrorObj+'_symmetryMoveConstraint')[0]
		elif bOrientation:
			constraint = mc.orientConstraint(duplicateObj, sMirrorObj, mo=False, n=sMirrorObj+'_symmetryMoveConstraint')[0]
		if bGlobalScale:
			mc.connectAttr(duplicateObj+'.globalScale', sMirrorObj+'.globalScale')


		# add all symmetry move nodes to the container
		utils.addNodeToContainer('symmetryMove_container', [duplicateObj, emptyGroup, expression, constraint], ihb=True)


	def deleteSymmetryMoveExpressions(self, *args):
		# delete the symmetry move ndoes, but expressions first, then constraints
		container = 'symmetryMove_container'
		if mc.objExists(container):
			mc.lockNode(container, lock=False)
			nodes = mc.container(container, q=True, nodeList=True)
			nodes = mc.ls(nodes, type=['parentConstraint','pointConstraint','orientConstraint'])

			if len(nodes) > 0:
				mc.delete(nodes)

			mc.delete(container)