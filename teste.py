"""
Tetris Bolado

Por trás da interface, há uma matriz que vai controlar o jogo,
denotada pela variável MATRIZ, onde 0 não contém peça, e 1 se o espaço já está ocupado
também tem a matriz peça, que, junto da tupla POSICAO_PECA vai denotar a geometria e posição da peça atual.
A matriz peça pode ser 2x2, 3x3 ou 4x4 dependendo da peça em questão

Fluxo do jogo:
Começa o jogo com a matriz toda zerada
O jogo pega uma peça da sacola e renderiza
Esse peça é a atual e o jogador pode controla-la
Depois dela encostar em algo da base (No tempo seguinte,se a próxima posição tiver algum 1 na matriz do tabuleiro),
ela fica fixa, uma próxima peça sai da sacola e se torna a principal
Se a próxima peça não tiver espaço para surgir, o jogador perde
Se ele tiver limpado X linhas, ele ganha

Ponto inferior esquerdo do grid: (-0.5,-1)
Ponto superior direito do grid: (0.5,1)

Cada quadrado tem 40x40 pixels ou (0.05) quando normalizado
"""
import sys
from pathlib import Path

import glfw
import moderngl
import numpy as np

SHADERS = Path(__file__).parent / "shaders"

#Matriz para controlar o estado do jogo
MATRIZ = np.zeros((20,10))

# Controle de linhas limpas
LINHAS_LIMPAS = 0

# Cada quadrado tem 40x40pxs (GRID 10x20)
BASE_JANELA = 800
ALTURA_JANELA = 800

MATRIZ_PECA = [
    [1, 1],
    [1, 1]
]

POSICAO_INICIAL = (19, 4)
POSICAO = POSICAO_INICIAL

LIMITE_Y = 0.9
LIMITE_X = 0.4    
ESCALA_JOGADOR = 0.20


ESCALA_TIRO = 0.06
#Unidades de NDC por SEGUNDO -- nao por quadro. Essa e a diferenca do capitulo.
VEL_JOGADOR, VEL_ALVO, VEL_TIRO = 1.5, 1.2, 2.5
LIMITE_Y = 0.78   # ate onde jogador e alvo sobem

# Placar: uma marca por acerto, desenhada com o MESMO quadrado.
PLACAR_CANTO = (-0.90, 0.90)
PLACAR_PASSO, ESCALA_MARCA = 0.058, 0.042
PLACAR_MAXIMO = 12  # depois disso a fileira sairia da tela
COR_O = (0.89, 0.62, 0.01, 1.0)
COR_T = (0.686,0.16,0.55, 1.0)
COR_I = (0.06, 0.607, 0.84, 1.0)
COR_Z = (0.843,0.06,0.2,1.0)
COR_J = (0.13, 0.255, 0.77, 1.0)
COR_L= (0.89,0.36,0.08,1.0)
COR_S = (0.35, 0.695, 0.004,1.0)


FUNDO = (0.04, 0.05, 0.09, 1.0)

# ------------------------------------------------------------------ inicializacao

# Essa função considera que a posição está em um lugar válido
# Temos que chamar ela sempre que a peça bater em algum lugar, não a cada instante de tempo
def verifica_matriz(matriz_peca, posicao):
    global LINHAS_LIMPAS, MATRIZ
    linha_base, coluna_base = posicao
    tamanho = len(matriz_peca)

    # Fixa a peça no tabuleiro
    for r in range(tamanho):
        for c in range(tamanho):
            if matriz_peca[r][c] == 1:
                MATRIZ[linha_base - r][coluna_base + c] = 1

    # Verifica e limpa linhas completas (de cima para baixo)
    for i in range(19, -1, -1):
        if np.all(MATRIZ[i] == 1):  # completou a linha
            LINHAS_LIMPAS += 1
            for k in range(i, 19):  # desce o que está acima
                MATRIZ[k] = MATRIZ[k + 1]
            MATRIZ[19] = np.zeros(10)

def pode_descer(matriz_peca, posicao):
    linha_base, coluna_base = posicao
    tamanho = len(matriz_peca)

    for r in range(tamanho):
        for c in range(tamanho):
            if matriz_peca[r][c] == 1:
                linha = linha_base - r - 1  # célula embaixo
                coluna = coluna_base + c
                if linha < 0:               # bateu no chão
                    return False
                if MATRIZ[linha][coluna] == 1:  # bateu em outra peça
                    return False
    return True

def pode_ir_de_ladinho(matriz_peca, posicao):
    linha_base, coluna_base = posicao
    tamanho = len(matriz_peca)
    for r in range(tamanho):
        for c in range(tamanho):
            if matriz_peca[r][c] == 1:
                linha = linha_base - r
                coluna = coluna_base +c
                #print(coluna)
                if(coluna+1 < 10):
                    if MATRIZ[linha][coluna+1] ==1 or MATRIZ[linha][coluna-1]:
                        return False
    return True

