import pygame
import random
import sys
import os
import math
from pathlib import Path
from arcade_machine_sdk import GameBase, GameMeta, BASE_WIDTH, BASE_HEIGHT

# Importar clase Fighter
from fighter import Fighter

#GESTION DE RUTAS (REQUISITO SDK)
GAME_DIR = Path(__file__).resolve().parent.parent 
ASSETS_DIR = GAME_DIR / "assets"

class StreetFighterGame(GameBase):
    def __init__(self, metadata: GameMeta):
        super().__init__(metadata)
        
        #CONFIGURACION DE RESOLUCION
        # juego original es 1200x600, el SDK es 1024x768
        self.original_width = 1200
        self.original_height = 600
        # Creamos un lienzo interno
        self.game_canvas = pygame.Surface((self.original_width, self.original_height))

        #VARIABLES DE ESTADO
        self.game_state = "intro"
        self.intro_index = 0
        self.current_music = None
        self.last_state = None
        
        #Seleccion de personajes
        self.p1_pos = [0, 0]
        self.p2_pos = [3, 0]
        self.p1_ready = False
        self.p2_ready = False
        
        #Combate
        self.fighter_1 = None
        self.fighter_2 = None
        self.background_fight = []
        self.bg_index = 0
        self.score = [0, 0]
        self.fight_timer = 90
        self.intro_count = 3
        self.round_over = False
        self.show_fight_img = False
        self.fight_img_timer = 0
        self.camera_x = 0
        self.audio_reproducido = False
        
        #timers
        self.timer_last_update = 0
        self.last_count_update = 0
        
        #grupos de sprites
        self.effects_group = pygame.sprite.Group()
        self.projectiles_group = pygame.sprite.Group()

        #satos estaticos (Mapas, Grid)
        self.ROWS, self.COLS = 2, 4
        self.CELL_SIZE = 105
        self.OFFSET_X = (self.original_width // 2) - (self.COLS * self.CELL_SIZE // 2)
        self.OFFSET_Y = 380
        
        self.fighters_grid = [
            ["ryu", "honda", "blanka", "guile"],
            ["ken", "chunli", "zangief", "dhalsim"]
        ]
        
        self.world_map_data = {
            "ryu":     {"country": "japon",  "pos": (596, 192), "data": [118, 1.8, [30, 30], "left"], "steps":  [4, 5, 4, 3, 5, 4, 5, 1, 1, 3, 3]},
            "honda":   {"country": "japon",  "pos": (663, 112), "data": [118, 1.8, [30, 30], "right"], "steps": [3, 5, 6, 5, 3, 4, 4, 1, 1, 7, 6]},
            "blanka":  {"country": "brazil", "pos": (869, 272), "data": [118, 1.8, [30, 30], "right"], "steps": [3, 6, 6, 3, 4, 6, 6, 1, 1, 7, 2]},
            "guile":   {"country": "usa",    "pos": (912, 94),  "data": [118, 1.8, [30, 15], "right"], "steps": [5, 5, 4, 6, 6, 7, 3, 1, 1, 7, 7]},
            "ken":     {"country": "usa",    "pos": (902, 168), "data": [118, 1.8, [30, 30], "left"], "steps":  [4, 4, 4, 5, 3, 4, 4, 1, 1, 5, 4]},
            "chunli":  {"country": "china",   "pos": (522 ,110),"data": [118 ,1.8 ,[30 ,30],"right"],"steps":   [4 ,6 ,7 ,4 ,7 ,7 ,7 ,1 ,1 ,7, 7]},
            "zangief": {"country": "ussr",   "pos": (340 ,113),"data":  [118 ,1.8 ,[30 ,30],"right"],"steps":   [4 ,6 ,3 ,3 ,6 ,2 ,6 ,1 ,1 ,5, 5]},
            "dhalsim": {"country": "india",   "pos": (350 ,205),"data": [118 ,1.8 ,[30 ,30],"right"],"steps":   [6 ,6 ,3 ,4 ,3 ,4 ,4 ,1 ,1 ,7, 4]},
        }

        #diccionarios de recursos
        self.icons = {}
        self.portraits = {}
        self.name_logos = {}
        self.maps_bw = {}
        self.maps_color = {}
        self.timer_sprites_yellow = []
        self.timer_sprites_red = []

    #AUXILIARES
    def get_asset_path(self, relative_path):
        return str(ASSETS_DIR / relative_path)

    def swap_color(self, image, color_original, color_nuevo):
        new_surf = image.copy()
        with pygame.PixelArray(new_surf) as pixels:
            pixels.replace(color_original, color_nuevo)
        return new_surf

    def play_music(self, music_file, loop=-1):
        full_path = self.get_asset_path(music_file)
        if self.current_music != full_path:
            if os.path.exists(full_path):
                pygame.mixer.music.stop()
                pygame.mixer.music.load(full_path)
                pygame.mixer.music.play(loop)
                self.current_music = full_path

    def load_stage(self, char_name):
        frames = []
        folder_path = ASSETS_DIR / "imagenes" / "escenarios" / char_name
        if folder_path.exists():
            files = sorted([f.name for f in folder_path.glob("fondo_*.png")])
            for f in files:
                img = pygame.image.load(str(folder_path / f)).convert_alpha()
                frames.append(pygame.transform.scale(img, (self.original_width, self.original_height)))
        return frames

    def draw_text(self, text, font, color, x, y, center=False, surface=None):
        if surface is None: surface = self.game_canvas
        img = font.render(text, True, color)
        rect = img.get_rect()
        if center: rect.center = (x, y)
        else: rect.topleft = (x, y)
        surface.blit(img, rect)

    def draw_health_bar(self, health, x, y, right_to_left=True):
        ratio = max(0, health / 100)
        max_width = 400
        current_width = max_width * ratio
        
        pygame.draw.rect(self.game_canvas, (255,255,255), (x - 5, y - 5, max_width + 10, 35))
        pygame.draw.rect(self.game_canvas, (255,0,0), (x, y, max_width, 25))
        
        if right_to_left:
            pygame.draw.rect(self.game_canvas, (255,255,0), (x, y, current_width, 25))
        else:
            empty_space = max_width - current_width
            pygame.draw.rect(self.game_canvas, (255,255,0), (x + empty_space, y, current_width, 25))

    def load_all_assets(self):
        bg_s_path = self.get_asset_path("imagenes/escenarios/seleccion.png")
        if os.path.exists(bg_s_path):
            self.background_select = pygame.transform.scale(pygame.image.load(bg_s_path).convert(), (self.original_width, self.original_height))
        
        bg_m_path = self.get_asset_path("imagenes/escenarios/menu.jpg")
        if os.path.exists(bg_m_path):
             self.background_menu = pygame.transform.scale(pygame.image.load(bg_m_path).convert(), (self.original_width, self.original_height))

        for name, info in self.world_map_data.items():
            icon_p = self.get_asset_path(f"imagenes/icono/icons/icon_{name}.png")
            port_p = self.get_asset_path(f"imagenes/icono/bigimagenes/big_{name}.png")
            name_p = self.get_asset_path(f"imagenes/icono/nombres/{name}.png")
            
            if os.path.exists(icon_p):
                self.icons[name] = pygame.transform.scale(pygame.image.load(icon_p).convert_alpha(), (self.CELL_SIZE, self.CELL_SIZE))
            if os.path.exists(port_p):
                self.portraits[name] = pygame.transform.scale(pygame.image.load(port_p).convert_alpha(), (250, 300))
            if os.path.exists(name_p):
                self.name_logos[name] = pygame.image.load(name_p).convert_alpha()
            
            c = info["country"]
            if c not in self.maps_bw:
                path_bw = self.get_asset_path(f"imagenes/icono/mapas/map_{c}.png")
                path_col = self.get_asset_path(f"imagenes/icono/mapas/map_{c}_color.png")
                if os.path.exists(path_bw):
                    self.maps_bw[c] = pygame.transform.scale(pygame.image.load(path_bw).convert_alpha(), (60, 40))
                if os.path.exists(path_col):
                    self.maps_color[c] = pygame.transform.scale(pygame.image.load(path_col).convert_alpha(), (60, 40))

        try:
            ko_path = self.get_asset_path("imagenes/icono/ko.png")
            self.ko_img = pygame.transform.scale(pygame.image.load(ko_path).convert_alpha(), (100, 50))
        except: self.ko_img = None
        
        self.victory_img = pygame.image.load(self.get_asset_path("imagenes/icono/gameover.png")).convert_alpha()
        self.fight_img = pygame.image.load(self.get_asset_path("imagenes/icono/fight.png")).convert_alpha()
        self.timeover_img = pygame.image.load(self.get_asset_path("imagenes/icono/timeover.png")).convert_alpha()
        
        cont_path = self.get_asset_path("imagenes/icono/pushstart.png")
        self.continue_img = pygame.transform.scale(pygame.image.load(cont_path).convert_alpha(), (400, 100))

        path_yellow = ASSETS_DIR / "imagenes/icono/timer"
        path_red = ASSETS_DIR / "imagenes/icono/timer_blue"
        COLOR_ORIGINAL_NUMEROS = (255, 255, 0)

        for i in range(10):
            file_path = path_yellow / f"{i}.png"
            if file_path.exists():
                img = pygame.image.load(str(file_path)).convert_alpha()
                self.timer_sprites_yellow.append(pygame.transform.scale(img, (55, 75)))
            else:
                s = pygame.Surface((55, 75)); s.fill((255,255,0))
                self.timer_sprites_yellow.append(s)
            
            file_path_r = path_red / f"{i}.png"
            if file_path_r.exists():
                img = pygame.image.load(str(file_path_r)).convert_alpha()
                self.timer_sprites_red.append(pygame.transform.scale(img, (55, 75)))
            else:
                self.timer_sprites_red.append(self.swap_color(self.timer_sprites_yellow[-1], COLOR_ORIGINAL_NUMEROS, (255, 30, 30)))

    def start_fight(self):
        self.effects_group.empty()
        self.projectiles_group.empty()
        
        p1_char = self.fighters_grid[self.p1_pos[1]][self.p1_pos[0]]
        p2_char = self.fighters_grid[self.p2_pos[1]][self.p2_pos[0]]
        
        chosen_stage = random.choice([p1_char, p2_char])
        self.background_fight = self.load_stage(chosen_stage)
        self.bg_index = 0
        
        path_s1 = self.get_asset_path(f"imagenes/personajes/{p1_char}/sprites/{p1_char.capitalize()}.png")
        path_s2 = self.get_asset_path(f"imagenes/personajes/{p2_char}/sprites/{p2_char.capitalize()}.png")
        
        sheet1 = pygame.image.load(path_s1).convert_alpha()
        sheet2 = pygame.image.load(path_s2).convert_alpha()
        
        if p1_char == p2_char:
            sheet2 = self.swap_color(sheet2, (255, 255, 255), (100, 200, 255))
        
        self.fighter_1 = Fighter(1, 200, 395, False, self.world_map_data[p1_char]["data"], sheet1, self.world_map_data[p1_char]["steps"], p1_char)
        self.fighter_2 = Fighter(2, 900, 395, True, self.world_map_data[p2_char]["data"], sheet2, self.world_map_data[p2_char]["steps"], p2_char)

        self.fighter_1.update(self.fighter_2, self.effects_group, self.projectiles_group)
        self.fighter_2.update(self.fighter_1, self.effects_group, self.projectiles_group)

        self.play_music(f"sonidos/musica/escenarios/{chosen_stage}.mp3")
        
        self.fight_timer = 90
        self.intro_count = 3
        self.round_over = False
        self.show_fight_img = False
        self.timer_last_update = pygame.time.get_ticks()
        self.last_count_update = pygame.time.get_ticks()
        self.audio_reproducido = False 

    #METODOS DEL SDK
    def start(self, surface: pygame.Surface) -> None:
        super().start(surface)
        pygame.mixer.pre_init(44100, -16, 2, 2048)
        try:
            f_path = self.get_asset_path("fuentes/ARCADEPI.ttf")
            self.score_font = pygame.font.Font(f_path, 80)
            self.count_font = pygame.font.Font(f_path, 80)
        except:
            self.score_font = pygame.font.SysFont("arial", 80)
            self.count_font = pygame.font.SysFont("arial", 80)

        try:
            self.sonido_fight = pygame.mixer.Sound(self.get_asset_path("sonidos/voces/round1_fight.mp3"))
            self.sonido_fight.set_volume(1.0)
        except: self.sonido_fight = None

        self.load_all_assets()
        self.play_music("sonidos/musica/intro.mp3")

    def stop(self) -> None:
        super().stop()
        pygame.mixer.music.stop()

    def handle_events(self, events: list[pygame.event.Event]):
        for event in events:
            #SALTAR INTRO CON ENTER
            if self.game_state == "intro":
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_RETURN or event.key == pygame.K_SPACE):
                    self.game_state = "menu"
                    
            elif self.game_state == "menu":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    self.game_state = "select"
            
            elif self.game_state == "select":
                if event.type == pygame.KEYDOWN:
                    if not self.p1_ready:
                        if event.key == pygame.K_a and self.p1_pos[0] > 0: self.p1_pos[0] -= 1
                        if event.key == pygame.K_d and self.p1_pos[0] < self.COLS - 1: self.p1_pos[0] += 1
                        if event.key == pygame.K_w and self.p1_pos[1] > 0: self.p1_pos[1] -= 1
                        if event.key == pygame.K_s and self.p1_pos[1] < self.ROWS - 1: self.p1_pos[1] += 1
                        if event.key == pygame.K_SPACE: self.p1_ready = True
                    elif event.key == pygame.K_ESCAPE: self.p1_ready = False

                    if not self.p2_ready:
                        if event.key == pygame.K_LEFT and self.p2_pos[0] > 0: self.p2_pos[0] -= 1
                        if event.key == pygame.K_RIGHT and self.p2_pos[0] < self.COLS - 1: self.p2_pos[0] += 1
                        if event.key == pygame.K_UP and self.p2_pos[1] > 0: self.p2_pos[1] -= 1
                        if event.key == pygame.K_DOWN and self.p2_pos[1] < self.ROWS - 1: self.p2_pos[1] += 1
                        if event.key == pygame.K_RETURN: self.p2_ready = True
                    elif event.key == pygame.K_BACKSPACE: self.p2_ready = False

    def update(self, dt: float):
        current_time = pygame.time.get_ticks()

        if self.game_state != self.last_state:
            if self.game_state == "intro": self.play_music("sonidos/musica/intro.mp3")
            elif self.game_state in ["menu", "select"]: self.play_music("sonidos/musica/select.mp3")
            self.last_state = self.game_state

        if self.game_state == "intro":
            pass

        elif self.game_state == "select":
            if self.p1_ready and self.p2_ready:
                self.start_fight()
                self.game_state = "game"

        elif self.game_state == "game":
            if self.fighter_1 and self.fighter_2:
                if self.intro_count > 0:
                    if self.intro_count == 2 and not self.audio_reproducido and self.sonido_fight:
                        self.sonido_fight.play()
                        self.audio_reproducido = True
                    
                    if current_time - self.last_count_update >= 1000:
                        self.intro_count -= 1
                        self.last_count_update = current_time
                    
                    self.fighter_1.update(self.fighter_2, self.effects_group, self.projectiles_group)
                    self.fighter_2.update(self.fighter_1, self.effects_group, self.projectiles_group)
                else:
                    if not self.show_fight_img and not self.round_over:
                        self.show_fight_img = True
                        self.fight_img_timer = current_time

                    if not self.round_over:
                        if current_time - self.timer_last_update >= 1000:
                            self.fight_timer -= 1
                            self.timer_last_update = current_time
                        
                        if self.fight_timer <= 0 or not self.fighter_1.alive or not self.fighter_2.alive:
                            self.round_over = True
                            self.round_over_time = current_time
                            if self.fighter_1.health > self.fighter_2.health:
                                self.score[0] += 1
                                if self.fighter_1.alive: self.fighter_1.won = True
                            elif self.fighter_2.health > self.fighter_1.health:
                                self.score[1] += 1
                                if self.fighter_2.alive: self.fighter_2.won = True

                        self.fighter_1.mover(self.original_width, self.original_height, self.fighter_2, self.round_over, self.camera_x)
                        self.fighter_2.mover(self.original_width, self.original_height, self.fighter_1, self.round_over, self.camera_x)

                    self.fighter_1.update(self.fighter_2, self.effects_group, self.projectiles_group)
                    self.fighter_2.update(self.fighter_1, self.effects_group, self.projectiles_group)

                    for p in self.projectiles_group:
                        target = self.fighter_2 if p.direction == 1 else self.fighter_1
                        p.update(target)
                    
                    self.effects_group.update(self.camera_x)

                    if self.round_over and current_time - self.round_over_time > 3000:
                        if self.score[0] >= 2 or self.score[1] >= 2:
                            self.game_state = "menu"
                            self.p1_ready, self.p2_ready = False, False
                            self.score = [0, 0]
                        else:
                            self.start_fight()

    def render(self, surface: pygame.Surface):
        self.game_canvas.fill((0,0,0))
        current_time = pygame.time.get_ticks()

        if self.game_state == "intro":
            frame_num = int(self.intro_index)
            intro_path = self.get_asset_path(f"imagenes/intro/intro_{frame_num}.jpg")
            if os.path.exists(intro_path):
                img = pygame.image.load(intro_path).convert()
                self.game_canvas.blit(pygame.transform.scale(img, (self.original_width, self.original_height)), (0, 0))
                self.intro_index += 0.45
            else:
                self.game_state = "menu"

        elif self.game_state == "menu":
            self.game_canvas.blit(self.background_menu, (0, 0))
            overlay = pygame.Surface((self.original_width, self.original_height))
            overlay.set_alpha(160); overlay.fill((0,0,0))
            self.game_canvas.blit(overlay, (0,0))
            
            fade_alpha = int((math.sin(current_time * 0.005) + 1) * 127.5)
            self.continue_img.set_alpha(fade_alpha)
            self.game_canvas.blit(self.continue_img, self.continue_img.get_rect(center=(self.original_width // 2, 470)))

        elif self.game_state == "select":
            self.game_canvas.blit(self.background_select, (0,0))
            p1_char = self.fighters_grid[self.p1_pos[1]][self.p1_pos[0]]
            p2_char = self.fighters_grid[self.p2_pos[1]][self.p2_pos[0]]
            
            #DIBUJAR LOGOS DE NOMBRES EN SELECCION
            if p1_char in self.name_logos:
                logo_p1 = pygame.transform.scale(self.name_logos[p1_char], (160, 80))
                self.game_canvas.blit(logo_p1, (50, 40))
                
            if p2_char in self.name_logos:
                logo_p2 = pygame.transform.scale(self.name_logos[p2_char], (160, 80))
                self.game_canvas.blit(logo_p2, (self.original_width - logo_p2.get_width() - 50, 40))

            for name, data in self.world_map_data.items():
                img = self.maps_color.get(data["country"]) if (name in [p1_char, p2_char] and (current_time // 200) % 2 == 0) else self.maps_bw.get(data["country"])
                if img: self.game_canvas.blit(img, data["pos"])

            if not self.p1_ready or (current_time // 100) % 2 == 0:
                self.game_canvas.blit(self.portraits[p1_char], (-5, 305))
            if not self.p2_ready or (current_time // 100) % 2 == 0:
                self.game_canvas.blit(pygame.transform.flip(self.portraits[p2_char], True, False), (self.original_width - 250, 300))
            
            for r in range(self.ROWS):
                for c in range(self.COLS):
                    name = self.fighters_grid[r][c]
                    x, y = self.OFFSET_X + c * self.CELL_SIZE, self.OFFSET_Y + r * self.CELL_SIZE
                    self.game_canvas.blit(self.icons[name], (x, y))
                    pygame.draw.rect(self.game_canvas, (255,255,255), (x, y, self.CELL_SIZE, self.CELL_SIZE), 1)
            
            glow = abs(math.sin(current_time * 0.01)) * 255
            pygame.draw.rect(self.game_canvas, (0, glow, glow) if not self.p1_ready else (255,255,255), 
                            (self.OFFSET_X + self.p1_pos[0] * self.CELL_SIZE, self.OFFSET_Y + self.p1_pos[1] * self.CELL_SIZE, self.CELL_SIZE, self.CELL_SIZE), 6)
            pygame.draw.rect(self.game_canvas, (glow, 0, 0) if not self.p2_ready else (255,255,255), 
                            (self.OFFSET_X + self.p2_pos[0] * self.CELL_SIZE, self.OFFSET_Y + self.p2_pos[1] * self.CELL_SIZE, self.CELL_SIZE, self.CELL_SIZE), 4)

        elif self.game_state == "game":
            if self.fighter_1 and self.fighter_2:
                self.bg_index += 0.12
                if self.bg_index >= len(self.background_fight): self.bg_index = 0
                self.game_canvas.blit(self.background_fight[int(self.bg_index)], (0 - self.camera_x, 0))

                self.draw_health_bar(self.fighter_1.health, 170, 30, False)
                self.draw_health_bar(self.fighter_2.health, 620, 30, True)
                
                #DIBUJAR NOMBRES DE LOS PERSONAJES EN JUEGO
                p1_char_game = self.fighters_grid[self.p1_pos[1]][self.p1_pos[0]]
                p2_char_game = self.fighters_grid[self.p2_pos[1]][self.p2_pos[0]]
                
                if p1_char_game in self.name_logos:
                    logo_p1 = pygame.transform.scale(self.name_logos[p1_char_game], (140, 80))
                    self.game_canvas.blit(logo_p1, (20, 0))
                    
                if p2_char_game in self.name_logos:
                    logo_p2 = pygame.transform.scale(self.name_logos[p2_char_game], (120, 80))
                    self.game_canvas.blit(logo_p2, (self.original_width - 180, 0))
                
                # Cooldown indicadors
                time_now = pygame.time.get_ticks()
                color_p1 = (0, 255, 0) if (time_now - self.fighter_1.last_special_attack >= self.fighter_1.special_cooldown) else (255, 0, 0)
                pygame.draw.circle(self.game_canvas, color_p1, (50, 80), 10)
                pygame.draw.circle(self.game_canvas, (255,255,255), (50, 80), 10, 2)

                color_p2 = (0, 255, 0) if (time_now - self.fighter_2.last_special_attack >= self.fighter_2.special_cooldown) else (255, 0, 0)
                pygame.draw.circle(self.game_canvas, color_p2, (1150, 80), 10)
                pygame.draw.circle(self.game_canvas, (255,255,255), (1150, 80), 10, 2)

                if self.ko_img:
                    ko_rect = self.ko_img.get_rect(center=(self.original_width // 2, 42))
                    self.game_canvas.blit(self.ko_img, ko_rect)
                
                self.draw_text(str(self.score[0]), self.score_font, (255,255,0), self.original_width//2 - 100, 70)
                self.draw_text(str(self.score[1]), self.score_font, (255,255,0), self.original_width//2 + 60, 70)
                
                display_time = max(0, int(self.fight_timer))
                time_str = str(display_time).zfill(2)
                sprites = self.timer_sprites_yellow if display_time > 10 else self.timer_sprites_red
                total_w = sum([sprites[int(c)].get_width() for c in time_str])
                cur_x = (self.original_width // 2) - (total_w // 2)
                for c in time_str:
                    spr = sprites[int(c)]
                    self.game_canvas.blit(spr, (cur_x, 70))
                    cur_x += spr.get_width()

                self.fighter_1.draw(self.game_canvas, self.camera_x)
                self.fighter_2.draw(self.game_canvas, self.camera_x)
                
                for p in self.projectiles_group: p.draw(self.game_canvas, self.camera_x)
                for e in self.effects_group: e.draw(self.game_canvas, self.camera_x)

                if self.intro_count > 0:
                    if self.intro_count < 10: 
                        cnt_img = self.timer_sprites_red[self.intro_count]
                        cnt_img = pygame.transform.scale(cnt_img, (80, 150))
                        cnt_rect = cnt_img.get_rect(center=(self.original_width//2, self.original_height//2))
                        self.game_canvas.blit(cnt_img, cnt_rect)
                
                if self.show_fight_img:
                    elapsed = current_time - self.fight_img_timer
                    if elapsed < 1000:
                        zoom = 2.5 * min(1.0, elapsed / 200)
                        w, h = int(self.fight_img.get_width() * zoom), int(self.fight_img.get_height() * zoom)
                        if w>0 and h>0:
                            bi = pygame.transform.scale(self.fight_img, (w, h))
                            self.game_canvas.blit(bi, bi.get_rect(center=(self.original_width//2, self.original_height//2)))

                if self.round_over:
                    if self.fight_timer <= 0:
                        img = self.timeover_img
                    else:
                        img = self.victory_img
                    big = pygame.transform.scale(img, (img.get_width()*1.5, img.get_height()*1.5))
                    self.game_canvas.blit(big, big.get_rect(center=(self.original_width//2, self.original_height//2)))

        # 2.ESCALAR Y DIBUJAR EN SURFACE DEL SDK
        scaled_surface = pygame.transform.scale(self.game_canvas, (BASE_WIDTH, BASE_HEIGHT))
        surface.blit(scaled_surface, (0, 0))


if not pygame.get_init():
    pygame.init()

metadata = (GameMeta()
            .with_title("Street Fighters 2")
            .with_description("Clásico juego de pelea arcade")
            .with_release_date("10/02/2026")
            .with_group_number(3)
            .add_tag("Pelea")
            .add_author("Keiber Medina y Juan Rodríguez"))

game = StreetFighterGame(metadata)

if __name__ == "__main__":
    game.run_independently()
