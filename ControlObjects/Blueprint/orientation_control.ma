//Maya ASCII 2009 scene
//Name: orientation_control.ma
//Last modified: Sun, Aug 23, 2009 07:32:05 PM
//Codeset: 1252
requires maya "2009";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya Complete 2009";
fileInfo "version" "2009";
fileInfo "cutIdentifier" "200809110030-734661";
fileInfo "osv" "Microsoft Windows XP Service Pack 2 (Build 2600)\n";
createNode transform -n "orientation_control";
	setAttr -l on -k off ".v";
	setAttr -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr -k off ".sx";
	setAttr -l on -k off ".sy";
	setAttr -l on -k off ".sz";
createNode mesh -n "orientation_controlShape" -p "orientation_control";
	addAttr -ci true -sn "mso" -ln "miShadingSamplesOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "msh" -ln "miShadingSamples" -min 0 -smx 8 -at "float";
	addAttr -ci true -sn "mdo" -ln "miMaxDisplaceOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "mmd" -ln "miMaxDisplace" -min 0 -smx 1 -at "float";
	setAttr -k off ".v";
	setAttr -s 2 ".iog[0].og";
	setAttr ".iog[0].og[0].gcl" -type "componentList" 2 "f[0:10]" "f[28:33]";
	setAttr ".iog[0].og[1].gcl" -type "componentList" 1 "f[11:27]";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 72 ".uvst[0].uvsp[0:71]" -type "float2" 0.62640893 0.064408526 
		0.54828387 0.0076473951 0.45171607 0.00764741 0.37359107 0.064408556 0.34375 0.15625001 
		0.37359107 0.24809146 0.4517161 0.3048526 0.54828393 0.3048526 0.62640893 0.24809144 
		0.65625 0.15625 0.375 0.3125 0.40000001 0.3125 0.42500001 0.3125 0.45000002 0.3125 
		0.47500002 0.3125 0.5 0.3125 0.52499998 0.3125 0.54999995 0.3125 0.57499993 0.3125 
		0.5999999 0.3125 0.62499988 0.3125 0.5 0.68843985 0.375 0.3125 0.40000001 0.3125 
		0.5 0.68843985 0.42500001 0.3125 0.45000002 0.3125 0.47500002 0.3125 0.5 0.3125 0.52499998 
		0.3125 0.54999995 0.3125 0.57499993 0.3125 0.5999999 0.3125 0.62499988 0.3125 0.62640893 
		0.064408526 0.65625 0.15625 0.62640893 0.24809144 0.54828393 0.3048526 0.4517161 
		0.3048526 0.37359107 0.24809146 0.34375 0.15625001 0.37359107 0.064408556 0.45171607 
		0.00764741 0.54828387 0.0076473951 0.375 0 0.625 0 0.625 0.25 0.375 0.25 0.625 0.5 
		0.375 0.5 0.625 0.75 0.375 0.75 0.625 1 0.375 1 0.875 0 0.875 0.25 0.125 0 0.125 
		0.25 0.375 0 0.625 0 0.625 0.25 0.375 0.25 0.625 0.5 0.375 0.5 0.625 0.75 0.375 0.75 
		0.625 1 0.375 1 0.875 0 0.875 0.25 0.125 0 0.125 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 38 ".pt[0:37]" -type "float3"  0.5 0 0 0.5 0 0 0.5 0 0 0.5 
		0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 
		0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 
		0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 0 0 0.5 
		0 0 0.5 0 0 0.5 0 0 0.5 0 0;
	setAttr -s 38 ".vt[0:37]"  0.095147073 0.49463958 -0.069128409 0.036342937 
		0.49463958 -0.11185211 -0.036342964 0.49463958 -0.11185209 -0.095147088 0.49463958 
		-0.069128387 -0.11760826 0.49463958 7.0099975e-009 -0.095147073 0.49463958 0.069128402 
		-0.036342941 0.49463958 0.11185209 0.036342949 0.49463958 0.11185209 0.095147066 
		0.49463958 0.069128387 0.11760824 0.49463958 0 -4.5564983e-009 0.72985607 -4.205998e-010 
		0.095147073 0.069128409 0.49463958 0.036342937 0.11185211 0.49463958 -0.036342964 
		0.11185209 0.49463958 -0.095147088 0.069128387 0.49463958 -0.11760826 -7.0099975e-009 
		0.49463958 -0.095147073 -0.069128402 0.49463958 -0.036342941 -0.11185209 0.49463958 
		0.036342949 -0.11185209 0.49463958 0.095147066 -0.069128387 0.49463958 0.11760824 
		1.0983205e-016 0.49463958 -4.5564983e-009 4.2059997e-010 0.72985607 -0.5 -0.075000018 
		-0.5 0.5 -0.075000018 -0.5 -0.5 -0.074999988 0.5 0.5 -0.074999988 0.5 -0.5 0.075000018 
		0.5 0.5 0.075000018 0.5 -0.5 0.074999988 -0.5 0.5 0.074999988 -0.5 -0.5 -0.5 -0.074999988 
		0.5 -0.5 -0.074999988 -0.5 -0.5 0.075000018 0.5 -0.5 0.075000018 -0.5 0.5 0.074999988 
		0.5 0.5 0.074999988 -0.5 0.5 -0.075000018 0.5 0.5 -0.075000018;
	setAttr -s 64 ".ed[0:63]"  0 1 0 1 2 0 
		2 3 0 3 4 0 4 5 0 5 6 0 
		6 7 0 7 8 0 8 9 0 9 0 0 
		0 10 0 1 10 0 2 10 0 3 10 0 
		4 10 0 5 10 0 6 10 0 7 10 0 
		8 10 0 9 10 0 11 12 0 12 13 0 
		13 14 0 14 15 0 15 16 0 16 17 0 
		17 18 0 18 19 0 19 20 0 20 11 0 
		11 21 0 12 21 0 13 21 0 14 21 0 
		15 21 0 16 21 0 17 21 0 18 21 0 
		19 21 0 20 21 0 22 23 0 24 25 0 
		26 27 0 28 29 0 22 24 0 23 25 0 
		24 26 0 25 27 0 26 28 0 27 29 0 
		28 22 0 29 23 0 30 31 0 32 33 0 
		34 35 0 36 37 0 30 32 0 31 33 0 
		32 34 0 33 35 0 34 36 0 35 37 0 
		36 30 0 37 31 0;
	setAttr -s 34 ".fc[0:33]" -type "polyFaces" 
		f 3 0 11 -11 
		mu 0 3 10 11 21 
		f 3 1 12 -12 
		mu 0 3 11 12 21 
		f 3 2 13 -13 
		mu 0 3 12 13 21 
		f 3 3 14 -14 
		mu 0 3 13 14 21 
		f 3 4 15 -15 
		mu 0 3 14 15 21 
		f 3 5 16 -16 
		mu 0 3 15 16 21 
		f 3 6 17 -17 
		mu 0 3 16 17 21 
		f 3 7 18 -18 
		mu 0 3 17 18 21 
		f 3 8 19 -19 
		mu 0 3 18 19 21 
		f 3 9 10 -20 
		mu 0 3 19 20 21 
		f 10 -10 -9 -8 -7 -6 -5 -4 -3 -2 -1 
		
		mu 0 10 0 9 8 7 6 5 4 3 2 
		1 
		f 3 20 31 -31 
		mu 0 3 22 23 24 
		f 3 21 32 -32 
		mu 0 3 23 25 24 
		f 3 22 33 -33 
		mu 0 3 25 26 24 
		f 3 23 34 -34 
		mu 0 3 26 27 24 
		f 3 24 35 -35 
		mu 0 3 27 28 24 
		f 3 25 36 -36 
		mu 0 3 28 29 24 
		f 3 26 37 -37 
		mu 0 3 29 30 24 
		f 3 27 38 -38 
		mu 0 3 30 31 24 
		f 3 28 39 -39 
		mu 0 3 31 32 24 
		f 3 29 30 -40 
		mu 0 3 32 33 24 
		f 10 -30 -29 -28 -27 -26 -25 -24 -23 -22 -21 
		
		mu 0 10 34 35 36 37 38 39 40 41 42 
		43 
		f 4 40 45 -42 -45 
		mu 0 4 44 45 46 47 
		f 4 41 47 -43 -47 
		mu 0 4 47 46 48 49 
		f 4 42 49 -44 -49 
		mu 0 4 49 48 50 51 
		f 4 43 51 -41 -51 
		mu 0 4 51 50 52 53 
		f 4 -52 -50 -48 -46 
		mu 0 4 45 54 55 46 
		f 4 50 44 46 48 
		mu 0 4 56 44 47 57 
		f 4 52 57 -54 -57 
		mu 0 4 58 59 60 61 
		f 4 53 59 -55 -59 
		mu 0 4 61 60 62 63 
		f 4 54 61 -56 -61 
		mu 0 4 63 62 64 65 
		f 4 55 63 -53 -63 
		mu 0 4 65 64 66 67 
		f 4 -64 -62 -60 -58 
		mu 0 4 59 68 69 60 
		f 4 62 56 58 60 
		mu 0 4 70 58 61 71 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
