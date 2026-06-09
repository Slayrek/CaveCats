# ============================================================
#  item_drop.py — Логіка предметів, що випадають на землю
# ============================================================

import pygame
import math
import random
import os
from src.core.settings import TILE_SIZE, GRAVITY, MAX_FALL_SPEED, BLACK
from src.items.items import get_item_def
from src.world.blocks import BLOCK_DEFS, BLOCK_LAVA, BLOCK_WATER
from src.core.utils import resource_path

class ItemDrop(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, item_id: str, world) -> None:
        super().__init__()
        self.item_id    = item_id
        self.world      = world
        self.size       = TILE_SIZE // 2 # Зазвичай 20x20 пікселів

        self.base_image = self._create_image()
        # Поверхня трохи вища, щоб було місце для анімації "підстрибування"
        self.image      = pygame.Surface((self.size, self.size + 8), pygame.SRCALPHA)
        self.image.blit(self.base_image, (0, 4))
        self.rect       = self.image.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
        
        self.hitbox     = pygame.Rect(0, 0, self.size, self.size)
        self.hitbox.midbottom = self.rect.midbottom

        self.vel_x:     float = random.uniform(-3.0, 3.0)
        self.vel_y:     float = random.uniform(-6.0, -2.0)
        self.pos_x:     float = float(self.hitbox.x)
        self.pos_y:     float = float(self.hitbox.y)
        self.spawn_time: int  = pygame.time.get_ticks()
        self.pickup_delay = 60 # Щоб предмет не підбирався миттєво
        
        # Network sync
        import uuid
        self.net_id = str(uuid.uuid4())
        self.target_x = x
        self.target_y = y

    def _create_image(self) -> pygame.Surface:
        # 1. СПРОБА ЗАВАНТАЖИТИ PNG З ПАПКИ pics/sprites/
        texture_path = resource_path(os.path.join("pics", "sprites", f"{self.item_id}.png"))
        if os.path.exists(texture_path):
            img = pygame.image.load(texture_path).convert_alpha()
            # Масштабуємо текстуру під розмір дропу (20x20)
            return pygame.transform.scale(img, (self.size, self.size))

        # 2. РЕЗЕРВНИЙ ВАРІАНТ: МАЛЮЄМО СТАРИЙ КОЛЬОРОВИЙ КВАДРАТ
        surf     = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        item_def = get_item_def(self.item_id)
        color    = item_def.get("color",        (200, 0, 200))
        border   = item_def.get("border_color", BLACK)
        pygame.draw.rect(surf, color,  (0, 0, self.size, self.size))
        pygame.draw.rect(surf, border, (0, 0, self.size, self.size), 1)
        return surf

    def _get_nearby_solid(self) -> list[pygame.Rect]:
        rects = []
        col = int(self.pos_x // TILE_SIZE)
        row = int(self.pos_y // TILE_SIZE)
        for r in range(max(0, row - 2), min(self.world.rows, row + 3)):
            for c in range(max(0, col - 2), min(self.world.cols, col + 3)):
                if BLOCK_DEFS[self.world.grid[r][c]].get("solid", False):
                    rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects

    def update(self) -> None:
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if self.pickup_delay > 0: self.pickup_delay -= 1
        
        if is_client:
            self.hitbox.centerx += (self.target_x - self.hitbox.centerx) * 0.3
            self.hitbox.centery += (self.target_y - self.hitbox.centery) * 0.3
            self.pos_x = float(self.hitbox.x)
            self.pos_y = float(self.hitbox.y)
            self.rect.midbottom = self.hitbox.midbottom
            
            # Анімація легкого підстрибування на місці
            self.image.fill((0, 0, 0, 0))
            t = (pygame.time.get_ticks() - self.spawn_time) * 0.005
            offset = 4 + int(math.sin(t) * 3) 
            self.image.blit(self.base_image, (0, offset))
            return

        col = int(self.hitbox.centerx // TILE_SIZE)
        row = int(self.hitbox.centery // TILE_SIZE)
        if self.world._in_bounds(row, col):
            if self.world.grid[row][col] == BLOCK_LAVA:
                if self.item_id == "slimeball":
                    if random.random() < 0.5:
                        self.item_id = "magma_clot"
                        self.vel_y = -8.0
                        self.vel_x = random.uniform(-4.0, 4.0)
                        self.pickup_delay = 60
                        self.base_image = self._create_image()
                    else:
                        self.kill()
                elif self.item_id not in ("magma_clot", "lava_fishing_rod", "ruby", "ruby_sword", "ruby_helmet", "ruby_boots", "lavacalibur"):
                    self.kill()
            elif self.world.grid[row][col] == BLOCK_WATER:
                if self.item_id == "ruby":
                    self.item_id = "magnum_opus"
                    self.vel_y = -8.0
                    self.vel_x = random.uniform(-4.0, 4.0)
                    self.pickup_delay = 60
                    self.base_image = self._create_image()
        
        if not self.alive(): return

        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        solid = self._get_nearby_solid()
        
        self.pos_x += self.vel_x
        self.hitbox.x = int(self.pos_x)
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if self.vel_x > 0: self.hitbox.right = tile.left
                elif self.vel_x < 0: self.hitbox.left = tile.right
                self.pos_x = float(self.hitbox.x)
                self.vel_x *= -0.5

        self.pos_y += self.vel_y
        self.hitbox.y = int(self.pos_y)

        on_ground = False
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if self.vel_y > 0:
                    self.hitbox.bottom = tile.top
                    self.pos_y       = float(self.hitbox.y)
                    self.vel_y       = 0.0
                    self.vel_x       *= 0.8
                    on_ground        = True
                elif self.vel_y < 0:
                    self.hitbox.top = tile.bottom
                    self.pos_y    = float(self.hitbox.y)
                    self.vel_y    = 0.0
                    self.vel_x    *= -0.5

        self.rect.midbottom = self.hitbox.midbottom

        # Анімація легкого підстрибування на місці
        self.image.fill((0, 0, 0, 0))
        offset = 4
        if on_ground or self.vel_y == 0.0:
            t = (pygame.time.get_ticks() - self.spawn_time) * 0.005
            offset = 4 + int(math.sin(t) * 3) 
        self.image.blit(self.base_image, (0, offset))