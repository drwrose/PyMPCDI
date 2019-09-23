from MpcdiFile import MpcdiFile
import sys
import getopt
import copy
from OpenGL.GL import *
from OpenGL.GLUT import *
import TextureImage

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

    -r regionName
        Specify the name of a region to display.  If this is omitted,
        the first region encountered in the file is used.  This option
        may be repeated to display multiple regions; if it is
        repeated, then any other options that precede the first -r
        apply to all regions, and options that follow each -r apply
        only to that particular region.

    -i mediaFilename
        Specify the media file to load and warp.  The default is a plain grid.

    -o outputFilename
        Specify an optional image filename to save the warped output
        to.  The default is not to save it, only to display it.

    -s width,height
        Specify the size of the window.

    -g gamma
        Specify the gamma response curve of the target display device.

    -b
        Omit the blend maps from the rendered result.

    -M
        Enable mipmapping.  Without this option simple bilinear
        filtering is used instead.

    -f
        Use the fixed-function implementation instead of the
        shader-based implementation.

"""


def usage(code, msg = ''):
    print >> sys.stderr, help
    print >> sys.stderr, msg
    sys.exit(code)

class Window:
    def __init__(self):
        # Command-line parameters.
        self.mpcdiFilename = None
        self.mediaFilename = None
        self.outputFilename = None
        self.useFbo = False
        self.regionName = None
        self.mediaFilename = 'color_grid.png'
        self.targetGamma = None
        self.useFixedFunction = False
        self.windowSize = None
        self.includeBlend = None

        # MPCDI file.
        self.mpcdi = None

        # Warping object.
        self.warp = None

    def draw_bg(self):
        glClear(GL_COLOR_BUFFER_BIT)
        self.warp.draw()

    def draw(self):
        self.draw_bg()
        glutSwapBuffers()

    def key(self, k, x, y):
        # If any key is pressed, close the window and exit.
        sys.exit(0)

    def reshape(self, width, height):
        if self.useFbo:
            # In this case we insist on keeping the actual buffer
            # size, because we're rendering to a buffer that's not
            # necessarily attached to the window anyway.
            width, height = self.windowSize

        print "%s rendering at size %s, %s" % (self.regionName, width, height)
        self.warp.setWindowSize((width, height))

        h = float(height) / float(width);
        glViewport(0, 0, width, height)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 1, 0, -100, 100)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def setupFbo(self):
        # All we need is a color buffer.
        self.rbobj = glGenRenderbuffers(1)
        glBindRenderbuffer(GL_RENDERBUFFER, self.rbobj)
        glRenderbufferStorage(GL_RENDERBUFFER, GL_RGBA8,
                              self.windowSize[0], self.windowSize[1])

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        self.fbobj = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.fbobj)

        glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0,
                                  GL_RENDERBUFFER, self.rbobj)

        status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
        assert(status == GL_FRAMEBUFFER_COMPLETE)

    def setupDisplay(self):

        if not self.regionName:
            self.regionName = self.mpcdi.regionIdList[0]

        self.region = self.mpcdi.regions[self.regionName]

        if self.useFixedFunction:
            self.warp = MpacsWarp2DFixedFunction(self.mpcdi, self.region)
        else:
            self.warp = MpacsWarp2DShader(self.mpcdi, self.region)

        if self.targetGamma is not None:
            self.warp.targetGamma = self.targetGamma

        if self.includeBlend is not None:
            self.warp.includeBlend = self.includeBlend

        if not self.windowSize:
            self.windowSize = self.region.Xresolution, self.region.Yresolution

        self.warp.setWindowSize(self.windowSize)
        self.warp.setMediaFilename(self.mediaFilename)
        if self.outputFilename:
            self.warp.setOutputFilename(self.outputFilename)
            self.useFbo = True

        displayMode = GLUT_RGB | GLUT_DOUBLE
        glutInitDisplayMode(displayMode)

        if not self.outputFilename:
            glutInitWindowSize(*self.windowSize)
        if self.useFbo:
            glutInitWindowPosition(12000, 12000)  # probably this is offscreen.
        else:
            glutInitWindowPosition(-1, -1)

        self.windowId = glutCreateWindow(self.regionName)

        if self.useFbo:
            # If we're using an FBO to render, we don't need an
            # onscreen window.
            self.setupFbo()

        self.warp.initGL()

        glutDisplayFunc(self.draw)
        glutReshapeFunc(self.reshape)
        glutKeyboardFunc(self.key)

defaultWindowParams = Window()
currentWindow = defaultWindowParams
windows = []

try:
    opts, args = getopt.getopt(sys.argv[1:], 'm:i:o:r:s:g:bfMh')
except getopt.error, msg:
    usage(1, msg)

# A global table of MPCDI files read from disk.
mpcdis = {}

def readMpcdi(mpcdiFilename):
    mpcdi = mpcdis.setdefault(mpcdiFilename, None)
    if mpcdi is None:
        mpcdi = MpcdiFile(mpcdiFilename)
        mpcdis[mpcdiFilename] = mpcdi
    return mpcdi

for opt, arg in opts:
    if opt == '-m':
        currentWindow.mpcdiFilename = arg
        currentWindow.mpcdi = readMpcdi(arg)
    elif opt == '-i':
        currentWindow.mediaFilename = arg
    elif opt == '-o':
        currentWindow.outputFilename = arg
    elif opt == '-r':
        # Each occurrence of -r defines a new region.  The parameters
        # following -r apply to the region we just named.
        currentWindow = copy.copy(defaultWindowParams)
        windows.append(currentWindow)
        currentWindow.regionName = arg
    elif opt == '-s':
        currentWindow.windowSize = map(int, arg.split(','))
    elif opt == '-g':
        currentWindow.targetGamma = float(arg)
    elif opt == '-b':
        currentWindow.includeBlend = False
    elif opt == '-f':
        currentWindow.useFixedFunction = True
    elif opt == '-M':
        TextureImage.useMipmapping = True
    elif opt == '-h':
        usage(0)

if currentWindow is defaultWindowParams:
    # No regionName has been specified, so no explicit Window object
    # was created; use the default.
    windows.append(currentWindow)

for window in windows:
    if not window.mpcdiFilename:
        print >> sys.stderr, "No mpcdi filename specified.  Use -h for help."
        sys.exit(1)

glutInit(sys.argv)
allOutputFilename = True
for window in windows:
    window.setupDisplay()
    if not window.outputFilename:
        allOutputFilename = False

quitCount = 0
def quitFunc():
    global quitCount
    quitCount += 1
    if quitCount < 50:
        return

    print "Exiting"
    sys.exit(0)

if allOutputFilename:
    # If everything is going to disk, quit after a few frames.  (If we
    # quit after one frame, it sometimes locks up; some weird glut
    # interaction I suppose.)
    glutIdleFunc(quitFunc)

glutMainLoop()
