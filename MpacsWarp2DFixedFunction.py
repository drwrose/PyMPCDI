from MpacsWarp2D import MpacsWarp2D
from BlendQuad import BlendQuad
from OpenGL.GL import *
import numpy

class MpacsWarp2DFixedFunction(MpacsWarp2D):
    """
    Implements 2D warping via the OpenGL fixed-function pipeline.

    This class creates a 2-d mesh out of the data in a pfm file,
    and renders the input media on this mesh to compute the warping.
    Each point in the pfm file becomes a vertex in the mesh.
    """

    def __init__(self, mpcdi, region):
        MpacsWarp2D.__init__(self, mpcdi, region)

        self.blendCard = BlendQuad(self.alpha)

        # We don't attempt to do beta-map processing in the
        # fixed-function renderer, only alpha-map processing.

    def initGL(self):
        MpacsWarp2D.initGL(self)
        self.blendCard.initGL()

        xSize = self.warp.xSize
        ySize = self.warp.ySize

        # Discard every third element of the UV data, which is mostly
        # NaN's and isn't really useful, and can confuse OpenGL into
        # ignoring the first two.
        uv_list = numpy.fromstring(self.warp.data, dtype = 'float32')
        uvs3 = numpy.reshape(uv_list, (-1, 3), 'C')
        uvs = uvs3[:,0:2]

        self.uvdata = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.uvdata)
        glBufferData(GL_ARRAY_BUFFER, uvs, GL_STATIC_DRAW)

        verts = []
        xScale = 1.0 / float(xSize)
        yScale = 1.0 / float(ySize)
        for yi in range(ySize):
            for xi in range(xSize):
                verts.append((float(xi) + 0.5) * xScale)
                verts.append((float(yi) + 0.5) * yScale)

        self.numVertices = len(verts) / 2
        verts = numpy.array(verts, dtype = 'float32')

        self.vertdata = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)

        ## def has_point(xi, yi):
        ##     if xi < xSize and y < ySize and

        tris = []
        for yi in range(ySize - 1):
            for xi in range(xSize - 1):
                vi0 = ((xi) + (yi) * xSize);
                vi1 = ((xi) + (yi + 1) * xSize);
                vi2 = ((xi + 1) + (yi + 1) * xSize);
                vi3 = ((xi + 1) + (yi) * xSize);

                tris += [vi2, vi0, vi1]
                tris += [vi3, vi0, vi2]

        self.numIndices = len(tris)
        tris = numpy.array(tris, dtype = 'int32')
        self.idata = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.idata)
        glBufferData(GL_ARRAY_BUFFER, tris, GL_STATIC_DRAW)

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)

        # First, draw the mesh with the media texture applied.

        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadIdentity()

        # Flip the V axis to match OpenGL's texturing convention.  (Or
        # we could have loaded the media file in upside-down.)
        glTranslatef(0.0, 1.0, 0.0)
        glScalef(1.0, -1.0, 1.0)

        # Scale the warping UV's into the correct range specified by
        # the Region (as defined in the mpcdi.xml file).
        glTranslatef(self.region.x, self.region.y, 0.0)
        glScale(self.region.xsize, self.region.ysize, 1.0)

        self.media.apply()

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glVertexPointer(2, GL_FLOAT, 0, None)

        glBindBuffer(GL_ARRAY_BUFFER, self.uvdata)
        glTexCoordPointer(2, GL_FLOAT, 0, None)

        glColor3f(1.0, 1.0, 1.0)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.idata)
        glDrawElements(GL_TRIANGLES, self.numIndices, GL_UNSIGNED_INT, None)

        glMatrixMode(GL_TEXTURE)
        glPopMatrix()

        glPopClientAttrib()
        glPopAttrib()

        # Now apply the blending map.

        # We ought to apply the blending map in linear space, then
        # re-apply the gamma curve; but this isn't really possible in
        # the fixed-function pipeline.  So we just naively apply the
        # blending map to the warp by multiplying it as-is over the
        # whole frame (assuming that it's been pre-scaled with the
        # target gamma).  This actually isn't a terrible approach, and
        # looks fine as long as the media is sufficiently bright.
        self.blendCard.draw()

        self.saveOutputImage()
