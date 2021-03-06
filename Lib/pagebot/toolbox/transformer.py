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
#     transformer.py
#
#     Implements a range of common transforms.
#
import json, re, math, hashlib
import os
from time import time
import datetime
from random import randint

WHITESPACE = ' \t\r\n'
ROMAN_NUMERAL_VALUES = {'M': 1000, 'D': 500, 'C': 100, 'L': 50, 'X': 10, 'V': 5, 'I': 1}

# P O I N T

def point3D(p):
    u"""Answer p as 3D point. If it already is a list of 3 elements, then don't change
    and answer the original."""
    if not p: # None or zero.
        return [0, 0, 0] # Undefined 3D point as list.
    if isinstance(p, tuple):
        p = list(p)
    while len(p) < 3:
        p.append(0) # Value undefined, add origin.
    return p

def point2D(p):
    u"""Answer the 2D origin as combination of p and offset."""
    return point3D(p)[:2]

def pointOffset(point, offset):
    u"""Answer new 3D point, shifted by offset."""
    if not len(point) == 3:
        point = point3D(point)
    if not len(offset) == 3:
        offset = point3D(offset)
    return point[0] + offset[0], point[1] + offset[1], point[2] + offset[2]

def point2S(p):
    u"""Answer the point as string of rounded integers. Ignore z value if it is 0."""
    x, y, z = point3D(p)
    if z:
        return '%d %d %d' % (round(x), round(y), round(z))
    return '%d %d' % (round(x), round(y))

# C O L O R

def moreRed(c='bla', v=0.5):
    u"""Answer a lighter color of c. v = 0 gives same color, v = 1 gives white"""
    moreRedC = [c[0] + (1 - c[0])*v, c[1], c[2]]
    if len(c) == 4:
        moreRedC.append(c[3])
    return moreRedC

def moreGreen(c, v=0.5):
    u"""Answer a lighter color of c. v = 0 gives same color, v = 1 gives white"""
    moreGreenC = [c[0], c[1] + (1 - c[1])*v, c[2]]
    if len(c) == 4:
        moreGreenC.append(c[3])
    return moreGreenC

def moreBlue(c, v=0.5):
    u"""Answer a lighter color of c. v = 0 gives same color, v = 1 gives white"""
    moreBlueC = [c[0], c[1], c[2] + (1 - c[2])*v]
    if len(c) == 4:
        moreBlueC.append(c[3])
    return moreBlueC

def lighter(c, v=0.5):
    u"""Answer a lighter color of c. v = 0 gives same color, v = 1 gives white"""
    return moreRed(moreGreen(moreBlue(c, v), v), v)

def lessRed(c, v=0.5):
    u"""Answer a lighter color of c. v = 0 gives same color, v = 1 gives white"""
    lessRedC = [c[0]*v, c[1], c[2]]
    if len(c) == 4:
        lessRedC.append(c[3])
    return lessRedC

def lessGreen(c, v=0.5):
    u"""Answer a lighter color of c. v = 0 gives same color, v = 1 gives white"""
    lessGreenC = [c[0], c[1]*v, c[2]]
    if len(c) == 4:
        lessGreenC.append(c[3])
    return lessGreenC

def lessBlue(c, v=0.5):
    u"""Answer a lighter color of c. v = 0 gives same color, v = 1 gives white"""
    lessBlueC = [c[0], c[1], c[2]*v]
    if len(c) == 4:
        lessBlueC.append(c[3])
    return lessBlueC

def darker(c, v=0.5):
    u"""Answer a darker color of c. v = 0 gives black, v = 1 gives same color"""
    return lessRed(lessGreen(lessBlue(c, v), v), v)

def int2Color(c):
    u"""Answer the color typle, represented by the integer, e.g. 0xFFEE99."""
    return ((c >> 16) & 255)/255.0, ((c >> 8) & 255)/255.0, (c & 255)/255.0

def s2Color(s):
    u"""Answer the color typle, represented by the hex-string, e.g. #FFEE99.
    The "#" is optional, and will be ignored in the conversion."""
    s = s.replace('#','').replace(' ','')
    try:
        c = int(s, 16)
        return int2Color(c)
    except ValueError:
        return None

