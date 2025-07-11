/*{
  "DESCRIPTION": "Multi-pass: first pass outputs red, second swaps red/blue to output blue",
  "ISFVSN": "2.0",
  "PASSES": [
    {"TARGET": "redBuffer"},
    {}
  ]
}*/

// First pass: output red to redBuffer
// Second pass: read from redBuffer, swap red/blue, output blue
void main() {
    if (PASSINDEX == 0) {
        gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0); // Red
    } else if (PASSINDEX == 1) {
        vec4 c = IMG_THIS_NORM_PIXEL(redBuffer);
        gl_FragColor = vec4(c.b, c.g, c.r, c.a); // Swap R/B (should be blue)
    }
} 