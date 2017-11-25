
# --------------------------------------------------------------------------
# rem_findVector.py - Python
#
#	Remi CAUZID - remi@cauzid.com
#	Copyright 2013 Remi Cauzid - All Rights Reserved.
# --------------------------------------------------------------------------
#
#
# 	snpas joint on a 2 curve using motion path
# 	ossibility to create an offset group to keep joint tr and ro free
#
 
if not (cmds.pluginInfo('closestPointOnCurve',q=1,loaded=1)):
	cmds.loadPlugin('closestPointOnCurve',quiet=1)

	
############################
#
#           #
#           ###
#################
###################  !!!! createNodeOnCurve IS A BETTER SOLUTION !!!!
#################
#           ###
#           #
#
############################

	

def rem_transformOnCurve( target, crv, name, side ):
	tmpCurve = cmds.circle( ch=0 )[0]
	
	fullname = name
	if side == 'L' or  side == 'R' or  side == 'l' or  side == 'r':
		fullname = side+'_'+name

	loc = cmds.spaceLocator( n='toDelete_loc' )[0]
	cmds.parent( loc, target, r=1 )
	cpoc = cmds.createNode( 'closestPointOnCurve' )	
	cmds.connectAttr( loc+'.worldPosition', cpoc+'.ip' )
	cmds.connectAttr( crv+'.ws', cpoc+'.ic' )
	pos = cmds.getAttr( cpoc+'.paramU' )


	#create group and joint
	cmds.select( cl=1 )	
	onCurve_grp = cmds.group( empty=1, n=fullname+'_null' )

	#create motion path
	up_motionPath = cmds.pathAnimation( tmpCurve, onCurve_grp, fm=1, f=1, fa='x', ua='y', wut='scene', b=0 )
	cmds.connectAttr( crv+'.ws', up_motionPath+'.geometryPath', f=1  ) 
	for axe in ['x','y','z']:
		addDouble = cmds.listConnections( up_motionPath+'.'+axe+'Coordinate' )
		cmds.delete( addDouble )
		cmds.connectAttr( up_motionPath+'.'+axe+'Coordinate', onCurve_grp+'.t'+axe )

	#delete  anim curve on u val
	up_animCrv = cmds.listConnections( up_motionPath+'.u' )
	cmds.delete( up_animCrv, loc, tmpCurve )
	#set u val
	cmds.setAttr( up_motionPath+'.fractionMode', False )
	cmds.setAttr( up_motionPath+'.uValue', pos )
	
	return up_motionPath




