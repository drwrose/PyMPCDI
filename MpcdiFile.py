import zipfile
from xml.etree import ElementTree
import PfmFile
import TextureImage
import os.path

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

class BufferDef:
    def __init__(self, xbuffer):
        self.id = xbuffer.attrib['id']

        # Integer properties
        for keyword in ['Xresolution', 'Yresolution']:
            value = xbuffer.attrib[keyword]
            if value:
                value = int(value)
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
        if xframe:
            self.frame = FrameDef(xframe)

        print "Found region %s of size %s, %s" % (self.id, self.Xresolution, self.Yresolution)

    def addFileset(self, xfileset):
        for keyword in ['geometryWarpFile', 'alphaMap', 'distortionMap']:
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
