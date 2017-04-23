//Maya ASCII 2009 scene
//Name: hierarchy_representation.ma
//Last modified: Sun, Aug 23, 2009 07:49:35 PM
//Codeset: 1252
requires maya "2009";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya Complete 2009";
fileInfo "version" "2009";
fileInfo "cutIdentifier" "200809110030-734661";
fileInfo "osv" "Microsoft Windows XP Service Pack 2 (Build 2600)\n";
createNode transform -n "hierarchy_representation";
createNode nurbsSurface -n "hierarchy_representationShape" -p "hierarchy_representation";
	addAttr -ci true -sn "mso" -ln "miShadingSamplesOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "msh" -ln "miShadingSamples" -min 0 -smx 8 -at "float";
	addAttr -ci true -sn "mdo" -ln "miMaxDisplaceOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "mmd" -ln "miMaxDisplace" -min 0 -smx 1 -at "float";
	setAttr -k off ".v";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr ".dvu" 0;
	setAttr ".dvv" 0;
	setAttr ".cpr" 4;
	setAttr ".cps" 4;
	setAttr ".cc" -type "nurbsSurface" 
		3 3 0 2 no 
		6 0 0 0 10 10 10
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		
		44
		0 -0.15672232497824501 -0.15672232497824506
		0 -0.22163883751087782 -3.5945998741709007e-017
		0 -0.15672232497824509 0.15672232497824481
		0 -2.862699950697759e-016 0.22163883751087754
		0 0.15672232497824459 0.15672232497824484
		0 0.22163883751087743 5.5517673144427339e-018
		0 0.15672232497824468 -0.15672232497824484
		0 -1.030019529394196e-016 -0.22163883751087765
		0 -0.15672232497824501 -0.15672232497824506
		0 -0.22163883751087782 -3.5945998741709007e-017
		0 -0.15672232497824509 0.15672232497824481
		0.33333333333333337 -0.15672232497824487 -0.15672232497824504
		0.33333333333333337 -0.22163883751087768 4.8755612298694312e-018
		0.33333333333333337 -0.15672232497824495 0.15672232497824484
		0.33333333333333331 -1.3824025845308839e-016 0.22163883751087757
		0.33333333333333326 0.15672232497824473 0.15672232497824487
		0.33333333333333326 0.22163883751087757 4.6373327286021172e-017
		0.33333333333333326 0.15672232497824481 -0.15672232497824481
		0.33333333333333331 4.502778367726793e-017 -0.22163883751087762
		0.33333333333333337 -0.15672232497824487 -0.15672232497824504
		0.33333333333333337 -0.22163883751087768 4.8755612298694312e-018
		0.33333333333333337 -0.15672232497824495 0.15672232497824484
		0.66666666666666674 -0.1567223249782447 -0.15672232497824498
		0.66666666666666674 -0.22163883751087751 4.5697121201447876e-017
		0.66666666666666674 -0.15672232497824479 0.1567223249782449
		0.66666666666666674 9.7894781635991762e-018 0.22163883751087762
		0.66666666666666663 0.1567223249782449 0.15672232497824493
		0.66666666666666663 0.22163883751087773 8.719488725759961e-017
		0.66666666666666663 0.15672232497824498 -0.15672232497824476
		0.66666666666666674 1.9305752029395549e-016 -0.22163883751087757
		0.66666666666666674 -0.1567223249782447 -0.15672232497824498
		0.66666666666666674 -0.22163883751087751 4.5697121201447876e-017
		0.66666666666666674 -0.15672232497824479 0.1567223249782449
		1 -0.15672232497824456 -0.15672232497824495
		1 -0.22163883751087737 8.651868117302632e-017
		1 -0.15672232497824465 0.15672232497824493
		1 1.5781921478028672e-016 0.22163883751087765
		1 0.15672232497824504 0.15672232497824495
		1 0.22163883751087787 1.2801644722917804e-016
		1 0.15672232497824512 -0.15672232497824473
		1 3.4108725691064299e-016 -0.22163883751087754
		1 -0.15672232497824456 -0.15672232497824495
		1 -0.22163883751087737 8.651868117302632e-017
		1 -0.15672232497824465 0.15672232497824493
		
		;
	setAttr ".nufa" 4.5;
	setAttr ".nvfa" 4.5;