def color2Hex(c):
    u"""Answer the CSS hex color string from the color (r, g, b, o) or (r, g, b) tuple.
    This format is CSS compatible."""
    if isinstance(c, (int, long, float)):
        if c > 1:
            return '#%06x' % c
        c = (c, c, c)
    if len(c) == 4: # Includes opacity
        r, g, b, _ = c
    else: # Must be just r, g, b
        r, g, b = c
    return '#%02x%02x%02x' % (r*255, g*255, b*255)

def color2HexOpacity(c):
    u"""Answer the tuple ((r, g, b), opacity) with CSS hex color and value for opacity from the color 
    (r, g, b, o) or (r, g, b) tuple. This format is CSS compatible."""
    if isinstance(c, (int, long, float)):
        c = (c, c, c)
    if len(c) == 4: # Includes opacity
        return color2Hex(c), c[-1] # 0..1
    return color2Hex(c), 1

def value2Tuple4(v):
    u"""Answer a tuple of 4 values."""
    if not isinstance(v, (list, tuple)):
        v = [v]
    if len(v) == 1:
        return v[0], v[0], v[0], v[0]
    if len(v) == 2:
        return v[0], v[1], v[0], v[1]
    if len(v) == 4:
        return v
    raise ValueError

# N U M B E R S

def asNumber(v):
    try:
        fv = float(v)
        iv = int(v)
        if fv == iv:
            return iv
        return fv
    except (ValueError, TypeError):
        pass
    return 0

def asNumberOrNone(value):
    try:
        if value == int(value):
            return asIntOrNone(value)
        return asFloatOrNone(value)
    except (ValueError, TypeError):
        pass
    return None

