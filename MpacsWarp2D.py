from TextureImage import TextureImage

class MpacsWarp2D:
    """ The base class for performing warping in the "2d" profile
    specified in the mpcdi file.  This warps media according to a 2-d
    pfm file and applies a blending map. """
    
    def __init__(self, mpcdi, region):
        self.mpcdi = mpcdi
        self.region = region

        # This class only supports the "2d" profile.
        assert self.mpcdi.profile == '2d'

        self.media = None

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

    def initGL(self):
        self.media.initGL()

        
