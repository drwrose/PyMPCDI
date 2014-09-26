from MpcdiFile import MpcdiFile
import sys
from OpenGL.GL import *
from OpenGL.GLUT import *

from PfmFile import PfmFile
from PfmMesh2D import PfmMesh2D
from TextureImage import TextureImage
from BlendQuad import BlendQuad

mpcdi = MpcdiFile(sys.argv[1])

pfm = mpcdi.extractPfmFile('proj_a_warp.pfm')
print pfm.xSize, pfm.ySize, pfm.scale

tex = TextureImage('color_grid.png')
blend = mpcdi.extractTextureImage('proj_a_blend.png')

mesh = PfmMesh2D(pfm, tex)
card = BlendQuad(blend)

def init():
    tex.initGL()
    blend.initGL()
    mesh.initGL()
    card.initGL()

def draw():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    mesh.draw()
    card.draw()

    glutSwapBuffers()

def key(k, x, y):
    if ord(k) == 27: # Escape
        sys.exit(0)
    else:
        return
    glutPostRedisplay()

def reshape(width, height):
    h = float(height) / float(width);
    glViewport(0, 0, width, height)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, 1, 1, 0, -100, 100)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

if __name__ == '__main__':
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH)

    glutInitWindowPosition(0, 0)
    glutInitWindowSize(960, 540)
    glutCreateWindow("mpcdi")
    init()
    
    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(key)
    #glutSpecialFunc(special)
    #glutVisibilityFunc(visible)

    glutMainLoop()
    
