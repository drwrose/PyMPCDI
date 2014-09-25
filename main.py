from MpcdiFile import MpcdiFile
import sys
from OpenGL.GL import *
from OpenGL.GLUT import *

from PfmFile import PfmFile

mpcdi = MpcdiFile(sys.argv[1])

pfm = PfmFile('t.pfm')
#mpcdi.extractPfmFile('right_warp.pfm')
print pfm.xSize, pfm.ySize, pfm.scale

def init():
    pass

def draw():
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
    glFrustum(-1.0, 1.0, -h, h, 5.0, 60.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -40.0)

if __name__ == '__main__':
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE | GLUT_DEPTH)

    glutInitWindowPosition(0, 0)
    glutInitWindowSize(300, 300)
    glutCreateWindow("mpcdi")
    init()
    
    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(key)
    #glutSpecialFunc(special)
    #glutVisibilityFunc(visible)

    glutMainLoop()
    
