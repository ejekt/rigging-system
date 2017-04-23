//Maya ASCII 2009 scene
//Name: zAxisCircle.ma
//Last modified: Tue, Sep 08, 2009 12:15:24 PM
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
createNode nurbsCurve -n "controlShape" -p "control";
	setAttr -k off ".v";
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		0.78361162489122504 0.78361162489122382 -1.2601436025374895e-016
		-1.2643170607829326e-016 1.1081941875543879 -1.7821121732462098e-016
		-0.78361162489122427 0.78361162489122427 -1.26014360253749e-016
		-1.1081941875543879 3.2112695072372299e-016 -5.1641152288041213e-032
		-0.78361162489122449 -0.78361162489122405 1.2601436025374897e-016
		-3.3392053635905195e-016 -1.1081941875543881 1.78211217324621e-016
		0.78361162489122382 -0.78361162489122438 1.2601436025374902e-016
		1.1081941875543879 -5.9521325992805852e-016 9.5717592467817795e-032
		0.78361162489122504 0.78361162489122382 -1.2601436025374895e-016
		-1.2643170607829326e-016 1.1081941875543879 -1.7821121732462098e-016
		-0.78361162489122427 0.78361162489122427 -1.26014360253749e-016
		;
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
select -ne :ikSystem;
	setAttr -s 4 ".sol";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[0].llnk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.lnk[0].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.lnk[1].llnk";
connectAttr ":initialParticleSE.msg" "lightLinker1.lnk[1].olnk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[0].sllk";
connectAttr ":initialShadingGroup.msg" "lightLinker1.slnk[0].solk";
connectAttr ":defaultLightSet.msg" "lightLinker1.slnk[1].sllk";
connectAttr ":initialParticleSE.msg" "lightLinker1.slnk[1].solk";
connectAttr "lightLinker1.msg" ":lightList1.ln" -na;
// End of zAxisCircle.ma
