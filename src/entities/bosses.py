# ============================================================
#  bosses.py — Боси та їхня логіка
# ============================================================

import pygame
import random
from src.core import audio 
from src.core.settings import TILE_SIZE, GRAVITY, MAX_FALL_SPEED

# ВИПРАВЛЕНО ОПЕЧАТКУ ТУТ:
from src.world.blocks import BLOCK_DEFS
from src.entities.item_drop import ItemDrop

class Gargoyle(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, world, drops_group, projectiles_group=None) -> None:
        super().__init__()
        self.world = world
        self.drops_group = drops_group
        self.spawn_pos = (x, y)
        self.projectiles_group = projectiles_group
        self.damage = 40
        
        self.size = TILE_SIZE * 2
        
        self.image_normal = self._create_image(hurt=False)
        self.image_hurt   = self._create_image(hurt=True)
        self.image = self.image_normal
        
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hitbox = pygame.Rect(0, 0, self.size - 8, self.size - 4)
        self.hitbox.midbottom = self.rect.midbottom

        self.vel_y: float = 0.0
        self.vel_x: float = 0.0
        
        self.max_hp = 550
        self.hp = 550
        self.damage = 10 
        self.facing_right = False
        self.hurt_timer = 0
        
        # Network sync
        import uuid
        self.net_id = str(uuid.uuid4())
        self.target_x = x
        self.target_y = y

    def _create_image(self, hurt: bool) -> pygame.Surface:
        surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        cx, cy = self.size // 2, self.size // 2
        
        body_color = (200, 50, 50) if hurt else (60, 60, 60)
        head_color = (255, 100, 100) if hurt else (70, 70, 70)
        wing_color = (150, 40, 40) if hurt else (40, 40, 40)
        
        pygame.draw.polygon(surf, wing_color, [(cx - 15, cy), (cx - 35, cy - 20), (cx - 10, cy + 10)])
        pygame.draw.polygon(surf, wing_color, [(cx + 15, cy), (cx + 35, cy - 20), (cx + 10, cy + 10)])
        
        pygame.draw.rect(surf, body_color, (cx - 20, cy - 10, 40, 30), border_radius=10)
        pygame.draw.circle(surf, head_color, (cx, cy - 20), 16)
        
        pygame.draw.polygon(surf, body_color, [(cx - 10, cy - 32), (cx - 16, cy - 45), (cx - 2, cy - 34)])
        pygame.draw.polygon(surf, body_color, [(cx + 10, cy - 32), (cx + 16, cy - 45), (cx + 2, cy - 34)])
        
        pygame.draw.circle(surf, (255, 0, 0), (cx - 6, cy - 22), 4)
        pygame.draw.circle(surf, (255, 0, 0), (cx + 6, cy - 22), 4)
        
        pygame.draw.circle(surf, head_color, (cx - 12, cy + 20), 8)
        pygame.draw.circle(surf, head_color, (cx + 12, cy + 20), 8)
        
        return surf

    def take_damage(self, amount: int, source_x: int):
        # ВИДАЛЕНО ЗАЙВИЙ ІМПОРТ ЗВІДСИ
        self.hp -= amount
        self.hurt_timer = 15 
        audio.play_sfx("gargoyle_damage")
        
        self.vel_y = -3
        if source_x > self.hitbox.centerx:
            self.vel_x = -3.0
        else:
            self.vel_x = 3.0
            
        if self.hp <= 0:
            for _ in range(random.randint(3, 5)):
                drop = ItemDrop(self.hitbox.x, self.hitbox.y, "ruby", self.world)
                drop.vel_x = random.uniform(-4.0, 4.0)
                drop.vel_y = random.uniform(-6.0, -3.0)
                self.drops_group.add(drop)
            self.kill()
            return True 
        return False

    def _get_nearby_solid(self) -> list[pygame.Rect]:
        rects = []
        col, row = self.hitbox.centerx // TILE_SIZE, self.hitbox.centery // TILE_SIZE
        for r in range(max(0, row - 3), min(self.world.rows, row + 4)):
            for c in range(max(0, col - 3), min(self.world.cols, col + 4)):
                if BLOCK_DEFS[self.world.grid[r][c]].get("solid", False):
                    rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects

    def update(self, cat) -> None:
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            self.image = self.image_hurt
        else:
            self.image = pygame.transform.flip(self.image_normal, not self.facing_right, False)

        if is_client:
            self.hitbox.centerx += (self.target_x - self.hitbox.centerx) * 0.3
            self.hitbox.centery += (self.target_y - self.hitbox.centery) * 0.3
            self.rect.midbottom = self.hitbox.midbottom
            return

        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        
        dist_x = cat.hitbox.centerx - self.hitbox.centerx
        dist_y = cat.hitbox.centery - self.hitbox.centery
        
        if abs(dist_x) < TILE_SIZE * 12 and abs(dist_y) < TILE_SIZE * 8:
            if dist_x > 10:
                self.vel_x = 2.0
                self.facing_right = True
            elif dist_x < -10:
                self.vel_x = -2.0
                self.facing_right = False
        else:
            if abs(self.vel_x) > 0.5: self.vel_x *= 0.8
            else: self.vel_x = 0

        solid = self._get_nearby_solid()
        self.hitbox.x += int(self.vel_x)
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if self.vel_x > 0: self.hitbox.right = tile.left
                elif self.vel_x < 0: self.hitbox.left = tile.right
                
                if self.on_ground: self.vel_y = -5

        self.hitbox.y += int(self.vel_y)
        self.on_ground = False
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if self.vel_y > 0:
                    self.hitbox.bottom = tile.top
                    self.vel_y = 0.0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.hitbox.top = tile.bottom
                    self.vel_y = 0.0

        self.rect.midbottom = self.hitbox.midbottom