createNode transform -n "hierarchy_arrow_representation" -p "hierarchy_representation";
	setAttr ".r" -type "double3" 0 0 -90 ;
	setAttr ".s" -type "double3" 0.46739519169468152 0.46739519169468152 0.46739519169468152 ;
	setAttr ".rp" -type "double3" 1.1102230246251565e-016 0.5 0 ;
	setAttr ".rpt" -type "double3" 0.49999999999999989 -0.5 0 ;
	setAttr ".sp" -type "double3" 2.3753411339122038e-016 1.0697585445564812 0 ;
	setAttr ".spt" -type "double3" -1.2651181092870475e-016 -0.56975854455648134 0 ;
createNode mesh -n "hierarchy_arrow_representationShape" -p "hierarchy_arrow_representation";
	addAttr -ci true -sn "mso" -ln "miShadingSamplesOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "msh" -ln "miShadingSamples" -min 0 -smx 8 -at "float";
	addAttr -ci true -sn "mdo" -ln "miMaxDisplaceOverride" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "mmd" -ln "miMaxDisplace" -min 0 -smx 1 -at "float";
	setAttr -k off ".v";
	setAttr ".ovdt" 2;
	setAttr ".ove" yes;
	setAttr ".vir" yes;
	setAttr ".vif" yes;
	setAttr ".uvst[0].uvsn" -type "string" "map1";
	setAttr -s 18 ".uvst[0].uvsp[0:17]" -type "float2" 0.67677665 0.073223323 
		0.5 2.9802322e-008 0.32322332 0.073223323 0.25000003 0.25 0.32322332 0.42677668 0.5 
		0.5 0.67677671 0.42677671 0.75 0.25 0.25 0.5 0.3125 0.5 0.375 0.5 0.4375 0.5 0.5 
		0.5 0.5625 0.5 0.625 0.5 0.6875 0.5 0.75 0.5 0.5 1;
	setAttr ".cuvs" -type "string" "map1";
	setAttr ".dcc" -type "string" "Ambient+Diffuse";
	setAttr ".covm[0]"  0 1 1;
	setAttr ".cdvm[0]"  0 1 1;
	setAttr -s 9 ".pt[0:8]" -type "float3"  0.33249366 1.0697585 -0.33249369 
		-2.8027111e-008 1.0697585 -0.4702169 -0.33249369 1.0697585 -0.33249369 -0.4702169 
		1.0697585 -1.4013556e-008 -0.33249369 1.0697585 0.33249366 -2.8027111e-008 1.0697585 
		0.4702169 0.33249369 1.0697585 0.33249369 0.4702169 1.0697585 -1.4013556e-008 2.3753411e-016 
		1.0697585 0;
	setAttr -s 9 ".vt[0:8]"  0.70710671 -0.25 -0.70710671 0 -0.25 -0.99999988 
		-0.70710671 -0.25 -0.70710671 -0.99999988 -0.25 0 -0.70710671 -0.25 0.70710671 0 
		-0.25 0.99999994 0.70710677 -0.25 0.70710677 1 -0.25 0 0 0.25 0;
	setAttr -s 16 ".ed[0:15]"  0 1 0 1 2 0 
		2 3 0 3 4 0 4 5 0 5 6 0 
		6 7 0 7 0 0 0 8 0 1 8 0 
		2 8 0 3 8 0 4 8 0 5 8 0 
		6 8 0 7 8 0;
	setAttr -s 9 ".fc[0:8]" -type "polyFaces" 
		f 8 -8 -7 -6 -5 -4 -3 -2 -1 
		mu 0 8 0 7 6 5 4 3 2 1 
		f 3 0 9 -9 
		mu 0 3 8 9 17 
		f 3 1 10 -10 
		mu 0 3 9 10 17 
		f 3 2 11 -11 
		mu 0 3 10 11 17 
		f 3 3 12 -12 
		mu 0 3 11 12 17 
		f 3 4 13 -13 
		mu 0 3 12 13 17 
		f 3 5 14 -14 
		mu 0 3 13 14 17 
		f 3 6 15 -15 
		mu 0 3 14 15 17 
		f 3 7 8 -16 
		mu 0 3 15 16 17 ;
	setAttr ".cd" -type "dataPolyComponent" Index_Data Edge 0 ;
	setAttr ".cvd" -type "dataPolyComponent" Index_Data Vertex 0 ;
