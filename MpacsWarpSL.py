from MpacsWarp3D import MpacsWarp3D
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy
import math

vertexShader = """
void main() {
  gl_TexCoord[0] = gl_MultiTexCoord0;
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

fragmentShader = """
uniform sampler2D texture0, texture1, texture2;
uniform float blendGamma, targetGamma, mediaGamma;
uniform mat4 warpMat;

void main() {
  vec4 uv = gl_TexCoord[0];
  uv.y = 1.0 - uv.y;
  gl_FragColor = texture2D(texture1, uv.xy);
}
"""

class MpacsWarpSL(MpacsWarp3D):
    """
    Implements Shader-lamp warping via a shader pipeline.

    This class loads and renders an obj file from the point-of-view of
    the projector.  The obj file must be externally specified.
    """

    def __init__(self, mpcdi, region):
        MpacsWarp3D.__init__(self, mpcdi, region)

        self.distort = self.mpcdi.extractPfmFile(self.region.distortionMap.path)

    def initGL(self):
        MpacsWarp3D.initGL(self)
        self.model.initGL()
        self.alpha.initGL()
        self.beta.initGL()
        self.distort.initGL()

        # A matrix to scale the warping UV's into the correct range
        # specified by the Region (as defined in the mpcdi.xml file).
        rangeMat = numpy.array(
            [[self.region.xsize, 0, 0, 0],
             [0, self.region.ysize, 0, 0],
             [0, 0, 1, 0],
             [self.region.x, self.region.y, 0, 1]])

        # We also need to flip the V axis to match OpenGL's texturing
        # convention.  (Or we could have loaded the media file in
        # upside-down.)
        flipMat = numpy.array(
            [[1, 0, 0, 0],
             [0, -1, 0, 0],
             [0, 0, 1, 0],
             [0, 1, 0, 1]])

        # Accumulate them both into the single warping matrix.
        self.warpMat = rangeMat.dot(flipMat)

        # Compile the shaders.
        vs = shaders.compileShader(vertexShader, GL_VERTEX_SHADER)
        fs = shaders.compileShader(fragmentShader, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)

        self.texture0Loc = glGetUniformLocation(self.shader, 'texture0')
        self.texture1Loc = glGetUniformLocation(self.shader, 'texture1')
        self.texture2Loc = glGetUniformLocation(self.shader, 'texture2')
        self.texture3Loc = glGetUniformLocation(self.shader, 'texture3')
        self.alphaGammaLoc = glGetUniformLocation(self.shader, 'alphaGamma')
        self.betaGammaLoc = glGetUniformLocation(self.shader, 'betaGamma')
        self.targetGammaLoc = glGetUniformLocation(self.shader, 'targetGamma')
        self.mediaGammaLoc = glGetUniformLocation(self.shader, 'mediaGamma')
        self.warpMatLoc = glGetUniformLocation(self.shader, 'warpMat')

    def draw(self):
        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.distort.texobj)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.media.texobj)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.alpha.texobj)
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, self.beta.texobj)

        # Hack, set up frustum and transform
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

        shaders.glUseProgram(self.shader)
        glUniform1i(self.texture0Loc, 0)
        glUniform1i(self.texture1Loc, 1)
        glUniform1i(self.texture2Loc, 2)
        glUniform1i(self.texture3Loc, 3)
        glUniform1f(self.alphaGammaLoc, self.alphaGamma)
        glUniform1f(self.betaGammaLoc, self.betaGamma)
        glUniform1f(self.targetGammaLoc, self.targetGamma)
        glUniform1f(self.mediaGammaLoc, self.mediaGamma)
        glUniformMatrix4fv(self.warpMatLoc, 1, GL_FALSE, self.warpMat)

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

        self.saveOutputImage()
