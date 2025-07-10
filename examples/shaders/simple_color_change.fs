/*{
    "DESCRIPTION": "Every pixel is the selected color.",
    "CREDIT": "pyvvisf example",
    "ISFVSN": "2.0",
    "CATEGORIES": ["Generator"],
    "INPUTS": [
        {"NAME": "color", "TYPE": "color", "DEFAULT": [1.0, 0.0, 0.0, 1.0]}
    ]
}*/
void main() {
    gl_FragColor = color;
} 