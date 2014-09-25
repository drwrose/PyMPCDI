import zipfile
from xml.etree import ElementTree
import PfmFile

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
        self.zip = zipfile.ZipFile(self.filename, 'r')
        docData = self.extractSubfile('mpcdi.xml')
        self.doc = ElementTree.fromstring(docData)

        self.profile = None
        self.buffers = {}
        self.regions = {}
        
        self.profile = self.doc.attrib['profile']

        xdisplay = self.doc.find('display')
        for xbuffer in xdisplay.iter('buffer'):
            buffer = BufferDef(xbuffer)
            self.buffers[buffer.id] = buffer

            for xregion in xbuffer.iter('region'):
                region = RegionDef(buffer, xregion)
                self.regions[region.id] = region

        xfiles = self.doc.find('files')
        for xfileset in xfiles.iter('fileset'):
            regionName = xfileset.attrib['region']
            region = self.regions[regionName]
            region.addFileset(xfileset)

    def extractSubfile(self, filename):
        """ Returns the string data from the subfile within the mpcdi
        file with the given name. """
        
        return self.zip.read(filename)

    def extractPfmFile(self, filename):
        """ Returns a PfmFile object corresponding to the named
        file.pfm within the mpcdi file. """

        data = self.extractSubfile(filename)
        return PfmFile.PfmFile(filename = filename, data = data)

class BufferDef:
    def __init__(self, xbuffer):
        self.id = xbuffer.attrib['id']

        # Integer properties
        for keyword in ['XResolution', 'YResolution']:
            value = xbuffer.attrib[keyword]
            if value:
                value = int(value)
            setattr(self, keyword, value)

class RegionDef:
    def __init__(self, buffer, xregion):
        self.buffer = buffer
        self.id = xregion.attrib['id']
        self.XResolution = None
        self.YResolution = None

        # Integer properties
        for keyword in ['XResolution', 'YResolution']:
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

    def addFileset(self, xfileset):
        for keyword in ['geometryWarpFile', 'alphaMap', 'distortionMap']:
            xfile = xfileset.attrib.get(keyword, None)
            if xfile:
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
            if xe:
                value = int(xe.text)
            else:
                value = None
            setattr(self, keyword, value)
            
        # Float properties
        for keyword in ['gammaEmbedded']:
            xe = xfile.FirstChildElement(keyword)
            if xe:
                value = float(xe.text)
            else:
                value = None
            setattr(self, keyword, value)
