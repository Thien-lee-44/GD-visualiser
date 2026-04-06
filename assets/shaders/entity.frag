#version 330 core
in vec2 TexCoords;
out vec4 FragColor;

uniform vec3 objectColor;
uniform float alpha;
uniform int useTexture;
uniform sampler2D uTexture;

void main() {
    if (useTexture == 1) {
        vec4 texColor = texture(uTexture, TexCoords);
        vec3 tintedColor = texColor.rgb * objectColor * 1.2;
        FragColor = vec4(clamp(tintedColor, 0.0, 1.0), alpha);
    } else {
        FragColor = vec4(objectColor, alpha);
    }
}