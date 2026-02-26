import pygame
from pathlib import Path

#GESTION DE RUTAS
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

#CLASE PROYECTIL
class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, char_type, player_owner): 
        super().__init__()
        self.speed = 12 * direction
        self.direction = direction
        self.player_owner = player_owner 
        
        self.images = []
        self.frame_index = 0
        self.animation_speed = 60
        self.last_update = pygame.time.get_ticks()
        
        try:
            for i in range(3): 
                #construcción de ruta segura con pathlib
                ruta = ASSETS_DIR / "imagenes" / "personajes" / char_type / "ataques" / f"special_{i}.png"
                
                #convertir ruta a string con str() para pygame
                img = pygame.image.load(str(ruta)).convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * 1.5), int(img.get_height() * 1.5)))
                if direction == -1:
                    img = pygame.transform.flip(img, True, False)
                self.images.append(img)
        except Exception as e:
            # print(f"Error cargando proyectil: {e}") 
            pass 

        if len(self.images) == 0:
            cuadro = pygame.Surface((40, 40))
            cuadro.fill((0, 255, 255)) 
            self.images = [cuadro]

        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self, target):
        self.rect.x += self.speed
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update > self.animation_speed:
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.frame_index = 0
            self.image = self.images[self.frame_index]
            self.last_update = current_time

        if self.rect.right < -200 or self.rect.left > 2200:
            self.kill()

        #LOGICA DE PROTECCION DE DUEÑO 
        if self.player_owner != target.player:
            if self.rect.colliderect(target.rect):
                if not target.hit:
                    target.health -= 15
                    target.hit = True
                    
                    if target.health <= 0:
                        try: target.sonido_death.play()
                        except: pass
                    else:
                        try: target.sonido_hurt.play()
                        except: pass
                    
                    self.kill()

    def draw(self, surface, camera_x):
        surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))


