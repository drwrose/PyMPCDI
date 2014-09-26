from MpcdiFile import MpcdiFile
import sys
import getopt
from OpenGL.GL import *
from OpenGL.GLUT import *

from MpacsWarp2DShader import MpacsWarp2DShader
from MpacsWarp2DFixedFunction import MpacsWarp2DFixedFunction

help = """

This program provides a bare-bones OpenGL implementation of the 2-D
MPCDI warping specification, using PyOpenGL.  See:

http://www.vesa.org/news/vesa-completes-specifications-for-new-multiple-projector-common-data-interchange-standard-mpcdi/

The input is an mpcdi file using the '2d' profile, and the name of one
region defined within the file.  This program will open a window to
display the contents of the indicated media image (a single frame) as
warped according to the mpcdi file.

This program is intended primarily to serve as a reference
implementation, and not so much to provide a useful function in
itself, though it can be useful to sanity-check mpcdi files.

Options:

    -m mpcdiFilename
        Specify the mpcdi file.  This is required.

    -i mediaFilename
        Specify the media file to load and warp.  The default is a plain grid.

    -r regionName
        Specify the name of a region to display.  If this is omitted,
        the first region encountered in the file is used.

    -s width,height
        Specify the size of the window.

    -g gamma
        Specify the gamma response curve of the target display device.

    -f
        Use the fixed-function implementation instead of the
        shader-based implementation.
        
"""


def usage(code, msg = ''):
    print >> sys.stderr, help
    print >> sys.stderr, msg
    sys.exit(code)

def draw():
    glClear(GL_COLOR_BUFFER_BIT)

    warp.draw()

    glutSwapBuffers()

def key(k, x, y):
    # If any key is pressed, close the window and exit.
    sys.exit(0)

def reshape(width, height):
    h = float(height) / float(width);
    glViewport(0, 0, width, height)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, 1, 1, 0, -100, 100)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def run():
    global regionName, windowSize, warp
    
    mpcdi = MpcdiFile(mpcdiFilename)
    if not regionName:
        regionName = mpcdi.regionIdList[0]

    region = mpcdi.regions[regionName]

    if useFixedFunction:
        warp = MpacsWarp2DFixedFunction(mpcdi, region)
    else:
        warp = MpacsWarp2DShader(mpcdi, region)

    if targetGamma is not None:
        warp.targetGamma = targetGamma
        
    if not windowSize:
        windowSize = region.XResolution, region.YResolution

    warp.setMediaFilename(mediaFilename)

    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGB | GLUT_DOUBLE)

    glutInitWindowSize(*windowSize)
    glutCreateWindow(regionName)
    warp.initGL()
    
    glutDisplayFunc(draw)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(key)

    glutMainLoop()

# Global warping object.
warp = None

# Command-line parameters.
mpcdiFilename = None
mediaFilename = None
regionName = None
mediaFilename = 'color_grid.png'
targetGamma = None
useFixedFunction = False
windowSize = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'm:i:r:s:g:fh')
except getopt.error, msg:
    usage(1, msg)

for opt, arg in opts:
    if opt == '-m':
        mpcdiFilename = arg
    elif opt == '-i':
        mediaFilename = arg
    elif opt == '-r':
        regionName = arg
    elif opt == '-s':
        windowSize = map(int, arg.split(','))
    elif opt == '-g':
        targetGamma = float(arg)
    elif opt == '-f':
        useFixedFunction = True
    elif opt == '-h':
        usage(0)
    
if not mpcdiFilename:
    print >> sys.stderr, "No mpcdi filename specified.  Use -h for help."
    sys.exit(1)

run()
