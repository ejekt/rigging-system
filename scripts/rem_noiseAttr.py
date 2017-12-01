
# --------------------------------------------------------------------------
# rem_noiseAttr.py - Python
#
#	Remi CAUZID - remi@cauzid.com
#	Copyright 2013 Remi Cauzid - All Rights Reserved.
# --------------------------------------------------------------------------
#
#
# DESCRIPTION:
# 	rem_createNoiseAttr : create noise output on a control and add att on it
# 	rem_connectNoiseToSlave : add to the slave obj his attr value's and the noise output to the attr
#

def rem_createNoiseAttr( ctrlToTweak, ctrl_attrs_to_tweak, nameSuffix ):
    #########
    # create Attributes
    outputAttr = []
    noiseNode =[]
    
    #separator
    cmds.addAttr( ctrlToTweak, ln=nameSuffix+'1', nn='_______', at='enum', en='______' ) 
    cmds.setAttr( ctrlToTweak+'.'+nameSuffix+'1', e=1, k=1, cb=1 )

    for attr_index, slave_attr in enumerate(ctrl_attrs_to_tweak):
        name = nameSuffix+slave_attr
        #name
        cmds.addAttr( ctrlToTweak, ln='noise_'+name, nn='noiseFor', at='enum', en=slave_attr+':' ) 
        cmds.setAttr( ctrlToTweak+'.noise_'+name, e=1, k=1, cb=1 )
        #speed
        cmds.addAttr( ctrlToTweak, ln='speed_'+name, nn='speed', at='double', dv=1, k=1, min=0 )
        time_speed = rem_multiplyReverseDivideOrAddAttr( 'mul', attrOutA='time1.outTime', attrOutB=ctrlToTweak+'.speed_'+name, attrIn=None )
        #speedOffset
        cmds.addAttr( ctrlToTweak, ln='speedOffset_'+name, nn='offset', at='double', dv=attr_index, k=1 )
        time_speed_offset = rem_multiplyReverseDivideOrAddAttr( 'add', attrOutA=time_speed, attrOutB=ctrlToTweak+'.speedOffset_'+name, attrIn=None )
        #amplitude
        cmds.addAttr( ctrlToTweak, ln='amplitude_'+name, nn='amplitude', at='double', dv=1, k=1, min=0 )
        # output
        cmds.addAttr( ctrlToTweak, ln='output'+name, at='double' )
        outputAttr.append( ctrlToTweak+'.output'+name )   
        
        #################
        # create noise output
        noise_node = cmds.createNode( 'noise' )
        cmds.connectAttr( time_speed_offset, noise_node+'.time' )
        noiseOutput_normalized = rem_multiplyReverseDivideOrAddAttr( 'add', attrOutA=noise_node+'.outColorR', attrOutB=-0.5, attrIn=None )
        noise_amplitude = rem_multiplyReverseDivideOrAddAttr( 'mul', attrOutA=noiseOutput_normalized, attrOutB=ctrlToTweak+'.amplitude_'+name, attrIn=None )
        cmds.connectAttr( noise_amplitude, ctrlToTweak+'.output'+name )        
        if attr_index == 0:
            cmds.setAttr( noise_node+'.noiseType', 0 )
            noiseNode.append( noise_node  )
            noise_node_attr = cmds.listAttr( noise_node )
        else:
            for attr in cmds.listAttr( noiseNode[0] ):
                if not attr in ['time','message','binMembership','outColor','outColorR','outColorG','outColorB','outAlpha'] :
                    cmds.connectAttr( noiseNode[0]+'.'+attr, noise_node+'.'+attr, f=1 )

    return outputAttr
    