createNode container -n "hierarchy_representation_container";
	setAttr ".o" -type "string" "Administrator";
	setAttr ".cd" -type "string" "2009/07/28 18:18:37";
createNode lambert -n "m_hierarchyRepresentation";
	setAttr ".c" -type "float3" 0.85100001 0.74200565 0.677396 ;
createNode hyperLayout -n "hyperLayout1";
	setAttr ".ihi" 0;
	setAttr -s 6 ".hyp";
	setAttr ".hyp[1].x" 71;
	setAttr ".hyp[1].y" 93;
	setAttr ".hyp[1].isf" yes;
	setAttr ".hyp[3].x" 259;
	setAttr ".hyp[3].y" 93;
	setAttr ".hyp[3].isf" yes;
	setAttr ".anf" yes;
createNode shadingEngine -n "m_hookRepresentation_SG";
	setAttr ".ihi" 0;
	setAttr -s 2 ".dsm";
	setAttr ".ro" yes;
createNode materialInfo -n "materialInfo1";
createNode lightLinker -n "lightLinker1";
	setAttr -s 3 ".lnk";
	setAttr -s 3 ".slnk";
select -ne :time1;
	setAttr ".o" 1;
select -ne :renderPartition;
	setAttr -s 3 ".st";
select -ne :renderGlobalsList1;
select -ne :defaultShaderList1;
	setAttr -s 3 ".s";
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
connectAttr "hyperLayout1.msg" "hierarchy_representation_container.hl";
connectAttr "m_hierarchyRepresentation.msg" "hyperLayout1.hyp[1].dn";
connectAttr "m_hookRepresentation_SG.msg" "hyperLayout1.hyp[3].dn";
connectAttr "hierarchy_representation.msg" "hyperLayout1.hyp[4].dn";
connectAttr "hierarchy_representationShape.msg" "hyperLayout1.hyp[5].dn";
connectAttr "hierarchy_arrow_representation.msg" "hyperLayout1.hyp[6].dn";
connectAttr "hierarchy_arrow_representationShape.msg" "hyperLayout1.hyp[7].dn";
connectAttr "m_hierarchyRepresentation.oc" "m_hookRepresentation_SG.ss";
connectAttr "hierarchy_representationShape.iog" "m_hookRepresentation_SG.dsm" -na
		;
connectAttr "hierarchy_arrow_representationShape.iog" "m_hookRepresentation_SG.dsm"
		 -na;
connectAttr "m_hookRepresentation_SG.msg" "materialInfo1.sg";
connectAttr "m_hierarchyRepresentation.msg" "materialInfo1.m";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[0].llnk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.lnk[0].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[1].llnk";
connectAttr ":initialParticleSE.msg" "lightLinker1.lnk[1].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[2].llnk";
connectAttr "m_hookRepresentation_SG.msg" "lightLinker1.lnk[2].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[0].sllk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.slnk[0].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[1].sllk";
connectAttr ":initialParticleSE.msg" "lightLinker1.slnk[1].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[4].sllk";
connectAttr "m_hookRepresentation_SG.msg" "lightLinker1.slnk[4].solk";
connectAttr "m_hookRepresentation_SG.pa" ":renderPartition.st" -na;
connectAttr "m_hierarchyRepresentation.msg" ":defaultShaderList1.s" -na;
connectAttr "lightLinker1.msg" ":lightList1.ln" -na;
// End of hierarchy_representation.ma
