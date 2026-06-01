"""GLSL shader skeleton templates and ISF→GLSL type mapping."""

# ISF Type to GLSL uniform type mapping (from JavaScript reference)
TYPE_UNIFORM_MAP = {
    "float": "float",
    "image": "sampler2D",
    "bool": "bool",
    "event": "bool",
    "long": "int",
    "color": "vec4",
    "point2D": "vec2",
}

# ISF Fragment Shader Skeleton (modernized for GLSL 330+)
ISF_FRAGMENT_SHADER_SKELETON = """
precision highp float;
precision highp int;

uniform int PASSINDEX;
uniform vec2 RENDERSIZE;
in vec2 isf_FragNormCoord;
in vec2 isf_FragCoord;
uniform float TIME;
uniform float TIMEDELTA;
uniform int FRAMEINDEX;
uniform vec4 DATE;

[[uniforms]]

// ISF sampling functions (from JavaScript reference)
vec4 VVSAMPLER_2DBYPIXEL(sampler2D sampler, vec4 samplerImgRect, vec2 samplerImgSize, bool samplerFlip, vec2 loc) {
  return (samplerFlip)
    ? texture(sampler,vec2(((loc.x/samplerImgSize.x*samplerImgRect.z)+samplerImgRect.x), (samplerImgRect.w-(loc.y/samplerImgSize.y*samplerImgRect.w)+samplerImgRect.y)))
    : texture(sampler,vec2(((loc.x/samplerImgSize.x*samplerImgRect.z)+samplerImgRect.x), ((loc.y/samplerImgSize.y*samplerImgRect.w)+samplerImgRect.y)));
}
vec4 VVSAMPLER_2DBYNORM(sampler2D sampler, vec4 samplerImgRect, vec2 samplerImgSize, bool samplerFlip, vec2 normLoc)  {
  vec4 returnMe = VVSAMPLER_2DBYPIXEL(sampler,samplerImgRect,samplerImgSize,samplerFlip,vec2(normLoc.x*samplerImgSize.x, normLoc.y*samplerImgSize.y));
  return returnMe;
}

out vec4 fragColor;
#define gl_FragColor fragColor

[[main]]
"""

# ISF Vertex Shader Skeleton (modernized for GLSL 330+)
ISF_VERTEX_SHADER_SKELETON = """
precision highp float;
precision highp int;
void isf_vertShaderInit();

in vec2 isf_position; // -1..1

uniform int     PASSINDEX;
uniform vec2    RENDERSIZE;
out vec2    isf_FragNormCoord; // 0..1
vec2    isf_fragCoord; // Pixel Space

[[uniforms]]

[[main]]
void isf_vertShaderInit(void)  {
    gl_Position = vec4( isf_position, 0.0, 1.0 );
    isf_FragNormCoord = vec2((gl_Position.x+1.0)/2.0, 1.0 - (gl_Position.y+1.0)/2.0);
    isf_fragCoord = floor(isf_FragNormCoord * RENDERSIZE);
    [[functions]]
}
"""

# Default vertex shader (from JavaScript reference)
ISF_VERTEX_SHADER_DEFAULT = """
void main() {
  isf_vertShaderInit();
}
"""
