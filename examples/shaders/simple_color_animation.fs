/*{
    "DESCRIPTION": "Fades between two user-selected colors over time.",
    "CREDIT": "pyvvisf example",
    "ISFVSN": "2.0",
    "CATEGORIES": ["Generator"],
    "INPUTS": [
        {"NAME": "colorA", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]},
        {"NAME": "colorB", "TYPE": "color", "DEFAULT": [0.0, 0.0, 1.0, 1.0]}
    ]
}*/
void main() {
    float t = 0.5 + 0.5 * sin(TIME);
    gl_FragColor = mix(colorA, colorB, t);
} 