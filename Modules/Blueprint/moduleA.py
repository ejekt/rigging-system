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

#cNamer = n.Name(type='blueprint', mod=CLASS_NAME)

class ModuleA:
	def __init__(self, sName):
		# module namespace name initialized
		self.moduleName = CLASS_NAME
		self.userSpecifiedName = sName

		self.moduleNamespace = self.moduleName + '__' + self.userSpecifiedName

		print 'init module namespace: ', self.moduleNamespace

	def install(self):
		print '\n== MODULE install class {} using namespace {}'.format(CLASS_NAME, self.moduleNamespace)
		# check if one already exists and increment the index if it does
		mc.namespace(setNamespace=':')
		mc.namespace(add=self.moduleNamespace)