'''
OLD VERSION
def rem_createNoiseAttr( ctrlToTweak, ctrlAttrToTweak, nameSuffix ):
    #add Time Amplitude 
    cmds.addAttr( ctrlToTweak, ln=nameSuffix+'1', nn='_______', at='enum', en='______' ) 
    cmds.setAttr( ctrlToTweak+'.'+nameSuffix+'1', e=1, k=1, cb=1 )
    cmds.addAttr( ctrlToTweak, ln=nameSuffix+'2', nn=nameSuffix, at='enum', en='Noise:' ) 
    cmds.setAttr( ctrlToTweak+'.'+nameSuffix+'2', e=1, k=1, cb=1 )
    
    attrNoise = ['TIME_'+nameSuffix, 'AMPLITUDE_'+nameSuffix ]
    for a in attrNoise:
        cmds.addAttr( ctrlToTweak, ln=a, at='double' )
        cmds.setAttr( ctrlToTweak+'.'+a, e=1, k=1 )
    cmds.addAttr( ctrlToTweak, ln=nameSuffix+'Secondary', nn='Secondary', at='enum', en='options:' ) 
    cmds.setAttr( ctrlToTweak+'.'+nameSuffix+'Secondary', e=1, k=1, cb=1 )
    
    #time offset and env
    i=0
    attrSecondaryCtrl = []
    for a in ctrlAttrToTweak:
        cmds.addAttr( ctrlToTweak, ln=a+'TimeOffset_'+nameSuffix, at='double', k=1, dv=0 )
        cmds.addAttr( ctrlToTweak, ln=a+'Envelope_'+nameSuffix, at='double', k=1, dv=0 )
        attrSecondaryCtrl.append(a+'TimeOffset_'+nameSuffix)
        attrSecondaryCtrl.append(a+'Envelope_'+nameSuffix)
    
        cmds.setAttr( ctrlToTweak+'.'+a+'TimeOffset_'+nameSuffix, (1*i) )
        cmds.setAttr( ctrlToTweak+'.'+a+'Envelope_'+nameSuffix, 1 )
        i=i+10
    
    #output
    outputAttr = []
    for a in ctrlAttrToTweak:
        cmds.addAttr( ctrlToTweak, ln=nameSuffix+'Noise_'+a+'OUTPUT', at='double' )
        outputAttr.append( nameSuffix+'Noise_'+a+'OUTPUT' )
    
    #creat noise nodes
    noiseNode =[]
    for a in ctrlAttrToTweak:
        noiseNode.append( cmds.createNode( 'noise' ) )
    cmds.setAttr( noiseNode[0]+'.noiseType', 0 )
        
    #connect all attr from first noise to second
    attr = cmds.listAttr( noiseNode[0] )
    for n in noiseNode:
        if n != noiseNode[0]:
            for a in attr:
                if a != 'message' and a != 'binMembership' and a != 'outColor' and a != 'outColorR' and a != 'outColorG' and a != 'outColorB' and a != 'outAlpha' :
                    cmds.connectAttr( noiseNode[0]+'.'+a, n+'.'+a, f=1 )
    
    #add offset in time btw noise for more randomness goodness
    animCurv = cmds.createNode( 'animCurveTL' )
    cmds.setKeyframe( animCurv, t=0, v=0, itt='linear', ott='linear' )
    cmds.setKeyframe( animCurv, t=1, v=1, itt='linear', ott='linear' )
    cmds.selectKey( animCurv, t=(0,1) )
    cmds.setInfinity( poi='cycleRelative', pri='cycleRelative' )
    #curve mul by time speed
    timeMul = cmds.createNode( 'multiplyDivide' )
    cmds.setAttr( timeMul+'.operation', 1 )
    cmds.connectAttr( animCurv+'.output', timeMul+'.input1X' )
    cmds.connectAttr( ctrlToTweak+'.TIME_'+nameSuffix, timeMul+'.input2X' )
    cmds.connectAttr( timeMul+'.outputX', noiseNode[0]+'.time' )
    #connect Time speed
    cmds.connectAttr( ctrlToTweak+'.TIME_'+nameSuffix, animCurv+'.input' )
    #add off btw times in noises
    i=0
    j=0
    k=0
    envMultNodes = []
    for a in attrSecondaryCtrl:
        if i == 0:
            #add offset times in noises
            timeAdd = cmds.createNode( 'plusMinusAverage', n=nameSuffix+str(j)+'TimeOffset_ADD' )
            cmds.setAttr( timeAdd+'.operation', 1 )
            cmds.connectAttr( animCurv+'.output', timeAdd+'.input1D[0]' )
            cmds.connectAttr( ctrlToTweak+'.'+a, timeAdd+'.input1D[1]' )
            cmds.connectAttr( timeAdd+'.output1D', noiseNode[j]+'.time', f=1 )
            j=j+1
        if i == 1:
            #add 0.5 to noise:
            amplitudeMul = cmds.createNode( 'multiplyDivide', n=nameSuffix+str(j)+'amp_MUL' )
            amplitudeAdd = cmds.createNode( 'plusMinusAverage', n=nameSuffix+str(k)+'CenterVal_ADD' )
            cmds.setAttr( amplitudeAdd+'.operation', 2 )
            cmds.connectAttr( noiseNode[k]+'.outColorR', amplitudeAdd+'.input1D[0]' )
            cmds.setAttr( amplitudeAdd+'.input1D[1]', 0.5 )
            cmds.connectAttr( amplitudeAdd+'.output1D', amplitudeMul+'.input2X' )
            cmds.setAttr( amplitudeMul+'.operation', 1 )
            cmds.connectAttr( ctrlToTweak+'.AMPLITUDE_'+nameSuffix, amplitudeMul+'.input1X' )
           #add envelope
            envMul = cmds.createNode( 'multiplyDivide', n=nameSuffix+str(j)+'Env_MUL' )
            cmds.setAttr( timeAdd+'.operation', 1 )
            cmds.connectAttr( amplitudeMul+'.outputX', envMul+'.input2X' )
            cmds.connectAttr( ctrlToTweak+'.'+a, envMul+'.input1X' )
            cmds.connectAttr( envMul+'.outputX', ctrlToTweak+'.'+outputAttr[k], f=1 )
            k=k+1
        i=i+1
        if i == 2:
            i=0
    
    return outputAttr
    
OLD VERSION
def rem_createNoiseAttr( ctrlToTweak, ctrlAttrToTweak, nameSuffix ):
    #add attr on ctrl
    cmds.addAttr( ctrlToTweak, ln=nameSuffix+'1', nn='_______', at='enum', en='______' ) 
    cmds.setAttr( ctrlToTweak+'.'+nameSuffix+'1', e=1, k=1, cb=1 )
    cmds.addAttr( ctrlToTweak, ln=nameSuffix+'2', nn='NOISE', at='enum', en=nameSuffix+':' ) 
    cmds.setAttr( ctrlToTweak+'.'+nameSuffix+'2', e=1, k=1, cb=1 )
    
    attrNoise = ['TIME_'+nameSuffix, 'AMPLITUDE_'+nameSuffix ]
    attrNiceName = ['time', 'amplitude' ]
    for a, nn in zip(attrNoise, attrNiceName):
        cmds.addAttr( ctrlToTweak, ln=a, nn=nn, at='double' )
        cmds.setAttr( ctrlToTweak+'.'+a, e=1, k=1 )
    cmds.addAttr( ctrlToTweak, ln=nameSuffix+'Secondary', nn='Secondary', at='enum', en='options:' ) 
    cmds.setAttr( ctrlToTweak+'.'+nameSuffix+'Secondary', e=1, k=1, cb=1 )
    
    attrSecondaryCtrl = []
    i=0
    for a in ctrlAttrToTweak:
        cmds.addAttr( ctrlToTweak, ln=a+'timeOffset_'+nameSuffix, at='double' )
        cmds.setAttr( ctrlToTweak+'.'+a+'timeOffset_'+nameSuffix, e=1, k=1 )
        cmds.addAttr( ctrlToTweak, ln=a+'Envelope_'+nameSuffix, at='double' )
        cmds.setAttr( ctrlToTweak+'.'+a+'Envelope_'+nameSuffix, e=1, k=1 )
        attrSecondaryCtrl.append(a+'timeOffset_'+nameSuffix)
        attrSecondaryCtrl.append(a+'Envelope_'+nameSuffix)
    
        cmds.setAttr( ctrlToTweak+'.'+a+'timeOffset_'+nameSuffix, (1*i) )
        cmds.setAttr( ctrlToTweak+'.'+a+'Envelope_'+nameSuffix, 1 )
        i=i+10
    
    #set Attr to node
    cmds.setAttr( ctrlToTweak+'.TIME_'+nameSuffix, 0 )
    cmds.setAttr( ctrlToTweak+'.AMPLITUDE_'+nameSuffix, 0 )
    
    #creat noise nodes
    noiseNode =[]
    for a in ctrlAttrToTweak:
        noise = cmds.createNode( 'noise' )
        noiseNode.append(noise)
    cmds.setAttr( noiseNode[0]+'.noiseType', 0 )
        
    #connect all attr from first noise to second
    attr = cmds.listAttr( noiseNode[0] )
    for n in noiseNode:
        if n != noiseNode[0]:
            for a in attr:
                if a != 'message' and a != 'binMembership' and a != 'outColor' and a != 'outColorR' and a != 'outColorG' and a != 'outColorB' and a != 'outAlpha' :
                    cmds.connectAttr( noiseNode[0]+'.'+a, n+'.'+a, f=1 )
    
    #add offset in time btw noise for more randomness goodness
    animCurv = cmds.createNode( 'animCurveTL' )
    cmds.setKeyframe( animCurv, t=0, v=0, itt='linear', ott='linear' )
    cmds.setKeyframe( animCurv, t=1, v=1, itt='linear', ott='linear' )
    cmds.selectKey( animCurv, t=(0,1) )
    cmds.setInfinity( poi='cycleRelative', pri='cycleRelative' )
        #curve mul by time speed
    timeMul = cmds.createNode( 'multiplyDivide' )
    cmds.setAttr( timeMul+'.operation', 1 )
    cmds.connectAttr( animCurv+'.output', timeMul+'.input1X' )
    cmds.connectAttr( ctrlToTweak+'.TIME_'+nameSuffix, timeMul+'.input2X' )
    cmds.connectAttr( timeMul+'.outputX', noiseNode[0]+'.time' )
        #add off btw times in noises
    i=0
    j=0
    k=0
    envMultNodes = []
    for a in attrSecondaryCtrl:
        if i == 0:
            #add offset times in noises
            timeAdd = cmds.createNode( 'plusMinusAverage' )
            cmds.setAttr( timeAdd+'.operation', 1 )
            cmds.connectAttr( animCurv+'.output', timeAdd+'.input1D[0]' )
            cmds.connectAttr( ctrlToTweak+'.'+a, timeAdd+'.input1D[1]' )
            cmds.connectAttr( timeAdd+'.output1D', noiseNode[j]+'.time', f=1 )
            j=j+1
        if i == 1:
            #add envelope
            envMul = cmds.createNode( 'multiplyDivide' )
            cmds.setAttr( timeAdd+'.operation', 1 )
            cmds.connectAttr( noiseNode[k]+'.outColorR', envMul+'.input2X' )
            cmds.connectAttr( ctrlToTweak+'.'+a, envMul+'.input1X' )
            #cmds.connectAttr( envMul+'.outputX', ctrlToTweak+'.'+ctrlAttrToTweak[k] )
            envMultNodes.append(envMul)
            k=k+1
        i=i+1
        if i == 2:
            i=0
    #connect Time speed
    cmds.connectAttr( ctrlToTweak+'.TIME_'+nameSuffix, animCurv+'.input' )
    
    #connect amplitude output
    outputAttr = []
    for a in ctrlAttrToTweak:
        cmds.addAttr( ctrlToTweak, ln=nameSuffix+'Noise_'+a+'OUTPUT', at='double' )
        outputAttr.append( nameSuffix+'Noise_'+a+'OUTPUT' )
    k=0
    for envMul in envMultNodes:
        amplitudeMul = cmds.createNode( 'multiplyDivide' )
        amplitudeAdd = cmds.createNode( 'plusMinusAverage' )
        cmds.setAttr( amplitudeAdd+'.operation', 2 )
        cmds.connectAttr( envMul+'.outputX', amplitudeAdd+'.input1D[0]' )
        cmds.setAttr( amplitudeAdd+'.input1D[1]', 0.5 )
        cmds.connectAttr( amplitudeAdd+'.output1D', amplitudeMul+'.input2X' )
        cmds.setAttr( amplitudeMul+'.operation', 1 )
        cmds.connectAttr( ctrlToTweak+'.AMPLITUDE_'+nameSuffix, amplitudeMul+'.input1X' )
        cmds.connectAttr( amplitudeMul+'.outputX', ctrlToTweak+'.'+outputAttr[k], f=1 )
        k=k+1
    
    # hide show secondary controls
    attrSecondaryCtrl.append(nameSuffix+'Secondary')
    for a in attrSecondaryCtrl: #['tzEnvelope_translate','txtimeOffset_translate','txEnvelope_translate','tytimeOffset_translate','tyEnvelope_translate','tztimeOffset_translate','translateSecondary']:
        cmds.setAttr( ctrlToTweak+'.'+a, e=1, l=1, k=0, cb=0 )
    
    return outputAttr
OLD VERSION
'''

