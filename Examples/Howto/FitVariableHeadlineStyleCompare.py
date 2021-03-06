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
#     fitVariableHeadlineStyleCompare.py
#
#     Demo version of pagebot.fonttoolbox.variablefontbuilder.fitVariableWidth, to
#     show usage and format of the answered dictionary.
#     For real use, import the function as:
#     from pagebot.fonttoolbox.variablefontbuilder import fitVariableWidth
#     
import copy
from pagebot import newFS, getRootPath
from pagebot.fonttoolbox.objects.font import Font, getFontByName
from pagebot.fonttoolbox.variablefontbuilder import getVariableFont

ROOT_PATH = getRootPath()
FONT_PATH = ROOT_PATH + '/Fonts/fontbureau/AmstelvarAlpha-VF.ttf'
f = Font(FONT_PATH, install=True) # Get PageBot Font instance of Variable font.

def fitVariableWidth(varFont, s, w, fontSize, condensedLocation, wideLocation, fixedSize=False, 
        tracking=None, rTracking=None):
    u"""Answer the font instance that makes string s width on the given width *w* for the given *fontSize*.
    The *condensedLocation* dictionary defines the most condensed font instance (optionally including the opsz)
    and the *wideLocation* dictionary defines the most wide font instance (optionally including the opsz).
    The string width for s is calculated with both locations and then the [wdth] value is interpolated and iterated
    until the location is found where the string *s* fits width *w). Note that interpolation may not be enough,
    as the width axis may contain non-linear masters.
    If the requested w outside of what is possible with two locations, then interations are performed to 
    change the size. Again this cannot be done by simple interpolation, as the [opsz] also changes the width.
    It one of the axes does not exist in the font, then use the default setting of the font.
    """
    condensedFont = getVariableFont(varFont, condensedLocation)
    condensedFs = newFS(s, style=dict(font=condensedFont.installedName, fontSize=fontSize, tracking=tracking, rTracking=rTracking, textFill=0))
    condensedWidth, _ = textSize(condensedFs)
    wideFont = getVariableFont(varFont, wideLocation)
    wideFs = newFS(s, style=dict(font=wideFont.installedName, fontSize=fontSize, tracking=tracking, rTracking=rTracking, textFill=0))
    wideWidth, _ = textSize(wideFs)
    # Check if the requested with is inside the boundaries of the font width axis
    if w < condensedWidth:
        font = condensedFont
        fs = condensedFs
        location = condensedLocation
    elif w > wideWidth:       
        font = wideFont
        fs = wideFs
        location = wideLocation
    else:
        # Now interpolation the fitting location
        widthRange = wideLocation['wdth'] - condensedLocation['wdth'] 
        location = copy.copy(condensedLocation)
        location['wdth'] += widthRange*(w-condensedWidth)/(wideWidth-condensedWidth)
        font = getVariableFont(varFont, location)
        fs = newFS(s, style=dict(font=font.installedName, fontSize=fontSize, tracking=tracking, rTracking=rTracking, textFill=0))
    return dict(
        condensendFont=condensedFont, condensedFs=condensedFs, condensedWidth=condensedWidth, condensedLocation=condensedLocation,
        wideFont=wideFont, wideFs=wideFs, wideWidth=wideWidth, wideLocation=wideLocation,
        font=font, fs=fs, width=textSize(fs)[0], location=location
    )
    
HEADLINE_SIZE = 36
HEADLINE = """When fonts started a new world."""


MIN_WDTH = 0 # Minimum value of width [wdth] axis. 0 == Normal width
MAX_WDTH = 0.8 # Maximum amount of compressions. Larger value gives more condensed instance of the Variable Font.
assert MIN_WDTH < MAX_WDTH

condensedLocation = dict(opsz=HEADLINE_SIZE, wdth=MAX_WDTH, wght=0.7) # Amount of condensed-ness > 0
wideLocation = dict(opsz=HEADLINE_SIZE, wdth=MIN_WDTH, wght=0.7) # Full default width = 0

W = 600
H = 340
Width = 200
PADDING = 20

INTERACTIVE = False # Interactive or save as animation.
FRAMES = 60
LEADING = 70

def draw(w):
    u"""Draw 3 lines of text: the boundaries of with the width axis and the interpolated width from the slider value.
    If the slider goes of the extremes, then the middle line stops at the boundary width."""
    d = fitVariableWidth(f, HEADLINE, w, HEADLINE_SIZE, condensedLocation, wideLocation)

    minWidth = d['condensedWidth']
    maxWidth = d['wideWidth']
    fixedWidth = minWidth + (maxWidth - minWidth)/2
    dFixed = fitVariableWidth(f, HEADLINE, fixedWidth, HEADLINE_SIZE, condensedLocation, wideLocation)
    
    newPage(W, H)
    y = 2*PADDING
    fill(1)
    rect(0, 0, W, H)
    #
    
    # Draw calculated fitting instance and the two boundary instances.
    text(d['condensedFs'], (PADDING, y+LEADING))
    text(d['fs'], (PADDING, y+2*LEADING))
    text(d['wideFs'], (PADDING, y+3*LEADING))
    
    # Draw the instance choice of 3
    if w < fixedWidth:
        text(d['condensedFs'], (PADDING, y))
    elif w < maxWidth:
        text(dFixed['fs'], (PADDING, y))
    else:
        text(d['wideFs'], (PADDING, y))
        
    fill(0.5)
    fontSize(12)
    text('Variable Font Amstelvar (Maximum width)', (PADDING, y+3*LEADING+40))
    text('Variable Font Amstelvar (Calculated width)', (PADDING, y+2*LEADING+40))
    text('Variable Font Amstelvar (Minimum width)', (PADDING, y+LEADING+40))
    text('Traditional fixed font styles', (PADDING, y+40))
    
    
    # Draw vertical lines, marking the text headline widths and in read the requested column width.
    # Also draw the values of the column width and the [wdth] axis value for that fitting location.
    fill(None)
    stroke(0)
    line((PADDING, PADDING), (PADDING, H-PADDING)) 
    line((PADDING+d['condensedWidth'], PADDING), (PADDING+d['condensedWidth'], H-PADDING)) 
    line((PADDING+d['width'], PADDING), (PADDING+d['width'], H-PADDING)) 
    line((PADDING+d['wideWidth'], PADDING), (PADDING+d['wideWidth'], H-PADDING)) 
    stroke(None)
    fill(0)
    text('%d %0.2f' % (round(d['condensedWidth']), d['condensedLocation']['wdth']), (PADDING+d['condensedWidth']+5, PADDING))
    text('%d %0.2f' % (round(d['width']), d['location']['wdth']), (PADDING+d['width']+5, PADDING))
    text('%d %0.2f' % (round(d['wideWidth']), d['wideLocation']['wdth']), (PADDING+d['wideWidth']+5, PADDING))
    stroke(1, 0, 0)
    line((PADDING+w, PADDING), (PADDING+w, H-PADDING)) 
    stroke(None)
    fill(1, 0, 0)
    text('w=%d' % w, (PADDING+w+5, H-PADDING-5))

if INTERACTIVE:
    Variable([
        #dict(name='ElementOrigin', ui='CheckBox', args=dict(value=False)),
        dict(name='Width', ui='Slider', args=dict(minValue=PADDING, value=200, maxValue=W-2*PADDING)),
    ], globals())

    draw(Width)
else:
    angle = 0
    while angle < 360:
        dx = sin(radians(angle))*0.5+0.5
        draw(160 + (W-2*PADDING-160) * dx)
        angle += 360/FRAMES
    saveImage('_export/fitVariableHeadlineStyleCompare.gif')