#CLASE FIGHTER
class Fighter:
    def __init__(self, player, x, y, flip, data, sprite_sheet, animation_steps, char_type):
        self.player = player
        self.char_type = char_type 
        self.size = data[0]
        self.image_scale = data[1]
        self.desplazamiento = data[2]
        self.default_facing = data[3]
        
        self.initial_x = x
        self.initial_y = y
        
        self.flip = flip
        self.animation_list = self.cargar_animaciones(sprite_sheet, animation_steps)
        self.accion = 0 
        self.frame_index = 0
        self.image = self.animation_list[self.accion][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        
        self.rect = pygame.Rect(x, y, 80, 180)
        self.vel_y = 0
        
        self.running = False
        self.jump = False
        self.crouch = False
        self.blocking = False
        self.attacking = False
        self.attack_type = 0 
        self.attack_cooldown = 0
        self.damage_applied = False 
        self.hit = False
        self.health = 100
        self.alive = True
        self.won = False
        self.win_repeat_count = 0
        
        self.special_attack_fired = False

        #SISTEMA DE COOLDOWN PARA ATAQUE ESPECIAL
        self.last_special_attack = 0
        self.special_cooldown = 5000 # 5 Segundos

        #Carga de sonidos con rutas seguras
        try:
            p_golpe = ASSETS_DIR / "sonidos" / "personajes" / self.char_type / "golpe.wav"
            p_hurt = ASSETS_DIR / "sonidos" / "personajes" / self.char_type / "hurt.wav"
            p_block = ASSETS_DIR / "sonidos" / "combate" / "block.wav"
            p_special = ASSETS_DIR / "sonidos" / "personajes" / self.char_type / "especial.wav"
            p_death = ASSETS_DIR / "sonidos" / "personajes" / self.char_type / "death.wav"

            self.sonido_golpe = pygame.mixer.Sound(str(p_golpe))
            self.sonido_hurt = pygame.mixer.Sound(str(p_hurt))
            self.sonido_bloqueo = pygame.mixer.Sound(str(p_block))
            self.sonido_especial = pygame.mixer.Sound(str(p_special))
            self.sonido_death = pygame.mixer.Sound(str(p_death))
            
            self.sonido_death.set_volume(20)
            self.sonido_golpe.set_volume(20)
            self.sonido_hurt.set_volume(20)
        except Exception as e:
            # print(f"Error sonidos {self.char_type}: {e}")
            pass

    def cargar_animaciones(self, sprite_sheet, animation_steps):
        animations_list = [] 
        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                temp_img = sprite_sheet.subsurface(x * self.size, y * self.size, self.size, self.size)
                scaled_img = pygame.transform.scale(temp_img, (int(self.size * self.image_scale), int(self.size * self.image_scale)))
                temp_img_list.append(scaled_img)
            animations_list.append(temp_img_list)
        return animations_list
    
    def mover(self, screen_width, screen_height, target, round_over, camera_x):
        speed = 10
        gravedad = 2
        dx = 0
        dy = 0
        self.running = False
        self.blocking = False
        
        if self.alive and not self.won:
            if target.rect.centerx > self.rect.centerx:
                self.flip = False if self.default_facing == "right" else True
            else:
                self.flip = True if self.default_facing == "right" else False

        key = pygame.key.get_pressed()
        
        current_time = pygame.time.get_ticks()

        if not self.attacking and self.alive and not round_over:
            if self.player == 1:
                if key[pygame.K_s]: self.crouch = True
                else: self.crouch = False
                if key[pygame.K_f]: self.blocking = True
                
                if not self.crouch and not self.blocking:
                    if key[pygame.K_a]:
                        dx = -speed
                        self.running = True
                    if key[pygame.K_d]:
                        dx = speed
                        self.running = True
                    if key[pygame.K_w] and not self.jump:
                        self.vel_y = -30
                        self.jump = True
                
                if not self.crouch:
                    if key[pygame.K_r]: 
                        self.attack_type = 1
                        self.attack()
                    elif key[pygame.K_t]: 
                        self.attack_type = 2
                        self.attack()
                    elif key[pygame.K_y]: 
                        if current_time - self.last_special_attack >= self.special_cooldown:
                            self.attack_type = 3 
                            self.attack()
                            self.last_special_attack = current_time 

            if self.player == 2:
                if key[pygame.K_DOWN]: self.crouch = True
                else: self.crouch = False
                if key[pygame.K_p]: self.blocking = True
                
                if not self.crouch and not self.blocking:
                    if key[pygame.K_LEFT]:
                        dx = -speed
                        self.running = True
                    if key[pygame.K_RIGHT]:
                        dx = speed
                        self.running = True
                    if key[pygame.K_UP] and not self.jump:
                        self.vel_y = -30
                        self.jump = True
                
                if not self.crouch:
                    if key[pygame.K_k]: 
                        self.attack_type = 1
                        self.attack()
                    elif key[pygame.K_l]:
                        self.attack_type = 2
                        self.attack()
                    elif key[pygame.K_o]: 
                        if current_time - self.last_special_attack >= self.special_cooldown:
                            self.attack_type = 3
                            self.attack()
                            self.last_special_attack = current_time

        self.vel_y += gravedad  
        dy += self.vel_y

        if self.rect.left + dx < 0: dx = -self.rect.left
        if self.rect.right + dx > screen_width: dx = screen_width - self.rect.right 
        if self.rect.bottom + dy > screen_height - 25:
            self.vel_y = 0
            self.jump = False
            dy = screen_height - 25 - self.rect.bottom

        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        self.rect.x += dx
        self.rect.y += dy

    def aplicar_dano(self, target, cantidad):
        if target.blocking:
            target.health -= cantidad // 5
            try: self.sonido_bloqueo.play()
            except: pass
        else:
            target.health -= cantidad
            target.hit = True
            
            if target.health <= 0:
                try: target.sonido_death.play()
                except: pass
            else:
                try:
                    self.sonido_golpe.play()
                    target.sonido_hurt.play()
                except: pass

    def gestionar_golpe_fisico(self, target, dano):
        if self.rect.colliderect(target.rect):
            if not self.damage_applied:
                self.aplicar_dano(target, dano)
                self.damage_applied = True    

    def attack(self):
        if self.attack_cooldown == 0:
            self.attacking = True
            self.damage_applied = False
            self.special_attack_fired = False 
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def update_accion(self, new_action):
        if new_action != self.accion:
            self.accion = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def update(self, target, effects_group, projectiles_group):
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_accion(6) 
        elif self.won:
            self.update_accion(9) 
        elif self.hit:
            self.update_accion(5) 
        elif self.blocking:
            self.update_accion(8) 
        elif self.attacking:
            if self.attack_type == 1: self.update_accion(3) 
            elif self.attack_type == 2: self.update_accion(4)
            elif self.attack_type == 3: self.update_accion(10) 
        elif self.jump:
            self.update_accion(2) 
        elif self.crouch:
            self.update_accion(7) 
        elif self.running:
            self.update_accion(1) 
        else:
            self.update_accion(0) 

        animation_cooldown = 100
        self.image = self.animation_list[self.accion][self.frame_index]
        
        if self.attacking:
            if self.attack_type == 3:
                
                # ZONERS (Proyectiles)
                if self.char_type in ["ryu", "ken", "dhalsim", "guile"]:
                    # Disparar en frame 2 para coordinar con animacin
                    if self.frame_index == 2 and not self.special_attack_fired:
                        
                        if target.rect.centerx > self.rect.centerx:
                            direction = 1  
                        else:
                            direction = -1 
                        
                        spawn_x = self.rect.centerx + (0.7 * self.rect.width * direction)
                        spawn_y = self.rect.centery - 10
                        
                        projectile = Projectile(spawn_x, spawn_y, direction, self.char_type, self.player)
                        projectiles_group.add(projectile)
                        
                        self.special_attack_fired = True
                        try: self.sonido_especial.play()
                        except: pass

                # RUSHERS (Fisicos)
                elif self.char_type in ["honda", "blanka", "chunli"]:
                    # 1.dejar de avanzar si ya conectaron el golpe
                    if not self.damage_applied: 
                        velocidad_especial = 15
                        if self.flip: self.rect.x -= velocidad_especial
                        else: self.rect.x += velocidad_especial
                        
                        # 2.limite de pantalla manual forzado
                        if self.rect.left < 0: self.rect.left = 0
                        if self.rect.right > 1200: self.rect.right = 1200
                        
                        self.gestionar_golpe_fisico(target, 20)

                # GRAPPLERS (Agarres/area)
                elif self.char_type == "zangief":
                    area_rect = pygame.Rect(self.rect.x - 40, self.rect.y, self.rect.width + 80, self.rect.height)
                    if area_rect.colliderect(target.rect):
                         if not self.damage_applied:
                             self.aplicar_dano(target, 25)
                             self.damage_applied = True

            elif not self.damage_applied:
                if self.frame_index == 2: 
                    ancho_ataque = 120
                    alto_ataque = 80
                    mirando_a_la_derecha = (target.rect.centerx > self.rect.centerx)
                    ataque_x = self.rect.centerx if mirando_a_la_derecha else self.rect.centerx - ancho_ataque
                    attacking_rect = pygame.Rect(ataque_x, self.rect.y + 30, ancho_ataque, alto_ataque)

                    if attacking_rect.colliderect(target.rect):
                        self.aplicar_dano(target, 10)
                        self.damage_applied = True

        if pygame.time.get_ticks() - self.update_time > animation_cooldown:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
            
        if self.frame_index >= len(self.animation_list[self.accion]):
            if self.won:
                self.win_repeat_count += 1
                if self.win_repeat_count < 2: self.frame_index = 0
                else: self.frame_index = len(self.animation_list[self.accion]) - 1
            elif not self.alive:
                self.frame_index = len(self.animation_list[self.accion]) - 1
            else:
                self.frame_index = 0
                if self.attacking:
                    self.attacking = False
                    self.damage_applied = False
                    self.attack_cooldown = 20 
                if self.accion == 5:
                    self.hit = False

    def draw(self, surface, camera_x):
        img = pygame.transform.flip(self.image, self.flip, False)
        ajuste_x = self.desplazamiento[0] * self.image_scale
        ajuste_y = self.desplazamiento[1] * self.image_scale
        
        pos_x = self.rect.x - ajuste_x
        if self.flip:
            pos_x = self.rect.x - (img.get_width() - self.rect.width - ajuste_x)

        surface.blit(img, (pos_x - camera_x, self.rect.y - ajuste_y))