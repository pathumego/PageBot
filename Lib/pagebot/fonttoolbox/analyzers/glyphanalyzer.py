# -*- coding: UTF-8 -*-
# -----------------------------------------------------------------------------
#
#     P A G E B O T
#
#     Copyright (c) 2016+ Type Network, www.typenetwork.com, www.pagebot.io
#     Licensed under MIT conditions
#     Made for usage in DrawBot, www.drawbot.com
# -----------------------------------------------------------------------------
#
#     glyphanalyzer.py
#
#     Implements a PageBot font classes to get info from a TTFont.
#
import weakref

from pagebot.toolbox.transformer import point2D
from pointcontextlist import Vertical, Horizontal

SPANSTEP = 4

class GlyphAnalyzer(object):

    VERTICAL_CLASS = Vertical # Allow inheriting classes to change this
    HORIZONTAL_CLASS = Horizontal

    def __init__(self, glyph):
        self._glyph = weakref.ref(glyph)
        self._analyzer = None

        self._horizontals = None
        self._stems = None # Recognized stems, so not filtered by FloqMemes
        self._roundStems = None # Recognized round stems, not filtered by FloqMemes

        self._verticals = None
        self._bars = None # Recognized bars, so not filtered by FloqMemes
        self._roundBars = None # Recognized round bars, so not filtered by FloqMemes

    def _get_glyph(self):
        return self._glyph()
    glyph = property(_get_glyph)

    def __repr__(self):
        return '<Analyzer of "%s">' % self.glyph.name

    # self.verticals

    def _get_verticals(self):
        if self._verticals is None:
            self.findVerticals()
        return self._verticals
    verticals = property(_get_verticals)

    # self.horizontals

    def _get_horizontals(self):
        if self._horizontals is None:
            self.findHorizontals()
        return self._horizontals
    horizontals = property(_get_horizontals)

    def findVerticals(self):
        u"""The findVerticals method answers a list of verticals."""
        self._verticals = verticals = {}

        for pc in sorted(self.glyph.pointContexts):
            if pc.isVertical():
                if not pc.x in verticals:
                    verticals[pc.x] = self.VERTICAL_CLASS()
                verticals[pc.x].append(pc)

    def findHorizontals(self):
        u"""
        The findHorizontals method answers a list of horizontals where the
        main point is on curve."""
        self._horizontals = horizontals = {}

        for pc in self.glyph.pointContexts:
            if pc.isHorizontal():
                if not pc.y in horizontals:
                    horizontals[pc.y] = self.HORIZONTAL_CLASS()
                horizontals[pc.y].append(pc)

    #   S T E M S

    # self.stems
    def _get_stems(self):
        if self._stems is None:
            self.findStems()
        return self._stems
    stems = property(_get_stems)

    def findStems(self):
        u"""
        The @findStems@ method finds the stems in the current glyph and assigns
        them as dictionary to @self._stems@. Since we cannot use the CVT of the
        glyph (the analyzer is used to find these values, not to use them),
        we'll make an assumption about the pattern of vertices found. It is up
        to the caller to make sure that the current glyph is relevant in the
        kind of vertices that we are looking for.<br/>

        NOTE: An alternative approach could be to make a Fourier analysis of all
        stem distances of the font, and so find out which are likely to have a
        stem distance.

        Additionally the stems are found by manual hints in the glyph, as
        generated by the Hint Editor. Since these stem definitions not
        necessarily run from point to point (instead an interpolated location
        on a curve or straight line can be used), a special kind of
        PointContext is added there.
        """
        self._stems = stems = {}
        self._roundStems = roundStems = {}
        self._straightRoundStems = straightRoundStems = {}
        self._allHorizontalCounters = horizontalCounters = {} # Space between all neighboring stems, running over white only.

        verticals = self.verticals
        checked = set() # Store what we checked, to avoid doubles in the loops

        for _, vertical1 in sorted(verticals.items()): # x1, vertical1
            for _, vertical2 in sorted(verticals.items()): # x2, vertical2
                if vertical1 is vertical2:
                    continue
                # We need to loop through the points of the vertical
                # separate, to find e.g. the horizontal separate round stems
                # of the points of a column. Otherwise they will be seen as one vertical.
                for pc0 in vertical1:
                    for pc1 in vertical2:
                        # Skip if identical, they cannot be a stem.
                        if pc0 is pc1:
                            continue
                        # Skip if we already examined this one.
                        if (pc0.index, pc1.index) in checked:
                            continue
                        checked.add((pc0.index, pc1.index))
                        checked.add((pc1.index, pc0.index))
                        # Test if the y values are in range so this can be seen as stem pair
                        # and test if this pair is spanning a black space and the lines are
                        # not entirely covered in black.
                        if self.isStem(pc0, pc1):
                            # Add this stem to the result.
                            stem = self.STEMCLASS(pc0, pc1, self.glyph.name)
                            size = TX.asInt(stem.size) # Make sure not to get floats as key
                            if not size in stems:
                                stems[size] = []
                            stems[size].append(stem)

                        elif self.isRoundStem(pc0, pc1):
                            # If either of the point context is a curve extreme
                            # then count this stem as round stem
                            stem = self.STEMCLASS(pc0, pc1, self.glyph.name)
                            size = TX.asInt(stem.size) # Make sure not to get floats as key
                            if not size in roundStems:
                                roundStems[size] = []
                            roundStems[size].append(stem)

                        elif self.isStraightRoundStem(pc0, pc1):
                            # If one side is straight and the other side is round extreme
                            # then count this stem as straight round stem.
                            stem = self.STEMCLASS(pc0, pc1, self.glyph.name)
                            size = TX.asInt(stem.size) # Make sure not to get floats as key
                            if not size in straightRoundStems:
                                straightRoundStems[size] = []
                            straightRoundStems[size].append(stem)

                        elif self.isHorizontalCounter(pc0, pc1):
                            # If there is just whitspace between the points and they are some kind of extreme,
                            # then assume this is a counter.
                            counter = self.COUNTERCLASS(pc0, pc1, self.glyph.name)
                            size = TX.asInt(counter.size)
                            if not size in horizontalCounters:
                                horizontalCounters[size] = []
                            horizontalCounters[size].append(counter)

        return self._stems

    def isStem(self, pc0, pc1):
        u"""The isStem method takes the point contexts pc0 and
        pc1 to compare if the can be defined as a “stem”: if they are
        not round extremes, if the two point contexts have overlap in the
        vertical directions (being part of the same window) that runs on black
        and if both lines are not entirely covered in black.
        """
        return not pc0.isHorizontalRoundExtreme() \
            and not pc1.isHorizontalRoundExtreme()\
            and pc0.isVertical() and pc1.isVertical()\
            and pc0.inHorizontalWindow(pc1)\
            and self.middleLineOnBlack(pc0, pc1)\
            and self.overlappingLinesInWindowOnBlack(pc0, pc1)
            #and not (self.pointCoveredInBlack(pc0) or self.pointCoveredInBlack(pc1))

    def middleLineOnBlack(self, pc0, pc1, step=SPANSTEP):
        m0 = pc0.middle()
        m1 = pc1.middle()
        return self.spanBlack(m0, m1, step)

    def spanBlack(self, p1, p2, step=SPANSTEP):
        u"""The spanBlack method answers the boolean flag if the number
        of recursive steps between p1 and p2 are on black area
        of the glyph. If step is smaller than the distance between the points,
        then just check in the middle of the line.  The method does not check
        on the end points of the segment, allowing to test these separate
        through self.onBlack or self.coveredInBlack."""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        distance = dx*dx + dy*dy # Save sqrt time, compare with square of step
        m = p1[0] + dx/2, p1[1] + dy/2
        result = self.onBlack(m) # Check the middle of the vector distance.
        if distance > step*step: # Check for the range of steps if the middle point of the line is still on black
            result = result and self.spanBlack(p1, m, step) and self.spanBlack(m, p2, step)
        # Check if distance is still larger than step, otherwise just check in the middle
        return result

    #   B A R S

    # self.bars
    def _get_bars(self):
        if self._bars is None:
            self.findBars()
        return self._bars
    bars = property(_get_bars)

    #   P O I N T S

    def onBlack(self, p):
        u"""Answers the boolean flag is the single point (x, y) is on black."""
        p = point2D(p)
        return self.glyph.path._path.containsPoint_(p)
