import maya.cmds as mc

def findAllModules(sDir):
	#find the available modules in the path
	# returns: list of modules excluding the *.py
	aModuleList = []
	aAllPyFiles = findAllFiles(sDir, '.py')
	for file in aAllPyFiles:
		if file != '__init__':
			aModuleList.append(file)

	return aModuleList

def findAllModuleNames(sDir):
	# take list of available modules and 
	# return list of touples: (moduleName, module.CLASS_NAME)
	validModules = findAllModules(sDir)
	validModuleNames = []

	packageDir = sDir.partition('/Modules/')[2]

	for module in validModules:
		mod = __import__(packageDir+'.' + module, {}, {}, [module])
		reload(mod)

		validModuleNames.append(mod.CLASS_NAME)

	return(validModules, validModuleNames)


def findAllFiles(sDir, sFileExtension):
	# Search the given directory for all files with given file extension
	# returns: list of file names excluding the extension
	import os

	sFileDirectory = os.environ['RIGGING_TOOL_ROOT'] + '/' + sDir + '/'
	allFiles = os.listdir(sFileDirectory)

	# filter list
	aReturnList = []
	for file in allFiles:
		splitString = str(file).rpartition(sFileExtension)
		if not splitString[1] == '' and splitString[2] == '':
			aReturnList.append(splitString[0])

	return aReturnList

def findHighestIndex(aNames, sBaseName):
	import re
	iHighestValue = 0

	for n in aNames:
		if n.find(sBaseName) == 0:
			suffix = n.partition(sBaseName)[2]
			#suffix = sBaseName
			#print 'suffix ' + suffix
			if re.match('^[0-9]*$', suffix):
				iIndex = int(suffix)
				if iIndex > iHighestValue:
					iHighestValue = iIndex
	print 'highest value found for base name {} is: {}'.format(sBaseName, str(iHighestValue))
	return iHighestValue


def checkNamespaceIndex(sBaseName):
	mc.namespace(setNamespace=':')
	namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
	for i in range(len(namespaces)):
		if namespaces[i].find('__') != -1:
			namespaces[i]=namespaces[i].partition('__')[2]
	cNamer.idx = utils.findHighestIndex(namespaces, sBaseName) + 1
	return sName


def stripLeadingNamespace(sNode):
	# returns [0] the first namespace in the node
	# [1] everything after the first ":"
	if str(sNode).find(':') == -1:
		return None

	splitString = str(sNode).partition(':')

	return [splitString[0], splitString[2]]

def stripAllNamespaces(sNode):
	# returns [0] all the namespaces in the node. Everything before the last ":"
	# [1] the last name. What's after the last ":"
	if str(sNode).find(':') == -1:
		return None

	splitString = str(sNode).rpartition(':')

	return [splitString[0], splitString[2]]	

