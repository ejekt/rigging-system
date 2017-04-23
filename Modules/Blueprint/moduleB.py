import os

CLASS_NAME = 'ModuleB'

TITLE = 'Module B'
DESCRIPTION = 'Test desc for module B'
ICON = os.environ['RIGGING_TOOL_ROOT'] + '/Icons/_hinge.xpm'

class ModuleB:
	def __init__(self):
		print 'moduleB init'

	def install(self):
		print 'install' + CLASS_NAME