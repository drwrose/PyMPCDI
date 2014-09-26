from TextureImage import TextureImage

class MpacsWarp2D:
    """ The base class for performing warping in the "2d" model
    specified in the mpcdi file.  This warps media according to a 2-d
    pfm file and applies a blending map. """
    
    def __init__(self, mpcdi, region):
        self.mpcdi = mpcdi
        self.region = region

        self.media = None

        self.pfm = self.mpcdi.extractPfmFile(self.region.geometryWarpFile.path)
        print self.pfm.xSize, self.pfm.ySize, self.pfm.scale
        self.blend = self.mpcdi.extractTextureImage(self.region.alphaMap.path)

        self.gamma = self.region.alphaMap.gammaEmbedded
        self.offset = (self.region.x, self.region.y)
        self.scale = (self.region.xsize, self.region.ysize)
        
    def setMediaFilename(self, mediaFilename):
        self.mediaFilename = mediaFilename
        self.media = TextureImage(self.mediaFilename)

    def initGL(self):
        self.media.initGL()

        
