#version 330 core
in float height;
in float raw01;
out vec4 FragColor;

uniform int is_contour;
uniform int is_grid;
uniform vec3 objectColor;
uniform float alpha;
uniform float line_brightness;
uniform float flattenY;

uniform int use_log;
uniform float raw_min;
uniform float raw_max;
uniform float processed_min;
uniform float auto_height_scale;

void main() {
    if (is_grid == 1) {
        FragColor = vec4(objectColor, 1.0);
        return;
    }

    float t = clamp(raw01, 0.0, 1.0);

    if (is_contour == 1) {
        float y_proc = processed_min;
        if (auto_height_scale > 0.0001) {
            y_proc = (height / auto_height_scale) + processed_min;
        }
        float raw_y = (use_log == 1) ? (exp(y_proc) - 1.0 + raw_min) : y_proc;
        t = clamp((raw_y - raw_min) / (raw_max - raw_min + 0.0001), 0.0, 1.0);
    }

    vec3 low_c = vec3(0.1, 0.3, 0.8);
    vec3 mid_c = vec3(0.2, 0.8, 0.2);
    vec3 high_c = vec3(0.9, 0.2, 0.2);
    
    vec3 surfaceColor = (t < 0.5) ? mix(low_c, mid_c, t * 2.0) : mix(mid_c, high_c, (t - 0.5) * 2.0);
    
    if (!gl_FrontFacing && flattenY > 0.5 && is_contour == 0) surfaceColor *= 0.65; 

    if (is_contour == 1) FragColor = vec4(clamp(surfaceColor * line_brightness, 0.0, 1.0), 1.0);
    else FragColor = vec4(surfaceColor, alpha);
}
