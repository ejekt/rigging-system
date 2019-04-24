import maya.cmds as mc


def getAttrToGraph():
    # returns attribute path if one is selected in the channelbox
    selAttr = mc.channelBox('mainChannelBox', q=1, selectedMainAttributes=1)
    if selAttr and len(selAttr) == 1:
        selObj = mc.ls(sl=1)[-1]
        attrPath = '{}.{}'.format(selObj, selAttr[0])
        return attrPath

def createVisualizerNodes():
    # create node tree
    sGrpFollow = mc.group(n='grp_graphKeys', em=1)
    sLocGraphThis = mc.spaceLocator(n='loc_pointOnGraph')[0]
    mc.addAttr(ln='time')
    mc.addAttr(ln='offsetGraph')
    mc.parent(sGrpFollow, sLocGraphThis)
    iStartTime = int(mc.playbackOptions(q=1, min=1))
    iEndTime = int(mc.playbackOptions(q=1, max=1))
    # adding keys to mark second marks
    for t in range(iStartTime, iEndTime, 24):
        mc.setKeyframe(sGrpFollow, at='translateX', time=[t])
    # setting up the X offset
    sExprCmd = '{0}.offsetGraph = {0}.time - `playbackOptions -q -min` + 1'.format(sLocGraphThis)
    mc.expression(s=sExprCmd, n='expr_visualizerOffset', ae=1)
    return sLocGraphThis, sGrpFollow

createVisualizerNodes()


