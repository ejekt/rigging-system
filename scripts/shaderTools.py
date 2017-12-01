import re
import json
import os
import maya.cmds as mc

def _createShader(name, shaderType):

	shader = mc.shadingNode(shaderType,asShader=1,n=(name))

	if name.endswith('_shader'):
		shader = mc.rename(shader, name)
	else:
		shader = mc.rename(shader, name + '_shader')

	SG = mc.sets(shader,renderable=1,noSurfaceShader=1,em=1,name = name + 'SG')
	mc.connectAttr(shader+'.outColor',SG + '.surfaceShader',f=1)

	return(SG,shader)

def getObjectCentric(target=mc.ls('*_geo',), path=True, precision=3, debug=True):
	'''
	user defined attributes are not supported
	# TODO add support for the fullPath flag
	# TODO figure out why the precision option doesn't work
	'''
	data = {}
	for obj in target:

		#if debug:
			#print(obj)

		# find the shaders assigned to each object
		SG = mc.listConnections(obj,type='shadingEngine')
		if SG == None:
			# check the shape node for assignments
			if mc.objectType(obj)== 'transform':
				if path:
					shape = mc.listRelatives(obj, s=True, path=True)
				else:
					shape = mc.listRelatives(obj, s=True)

				if shape != None:
					SG = mc.listConnections(shape[0],type='shadingEngine')

		if SG != None:
			for sg in SG:

				shader = mc.listConnections(sg + '.surfaceShader')[0]
				shaderType = mc.objectType(shader)

				data[shader] = {'type':shaderType}
				# store asignments
				data[shader]['assignments']=mc.sets(sg,q=1)

				compareShader = mc.createNode(shaderType,n=shaderType + '_dummy')
				defaultAttrs = mc.listAttr(compareShader,k=1)

				for attr in defaultAttrs:
					if mc.attributeQuery(attr,n=shader,ex=1):
						attrType = mc.getAttr(compareShader + '.' + attr,type=1)
						shaderData = mc.getAttr(shader + '.' + attr)
						compareData = mc.getAttr(compareShader + '.' + attr)


					if shaderData != compareData:
						if attrType == 'float3':
							shaderData = shaderData[0]

						if type(shaderData) == float:
							shaderData = round(shaderData,precision)

					data[shader][attr] = shaderData

				mc.delete(compareShader)

	return(data)

def write(destFile,data):
	# TODO add support for an append mode
	# TODO warn if the same object is being assigned a shader twice?
	try:
		filehandle = open(destFile, 'w')
		json.dump(data, filehandle, indent=4, sort_keys=True)
		filehandle.close()
	except IOError:
		print "shaderTools.py: IOError when attempting to dump shader info in to json file!"

def read(targFile):
	# read the json file
	fileHandle = open(targFile, 'r')
	data = json.load(fileHandle)
	fileHandle.close()
	return(data)

def apply(data, merge=1,assign=1,pfx=''):
	# TODO test ordering of the dictionary and make sure that any assignments that are to faces
	# happen last

	for shader in data.keys():
		print (shader)
		if shader != 'lambert1':
			new = 0
			shaderType = data[shader]['type']
			SG = ''
			if mc.objExists(shader) == 0:
				SG, shaderNode = _createShader(shader,shaderType)
				new = 1
			else:
				SG = mc.listConnections(shader,type='shadingEngine')[0]
				shaderNode = shader

			# set the attributes on the shader
			if merge or new:
				for attr in data[shader].keys():
					if mc.attributeQuery(attr,n=shaderNode,ex=1):
						attrData = data[shader][attr]
						attrType = mc.getAttr(shaderNode + '.' + attr,type=1)
						try:
							if attrType == 'float':
								mc.setAttr(shaderNode + '.' + attr,attrData)
							elif attrType == 'float3':
								mc.setAttr(shaderNode + '.' + attr,attrData[0], attrData[1], attrData[2],type='double3')
						except RuntimeError:
							pass

			# assign the shaderData
			if assign:
				# TODO assign shaders individually and report errors/missing objects
				for obj in data[shader]['assignments']:
					if pfx != '':
						obj = pfx + obj

					if mc.objExists(obj):
						mc.sets(obj,fe=SG)



def shaders(jsonFile='',mode='import'):
	if mode == 'export':
		nodes = [
			node for node in mc.ls()
			if re.match(".*?(_geo$|_mesh$)", node)
		]
		data = getObjectCentric(target=nodes)
		write(jsonFile, data)

	elif mode == 'import':
		data = read(jsonFile)
		apply(data)