createNode container -n "orientation_control_container";
	setAttr ".o" -type "string" "Administrator";
	setAttr ".cd" -type "string" "2009/07/28 18:25:27";
createNode lambert -n "m_zAxisBlock";
	setAttr ".c" -type "float3" 0.097775996 0.38538396 0.87300003 ;
createNode lambert -n "m_yAxisBlock";
	setAttr ".c" -type "float3" 0.43241283 1 0.19700003 ;
createNode shadingEngine -n "m_zAxisBlockSG";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode shadingEngine -n "m_yAxisBlockSG";
	setAttr ".ihi" 0;
	setAttr ".ro" yes;
createNode hyperLayout -n "hyperLayout1";
	setAttr ".ihi" 0;
	setAttr -s 6 ".hyp";
	setAttr ".hyp[0].x" 286;
	setAttr ".hyp[0].y" 613;
	setAttr ".hyp[0].isf" yes;
	setAttr ".hyp[1].x" 286;
	setAttr ".hyp[1].y" 93;
	setAttr ".hyp[1].isf" yes;
	setAttr ".hyp[3].x" 497;
	setAttr ".hyp[3].y" 487;
	setAttr ".hyp[3].isf" yes;
	setAttr ".hyp[4].x" 474;
	setAttr ".hyp[4].y" 223;
	setAttr ".hyp[4].isf" yes;
	setAttr ".hyp[5].x" 148;
	setAttr ".hyp[5].y" 353;
	setAttr ".hyp[5].isf" yes;
	setAttr ".hyp[6].x" 148;
	setAttr ".hyp[6].y" 353;
	setAttr ".hyp[6].isf" yes;
	setAttr ".anf" yes;