def posicao_para_tela(posicao):
    """Converte (linha, coluna) da célula de cima à esquerda da peça
    para o centro do bloco 2x2 na tela."""
    linha, coluna = posicao
    x = -0.45 + coluna * 0.1   # centro da célula
    y = -0.95 + linha * 0.1
    return (x + 0.05, y - 0.05)  # meia célula para a direita e para baixo

def erro_glfw(codigo, descricao):
    """Sem este callback, a razao real de uma falha do GLFW e descartada e
    so resta a mensagem generica do sys.exit."""
    print(f"GLFW [{codigo}]: {descricao}", file=sys.stderr)


glfw.set_error_callback(erro_glfw)  # antes de glfw.init(), de proposito

if not glfw.init():
    sys.exit("FALHA: glfw nao inicializou")

glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 0)
glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
# Sem a dica acima, o macOS recusa qualquer contexto 3.2+ e
# create_window devolve None. E inofensiva no Windows e no Linux.
glfw.window_hint(glfw.SAMPLES, 4)
# Sem esta linha, redimensionar a janela deforma a cena: o viewport continua
# com o tamanho antigo, e o NDC deixa de ser quadrado na tela.
glfw.window_hint(glfw.RESIZABLE, False)

janela = glfw.create_window(BASE_JANELA,  ALTURA_JANELA, "Acerte o alvo", None, None)
if not janela:
    glfw.terminate()
    sys.exit("FALHA: nao foi possivel criar a janela")

glfw.make_context_current(janela)
glfw.swap_interval(1)  # espera o retraco vertical: ver a nota sobre vsync
ctx = moderngl.create_context()

prog = ctx.program(
    vertex_shader=(SHADERS / "acerte_o_alvo.vert").read_text(encoding="utf-8"),
    fragment_shader=(SHADERS / "basico.frag").read_text(encoding="utf-8"),
)

# ---------------------------------------------------------------------- geometria

CANTOS = ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))
CORES = ((1.0, 0.2, 0.2), (0.2, 1.0, 0.2), (0.2, 0.4, 1.0), (1.0, 0.9, 0.2))


PECA_O = np.array([
    -0.5, -0.5, 0.0, 1.0, 0.89, 0.62, 0.01, 1.0,
     0.5, -0.5, 0.0, 1.0, 0.89, 0.62, 0.01, 1.0,
     0.5,  0.5, 0.0, 1.0, 0.89, 0.62, 0.01, 1.0,
    -0.5,  0.5, 0.0, 1.0, 0.89, 0.62, 0.01, 1.0
], dtype='f4')

CINZA = (0.5, 0.5, 0.5)

QUADRADO_CINZA = np.array([
    v for (x, y) in CANTOS
    for v in (x, y, 0.0, 1.0) + CINZA + (1.0,)
], dtype='f4')

LINHA_V = np.array([
    0.0, -0.5, 0.0, 1.0,   1.0, 1.0, 1.0, 1.0,   # ponto de baixo
    0.0,  0.5, 0.0, 1.0,   1.0, 1.0, 1.0, 1.0,   # ponto de cima
], dtype='f4')

LINHA_H = np.array([
    -0.5, 0.0, 0.0, 1.0,   1.0, 1.0, 1.0, 1.0,   # ponto da esquerda
     0.5, 0.0, 0.0, 1.0,   1.0, 1.0, 1.0, 1.0,   # ponto da direita
], dtype='f4')

# Os MESMOS quatro vertices, lidos de duas maneiras. Como no exemplo da
# diagonal: muda so a ordem de leitura, o VBO nao e tocado.
TRIANGULOS = np.array([0, 1, 2, 2, 3, 0], dtype='u4')  # dois triangulos
CONTORNO = np.array([0, 1, 2, 3], dtype='u4')          # o ciclo dos cantos

vbo = ctx.buffer(PECA_O.tobytes())
vbo_cinza = ctx.buffer(QUADRADO_CINZA.tobytes())
ebo_cheio = ctx.buffer(TRIANGULOS.tobytes())
ebo_borda = ctx.buffer(CONTORNO.tobytes())

# Um VAO por EBO: o buffer de indices faz parte do estado do VAO.
vao_cheio = ctx.vertex_array(
    prog, [(vbo, '4f 4f', 'vPosition', 'vColors')], index_buffer=ebo_cheio)
vao_cheio_cinza = ctx.vertex_array(
    prog, [(vbo_cinza, '4f 4f', 'vPosition', 'vColors')], index_buffer=ebo_cheio)
