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
#     textbox.py
#
import re
import CoreText
import Quartz

from drawBot import textOverflow, hyphenation, textBox, text, rect, textSize, FormattedString, line, fill, \
    stroke, strokeWidth, save, restore

from pagebot import newFS, setStrokeColor, setFillColor, setGradient, setShadow
from pagebot.style import LEFT, RIGHT, CENTER, NO_COLOR, MIN_WIDTH, MIN_HEIGHT, makeStyle, MIDDLE, BOTTOM, DEFAULT_WIDTH, DEFAULT_HEIGHT
from pagebot.elements.element import Element
from pagebot.toolbox.transformer import pointOffset
from pagebot.fonttoolbox.objects.glyph import Glyph

class FoundPattern(object):
    def __init__(self, s, x, ix, y=None, w=None, h=None, line=None, run=None):
        self.s = s # Actual found string
        self.x = x
        self.ix = ix
        self.y = y
        self.w = w
        self.h = h
        self.line = line # TextLine instance that this was found in
        self.run = run # List of  of this strin,g
    
    def __repr__(self):
        return '[Found "%s" @ %d,%d]' % (self.s, self.x, self.y) 

class TextRun(object):
    def __init__(self, ctRun, runIndex):
        self.runIndex = runIndex # Index of the run in the TextLine
        self._ctRun = ctRun
        self._style = None # Property cash for constructed style from run parameters.
        self.glyphCount = gc = CoreText.CTRunGetGlyphCount(ctRun)
        # Reverse the style from 
        attrs = CoreText.CTRunGetAttributes(ctRun)
        self.nsFont = attrs['NSFont']
        #self.fontDescriptor = f.fontDescriptor()
        self.fill = attrs['NSColor']
        self.nsParagraphStyle = attrs['NSParagraphStyle']
        self.attrs = attrs # Save, in case the caller want to query run parameters.

        self.iStart, self.iEnd = CoreText.CTRunGetStringRange(ctRun)
        self.string = u''    
        # Hack for now to find the string in repr-string if self._ctLine.
        # TODO: Make a better conversion here, not relying on the format of the repr-string.
        for index, part in enumerate(`ctRun`.split('"')[1].split('\\u')):
            if index == 0:
                self.string += part
            elif len(part) >= 4:
                self.string += unichr(int(part[0:4], 16))
                self.string += part[4:]

        #print gc, len(CoreText.CTRunGetStringIndicesPtr(ctRun)), CoreText.CTRunGetStringIndicesPtr(ctRun), ctRun
        try:
            self.stringIndices = CoreText.CTRunGetStringIndicesPtr(ctRun)[0:gc]
        except TypeError:
            self.stringIndices = [0]
        #CoreText.CTRunGetStringIndices(ctRun._ctRun, CoreText.CFRange(0, 5), None)[4]
        self.advances = CoreText.CTRunGetAdvances(ctRun, CoreText.CFRange(0, 5), None)
        #self.positions = CoreText.CTRunGetPositionsPtr(ctRun)[0:gc]
        #CoreText.CTRunGetPositions(ctRun, CoreText.CFRange(0, 5), None)[4]
        #self.glyphFontIndices = CoreText.CTRunGetGlyphsPtr(ctRun)[0:gc]
        #print CoreText.CTRunGetGlyphs(ctRun, CoreText.CFRange(0, 5), None)[0:5]
        self.status = CoreText.CTRunGetStatus(ctRun)

        # get all positions
        self.positions = CoreText.CTRunGetPositions(ctRun, (0, gc), None)
        # get all glyphs
        self.glyphs = CoreText.CTRunGetGlyphs(ctRun, (0, gc), None)

    def __len__(self):
        return self.glyphCount

    def __repr__(self):
        return '[TextRun #%d "%s"]' % (self.runIndex, self.string) 

    def __getitem__(self, index):
        return self.string[index]

    def _get_style(self):
        u"""Answer the constructed style dictionary, with names that fit the standard
        PageBot style."""
        if self._style is None:
            self._style = dict(
                textFill=self.fill,
                pl=self.headIndent,
                pr=self.tailIndent,
                fontSize=self.fontSize,
                font=self.displayName,
                leading=self.leading + self.fontSize, # ??
            )
        return self._style
    style = property(_get_style)

    # Font stuff

    def _get_displayName(self):
        return self.nsFont.displayName()
    displayName = property(_get_displayName)

    def _get_familyName(self):
        return self.nsFont.familyName()
    familyName = property(_get_familyName)

    def _get_fontName(self):
        return self.nsFont.fontName()
    fontName = font = property(_get_fontName)

    def _get_isVertical(self):
        return self.nsFont.isVertical()
    isVertical = property(_get_isVertical)

    def _get_isFixedPitch(self):
        return self.nsFont.isFixedPitch()
    isFixedPitch = property(_get_isFixedPitch)

    def _get_boundingRectForFont(self):
        (x, y), (w, h) = self.nsFont.boundingRectForFont()
        return x, y, w, h
    boundingRectForFont = property(_get_boundingRectForFont)

    def _get_renderingMode(self):
        return self.nsFont.renderingMode()
    renderingMode = property(_get_renderingMode)

    #   Font metrics

    def _get_ascender(self):
        return self.nsFont.ascender()
    ascender = property(_get_ascender)
    
    def _get_descender(self):
        return self.nsFont.descender()
    descender = property(_get_descender)
    
    def _get_capHeight(self):
        return self.nsFont.capHeight()
    capHeight = property(_get_capHeight)
    
    def _get_xHeight(self):
        return self.nsFont.xHeight()
    xHeight = property(_get_xHeight)

    def _get_italicAngle(self):
        return self.nsFont.italicAngle()
    italicAngle = property(_get_italicAngle)

    def _get_fontSize(self):
        return self.nsFont.pointSize()
    fontSize = property(_get_fontSize)

    def _get_leading(self):
        return self.nsFont.leading()
    leading = property(_get_leading)
    
    def _get_fontMatrix(self):
        return self.nsFont.matrix()
    fontMatrix = property(_get_fontMatrix)

    def _get_textTransform(self):
        return self.nsFont.textTransform()
    textTransform = property(_get_textTransform)

    def _get_underlinePosition(self):
        return self.nsFont.underlinePosition()
    underlinePosition = property(_get_underlinePosition)

    def _get_underlineThickness(self):
        return self.nsFont.underlineThickness()
    underlineThickness = property(_get_underlineThickness)

    #   Paragraph attributes

    def _get_matrix(self):
        return CoreText.CTRunGetTextMatrix(self._ctRun)
    matrix = property(_get_matrix)

    def _get_alignment(self):
        return self.nsParagraphStyle.alignment()
    alignment = property(_get_alignment)

    def _get_lineSpacing(self):
        return self.nsParagraphStyle.lineSpacing()
    lineSpacing = property(_get_lineSpacing)

    def _get_paragraphSpacing(self):
        return self.nsParagraphStyle.paragraphSpacing()
    paragraphSpacing = property(_get_paragraphSpacing)

    def _get_paragraphSpacingBefore(self):
        return self.nsParagraphStyle.paragraphSpacingBefore()
    paragraphSpacingBefore = property(_get_paragraphSpacingBefore)

    def _get_headIndent(self):
        return self.nsParagraphStyle.headIndent()
    headIndent = property(_get_headIndent)

    def _get_tailIndent(self):
        return self.nsParagraphStyle.tailIndent()
    tailIndent = property(_get_tailIndent)

    def _get_firstLineHeadIndent(self):
        return self.nsParagraphStyle.firstLineHeadIndent()
    firstLineHeadIndent = property(_get_firstLineHeadIndent)

    def _get_lineHeightMultiple(self):
        return self.nsParagraphStyle.lineHeightMultiple()
    lineHeightMultiple = property(_get_lineHeightMultiple)

    def _get_maximumLineHeight(self):
        return self.nsParagraphStyle.maximumLineHeight()
    maximumLineHeight = property(_get_maximumLineHeight)

    def _get_minimumLineHeight(self):
        return self.nsParagraphStyle.minimumLineHeight()
    minimumLineHeight = property(_get_minimumLineHeight)

        
