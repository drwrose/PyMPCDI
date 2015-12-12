from PIL import Image
from OpenGL.GL import *
from cStringIO import StringIO
import numpy

useMipmapping = False

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
        if img.mode not in ['RGB', 'L', 'I']:
            img = img.convert('RGB')

        self.texobj = glGenTextures(1)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, self.texobj)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        if useMipmapping:
            # Enable mipmapping (i.e. trilinear filtering) to soften
            # out the subsampling artifacts.
            glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, GL_TRUE)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        else:
            # Just use bilinear filtering.
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        if img.mode == 'I':
            # PIL mode 'I': integer 32-bit pixels.  This is how PIL
            # loads 16-bit image files.
            img_data = numpy.fromstring(img.tobytes(), dtype = 'uint32')
            num_pixels = img.size[0] * img.size[1]
            type = GL_UNSIGNED_SHORT

            if len(img_data) == num_pixels:
                # Must be grayscale.
                format = GL_LUMINANCE
            elif len(img_data) == num_pixels * 3:
                # Must be RGB.
                format = GL_RGB
            elif len(img_data) == num_pixels * 4:
                # Must be RGBA.
                format = GL_RGBA
            else:
                # What could it be?
                assert False
        else:
            # Otherwise, it's an 8-bit format.
            type = GL_UNSIGNED_BYTE
            if img.mode == 'RGB':
                format = GL_RGB
            elif img.mode == 'L':
                format = GL_LUMINANCE
            else:
                assert False
            img_data = numpy.fromstring(img.tobytes(), dtype = 'uint8')

        glTexImage2D(GL_TEXTURE_2D, 0, format, img.size[0], img.size[1], 0, format, type, img_data)

    def apply(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.texobj)
        glEnable(GL_TEXTURE_2D)