def rem_jointSnapOnCurve( nbOfJoint, curvePath, curveUp, name, side, jointUnderParent=0 ):
	# as sometime maya pathAnimation get lost let help him
	tmpCurve = cmds.circle( ch=0 )[0]
	
	fullname = name
	if side == 'L' or  side == 'R' or  side == 'l' or  side == 'r':
		fullname = side+'_'+name
	
	upGroup = []
	jointOnCurve = []
	up_motionPaths = []
	path_motionPaths = []
	offsetOnCurve = []

	#test if curve close or open
	testClose = cmds.getAttr( curvePath+'.form' )
	close = 'no'
	if testClose>0:
		close = 'yes'
	if nbOfJoint > 1:
		if close == 'no':
			distBtwJoints = float(1)/(nbOfJoint-1)
		else:
			distBtwJoints = float(1)/(nbOfJoint)
	else:
		distBtwJoints = 0
	
	#groupe
	curveRig_grp = cmds.group( em=1, n=fullname+'Rig_null' )
	curveNT_grp = cmds.group( em=1, n=fullname+'NoTransform_null' )
	cmds.setAttr( curveNT_grp+'.inheritsTransform', 0 )
	curveRig_DATA = cmds.group( em=1, n=fullname+'DATA_null' )
	cmds.parent( curveRig_DATA, curveNT_grp, curveRig_grp )

	i=0
	while i<nbOfJoint:
		jntName = 'jntChain'
		#create group and joint
		cmds.select( cl=1 )	
		up_grp = cmds.group( empty=1, n=fullname+str(i)+'_null' )
		cmds.select( cl=1 )	
		OnCurve_jnt = cmds.joint( p=[0,0,0], n=fullname+'_'+str(i)+'_env' )
		onCurve_grp = ''
		onCurveSlave = OnCurve_jnt
		if jointUnderParent == 1:
			onCurve_grp = cmds.group( empty=1, n=fullname+str(i)+'Offset_null' )
			cmds.parent( OnCurve_jnt, onCurve_grp)
			onCurveSlave = onCurve_grp
			
		#create motion path
		up_motionPath = cmds.pathAnimation( tmpCurve, up_grp, fm=1, f=1, fa='x', ua='y', wut='vector', wu=[0,1,0], b=0 )
		cmds.connectAttr( curveUp+'.ws', up_motionPath+'.geometryPath', f=1  ) 
		joint_motionPath = cmds.pathAnimation( tmpCurve, onCurveSlave, fm=1, f=1, fa='x', ua='y', wut='vector', wu=[0,1,0], iu=0, b=0 )
		cmds.connectAttr( curvePath+'.ws', joint_motionPath+'.geometryPath', f=1  ) 
		up_addDoublex = cmds.listConnections( up_motionPath+'.xCoordinate' )
		up_addDoubley = cmds.listConnections( up_motionPath+'.yCoordinate' )
		up_addDoublez = cmds.listConnections( up_motionPath+'.zCoordinate' )
		path_addDoublex = cmds.listConnections( joint_motionPath+'.xCoordinate' )
		path_addDoubley = cmds.listConnections( joint_motionPath+'.yCoordinate' )
		path_addDoublez = cmds.listConnections( joint_motionPath+'.zCoordinate' )
		cmds.delete( up_addDoublex, up_addDoubley, up_addDoublez, path_addDoublex, path_addDoubley, path_addDoublez )
		cmds.connectAttr( up_motionPath+'.xCoordinate', up_grp+'.tx' )
		cmds.connectAttr( up_motionPath+'.yCoordinate', up_grp+'.ty' )
		cmds.connectAttr( up_motionPath+'.zCoordinate', up_grp+'.tz' )
		cmds.connectAttr( joint_motionPath+'.xCoordinate', onCurveSlave+'.tx' )
		cmds.connectAttr( joint_motionPath+'.yCoordinate', onCurveSlave+'.ty' )
		cmds.connectAttr( joint_motionPath+'.zCoordinate', onCurveSlave+'.tz' )
		#delete  anim curve on u val
		up_animCrv = cmds.listConnections( up_motionPath+'.u' )
		jnt_animCrv = cmds.listConnections( joint_motionPath+'.u' )
		cmds.delete( up_animCrv, jnt_animCrv )
		#set u val
		uVal = i*distBtwJoints
		if nbOfJoint == 1:
			uVal = 0.5
		cmds.setAttr( up_motionPath+'.uValue', uVal )
		cmds.setAttr( joint_motionPath+'.uValue', uVal )
		#set up object on motion path
		cmds.setAttr( joint_motionPath+'.worldUpType', 1 )

		cmds.setAttr( joint_motionPath+'.frontAxis', 2 )
		cmds.setAttr( joint_motionPath+'.upAxis', 0 )
		cmds.setAttr( joint_motionPath+'.inverseUp', 1 )
		
		cmds.connectAttr( up_grp+'.worldMatrix[0]', joint_motionPath+'.worldUpMatrix' )
		#save outpout
		upGroup.append( up_grp )
		jointOnCurve.append( OnCurve_jnt )
		offsetOnCurve.append( onCurve_grp )
		up_motionPaths.append( up_motionPath )
		path_motionPaths.append( joint_motionPath )
		#increment i
		i = i+1
		
		if cmds.objExists( 'base_prefs_null.jointVis' ):
			cmds.connectAttr( 'base_prefs_null.jointVis', OnCurve_jnt+'.v' )
		if cmds.objExists( 'base_prefs_null.jointDispType' ):
			cmds.setAttr( OnCurve_jnt+'.overrideEnabled', 1 )
			cmds.connectAttr( 'base_prefs_null.jointDispType', OnCurve_jnt+'.overrideDisplayType' )
	cmds.delete( tmpCurve )

	#parent stuff
	cmds.parent( upGroup, curveNT_grp )
	if jointUnderParent == 0:
		cmds.parent( jointOnCurve, curveNT_grp )
	else:
		cmds.parent( offsetOnCurve, curveNT_grp )
	
	#connect stuff to DATA grp
	if not cmds.objExists( curveRig_DATA+'.curveUp' ): 
		cmds.addAttr( curveRig_DATA, ln='curveUp', at='double' )
	if not cmds.objExists( curveUp+'.curveUp' ): 
		cmds.addAttr( curveUp, ln='curveUp', at='double' )
	cmds.connectAttr( curveRig_DATA+'.curveUp', curveUp+'.curveUp', f=1 )

	if not cmds.objExists( curveRig_DATA+'.curvePath' ): 
		cmds.addAttr( curveRig_DATA, ln='curvePath', at='double' )
	if not cmds.objExists( curvePath+'.curvePath' ): 
		cmds.addAttr( curvePath, ln='curvePath', at='double' )
	cmds.connectAttr( curveRig_DATA+'.curvePath', curvePath+'.curvePath', f=1 )

	if not cmds.objExists( curveRig_DATA+'.topNode' ): 
		cmds.addAttr( curveRig_DATA, ln='topNode', at='double' )
	if not cmds.objExists( curveRig_grp+'.topNode' ): 
		cmds.addAttr( curveRig_grp, ln='topNode', at='double' )
	cmds.connectAttr( curveRig_DATA+'.topNode', curveRig_grp+'.topNode', f=1 )

	if not cmds.objExists( curveRig_DATA+'.upGroup' ): 
		cmds.addAttr( curveRig_DATA, ln='upGroup', at='double' )
	for grp in upGroup:
		if not cmds.objExists( grp+'.upGroup' ): 
			cmds.addAttr( grp, ln='upGroup', at='double' )
		cmds.connectAttr( curveRig_DATA+'.upGroup', grp+'.upGroup', f=1 )

	if not cmds.objExists( curveRig_DATA+'.joint' ): 
		cmds.addAttr( curveRig_DATA, ln='joint', at='double' )
	for jnt in jointOnCurve:
		if not cmds.objExists( jnt+'.joint' ): 
			cmds.addAttr( jnt, ln='joint', at='double' )
		cmds.connectAttr( curveRig_DATA+'.joint', jnt+'.joint', f=1 )

	if not cmds.objExists( curveRig_DATA+'.offset' ): 
		cmds.addAttr( curveRig_DATA, ln='offset', at='double' )
	for grp in offsetOnCurve:
		if not grp == '':
			if not cmds.objExists( grp+'.offset' ): 
				cmds.addAttr( grp, ln='offset', at='double' )
			cmds.connectAttr( curveRig_DATA+'.offset', grp+'.offset', f=1 )

	if not cmds.objExists( curveRig_DATA+'.upMotionPath' ): 
		cmds.addAttr( curveRig_DATA, ln='upMotionPath', at='double' )
	for montion in up_motionPaths:
		if not cmds.objExists( montion+'.upMotionPath' ): 
			cmds.addAttr( montion, ln='upMotionPath', at='double' )
		cmds.connectAttr( curveRig_DATA+'.upMotionPath', montion+'.upMotionPath', f=1 )

	if not cmds.objExists( curveRig_DATA+'.pathMotionPath' ): 
		cmds.addAttr( curveRig_DATA, ln='pathMotionPath', at='double' )
	for montion in path_motionPaths:
		if not cmds.objExists( montion+'.pathMotionPath' ): 
			cmds.addAttr( montion, ln='pathMotionPath', at='double' )
		cmds.connectAttr( curveRig_DATA+'.pathMotionPath', montion+'.pathMotionPath', f=1 )
			
	return curveRig_DATA

