from PIL import Image
from OpenGL.GL import *
from cStringIO import StringIO
import numpy

class TextureImage:
    """ A basic 2-d OpenGL texture image, as loaded from (for instance) a png file. """
    
    def __init__(self, filename = None, data = None):
        self.filename = filename
        self.data = data
        self.texobj = None

    def __read(self):
        if self.data:
            return Image.open(StringIO(self.data))
        if self.filename:
            return Image.open(self.filename)

        assert False

    def initGL(self):
        img = self.__read()
        if img.mode not in ['RGB', 'L']:
            img = img.convert('RGB')
            
        img_data = numpy.fromstring(img.tostring(), dtype = 'uint8')

        self.texobj = glGenTextures(1)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, self.texobj)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        if img.mode == 'RGB':
            format = GL_RGB
        elif img.mode == 'L':
            format = GL_LUMINANCE
        else:
            assert False
        
        glTexImage2D(GL_TEXTURE_2D, 0, format, img.size[0], img.size[1], 0, format, GL_UNSIGNED_BYTE, img_data)
        
    def apply(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texobj)
        glEnable(GL_TEXTURE_2D)
        
