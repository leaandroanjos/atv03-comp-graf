#version 400 core
// Vertex shader
// Posiciona um quadrado em qualquer lugar
// da tela, com qualquer tamanho.
// Usa a cor que vem do vertice.

layout(location = 0) in vec4 vPosition;
layout(location = 1) in vec4 vColors;

uniform float u_escala;
uniform vec2  u_deslocamento;

out vec4 v2fcolor;

void main() {
    gl_Position = vec4(vPosition.xy * u_escala + u_deslocamento, vPosition.zw);
    v2fcolor = vColors;
}
