# -*- coding: UTF-8 -*-
# -----------------------------------------------------------------------------
#
#     P A G E B O T
#
#     Copyright (c) 2016+ Buro Petr van Blokland + Claudia Mens & Font Bureau
#     www.pagebot.io
#     Licensed under MIT conditions
#     Made for usage in DrawBot, www.drawbot.com
# -----------------------------------------------------------------------------
#
#     view.py
#
from __future__ import division
from datetime import datetime
from math import atan2, radians, degrees, cos, sin

from drawBot import saveImage, newPage, rect, oval, line, newPath, moveTo, lineTo, drawPath,\
    save, restore, scale, textSize, FormattedString, cmykStroke, text, fill, stroke,\
    strokeWidth, curveTo, closePath

from pagebot import setFillColor, setStrokeColor, newFS
from pagebot.elements.element import Element
from pagebot.style import makeStyle, getRootStyle, NO_COLOR, RIGHT
from pagebot.toolbox.transformer import *

class View(Element):
    u"""A View is just another kind of container, kept by document to make a certain presentation of the page tree."""
    viewId = 'View'
    isView = True

    def __init__(self, w=None, h=None, parent=None, **kwargs):
        Element.__init__(self, parent=parent, **kwargs)
        if not w and self.parent:
            w = self.parent.w
        if not h and self.parent:
            h = self.parent.h
        self.w = w
        self.h = h
        self._initializeControls()
        self.setControls()
        # List of collected elements that need to draw their info on top of the main drawing,
        self.elementsNeedingInfo = {}
        self._isDrawn = False # Automatic call self.drawPages if export is called without drawing.

    def _initializeControls(self):
        self.showElementInfo = False
        self.showElementFrame = False
        self.showElementOrigin = False
        self.showElementDimensions = False # TODO: Does not work if there is view padding.
        self.showMissingElementRect = True
        # Grid stuff
        self.showGrid = False
        self.showGridColumns = False
        self.showBaselineGrid = False
        # Document/page stuff
        self.showPageCropMarks = False
        self.showPageRegistrationMarks = False
        self.showPagePadding = False
        self.showPageFrame = False
        self.showPageNameInfo = False
        self.showPageMetaInfo = False
        # TextBox stuff
        self.showTextBoxIndex = False # Show the line index number on the left side.
        self.showTextBoxY = False # Show the realtic y-position value if text lines on right side.
        self.showTextBoxLeading = False # Show distance of leading on the right side.
        self.showTextBoxBaselines = False
        # Flow stuff
        self.showFlowConnections = False
        self.showTextOverflowMarker = True
        # Image stuff
        self.showImageReference = False
        # Spread stuff
        self.showSpreadMiddleAsGap = True # Show the spread with single crop marks. False glues pages togethers as in real spread.
        # CSS flags
        self.cssVerbose = True # Adds information comments with original values to CSS export.

    def setControls(self):
        u"""Inheriting views can redefine to alter showing parameters."""
        pass

    MIN_PADDING = 20 # Minimum padding needed to show meta info. Otherwise truncated to 0 and not showing meta info.

    def draw(self, origin, ignoredView):
        u"""This method is called is the view is used as a placable element inside
        another element, such as a Page or Template. """
        p = pointOffset(self.oPoint, origin)
        p = self._applyScale(p)    
        px, py, _ = p = self._applyAlignment(p) # Ignore z-axis for now.

        if self.drawBefore is not None: # Call if defined
            self.drawBefore(self, p, self)

        self.drawElementFrame(self, p)
        for page in self.elements:
            self.drawPageMetaInfo(page, p)
            page.draw((px, py), self)

        if self.drawAfter is not None: # Call if defined
            self.drawAfter(self, p, self)

        self._restoreScale()
        #view.drawElementMetaInfo(self, origin)

    def drawPages(self, pageSelection=None):
        u"""Draw the selected pages. pageSelection is an optional set of y-pageNumbers to draw."""
        doc = self.parent

        w, h, _ = doc.getMaxPageSizes(pageSelection)
        for pn, pages in doc.getSortedPages():
            #if pageSelection is not None and not page.y in pageSelection:
            #    continue
            # Create a new DrawBot viewport page to draw template + page, if not already done.
            # In case the document is oversized, then make all pages the size of the document, so the
            # pages can draw their crop-marks. Otherwise make DrawBot pages of the size of each page.
            # Size depends on the size of the larges pages + optional decument padding.
            page = pages[0] # TODO: make this work for pages that share the same page number
            pw, ph = w, h  # Copy from main (w, h), since they may be altered.
            
            if self.pl > self.MIN_PADDING and self.pt > self.MIN_PADDING and self.pb > self.MIN_PADDING and self.pr > self.MIN_PADDING:
                pw += self.pl + self.pr
                ph += self.pt + self.pb
                if self.originTop:
                    origin = self.pl, self.pt, 0
                else:
                    origin = self.pl, self.pb, 0
            else:
                pw = page.w # No padding defined, follow the size of the page.
                ph = page.h
                origin = (0, 0, 0)

            newPage(pw, ph) #  Make page in DrawBot of self size, actual page may be smaller if showing cropmarks.
            # View may have defined a background
            if self.style.get('fill') is not None:
                setFillColor(self.style['fill'])
                rect(0, 0, pw, ph)

            if self.drawBefore is not None: # Call if defined
                self.drawBefore(page, origin, self)

            # Use the (docW, docH) as offset, in case cropmarks need to be displayed.
            page.draw(origin, self)

            if self.drawAfter is not None: # Call if defined
                self.drawAfter(page, origin, self)

            # Self.infoElements now may have collected elements needed info to be drawn, after all drawing is done.
            # So the info boxes don't get covered by regular page content.
            for e in self.elementsNeedingInfo.values():
                self._drawElementsNeedingInfo()

    def export(self, fileName, pageSelection=None, multiPage=True):
        u"""Export the document to fileName for all pages in sequential order.
        If pageSelection is defined, it must be a list with page numbers to
        export. This allows the order to be changed and pages to be omitted.
        The fileName can have extensions ['pdf', 'svg', 'png', 'gif'] to direct
        the type of drawing and export that needs to be done.

        The multiPage value is passed on to the DrawBot saveImage call.
        document.export(...) is the most common way to export documents. But in
        special cases, there is not straighforward (or sequential) export of
        pages, e.g. when generating HTML/CSS. In that case use
        MyBuilder(document).export(fileName), the builder is responsible to
        query the document, pages, elements and styles.
        """
        if not self._isDrawn:
            self.drawPages(pageSelection=pageSelection)
            self._isDrawn = True

        # If rootStyle['frameDuration'] is set and saving as movie or animated gif,
        # then set the global frame duration.
        frameDuration = self.css('frameDuration')

        folder = path2ParentPath(fileName)

        if not os.path.exists(folder):
            os.mkdir(folder)

        if frameDuration is not None and (fileName.endswith('.mov') or fileName.endswith('.gif')):
            frameDuration(frameDuration)

        # Select other than standard DrawBot export builders here.
        # TODO: Take build into separte htmlView, instead of split by extension
        # TODO: Show be more generic if number of builders grows.
        # TODO: Build multiple pages, now only doc[0] is supported.
        saveImage(fileName, multipage=multiPage)

    #   D R A W I N G  P A G E  M E T A  I N F O

    def drawPageMetaInfo(self, page, origin):
        self.drawPageFrame(page, origin)
        self.drawPagePadding(page, origin)
        self.drawPageNameInfo(page, origin)
        self.drawPageRegistrationMarks(page, origin)
        self.drawPageCropMarks(page, origin)
        self.drawGrid(page, origin)
        self.drawBaselineGrid(page, origin)

    def drawPageFrame(self, page, origin):
        u"""Draw the page frame if the the flag is on and  if there ie padding enough to show other meta info.
        Otherwise the padding is truncated to 0: no use to draw the frame."""
        if self.showPageFrame and \
                self.pl > self.MIN_PADDING and self.pr > self.MIN_PADDING and \
                self.pt > self.MIN_PADDING and self.pb > self.MIN_PADDING:
            fill(None)
            stroke(0, 0, 1)
            strokeWidth(0.5)
            rect(origin[0], origin[1], page.w, page.h)
            #page.drawFrame(origin, self)

    def drawPagePadding(self, page, origin):
        u"""Draw the page frame of its current padding."""
        pt, pr, pb, pl = page.padding
        if self.showPagePadding and (pt or pr or pb or pl):
            p = pointOffset(page.oPoint, origin)
            p = page._applyScale(p)
            px, py, _ = page._applyAlignment(p) # Ignore z-axis for now.
            fill(None)
            stroke(0, 0, 1)
            strokeWidth(0.5)
            if page.originTop:
                rect(px+pr, py+page.h-pb, page.w-pl-pr, page.h-pt-pb)
            else:
                rect(px+pr, py+pb, page.w-pl-pr, page.h-pt-pb)

    def drawPageNameInfo(self, page, origin):
        u"""Draw additional document information, color markers, page number, date, version, etc.
        outside the page frame, if drawing crop marks."""
        if self.showPageNameInfo:
            bleed = self.css('bleed')
            cms = self.css('viewCropMarkSize') - bleed
            fontSize = self.css('viewPageNameFontSize')
            dt = datetime.datetime.now()
            d = dt.strftime("%A, %d. %B %Y %I:%M%p")
            s = 'Page %s | %s | %s' % (page.parent.getPageNumber(page), d, page.parent.title or 'Untitled')
            if page.name:
                s += ' | ' + page.name
            fs = FormattedString(s, font=self.css('viewPageNameFont'), fill=0, fontSize=fontSize)
            text(fs, (self.pl + bleed, self.pb + page.h + cms - fontSize*2)) # Draw on top of page.

    #   D R A W I N G  F L O W S

    def drawFlowConnections(self, e, origin):
        u"""If rootStyle.showFlowConnections is True, then draw the flow connections
        on the page, using their stroke/width settings of the style."""
        px, py, _ = pointOffset(self.point, origin) # Ignore z-axis for now.

        if self.showFlowConnections:
            for seq in e.getFlows().values():
                # For all the flow sequences found in the page, draw flow arrows at offset (ox, oy)
                # This offset is defined by optional
                tbStart = e.getElement(seq[0].eId)
                startX = tbStart.x
                startY = tbStart.y
                for tbTarget in seq[1:]:
                    tbTarget = e.getElement(tbTarget.eId)
                    targetX = tbTarget.x
                    targetY = tbTarget.y
                    self.drawArrow(e, px+startX, py+startY+tbStart.h, px+startX+tbStart.w, py+startY, -1)
                    self.drawArrow(e, px+startX+tbStart.w, py+startY, px+targetX, py+targetY+tbTarget.h, 1)
                    tbStart = tbTarget
                    startX = targetX
                    startY = targetY
                self.drawArrow(e, px+startX, py+startY+tbStart.h, px+startX+tbStart.w, py+startY, -1)

                if e != e.parent.getLastPage():
                    # Finalize with a line to the start, assuming it is on the next page.
                    tbTarget = e.getElement(seq[0].eId)
                    self.drawArrow(e, px+startX+tbStart.w, py+startY, px+tbTarget.x, py+tbTarget.y+tbTarget.h-e.h, 1)

    def drawArrow(self, e, xs, ys, xt, yt, onText=1, startMarker=False, endMarker=False, fms=None, fmf=None,
            fill=None, stroke=None, strokeWidth=None):
        u"""Draw curved arrow marker between the two points.
        TODO: Add drawing of real arrow-heads, rotated in the right direction."""
        if fms is None:
            fms = self.css('viewFlowMarkerSize')
        if fmf is None:
            fmf or self.css('viewFlowCurvatureFactor')

        if stroke is None:
            if onText == 1:
                stroke = self.css('viewFlowConnectionStroke2', NO_COLOR)
            else:
                stroke = self.css('viewFlowConnectionStroke1', NO_COLOR)
        if strokeWidth is None:
            strokeWidth = self.css('viewFlowConnectionStrokeWidth', 0.5)

        setStrokeColor(stroke, strokeWidth)
        if startMarker:
            if fill is None:
                fill = self.css('viewFlowMarkerFill', NO_COLOR)
            setFillColor(fill)
            oval(xs - fms, ys - fms, 2 * fms, 2 * fms)

        xm = (xt + xs)/2
        ym = (yt + ys)/2
        xb1 = xm + onText * (yt - ys) * fmf
        yb1 = ym - onText * (xt - xs) * fmf
        xb2 = xm - onText * (yt - ys) * fmf
        yb2 = ym + onText * (xt - xs) * fmf
        # Arrow head position
        arrowSize = 12
        arrowAngle = 0.4
        angle = atan2(xt-xb2, yt-yb2)
        hookedAngle = radians(degrees(angle)-90)
        ax1 = xt - cos(hookedAngle+arrowAngle) * arrowSize
        ay1 = yt + sin(hookedAngle+arrowAngle) * arrowSize
        ax2 = xt - cos(hookedAngle-arrowAngle) * arrowSize
        ay2 = yt + sin(hookedAngle-arrowAngle) * arrowSize
        newPath()
        setFillColor(None)
        moveTo((xs, ys))
        curveTo((xb1, yb1), (xb2, yb2), ((ax1+ax2)/2, (ay1+ay2)/2)) # End in middle of arrow head.
        drawPath()

        #  Draw the arrow head.
        newPath()
        setFillColor(stroke)
        setStrokeColor(None)
        moveTo((xt, yt))
        lineTo((ax1, ay1))
        lineTo((ax2, ay2))
        closePath()
        drawPath()

        if endMarker:
            setFillColor(self.css('viewFlowMarkerFill', NO_COLOR))
            oval(xt - fms, yt - fms, 2 * fms, 2 * fms)

    #   D R A W I N G  E L E M E N T

    def drawElementFrame(self, e, origin):
        if self.showElementFrame:
            e.draw(origin, self, False) # Don't recursively draw children.

    def drawElementMetaInfo(self, e, origin):
        self.drawElementInfo(e, origin)
        self.drawElementOrigin(e, origin)

    def drawElementInfo(self, e, origin):
        u"""For debugging this will make the elements show their info. The css flag "showElementOrigin"
        defines if the origin marker of an element is drawn. Collect the (e, origin), so we can later
        draw all info, after the main drawing has been done."""
        if not e.eId in self.elementsNeedingInfo:
            self.elementsNeedingInfo[e.eId] = (e, origin)

    def _drawElementsNeedingInfo(self):
        for e, origin in self.elementsNeedingInfo.values():
            p = pointOffset(e.oPoint, origin)
            p = e._applyScale(p)
            px, py, _ = e._applyAlignment(p) # Ignore z-axis for now.
            if self.showElementInfo:
                # Draw box with element info.
                fs = newFS(e.getElementInfoString(), style=dict(font=self.css('viewInfoFont'),
                    fontSize=self.css('viewInfoFontSize'), leading=self.css('viewInfoLeading'), textFill=0.1))
                tw, th = textSize(fs)
                Pd = 4 # Padding in box and shadow offset.
                tpx = px - Pd/2 # Make info box outdent the element. Keeping shadow on the element top left corner.
                tpy = py + e.h - th - Pd
                # Tiny shadow
                setFillColor((0.3, 0.3, 0.3, 0.5))
                setStrokeColor(None)
                rect(tpx+Pd/2, tpy, tw+2*Pd, th+1.5*Pd)
                # Frame
                setFillColor(self.css('viewInfoFill'))
                setStrokeColor(0.3, 0.25)
                rect(tpx, tpy, tw+2.5*Pd, th+1.5*Pd)
                text(fs, (tpx+Pd, tpy+th))
                e._restoreScale()

            if self.showElementDimensions:
                # TODO: Make separate arrow functio and better positions
                # Draw width and height measures
                setFillColor(None)
                setStrokeColor(0, 0.25)
                S = self.css('viewInfoOriginMarkerSize', 4)
                x1, y1, x2, y2 = px + e.left, py + e.bottom, e.right, e.top

                # Horizontal measure
                line((x1, y1 - 0.5*S), (x1, y1 - 3.5*S))
                line((x2, y1 - 0.5*S), (x2, y1 - 3.5*S))
                line((x1, y1 - 2*S), (x2, y1 - 2*S))
                # Arrow heads
                line((x1, y1 - 2*S), (x1+S, y1 - 1.5*S))
                line((x1, y1 - 2*S), (x1+S, y1 - 2.5*S))
                line((x2, y1 - 2*S), (x2-S, y1 - 1.5*S))
                line((x2, y1 - 2*S), (x2-S, y1 - 2.5*S))

                fs = newFS(asFormatted(x2 - x1), style=dict(font=self.css('viewInfoFont'),
                    fontSize=self.css('viewInfoFontSize'), leading=self.css('viewInfoLeading'), textFill=0.1))
                tw, th = textSize(fs)
                text(fs, ((x2 + x1)/2 - tw/2, y1-1.5*S))

                # Vertical measure
                line((x2+0.5*S, y1), (x2+3.5*S, y1))
                line((x2+0.5*S, y2), (x2+3.5*S, y2))
                line((x2+2*S, y1), (x2+2*S, y2))
                # Arrow heads
                line((x2+2*S, y2), (x2+2.5*S, y2-S))
                line((x2+2*S, y2), (x2+1.5*S, y2-S))
                line((x2+2*S, y1), (x2+2.5*S, y1+S))
                line((x2+2*S, y1), (x2+1.5*S, y1+S))

                fs = newFS(asFormatted(y2 - y1), style=dict(font=self.css('viewInfoFont'),
                    fontSize=self.css('viewInfoFontSize'), leading=self.css('viewInfoLeading'), textFill=0.1))
                tw, th = textSize(fs)
                text(fs, (x2+2*S-tw/2, (y2+y1)/2))

    def drawElementOrigin(self, e, origin):
        px, py, _ = pointOffset(e.oPoint, origin)
        S = self.css('viewInfoOriginMarkerSize', 4)
        if self.showElementOrigin:
            # Draw origin of the element
            setFillColor((0.5,0.5,0.5,0.1)) # Transparant fill, so we can see the marker on dark backgrounds.
            setStrokeColor(0, 0.25)
            oval(px-S, py-S, 2*S, 2*S)
            line((px-S, py), (px+S, py))
            line((px, py-S), (px, py+S))

        if self.showElementDimensions:
            fs = newFS(point2S(e.point3D), style=dict(font=self.css('viewInfoFont'),
                fontSize=self.css('viewInfoFontSize'), leading=self.css('viewInfoLeading'), textFill=0.1))
            w, h = textSize(fs)
            text(fs, (px - w/2, py + S*1.5))

    def drawMissingElementRect(self, e, origin):
        u"""When designing templates and pages, this will draw a filled rectangle on the element
        bounding box (if self.css('missingElementFill' is defined) and a cross, indicating
        that this element has missing content (as in unused image frames).
        Only draw if self.css('showGrid') is True."""
        if self.showMissingElementRect:

            p = pointOffset(e.point, origin)
            p = e._applyOrigin(p)
            p = e._applyScale(p)
            px, py, _ = e._applyAlignment(p) # Ignore z-axis for now.
            self.setShadow()

            sMissingElementFill = self.css('viewMissingElementFill', NO_COLOR)
            if sMissingElementFill is not NO_COLOR:
                setFillColor(sMissingElementFill)
                setStrokeColor(None)
                rect(px, py, self.w, self.h)
            # Draw crossed rectangle.
            setFillColor(None)
            setStrokeColor(0, 0.5)
            rect(px, py, self.w, self.h)
            newPath()
            moveTo((px, py))
            lineTo((px + self.w, py + self.h))
            moveTo((px + self.w, py))
            lineTo((px, py + self.h))
            drawPath()

            self.resetShadow()
            e._restoreScale()

    #   S H A D O W

    def setShadow(self, e):
        u"""Set the DrawBot graphics state for shadow if all parameters are set. Pair the call of this
        method with self._resetShadow()"""
        shadowOffset = e.css('shadowOffset') # Use DrawBot graphic state switch on shadow mode.
        if shadowOffset is not None:
            save() # DrawBot graphics state push
            shadowBlur = e.css('shadowBlur') # Should be integer.
            shadowFill = e.css('shadowFill') # Should be color, different from NO_COLOR
            shadow(shadowOffset, shadowBlur, shadowFill)

    def resetShadow(self, e):
        u"""Restore the shadow mode of DrawBot. Should be paired with call self._setShadow()."""
        if e.css('shadowOffset') is not None:
            restore() # DrawBot graphics state pop.

    #    G R I D

    def drawGrid(self, e, origin):
        u"""Draw grid of lines and/or rectangles if colors are set in the style.
        Normally px and py will be 0, but it's possible to give them a fixed offset."""
        # Drawing the grid as squares.
        if not self.showGrid:
            return
        #if not self.showGridColumns or not self.showGrid:
        #    return
        p = pointOffset(e.oPoint, origin)
        p = self._applyScale(p)
        px, py, _ = e._applyAlignment(p) # Ignore z-axis for now.

        sGridFill = e.css('viewGridFill', NO_COLOR)
        gutterW = e.gw # Gutter width
        gutterH = e.gh # Gutter height
        columnWidth = e.cw # Column width
        columnHeight = e.ch # Column height
        padL = e.pl # Padding left
        padT = e.pt # Padding top
        padR = e.pr # padding right
        padB = e.pb # padding bottom
        padW = e.pw # Padding width
        padH = e.ph # Padding height

        w = e.w
        h = e.h

        if e.isRight():
            ox = px + padR
        else:
            ox = px + padL
        oy = py + padB

        if self.showGrid and self.css('viewGridStroke', NO_COLOR) is not NO_COLOR:
            setFillColor(None)
            setStrokeColor(self.css('viewGridStroke', NO_COLOR), self.css('viewGridStrokeWidth'))
            newPath()
            for cx, cw in e.getGridColumns():
                moveTo((ox+cx, oy))
                lineTo((ox+cx, oy + padH))
                moveTo((ox+cx + cw, oy))
                lineTo((ox+cx + cw, oy + padH))
            for cy, ch in e.getGridRows():
                moveTo((ox, oy+cy))
                lineTo((ox + padW, oy+cy))
                moveTo((ox, oy+cy + ch))
                lineTo((ox + padW, oy+cy + ch))
            drawPath()
                #text(fs+repr(index), (ox + M * 0.3, oy + M / 4))

        """
        if self.showGridColumns and sGridFill is not NO_COLOR:
            setFillColor(sGridFill)
            setStrokeColor(None)
            ox = px + padL
            while ox < w - padR - columnWidth:
                oy = h - padT - columnHeight - gutterH
                while oy >= 0:
                    rect(ox, oy + gutterH, columnWidth, columnHeight)
                    oy -= columnHeight + gutterH
                ox += columnWidth + gutterW

        # Drawing the grid as lines.
        if self.showGrid and self.css('viewGridStroke', NO_COLOR) is not NO_COLOR:
            setFillColor(None)
            setStrokeColor(self.css('viewGridStroke', NO_COLOR), self.css('viewGridStrokeWidth'))
            # TODO: DrawBot align and fill don't work properly now.
            M = 16
            fs = newFS('', self, dict(font='Verdana', xTextAlign=RIGHT, fontSize=M/2,
                stroke=None, textFill=self.css('viewGridStroke')))
            ox = px + padL
            for cw, gutter in e.getGridX(): # Answer the sequence or relative (column, gutter) measures.
                    newPath()
                    moveTo((ox, py))
                    lineTo((ox, py + h))
                    moveTo((ox + columnWidth, py))
                    lineTo((ox + columnWidth, py + h))
                    drawPath()
                    text(fs+repr(index), (ox + M * 0.3, oy + M / 4))
                    index += 1
                    ox += columnWidth + gutterW
            index = 0
            while oy > py:
                newPath()
                moveTo((px, oy))
                lineTo((px + w, oy))
                moveTo((px, oy - columnHeight))
                lineTo((px+w, oy - columnHeight))
                drawPath()
                text(fs + repr(index), (px + padL - M / 2, oy - M * 0.6))
                index += 1
                oy -= columnHeight + gutterH
        """

    def drawBaselineGrid(self, e, origin):
        u"""Draw baseline grid if line color is set in the style.
        TODO: Make fixed values part of calculation or part of grid style.
        Normally px and py will be 0, but it's possible to give them a fixed offset."""
        if not self.showBaselineGrid:
            return
        p = pointOffset(self.oPoint, origin)
        p = self._applyScale(p)
        px, py, _ = self._applyAlignment(p) # Ignore z-axis for now.
        M = 16
        startY = e.css('baselineGridStart')
        if startY is None:
            startY = e.pt # Otherwise use the top padding as start Y.
        oy = e.h - startY#- py
        line = 0
        # Format of line numbers.
        # TODO: DrawBot align and fill don't work properly now.
        fs = newFS('', self, dict(font=e.css('fallbackFont','Verdana'), xTextAlign=RIGHT,
            fontSize=M/2, stroke=None, textFill=e.css('gridStroke')))
        while oy > e.pb or 0:
            setFillColor(None)
            setStrokeColor(e.css('baselineGridStroke', NO_COLOR), e.css('gridStrokeWidth'))
            newPath()
            moveTo((px + e.pl, py + oy))
            lineTo((px + e.w - e.pr, py + oy))
            drawPath()
            text(fs + repr(line), (px + e.pl - 2, py + oy - e.pl * 0.6))
            text(fs + repr(line), (px + e.w - e.pr - 8, py + oy - e.pr * 0.6))
            line += 1 # Increment line index.
            oy -= e.css('baselineGrid') # Next vertical line position of baseline grid.

    #    M A R K E R S

    def _drawPageRegistrationMark(self, page, origin, cmSize, cmStrokeWidth, vertical):
        u"""Draw registration mark as position x, y."""
        x, y = origin
        if vertical:
            dx = cmSize/2
            dy = cmSize
        else:
            dx = cmSize
            dy = cmSize/2
        fill(None)
        cmykStroke(1,1,1,1)
        strokeWidth(cmStrokeWidth)
        newPath()
        # Registration circle
        oval(x - cmSize/4, y - cmSize/4, cmSize/2, cmSize/2)
        # Registration cross, in length of direction.
        moveTo((x - dx, y)) # Horizontal line.
        lineTo((x + dx, y))
        moveTo((x, y + dy)) # Vertical line.
        lineTo((x, y - dy))
        drawPath()

    def drawPageRegistrationMarks(self, page, origin):
        u"""Draw standard registration mark, to show registration of CMYK colors.
        https://en.wikipedia.org/wiki/Printing_registration."""
        if self.showPageRegistrationMarks:
            cmSize = min(self.pl/2, self.css('viewCropMarkSize')) # TODO: Make cropmark go closer to page edge and disappear if too small.
            cmStrokeWidth = self.css('viewCropMarkStrokeWidth')
            x, y, _ = point3D(origin)
            w, h = page.w, page.h
            self._drawPageRegistrationMark(page, (x + w/2, y - cmSize), cmSize, cmStrokeWidth, False) # Bottom registration mark
            self._drawPageRegistrationMark(page, (x - cmSize, y + h/2), cmSize, cmStrokeWidth, True) # Left registration mark
            self._drawPageRegistrationMark(page, (x + w + cmSize, y + h/2), cmSize, cmStrokeWidth, True) # Right registration mark
            self._drawPageRegistrationMark(page, (x + w/2, y + h + cmSize), cmSize, cmStrokeWidth, False) # Top registration mark

    def drawPageCropMarks(self, e, origin):
        u"""If the show flag is set, then draw the cropmarks or page frame."""
        if self.showPageCropMarks:
            x, y, _ = point3D(origin) # Ignore z-axus for now.
            w, h = e.w, e.h
            folds = self.css('folds')
            bleed = self.css('bleed')/2 # 1/2 overlap with image bleed
            cmSize = min(self.css('viewCropMarkSize', 32), self.pl)
            cmStrokeWidth = self.css('viewCropMarkStrokeWidth')

            fill(None)
            cmykStroke(1,1,1,1)
            strokeWidth(cmStrokeWidth)
            newPath()
            # Bottom left
            moveTo((x - bleed, y))
            lineTo((x - cmSize, y))
            moveTo((x, y - bleed))
            lineTo((x, y - cmSize))
            # Bottom right
            moveTo((x + w + bleed, y))
            lineTo((x + w + cmSize, y))
            moveTo((x + w, y - bleed))
            lineTo((x + w, y - cmSize))
            # Top left
            moveTo((x - bleed, y + h))
            lineTo((x - cmSize, y + h))
            moveTo((x, y + h + bleed))
            lineTo((x, y + h + cmSize))
            # Top right
            moveTo((x + w + bleed, y + h))
            lineTo((x + w + cmSize, y + h))
            moveTo((x + w, y + h + bleed))
            lineTo((x + w, y + h + cmSize))
            # Any fold lines to draw?
            if folds is not None:
                for fx, fy in folds:
                    if fx is not None:
                        moveTo((x + fx, y - bleed))
                        lineTo((x + fx, y - cmSize))
                        moveTo((x + fx, y + h + bleed))
                        lineTo((x + fx, y + h + cmSize))
                    if fy is not None:
                        moveTo((x - bleed, y + fy))
                        lineTo((x - cmSize, y + fy))
                        moveTo((x + w + bleed, y + fy))
                        lineTo((x + w + cmSize, y + fy))
            drawPath()