class TextLine(object):
    def __init__(self, ctLine, p, lineIndex):
        self._ctLine = ctLine
        self.x, self.y = p # Relative position from top of TextBox
        self.lineIndex = lineIndex # Vertical line index in TextBox.
        self.glyphCount = CoreText.CTLineGetGlyphCount(ctLine)

        self.string = '' 
        self.runs = []
        #print ctLine
        for runIndex, ctRun in enumerate(CoreText.CTLineGetGlyphRuns(ctLine)):
            textRun = TextRun(ctRun, runIndex)
            self.runs.append(textRun)
            self.string += textRun.string

    def __repr__(self):
        return '[TextLine #%d Glyphs:%d Runs:%d]' % (self.lineIndex, self.glyphCount, len(self.runs))

    def __len__(self):
        return self.glyphCount

    def __getitem__(self, index):
        return self.runs[index]
        
    def getIndexForPosition(self, (x, y)):
        return CoreText.CTLineGetStringIndexForPosition(self._ctLine, CoreText.CGPoint(x, y))[0]
    
    def getOffsetForStringIndex(self, i):
        u"""Answer the z position that is closest to glyph string index i. If i is out of bounds,
        then answer the closest x position (left and right side of the string)."""
        return CoreText.CTLineGetOffsetForStringIndex(self._ctLine, i, None)[0]
                
    def _get_stringIndex(self):
        return CoreText.CTLineGetStringRange(self._ctLine).location
    stringIndex = property(_get_stringIndex)
 
    def getGlyphIndex2Run(self, glyphIndex):
        for run in self.runs:
            if run.iStart >= glyphIndex:
                return run
        return None
        
    #def _get_alignment(self):
    #    return CoreText.CTTextAlignment(self._ctLine)
    #alignment = property(_get_alignment)
            
    def _get_imageBounds(self):
        u"""Property that answers the bounding box (actual black shape) of the line."""
        (x, y), (w, h) = CoreText.CTLineGetImageBounds(self._ctLine, None)
        return x, y, w, h
    imageBounds = property(_get_imageBounds)
    
    def _get_bounds(self):
        u"""Property that returns the EM bounding box of the line."""
        return CoreText.CTLineGetTypographicBounds(self._ctLine, None, None, None)
    bounds = property(_get_bounds)
    
    def _get_trailingWhiteSpace(self):
        return CoreText.CTLineGetTrailingWhitespaceWidth(self._ctLine)
    trailingWhiteSpace = property(_get_trailingWhiteSpace)

    def findPattern(self, pattern):
        founds = []
        if isinstance(pattern, basestring):
            pattern = re.compile(pattern)
            #pattern = re.compile('([a-ZA-Z0-9\.\-\_]*])
        for iStart, iEnd in [(m.start(0), m.end(0)) for m in re.finditer(pattern, self.string)]:
            xStart = self.getOffsetForStringIndex(iStart)
            xEnd = self.getOffsetForStringIndex(iEnd)
            #print 'xStart, xEnd', xStart, xEnd
            run = self.getGlyphIndex2Run(xStart)
            #print 'iStart, xStart', iStart, xStart, iEnd, xEnd, run
            founds.append(FoundPattern(self.string[iStart:iEnd], xStart, iStart, line=self, run=run))
        return founds
           
