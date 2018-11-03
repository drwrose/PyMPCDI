from TextureImage import TextureImage
from OpenGL.GL import *
from PIL import Image
import sys

class MpacsWarp2D:
    """ The base class for performing warping in the "2d" profile
    specified in the mpcdi file.  This warps media according to a 2-d
    pfm file and applies a blending map. """

    def __init__(self, mpcdi, region):
        self.mpcdi = mpcdi
        self.region = region

        # This class only supports the "2d" profile.
        assert self.mpcdi.profile == '2d'

        self.windowSize = self.region.Xresolution, self.region.Yresolution

        self.mediaFilename = None
        self.media = None

        self.outputFilename = None
        self.includeBlend = True

        self.pfm = self.mpcdi.extractPfmFile(self.region.geometryWarpFile.path)

        # If an alpha map is included, it is the primary blend map,
        # and is used to darken the whites.
        if self.region.alphaMap:
            self.alpha = self.mpcdi.extractTextureImage(self.region.alphaMap.path)
            # This is the gamma value of the embedded alpha map.
            self.alphaGamma = self.region.alphaMap.gammaEmbedded
        else:
            self.alpha = TextureImage(flat = ('L', (self.pfm.xSize, self.pfm.ySize), 255))
            self.alphaGamma = 1.0

        # If a beta map is included, it is a "black level uplift" map,
        # used to brighten the blacks.
        if self.region.betaMap:
            self.beta = self.mpcdi.extractTextureImage(self.region.betaMap.path)
            # This is the gamma value of the embedded beta map.
            self.betaGamma = self.region.betaMap.gammaEmbedded
        else:
            self.beta = TextureImage(flat = ('L', (self.pfm.xSize, self.pfm.ySize), 0))
            self.betaGamma = 1.0


        # This is the gamma value we will want to display.
        self.targetGamma = self.alphaGamma

        # This is the gamma value of the source media image.
        self.mediaGamma = self.alphaGamma

    def setWindowSize(self, windowSize):
        self.windowSize = windowSize

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
        width, height = self.windowSize
        buffer = glReadPixels(0, 0, width, height, external_format, component_type)
        img = Image.frombytes(mode="RGBA", size=(width, height), data = buffer)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        img.save(self.outputFilename)
        print self.outputFilename

    def initGL(self):
        self.media.initGL()
