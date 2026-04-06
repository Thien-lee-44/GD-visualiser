#version 330 core
in float height;
out vec4 FragColor;
uniform float alpha;

void main() {
    float t = clamp(height, 0.0, 1.0); 
    t = log(1.0 + t * 50.0) / log(51.0); 
    
    vec3 color;
    if (t < 0.25) color = mix(vec3(0.0, 0.0, 0.5), vec3(0.0, 0.0, 1.0), t / 0.25);
    else if (t < 0.5) color = mix(vec3(0.0, 0.0, 1.0), vec3(0.0, 1.0, 1.0), (t - 0.25) / 0.25);
    else if (t < 0.75) color = mix(vec3(0.0, 1.0, 1.0), vec3(1.0, 1.0, 0.0), (t - 0.5) / 0.25);
    else color = mix(vec3(1.0, 1.0, 0.0), vec3(1.0, 0.0, 0.0), (t - 0.75) / 0.25);
    
    FragColor = vec4(color, alpha);
}