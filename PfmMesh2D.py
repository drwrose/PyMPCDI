from OpenGL.GL import *
import numpy

class PfmMesh2D:
    """ This class creates a 2-d mesh out of the data in a pfm file.
    Each non-NaN point in the pfm file becomes a vertex in the
    mesh. """

    def __init__(self, pfm, tex, offset, scale):
        self.pfm = pfm
        self.tex = tex
        self.offset = offset
        self.scale = scale

    def initGL(self):
        xSize = self.pfm.xSize
        ySize = self.pfm.ySize

        uvs = numpy.fromstring(self.pfm.data, dtype = 'float32')
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

        glMatrixMode(GL_TEXTURE)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(self.offset[0], self.offset[1], 0.0)
        glScale(self.scale[0], self.scale[1], 0.0)
        print self.offset
        glTranslatef(0.0, 1.0, 0.0)
        glScalef(1.0, -1.0, 1.0)

        self.tex.apply()
        
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glVertexPointer(2, GL_FLOAT, 0, None)

        glBindBuffer(GL_ARRAY_BUFFER, self.uvdata)
        glTexCoordPointer(3, GL_FLOAT, 0, None)

        glColor3f(1.0, 1.0, 1.0)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.idata)
        glDrawElements(GL_TRIANGLES, self.numIndices, GL_UNSIGNED_INT, None)

        glMatrixMode(GL_TEXTURE)
        glPopMatrix()
        
        glPopClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)
        glPopAttrib(GL_ENABLE_BIT)
