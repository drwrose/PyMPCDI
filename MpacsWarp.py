from TextureImage import TextureImage
from ObjFile import ObjFile
from OpenGL.GL import *
from PIL import Image
import sys

class MpacsWarp:
    """ The base class for all kinds of MPCDI profiles. """

    def __init__(self, mpcdi, region):
        self.mpcdi = mpcdi
        self.region = region

        self.windowSize = self.region.Xresolution, self.region.Yresolution

        self.mediaFilename = None
        self.media = None

        self.modelFilename = None
        self.model = None

        self.outputFilename = None

        # If an alpha map is included, it is the primary blend map,
        # and is used to darken the whites.
        if self.region.alphaMap:
            self.alpha = self.mpcdi.extractTextureImage(self.region.alphaMap.path)
            # This is the gamma value of the embedded alpha map.
            self.alphaGamma = self.region.alphaMap.gammaEmbedded
        else:
            self.__makeDefaultAlpha()

        # If a beta map is included, it is a "black level uplift" map,
        # used to brighten the blacks.
        if self.region.betaMap:
            self.beta = self.mpcdi.extractTextureImage(self.region.betaMap.path)
            # This is the gamma value of the embedded beta map.
            self.betaGamma = self.region.betaMap.gammaEmbedded
        else:
            self.__makeDefaultBeta()

        # This is the gamma value we will want to display.
        self.targetGamma = self.alphaGamma

        # This is the gamma value of the source media image.
        self.mediaGamma = self.alphaGamma

        # This is the gamma value of the embedded alpha map.
        self.blendGamma = self.region.alphaMap.gammaEmbedded

        # This is the gamma value we will want to display.
        self.targetGamma = self.blendGamma

    def disableBlend(self):
        # Turn off blending by clearing the alpha and beta maps.
        self.__makeDefaultAlpha()
        self.__makeDefaultBeta()

    def __makeDefaultAlpha(self):
        self.alpha = TextureImage(flat = ('L', self.windowSize, 255))
        self.alphaGamma = 1.0

    def __makeDefaultBeta(self):
        self.beta = TextureImage(flat = ('L', self.windowSize, 0))
        self.betaGamma = 1.0

    def setWindowSize(self, windowSize):
        self.windowSize = windowSize

    def setMediaFilename(self, mediaFilename):
        self.mediaFilename = mediaFilename
        self.media = TextureImage(self.mediaFilename)

    def setModelFilename(self, modelFilename):
        self.modelFilename = modelFilename
        self.model = ObjFile(self.modelFilename)

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