#no up curve just Translate can be used
def rem_jointSnapOnCurveSimple( nbOfJoint, curvePath, name, side ):
	fullname = name
	if side == 'L' or  side == 'R' or  side == 'l' or  side == 'r':
		fullname = side+'_'+name
	
	jointOnCurve = []
	path_motionPaths = []
	offsetOnCurve = []

	#test if curve close or open
	testClose = cmds.getAttr( curvePath+'.form' )
	close = 'no'
	if testClose>0:
		close = 'yes'
	if close == 'no':
		distBtwJoints = float(1)/(nbOfJoint-1)
	else:
		distBtwJoints = float(1)/(nbOfJoint)
	
	#groupe
	curveRig_grp = cmds.group( em=1, n=fullname+'Rig_null' )
	curveNT_grp = cmds.group( em=1, n=fullname+'NoTransform_null' )
	cmds.setAttr( curveNT_grp+'.inheritsTransform', 0 )
	curveRig_DATA = cmds.group( em=1, n=fullname+'DATA_null' )
	cmds.parent( curveNT_grp, curveRig_DATA, curveRig_grp )

	i=0
	while i<nbOfJoint:
		jntName = 'jntChain'
		#create group and joint
		cmds.select( cl=1 )	
		OnCurve_jnt = cmds.joint( p=[0,0,0], n=fullname+'_'+str(i)+'_env' )
		onCurve_grp = ''
		onCurveSlave = OnCurve_jnt
			
		#create motion path
		joint_motionPath = cmds.pathAnimation( curvePath, onCurveSlave, fm=1, f=1, fa='x', ua='y', wut='vector', wu=[0,1,0], iu=0, b=0 )
		path_addDoublex = cmds.listConnections( joint_motionPath+'.xCoordinate' )
		path_addDoubley = cmds.listConnections( joint_motionPath+'.yCoordinate' )
		path_addDoublez = cmds.listConnections( joint_motionPath+'.zCoordinate' )
		cmds.delete(path_addDoublex, path_addDoubley, path_addDoublez )
		cmds.connectAttr( joint_motionPath+'.xCoordinate', onCurveSlave+'.tx' )
		cmds.connectAttr( joint_motionPath+'.yCoordinate', onCurveSlave+'.ty' )
		cmds.connectAttr( joint_motionPath+'.zCoordinate', onCurveSlave+'.tz' )
		#delete  anim curve on u val
		jnt_animCrv = cmds.listConnections( joint_motionPath+'.u' )
		cmds.delete( jnt_animCrv )
		#set u val
		cmds.setAttr( joint_motionPath+'.uValue', i*distBtwJoints )
		#set up object on motion path
		cmds.setAttr( joint_motionPath+'.frontAxis', 2 )
		cmds.setAttr( joint_motionPath+'.upAxis', 0 )
		cmds.setAttr( joint_motionPath+'.inverseUp', 1 )
		#save outpout
		jointOnCurve.append( OnCurve_jnt )
		offsetOnCurve.append( onCurve_grp )
		path_motionPaths.append( joint_motionPath )
		#increment i
		i = i+1
		
		if cmds.objExists( 'base_prefs_null.jointVis' ):
			cmds.connectAttr( 'base_prefs_null.jointVis', OnCurve_jnt+'.v' )
		if cmds.objExists( 'base_prefs_null.jointDispType' ):
			cmds.setAttr( OnCurve_jnt+'.overrideEnabled', 1 )
			cmds.connectAttr( 'base_prefs_null.jointDispType', OnCurve_jnt+'.overrideDisplayType' )

	#parent stuff
	cmds.parent( jointOnCurve, curveNT_grp )
	
	#connect stuff to DATA grp
	if not cmds.objExists( curveRig_DATA+'.curvePath' ): 
		cmds.addAttr( curveRig_DATA, ln='curvePath', at='double' )
	if not cmds.objExists( curvePath+'.curvePath' ): 
		cmds.addAttr( curvePath, ln='curvePath', at='double' )
	cmds.connectAttr( curveRig_DATA+'.curvePath', curvePath+'.curvePath', f=1 )

	if not cmds.objExists( curveRig_DATA+'.topNode' ): 
		cmds.addAttr( curveRig_DATA, ln='topNode', at='double' )
	if not cmds.objExists( curveRig_grp+'.topNode' ): 
		cmds.addAttr( curveRig_grp, ln='topNode', at='double' )
	cmds.connectAttr( curveRig_DATA+'.topNode', curveRig_grp+'.topNode', f=1 )

	if not cmds.objExists( curveRig_DATA+'.joint' ): 
		cmds.addAttr( curveRig_DATA, ln='joint', at='double' )
	for jnt in jointOnCurve:
		if not cmds.objExists( jnt+'.joint' ): 
			cmds.addAttr( jnt, ln='joint', at='double' )
		cmds.connectAttr( curveRig_DATA+'.joint', jnt+'.joint', f=1 )

	if not cmds.objExists( curveRig_DATA+'.offset' ): 
		cmds.addAttr( curveRig_DATA, ln='offset', at='double' )
	for grp in offsetOnCurve:
	    if not grp == '':
			if not cmds.objExists( grp+'.offset' ): 
				cmds.addAttr( grp, ln='offset', at='double' )
			cmds.connectAttr( curveRig_DATA+'.offset', grp+'.offset', f=1 )

	if not cmds.objExists( curveRig_DATA+'.pathMotionPath' ): 
		cmds.addAttr( curveRig_DATA, ln='pathMotionPath', at='double' )
	for montion in path_motionPaths:
		if not cmds.objExists( montion+'.pathMotionPath' ): 
			cmds.addAttr( montion, ln='pathMotionPath', at='double' )
		cmds.connectAttr( curveRig_DATA+'.pathMotionPath', montion+'.pathMotionPath', f=1 )
			
	return jointOnCurve