def rem_connectNoiseToSlave( ctrlMaster, ctrlAttrToTweak, noiseOutput, childSlave ):
    i=0
    for a in ctrlAttrToTweak:
        val = cmds.getAttr( childSlave+'.'+a )
        Add = cmds.createNode( 'plusMinusAverage' )
        cmds.setAttr( Add+'.operation', 1 )
        cmds.connectAttr( ctrlMaster+'.'+noiseOutput[i], Add+'.input1D[0]' )
        cmds.setAttr( Add+'.input1D[1]', val )
        cmds.connectAttr( Add+'.output1D', childSlave+'.'+a )
        i=i+1

'''   
ctrlToTweak = 'R_flower05_ctrl'
childSlave = cmds.listRelatives( ctrlToTweak, typ='transform' )
ctrlAttrToTweak = ['tx', 'ty', 'tz']
nameSuffix = "translate"
noiseAttr = rem_createNoiseAttr( ctrlToTweak, ctrlAttrToTweak, nameSuffix )
rem_connectNoiseToSlave( ctrlToTweak, ctrlAttrToTweak, noiseAttr, childSlave[0] )   
'''




# --------------------------------------------------------------------------
# rem_findVector.py - Python
#
#	Remi CAUZID - remi@cauzid.com
#	Copyright 2013 Remi Cauzid - All Rights Reserved.
# --------------------------------------------------------------------------
#
# DESCRIPTION:
# 	rem_createNoiseAttr : create noise output on a control and add att on it
# 	rem_connectNoiseToSlave : add to the slave obj his attr value's and the noise output to the attr
#
# USAGE:
#	ctrlToTweak = 'R_flower05_ctrl'
#	ctrlAttrToTweak = ['tx', 'ty', 'tz']
#	nameSuffix = "translate"
#	noiseAttr = rem_createNoiseAttr( ctrlToTweak, ctrlAttrToTweak, nameSuffix )
#
#	childSlave = cmds.listRelatives( ctrlToTweak, typ='transform' )
#	rem_connectNoiseToSlave( ctrlToTweak, ctrlAttrToTweak, noiseAttr, childSlave[0] )   
#
#
# AUTHORS:
#	Remi CAUZID - remi@cauzid.com
#	Copyright 2013 Remi Cauzid - All Rights Reserved.
#
# VERSIONS:
#	1.00 - mars 25, 2013 - Initial Release.
#
# --------------------------------------------------------------------------
#
#       ______               _    _____                 _     _  
#       | ___ \             (_)  /  __ \               (_)   | | 
#       | |_/ /___ _ __ ___  _   | /  \/ __ _ _   _ _____  __| | 
#       |    # _ \ '_ ` _ \| |  | |    / _` | | | |_  / |/ _` | 
#       | |\ \  __/ | | | | | |  | \__/\ (_| | |_| |/ /| | (_| | 
#       \_| \_\___|_| |_| |_|_|   \____/\__,_|\__,_/___|_|\__,_| 
#                                                        
# --------------------------------------------------------------------------




