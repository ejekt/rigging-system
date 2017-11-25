	
def createNodeOnCurve( side, name, number_of_nodes, main_curve, up_curve=None, create_joints=False, parent_joints_to_nodes=True, u_values_override=None, u_as_percentage=False, aim_axis='x', up_axis='y' ):
	'''
	=> This proc will create group(s) on a single curve or more.
	
	How to run:
	=> test_data = CreateNodeOnCurve( '', 'test', 10, 'path_crv' )   
	  
	Options:
	=> If you specify an up curve those groups will use it as up_vector.
	==> If you want to create joint(s) it will add joint(s) driven by the group(s).
	===> If you specify parent_joints_to_nodes = 1 the joint will be parented under the node(s), if 0 joint(s) will be parented under 'jointHierarchy'.
	====> If you specify u_values_override = [0.1,0.2,0.3] the node(s) will use those value(s) as motion path u value(s) otherwise they are uniformly spreaded.
	=====> If you set u_as_percentage = 1 the u values will be used as a pourcentage of the lenth of the curve, otherwise it will be used as the "raw" u value of the curve.
	======> If you specify aim_axis or up_axis you can get different orientation for your objects.
	
	How to get infor back after creation ?
	=> the object created in this proc get attributes added to all of them
	'''
	
	########
	# TEST
	########
	
	if not cmds.objExists(main_curve): 
		cmds.error('the main curve: "'+main_curve+ '" do not exists in your scene (createNodeOnCurve)' )	
	if up_curve: 
		if not cmds.objExists(up_curve): 
			cmds.error('the main curve: "'+up_curve+ '" do not exists in your scene (createNodeOnCurve)' )	
	
	########
	# GET FULL NAME
	########
	
	fullname = name
	if side:
		fullname = side+'_'+name

	########
	# FEW HELPERS
	########
	
	# create a group on a curve using a motion path
	def _createSingleNodeOnSingleCurve( fullname, main_curve, aim_int, inverse_front, up_int, inverse_up, u_as_percentage):
		grp = cmds.group( em=True, n=fullname+'_null' )
		main_curve_shape = cmds.listRelatives( main_curve, shapes=True )[0]
		motion_path = cmds.createNode( 'motionPath', n=fullname+'_MP' )
		cmds.connectAttr( main_curve_shape+'.worldSpace', motion_path+'.geometryPath' )
		cmds.connectAttr( motion_path+'.rotateOrder', grp+'.rotateOrder' )
		cmds.connectAttr( motion_path+'.rotate', grp+'.r' )
		cmds.connectAttr( motion_path+'.allCoordinates', grp+'.translate' )

		cmds.setAttr( motion_path+'.worldUpType', 1 )
		cmds.setAttr( motion_path+'.frontAxis', aim_int )
		cmds.setAttr( motion_path+'.upAxis', up_int )
		cmds.setAttr( motion_path+'.inverseUp', inverse_up )
		cmds.setAttr( motion_path+'.inverseFront', inverse_front )
		cmds.setAttr( motion_path+'.fractionMode', int(u_as_percentage) )

		return motion_path, grp

	# get the info necessary to populate the motion path option from a string axis.
	def _getAxeInfos( stringAxe ):
		vecAxe = [1,0,0]
		reverse = 0
		intAxe = 0
		if '-' in stringAxe:
			reverse = 1
		if stringAxe == '-x':
			vecAxe = [-1,0,0] 
		if 'y' in stringAxe:
			vecAxe = [0,1,0] 
			intAxe = 1
		if stringAxe == '-y':
			vecAxe = [0,-1,0] 
		if 'z' in stringAxe:
			vecAxe = [0,0,1] 
			intAxe = 2
		if stringAxe == '-z':
			vecAxe = [0,0,-1]   
		stringAxe = stringAxe.replace('-','')
		return intAxe, reverse, vecAxe	
		

	########
	# DECLARE
	########

	cv_grps = []
	up_grps = []
	jnts = []
	cv_motion_paths = []
	up_motion_paths = []
	
	aim_int, inverse_front, aim_vec	 = _getAxeInfos( aim_axis )
	up_int, inverse_up, up_vec	 = _getAxeInfos( up_axis )

	########	
	# GET INFOS FROM SCENE
	########
	
	# get distance between groups
	testClose = cmds.getAttr( main_curve+'.form' )
	distance_btw_nodes = 0
	if number_of_nodes > 1:
		if testClose == 0:
			distance_btw_nodes = float(1)/(number_of_nodes-1)
		else:
			distance_btw_nodes = float(1)/(number_of_nodes)
	
	# create rig groups
	top_grp = fullname+'_top_grp'
	if not cmds.objExists( top_grp ):
		top_grp = cmds.group( em=True, n=top_grp )
		
	nt_grp = fullname+'_noTransform'
	if not cmds.objExists( nt_grp ):
		nt_grp = cmds.group( em=True, n=nt_grp )
		cmds.setAttr( nt_grp+'.inheritsTransform', 0 )
		cmds.parent( nt_grp, top_grp )

	u_max_value = cmds.getAttr( main_curve+'.maxValue' )
	# iterating to get the right number of nodes 
	for iterator in xrange(number_of_nodes):
		#set u val
		uVal = (iterator*distance_btw_nodes)*u_max_value
		if u_as_percentage:
			uVal = (iterator*distance_btw_nodes)
		if number_of_nodes == 1:
			uVal = u_max_value/2.0
		
		##############	
		# create main curve groups
		cv_motion_path, cv_grp = _createSingleNodeOnSingleCurve( fullname+'_main'+str(iterator)+'_grp', main_curve, aim_int, inverse_front, up_int, inverse_up, u_as_percentage)
		cv_motion_paths.append(cv_motion_path)
		if u_values_override:
			cmds.setAttr( cv_motion_path+'.uValue', u_values_override[iterator] )
		else:
			cmds.setAttr( cv_motion_path+'.uValue', uVal )
		# if no up curves set up the fisrt motion path to look up
		if iterator == 0 and not up_curve:
			cmds.setAttr( cv_motion_path+'.worldUpVector', *up_vec )
			cmds.setAttr( cv_motion_path+'.worldUpType', 0 )
		
		cv_grps.append(cv_grp)
		cmds.parent( cv_grp, nt_grp )
		
		##############	
		# create up curve groups
		if up_curve:
			up_motion_path, up_grp = _createSingleNodeOnSingleCurve( fullname+'_up'+str(iterator)+'_grp', up_curve, aim_int, inverse_front, up_int, inverse_up, u_as_percentage)
			up_motion_paths.append(up_motion_path)
			if u_values_override:
				cmds.setAttr( up_motion_path+'.uValue', u_values_override[iterator] )
			else:
				cmds.setAttr( up_motion_path+'.uValue', uVal )
			cmds.connectAttr( up_grp+'.worldMatrix', cv_motion_path+'.worldUpMatrix' )

			up_grps.append(up_grp)
			cmds.parent( up_grp, nt_grp )
			
		# if no up curves set up all group to be oriented as previous group
		if not up_curve:
			if iterator > 0:
				cmds.connectAttr( cv_grps[-2]+'.worldMatrix', cv_motion_path+'.worldUpMatrix' )
				cmds.setAttr( cv_motion_path+'.worldUpType', 2 )
				for attr in ['upAxis','frontTwist','upTwist','sideTwist','bank','bankScale','bankLimit']:
					cmds.connectAttr( cv_motion_paths[-2]+'.'+attr, cv_motion_path+'.'+attr )
					cmds.setAttr( cv_motion_path+'.worldUpVector', *up_vec )
					cmds.setAttr( cv_motion_path+'.inverseUp', inverse_up )
					cmds.setAttr( cv_motion_path+'.inverseFront', inverse_front )
				if iterator > 1:
					for attr in ['worldUpType','worldUpVector']: 
						cmds.connectAttr( cv_motion_paths[-2]+'.'+attr, cv_motion_path+'.'+attr )
		
		##############	
		# create joints
		if create_joints:
			cmds.select( cl=True )	
			jnt = cmds.joint( p=[0,0,0], n=fullname+'_'+str(iterator)+'_env' )
			jnts.append(jnt)
			if cmds.objExists( 'base_prefs_null.jointVis' ):
				cmds.connectAttr( 'base_prefs_null.jointVis', +'.v' )
			if cmds.objExists( 'base_prefs_null.jointDispType' ):
				cmds.setAttr( OnCurve_jnt+'.overrideEnabled', 1 )
			if parent_joints_to_nodes == 1:
				cmds.parent( jnt, cv_grp, r=True)
			else:
				cmds.parentConstraint( cv_grp, jnt, mo=False )
				
	##############	
	# gather result and return values
	
	datas = {
			'help':['top_group: parent of all of this','jnts: all joints','cv_grps: all group attached to the crv',
					'up_grps: all groups (attached to the up_crv) used as up vector for the cv_grps',
					'cv_motion_paths: cv_groups motions paths nodes','up_motion_paths: up_groups motions paths nodes'], 
			'top_group':top_grp, 'jnts':jnts, 'cv_grps':cv_grps, 'up_grps':up_grps, 'cv_motion_paths':cv_motion_paths, 
			'up_motion_paths':up_motion_paths 
	}
	return datas
	
	
test = createNodeOnCurve( '', 'a', 10, 'curve8', create_joints=1, u_as_percentage=1  )
