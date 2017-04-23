//Maya ASCII 2009 scene
//Name: footControl.ma
//Last modified: Tue, Sep 08, 2009 04:55:00 PM
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
		3 12 2 no 3
		17 -2 -1 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14
		15
		-0.90650843775588574 5.5507632834890673e-017 -0.79721030497758161
		-1.0467457811220569 6.4094693518606145e-017 -0.0090965405327602944
		-0.90650843775588685 5.550763283489071e-017 0.77901722391205797
		0.45582796786059671 3.2047346759303085e-017 1.3559565416300372
		2.3207509512442637 -0.20442230721571875 0.81421038897680631
		5.6816380979481025 0.04147973012676328 1.6398914873769099
		6.9923453953578774 -5.5507632834890697e-017 0.58505408365343026
		7.1325827387240466 -6.4094693518606133e-017 -0.0090965405327582318
		6.9923453953578782 -5.550763283489074e-017 -0.60324716471894724
		5.6816380979481025 0.02372183061507013 -1.6071136154233066
		2.3207509512442637 -0.19544576356909005 -0.96249425225079477
		0.45582796786059826 3.2047346759303023e-017 -1.3741496226955587
		-0.90650843775588574 5.5507632834890673e-017 -0.79721030497758161
		-1.0467457811220569 6.4094693518606145e-017 -0.0090965405327602944
		-0.90650843775588685 5.550763283489071e-017 0.77901722391205797
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
// End of footControl.ma
