from MpacsWarp3D import MpacsWarp3D
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy

vertexShader = """
void main() {
  gl_TexCoord[0] = gl_MultiTexCoord0;
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

fragmentShaderWithBlend = """
uniform sampler2D texture0, texture1, texture2;
uniform float blendGamma, targetGamma, mediaGamma;
uniform mat4 warpMat;

void main() {
  // Look up the warped UV coordinate in the pfm texture . . .
  vec4 uv = texture2D(texture0, gl_TexCoord[0].xy);

  // . . . apply the specified transform . . .
  uv = warpMat * uv;

  // . . . and use that UV coordinate to look up the media color.
  vec4 col = texture2D(texture1, uv.xy);

  // Linearize the media color.  We could also pre-linearize the media
  // by using an sRGB texture format.
  col.x = pow(col.x, mediaGamma);
  col.y = pow(col.y, mediaGamma);
  col.z = pow(col.z, mediaGamma);

  // Get the blend color at this pixel, and linearize it.
  vec4 blend = texture2D(texture2, gl_TexCoord[0].xy);
  float blendLinear = pow(blend.x, blendGamma);

  // Apply the blend color, and then re-apply the gamma curve.
  col.x = pow(col.x * blendLinear, 1.0 / targetGamma);
  col.y = pow(col.y * blendLinear, 1.0 / targetGamma);
  col.z = pow(col.z * blendLinear, 1.0 / targetGamma);

  gl_FragColor = col;
}
"""

fragmentShaderNoBlend = """
uniform sampler2D texture0, texture1, texture2;
uniform float blendGamma, targetGamma, mediaGamma;
uniform mat4 warpMat;

void main() {
  // Look up the warped UV coordinate in the pfm texture . . .
  vec4 uv = texture2D(texture0, gl_TexCoord[0].xy);

  // . . . apply the specified transform . . .
  uv = warpMat * uv;

  // . . . and use that UV coordinate to look up the media color.
  vec4 col = texture2D(texture1, uv.xy);

  // Linearize the media color.  We could also pre-linearize the media
  // by using an sRGB texture format.
  col.x = pow(col.x, mediaGamma);
  col.y = pow(col.y, mediaGamma);
  col.z = pow(col.z, mediaGamma);

  gl_FragColor = col;
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

        self.pfmtexobj = None

    def initGL(self):
        MpacsWarp3D.initGL(self)
        self.blend.initGL()

        # Load the pfm data as a floating-point texture.
        self.pfmtexobj = glGenTextures(1)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, self.pfmtexobj)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        # Fill every third element of the UV data with zeroes, instead
        # of the default NaN's which aren't really useful, and can
        # confuse OpenGL into ignoring the first two.
        uv_list = numpy.fromstring(self.pfm.data, dtype = 'float32')
        uvs3 = numpy.reshape(uv_list, (-1, 3), 'C')
        uvs3[:,2].fill(0)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.pfm.xSize, self.pfm.ySize, 0, GL_RGB, GL_FLOAT, uvs3)

        # Create a VBO with two triangles to make a unit quad.
        verts = [
            [0, 1], [1, 0], [1, 1],
            [0, 1], [1, 0], [0, 0],
            ]
        verts = numpy.array(verts, dtype = 'float32')
        self.vertdata = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)

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
        if self.includeBlend:
            fs = shaders.compileShader(fragmentShaderWithBlend, GL_FRAGMENT_SHADER)
        else:
            fs = shaders.compileShader(fragmentShaderNoBlend, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)

        self.texture0Loc = glGetUniformLocation(self.shader, 'texture0')
        self.texture1Loc = glGetUniformLocation(self.shader, 'texture1')
        self.texture2Loc = glGetUniformLocation(self.shader, 'texture2')
        self.blendGammaLoc = glGetUniformLocation(self.shader, 'blendGamma')
        self.targetGammaLoc = glGetUniformLocation(self.shader, 'targetGamma')
        self.mediaGammaLoc = glGetUniformLocation(self.shader, 'mediaGamma')
        self.warpMatLoc = glGetUniformLocation(self.shader, 'warpMat')

    def draw(self):
        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.pfmtexobj)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, self.media.texobj)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.blend.texobj)

        shaders.glUseProgram(self.shader)
        glUniform1i(self.texture0Loc, 0)
        glUniform1i(self.texture1Loc, 1)
        glUniform1i(self.texture2Loc, 2)
        glUniform1f(self.blendGammaLoc, self.blendGamma)
        glUniform1f(self.targetGammaLoc, self.targetGamma)
        glUniform1f(self.mediaGammaLoc, self.mediaGamma)
        glUniformMatrix4fv(self.warpMatLoc, 1, GL_FALSE, self.warpMat)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glVertexPointer(2, GL_FLOAT, 0, None)
        glTexCoordPointer(2, GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES, 0, 6)

        glUseProgram(0)

        glPopClientAttrib()

        self.saveOutputImage()