class TextBox(Element):

    # Initialize the default behavior tags as different from Element.
    isText = True  # This element is capable of handling text.
    isTextBox = True

    TEXT_MIN_WIDTH = 24 # Absolute minumum with of a text box.

    def __init__(self, fs, html=None, minW=None, w=DEFAULT_WIDTH, h=None, showBaselines=False, **kwargs):
        Element.__init__(self,  **kwargs)
        u"""Default is the storage of self.fs (DrawBot FormattedString), but optional can be ts (tagged basestring)
        if output is mainly through build and HTML/CSS. Since both strings cannot be conversted lossless one into the other,
        it is safer to keep them both if they are available."""
        # Make sure that this is a formatted string. Otherwise create it with the current style.
        # Note that in case there is potential clash in the double usage of fill and stroke.
        self.minW = max(minW or 0, MIN_WIDTH, self.TEXT_MIN_WIDTH)
        self._textLines = self._baseLines = None # Force initiaize upon first usage.
        self.size = w, h
        if isinstance(fs, basestring):
            fs = newFS(fs, self)
        self.fs = fs # Keep as plain string, in case parent is not set yet.
        self.html = html or '' # Parallel storage of html content.
        self.showBaselines = showBaselines # Force showing of baseline if view.showBaselines is False.

    def _get_w(self): # Width
        return min(self.maxW, max(self.minW, self.style['w'], MIN_WIDTH)) # From self.style, don't inherit.
    def _set_w(self, w):
        self.style['w'] = w or MIN_WIDTH # Overwrite element local style from here, parent css becomes inaccessable.
        self._textLines = None # Force reset if being called
    w = property(_get_w, _set_w)

    def _get_h(self):
        u"""Answer the height of the textBox. If self.style['elasticH'] is set, then answer the 
        vertical space that the text needs. This overwrites the setting of self._h."""
        if self.style['h'] is None: # Elastic height
            h = self.getTextSize(self.w)[1] + self.pt + self.pb # Add paddings
        else:
            h = self.style['h']
        return min(self.maxH, max(self.minH, h)) # Should not be 0 or None
    def _set_h(self, h):
        # Overwrite style from here, unless self.style['elasticH'] is True
        self.style['h'] = h # If None, then self.h is elastic from content
    h = property(_get_h, _set_h)

    def __getitem__(self, lineIndex):
        print '#@@@@#@#@@', self
        return self.textLines[lineIndex]

    def __len__(self):
        return len(self.textLines)
  
    def __repr__(self):
        if self.title:
            name = ':'+self.title
        elif self.name:
            name = ':'+self.name
        else: # No naming, show unique self.eId:
            name = ':'+self.eId

        if self.fs:
            fs = ' FS(%d)' % len(self.fs)
        else:
            fs = ''

        if self.elements:
            elements = ' E(%d)' % len(self.elements)
        else:
            elements = ''
        return '%s%s (%d, %d)%s%s' % (self.__class__.__name__, name, int(round(self.point[0])), int(round(self.point[1])), fs, elements)

    # Formatted string

    def _get_fs(self):
        return self._fs
    def _set_fs(self, fs):
        self._fs = fs
        self._textLines = None # Force reset when called.
    fs = property(_get_fs, _set_fs)
  
    def setText(self, s):
        u"""Set the formatted string to s, using self.style."""
        self.fs = newFS(s, self)

    def _get_text(self):
        u"""Answer the plain text of the current self.fs"""
        return u'%s' % self.fs
    text = property(_get_text)
    
    def appendString(self, fs):
        u"""Append s to the running formatted string of the self. Note that the string
        is already assumed to be styled or can be added as plain string.
        Don't calculate the overflow here, as this is slow/expensive operation.
        Also we don't want to calcualte the textLines/runs for every string appended,
        as we don't know how much more the caller will add. self._textLines is set to None
        to force recalculation as soon as self.textLines is called again."""
        assert fs is not None
        self._textLines = None # Reset to force call to self.initializeTextLines()
        if self.fs is None:
            self.fs = fs
        else:
            self.fs += fs
        return self.fs # Answer the complete FormattedString as convenience for the caller.

    def appendHtml(self, html):
        u"""Add parellel utf-8 html string to the self content."""
        self.html += html or ''

    def appendMarker(self, markerId, arg=None):
        marker = getMarker(markerId, arg=arg)
        self.appendString(marker)
        self.appendHtml('<!-- %s -->' % marker)

    def _get_textLines(self):
        if self._textLines is None:
            self.initializeTextLines()
        return self._textLines
    textLines = property(_get_textLines)

    def _get_baseLines(self):
        if self._textLines is None: # Check if initialization is needed.
            self.initializeTextLines()
        return self._baseLines
    baseLines = property(_get_baseLines)

    def initializeTextLines(self):
        u"""Answer an ordered list of all baseline position, starting at the top."""    
        self._box = 0, 0, self.w, self.h
        attrString = self._fs.getNSObject()
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = Quartz.CGPathCreateMutable()
        Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(*self._box))
        ctBox = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)
        self._ctLines = CoreText.CTFrameGetLines(ctBox)
        self._textLines = []
        for lineIndex, p in enumerate(CoreText.CTFrameGetLineOrigins(ctBox, (0, len(self._ctLines)), None)):
            x = p.x
            if self.originTop:
                y = self.h - p.y
            else:
                y = p.y
            ctLine = self._ctLines[lineIndex]
            textLine = TextLine(ctLine, (x, y), lineIndex)
            self._textLines.append(textLine)
 
    def getTextSize(self, fs=None, w=None):
        """Figure out what the width/height of the text self.fs is, with or given width or
        the styled width of this text box. If fs is defined as external attribute, then the
        size of the string is answers, as if it was already inside the text box."""
        if fs is None:
            fs = self.fs
        return textSize(self.fs, width=w or self.w)

    def getOverflow(self, w=None, h=None):
        """Figure out what the overflow of the text is, with the given (w,h) or styled
        (self.w, self.h) of this text box. If self.style['elasticH'] is True, then by
        definintion overflow will allways be empty."""
        if self.css('elasticH'): # In case elasticH is True, box will aways fit the content.
            return ''
        # Otherwise test if there is overflow of text in the given size.
        return textOverflow(self.fs, (0, 0, w or self.w-self.pr-self.pl, h or self.h-self.pt-self.pb), LEFT)

    def NOTNOW_getBaselinePositions(self, y=0, w=None, h=None):
        u"""Answer the list vertical baseline positions, relative to y (default is 0)
        for the given width and height. If omitted use (self.w, self.h)"""
        baselines = []
        for _, baselineY in textBoxBaseLines(self.fs, (0, y, w or self.w, h or self.h)):
            baselines.append(baselineY)
        return baselines

    def _findStyle(self, run):
        u"""Answer the name and style that desctibes this run best. If there is a doc
        style, then answer that one with its name. Otherwise answer a new unique style name
        and the style dict with its parameters."""
        print run.attrs
        print '#++@+', run.style
        return 'ZZZ', run.style

    def getStyledLines(self):
        u"""Answer the list with (styleName, style, textRun) tuples, reversed engeneered
        from the FormattedString self.fs. This list can be used to query the style parameters
        used in the textBox, or to create CSS styles from its content."""
        styledLines = []
        prevStyle = None
        for line in self.textLines:
            for run in line.runs:
                styleName, style = self._findStyle(run)
                if prevStyle is None or prevStyle != style:
                    styledLines.append([styleName, style, run.string])
                else: # In case styles of runs are identical (e.g. on line wraps), just add.
                    styledLines[-1][-1] += run.string
                prevStyle = style
        return styledLines

    #   F L O W

    def isOverflow(self, tolerance=0):
        u"""Answer the boolean flag if this element needs overflow to be solved.
        This method is typically called by conditions such as Overflow2Next or during drawing
        if the overflow marker needs to be drawn.
        Note: There is currently not a test if text actually went into the next element. It's just
        checking if there is a name defined, not if it exists or is already filled by another flow."""
        return self.nextElement is None and len(self.getOverflow())

    def overflow2Next(self):
        u"""Try to fix if there is overflow."""
        result = True
        overflow = self.getOverflow()
        if overflow and self.nextElement: # If there is text overflow and there is a next element?
            result = False
            # Find the page of self
            page = self.getElementPage()
            if page is not None:        
                # Try next page
                nextElement = page.getElementByName(self.nextElement) # Optional search  next page too.
                if nextElement is None or nextElement.fs and self.nextPage:
                    # Not found or not empty, search on next page.
                    page = self.doc.getPage(self.nextPage)
                    nextElement =  page.getElementByName(self.nextElement)
                if nextElement is not None and not nextElement.fs: 
                    # Finally found one empty box on this page or next page?
                    nextElement.fs = overflow
                    nextElement.prevPage = page.name
                    nextElement.prevElement = self.name # Remember the back link
                    score = nextElement.solve() # Solve any overflow on the next element.
                    result = len(score.fails) == 0 # Test if total flow placement succeeded.
        return result

    #   B U I L D

    def build(self, view, b):
        u"""Build the HTML/CSS code through WebBuilder (or equivalent) that is the closest representation of self. 
        If there are any child elements, then also included their code, using the
        level recursive indent."""
        if self.info.cssPath is not None:
            b.includeCss(self.cssPath) # Add CSS content of file, if path is not None and the file exists.
        if self.info.htmlPath is not None:
            b.includeHtml(self.htmlPath) # Add HTML content of file, if path is not None and the file exists.
        else:
            b.div(id=self.eId, class_=self.class_)
            b.addHtml(self.html)
            for e in self.elements:
                e.build(view, b)
            b._div() 

    #   D R A W 

    def draw(self, origin, view):
        u"""Draw the text on position (x, y). Draw background rectangle and/or frame if
        fill and/or stroke are defined."""
        p = pointOffset(self.oPoint, origin)
        p = self._applyScale(p)    
        px, py, _ = p = self._applyAlignment(p) # Ignore z-axis for now.
   
        # TODO: Add marker if there is overflow text in the textbox.

        self.drawFrame(p, view) # Draw optional frame or borders.

        if self.drawBefore is not None: # Call if defined
            self.drawBefore(self, p, view)

        # Draw the text with horizontal and vertical alignment
        tw, th = textSize(self.fs)
        xOffset = yOffset = 0
        if self.css('yTextAlign') == MIDDLE:
            yOffset = (self.h - self.pb - self.pt - th)/2
        elif self.css('yTextAlign') == BOTTOM:
            yOffset = self.h - self.pb - self.pt - th
        if self.css('xTextAlign') == CENTER:
            xOffset = (self.w - self.pl - self.pr - tw)/2
        elif self.css('xTextAlign') == RIGHT:
            xOffset = self.w - self.pl - self.pr - tw

        textShadow = self.textShadow
        if textShadow:
            save()
            setShadow(textShadow)

        textBox(self.fs, (px + self.pl + xOffset, py + self.pb-yOffset, 
            self.w-self.pl-self.pr, self.h-self.pb-self.pt))

        if textShadow:
            restore()

        # If there are any child elements, draw them over the text.
        self._drawElements(p, view)

        # Draw markers on TextLine and TextRun positions.
        self._drawBaselines(px, py, view)
 
        if view.showTextOverflowMarker and self.isOverflow():
            self._drawOverflowMarker(px, py, view)

        if self.drawAfter is not None: # Call if defined
            self.drawAfter(self, p, view)

        self._restoreScale()
        view.drawElementMetaInfo(self, origin) # Depends on css flag 'showElementInfo'

    def _drawBaselines(self, px, py, view):
        # Let's see if we can draw over them in exactly the same position.
        if not view.showTextBoxBaselines and not self.showBaselines:
            return

        fontSize = self.css('baseLineMarkerSize')
        indexStyle = dict(font='Verdana', fontSize=8, textFill=(0, 0, 1))
        yStyle = dict(font='Verdana', fontSize=fontSize, textFill=(0, 0, 1))
        leadingStyle = dict(font='Verdana', fontSize=fontSize, textFill=(1, 0, 0))

        if view.showTextBoxY:
            fs = newFS(`0`, style=indexStyle)
            _, th = textSize(fs)
            text(fs, (px + self.w + 3,  py + self.h - th/4))

        stroke(0, 0, 1)
        strokeWidth(0.5)
        prevY = 0
        for textLine in self.textLines: 
            y = textLine.y
            # TODO: Why measures not showing?
            line((px, py+y), (px + self.w, py+y))
            if view.showTextBoxIndex:
                fs = newFS(`textLine.lineIndex`, style=indexStyle)
                tw, th = textSize(fs) # Calculate right alignment
                text(fs, (px-3-tw, py + y - th/4))
            if view.showTextBoxY:
                fs = newFS('%d' % round(y), style=yStyle)
                _, th = textSize(fs)
                text(fs, (px + self.w + 3, py + y - th/4))
            if view.showTextBoxLeading:
                leading = round(abs(y - prevY))
                fs = newFS('%d' % leading, style=leadingStyle)
                _, th = textSize(fs)
                text(fs, (px + self.w + 3, py + prevY - leading/2 - th/4))
            prevY = y
 
    def _drawOverflowMarker(self, px, py, view):
        fs = newFS('[+]', style=dict(textFill=(1, 0, 0), font='Verdana-Bold', fontSize=8))
        tw, th = textSize(fs)
        if self.originTop:
            pass
        else:
            text(fs, (px + self.w - 3 - tw, py + th/2))

    #   C O N D I T I O N S

    # Text conditions

    def isBaselineOnTop(self, tolerance):
        u"""Answer the boolean if the top baseline is located at self.parent.pt."""
        return abs(self.top - (self.parent.h - self.parent.pt - self.textLines[0].y + self.h)) <= tolerance

    def isBaselineOnBottom(self, tolerance):
        u"""Answer the boolean if the bottom baseline is located at self.parent.pb."""
        return abs(self.bottom - self.parent.pb) <= tolerance

    def isAscenderOnTop(self, tolerance):
        return True

    def isCapHeightOnTop(self, tolerance):
        return True

    def isXHeightOnTop(self, tolerance):
        return True


    def baseline2Top(self):
        self.top = self.parent.h - self.parent.pt - self.textLines[0].y + self.h
        return True
        
    def baseline2Bottom(self):
        self.bottom = self.parent.pb # - self.textLines[-1].y
        return True

    def floatBaseline2Top(self):
        # ...
        return True

    def floatAscender2Top(self):
        # ...
        return True

    def floatCapHeight2Top(self):
        # ...
        return True

    def floatXHeight2Top(self):
        # ...
        return True


    #   F I N D

    def findPattern(self, pattern):
        u"""Answer the point locations where this pattern occures in the Formatted String."""
        foundPatterns = [] # List of FoundPattern instances. 
        for lineIndex, textLine in enumerate(self.textLines):
            for foundPattern in textLine.findPattern(pattern):
                foundPattern.y = textLine.y
                foundPattern.z = self.z
                foundPatterns.append(foundPattern)
        return foundPatterns
                


