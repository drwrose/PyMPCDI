from OpenGL.GL import *
import numpy

class BlendQuad:
    """ A single 1x1 quad drawn over the screen, for applying a blending map. """

    def __init__(self, alpha):
        self.alpha = alpha

    def initGL(self):
        self.alpha.initGL()

        # Create a VBO with two triangles to make a unit quad.
        verts = [
            [0, 1], [1, 0], [1, 1],
            [0, 1], [1, 0], [0, 0],
            ]
        verts = numpy.array(verts, dtype = 'float32')
        self.vertdata = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)
        self.alpha.apply()

        glBlendFunc(GL_ZERO, GL_SRC_COLOR)
        glEnable(GL_BLEND)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glVertexPointer(2, GL_FLOAT, 0, None)
        glTexCoordPointer(2, GL_FLOAT, 0, None)

        glColor3f(1.0, 1.0, 1.0)

        glDrawArrays(GL_TRIANGLES, 0, 6)

        glPopClientAttrib()
        glPopAttrib()
