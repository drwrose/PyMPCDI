from MpacsWarp import MpacsWarp
from ObjFile import ObjFile
from OpenGL.GL import *
import sys

class MpacsWarp3D(MpacsWarp):
    """ The base class for performing warping in the "3d", "a3", and
    "sl" profiles specified in the mpcdi file.  In addition to the
    regular media file, we also accept a model file, an obj file
    describing a simple 3-D scene. """

    def __init__(self, mpcdi, region):
        MpacsWarp.__init__(self, mpcdi, region)

        assert self.mpcdi.profile in ['3d', 'a3', 'sl']

    def initGL(self):
        MpacsWarp.initGL(self)
