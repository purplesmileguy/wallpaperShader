import moderngl
import pygame
import numpy as np
import win32gui
import win32con
from ctypes import windll

# Настройки
WIDTH, HEIGHT = 1920, 1200
FPS = 26  # Фиксируем FPS на 26

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode(
    (WIDTH, HEIGHT),
    pygame.OPENGL | pygame.DOUBLEBUF | pygame.NOFRAME
)
hwnd = pygame.display.get_wm_info()["window"]

# Функция для установки обоев
workerw = None
def find_workerw(hwnd, extra):
    global workerw
    if win32gui.GetClassName(hwnd) == "WorkerW":
        workerw = hwnd

def set_wallpaper():
    global workerw
    progman = win32gui.FindWindow("Progman", None)
    win32gui.SendMessageTimeout(progman, 0x52C, 0, None, 0, 1000)
    win32gui.EnumWindows(find_workerw, None)
    if workerw:
        win32gui.SetParent(hwnd, workerw)
        win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, 0, 0, WIDTH, HEIGHT, 0)

set_wallpaper()

# OpenGL контекст
ctx = moderngl.create_context(require=330)
ctx.enable(moderngl.BLEND)

# Шейдеры
vertex_shader = """
#version 330
in vec2 in_position;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
}
"""
fragment_shader = """
#version 330
uniform float time;
uniform vec2 resolution;
out vec4 fragColor;

// --- Noise from procedural pseudo-Perlin (adapted from IQ) ---------
float noise3(vec3 x) {
    vec3 p = floor(x), f = fract(x);
    f = f * f * (3.0 - 2.0 * f);  // smoothstep to make derivative continuous at borders

    #define hash3(p) fract(sin(1e3 * dot(p, vec3(1, 57, -13.7))) * 4375.5453)

    return mix(mix(mix(hash3(p + vec3(0, 0, 0)), hash3(p + vec3(1, 0, 0)), f.x),
                   mix(hash3(p + vec3(0, 1, 0)), hash3(p + vec3(1, 1, 0)), f.x), f.y),
               mix(mix(hash3(p + vec3(0, 0, 1)), hash3(p + vec3(1, 0, 1)), f.x),
                   mix(hash3(p + vec3(0, 1, 1)), hash3(p + vec3(1, 1, 1)), f.x), f.y), f.z);
}

#define noise(x) (noise3(x) + noise3(x + 11.5)) / 2.0  // pseudoperlin improvement

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;
    uv = uv * 2.0 - 1.0;
    uv.x *= resolution.x / resolution.y;
    
    float n = noise(vec3(uv * 8.0, 0.1 * time));
    float v = sin(6.28 * 10.0 * n);
    
    v = smoothstep(1.0, 0.0, 0.5 * abs(v) / fwidth(v));
    
    vec3 color = mix(vec3(0.0), vec3(0.5 + 0.5 * sin(12.0 * n + vec3(0.0, 2.1, -2.1))), v);
    
    fragColor = vec4(color, 1.0);
}

"""

prog = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
prog["resolution"] = (WIDTH, HEIGHT)

# Полноэкранный квадрат
vertices = np.array([
    -1, -1,  1, -1, -1,  1,
    -1,  1,  1, -1,  1,  1
], dtype='f4')

vbo = ctx.buffer(vertices)
vao = ctx.simple_vertex_array(prog, vbo, "in_position")

# Основной цикл
clock = pygame.time.Clock()
running = True
start_time = pygame.time.get_ticks()

while running:
    clock.tick(FPS)  # FPS лок
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    prog["time"] = (pygame.time.get_ticks() - start_time) / 1000.0
    ctx.clear(0.0, 0.0, 0.0, 0.0)
    vao.render(moderngl.TRIANGLES)
    pygame.display.flip()

# Очистка
vao.release()
vbo.release()
prog.release()
pygame.quit()
input("Нажмите Enter, чтобы закрыть окно...")

