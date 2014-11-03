from TextureImage import TextureImage
from OpenGL.GL import *
from PIL import Image

class MpacsWarp2D:
    """ The base class for performing warping in the "2d" profile
    specified in the mpcdi file.  This warps media according to a 2-d
    pfm file and applies a blending map. """
    
    def __init__(self, mpcdi, region):
        self.mpcdi = mpcdi
        self.region = region

        # This class only supports the "2d" profile.
        assert self.mpcdi.profile == '2d'

        self.mediaFilename = None
        self.media = None

        self.outputFilename = None

        self.pfm = self.mpcdi.extractPfmFile(self.region.geometryWarpFile.path)
        self.blend = self.mpcdi.extractTextureImage(self.region.alphaMap.path)

        # This is the gamma value of the embedded alpha map.
        self.blendGamma = self.region.alphaMap.gammaEmbedded

        # This is the gamma value we will want to display.
        self.targetGamma = self.blendGamma

        # This is the gamma value of the source media image.
        self.mediaGamma = self.blendGamma
        
    def setMediaFilename(self, mediaFilename):
        self.mediaFilename = mediaFilename
        self.media = TextureImage(self.mediaFilename)
        
    def setOutputFilename(self, outputFilename):
        self.outputFilename = outputFilename

    def saveOutputImage(self):
        """ Saves a screenshot to the indicated filename for reference. """
        if not self.outputFilename:
            return
        
        external_format = GL_RGBA
        component_type = GL_UNSIGNED_BYTE
        width = self.region.XResolution
        height = self.region.YResolution        
        buffer = glReadPixels(0, 0, width, height, external_format, component_type)
        img = Image.fromstring(mode="RGBA", size=(width, height), data = buffer)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(self.outputFilename)
        print self.outputFilename

        # Don't do this again next frame; just do it once.
        self.outputFilename = None

    def initGL(self):
        self.media.initGL()

        
