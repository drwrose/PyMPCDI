from MpacsWarp2D import MpacsWarp2D
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
uniform sampler2D texture0, texture1, texture2, texture3;
uniform float alphaGamma, betaGamma, targetGamma, mediaGamma;
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

  // Get the alpha color at this pixel, and linearize it.
  vec4 alpha = texture2D(texture2, gl_TexCoord[0].xy);
  vec3 alphaLinear = vec3(pow(alpha.x, alphaGamma),
                          pow(alpha.y, alphaGamma),
                          pow(alpha.z, alphaGamma));

  // Get the beta color at this pixel, and linearize it.
  vec4 beta = texture2D(texture3, gl_TexCoord[0].xy);
  vec3 betaLinear = vec3(pow(beta.x, betaGamma),
                         pow(beta.y, betaGamma),
                         pow(beta.z, betaGamma));

  // Apply the alpha and beta colors.
  col.x = (col.x * alphaLinear.x * (1.0 - betaLinear.x)) + betaLinear.x;
  col.y = (col.y * alphaLinear.y * (1.0 - betaLinear.y)) + betaLinear.y;
  col.z = (col.z * alphaLinear.z * (1.0 - betaLinear.z)) + betaLinear.z;

  // And finally, re-apply the gamma curve.
  col.x = pow(col.x, 1.0 / targetGamma);
  col.y = pow(col.y, 1.0 / targetGamma);
  col.z = pow(col.z, 1.0 / targetGamma);

  gl_FragColor = col;
}
"""

fragmentShaderNoBlend = """
uniform sampler2D texture0, texture1, texture2;
uniform float alphaGamma, betaGamma, targetGamma, mediaGamma;
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

class MpacsWarp2DShader(MpacsWarp2D):
    """
    Implements 2D warping via a shader pipeline.

    This class creates a floating-point texture out of the data in
    a pfm file, and performs all of the warping and blending in the
    fragment shader via a two-step texture lookup.
    """

    def __init__(self, mpcdi, region):
        MpacsWarp2D.__init__(self, mpcdi, region)

        self.pfmtexobj = None

    def initGL(self):
        MpacsWarp2D.initGL(self)
        self.alpha.initGL()
        self.beta.initGL()

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
        self.texture3Loc = glGetUniformLocation(self.shader, 'texture3')
        self.alphaGammaLoc = glGetUniformLocation(self.shader, 'alphaGamma')
        self.betaGammaLoc = glGetUniformLocation(self.shader, 'betaGamma')
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
        glBindTexture(GL_TEXTURE_2D, self.alpha.texobj)
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, self.beta.texobj)

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

        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glVertexPointer(2, GL_FLOAT, 0, None)
        glTexCoordPointer(2, GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES, 0, 6)

        glUseProgram(0)

        glPopClientAttrib()

        self.saveOutputImage()
