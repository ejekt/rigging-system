//Maya ASCII 2009 scene
//Name: locator.ma
//Last modified: Tue, Sep 08, 2009 07:51:58 PM
//Codeset: 1252
requires maya "2009";
requires "stereoCamera" "10.0";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya Complete 2009";
fileInfo "version" "2009";
fileInfo "cutIdentifier" "200809110030-734661";
fileInfo "osv" "Microsoft Windows XP Service Pack 2 (Build 2600)\n";
createNode transform -n "control";
createNode mesh -n "controlShape" -p "control";
	setAttr -k off ".v";
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 12 ".uvst[0].uvsp[0:11]" -type "float2" 0.375 0 0.625 0 
		0.625 0.25 0.375 0.25 0.375 0 0.625 0 0.625 0.25 0.375 0.25 0.375 0 0.625 0 0.625 
		0.25 0.375 0.25;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 12 ".vt[0:11]"  -4.3673398e-007 -1.4887053 0 4.3673398e-007 
		-1.4887053 0 -4.3673398e-007 1.4887053 0 4.3673398e-007 1.4887053 0 1.4887053 -4.3673398e-007 
		0 1.4887053 4.3673398e-007 0 -1.4887053 -4.3673398e-007 0 -1.4887053 4.3673398e-007 
		0 3.3055887e-016 -4.3673398e-007 -1.4887053 3.3055905e-016 4.3673398e-007 -1.4887053 
		-3.3055905e-016 -4.3673398e-007 1.4887053 -3.3055887e-016 4.3673398e-007 1.4887053;
	setAttr -s 12 ".ed[0:11]"  0 1 0 2 3 0 
		0 2 0 1 3 0 4 5 0 6 7 0 
		4 6 0 5 7 0 8 9 0 10 11 0 
		8 10 0 9 11 0;
	setAttr -s 3 ".fc[0:2]" -type "polyFaces" 
		f 4 0 3 -2 -3 
		mu 0 4 0 1 2 3 
		f 4 4 7 -6 -7 
		mu 0 4 4 5 6 7 
		f 4 8 11 -10 -11 
		mu 0 4 8 9 10 11 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
createNode lightLinker -n "lightLinker1";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
select -ne :time1;
	setAttr ".o" 1;
select -ne :renderPartition;
	setAttr -s 2 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 2 ".s";
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
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[0].llnk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.lnk[0].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[1].llnk";
connectAttr ":initialParticleSE.msg" "lightLinker1.lnk[1].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[0].sllk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.slnk[0].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[1].sllk";
connectAttr ":initialParticleSE.msg" "lightLinker1.slnk[1].solk";
connectAttr "lightLinker1.msg" ":lightList1.ln" -na;
connectAttr "controlShape.iog" ":initialShadingGroup.dsm" -na;
// End of locator.ma