class AbyssalBehemoth(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, world, drops_group, projectiles_group=None) -> None:
        super().__init__()
        self.world = world
        self.drops_group = drops_group
        self.spawn_pos = (x, y)
        self.projectiles_group = projectiles_group
        self.damage = 40
        
        self.image = pygame.Surface((TILE_SIZE * 3, TILE_SIZE * 3), pygame.SRCALPHA)
        # Background aura
        pygame.draw.circle(self.image, (50, 0, 80, 150), (TILE_SIZE*1.5, TILE_SIZE*1.5), TILE_SIZE*1.5)
        # Main body
        pygame.draw.circle(self.image, (20, 0, 40), (TILE_SIZE*1.5, TILE_SIZE*1.5), TILE_SIZE*1.2)
        # Glowing runes / cracks
        pygame.draw.line(self.image, (150, 0, 255), (TILE_SIZE*1.5, 0), (TILE_SIZE*1.5, TILE_SIZE*3), 3)
        pygame.draw.line(self.image, (150, 0, 255), (0, TILE_SIZE*1.5), (TILE_SIZE*3, TILE_SIZE*1.5), 3)
        # Glowing Eyes
        pygame.draw.circle(self.image, (255, 0, 0), (TILE_SIZE*1.0, TILE_SIZE*1.2), 8)
        pygame.draw.circle(self.image, (255, 0, 0), (TILE_SIZE*2.0, TILE_SIZE*1.2), 8)
        # Spikes
        pygame.draw.polygon(self.image, (80, 0, 120), [(TILE_SIZE*1.5, 0), (TILE_SIZE*1.2, -10), (TILE_SIZE*1.8, -10)])
        pygame.draw.polygon(self.image, (80, 0, 120), [(0, TILE_SIZE*1.5), (-10, TILE_SIZE*1.2), (-10, TILE_SIZE*1.8)])
        pygame.draw.polygon(self.image, (80, 0, 120), [(TILE_SIZE*3, TILE_SIZE*1.5), (TILE_SIZE*3+10, TILE_SIZE*1.2), (TILE_SIZE*3+10, TILE_SIZE*1.8)])

        
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.hitbox = pygame.Rect(0, 0, TILE_SIZE * 2.8, TILE_SIZE * 2.8)
        self.hitbox.midbottom = self.rect.midbottom
        
        self.hp = 2000
        self.max_hp = 2000
        self.speed = 4.0
        self.vel_y = 0.0
        self.on_ground = False
        
        self.state = 'idle'
        self.state_timer = 0
        self.invuln_timer = 0
        self.facing_right = True
        
        # Network sync
        import uuid
        self.net_id = str(uuid.uuid4())
        self.target_x = x
        self.target_y = y
        
    def take_damage(self, amount: int, src_x: int) -> bool:
        if self.invuln_timer > 0: return False
        self.hp -= amount
        self.invuln_timer = 10
        audio.play_sfx('hit')
        if self.hp <= 0:
            self._die()
            return True
        return False
        
    def _die(self):
        self.kill()
        # Loot
        drop = ItemDrop(self.hitbox.centerx, self.hitbox.centery, 'quantum_engine', self.world)
        self.drops_group.add(drop)
        for _ in range(15):
            d = ItemDrop(self.hitbox.centerx + random.randint(-40, 40), self.hitbox.centery + random.randint(-40, 40), 'ruby', self.world)
            self.drops_group.add(d)
            d2 = ItemDrop(self.hitbox.centerx + random.randint(-40, 40), self.hitbox.centery + random.randint(-40, 40), 'titanium_ingot', self.world)
            self.drops_group.add(d2)
        if random.random() < 0.05:
            d3 = ItemDrop(self.hitbox.centerx, self.hitbox.centery - 20, 'OVERPOWERED_SWORD666', self.world)
            self.drops_group.add(d3)
            
    def update(self, cat=None):
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if self.invuln_timer > 0: self.invuln_timer -= 1
        
        if is_client:
            self.hitbox.centerx += (self.target_x - self.hitbox.centerx) * 0.3
            self.hitbox.centery += (self.target_y - self.hitbox.centery) * 0.3
            self.rect.midbottom = self.hitbox.midbottom
            return

        self.state_timer -= 1
        
        dx = cat.hitbox.centerx - self.hitbox.centerx if cat else 0
        self.facing_right = dx > 0
        
        if self.state == 'idle':
            if self.state_timer <= 0:
                import random
                choice = random.choice(['jump', 'jump', 'shoot'])
                if choice == 'jump' or cat is None:
                    self.state = 'jump'
                    self.state_timer = 60
                    self.vel_y = -15.0
                    self.vel_x = self.speed * 2.5 if self.facing_right else -self.speed * 2.5
                    self.on_ground = False
                    audio.play_sfx('jump')
                else:
                    self.state = 'shoot'
                    self.state_timer = 30
                    audio.play_sfx('boss_spawn')
                    
        elif self.state == 'shoot':
            if self.state_timer == 15 and cat is not None and self.projectiles_group is not None:
                from src.entities.projectiles import AbyssalOrb
                import math
                dy = cat.hitbox.centery - self.hitbox.centery
                dist = math.hypot(dx, dy)
                if dist > 0:
                    vx, vy = (dx/dist)*8, (dy/dist)*8
                    orb1 = AbyssalOrb(self.hitbox.centerx, self.hitbox.centery, vx, vy, self.world)
                    orb2 = AbyssalOrb(self.hitbox.centerx, self.hitbox.centery, vx*0.8 - vy*0.5, vy*0.8 + vx*0.5, self.world)
                    orb3 = AbyssalOrb(self.hitbox.centerx, self.hitbox.centery, vx*0.8 + vy*0.5, vy*0.8 - vx*0.5, self.world)
                    self.projectiles_group.add(orb1, orb2, orb3)
            
            if self.state_timer <= 0:
                self.state = 'idle'
                self.state_timer = 40
        elif self.state == 'jump':
            if self.on_ground:
                self.state = 'idle'
                self.state_timer = 40
                self.vel_x = 0
                
        if self.state == 'jump':
            self._move(self.vel_x)
            
        self._apply_gravity()
        
        if cat and self.hitbox.colliderect(cat.hitbox):
            cat.take_damage(20, self.hitbox.centerx)
            
    def _move(self, dx: float):
        solid = self._get_nearby_solid()
        self.hitbox.x += int(dx)
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if dx > 0: self.hitbox.right = tile.left
                elif dx < 0: self.hitbox.left = tile.right
                
    def _apply_gravity(self):
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        solid = self._get_nearby_solid()
        self.hitbox.y += int(self.vel_y)
        self.on_ground = False
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if self.vel_y > 0:
                    self.hitbox.bottom = tile.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.hitbox.top = tile.bottom
                    self.vel_y = 0
        self.rect.midbottom = self.hitbox.midbottom

    def _get_nearby_solid(self) -> list[pygame.Rect]:
        rects = []
        col = self.hitbox.centerx // TILE_SIZE
        row = self.hitbox.centery // TILE_SIZE
        for r in range(max(0, row - 3), min(self.world.rows, row + 4)):
            for c in range(max(0, col - 3), min(self.world.cols, col + 4)):
                block_id = self.world.grid[r][c]
                if block_id in BLOCK_DEFS and BLOCK_DEFS[block_id].get('solid', False):
                    rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects
