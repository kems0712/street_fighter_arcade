import pygame
import random
import sys
import os
import math
from fighter import Fighter

#AJUSTE DE AUDIO
pygame.mixer.pre_init(44100, -16, 2, 2048)
pygame.init()

#VENTANA DEL JUEGO
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Street Fighters 2")

#iCONO DE LA VENTANA
try:
    window_icon = pygame.image.load("assets/imagenes/icono/icono.png")
    window_icon = pygame.transform.scale(window_icon, (32, 32))
    pygame.display.set_icon(window_icon)
except:
    pass

#COLORES
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

#FUENTES
try:
    title_font = pygame.font.Font("assets/fuentes/ARCADEPI.ttf", 80)
    menu_font = pygame.font.Font("assets/fuentes/ARCADEPI.ttf", 40)
    count_font = pygame.font.Font("assets/fuentes/ARCADEPI.ttf", 80)
    score_font = pygame.font.Font("assets/fuentes/ARCADEPI.ttf", 80)
except:
    title_font = pygame.font.SysFont("arial", 80)
    menu_font = pygame.font.SysFont("arial", 40)
    count_font = pygame.font.SysFont("arial", 80)
    score_font = pygame.font.SysFont("arial", 80)

#ESTADOS DEL JUEGO
INTRO = "intro"
MENU = "menu"
SELECT = "select"
GAME = "game"
game_state = INTRO

#CONFIGURACIÓN SELECCION
ROWS, COLS = 2, 4
CELL_SIZE = 105
OFFSET_X = (SCREEN_WIDTH // 2) - (COLS * CELL_SIZE // 2)
OFFSET_Y = 380 

fighters_grid = [
    ["ryu", "honda", "blanka", "guile"],
    ["ken", "chunli", "zangief", "dhalsim"]
]

world_map_data = {
    "ryu":     {"country": "japon",  "pos": (596, 192), "data": [118, 1.8, [30, 30], "left"], "steps":  [4, 5, 4, 3, 5, 4, 5, 1, 1, 3, 3]},
    "honda":   {"country": "japon",  "pos": (663, 112), "data": [118, 1.8, [30, 30], "right"], "steps": [3, 5, 6, 5, 3, 4, 4, 1, 1, 7, 6]},
    "blanka":  {"country": "brazil", "pos": (869, 272), "data": [118, 1.8, [30, 30], "right"], "steps": [3, 6, 6, 3, 4, 6, 6, 1, 1, 7, 2]},
    "guile":   {"country": "usa",    "pos": (912, 94),  "data": [118, 1.8, [30, 15], "right"], "steps": [5, 5, 4, 6, 6, 7, 3, 1, 1, 7, 7]},
    "ken":     {"country": "usa",    "pos": (902, 168), "data": [118, 1.8, [30, 30], "left"], "steps":  [4, 4, 4, 5, 3, 4, 4, 1, 1, 5, 4]},
    "chunli":  {"country": "china",   "pos": (522 ,110),"data": [118 ,1.8 ,[30 ,30],"right"],"steps":   [4 ,6 ,7 ,4 ,7 ,7 ,7 ,1 ,1 ,7, 7]},
    "zangief": {"country": "ussr",   "pos": (340 ,113),"data":  [118 ,1.8 ,[30 ,30],"right"],"steps":   [4 ,6 ,3 ,3 ,6 ,2 ,6 ,1 ,1 ,5, 5]},
    "dhalsim": {"country": "india",   "pos": (350 ,205),"data": [118 ,1.8 ,[30 ,30],"right"],"steps":   [6 ,6 ,3 ,3 ,4 ,4 ,4 ,1 ,1 ,7, 4]},
}

#CARGA DE ACTIVOS
icons = {}
portraits = {}
name_logos = {}
maps_bw = {}
maps_color = {}
intro_cache = {} 
background_select = None
last_state = None
current_music = None

victory_img = pygame.image.load("assets/imagenes/icono/gameover.png").convert_alpha()
fight_img = pygame.image.load("assets/imagenes/icono/fight.png").convert_alpha()
timeover_img = pygame.image.load("assets/imagenes/icono/timeover.png").convert_alpha()

#CARGAR IMAGEN K.O.
try:
    ko_img = pygame.image.load("assets/imagenes/icono/ko.png").convert_alpha()
    ko_img = pygame.transform.scale(ko_img, (100, 50)) 
except:
    print("Advertencia: No se encontró ko.png")
    ko_img = None

continue_img = pygame.image.load("assets/imagenes/icono/pushstart.png").convert_alpha()
continue_img = pygame.transform.scale(continue_img, (400, 100))

#VARIABLES DEL RELOJ(IMAGENES)
timer_sprites_yellow = []
timer_sprites_red = []

#Carga de sonidos de locutor
try:
    sonido_fight = pygame.mixer.Sound("assets/sonidos/voces/round1_fight.mp3")
    sonido_fight.set_volume(50) 
except:
    print("No se encontró el sonido de Round 1")
    sonido_fight = None

#FUNCIONES DE APOYO

def swap_color(image, color_original, color_nuevo):
    new_surf = image.copy()
    with pygame.PixelArray(new_surf) as pixels:
        pixels.replace(color_original, color_nuevo)
    return new_surf

def load_all_assets():
    global background_select
    bg_s_path = "assets/imagenes/escenarios/seleccion.png"
    if os.path.exists(bg_s_path):
        background_select = pygame.transform.scale(pygame.image.load(bg_s_path).convert(), (SCREEN_WIDTH, SCREEN_HEIGHT))

    for name, info in world_map_data.items():
        icon_p = f"assets/imagenes/icono/icons/icon_{name}.png"
        port_p = f"assets/imagenes/icono/bigimagenes/big_{name}.png"
        name_p = f"assets/imagenes/icono/nombres/{name}.png"
        
        if os.path.exists(icon_p):
            icons[name] = pygame.transform.scale(pygame.image.load(icon_p).convert_alpha(), (CELL_SIZE, CELL_SIZE))
        if os.path.exists(port_p):
            portraits[name] = pygame.transform.scale(pygame.image.load(port_p).convert_alpha(), (250, 300))
        if os.path.exists(name_p):
            name_logos[name] = pygame.image.load(name_p).convert_alpha()
        
        c = info["country"]
        if c not in maps_bw:
            path_bw = f"assets/imagenes/icono/mapas/map_{c}.png"
            path_col = f"assets/imagenes/icono/mapas/map_{c}_color.png"
            if os.path.exists(path_bw):
                maps_bw[c] = pygame.transform.scale(pygame.image.load(path_bw).convert_alpha(), (60, 40))
            if os.path.exists(path_col):
                maps_color[c] = pygame.transform.scale(pygame.image.load(path_col).convert_alpha(), (60, 40))

def load_timer_assets():
    path_yellow = "assets/imagenes/icono/timer/"
    path_red = "assets/imagenes/icono/timer_blue/" 
    
    COLOR_ORIGINAL_NUMEROS = (255, 255, 0) 

    if not os.path.exists(path_yellow):
        try: os.makedirs(path_yellow)
        except: pass
    if not os.path.exists(path_red):
        try: os.makedirs(path_red)
        except: pass
            
    for i in range(10):
        # 1. CARGAR IMAGEN AMARILLA
        file_path = f"{path_yellow}{i}.png"
        img_yellow = None
        
        if os.path.exists(file_path):
            img = pygame.image.load(file_path).convert_alpha()
            img_yellow = pygame.transform.scale(img, (55, 75))
            timer_sprites_yellow.append(img_yellow)
        else:
            surf = pygame.Surface((55, 75))
            surf.fill(YELLOW)
            img_yellow = surf
            timer_sprites_yellow.append(surf)

        # 2. CARGAR O GENERAR IMAGEN ROJA
        file_path_red = f"{path_red}{i}.png"
        
        if os.path.exists(file_path_red):
            img_red = pygame.image.load(file_path_red).convert_alpha()
            img_red = pygame.transform.scale(img_red, (55, 75))
            timer_sprites_red.append(img_red)
        else:
            img_red = swap_color(img_yellow, COLOR_ORIGINAL_NUMEROS, (255, 30, 30))
            timer_sprites_red.append(img_red)

load_all_assets()
load_timer_assets() 

def play_music(music_path, loop=-1):
    global current_music
    if current_music != music_path:
        if os.path.exists(music_path):
            pygame.mixer.music.stop()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.play(loop)
            current_music = music_path

def load_stage(char_name):
    frames = []
    folder_path = f"assets/imagenes/escenarios/{char_name}"
    if os.path.exists(folder_path):
        files = sorted([f for f in os.listdir(folder_path) if f.startswith('fondo_') and f.endswith('.png')])
        for f in files:
            img = pygame.image.load(os.path.join(folder_path, f)).convert_alpha()
            frames.append(pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)))
    return frames

def draw_text(text, font, color, x, y, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    screen.blit(img, rect)

def draw_image_timer(seconds, x, y):
    time_str = str(max(0, int(seconds))).zfill(2)
    
    if seconds > 10:
        sprites = timer_sprites_yellow
    else:
        sprites = timer_sprites_red
    
    total_width = 0
    for char in time_str:
        if char.isdigit():
            idx = int(char)
            if idx < len(sprites):
                total_width += sprites[idx].get_width()
    
    start_x = x - (total_width // 2)
    current_x = start_x
    
    for char in time_str:
        if char.isdigit():
            idx = int(char)
            if idx < len(sprites):
                screen.blit(sprites[idx], (current_x, y))
                current_x += sprites[idx].get_width()

def draw_health_bar(health, x, y, right_to_left=True):
    ratio = max(0, health / 100)
    max_width = 400
    current_width = max_width * ratio
    
    #borde Blanco y Fondo Rojo
    pygame.draw.rect(screen, WHITE, (x - 5, y - 5, max_width + 10, 35))
    pygame.draw.rect(screen, RED, (x, y, max_width, 25))
    
    #barra Amarilla
    if right_to_left:
        pygame.draw.rect(screen, YELLOW, (x, y, current_width, 25))
    else:
        empty_space = max_width - current_width
        pygame.draw.rect(screen, YELLOW, (x + empty_space, y, current_width, 25))

#VARIABLES DE LUCHA
background_fight = []
bg_index = 0
fighter_1 = None
fighter_2 = None
p1_pos = [0, 0]
p2_pos = [3, 0]
p1_ready = False
p2_ready = False
score = [0, 0]
round_over = False
fight_timer = 90
intro_count = 3
timer_last_update = 0
last_count_update = 0
show_fight_img = False
fight_img_timer = 0

#VARIABLES GLOBALES
camera_x = 0
audio_reproducido = False
effects_group = pygame.sprite.Group()
projectiles_group = pygame.sprite.Group()

def start_fight():
    global fighter_1, fighter_2, fight_timer, intro_count, round_over, timer_last_update, last_count_update
    global background_fight, bg_index, show_fight_img, effects_group, projectiles_group, audio_reproducido
    
    effects_group.empty()
    projectiles_group.empty()
    
    p1_char = fighters_grid[p1_pos[1]][p1_pos[0]]
    p2_char = fighters_grid[p2_pos[1]][p2_pos[0]]
    
    chosen_stage = random.choice([p1_char, p2_char])
    background_fight = load_stage(chosen_stage)
    bg_index = 0
    
    sheet1 = pygame.image.load(f"assets/imagenes/personajes/{p1_char}/sprites/{p1_char.capitalize()}.png").convert_alpha()
    sheet2 = pygame.image.load(f"assets/imagenes/personajes/{p2_char}/sprites/{p2_char.capitalize()}.png").convert_alpha()
    
    if p1_char == p2_char:
        sheet2 = swap_color(sheet2, (255, 255, 255), (100, 200, 255))
    
    fighter_1 = Fighter(1, 200, 395, False, world_map_data[p1_char]["data"], sheet1, world_map_data[p1_char]["steps"], p1_char)
    fighter_2 = Fighter(2, 900, 395, True, world_map_data[p2_char]["data"], sheet2, world_map_data[p2_char]["steps"], p2_char)

    fighter_1.update(fighter_2, effects_group, projectiles_group)
    fighter_2.update(fighter_1, effects_group, projectiles_group)

    music_path = f"assets/sonidos/musica/escenarios/{chosen_stage}.mp3"
    play_music(music_path)
    
    fight_timer = 90
    intro_count = 3
    round_over = False
    show_fight_img = False
    timer_last_update = pygame.time.get_ticks()
    last_count_update = pygame.time.get_ticks()
    audio_reproducido = False 

menu_bg_raw = pygame.image.load("assets/imagenes/escenarios/menu.jpg").convert()
background_menu = pygame.transform.scale(menu_bg_raw, (SCREEN_WIDTH, SCREEN_HEIGHT))

clock = pygame.time.Clock()
running = True
intro_index = 0

#BUCLE PRINCIPAL
while running:
    current_time = pygame.time.get_ticks()
    clock.tick(60)

    if game_state != last_state:
        if game_state == INTRO: play_music("assets/sonidos/musica/intro.mp3")
        elif game_state in [MENU, SELECT]: play_music("assets/sonidos/musica/select.mp3")
        last_state = game_state

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if game_state == MENU:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                game_state = SELECT
        
        elif game_state == SELECT:
            if event.type == pygame.KEYDOWN:
                if not p1_ready:
                    if event.key == pygame.K_a and p1_pos[0] > 0: p1_pos[0] -= 1
                    if event.key == pygame.K_d and p1_pos[0] < COLS - 1: p1_pos[0] += 1
                    if event.key == pygame.K_w and p1_pos[1] > 0: p1_pos[1] -= 1
                    if event.key == pygame.K_s and p1_pos[1] < ROWS - 1: p1_pos[1] += 1
                    if event.key == pygame.K_SPACE: p1_ready = True
                elif event.key == pygame.K_ESCAPE: p1_ready = False

                if not p2_ready:
                    if event.key == pygame.K_LEFT and p2_pos[0] > 0: p2_pos[0] -= 1
                    if event.key == pygame.K_RIGHT and p2_pos[0] < COLS - 1: p2_pos[0] += 1
                    if event.key == pygame.K_UP and p2_pos[1] > 0: p2_pos[1] -= 1
                    if event.key == pygame.K_DOWN and p2_pos[1] < ROWS - 1: p2_pos[1] += 1
                    if event.key == pygame.K_RETURN: p2_ready = True
                elif event.key == pygame.K_BACKSPACE: p2_ready = False

    if game_state == INTRO:
        frame_num = int(intro_index)
        intro_path = f"assets/imagenes/intro/intro_{frame_num}.jpg"
        if os.path.exists(intro_path):
            img = pygame.image.load(intro_path).convert()
            screen.blit(pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
            intro_index += 0.45
        else:
            game_state = MENU
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN] or keys[pygame.K_SPACE]:
            game_state = MENU

    elif game_state == MENU:
        screen.blit(background_menu, (0, 0))
        menu_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        menu_overlay.set_alpha(160)
        menu_overlay.fill(BLACK)
        screen.blit(menu_overlay, (0, 0))
        fade_alpha = int((math.sin(current_time * 0.005) + 1) * 127.5)
        continue_img.set_alpha(fade_alpha)
        screen.blit(continue_img, continue_img.get_rect(center=(SCREEN_WIDTH // 2, 470)))

    elif game_state == SELECT:
        screen.blit(background_select, (0,0))
        p1_char = fighters_grid[p1_pos[1]][p1_pos[0]]
        p2_char = fighters_grid[p2_pos[1]][p2_pos[0]]
        
        for name, data in world_map_data.items():
            img = maps_color.get(data["country"]) if (name in [p1_char, p2_char] and (current_time // 200) % 2 == 0) else maps_bw.get(data["country"])
            if img: screen.blit(img, data["pos"])
        
        if not p1_ready or (current_time // 100) % 2 == 0:
            screen.blit(portraits[p1_char], (-5, 305))
        if not p2_ready or (current_time // 100) % 2 == 0:
            screen.blit(pygame.transform.flip(portraits[p2_char], True, False), (SCREEN_WIDTH - 250, 300))
        
        if p1_char in name_logos:
            screen.blit(pygame.transform.scale(name_logos[p1_char], (160, 80)), (50, 40))
        if p2_char in name_logos:
            logo_p2 = pygame.transform.scale(name_logos[p2_char], (160, 80))
            screen.blit(logo_p2, (SCREEN_WIDTH - logo_p2.get_width() - 50, 40))

        for r in range(ROWS):
            for c in range(COLS):
                name = fighters_grid[r][c]
                x, y = OFFSET_X + c * CELL_SIZE, OFFSET_Y + r * CELL_SIZE
                screen.blit(icons[name], (x, y))
                pygame.draw.rect(screen, WHITE, (x, y, CELL_SIZE, CELL_SIZE), 1)

        #cURSORES
        glow = abs(math.sin(current_time * 0.01)) * 255
        pygame.draw.rect(screen, (0, glow, glow) if not p1_ready else WHITE, 
                         (OFFSET_X + p1_pos[0] * CELL_SIZE, OFFSET_Y + p1_pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE), 6)
        pygame.draw.rect(screen, (glow, 0, 0) if not p2_ready else WHITE, 
                         (OFFSET_X + p2_pos[0] * CELL_SIZE, OFFSET_Y + p2_pos[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE), 4)

        if p1_ready and p2_ready:
            start_fight()
            game_state = GAME

    elif game_state == GAME:
        if fighter_1 and fighter_2:
            bg_index += 0.12
            if bg_index >= len(background_fight): bg_index = 0
            screen.blit(background_fight[int(bg_index)], (0 - camera_x, 0))

            draw_health_bar(fighter_1.health, 170, 30, right_to_left=False)
            draw_health_bar(fighter_2.health, 620, 30, right_to_left=True)

            #INDICADORES VISUALES DE COOLDOWN
            time_now = pygame.time.get_ticks()

            # P1 Indicador (Circulo debajo de la barra de vida P1)
            # Verde si está listo, Rojo si faltan segundos
            color_p1 = (0, 255, 0) if (time_now - fighter_1.last_special_attack >= fighter_1.special_cooldown) else (255, 0, 0)
            pygame.draw.circle(screen, color_p1, (50, 80), 10)
            pygame.draw.circle(screen, WHITE, (50, 80), 10, 2) # Borde blanco

            # P2 Indicador (Circulo debajo de la barra de vida P2)
            color_p2 = (0, 255, 0) if (time_now - fighter_2.last_special_attack >= fighter_2.special_cooldown) else (255, 0, 0)
            pygame.draw.circle(screen, color_p2, (1150, 80), 10)
            pygame.draw.circle(screen, WHITE, (1150, 80), 10, 2) # Borde blanco
            
            if ko_img:
                ko_rect = ko_img.get_rect(center=(SCREEN_WIDTH // 2, 42))
                screen.blit(ko_img, ko_rect)

            p1_char_game = fighters_grid[p1_pos[1]][p1_pos[0]]
            p2_char_game = fighters_grid[p2_pos[1]][p2_pos[0]]
            if p1_char_game in name_logos:
                screen.blit(pygame.transform.scale(name_logos[p1_char_game], (140, 80)), (20, 0))
            if p2_char_game in name_logos:
                screen.blit(pygame.transform.scale(name_logos[p2_char_game], (120, 80)), (SCREEN_WIDTH - 180, 0))

            draw_text(str(score[0]), score_font, YELLOW, SCREEN_WIDTH//2 - 100, 70)
            draw_text(str(score[1]), score_font, YELLOW, SCREEN_WIDTH//2 + 60, 70)
            
            display_time = max(0, int(fight_timer))
            draw_image_timer(display_time, SCREEN_WIDTH // 2, 70)

            if intro_count > 0:
                if intro_count < len(timer_sprites_red):
                    cnt_img = timer_sprites_red[intro_count]
                    cnt_img = pygame.transform.scale(cnt_img, (80, 150))
                    cnt_rect = cnt_img.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                    screen.blit(cnt_img, cnt_rect)
                else:
                    draw_text(str(intro_count), count_font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2, True)
                
                if intro_count == 2 and not audio_reproducido and sonido_fight:
                    sonido_fight.play()
                    audio_reproducido = True

                if current_time - last_count_update >= 1000:
                    intro_count -= 1
                    last_count_update = current_time
                
                fighter_1.update(fighter_2, effects_group, projectiles_group)
                fighter_2.update(fighter_1, effects_group, projectiles_group)
            
            else:
                if not show_fight_img and not round_over:
                    show_fight_img = True
                    fight_img_timer = current_time

                if show_fight_img:
                    elapsed = current_time - fight_img_timer
                    if elapsed < 1000:
                        zoom_factor = 2.5 * min(1.0, elapsed / 200)
                        w_f = int(fight_img.get_width() * zoom_factor)
                        h_f = int(fight_img.get_height() * zoom_factor)
                        if w_f > 0 and h_f > 0:
                            big_fight = pygame.transform.scale(fight_img, (w_f, h_f))
                            screen.blit(big_fight, big_fight.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

                if not round_over:
                    if current_time - timer_last_update >= 1000:
                        fight_timer -= 1
                        timer_last_update = current_time
                    
                    if fight_timer <= 0 or not fighter_1.alive or not fighter_2.alive:
                        round_over = True
                        round_over_time = current_time
                        if fighter_1.health > fighter_2.health:
                            score[0] += 1
                            if fighter_1.alive: fighter_1.won = True
                        elif fighter_2.health > fighter_1.health:
                            score[1] += 1
                            if fighter_2.alive: fighter_2.won = True

                    fighter_1.mover(SCREEN_WIDTH, SCREEN_HEIGHT, fighter_2, round_over, camera_x)
                    fighter_2.mover(SCREEN_WIDTH, SCREEN_HEIGHT, fighter_1, round_over, camera_x)

                # 1 Actualizar logica de personajes
                fighter_1.update(fighter_2, effects_group, projectiles_group)
                fighter_2.update(fighter_1, effects_group, projectiles_group)
                
                # 2Actualizar logica de proyectiles
                for p in projectiles_group:
                    target = fighter_2 if p.direction == 1 else fighter_1
                    p.update(target)

            # 3 DIBUJAR TODO
            fighter_1.draw(screen, camera_x)
            fighter_2.draw(screen, camera_x)

            #DIBUJAR PROYECTILES
            for p in projectiles_group:
                p.draw(screen, camera_x)
                
            effects_group.update(camera_x)
            for effect in effects_group: 
                effect.draw(screen, camera_x)

            if round_over:
                if fight_timer <= 0:
                    big_to = pygame.transform.scale(timeover_img, (timeover_img.get_width() * 2, timeover_img.get_height() * 2))
                    screen.blit(big_to, big_to.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
                else:
                    big_v = pygame.transform.scale(victory_img, (victory_img.get_width() * 1.5, victory_img.get_height() * 1.5))
                    screen.blit(big_v, big_v.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))
                
                if current_time - round_over_time > 3000:
                    if score[0] >= 2 or score[1] >= 2:
                        game_state = MENU
                        p1_ready, p2_ready = False, False
                        score = [0, 0]
                    else:
                        start_fight()

    pygame.display.flip()

pygame.quit()
sys.exit()