Def Act 1, M_In16(10160) = 1 GoSub *sendpos
Act 0 = 1
Act 1 = 1
M_out32(10256) = 0 'g10016 d1006
Pxd = (3,0,0,0,0,0,0,0)(0,0)
Pyd = (0,80,0,0,0,0,0)(0,0)

Pnews = (0,0,0,0,0,0,0)(0,0)
Pnewe = (0,0,0,0,0,0,0)(0,0)

Pnewpos = P_Curr
Pstart = P_Curr
OVRD 2
*scanning
Pn = P_Curr - Pyd
MOV Pn
Pn = P_Curr + Pyd
MOV Pn
GoTO *scanning
*scanNewLine
MOV Pnewe
GOTO *noEdgeFound
*sendpos
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
*resetAndReturn
M_out32(10256) = 0
Return 0
*movNewPos
Mxs = M_in32(10162)
Mys = M_in32(10164)

Mxe = M_in32(10166)
Mye = M_in32(10168)

Pxs = (1,0,0,0,0,0,0,0)(0,0)*Mxs
Pys = (0,1,0,0,0,0,0,0)(0,0)*Mys

Pxe = (1,0,0,0,0,0,0,0)(0,0)*Mxe
Pye = (0,1,0,0,0,0,0,0)(0,0)*Mye

Pnews = Pxs + Pys
Pnewe = Pxe + Pye
Act 0 = 0
Act 1 = 0
MOV Pnews
Act 0 = 1
Act 1 = 1
M_out32(10256) = 5
GOTO *scanNewLine
END

*noEdgeFound
HLT