def basicStretchyIK(sRootJoint, 
					sEndJoint, 
					sContainer=None, 
					bMinLengthLock=True, 
					poleVectorObj=None, 
					sScaleCorrectionAttr=None):
	
	# calculate the length between the joints passed in
	from math import fabs
	containedNodes = []
	fTotalOrigLen = 0.0
	done = False
	parent = sRootJoint
	childJoints = []
	# loop through the joints below and not including the root joint adding up their tX
	while not done:
		children = mc.listRelatives(parent, children=True)
		children = mc.ls(children, type='joint')
		if len(children) == 0:
			done = True
		else:
			child = children[0]
			childJoints.append(child)
			fTotalOrigLen += fabs(mc.getAttr(child+'.tx'))
			parent = child
			if child == sEndJoint:
				done = True


	# create RP Ik chain
	ikNodes = mc.ikHandle(startJoint=sRootJoint, endEffector=sEndJoint, sol='ikRPsolver', n=sRootJoint+'_ikHandle')
	ikNodes[1] = mc.rename(ikNodes[1],sRootJoint+'_ikEffector')
	ikEffector = ikNodes[1]
	ikHandle = ikNodes[0]
	mc.setAttr(ikHandle+'.v', 0)
	containedNodes.extend(ikNodes)

	# create the pole vector
	if poleVectorObj == None:
		poleVectorObj = mc.spaceLocator(n=ikHandle+'_pvLoc')[0]
		containedNodes.append(poleVectorObj)
		mc.xform(poleVectorObj, ws=True, absolute=True, t=mc.xform(sRootJoint, q=True, ws=True, t=True))
		mc.xform(poleVectorObj, ws=True, r=True, t=[0.0,1.0,0.0])
		#mc.setAttr(poleVectorObj+'.v', 0)

	pvConstraint = mc.poleVectorConstraint(poleVectorObj, ikHandle)[0]
	containedNodes.append(pvConstraint)

	# create the start and end locators
	rootLoc = mc.spaceLocator(n=sRootJoint+'_rootPosLoc')[0]
	rootLoc_pCon = mc.pointConstraint(sRootJoint, rootLoc, mo=False, n=rootLoc+'_pConst')[0]
	endLoc = mc.spaceLocator(n=sEndJoint+'_endPosLoc')[0]
	mc.xform(endLoc, ws=True, absolute=True, t=mc.xform(ikHandle, q=True, ws=True, t=True))
	ikHandle_pCon = mc.pointConstraint(endLoc, ikHandle, mo=False, n=ikHandle+'_pConst')[0]
	containedNodes.extend([rootLoc, endLoc, rootLoc_pCon, ikHandle_pCon])
	mc.setAttr(rootLoc+'.v', 0)
	mc.setAttr(endLoc+'.v', 0)

	# find distance between the locators
	rootLoc_noNs = stripAllNamespaces(rootLoc)[1]
	endLoc_noNs = stripAllNamespaces(endLoc)[1]
	moduleNamespace = stripAllNamespaces(sRootJoint)[0]

	distNode = mc.shadingNode('distanceBetween', asUtility=True, 
		n=moduleNamespace+':distBetween_'+rootLoc_noNs+'_'+endLoc_noNs)
	mc.connectAttr(rootLoc+'Shape.worldPosition[0]', distNode+'.point1')
	mc.connectAttr(endLoc+'Shape.worldPosition[0]', distNode+'.point2')
	containedNodes.append(distNode)
	scaleAttr = distNode+'.distance'

	# divide distance by total original length = scale factor
	scaleFactorMd = mc.shadingNode('multiplyDivide', asUtility=True, n=ikHandle+'_scaleFactor')
	containedNodes.append(scaleFactorMd)
	mc.setAttr(scaleFactorMd+'.operation', 2) 		# divide
	mc.connectAttr(scaleAttr, scaleFactorMd+'.input1X')
	mc.setAttr(scaleFactorMd+'.input2X', fTotalOrigLen)
	translationDriver = scaleFactorMd + '.outputX'

	# connect joints to stretchy calculations
	for joint in childJoints:
		multNode = mc.shadingNode('multiplyDivide', asUtility=True, n=joint+'_multScale')
		containedNodes.append(multNode)
		mc.setAttr(multNode+'.input1X', mc.getAttr(joint+'.tx'))
		mc.connectAttr(translationDriver, multNode+'.input2X')
		mc.connectAttr(multNode+'.outputX', joint+'.tx')

	# add everything to the container and build return dict
	if sContainer:
		addNodeToContainer(sContainer, containedNodes, ihb=True)

	dReturn = {}
	dReturn['ikHandle'] = ikHandle
	dReturn['ikEffector'] = ikEffector
	dReturn['rootLoc'] = rootLoc
	dReturn['endLoc'] = endLoc
	dReturn['pvObj'] = poleVectorObj
	dReturn['ikHandle_pCon'] = ikHandle_pCon
	dReturn['rootLoc_pCon'] = rootLoc_pCon

	return dReturn


def forceSceneUpdate():
	mc.setToolTo('moveSuperContext')
	nodes = mc.ls()

	for node in nodes:
		mc.select(node, replace=True)

	mc.select(cl=True)
	mc.setToolTo('selectSuperContext')


def addNodeToContainer(sContainer, sNodesIn, includeShapes=False, ihb=False, force=False):
	import types

	nodes = []
	if type(sNodesIn) is types.ListType:
		nodes = list(sNodesIn)
	else:
		nodes = [sNodesIn]

	conversionNodes = []
	for node in nodes:
		node_conversionNodes = mc.listConnections(node, s=True, d=True)
		node_conversionNodes = mc.ls(node_conversionNodes, type='unitConversion')
		conversionNodes.extend(node_conversionNodes)
	nodes.extend(conversionNodes)
	mc.container(sContainer, edit=True, addNode=nodes, includeHierarchyBelow=ihb, includeShapes=includeShapes, force=force)


def doesBpUserSpecifiedNameExist(sName):
	mc.namespace(setNamespace=':')
	namespaces = mc.namespaceInfo(listOnlyNamespaces=True)

	names = []
	for namespace in namespaces:
		if namespace.find('__') != -1:
			names.append(namespace.partition('__')[2])

	return sName in names


