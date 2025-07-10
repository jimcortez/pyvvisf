/*{
    "DESCRIPTION": "Animated shapes: moving circle, rotating rectangle, pulsating ring.",
    "CREDIT": "pyvvisf example",
    "ISFVSN": "2.0",
    "CATEGORIES": ["Generator"],
    "INPUTS": [
        {"NAME": "circleColor", "TYPE": "color", "DEFAULT": [0.2, 0.8, 1.0, 1.0]},
        {"NAME": "rectColor", "TYPE": "color", "DEFAULT": [1.0, 0.5, 0.2, 1.0]},
        {"NAME": "ringColor", "TYPE": "color", "DEFAULT": [1.0, 1.0, 0.2, 1.0]}
    ]
}*/

float circle(vec2 uv, vec2 center, float radius) {
    return smoothstep(radius, radius - 0.01, length(uv - center));
}

float rectangle(vec2 uv, vec2 center, vec2 size, float angle) {
    vec2 p = uv - center;
    float s = sin(angle);
    float c = cos(angle);
    p = mat2(c, -s, s, c) * p;
    vec2 d = abs(p) - size * 0.5;
    float outside = length(max(d, 0.0));
    float inside = min(max(d.x, d.y), 0.0);
    return smoothstep(0.01, 0.0, outside + inside);
}

float ring(vec2 uv, vec2 center, float radius, float thickness) {
    float dist = length(uv - center);
    return smoothstep(thickness, 0.0, abs(dist - radius));
}

void main() {
    vec2 uv = isf_FragNormCoord;
    float aspect = RENDERSIZE.x / RENDERSIZE.y;
    uv.x *= aspect;
    // Animated circle
    vec2 circleCenter = vec2(0.5 + 0.3 * sin(TIME), 0.5 + 0.3 * cos(TIME * 0.7));
    float c = circle(uv, circleCenter, 0.18 + 0.05 * sin(TIME * 2.0));
    // Rotating rectangle
    float angle = TIME;
    float r = rectangle(uv, vec2(0.5, 0.5), vec2(0.4, 0.15), angle);
    // Pulsating ring
    float ringRadius = 0.32 + 0.08 * sin(TIME * 1.5);
    float ringVal = ring(uv, vec2(0.5, 0.5), ringRadius, 0.03 + 0.01 * cos(TIME * 2.0));
    // Compose
    vec4 color = vec4(0.0);
    color += circleColor * c;
    color += rectColor * r * (1.0 - c);
    color += ringColor * ringVal * (1.0 - c) * (1.0 - r);
    color.a = 1.0;
    gl_FragColor = color;
} 