vao_borda = ctx.vertex_array(
    prog, [(vbo, '4f 4f', 'vPosition', 'vColors')], index_buffer=ebo_borda)
vao_linha_v = ctx.vertex_array(
    prog, [(ctx.buffer(LINHA_V.tobytes()), '4f 4f', 'vPosition', 'vColors')])
vao_linha_h = ctx.vertex_array(
    prog, [(ctx.buffer(LINHA_H.tobytes()), '4f 4f', 'vPosition', 'vColors')])
# ------------------------------------------------------------- estado e controles

alvo_y = 0.0
sentido_alvo = 1.0
atirando, tiro = False, [0.0, 0.0]
acertos = 0
sobe, desce, direita ,esquerda,sentido_jogador_y,sentido_jogador_x,antes = 0, 0, 0 ,0, 0, 0, 0


def tecla(window, key, scancode, action, mods):
    global atirando, sobe, desce, direita, esquerda, sentido_jogador_y, sentido_jogador_x, antes,POSICAO
    if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
        glfw.set_window_should_close(window, True)

    elif key == glfw.KEY_LEFT or key == glfw.KEY_RIGHT:
        direita = glfw.get_key(janela, glfw.KEY_RIGHT) == glfw.PRESS
        esquerda  = glfw.get_key(janela, glfw.KEY_LEFT) == glfw.PRESS
        sentido_jogador_x = float(direita) - float(esquerda)
        linha, coluna = POSICAO
        coluna = coluna + int(sentido_jogador_x)
        coluna = max(0, min(10 - len(MATRIZ_PECA), coluna))
        if(pode_ir_de_ladinho(MATRIZ_PECA,POSICAO)):
            POSICAO = (linha, coluna)
    elif key == glfw.KEY_DOWN:
        linha, coluna = POSICAO
        if(pode_descer(MATRIZ_PECA,POSICAO)):
            POSICAO = (linha-1, coluna)


glfw.set_key_callback(janela, tecla)


def desenhar(vao, escala, deslocamento, modo=moderngl.TRIANGLES):
    prog['u_escala'].value = escala
    prog['u_deslocamento'].value = deslocamento
    vao.render(modo)



# ------------------------------------------------------------------ laco principal

instante_anterior = glfw.get_time()
quadros, marco = 0, instante_anterior

while not glfw.window_should_close(janela):
    agora = glfw.get_time()

    instante_anterior = agora

    # --- desenho ---
    ctx.clear(*FUNDO)
    
    for l in range(11): #11 Para aparecer na esquerda também
        desenhar(vao_linha_v, 2.0, (-0.5 + (l * 0.1), 0.0), moderngl.LINES)    # atravessa a tela toda no meio
    for l in range(21): #11 Para aparecer na esquerda também
        desenhar(vao_linha_h, 1, (0.0, -1 + (l * 0.1)), moderngl.LINES)    # atravessa a tela toda no meio

    for i in range(20):
        for j in range(10):
            if(MATRIZ[i][j] == 1):
                desenhar(vao_cheio_cinza, 0.1, (-0.45 + (j * 0.1), -0.95 + (i * 0.1)))

    desenhar(vao_cheio, ESCALA_JOGADOR, posicao_para_tela(POSICAO))

    # Placar: uma marca por acerto, com o MESMO quadrado de todo o resto.

    glfw.swap_buffers(janela)
    glfw.poll_events()

    # Taxa de quadros no titulo. E o numero que muda quando se troca o
    # swap_interval; a velocidade do jogo, nao.
    quadros += 1
    if agora - marco >= 0.8:
        if(pode_descer(MATRIZ_PECA, POSICAO)):
            linha, coluna = POSICAO
            POSICAO = (linha - 1, coluna)
        else:
            linha_base, coluna_base = POSICAO
            tamanho = len(MATRIZ_PECA)
            for r in range(tamanho):
                    for c in range(tamanho):
                        if MATRIZ_PECA[r][c] == 1:
                            MATRIZ[linha_base - r][coluna_base + c] = 1
            verifica_matriz(MATRIZ_PECA, POSICAO) # ve se completou a linha
            POSICAO = POSICAO_INICIAL

        glfw.set_window_title(
            janela, f"Acerte o alvo - {acertos} acertos - "
                    f"{quadros / (agora - marco):5.1f} fps")
        quadros, marco = 0, agora

for recurso in (vao_cheio, vao_borda, ebo_cheio, ebo_borda, vbo, prog):
    recurso.release()
glfw.terminate()
print(f"Execucao finalizada. Acertos: {acertos}")


"""
if(Sacola.empty()):
  Sacola = ['O', 'T' , 'I', 'Z', 'S', 'J', 'L']
  random.shuffle(Sacola)
else:
	peca_atual = Sacola.pop(0)
"""