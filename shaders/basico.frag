#version 400 core
// Fragment shader de repasse.
// Devolve a cor ja interpolada pelo rasterizador.

in vec4 v2fcolor;
out vec4 outfragcolor;

void main() {
    outfragcolor = v2fcolor;
}
