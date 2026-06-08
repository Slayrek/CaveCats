# ============================================================
#  entities.py — ігрові сутності: Cat
# ============================================================

import pygame
import math
import os
from src.core import audio 
import random
from src.core.settings import *
from src.items.items import get_item_def
from src.world.blocks import BLOCK_DEFS, BLOCK_CHEST, BLOCK_DIRT, BLOCK_GRASS, BLOCK_LADDER, BLOCK_WATER, BLOCK_LAVA, BLOCK_PLATFORM
from src.items.inventory import Inventory
from src.core.utils import resource_path

# --- НОВИЙ ІМПОРТ ---
from src.entities.item_drop import ItemDrop

class Cat(pygame.sprite.Sprite):
    _base_cat_img = None 

    def __init__(
        self,
        x: int,
        y: int,
        world,
        drops_group: pygame.sprite.Group,
        inventory,
        chest_manager,
    ) -> None:
        super().__init__()
        self.world        = world
        self.drops_group  = drops_group
        self.inventory    = inventory
        self.chest_manager = chest_manager

        self.facing_right = True
        self.attack_cooldown: int = 0
        self.step_timer = 0 
        
        self.hitbox = pygame.Rect(0, 0, TILE_SIZE // 2, TILE_SIZE - 4)
        self.hitbox.midbottom = (x + TILE_SIZE // 2, y + TILE_SIZE)

        self.spawn_x = x
        self.spawn_y = y
        self.active_hook = None

        self._cached_tool = None 
        self._cached_armor = None 
        self._cached_boots = None
        self.active_potion = None
        self.potion_timer = 0
        self._update_sprites()
        self.image = self.image_right
        
        self.rect = self.image.get_rect()
        self._align_rect()

        self.vel_y:    float = 0.0
        self.on_ground: bool = False
        
        self.noclip = False
        self.custom_speed = None
        
        self.max_hp = 20
        self.hp = 20
        self.max_armor = 20
        self.dead = False
        
        if self.world.config.get("hardcore"):
            self.max_hp = 10
            self.hp = 10
        
        self.invuln_timer = 0
        self.knockback_x = 0.0

    def apply_potion(self, effect: str):
        self.active_potion = effect
        self.potion_timer = FPS * 60 

    @property
    def armor(self) -> int:
        armor_id = self.inventory.armor_slot["id"]
        if armor_id:
            return get_item_def(armor_id).get("armor_value", 0)
        return 0

    @property
    def speed(self) -> float:
        if self.custom_speed is not None:
            return self.custom_speed
        boots_id = getattr(self.inventory, "boots_slot", {}).get("id")
        boost = 0.0
        if boots_id:
            boost = get_item_def(boots_id).get("speed_boost", 0.0)
        return PLAYER_SPEED + boost
        
    @speed.setter
    def speed(self, value: float):
        self.custom_speed = value

    def take_damage(self, amount: int, source_x: int):
        if self.invuln_timer <= 0 and not self.noclip:
            reduction = int(amount * (self.armor / 24.0)) 
            final_damage = max(1, amount - reduction)
            
            self.hp -= final_damage
            if self.hp <= 0:
                if self.world.config.get("hardcore"):
                    self.dead = True
                    return

                self.hp = self.max_hp
                self.hitbox.centerx = self.spawn_x
                self.hitbox.centery = self.spawn_y
                self.vel_y = 0
                self.knockback_x = 0
                if self.active_hook:
                    self.active_hook.kill()
                    self.active_hook = None
                audio.play_sfx("cat_damage") 
                return

            self.invuln_timer = FPS 
            audio.play_sfx("cat_damage") 
            
            self.vel_y = -6
            if source_x > self.hitbox.centerx:
                self.knockback_x = -8.0
            else:
                self.knockback_x = 8.0

    def _update_sprites(self):
        self.image_right        = self._make_sprite(attacking=False, tool_id=self._cached_tool, armor_id=self._cached_armor, boots_id=self._cached_boots)
        self.image_left         = pygame.transform.flip(self.image_right, True, False)
        self.image_right_attack = self._make_sprite(attacking=True, tool_id=self._cached_tool, armor_id=self._cached_armor, boots_id=self._cached_boots)
        self.image_left_attack  = pygame.transform.flip(self.image_right_attack, True, False)

    def _make_sprite(self, attacking: bool, tool_id: str | None, armor_id: str | None, boots_id: str | None) -> pygame.Surface:
        surf_size = max(int(TILE_SIZE * 8), 300) 
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        self._draw_cat(surf, surf_size, attacking, tool_id, armor_id, boots_id)
        return surf

    def _get_cat_image(self) -> pygame.Surface:
        if not Cat._base_cat_img:
            path = resource_path(os.path.join("pics", "cat.png"))
            if os.path.exists(path):
                Cat._base_cat_img = pygame.image.load(path).convert_alpha()
            else:
                temp_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
                pygame.draw.circle(temp_surf, WHITE, (32, 32), 20)
                Cat._base_cat_img = temp_surf
        return Cat._base_cat_img

    def _draw_cat(self, surface: pygame.Surface, surf_size: int, attacking: bool, tool_id: str | None, armor_id: str | None, boots_id: str | None) -> None:
        cx = surf_size // 2
        cy = surf_size // 2

        base_cat = self._get_cat_image()
        cat_w, cat_h = base_cat.get_size()
        
        if self.active_potion:
            tint = base_cat.copy()
            if self.active_potion == "strength": tint.fill((255, 100, 100), special_flags=pygame.BLEND_RGBA_MULT)
            elif self.active_potion == "fire_res": tint.fill((255, 150, 50), special_flags=pygame.BLEND_RGBA_MULT)
            elif self.active_potion == "jump": tint.fill((100, 255, 100), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(tint, (cx - cat_w // 2, cy - cat_h // 2 + 4))
        else:
            surface.blit(base_cat, (cx - cat_w // 2, cy - cat_h // 2 + 4))
        
        if armor_id and "helmet" in armor_id:
            h_color = get_item_def(armor_id).get("helmet_color", (200, 200, 200))
            pygame.draw.rect(surface, h_color, (cx - 11, cy - 15, 22, 10))
            pygame.draw.rect(surface, h_color, (cx - 14, cy - 16, 6, 8))
            pygame.draw.rect(surface, h_color, (cx + 8,  cy - 16, 6, 8))

        paw_x, paw_y = cx + TILE_SIZE // 2 - 2, cy + 6
        hand_x, hand_y = cx + TILE_SIZE // 2 - 6, cy + 2

        # --- МАЛЮЄМО ІНСТРУМЕНТ (ТВЕРДІ ТЕКСТУРИ) ---
        if tool_id:
            tool_path = resource_path(os.path.join("pics", "sprites", f"{tool_id}.png"))
            tool_img = None
            if os.path.exists(tool_path):
                tool_img = pygame.image.load(tool_path).convert_alpha()
            elif tool_id in Inventory.PROCEDURAL_TEXTURES:
                if tool_id not in Inventory._icon_cache or Inventory._icon_cache[tool_id] is None:
                    Inventory._icon_cache[tool_id] = Inventory._render_pixel_art(Inventory.PROCEDURAL_TEXTURES[tool_id], 40)
                tool_img = Inventory._icon_cache[tool_id]

            if tool_img:
                tool_img = pygame.transform.scale(tool_img, (32, 32))
                
                # По замовчуванню текстура лука дивиться вліво, а котик дивиться вправо, тому віддзеркалюємо
                # Removed bow flip as it made it render backwards
                if attacking:
                    rotated = pygame.transform.rotate(tool_img, -45)
                    surface.blit(rotated, (hand_x, hand_y - 10))
                else:
                    rotated = pygame.transform.rotate(tool_img, 0)
                    surface.blit(rotated, (hand_x - 5, hand_y - 20))
            else:
                # Резервний старий код лініями (якщо картинки нема)
                item_def = get_item_def(tool_id)
                t_color = item_def.get("tool_color", (200, 200, 200))
                
                if tool_id == "OVERPOWERED_SWORD666":
                    t = pygame.time.get_ticks() * 0.005
                    t_color = (int(127 + 127*math.sin(t)), int(127 + 127*math.sin(t+2)), int(127 + 127*math.sin(t+4)))

                if "pickaxe" in tool_id:
                    if attacking:
                        pygame.draw.line(surface, (120, 70, 40), (hand_x, hand_y), (hand_x+14, hand_y+14), 3)
                        pygame.draw.line(surface, t_color, (hand_x-2, hand_y+22), (hand_x+22, hand_y-2), 4)
                    else:
                        pygame.draw.line(surface, (120, 70, 40), (hand_x, hand_y), (hand_x+14, hand_y-14), 3)
                        pygame.draw.line(surface, t_color, (hand_x+7, hand_y-30), (hand_x+30, hand_y-7), 4)
                elif "sword" in tool_id or tool_id == "OVERPOWERED_SWORD666":
                    if attacking:
                        pygame.draw.line(surface, (120, 70, 40), (hand_x, hand_y), (hand_x+12, hand_y+12), 3)
                        pygame.draw.line(surface, t_color, (hand_x+12, hand_y+12), (hand_x+36, hand_y+36), 5)
                        pygame.draw.line(surface, (80, 80, 80), (hand_x+8, hand_y+16), (hand_x+16, hand_y+8), 3)
                    else:
                        pygame.draw.line(surface, (120, 70, 40), (hand_x, hand_y), (hand_x+12, hand_y-12), 3)
                        pygame.draw.line(surface, t_color, (hand_x+12, hand_y-12), (hand_x+36, hand_y-36), 5)
                        pygame.draw.line(surface, (80, 80, 80), (hand_x+8, hand_y-16), (hand_x+16, hand_y-8), 3)

        boots_color = WHITE
        if boots_id:
            boots_color = get_item_def(boots_id).get("color", WHITE)
            
        pygame.draw.circle(surface, boots_color, (paw_x, paw_y), 4)
        pygame.draw.circle(surface, (200, 200, 200), (paw_x, paw_y), 4, 1)

    def _align_rect(self):
        self.rect.centerx = self.hitbox.centerx
        cy = self.image.get_height() // 2
        feet_bottom_y = cy + 19
        self.rect.y = self.hitbox.bottom - feet_bottom_y

    def _get_nearby_solid(self) -> list[pygame.Rect]:
        rects = []
        col = self.hitbox.centerx // TILE_SIZE
        row = self.hitbox.centery // TILE_SIZE
        for r in range(max(0, row - 2), min(self.world.rows, row + 3)):
            for c in range(max(0, col - 2), min(self.world.cols, col + 3)):
                if BLOCK_DEFS[self.world.grid[r][c]].get("solid", False):
                    rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects

    def _get_nearby_ladders(self) -> list[pygame.Rect]:
        rects = []
        col = self.hitbox.centerx // TILE_SIZE
        row = self.hitbox.centery // TILE_SIZE
        for r in range(max(0, row - 2), min(self.world.rows, row + 3)):
            for c in range(max(0, col - 2), min(self.world.cols, col + 3)):
                if self.world.grid[r][c] in (BLOCK_LADDER, BLOCK_PLATFORM):
                    rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects

    def update(self, touch_ctrl=None) -> None:
        if self.invuln_timer > 0: self.invuln_timer -= 1
        
        if self.potion_timer > 0:
            self.potion_timer -= 1
            if self.potion_timer <= 0:
                self.active_potion = None
                self._update_sprites() # Reset tint
        
        if abs(self.knockback_x) > 0.5: self.knockback_x *= 0.8
        else: self.knockback_x = 0

        current_item = self.inventory.get_selected_slot()["id"]
        current_armor = self.inventory.armor_slot["id"]
        current_boots = getattr(self.inventory, "boots_slot", {}).get("id")
        if current_item == "OVERPOWERED_SWORD666" or current_item != self._cached_tool or current_armor != self._cached_armor or current_boots != self._cached_boots or (self.potion_timer == FPS * 60):
            self._cached_tool = current_item
            self._cached_armor = current_armor
            self._cached_boots = current_boots
            self._update_sprites()

        keys = pygame.key.get_pressed()
        dx = self.knockback_x
        
        is_moving = False
        if keys[pygame.K_LEFT] or keys[pygame.K_a] or (touch_ctrl and touch_ctrl.left_pressed):
            dx -= self.speed
            self.facing_right = False
            is_moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d] or (touch_ctrl and touch_ctrl.right_pressed):
            dx += self.speed
            self.facing_right = True
            is_moving = True

        if self.active_hook and not self.active_hook.alive():
            self.active_hook = None
            
        if self.active_hook and self.active_hook.stuck:
            hx = self.active_hook.x - self.hitbox.centerx
            hy = self.active_hook.y - self.hitbox.centery
            dist = math.hypot(hx, hy)
            if dist < TILE_SIZE:
                self.active_hook.kill()
                self.active_hook = None
                self.vel_y = -3
            else:
                pull_speed = 15.0
                self.vel_y = (hy / dist) * pull_speed
                dx += (hx / dist) * pull_speed
                
            if keys[pygame.K_SPACE] or (touch_ctrl and touch_ctrl.jump_pressed):
                if self.active_hook:
                    self.active_hook.kill()
                    self.active_hook = None
                    self.vel_y = -JUMP_POWER

        if self.on_ground and is_moving and not self.noclip:
            self.step_timer += 1
            if self.step_timer > 18: 
                audio.play_sfx("step")
                self.step_timer = 0
        else:
            self.step_timer = 18 

        if self.noclip:
            self.vel_y = 0
            if keys[pygame.K_UP] or keys[pygame.K_w]: self.vel_y = -self.speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]: self.vel_y = self.speed
                
            self.hitbox.x += int(dx)
            self.hitbox.y += int(self.vel_y)
            
            if self.attack_cooldown > 0: self.attack_cooldown -= 1
            attacking_anim = self.attack_cooldown > ATTACK_COOLDOWN // 2
            if self.facing_right: self.image = self.image_right_attack if attacking_anim else self.image_right
            else: self.image = self.image_left_attack if attacking_anim else self.image_left
            
            self.image = self.image.copy()
            self.image.set_alpha(150)
            self._align_rect()
            return 

        jump_pow = JUMP_POWER * 1.5 if self.active_potion == "jump" else JUMP_POWER
        jump_pressed = keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_SPACE] or (touch_ctrl and touch_ctrl.jump_pressed)
        if jump_pressed and self.on_ground:
            self.vel_y = jump_pow
            self.on_ground = False

        ladders = self._get_nearby_ladders()
        on_ladder = any(self.hitbox.colliderect(l) for l in ladders if self.world.grid[l.y // TILE_SIZE][l.x // TILE_SIZE] == BLOCK_LADDER)

        if not (self.active_hook and self.active_hook.stuck):
            if on_ladder:
                up_pressed = keys[pygame.K_UP] or keys[pygame.K_w] or (touch_ctrl and touch_ctrl.jump_pressed)
                down_pressed = keys[pygame.K_DOWN] or keys[pygame.K_s]
                if up_pressed: self.vel_y = -4 
                elif down_pressed: self.vel_y = 4  
                else: self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
            else:
                self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)

        if self.attack_cooldown > 0: self.attack_cooldown -= 1

        attacking_anim = self.attack_cooldown > ATTACK_COOLDOWN // 2
        if self.facing_right: self.image = self.image_right_attack if attacking_anim else self.image_right
        else: self.image = self.image_left_attack if attacking_anim else self.image_left

        if self.invuln_timer > 0 and (self.invuln_timer // 5) % 2 == 0:
            self.image = pygame.Surface((1,1), pygame.SRCALPHA)

        solid = self._get_nearby_solid()

        self.hitbox.x += int(dx)
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if dx > 0: self.hitbox.right = tile.left
                elif dx < 0: self.hitbox.left  = tile.right

        prev_bottom = self.hitbox.bottom 
        self.hitbox.y += int(self.vel_y)
        self.on_ground = False
        
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if self.vel_y > 0:
                    self.hitbox.bottom = tile.top
                    self.vel_y       = 0.0
                    self.on_ground   = True
                elif self.vel_y < 0:
                    self.hitbox.top = tile.bottom
                    self.vel_y    = 0.0

        if self.vel_y >= 0 and not (keys[pygame.K_DOWN] or keys[pygame.K_s]):
            for tile in ladders:
                if self.hitbox.colliderect(tile):
                    if prev_bottom <= tile.top + 4: 
                        self.hitbox.bottom = tile.top
                        self.vel_y       = 0.0
                        self.on_ground   = True

        self._align_rect()

    def can_reach(self, col: int, row: int) -> bool:
        cat_col, cat_row = self.hitbox.centerx // TILE_SIZE, self.hitbox.centery // TILE_SIZE
        return abs(cat_col - col) <= 2 and abs(cat_row - row) <= 2

    def try_break_block(self, col: int, row: int) -> int | None:
        if self.attack_cooldown > 0: return None
        if not self.can_reach(col, row): return None
        if not self.world._in_bounds(row, col): return None

        if self._cached_tool and ("sword" in self._cached_tool or self._cached_tool == "OVERPOWERED_SWORD666"):
            audio.play_sfx("attack")
        elif self._cached_tool and "pickaxe" in self._cached_tool:
            audio.play_sfx("pickaxe")
        else:
            audio.play_sfx("attack") 

        block_id = self.world.grid[row][col]
        if block_id in (BLOCK_DIRT, BLOCK_GRASS): return

        damage = 1 
        if self._cached_tool:
            tool_def = get_item_def(self._cached_tool)
            damage = tool_def.get("damage", 1)

        broken_id = self.world.hit_block(col, row, damage)
        if broken_id:
            audio.play_sfx("block_break") 
            drop = ItemDrop(col * TILE_SIZE, row * TILE_SIZE, broken_id, self.world)
            self.drops_group.add(drop)
            if block_id == BLOCK_CHEST:
                contents = self.chest_manager.remove_chest(row, col)
                for slot in contents:
                    if slot["id"] and slot["count"] > 0:
                        for _ in range(slot["count"]):
                            c_drop = ItemDrop(col * TILE_SIZE, row * TILE_SIZE, slot["id"], self.world)
                            self.drops_group.add(c_drop)

        self.facing_right = (col * TILE_SIZE + TILE_SIZE // 2 > self.hitbox.centerx)
        self.attack_cooldown = ATTACK_COOLDOWN
        return broken_id

    def try_place_block(self, col: int, row: int) -> bool:
        if self.attack_cooldown > 0: return False
        if not self.can_reach(col, row): return False
        if not self.world._in_bounds(row, col): return False

        item_id, block_id = self.inventory.get_selected_item_place_info()
        if item_id is None or block_id is None: return False

        block_rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        if BLOCK_DEFS[block_id].get("solid", False) and self.hitbox.colliderect(block_rect): return False

        if self.inventory.consume_item(item_id):
            if self.world.place_block(col, row, block_id):
                audio.play_sfx("block_place") 
                self.facing_right = (col * TILE_SIZE + TILE_SIZE // 2 > self.hitbox.centerx)
                self.attack_cooldown = ATTACK_COOLDOWN
                return True
            else:
                self.inventory.add_item(item_id)
        return False

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def try_fish(self, col: int, row: int) -> str | None:
        if self.attack_cooldown > 0: return None
        cat_col, cat_row = self.hitbox.centerx // TILE_SIZE, self.hitbox.centery // TILE_SIZE
        if abs(cat_col - col) > 3 or abs(cat_row - row) > 3: return None
        if not self.world._in_bounds(row, col): return None
        
        sel_id = self.inventory.get_selected_slot()["id"]
        
        if self.world.grid[row][col] == BLOCK_WATER:
            if random.random() < 0.2:
                drop = ItemDrop(col * TILE_SIZE, (row - 1) * TILE_SIZE, "raw_fish", self.world)
                drop.vel_y = -7.0 
                if col * TILE_SIZE > self.hitbox.centerx: drop.vel_x = -3.0
                else: drop.vel_x = 3.0
                self.drops_group.add(drop)
            self.facing_right = (col * TILE_SIZE + TILE_SIZE // 2 > self.hitbox.centerx)
            self.attack_cooldown = int(ATTACK_COOLDOWN * 1.5)
            return "water_fish" if random.random() < 0.2 else None
            
        elif self.world.grid[row][col] == BLOCK_LAVA:
            if sel_id == "lava_fishing_rod":
                if random.random() < 0.2:
                    chance = random.random()
                    if chance < 0.01: item_res = "lavacalibur"
                    elif chance < 0.20: item_res = "magma_clot"
                    elif chance < 0.50: item_res = "coal"
                    else: item_res = "stone"
                    
                    drop = ItemDrop(col * TILE_SIZE, (row - 1) * TILE_SIZE, item_res, self.world)
                    drop.vel_y = -7.0 
                    if col * TILE_SIZE > self.hitbox.centerx: drop.vel_x = -3.0
                    else: drop.vel_x = 3.0
                    self.drops_group.add(drop)
                self.facing_right = (col * TILE_SIZE + TILE_SIZE // 2 > self.hitbox.centerx)
                self.attack_cooldown = int(ATTACK_COOLDOWN * 1.5)
                return "lava_fish" if item_res else None
        return None

    @property
    def tile_pos(self) -> tuple[int, int]:
        return self.hitbox.centerx // TILE_SIZE, self.hitbox.centery // TILE_SIZE

class OtherPlayer(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((64, 64), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.target_x = x
        self.target_y = y
        self.facing_right = True
        self.tool_id = None
        self.armor_id = None
        self.boots_id = None
        self.attacking = False
        self.active_potion = None
        self.hp = 100
        self.max_hp = 100
        self._base_cat_img = None
        
    def _get_cat_image(self):
        if self._base_cat_img is None:
            from src.core.settings import WHITE
            from src.core.utils import resource_path
            cat_path = resource_path(os.path.join("pics", "cat.png"))
            if os.path.exists(cat_path):
                img = pygame.image.load(cat_path).convert_alpha()
                self._base_cat_img = pygame.transform.scale(img, (64, 64))
            else:
                temp_surf = pygame.Surface((64, 64), pygame.SRCALPHA)
                pygame.draw.circle(temp_surf, WHITE, (32, 32), 20)
                self._base_cat_img = temp_surf
        return self._base_cat_img
        
    def update(self, *args, **kwargs):
        from src.core.settings import TILE_SIZE, WHITE
        from src.items.items import get_item_def
        from src.core.utils import resource_path
        
        self.rect.centerx += (self.target_x - self.rect.centerx) * 0.3
        self.rect.centery += (self.target_y - self.rect.centery) * 0.3
        self.image.fill((0, 0, 0, 0))
        cx, cy = 32, 32
        base_cat = self._get_cat_image()
        cat_w, cat_h = base_cat.get_size()
        self.image.blit(base_cat, (cx - cat_w // 2, cy - cat_h // 2 + 4))
        paw_x, paw_y = cx + TILE_SIZE // 2 - 2, cy + 6
        hand_x, hand_y = cx + TILE_SIZE // 2 - 6, cy + 2

        if self.tool_id:
            tool_path = resource_path(os.path.join("pics", "sprites", f"{self.tool_id}.png"))
            tool_img = None
            if os.path.exists(tool_path):
                tool_img = pygame.image.load(tool_path).convert_alpha()
            if tool_img:
                tool_img = pygame.transform.scale(tool_img, (32, 32))
                # Removed bow flip
                if self.attacking:
                    rotated = pygame.transform.rotate(tool_img, -45)
                    self.image.blit(rotated, (hand_x, hand_y - 10))
                else:
                    rotated = pygame.transform.rotate(tool_img, 0)
                    self.image.blit(rotated, (hand_x - 5, hand_y - 20))
                    
        boots_color = WHITE
        if self.boots_id:
            boots_color = get_item_def(self.boots_id).get("color", WHITE)
        pygame.draw.circle(self.image, boots_color, (paw_x, paw_y), 4)
        pygame.draw.circle(self.image, (200, 200, 200), (paw_x, paw_y), 4, 1)
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
        font = pygame.font.SysFont("arial", 12)
        name_surf = font.render(getattr(self, "name", "Player"), True, WHITE)
        name_rect = name_surf.get_rect(center=(cx, cy - 20))
        self.image.blit(name_surf, name_rect)

