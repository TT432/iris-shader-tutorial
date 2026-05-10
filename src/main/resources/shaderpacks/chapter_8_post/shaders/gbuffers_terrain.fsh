#version 330 compatibility

/* RENDERTARGETS: 0 */

uniform sampler2D texture;

in vec2 texcoord;
in vec2 lmcoord;
in vec4 glcolor;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 albedo = texture(texture, texcoord) * glcolor;
    float light = lmcoord.y * 0.8 + 0.2;
    vec3 color = albedo.rgb * light;
    outColor = vec4(color, 0.0);
}
