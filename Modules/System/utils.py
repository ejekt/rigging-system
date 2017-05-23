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
	print 'highest value found : ' + str(iHighestValue)
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
	if str(sNode).find(':') == -1:
		return none

	splitString = str(sNode).partition(':')

	return [splitString[0], splitString[2]]

def stripAllNamespaces(sNode):
	if str(sNode).find(':') == -1:
		return none

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
		mc.setAttr(poleVectorObj+'.v', 0)

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
	mc.container(sContainer, edit=True, addNode=nodes, ihb=ihb, includeShapes=includeShapes, force=force)