def asFloatOrNone(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def asId(value, default=0):
    u"""
    The *asId* method transforms the *value* attribute either to an instance of @
    long@ or to @None@, so it can be used as *id* field in a @Record@
    instance. If the value cannot be converted, then the optional *default* (default value is @0
    @) is answered.
    """
    try:
        value = long(value)
        if value <= 0:
            return default
        return value
    except (ValueError, TypeError):
        return default

def asIntOrNone(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def asIntOrDefault(value, default):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def asInt(value, default=None):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default or 0

def isInt(value):
    return asIntOrNone(value) is not None

def asIntOrValue(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return value

def asRoundedInt(value, default=None):
    value = asIntOrNone(value)
    if value is None:
        value = default
    try:
        return int(round(value))
    except (ValueError, TypeError):
        return int(round(default or 0))

def asFloat(value, default=None):
    value = asFloatOrNone(value)
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def asFormatted(value, default=None):
    if int(round(value)) == value: # Same as rounded whole number
        return '%d' % value
    return '%0.2f' % value # Otherwise show as float with 2 digits.

def asBool(value, default=None):
    if value is None:
        return default
    return bool(value)

def asTuple(value):
    if isinstance(value, list):
        value = tuple(value)
    elif not isinstance(value, tuple):
        value = (value,)
    return value

def asSet(value):
    if isinstance(value, (list, tuple)):
        value = set(value)
    if not isinstance(value, set):
        value = set((value,))
    return value

def interpolate(a, b, v, doRound=False):
    u"""Answer the interpolated value of factor v between a and b. If doRound is True (default is False), then
    round the result before answering it."""
    i = a + (b-a) * v
    if doRound:
        i = int(round(i))
    return i

# S T R I N G

def commaString2List(s):
    return stringList2StrippedList(s.split(','))

def stringList2StrippedList(strings):
    l = []
    for string in strings:
        l.append(string.strip())
    return l

def filterValue2Int(s):
    u"""Filter all numeric characters from the string and answer the resulting integer.
    Answer 0 if no digits are found. If s is already a number, then answer it as rounded int."""
    if isinstance(s, (int, float, long)):
        return int(round(s))
    digits = '0'
    for c in s:
        if c in '0123456789':
            digits += c
    return asInt(digits)

# B O O L E A N

def bool2Int(value):
    if value:
        return 1
    return 0

def int2Bool(value):
    if value:
        return True
    else:
        return False

def index2PointId(self, index):
    return '*Pid%d' % index

def none2Empty(value):
    # Answer an empty string if value is None, otherwise pass it through
    # To make sure that 0 empty objects show as result.
    if value is None:
        return ''
    return value

def asDict(value, isRoot=True):
    u"""Answer the value as dict as root. If the value itself is not a dict,
    answer it as dict(value=value). For lower levels than root, answer
    the plain value if is it a string or a number. Basic classed don't get
    translated when not called as root.
    All other objects are called by value.asDict()
    If the object cannot handle that method, then convert it to string."""
    d = {}
    if isinstance(value, dict):
        for key, v in value.items():
            d[key] = asDict(v, False)
    elif isinstance(value, (int, float, long, basestring)):
        if isRoot:
            d = dict(value=value)
        else:
            d = value # On lower levels than root, just copy the value, instead of making dict.
    elif isinstance(value, (list, tuple)):
        l = []
        if isRoot:
            d = dict(value=l) # Always answer a dict as root
        else:
            d = l # Otherwise answer the plain value.
        for v in value:
            l.append(asDict(v, False))
    elif hasattr(value, 'asDict'):
        d = value.asDict()
    else:
        d = dict(value=`value`)
    return d

# ---------------------------------------------------------------------------------------------------------
#    F I X E D

def value2Fixed(value):
    if isinstance(value, basestring):
        if value.endswith('u'):
            value = float2Fixed(asFloat(value[:-1]))
        else:
            value = asIntOrNone(value)
    return value

def float2Fixed(value):
    u"""
    <doc>The @float2Fixed@ method translates a float into a 1/64 pixel unit-value.</doc>
    """
    return int(round(value * 64))

def fixed2Float(value):
    u"""
    <doc>The @fixed2Float@ method translates a fixed 1/64 pixel-unit value to float.</doc>
    """
    return float(value) / 64

# ---------------------------------------------------------------------------------------------------------
#    S T R I N G

def asString(value, default=None):
    if value is None:
        value = default
    return u'%s' % value

def asStringOrEmpty(s):
    if s is None:
        return ''
    return asString(s)

def asRoundedOrZeroString(s):
    return '%d' % round(asFloat(s) or 0)

def shrink(s):
    return (s or '').strip().replace(' ', '').replace('\t', '')

def removeWhiteSpace(s):
    u"""Vacuum s by removing all white space."""
    for c in WHITESPACE:
        s = s.replace(c, '')
    return s

def strippedString(s):
    return (s or '').strip()

def list2SpacedString(l):
    return list2String(l, ' ')

def list2StringList(l):
    strings = []
    for element in l:
        if not isinstance(element, basestring):
            element = '%s' % element
        strings.append(element)
    return strings

def list2CommaString(l):
    return list2String(l, ',')

def value2IdCommaString(value):
    u"""Transform a list with numbers into a comma separated string. This can be used to convert a list of record ids
    into a SQL compatible list of ids, without integers showing up as @1234L@."""
    t = []
    if not isinstance(value, (set, list, tuple)):
        value = str(value).split(',')
    for item in value:
        if isInt(item):
            t.append('%s' % item) # Avoid longs show up as 1234L
    return ', '.join(t)

def idCommaString2IdSet(s):
    u"""Transform a string with comma separated items into a set of id integers."""
    t = set()
    if s is not None:
        for value in s.split(','):
            value = asInt(value)
            if value is not None:
                t.add(value)
    return t

def commaString2IntegerList(s):
    l = []
    for word in commaString2List(s):
        number = asInt(word)
        if number is not None:
            l.append(number)
    return l

def list2String(l, separator=''):
    return separator.join([asString(ll) for ll in l])

PLAINWORDS = re.compile('([a-z0-9_\<\>]*)')

def string2PlainWords(s):
    return PLAINWORDS.findall(s.lower())

def string2WordsKey(s):
    words = string2PlainWords(s)
    return words2WordsKey(words)

def words2WordsKey(words):
    k = []
    words.sort()
    for word in words:
        if word:
            k.append(word)
    return '_'.join(k)

# ---------------------------------------------------------------------------------------------------------
#    S T Y L E

def obj2StyleId(s):
    u"""Make sure s is styleId format, other recursively transform into string with space separators.
    Parts can be CSS-like #id and .class identifiers.
    Note that this may change in the future if more compatibility with CSS is necessary."""
    styleId = []
    if isinstance(s, (list, tuple)):
        for sPart in s:
            styleId.append(obj2StyleId(sPart))
        return ' '.join(styleId)

    if not isinstance(s, basestring):
        s = u'%s' % s
    for sPart in s.split(' '):
        if sPart:
            styleId.append(sPart)
    return ' '.join(styleId)

def obj2StyleIds(s):
    print s
    return obj2StyleId(s).split(' ')

# ---------------------------------------------------------------------------------------------------------
#    P A T H

def module2Path(module):
    return '/'.join((module.__file__).split('/')[:-1])

def path2ParentPath(path):
    u"""
    >>> path2ParentPath('/xxx/yyy/zzz/')
    '/xxx/yyy/zzz'
    >>> path2ParentPath('/xxx/yyy/zzz')
    '/xxx/yyy'
    >>> path2ParentPath('/xxx/yyy/zzz.gif')
    '/xxx/yyy'
    """
    return '/'.join(path.split('/')[:-1])

def path2ScriptId(path):
    u"""Answer the scriptId, derived from the __file__ of the main source."""
    return path.split('/src/')[-1]

def path2FormatPath(path, format=None):
    u"""Answers the path where the extension is changed to format If format is
    None, then the extension is removed."""
    if path is not None:
        path = '.'.join(path.split('.')[:-1])
        if format is not None:
            path += '.' + format
        return path
    return None

def path2Name(path):
    u"""Answers the file name part of the path."""
    if path is None:
        return None
    if not path:
        return 'Untitled'
    return path.split('/')[-1]

def path2FontName(path):
    u"""
    Take that file part of the path, and get the chunk until the first
    period to remove the extension, version numbers and the database download
    ID.

    /xxx/yyy/zzz/Agency_FB-Compressed.ufo becomes Agency_FB-Compressed
    /xxx/yyy/zzz/Agency_FB-Compressed.version01.ufo becomes Agency_FB-Compressed
    #xxx/yyy/zzz/Agency_FB-Bold.0001646411.ufo becomes Agency_FB-Bold

    >>> from pagebot.toolbox.transformer import *
    >>> path2FontName('/xxx/yyy/zzz/Agency_FB-Compressed.ufo')
    'Agency_FB-Compressed'
    >>> path2FontName('/xxx/yyy/zzz/Agency_FB-Compressed.version01.ufo')
    'Agency_FB-Compressed'
    >>> path2FontName('#xxx/yyy/zzz/Agency_FB-Bold.0001646411.ufo')
    'Agency_FB-Bold'
    """
    name = path2Name(path)
    if name is not None:
        return name.split('.')[0]
    return 'Untitled'

path2GlyphIdName = path2FontName

def path2HintPath(path):
    return path2FormatPath(path, 'autohint.ttf')

def path2FontId(path):
    u"""
    <doc>Answers the font ID for the font associated with this path. If the path does not exist, or if the font name
    is invalid, then answer None.<doc>
    """
    if path is not None:
        name = path2Name(path)
        return name
    return None

# ---------------------------------------------------------------------------------------------------------
#    F O N T

def font2Name(font):
    name = None

    if font is not None:
        name = path2Name(font2Path(font))

        if name is None and font.info: # The font may not have been saved yet, then there is no filename.
            if (font.info.styleMapFamilyName or font.info.familyName):
                name = (font.info.styleMapFamilyName or font.info.familyName)
                if name and font.info.styleName:
                    name += '-' + font.info.styleName
    if name is None:
        name = 'Untitled'
    return name

def font2FileName(font):
    u"""Answer the font file name. In case of a new unsaved font,
    answer *"Untitled"*."""
    return (font.path or 'Untitled').split('/')[-1]

def font2Naked(font):
    if font is not None and hasattr(font, 'naked'):
        font = font.naked()
    return font

def font2Path(font):
    if font2Naked(font) is None:
        return None
    return font.path

def font2ID(font):
    u"""Answer the unique record/adapter ID of the font/style. This can be the unique database record id
    or the unique file path. For now we just answer the file path."""
    return font2Path(font)

def font2FamilyID(font):
    u"""Answer the unique record/adapter ID of the family of *font*. This can be the unique database
    record id of the font parent or the unique directory path of the font. For now we just answer the
    the location of the family plist file.
    Special situation is if the font is not saved yet. In that case it does not have a path."""
    fontPath = font2Path(font)
    if fontPath is not None:
        return path2ParentPath(fontPath) + '/' + font2FamilyName(font) + '.plist'
    return None

def font2FamilyName(font):
    return fontName2FamilyName(font2Name(font))

def font2StyleName(font):
    return fontName2StyleName(font2Name(font))

def fontName2FamilyName(name):
    u"""For now take the chunk up till "-" in the filename and ignore the family name as set in the font.info
    Also make sure that the extension is removed, if the font has no "-" it isn't name. Relay-Medium_Italic.ufo
    becomes Relay. ThisFont.ufo becomes ThisFont.
    """
    return name.split('.')[0].split('-')[0]

def fontName2StyleName(name):
    return '-'.join(name.split('.')[0].split('-')[1:])

def font2UfoQueryName(font):
    key = 'com.typenetwork.ufoqueryname'
    name = font.lib.get(key)
    if name is None:
        name = font.lib[key] = font2Name(font)
    return name

def family2UfoQueryName(font):
    key = 'com.typenetwork.ufoqueryfamilyname'
    name = font.lib.get(key)
    if name is None:
        name = font.lib[key] = font2FamilyName(font)
    return name

# ---------------------------------------------------------------------------------------------------------
#    G E N E R A T O R

def uniqueID(obj=None):
    if obj is not None:
        return '%X%X' % (long(time()) * 100, id(obj))
    return '%x' % (long(time()) * 100000 + randint(0, 100000))

# ---------------------------------------------------------------------------------------------------------
#   T I M E

def seconds2Date(seconds, year=1904):
    u"""Answer TTF seconds converted to a datetime instance."""
    return datetime.datetime(year, 1, 1, 0, 0, 0) + datetime.timedelta(seconds=seconds)

def date2Seconds(dt, year=1904):
    u"""Answer the datetime converted to TTF seconds."""
    return int((dt - datetime.datetime(year, 1, 1, 0, 0, 0)).total_seconds())

# ---------------------------------------------------------------------------------------------------------
#    J S O N
#
#    Note that Status now has its own json conversion.

def json2Dict(src):
    try:
        return json.loads(src)
    except TypeError:
        return None

def dict2Json(d):
    return json.dumps(d, indent=4)

def json2List(src):
    try:
        return json.loads(src)
    except TypeError:
        return None

def list2Json(d):
    return json.dumps(d, indent=4)


# ---------------------------------------------------------------------------------------------------------
#    R O M A N  N U M E R A L S

def arabic2RomanNumerals(arabic):
    u"""
    <doc>Return the roman numeral representing n. Should work for n in (1, 4999). Borrowed from Nick Montfort.</doc>
    """
    numerals = [(value, numeral) for numeral, value in ROMAN_NUMERAL_VALUES.items()]
    numerals.sort()
    numerals.reverse()
    smaller = {1000: (100, 'C'), 500: (100, 'C'),
               100: (10, 'X'), 50: (10, 'X'), 10: (1, 'I'),
               5: (1, 'I')}
    roman = ''
    for (value, numeral) in numerals:
        roman += (arabic / value) * numeral
        arabic -= (arabic / value) * value
        if value in smaller and arabic >= value - smaller[value][0]:
            roman += smaller[value][1] + numeral
            arabic -= (value - smaller[value][0])
    return roman

""" -- "values" is error here
def romanNumeral2Arabic(roman, VERBOSE=False):
    letters = list(roman)
    letters.reverse()
    arabic = 0
    place = 0
    for letter in letters:
        if VERBOSE: print letter, place
        value = values[letter]
        if value >= place:
            arabic += value
            if VERBOSE: print '\t+', value
        else:
            arabic -= value
            if VERBOSE: print '\t-', value
        place = value
    return arabic
"""
# ---------------------------------------------------------------------------------------------------------
#    U N I C O D E

def dec2hex(n, uni=1):
        hex = "%X" % n
        if uni == 1:
            while len(hex) <= 3:
                hex = '0' + str(hex)
        return hex

def hex2dec(s):
        try:
            return int(s, 16)
        except:
            pass

def hex2char(hex):
    try:
        return unichr(hex2dec(hex))
    except:
        pass

def writeUnicode(unicodeString):
        u"""
        <doc>Takes a unicode string and returns a decimal integer.</doc>
        """
        if type(unicodeString) is str:
            return hex2dec(unicodeString)
        else:
            return int(unicodeString)

def readUnicode(unicodeInteger):
    u"""
    <doc>Takes a decimal integer and returns a unicode string.</doc>
    """
    if type(unicodeInteger) is int:
        return dec2hex(unicodeInteger)
    else:
        return str(unicodeInteger)

def writeUnicodes(uniStringList):
    u"""
    <doc>Takes a list of unicode strings and returns a list of robofab-friendly integers.</doc>
    """
    intList = []
    for u in uniStringList:
        intList.append(writeUnicode(u))
    return intList

def readUnicodes(uniIntList):
        u"""
        <doc>takes a list of robofab friendly integers and returns a string of unicodes.</doc>
        """
        stringList = []
        for u in uniIntList:
            stringList.append(readUnicode(u))
        return stringList

# ---------------------------------------------------------------------------------------------------------
# Floq field name conversion between Floq attributes and database fields

def floq2Field(floqName):
    if floqName.endswith('ID'):
        return floqName[:-2]+'_id'
    return floqName

def field2Floq(fieldName):
    if fieldName.endswith('_id'):
        return fieldName[:-3]+'ID'
    return fieldName

# ---------------------------------------------------------------------------------------------------------
#    T T X

def formatBinaryForTTX(b, length=32, segments=8):
    import string
    s = str(b)[2:]
    prefix = '0' * (length - len(s))
    s = prefix + s
    sWithSpaces = "".join(s[i:i + segments] + " " for i in xrange(0, len(s), segments))
    return string.strip(sWithSpaces)

# ----------------------------------------------------------------------------------------------------------
# Python Objects

def isUniqueList(l):
    try:
        if len(l) == len(set(l)):
            return True
        else:
            return False
    except:
        return False

def makeUniqueList(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def isUniqueDict(d):
    if isUniqueList(d.values()):
        return True
    else:
        return False

def reverseDict(d):
    if not isUniqueDict(d):
        usedValues = []
        duplicateValues = []
        for v in d.values():
            if v in usedValues:
                duplicateValues.append(v)
            usedValues.append(v)

        print 'Warning: duplicate values found', duplicateValues

    newDict = {}
    keys = d.keys()
    keys.sort()
    for k in keys:
        v = d[k]
        if isinstance(v, list):
            v = tuple(v)
        newDict[v] = k
    return newDict

def bash(cmd, cwd=None):
    u"""
    <doc>Runs a command in the bash shell.</doc>
    """
    import subprocess
    retVal = subprocess.Popen(cmd, shell=True, \
        stdout=subprocess.PIPE, cwd=cwd).stdout.read().strip('\n').split('\n')
    if retVal == ['']:
        return(0)
    else:
        return(retVal)

# ----------------------------------------------------------------------------------------------------------
# XML  transformers.

def dataAttribute2Html5Attribute(key):
    u"""The @dataAttribute2Html5Attribute@ method converts an *key*
    attribute that starts with @'data_'@ to the HTML5 attribute that starts
    with @'data-'@. Otherwise the *key* attribute is answered unchanged.
    """
    if key.startswith(u'data_'):
        return 'data-' + key[5:]
    return key

def pyAttrName2XmlAttrName(key):
    u"""
    The @pyAttrName2XmlAttrName@ converts the Python XML attribute name @key@ to an
    appropriate XML attribute identifier.
    If the *key* is @'class_'@ then it is translated into @'class'@.
    If there is an HTML5 attribute *data_xxxx* used, then change that to *data-xxxx*.
    """
    if key == 'class_':
        key = 'class'
    if key.startswith('data'):
        key = key.replace('_', '-')
    return key

def xmlAttrName2PyAttrName(key):
    u"""The @xmlAttrName2PyAttrName@ method converts the XML attribute name
    *key* to an appropriate Python attribute identifier.
    If the *key* is @'class'@ then it is translated into @'class_'@. If a
    namespace is defined (to be recognized on {...}, then replace that by
    prefix @'ns_'@. If there is an HTML5 attribute *data-xxxx* used,
    then change that to *data_xxxx*."""
    if key == 'class':
        key = 'class_'
    elif key.startswith('{'):
        key = 'ns_' + key.split('}')[-1]
    elif '-' in key:
        # In case of new HTML5 data-xxxx attributes.
        key = key.replace('-', '_')
    return key

def xmlValue2PyValue(value, conversions):
    u"""The @xmlValue2PyValue@ method converts the XML string attribute to
    the appropriate Python object type, if the class is defined in the list
    *conversions*. If the *value* is not a string, it must have been
    converted before (e.g. by self.EXPR), the answer it untouched."""
    if not isinstance(value, basestring):
        return value

    strippedvalue = value.strip()

    if int in conversions:
        try:
            return int(strippedvalue)
        except ValueError:
            pass

    if long in conversions:
        try:
            return long(strippedvalue)
        except ValueError:
            pass

    if float in conversions:
        try:
            return float(strippedvalue)
        except ValueError:
            pass

    if bool in conversions:
        if strippedvalue.lower() in ['true', 'false']:
            return strippedvalue.lower() == 'true'

    if dict in conversions or list in conversions or tuple in conversions:
        if ((strippedvalue.startswith('{') and strippedvalue.endswith('}')) or
            (strippedvalue.startswith('[') and strippedvalue.endswith(']')) or
            (strippedvalue.startswith('(') and strippedvalue.endswith(')'))):
            try:
                # In theory this is a security leak, since there maybe
                # "strange" objects inside the dictionary. Problem to be
                # solved in the future?
                return eval(strippedvalue)
            except (SyntaxError, NameError):
                pass

    # Can't do anything with this value. Return unstripped and untouched.
    return value

# Remove all tags from the string
REMOVETAGS = re.compile(r'<.*?>')

def stripTags(xml):
    return REMOVETAGS.sub('', xml)

def addHtmlBreaks(s, isXhtml=True):
    u"""Replace all returns by <br/> or <br>."""
    tag = {True:'<br/>\n', False:'<br>\n'}[isXhtml]
    return s.replace('\n',tag)

REMOVEMULTIPLEWHITESPACE = re.compile(r'\n\s+')

def stripMultipleWhiteLines(s):
    return REMOVEMULTIPLEWHITESPACE.sub('\n\n', s)

# support single or double quotes while ignoring quotes preceded by \
XMLATTRS = re.compile(r'''([A-Z][A-Z0-9_]*)\s*=\s*(?P<quote>["'])(.*?)(?<!\\)(?P=quote)''', re.IGNORECASE)

def xmlAttrString2PyAttr(s, conversions):
    attrs = {}
    for key, _, value in XMLATTRS.findall(s):
        attrs[key] = value
    return cls.xmlAttr2PyAttr(attrs, conversions)

def xmlAttr2PyAttr(par_dict, conversions):
    """Transforms an XML attribute dictionary to a Python attribute
    dictionary. The *class* attribute name is translated into *class_* and
    all values are tested to convert into either @int@, @long@, @float@ or
    boolean as represented by one of @'TRUE'@, @True@, @true@, @FALSE@,
    @False@, @false@. If the conversion fails, then pass the value
    unchanged. If there the attribute name is of format

    @'{http://www.w3.org/XML/1998/namespace}space'@

    e.g. as generated by Xopus XML Schema, then just remove the name space
    prefix. If there is an HTML5 attribute *data-xxxx* used, then change
    that to *data_xxxx*."""
    pydict = {}

    for key, value in par_dict.items():
        key = cls.xmlAttrName2PyAttrName(key)
        value = cls.xmlValue2PyValue(value, conversions)
        pydict[key] = value
    return pydict

def tableField2JoinedField(table, field):
    if field.startswith(table):
        return field
    return '%s_%s' % (table, field)

def value2TagName(value):
    u"""
    The @value2TagName@ class method converts the *value* object into a value XML tag name.
    """
    tagname = []
    if not isinstance(value, basestring):
        value = `value`
    if value.lower().startswith('xml'):
        tagname.append('_')
    for c in value:
        if c in ' !?@#$%^&*()[]\t\r\n/\\':
            pass
        elif c.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_1234567890:.':
            tagname.append(c)
        else:
            tagname.append('_')
    return ''.join(tagname)

def object2SpacedString(o):
    return `o`
    
