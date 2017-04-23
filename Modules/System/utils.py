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

def findHighestIndex_buzz3d(aNames, sBaseName):
	import re
	iHighestValue = 0

	for n in aNames:
		if n.find(sBaseName) == 0:
			suffix = n.partition(sBaseName)[2]
			#suffix = sBaseName
			print 'suffix ' + suffix
			if re.match('^[0-9]*$', suffix):
				iIndex = int(suffix)
				if iIndex > iHighestValue:
					iHighestValue = iIndex
	print 'highest value found : ' + str(iHighestValue)
	return iHighestValue

def findHighestIndex(sBaseName):
	import re
	iHighestValue = 0


	suffix = sBaseName.rpartition('_')[2]
	#suffix = sBaseName
	print 'suffix ' + suffix
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

