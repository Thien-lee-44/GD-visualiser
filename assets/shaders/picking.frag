#version 330 core
in vec3 vPickingColor;
out vec4 FragColor;

uniform int useUniformPickingColor;
uniform vec3 uPickingColor;

void main() {
    if (useUniformPickingColor == 1) FragColor = vec4(uPickingColor, 1.0);
    else FragColor = vec4(vPickingColor, 1.0);
}