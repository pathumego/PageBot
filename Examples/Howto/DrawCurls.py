# -----------------------------------------------------------------------------
#     Copyright (c) 2016+ Buro Petr van Blokland + Claudia Mens & Font Bureau
#     www.pagebot.io
#
#     P A G E B O T
#
#     Licensed under MIT conditions
#     Made for usage in DrawBot, www.drawbot.com
# -----------------------------------------------------------------------------
#
#     drawSpirals.py
#
from __future__ import division # Make integer division result in float.
import pagebot # Import to know the path of non-Python resources.
W = H = 1000
X = 300
y = 300
N = 64
Sx = 10
Sy = 10
Ex = 10
Ey = 10
D = 1
M = 20
w = W - 2*M
h = H - 2*H

def drawSpiral():
    mx = W/2
    my = H/2
    runs = False
    path = BezierPath()
    for n in range(0, N, 4):
        dx1 = n*Sx*D
        dy1 = n*Sy*D
        dx2 = (n+1)*Sx*D
        dy2 = (n+1)*Sy*D
        dx3 = (n+2)*Sx*D
        dy3 = (n+2)*Sy*D
        dx4 = (n+3)*Sx*D
        dy4 = (n+3)*Sy*D
        dx5 = (n+4)*Sx*D
        dy5 = (n+4)*Sy*D
        if not runs:
            path.moveTo((mx, my-dy1))
        else:
            path.curveTo((mx-dx1*Ex, my-dy1), (mx-dx1, my-dy1), (mx-dx1, my))
            path.curveTo((mx-dx2, my+dy2*Ey), (mx-dx2*Ex, my+dy3), (mx, my+dy3))
            path.curveTo((mx+dx4*Ex, my+dy3), (mx+dx4, my+dy3*Ey), (mx+dx4, my))
            path.curveTo((mx+dx4, my-dy5*Ey), (mx+dx4*Ex, my-dy5), (mx, my-dy5))
        runs = True
    # close the path
    fill(None)
    stroke(0)
    strokeWidth(2)
    drawPath(path)
    
    
Variable([
    #dict(name='ElementOrigin', ui='CheckBox', args=dict(value=False)),
    dict(name='X', ui='Slider', args=dict(minValue=100, value=300, maxValue=1000)),
    dict(name='Y', ui='Slider', args=dict(minValue=100, value=300, maxValue=1000)),
    dict(name='Sx', ui='Slider', args=dict(minValue=2, value=10, maxValue=40)),
    dict(name='Sy', ui='Slider', args=dict(minValue=2, value=10, maxValue=40)),
    dict(name='Ex', ui='Slider', args=dict(minValue=0.01, value=0.5, maxValue=1)),
    dict(name='Ey', ui='Slider', args=dict(minValue=0.01, value=0.5, maxValue=1)),
    dict(name='D', ui='Slider', args=dict(minValue=0.1, value=0.5, maxValue=5)),
], globals())
       
drawSpiral()