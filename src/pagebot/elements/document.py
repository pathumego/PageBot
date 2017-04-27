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
#     document.py
#
import copy

from drawBot import newPage, saveImage, installedFonts, installFont

from pagebot.elements.page import Page
from pagebot.elements.view import View, DefaultView, SingleView, ThumbView
from pagebot.style import makeStyle, getRootStyle

class Document(object):
    u"""A Document is just another kind of container."""
    
    PAGE_CLASS = Page # Allow inherited versions of the Page class.

    def __init__(self, rootStyle=None, styles=None, views=None, autoPages=1, pageTemplate=None, **kwargs):
        u"""Contains a set of Page elements and other elements used for display in thumbnail mode. Allows to compose the pages
        without the need to send them directly to the output for "asynchronic" page filling."""
        if rootStyle is None:
            rootStyle = getRootStyle()
        self.rootStyle = rootStyle
        self.initializeStyles(rootStyle, styles) # Merge CSS for element tree

        # Used as default document master template if undefined in pages.
        self.pageTemplate = pageTemplate 

        self._pages = {} # Key is pageNumber, Value is row list of pages: self.pages[pn][index] = page

        # Initialize some basic views.
        self.initializeViews(views)

        # Document (w, h) size is default from page, but will modified by the type of display mode. 
        if autoPages:
            self.makePages(pageCnt=autoPages, **kwargs)
        # Storage lib for collected content while typesetting and composing, referring to the pages
        # they where placed on during composition.
        self._lib = {}

    def _get_lib(self):
        u"""Answer the global storage dictionary, used by TypeSetter and others to keep track of footnotes,
        table of content, etc. Some common entries are predefined. """
        return self._lib 
    lib = property(_get_lib)

    # Document[12] answers a list of pages where page.y == 12
    # This behaviour is different from regular elements, who want the page.eId as key.
    def __getitem__(self, pnIndex):
        u"""Answer the pages with pageNumber equal to page.y. """
        pn, index = pnIndex
        return self._pages[pn][index]
    def __setitem__(self, pn, page):
        if not pn in self._pages:
            self._pages[pn] = []
        self._pages[pn].append(page)
   
    def _get_ancestors(self):
        return []
    ancestors = property(_get_ancestors)
 
    #   S T Y L E

    def initializeStyles(self, rootStyle, styles):
        u"""Make sure that the default styles always exist."""
        if styles is None:
            styles = {}
        self.styles = styles # Dictionary of styles. Key is XML tag name value is Style instance.
        # Make sure that the default styles for document and page are always there.
        name = 'root'
        self.addStyle(name, rootStyle)
        name = 'document'
        if not name in self.styles: # Empty dict styles as placeholder, if nothing is defined.
            self.addStyle(name, dict(name=name))
        name = 'page'
        if not name in self.styles: # Empty dict styles as placeholder, if nothing is defined.
            self.addStyle(name, dict(name=name))

    def getMaxPageSizes(self, pageSelection=None):
        u"""Answer the (w, h, d) size of all pages together. If the optional pageSelection is defined (set of y-values),
        then only evaluate the selected pages."""
        w = h = d = 0
        for (y, x), page in self._pages.items():
            if pageSelection is not None and not y in pageSelection:
                continue
            w = max(w, e.w)
            h = max(h, e.h)
            d = max(d, e.d)
        return w, h, d

    # Answer the cascaded style value, looking up the chain of ancestors, until style value is defined.

    def css(self, name, default=None, styleId=None):
        u"""If optional sId is None or style cannot found, then use the root style. 
        If the style is found from the (cascading) sId, then use that to return the requested attribute."""
        style = self.findStyle(styleId)
        if style is None:
            style = self.rootStyle
        return style.get(name, default)

    def findStyle(self, styleId):
        u"""Answer the style that fits the optional sequence naming of styleId.
        Answer None if no style can be found. styleId can have one of these formats:
        ('main h1', 'h1 b')"""
        if styleId is None:
            return None
        styleId = obj2StyleId(styleId)
        while styleId and not ' '.join(styleId) in self.styles:
            styleId = styleId[1:]
        if styleId:
            return self.styles[styleId]
        return None

    def getNamedStyle(self, styleName):
        u"""In case we are looking for a named style (e.g. used by the Typesetter to build a stack
        of cascading tag style, then query the ancestors for the named style. Default behavior
        of all elements is that they pass the request on to the root, which is nornally the document."""
        return self.getStyle(styleName)

    def getStyle(self, name):
        u"""Answer the names style. If that does not exist, answer the default root style."""
        self.styles.get(name, self.getRootStyle())
    
    def getRootStyle(self):
        u"""Answer the default root style, used by the composer as default for all other stacked styles."""
        return self.rootStyle

    def addStyle(self, name, style):
        u"""Add the style to the self.styles dictionary."""
        assert not name in self.styles # Make sure that styles don't get overwritten. Remove them first.
        self.styles[name] = style
        # Force the name of the style to synchronize with the requested key.
        style['name'] = name
      
    def replaceStyle(self, name, style):
        u"""Set the style by name. Overwrite the style with that name if it already exists."""
        self.styles[name] = style
        # Force the name of the style to synchronize with the requested key.
        style['name'] = name
        return style # Answer the style for convenience of tha caller, e.g. when called by self.newStyle(args,...)

    def newStyle(self, **kwargs):
        u"""Create a new style with the supplied arguments as attributes. Force the style in self.styles,
        even if already exists. Forst the name of the style to be the same as the style key.
        Answer the new style."""
        return self.replaceStyle(kwargs['name'], dict(**kwargs))
     
    #   F O N T S

    def getInstalledFonts(self):
        u"""Answer the list of font names, currently installed in the application."""
        return installedFonts()

    def installFont(self, path):
        u"""Install a font with a given path and the postscript font name will be returned. The postscript
        font name can be used to set the font as the active font. Fonts are installed only for the current
        process. Fonts will not be accessible outside the scope of drawBot.
        All installed fonts will automatically be uninstalled when the script is done."""
        return installFont(path)

    #   P A G E S

    def getPage(self, pn, index=0):
        u"""Answer the page at index, for equal y and x. Raise index errors if it does not exist."""
        if not pn in self._pages:
            return None
        if index >= len(self._pages[pn]):
            return None
        return self._pages[pn][index]

    def getPages(self, pn):
        u"""Answer all pages that share the same page number. Rase KeyError if non exist."""
        return self._pages[pn]

    def findPages(self, eid=None, name=None, pattern=None, pageSelection=None):
        u"""Various ways to find pages from their attributes."""
        pages = []
        for pn, pnPages in sorted(self._pages.items()):
            if not pageSelection is None and not pn in pageSelection:
                continue
            for _, page in sorted(pnPages.items()):
                if eId == page.eId:
                    return [page]
                if (name is not None and name == page.name) or \
                       pattern is not None and page.name is not None and pattern in page.name:
                    pages.append(page)
        return pages

    def newPage(self, pn=None, **kwargs):
        u"""Use point (x, y) to define the order of pages and spreads. Ignore any parent here, force to self."""
        page = self.PAGE_CLASS(parent=self, **kwargs)
        if pn is None and self._pages.keys():
            pn = max(self._pages.keys())+1
        else:
            pn = 0
        self[pn] = page
    
    def makePages(self, pageCnt, pn=None, **kwargs):
        u"""Make a range of pages. (Mis)using the (x,y) position of page elements, as their sorting order.
        If no "point" is defined as page id, then we'll continue after the maximum value of page.y origin position."""
        for n in range(pageCnt):
            self.newPage(pn, template=self.pageTemplate, **kwargs) # Parent is forced to self.

    def nextPage(self, page, nextPage=1, makeNew=True):
        u"""Answer the next page of page. If it does not exist, create a new page."""
        found = False
        for pn, pnPages in sorted(self._pages.items()):
            for index, page in enumerate(pnPages):
                if found:
                    return page
                if eId == page.eId:
                    found = True
        # Not found, create new one?
        if makeNew:
            return self.newPage()
        return None

    def getFirstPage(self):
        u"""Answer the list of pages with the lowest sorted page.y. Answer empty list if there are no pages."""
        for pn, pnPages in sorted(self._pages.items()):
            for index, page in enumerate(pnPages):
                return page
        return None

    def getLastPage(self):
        u"""Answer last page with the highest sorted page.y. Answer empty list if there are no pages."""
        pn = sorted(self._pages.keys())[-1]
        return self._pages[pn][-1]

    def getSortedPages(self):
        u"""Answer the dynamic list of pages, sorted by y, x and index."""
        pages = []
        for _, pnPages in sorted(self._pages.items()):
            pages += pnPages
        return pages

    #   V I E W S

    def initializeViews(self, views):
        self.views = {} # Key is name of View instance. 
        if views is not None:
            for view in views:
                assert not view.name in self.views
                self.appendView(view)
        # Define some default views if not already  there.
        for viewClass in (DefaultView, SingleView, ThumbView):
            if not viewClass.viewId in self.views:
                self.appendView(viewClass())

    def appendView(self, view):
        self.views[view.viewId] = view
        view.parent = self

    def getView(self, viewId):
        u"""Answer the viewer instance with viewId. Answer DefaultView() if it does not exist."""
        view = self.views.get(viewId)
        if view is None:
            view = DefaultView()
        return view

    #   D R A W I N G

    def drawPages(self, viewName=None, pageSelection=None):
        u"""Draw the selected pages. pageSelection is an optional set of y-pageNumbers to draw."""
        view = self.getView(viewName)
        view.drawPages(self, pageSelection)

    def export(self, fileName=None, viewName=None, pageSelection=None, multiPage=True):
        u"""Let the view do the work."""
        view = self.getView(viewName)
        view.export(self, fileName, pageSelection, multiPage)

