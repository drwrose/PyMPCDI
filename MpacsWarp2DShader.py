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

fragmentShader = """
uniform sampler2D texture0;
uniform sampler2D texture1;
uniform sampler2D texture2;
uniform float gamma;

void main() {
  // Look up the warped UV coordinate in the pfm texture . . .
  vec4 uv = texture2D(texture0, gl_TexCoord[0].xy);

  // . . . and use that UV coordinate to look up the media color.
  vec4 col = texture2D(texture1, uv.xy);

  // Linearize the media color.  This assumes the media has the same
  // gamma exponent as our display.  We could also use some other
  // exponent; or we could pre-linearize the media by using an sRGB
  // texture format.
  col.x = pow(col.x, gamma);
  col.y = pow(col.y, gamma);
  col.z = pow(col.z, gamma);

  // Get the blend color at this pixel, and linearize it.
  vec4 blend = texture2D(texture2, gl_TexCoord[0].xy);
  float blendLinear = pow(blend.x, gamma);

  // Apply the blend color, and then re-apply the gamma curve.
  col.x = pow(col.x * blendLinear, 1.0 / gamma);
  col.y = pow(col.y * blendLinear, 1.0 / gamma);
  col.z = pow(col.z * blendLinear, 1.0 / gamma);
  
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
        self.blend.initGL()

        # Load the pfm data as a floating-point texture.
        self.pfmtexobj = glGenTextures(1)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glBindTexture(GL_TEXTURE_2D, self.pfmtexobj)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB32F, self.pfm.xSize, self.pfm.ySize, 0, GL_RGB, GL_FLOAT, self.pfm.data)

        # Create a VBO with two triangles to make a unit quad.
        verts = [
            [0, 1], [1, 0], [1, 1], 
            [0, 1], [1, 0], [0, 0],
            ]
        verts = numpy.array(verts, dtype = 'float32')
        self.vertdata = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glBufferData(GL_ARRAY_BUFFER, verts, GL_STATIC_DRAW)

        # Compile the shaders.
        vs = shaders.compileShader(vertexShader, GL_VERTEX_SHADER)
        fs = shaders.compileShader(fragmentShader, GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vs, fs)

        self.texture0Loc = glGetUniformLocation(self.shader, 'texture0')
        self.texture1Loc = glGetUniformLocation(self.shader, 'texture1')
        self.texture2Loc = glGetUniformLocation(self.shader, 'texture2')
        self.gammaLoc = glGetUniformLocation(self.shader, 'gamma')

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
        glUniform1f(self.gammaLoc, self.gamma)

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)

        glBindBuffer(GL_ARRAY_BUFFER, self.vertdata)
        glVertexPointer(2, GL_FLOAT, 0, None)
        glTexCoordPointer(2, GL_FLOAT, 0, None)
        
        glDrawArrays(GL_TRIANGLES, 0, 6)

        glUseProgram(0)
        glPopClientAttrib(GL_CLIENT_ALL_ATTRIB_BITS)
