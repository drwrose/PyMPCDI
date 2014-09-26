from MpcdiFile import MpcdiFile
import sys
from OpenGL.GL import *
from OpenGL.GLUT import *

from MpacsWarp2DShader import MpacsWarp2DShader
from MpacsWarp2DFixedFunction import MpacsWarp2DFixedFunction

mpcdi = MpcdiFile(sys.argv[1])
regionName = sys.argv[2]
region = mpcdi.regions[regionName]

warp = MpacsWarp2DShader(mpcdi, region)
#warp = MpacsWarp2DFixedFunction(mpcdi, region)

#warp.setMediaFilename('color_grid.png')
warp.setMediaFilename('1920x1080_HD_GRID_circles.png')

def init():
    warp.initGL()

def draw():
    glClear(GL_COLOR_BUFFER_BIT)

    warp.draw()

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
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE)

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
    
