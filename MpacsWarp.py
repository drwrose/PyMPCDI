from TextureImage import TextureImage
from OpenGL.GL import *
from PIL import Image
import sys

class MpacsWarp:
    """ The base class for all kinds of MPCDI profiles. """

    def __init__(self, mpcdi, region):
        self.mpcdi = mpcdi
        self.region = region

        self.windowSize = self.region.Xresolution, self.region.Yresolution

        self.outputFilename = None
        self.includeBlend = True

        self.blend = self.mpcdi.extractTextureImage(self.region.alphaMap.path)

        # This is the gamma value of the embedded alpha map.
        self.blendGamma = self.region.alphaMap.gammaEmbedded

        # This is the gamma value we will want to display.
        self.targetGamma = self.blendGamma

    def setWindowSize(self, windowSize):
        self.windowSize = windowSize

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
        pass