def Rp_2segment_stretchy_IK(rootJoint, hingeJoint, endJoint, container=None, scaleCorrectionAttribute=None):
	''' Function that takes 3 joints and creates a RPsolver IK system on them that is both stretchy and 
	stays on a single plane.
	'''
	moduleNamespaceInfo = stripAllNamespaces(rootJoint)
	moduleNamespace = ''
	if moduleNamespaceInfo != None:
		moduleNamespace = moduleNamespaceInfo[0]

	rootLocation = mc.xform(rootJoint, q=True, ws=True, t=True)
	elbowLocation = mc.xform(hingeJoint, q=True, ws=True, t=True)
	endLocation = mc.xform(endJoint, q=True, ws=True, t=True)

	ikNodes = mc.ikHandle(sj=rootJoint, ee=endJoint, n=rootJoint+'_ikHandle', solver='ikRPsolver')
	ikNodes[1] = mc.rename(ikNodes[1], rootJoint+'_ikEffector')
	ikEffector = ikNodes[1]
	ikHandle = ikNodes[0]

	mc.setAttr(ikHandle+'.v', 0)

	rootLoc = mc.spaceLocator(n=rootJoint+'_positionLoc')[0]
	mc.xform(rootLoc, ws=True, absolute=True, translation=rootLocation)
	mc.parent(rootJoint, rootLoc, absolute=True)

	endLoc = mc.spaceLocator(n=ikHandle+'_positionLoc')[0]
	mc.xform(endLoc, ws=True, absolute=True, translation=endLocation)
	mc.parent(ikHandle, endLoc, absolute=True)

	elbowLoc = mc.spaceLocator(n=hingeJoint+'_positionLoc')[0]
	mc.xform(elbowLoc, ws=True, absolute=True, translation=elbowLocation)
	elbowLocConstraint = mc.poleVectorConstraint(elbowLoc, ikHandle)[0]

	# setup stretchyness
	utilityNodes = []
	for locators in ((rootLoc, elbowLoc, hingeJoint), (elbowLoc, endLoc, endJoint)):
		from math import fabs 		# floating point absolute
		
		startLocNamespaceInfo = stripAllNamespaces(locators[0])
		startLocWithoutNamespace = ''
		if startLocNamespaceInfo != None:
			startLocWithoutNamespace = startLocNamespaceInfo[1]

		endLocNamespaceInfo = stripAllNamespaces(locators[1])
		endLocWithoutNamespace = ''
		if endLocNamespaceInfo != None:
			endLocWithoutNamespace = endLocNamespaceInfo[1]

		startLocShape = locators[0]+'Shape'
		endLocShape = locators[1]+'Shape'
		# distance between
		distNode = mc.shadingNode('distanceBetween', asUtility=True, 
					n=moduleNamespace+':distBetween_'+startLocWithoutNamespace+'_'+endLocWithoutNamespace)
		mc.connectAttr(startLocShape+'.worldPosition[0]', distNode+'.point1')
		mc.connectAttr(endLocShape+'.worldPosition[0]', distNode+'.point2')
		utilityNodes.append(distNode)	
		# scale factor
		scaleFactor = mc.shadingNode('multiplyDivide', asUtility=True, 
					n=distNode+'_scaleFactor')
		mc.setAttr(scaleFactor+'.operation', 2)		# divide
		originalLength = mc.getAttr(locators[2]+'.tx')
		mc.connectAttr(distNode+'.distance', scaleFactor+'.input1X')
		mc.setAttr(scaleFactor+'.input2X', originalLength)
		utilityNodes.append(scaleFactor)

		translationDriver = scaleFactor + '.outputX'

		# scale factor is mutiplied by the abs(originaLength) and that drives the end joints translateX
		translateX = mc.shadingNode('multiplyDivide', asUtility=True, 
					n=distNode+'_translationValue')
		mc.setAttr(translateX+'.input1X', fabs(originalLength))
		mc.connectAttr(translationDriver, translateX+'.input2X')
		mc.connectAttr(translateX+'.outputX', locators[2]+'.tx')
		utilityNodes.append(translateX)

	if container != None:
		containedNodes = list(utilityNodes)
		containedNodes.extend(ikNodes)
		containedNodes.extend( [rootLoc, elbowLoc, endLoc])
		containedNodes.append(elbowLocConstraint)

		# addNodeToContainer(container, containedNodes, ihb=True)

	return (rootLoc, elbowLoc, endLoc, utilityNodes)