# --------------------------------------------------------------------------
# rem_findVector.py - Python
#
#	Remi CAUZID - remi@cauzid.com
#	Copyright 2013 Remi Cauzid - All Rights Reserved.
# --------------------------------------------------------------------------
#
# DESCRIPTION:
# 	calculate vector value with two points
#
# USAGE:
# 	sys.path.append('/usr/people/remi-c/Documents/script_python')	
# 	from rem_findVector import  rem_findVectorObj
# 	from rem_findVector import  rem_findVectorData
# 	from rem_findVector import  rem_findVectorMix
#
# 	rem_findVector('locator2', 'locator1')
#	rem_findVector([-0.9, 0.0, 0.4], [-5.0, 0.0, 7.1])
#	rem_findVectorMix('locator1', [-5.0, 0.0, 7.1])
#
# AUTHORS:
#	Remi CAUZID - remi@cauzid.com
#	Copyright 2013 Remi Cauzid - All Rights Reserved.
#
# VERSIONS:
#	1.00 - juanary 14, 2013 - Initial Release.
#
# --------------------------------------------------------------------------
#
#	   ______			    _	_____				   _	 _  
#	   | ___ \			   (_)  /  __ \			   	  (_)   | | 
#	   | |_/ /___ _ __ ___  _   | /  \/ __ _ _   _ _____  __| | 
#	   |	# _ \ '_  ` _ \| |  | |	  / _`| | | |_  / |  / _` | 
#	   | |\ \  __/ | | | | | |  | \__/\ (_| | |_| |/ /| | (_| | 
#	   \_| \_\___|_| |_| |_|_|   \____/\__,_|\__,_/___|_|\__,_| 
#														
# --------------------------------------------------------------------------




