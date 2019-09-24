from MpacsWarp2D import MpacsWarp2D
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy
import math

vertexShaderSL = """
void main() {
  gl_TexCoord[0] = gl_MultiTexCoord0;
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

fragmentShaderSL = """
uniform sampler2D texture0;

void main() {
  vec4 uv = gl_TexCoord[0];
  uv.y = 1.0 - uv.y;
  gl_FragColor = texture2D(texture0, uv.xy);
}
"""

class MpacsWarpSL(MpacsWarp2D):
    """
    Implements Shader-lamp warping via a shader pipeline.

    This class loads and renders an obj file from the point-of-view of
    the projector.  The obj file must be externally specified.
    """

    def __init__(self, mpcdi, region):
        MpacsWarp2D.__init__(self, mpcdi, region)

        # In the Shader Lamp profile, the "geometryWarpFile" is
        # actually the screen geometry mesh, not the 2-d warp.
        self.geom = self.warp

        # But the "distortionMap" is basically the same as the 2-d
        # warp in the 2d profile.
        self.warp = self.mpcdi.extractPfmFile(self.region.distortionMap.path)

    def initGL(self):
        MpacsWarp2D.initGL(self)
        self.model.initGL()

        # Compile the shaders.
        vs = shaders.compileShader(vertexShaderSL, GL_VERTEX_SHADER)
        fs = shaders.compileShader(fragmentShaderSL, GL_FRAGMENT_SHADER)
        self.shaderSL = shaders.compileProgram(vs, fs)

        self.texture0LocSL = glGetUniformLocation(self.shaderSL, 'texture0')

    def draw_3d(self):
        """ Draws the scene from the POV of the projector.  Applies no
        distortion maps or blends yet. """

        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.media.texobj)

        # Set up frustum and transform
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        near, far = 1.0, 10000.0
        left = math.tan(self.region.frustum.leftAngle * math.pi / 180.0) * near
        right = math.tan(self.region.frustum.rightAngle * math.pi / 180.0) * near
        down = math.tan(self.region.frustum.downAngle * math.pi / 180.0) * near
        up = math.tan(self.region.frustum.upAngle * math.pi / 180.0) * near
        glFrustum(left, right, down, up, near, far)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glRotate(self.region.frustum.roll,
                 self.region.frame.rollx, self.region.frame.rolly, self.region.frame.rollz)

        # TODO: this seems wrong, but it matches 7th Sense
        glRotate(-self.region.frustum.pitch,
                 self.region.frame.pitchx, self.region.frame.pitchy, self.region.frame.pitchz)

        glRotate(self.region.frustum.yaw, self.region.frame.yawx, self.region.frame.yawy, self.region.frame.yawz)


        # TODO: this also seems wrong, but it matches 7th Sense
        glTranslate(-self.region.frame.posx, -self.region.frame.posz, self.region.frame.posy)

        shaders.glUseProgram(self.shaderSL)
        glUniform1i(self.texture0LocSL, 0)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, self.model.vertexData)
        glVertexPointer(3, GL_FLOAT, 0, None)

        glBindBuffer(GL_ARRAY_BUFFER, self.model.texcoordData)
        glTexCoordPointer(2, GL_FLOAT, 0, None)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.model.triData)

        glDrawElements(GL_TRIANGLES, len(self.model.tris) * 3, GL_UNSIGNED_INT, None)

        glUseProgram(0)

        glPopClientAttrib()

    def draw(self):
        # First, render the 3-D scene.
        self.draw_3d()

        # Copy the resulting image to a new texture.  We could have
        # rendered it to a different FBO instead of doing this copy,
        # but the point of this code is not necessarily to make the
        # most efficient use of OpenGL, and this is a bit simpler.
        self.texobj = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texobj)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        width, height = self.windowSize
        glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, 0, 0, width, height, 0);

        # Now, clear the buffr and draw the resulting image again in
        # 2-D, this time warping it with the distortion map, and also
        # apply the projector-space blends.
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        self.draw_2d_and_blend(self.texobj, flipMedia = False)

        self.saveOutputImage()
