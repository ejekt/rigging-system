import os, sys

try:
    riggingToolRoot = os.environ['RIGGING_TOOL_ROOT']
except:
    print 'RIGGING_TOOL_ROOT env variable not correctly configured'
else:
    print riggingToolRoot
    path = riggingToolRoot + '/Modules/'
    
    if path not in sys.path:
        sys.path.append(path)
    
    import System.blueprintUI as bpUI
    reload(bpUI)
    UI = bpUI.Blueprint_UI()
    