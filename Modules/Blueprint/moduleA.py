import os
import naming as n
reload(n)
import maya.cmds as mc
import System.utils as utils
reload(utils)

CLASS_NAME = 'ModuleA'

TITLE = 'Module A'
DESCRIPTION = 'Test desc for module A'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_hand.xpm'

cNamer = n.Name(type='blueprint', mod=CLASS_NAME)

class ModuleA:
	def __init__(self, sName):
		# module namespace name initialized
		cNamer.part = sName
		cNamer.idx = 0
		cNamer.constructName()
		self.sName = cNamer.name

		print 'NAME: ' + self.sName

	def install(self):
		print '\n== MODULE install\t' + CLASS_NAME
		# check if one already exists and increment the index if it does
		mc.namespace(setNamespace=':')
		namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
		self.partName = 'userGeneratedName'
		cNamer = n.Name( type='blueprint', mod=CLASS_NAME, part=self.partName)
		cNamer.constructName()
		sBaseName = cNamer.name


		print 'testing --  ' + sBaseName
		if mc.namespace(exists=':%s' % sBaseName ):
			print '\t--------'+ sBaseName	+ ' ---exists'
			cNamer.idx = cNamer.getIndex() + 1
			namespaces = mc.namespaceInfo(listOnlyNamespaces=True)
			print 'findHighestIndex returns: ' + str(utils.findHighestIndex_buzz3d(namespaces, sBaseName))
			print 'incrementing to:  ' + str(cNamer.idx)
		
		cNamer.constructName()
		print 'cnamer==' + cNamer.name + '\t INSTALLING'
		self.sName = cNamer.name
		mc.namespace(add=self.sName)