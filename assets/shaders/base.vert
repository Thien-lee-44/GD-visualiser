#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal; 
layout (location = 2) in vec2 aTexCoords; 

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform float flattenY; 

out vec3 FragPos;
out float height;
out float raw01;
out vec3 vPickingColor; 
out vec2 TexCoords;

void main() {
    height = aPos.y; 
    raw01 = clamp(aNormal.z, 0.0, 1.0);
    TexCoords = aTexCoords;
    
    vec3 modifiedPos = aPos;
    modifiedPos.y *= flattenY; 
    
    vec4 worldPos = model * vec4(modifiedPos, 1.0);
    FragPos = worldPos.xyz;
    gl_Position = projection * view * worldPos;

    vPickingColor = aNormal; 
}
