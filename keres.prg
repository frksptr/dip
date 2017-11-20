Def Act 1, M_In16(10160) = 1 GoSub *sendpos, S
Def Act 2, M_In16(10320) = 1 GoSub *goCenter
Act 0 = 1
Act 1 = 1
Act 2 = 1
M_out32(10256) = 0 'g10016 d1006
M_out32(10282) = 0 'g10016 d1008
Pstart = P_Curr
MVS Pstart
Pxd = (3,0,0,0,0,0,0,0)(0,0)
Pyd = (0,140,0,0,0,0,0,0)(0,0)
Pnews = (0,0,0,0,0,0,0,0)(0,0)
Pnewe = (0,0,0,0,0,0,0,0)(0,0)
Pnewpos = P_Curr
Pstart = P_Curr
OVRD 2
*scanning
Pn = P_Curr - Pyd
MVS Pn
Pn = P_Curr + Pyd
MVS Pn
GoTO *scanning
*scanNewLine
MVS Pnewe
GOTO *noEdgeFound
*sendpos
Act 0 = 0
Act 1 = 0
Pc = P_Curr
M1 = Pc.X
M2 = Pc.Y
M3 = Pc.Z
M_Out32(10160) = M1 'g10010 d1000
M_Out32(10192) = M2 'g10012 d1002
M_Out32(10224) = M3 'g10014 d1004
M_out32(10256) = 1 'g10016 d1006
*waitNew
IF M_in16(10160) = 1 THEN GOTO *waitNew
IF M_in16(10160) = 2 THEN GOTO *resetAndReturn
IF M_in16(10160) = 0 THEN GOTO *movNewPos
IF M_in16(10640) = 5 Then GOTO *goCenter
*resetAndReturn
M_out32(10256) = 0
Act 0 = 1
Act 1 = 1
Return 0
*movNewPos
Def Act 1, M_In16(10160) = 1 GoSub *sendpos, S
Def Act 2, M_in16(10640) = 1 GoSub *goCenter
Def Act 3, M_In16(10160) = 2 GoSub *scanning
Act 0 = 1
Act 1 = 1
Mxst = M_in16(10192) '502
Myst = M_in16(10224) '504
Mxe = M_in16(10256) '506
Mye = M_in16(10288) '508
Pxs = (1,0,0,0,0,0,0,0)(0,0)*Mxst
Pys = (0,1,0,0,0,0,0,0)(0,0)*Myst
Pxe = (1,0,0,0,0,0,0,0)(0,0)*Mxe
Pye = (0,1,0,0,0,0,0,0)(0,0)*Mye
Pnews = P_Curr + Pxs + Pys
Pnewe = P_Curr + Pxe + Pye
Ovrd 2
MVS Pnews
Ovrd 2
M_out32(10282) = 1
GOTO *scanNewLine
END
*noEdgeFound
HLT
*goCenter
Act 0 = 0
Act 1 = 0
Act 2 = 0
Act 3 = 0
Return 0

Mx1 = M_in16(10480)'520
My1 = M_in16(10512)'522
Mx2 = M_in16(10544)'524
My2 = M_in16(10576)'526

Px1 = (1,0,0,0,0,0,0,0)(0,0)*Mx1
Py1 = (0,1,0,0,0,0,0,0)(0,0)*My1
Px2 = (1,0,0,0,0,0,0,0)(0,0)*Mx2
Py2 = (0,1,0,0,0,0,0,0)(0,0)*My2

P1 = P_Curr+Px1+Py1
P2 = P_Curr+Px2+Py2
MVS P1
*sway
Ovrd 2
MVS P2
MVS P1
goto *sway
HLT