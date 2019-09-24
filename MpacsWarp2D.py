from MpacsWarp import MpacsWarp
from OpenGL.GL import *
from OpenGL.GL import shaders
import numpy

vertexShader2D = """
void main() {
  gl_TexCoord[0] = gl_MultiTexCoord0;
  gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
}
"""

fragmentShader2D = """
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

class MpacsWarp2D(MpacsWarp):
    """
    Implements basic 2D warping, for instance for the "2d" profile,
    but also to apply distortion maps in the Shader Lamps case.

    This class loads the warping texture as a floating-point texture,
    and performs all of the warping and blending in the fragment
    shader via a two-step texture lookup.  """

    def __init__(self, mpcdi, region):
        MpacsWarp.__init__(self, mpcdi, region)

        self.warp = self.mpcdi.extractPfmFile(self.region.geometryWarpFile.path)

    def initGL(self):
        MpacsWarp.initGL(self)
        self.alpha.initGL()
        self.beta.initGL()
        self.warp.initGL()

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
        self.rangeMat = numpy.array(
            [[self.region.xsize, 0, 0, 0],
             [0, self.region.ysize, 0, 0],
             [0, 0, 1, 0],
             [self.region.x, self.region.y, 0, 1]])

        # We also need to flip the V axis to match OpenGL's texturing
        # convention.  (Or we could have loaded the media file in
        # upside-down.)
        self.flipMat = numpy.array(
            [[1, 0, 0, 0],
             [0, -1, 0, 0],
             [0, 0, 1, 0],
             [0, 1, 0, 1]])

        # Compile the shaders.
        vs = shaders.compileShader(vertexShader2D, GL_VERTEX_SHADER)
        fs = shaders.compileShader(fragmentShader2D, GL_FRAGMENT_SHADER)
        self.shader2D = shaders.compileProgram(vs, fs)

        self.texture0Loc2D = glGetUniformLocation(self.shader2D, 'texture0')
        self.texture1Loc2D = glGetUniformLocation(self.shader2D, 'texture1')
        self.texture2Loc2D = glGetUniformLocation(self.shader2D, 'texture2')
        self.texture3Loc2D = glGetUniformLocation(self.shader2D, 'texture3')
        self.alphaGammaLoc2D = glGetUniformLocation(self.shader2D, 'alphaGamma')
        self.betaGammaLoc2D = glGetUniformLocation(self.shader2D, 'betaGamma')
        self.targetGammaLoc2D = glGetUniformLocation(self.shader2D, 'targetGamma')
        self.mediaGammaLoc2D = glGetUniformLocation(self.shader2D, 'mediaGamma')
        self.warpMatLoc2D = glGetUniformLocation(self.shader2D, 'warpMat')

    def draw_2d_and_blend(self, mediaTexobj, flipMedia = True):
        """ Draws the indicated media texture as warped by the warp
        map, and applies the alpha and beta maps. """

        glPushClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, 1, 1, 0, -100, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.warp.texobj)
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, mediaTexobj)
        glActiveTexture(GL_TEXTURE2)
        glBindTexture(GL_TEXTURE_2D, self.alpha.texobj)
        glActiveTexture(GL_TEXTURE3)
        glBindTexture(GL_TEXTURE_2D, self.beta.texobj)

        shaders.glUseProgram(self.shader2D)
        glUniform1i(self.texture0Loc2D, 0)
        glUniform1i(self.texture1Loc2D, 1)
        glUniform1i(self.texture2Loc2D, 2)
        glUniform1i(self.texture3Loc2D, 3)
        glUniform1f(self.alphaGammaLoc2D, self.alphaGamma)
        glUniform1f(self.betaGammaLoc2D, self.betaGamma)
        glUniform1f(self.targetGammaLoc2D, self.targetGamma)
        glUniform1f(self.mediaGammaLoc2D, self.mediaGamma)

        if flipMedia:
            # If we're flipping the media (because it was loaded
            # externally in the inverse of OpenGL's convention), then
            # combine the rangeMat and the flipMat into a single
            # transform matrix that does this.
            warpMat = self.rangeMat.dot(self.flipMat)
            glUniformMatrix4fv(self.warpMatLoc2D, 1, GL_FALSE, warpMat)
        else:
            # If we're not flipping the media (because it was
            # generated internally matching OpenGL's convention), then
            # only apply the rangeMat.
            glUniformMatrix4fv(self.warpMatLoc2D, 1, GL_FALSE, self.rangeMat)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glVertexPointer(2, GL_FLOAT, 0, None)
        glTexCoordPointer(2, GL_FLOAT, 0, None)

        glDrawArrays(GL_TRIANGLES, 0, 6)

        glUseProgram(0)

        glPopClientAttrib()


    def draw(self):
        self.draw_2d_and_blend(self.media.texobj, flipMedia = True)
        self.saveOutputImage()
