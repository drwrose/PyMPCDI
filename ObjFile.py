import string
from OpenGL.GL import *
import numpy

class ObjFile:
    def __init__(self, filename = None, data = None):
        self.filename = None

        self.vertexData = None
        self.texcoordData = None
        self.triData = None


        if filename or data:
            self.read(filename = filename, data = data)

    def read(self, filename = None, data = None):
        """ Reads the obj file and stores the data internally.  If
        data is not None, it provides the pre-read obj file data as a
        Python string. """

        self.filename = filename
        if data is None:
            data = open(filename, 'rb').read()

        # A temporary list of the 'v' and 'vt' elements encountered in
        # the obj file.  These are held during the read() call only;
        # their values are rolled into self.vertices, self.texcoords
        # instead.
        self.obj_vertices = []
        self.obj_texcoords = []

        # A temporary table of the (vindex, tindex) pair that makes
        # each entry in self.vertices/self.texcoords.  This allows us
        # to uniquely identify each combination of vertex and texcoord
        # index referenced in the obj file (we must create a different
        # OpenGL vertex for each unique combination.)  This table is
        # also held during the read() call only.
        self.obj_combined_verts = {}

        # The permanent table of vertices, texcoords, and triangle
        # index numbers we build up during this call.  Unlike
        # self.obj_vertices and self.obj_texcoords, we maintain a 1:1
        # relationship between self.vertices and self.texcoords; each
        # OpenGL vertex has data from the same element index of both.
        self.vertices = []
        self.texcoords = []
        self.tris = []

        # Wal through each line of the obj file.
        for line in data.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('#'):
                continue

            cols = line.split()
            if cols[0] == 'v':
                point = [self.__make_float(str) for str in cols[1:4]]
                self.obj_vertices.append(point)
            elif cols[0] == 'vt':
                texcoord = [self.__make_float(str) for str in cols[1:3]]
                self.obj_texcoords.append(texcoord)
            # We ignore normals, don't need them
            elif cols[0] == 'f':
                verts = self.__make_verts(cols[1:])
                # Now create a sequence of triangles for the vertices
                # in this face definition.  For quads and higher-order
                # polygons, we don't attempt to do anything smarter
                # than simply fanning out from the first vertex.
                if len(verts) > 2:
                    tri = [verts[0], None, None]
                    for fi in range(1, len(verts) - 1):
                        tri[1] = verts[fi]
                        tri[2] = verts[fi + 1]
                    self.tris.append(tri)

        del self.obj_vertices
        del self.obj_texcoords
        del self.obj_combined_verts

    def __make_verts(self, vert_defs):
        """ Makes a series of OpenGL vertex references that share the
        appropriate combination of vertex and texcoord from the obj
        table. """

        verts = []
        for vert_def in vert_defs:
            vert_pieces = vert_def.split('/')
            vindex = None
            tindex = None
            if len(vert_pieces) >= 1 and vert_pieces[0].strip():
                vindex = self.__make_int(vert_pieces[0])
            if len(vert_pieces) >= 2 and vert_pieces[1].strip():
                tindex = self.__make_int(vert_pieces[1])

            if vindex is None:
                # Not sure what to make of this one, ignore it
                continue

            vdef = (vindex, tindex)
            try:
                vi = self.obj_combined_verts[vdef]
                # This vdef has appeared before, re-use it.
                verts.append(vi)
            except KeyError:
                # This vdef has not appeared before, slot a new vertex.
                vi = len(self.vertices)
                vertex = self.obj_vertices[vindex - 1]
                texcoord = [0, 0]
                if tindex is not None:
                    texcoord = self.obj_texcoords[tindex - 1]
                self.vertices.append(vertex)
                self.texcoords.append(texcoord)
                self.obj_combined_verts[vdef] = vi
                verts.append(vi)

        return verts

    def __make_float(self, str):
        try:
            val = float(str)
        except ValueError:
            val = 0.0
        return val

    def __make_int(self, str):
        try:
            val = int(str)
        except ValueError:
            val = 0
        return val

    def initGL(self):
        assert self.vertexData is None

        np_vertices = numpy.array(self.vertices, dtype = 'float32')
        self.vertexData = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexData)
        glBufferData(GL_ARRAY_BUFFER, np_vertices, GL_STATIC_DRAW)

        np_texcoords = numpy.array(self.texcoords, dtype = 'float32')
        self.texcoordData = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.texcoordData)
        glBufferData(GL_ARRAY_BUFFER, np_texcoords, GL_STATIC_DRAW)

        np_tris = numpy.array(self.tris, dtype = 'uint32')
        self.triData = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.triData)
        glBufferData(GL_ARRAY_BUFFER, np_tris, GL_STATIC_DRAW)
