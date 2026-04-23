(Exported by FreeCAD)
(Post Processor: linuxcnc_post)
(begin preamble)
G17 G54 G40 G49 G80 G90
G21
O100 sub
#1 = 5
M5
M6 T4
G43 H4
G0 Z20.000
G1 X10.000 Y5.000 F1200.000
O100 endsub
M30
