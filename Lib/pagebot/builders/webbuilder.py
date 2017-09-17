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
#     webbuilder.py
#
from htmlbuilder import HtmlBuilder

class WebBuilder(HtmlBuilder):
    u"""Generic output builder container, used of collecting html, css, js, include paths and other data
    needed to export the website, e.g. by the GitView or MampView."""

