import maya.OpenMaya as OpenMaya     
import maya.cmds as mc 

def create_soft_cluster():
    ''' Create a cluster using the current selection and soft selection falloff
        applied as a weight map
    '''
    #Grab the soft selection
    selection = OpenMaya.MSelectionList()
    softSelection = OpenMaya.MRichSelection()
    OpenMaya.MGlobal.getRichSelection(softSelection)
    softSelection.getSelection(selection)
   
    dagPath = OpenMaya.MDagPath()
    component = OpenMaya.MObject()
   
    # Filter Defeats the purpose of the else statement
    iter = OpenMaya.MItSelectionList( selection,OpenMaya.MFn.kMeshVertComponent )
    elements, weights = [], []
    verts = []
    iter.getDagPath( dagPath, component )
    nv = OpenMaya.MFnMesh(dagPath.node()).numVertices()
    while not iter.isDone():
        iter.getDagPath( dagPath, component )
        dagPath.pop() #Grab the parent of the shape node
        node = dagPath.fullPathName()
        fnComp = OpenMaya.MFnSingleIndexedComponent(component)   
        getWeight = lambda i: fnComp.weight(i).influence() if fnComp.hasWeights() else 1.0
       
        for i in range(fnComp.elementCount()):
            ind = fnComp.element(i)
            verts.append('%s.vtx[%i]' % (node, ind))
            elements.append(ind)
            weights.append(getWeight(i)) 
        iter.next()
    cluster, cluster_handle =cmds.cluster(verts, before=True)

    mc.select(cluster_handle)
    for m in range(len(elements)):
        mc.setAttr('%s.weightList[0].weights[%d]' % (cluster, elements[m]),weights[m])  
    return cluster_handle
create_soft_cluster()
