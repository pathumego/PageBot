# -----------------------------------------------------------------------------
#
#     P A G E B O T
#
#     Copyright (c) 2016+ Buro Petr van Blokland + Claudia Mens & Font Bureau
#     www.pagebot.io
#     Licensed under MIT conditions
#     
#     Supporting usage of DrawBot, www.drawbot.com
#     Supporting usage of Flat, https://github.com/xxyxyz/flat
# -----------------------------------------------------------------------------
#
#     AlterGlyphCoordinates.py

import pagebot
from pagebot.contexts import defaultContext as c
from pagebot.fonttoolbox.objects.font import Font

EXPORT_PATH = '_export/TYPETR-Upgrade.pdf'
FONT_PATH = pagebot.getFontPath() + "/fontbureau/AmstelvarAlpha-VF.ttf"

W = H = 1000
# Scale em of 2048 back to page size.
s = 0.5
# Offset of drawing origin
c.translate(100, 100)

# Open the font and get the glyph
f = Font(FONT_PATH)
g = f['H']
# These are the points we have in the H
print g.points
# Get the 4th APoint instance, that has reference back to the glyph.points[p.index]
p = g.points[3]
# This is the point we got.
print p.x, p.y, p.glyph, p.index
# Change the point position. In DrawBot this works interactive while holding cmd-drag.
p.x -= -538
p.y += 308
p.onCurve = False
print g.dirty
g.update()
print g.dirty
c.drawPath(g.path, (0, 0), s)

c.stroke((1, 0, 0), 3)
c.fill(None)
R = 16
for p in g.points:
    c.oval(p.x*s-R/2, p.y*s-R/2, R, R)
    
    