from OpenGL.GL import *
import numpy

class BlendQuad:
    """ A single 1x1 quad drawn over the screen, for applying a blending map. """

    def __init__(self, blend):
        self.blend = blend

    def initGL(self):
        pass
                
    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        self.blend.apply()

        glBlendFunc(GL_ZERO, GL_SRC_COLOR)
        glEnable(GL_BLEND)
        
        glBegin(GL_QUADS)
        glColor3f(1.0, 1.0, 1.0)

        glTexCoord2f(0, 1)
        glVertex2f(0, 1)

        glTexCoord2f(1, 1)
        glVertex2f(1, 1)

        glTexCoord2f(1, 0)
        glVertex2f(1, 0)

        glTexCoord2f(0, 0)
        glVertex2f(0, 0)
        
        glEnd()
        glPopAttrib(GL_ENABLE_BIT)
        
