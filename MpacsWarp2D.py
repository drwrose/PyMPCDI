from MpacsWarp import MpacsWarp
from TextureImage import TextureImage
from OpenGL.GL import *
from PIL import Image
import sys

class MpacsWarp2D(MpacsWarp):
    """ The base class for performing warping in the "2d" profile
    specified in the mpcdi file.  This warps media according to a 2-d
    pfm file and applies a blending map. """

    def __init__(self, mpcdi, region):
        MpacsWarp.__init__(self, mpcdi, region)

        # This class only supports the "2d" profile.
        assert self.mpcdi.profile == '2d'

        self.warp = self.mpcdi.extractPfmFile(self.region.geometryWarpFile.path)

    def setWindowSize(self, windowSize):
        MpacsWarp.setWindowSize(self, windowSize)
        #self.warp = self.mpcdi.extractPfmFile(self.region.geometryWarpFile.path)

    def initGL(self):
        MpacsWarp.initGL(self)
