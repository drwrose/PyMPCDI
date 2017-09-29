from MpacsWarp import MpacsWarp
from TextureImage import TextureImage
from OpenGL.GL import *
from PIL import Image
import sys

class MpacsWarp3D(MpacsWarp):
    """ The base class for performing warping in the "3d", "a3", and
    "sl" profiles specified in the mpcdi file.  The media file in this
    case is an obj file describing a simple 3-D scene. """

    def __init__(self, mpcdi, region):
        MpacsWarp.__init__(self, mpcdi, region)

        # This class only supports the "2d" profile.
        assert self.mpcdi.profile == '2d'

        self.mediaFilename = None
        self.media = None

    def setMediaFilename(self, mediaFilename):
        self.mediaFilename = mediaFilename
        self.media = TextureImage(self.mediaFilename)

    def initGL(self):
        MpacsWarp.initGL(self)
        self.media.initGL()