createNode groupId -n "groupId19";
	setAttr ".ihi" 0;
createNode groupId -n "groupId20";
	setAttr ".ihi" 0;
createNode groupId -n "groupId18";
	setAttr ".ihi" 0;
createNode materialInfo -n "materialInfo1";
createNode materialInfo -n "materialInfo2";
createNode lightLinker -n "lightLinker1";
	setAttr -s 4 ".lnk";
	setAttr -s 4 ".slnk";
select -ne :time1;
	setAttr ".o" 1;
select -ne :renderPartition;
	setAttr -s 4 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 4 ".s";
select -ne :postProcessList1;
	setAttr -s 2 ".p";
select -ne :lightList1;
select -ne :initialShadingGroup;
	setAttr ".ro" yes;
select -ne :initialParticleSE;
	setAttr ".ro" yes;
select -ne :hardwareRenderGlobals;
	setAttr ".ctrs" 256;
	setAttr ".btrs" 512;
select -ne :defaultHardwareRenderGlobals;
	setAttr ".fn" -type "string" "im";
	setAttr ".res" -type "string" "ntsc_4d 646 485 1.333";
select -ne :ikSystem;
	setAttr -s 4 ".sol";
connectAttr "groupId19.id" "orientation_controlShape.iog.og[0].gid";
connectAttr "m_yAxisBlockSG.mwc" "orientation_controlShape.iog.og[0].gco";
connectAttr "groupId20.id" "orientation_controlShape.iog.og[1].gid";
connectAttr "m_zAxisBlockSG.mwc" "orientation_controlShape.iog.og[1].gco";
connectAttr "groupId18.id" "orientation_controlShape.ciog.cog[0].cgid";
connectAttr "hyperLayout1.msg" "orientation_control_container.hl";
connectAttr "m_zAxisBlock.oc" "m_zAxisBlockSG.ss";
connectAttr "orientation_controlShape.iog.og[1]" "m_zAxisBlockSG.dsm" -na;
connectAttr "groupId20.msg" "m_zAxisBlockSG.gn" -na;
connectAttr "m_yAxisBlock.oc" "m_yAxisBlockSG.ss";
connectAttr "orientation_controlShape.iog.og[0]" "m_yAxisBlockSG.dsm" -na;
connectAttr "groupId19.msg" "m_yAxisBlockSG.gn" -na;
connectAttr "m_yAxisBlock.msg" "hyperLayout1.hyp[0].dn";
connectAttr "m_zAxisBlock.msg" "hyperLayout1.hyp[1].dn";
connectAttr "m_yAxisBlockSG.msg" "hyperLayout1.hyp[3].dn";
connectAttr "m_zAxisBlockSG.msg" "hyperLayout1.hyp[4].dn";
connectAttr "orientation_control.msg" "hyperLayout1.hyp[5].dn";
connectAttr "orientation_controlShape.msg" "hyperLayout1.hyp[6].dn";
connectAttr "m_zAxisBlockSG.msg" "materialInfo1.sg";
connectAttr "m_zAxisBlock.msg" "materialInfo1.m";
connectAttr "m_yAxisBlockSG.msg" "materialInfo2.sg";
connectAttr "m_yAxisBlock.msg" "materialInfo2.m";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[0].llnk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.lnk[0].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[1].llnk";
connectAttr ":initialParticleSE.msg" "lightLinker1.lnk[1].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[2].llnk";
connectAttr "m_zAxisBlockSG.msg" "lightLinker1.lnk[2].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[3].llnk";
connectAttr "m_yAxisBlockSG.msg" "lightLinker1.lnk[3].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[0].sllk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.slnk[0].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[1].sllk";
connectAttr ":initialParticleSE.msg" "lightLinker1.slnk[1].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[2].sllk";
connectAttr "m_zAxisBlockSG.msg" "lightLinker1.slnk[2].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[3].sllk";
connectAttr "m_yAxisBlockSG.msg" "lightLinker1.slnk[3].solk";
connectAttr "m_zAxisBlockSG.pa" ":renderPartition.st" -na;
connectAttr "m_yAxisBlockSG.pa" ":renderPartition.st" -na;
connectAttr "m_yAxisBlock.msg" ":defaultShaderList1.s" -na;
connectAttr "m_zAxisBlock.msg" ":defaultShaderList1.s" -na;
connectAttr "lightLinker1.msg" ":lightList1.ln" -na;
connectAttr "groupId18.msg" ":initialShadingGroup.gn" -na;
// End of orientation_control.ma
