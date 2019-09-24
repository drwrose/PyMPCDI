import zipfile
from xml.etree import ElementTree
import PfmFile
import TextureImage
import os.path
from MpacsWarp2DShader import MpacsWarp2DShader
from MpacsWarp2DFixedFunction import MpacsWarp2DFixedFunction
from MpacsWarpSL import MpacsWarpSL

class MpcdiFile:
    def __init__(self, filename = None):
        self.filename = None
        self.zip = None
        self.doc = None
        self.profile = None
        self.buffers = {}
        self.regions = {}

        if filename:
            self.read(filename)

    def read(self, filename):
        """ Reads the mpcdi file and sets up the corresponding data
        structures internally. """

        self.filename = filename
        print "Reading %s" % (self.filename)

        if os.path.isdir(self.filename):
            # Read a directory directly
            self.zip = None
        else:
            # Read a zipfile via the ZipFile module
            self.zip = zipfile.ZipFile(self.filename, 'r')

        docData = self.extractSubfile('mpcdi.xml')
        self.doc = ElementTree.fromstring(docData)

        self.profile = None
        self.buffers = {}
        self.regions = {}
        self.regionIdList = []  # sorted in file order

        self.profile = self.doc.attrib['profile']

        xdisplay = self.doc.find('display')
        for xbuffer in xdisplay.iter('buffer'):
            buffer = BufferDef(xbuffer)
            self.buffers[buffer.id] = buffer

            for xregion in xbuffer.iter('region'):
                region = RegionDef(buffer, xregion)
                self.regions[region.id] = region
                self.regionIdList.append(region.id)

        xfiles = self.doc.find('files')
        for xfileset in xfiles.iter('fileset'):
            regionName = xfileset.attrib['region']
            region = self.regions[regionName]
            region.addFileset(xfileset)

    def extractSubfile(self, filename):
        """ Returns the string data from the subfile within the mpcdi
        file with the given name. """

        if self.zip:
            return self.zip.read(filename)
        else:
            return open(os.path.join(self.filename, filename), 'rb').read()

    def extractPfmFile(self, filename):
        """ Returns a PfmFile object corresponding to the named
        file.pfm within the mpcdi file. """

        data = self.extractSubfile(filename)
        return PfmFile.PfmFile(filename = filename, data = data)

    def extractTextureImage(self, filename):
        """ Returns a TextureImage object corresponding to the named
        file.png within the mpcdi file. """

        data = self.extractSubfile(filename)
        return TextureImage.TextureImage(filename = filename, data = data)

    def makeWarp(self, regionName, useFixedFunction = False):
        """ Returns an appropriate MpacsWarp instance to generate the
        output for the indicated region, according to the MPCDI file's
        profile.  If useFixedFunction is True, we return a
        fixed-function variant if it's available. """

        region = self.regions[regionName]

        if self.profile == '2d':
            if useFixedFunction:
                return MpacsWarp2DFixedFunction(self, region)
            else:
                return MpacsWarp2DShader(self, region)
        elif self.profile == 'sl':
            return MpacsWarpSL(self, region)

        else:
            message = "Not yet implemented: profile %s" % (self.profile)
            raise NotImplementedError, message

class BufferDef:
    def __init__(self, xbuffer):
        self.id = xbuffer.attrib['id']

        # Integer properties
        for keyword in ['Xresolution', 'Yresolution']:
            value = xbuffer.attrib[keyword]
            if value:
                value = int(value)
            setattr(self, keyword, value)

class FrustumDef:
    def __init__(self, xfrustum):

        # Float properties, children of the element
        for keyword in ['yaw', 'pitch', 'roll', 'leftAngle', 'rightAngle', 'downAngle', 'upAngle']:
            value = None
            xchild = xfrustum.find(keyword)
            if xchild is not None:
                value = xchild.text
                if value:
                    value = float(value)
            setattr(self, keyword, value)

class FrameDef:
    def __init__(self, xframe):

        # Float properties, children of the element
        for keyword in ['posx', 'posy', 'posz',
                        'yawx', 'yawy', 'yawz',
                        'pitchx', 'pitchy', 'pitchz',
                        'rollx', 'rolly', 'rollz']:
            value = None
            xchild = xframe.find(keyword)
            if xchild is not None:
                value = xchild.text
                if value:
                    value = float(value)
            setattr(self, keyword, value)

class RegionDef:
    def __init__(self, buffer, xregion):
        self.buffer = buffer
        self.id = xregion.attrib['id']
        self.Xresolution = None
        self.Yresolution = None

        # Integer properties
        for keyword in ['Xresolution', 'Yresolution']:
            value = xregion.attrib[keyword]
            if value:
                value = int(value)
            setattr(self, keyword, value)

        # Float properties
        for keyword in ['x', 'y', 'xsize', 'ysize']:
            value = xregion.attrib[keyword]
            if value:
                value = float(value)
            setattr(self, keyword, value)

        self.frustum = None
        for xfrustum in xregion.iter('frustum'):
            self.frustum = FrustumDef(xfrustum)

        self.frame = None
        xframe = xregion.find('coordinateFrame')
        if xframe is not None:
            self.frame = FrameDef(xframe)

        print "Found region %s of size %s, %s" % (self.id, self.Xresolution, self.Yresolution)

    def addFileset(self, xfileset):
        for keyword in ['geometryWarpFile', 'alphaMap', 'betaMap', 'distortionMap']:
            xfile = xfileset.find(keyword, None)
            if xfile is not None:
                file = FileDef(xfile)
            else:
                file = None

            setattr(self, keyword, file)

class FileDef:
    def __init__(self, xfile):
        self.path = xfile.find('path').text

        # Integer properties
        for keyword in ['componentDepth', 'bitdepth']:
            xe = xfile.find(keyword)
            if xe is not None:
                value = int(xe.text)
            else:
                value = None
            setattr(self, keyword, value)

        # Float properties
        for keyword in ['gammaEmbedded']:
            xe = xfile.find(keyword)
            if xe is not None:
                value = float(xe.text)
            else:
                value = None
            setattr(self, keyword, value)
