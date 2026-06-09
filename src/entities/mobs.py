import pygame
import random
import math
from src.core.settings import TILE_SIZE, GRAVITY, MAX_FALL_SPEED, WHITE, BLACK
from src.world.blocks import BLOCK_DEFS, BLOCK_CAVE, BLOCK_AIR, BLOCK_WATER
from src.entities.item_drop import ItemDrop

class Mob(pygame.sprite.Sprite):
    def __init__(self, x: int, y: int, world, drops_group):
        super().__init__()
        self.world = world
        self.drops_group = drops_group
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.hurt_timer = 0
        self.hp = 10
        self.damage = 1
        
        # Network sync
        import uuid
        self.net_id = str(uuid.uuid4())
        self.target_x = x
        self.target_y = y

    def take_damage(self, amount: int, source_x: int) -> bool:
        self.hp -= amount
        self.hurt_timer = 15
        self.vel_y = -3
        self.vel_x = -3.0 if source_x > self.hitbox.centerx else 3.0
        if self.hp <= 0:
            self.die()
            return True
        return False
        
    def die(self):
        self.kill()

    def _get_nearby_solid(self) -> list[pygame.Rect]:
        rects = []
        col, row = self.hitbox.centerx // TILE_SIZE, self.hitbox.centery // TILE_SIZE
        for r in range(max(0, row - 3), min(self.world.rows, row + 4)):
            for c in range(max(0, col - 3), min(self.world.cols, col + 4)):
                if BLOCK_DEFS[self.world.grid[r][c]].get("solid", False):
                    rects.append(pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        return rects

    def update_physics(self):
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        solid = self._get_nearby_solid()
        
        self.hitbox.x += int(self.vel_x)
        for tile in solid:
            if self.hitbox.colliderect(tile):
                if self.vel_x > 0: self.hitbox.right = tile.left
                elif self.vel_x < 0: self.hitbox.left = tile.right
                
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

class Bat(Mob):
    def __init__(self, x, y, world, drops_group):
        super().__init__(x, y, world, drops_group)
        self.hp = 5
        self.damage = 0 # Peaceful
        self.size = 20
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 16, 16)
        self.hitbox.center = self.rect.center
        self.flight_timer = random.randint(0, 100)

    def die(self):
        if random.random() < 0.5:
            drop = ItemDrop(self.hitbox.x, self.hitbox.y, "bat_wing", self.world)
            self.drops_group.add(drop)
        super().die()

    def update(self, cat):
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            
        if is_client:
            self.hitbox.centerx += (self.target_x - self.hitbox.centerx) * 0.3
            self.hitbox.centery += (self.target_y - self.hitbox.centery) * 0.3
        else:
            self.flight_timer += 1
            if self.flight_timer > 60:
                self.flight_timer = 0
                self.vel_x = random.uniform(-2, 2)
                self.vel_y = random.uniform(-2, 2)
                
            self.facing_right = self.vel_x > 0
            
            # Instead of physics, just move freely
            self.hitbox.x += int(self.vel_x)
            self.hitbox.y += int(self.vel_y)
            
            # Don't fly through solid
            col, row = self.hitbox.centerx // TILE_SIZE, self.hitbox.centery // TILE_SIZE
            if self.world._in_bounds(row, col) and BLOCK_DEFS[self.world.grid[row][col]].get("solid", False):
                self.vel_x *= -1
                self.vel_y *= -1
                self.hitbox.x += int(self.vel_x * 2)
                self.hitbox.y += int(self.vel_y * 2)

        # Draw bat
        self.image.fill((0,0,0,0))
        cx, cy = self.size//2, self.size//2
        color = (150, 50, 50) if self.hurt_timer > 0 else (40, 40, 40)
        pygame.draw.circle(self.image, color, (cx, cy), 6) # Body
        
        flap = math.sin(pygame.time.get_ticks() * 0.02) * 5
        if self.facing_right:
            pygame.draw.polygon(self.image, color, [(cx, cy), (cx-8, cy-8-flap), (cx-4, cy+4)])
            pygame.draw.polygon(self.image, color, [(cx, cy), (cx+10, cy-10+flap), (cx+6, cy+6)])
        else:
            pygame.draw.polygon(self.image, color, [(cx, cy), (cx+8, cy-8-flap), (cx+4, cy+4)])
            pygame.draw.polygon(self.image, color, [(cx, cy), (cx-10, cy-10+flap), (cx-6, cy+6)])

        self.rect.center = self.hitbox.center

class Slime(Mob):
    def __init__(self, x, y, world, drops_group):
        super().__init__(x, y, world, drops_group)
        self.hp = 15
        self.damage = 2
        self.size = 24
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.hitbox = pygame.Rect(0, 0, 20, 20)
        self.hitbox.midbottom = self.rect.midbottom
        self.jump_timer = random.randint(30, 90)
        self.is_aggro = False

    def take_damage(self, amount: int, source_x: int) -> bool:
        self.is_aggro = True # Becomes hostile when attacked
        return super().take_damage(amount, source_x)

    def die(self):
        for _ in range(random.randint(1, 2)):
            drop = ItemDrop(self.hitbox.x, self.hitbox.y, "slimeball", self.world)
            self.drops_group.add(drop)
        if random.random() < 0.01:
            drop = ItemDrop(self.hitbox.x, self.hitbox.y, "suspicious_slime", self.world)
            self.drops_group.add(drop)
        super().die()

    def update(self, cat):
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            
        if is_client:
            self.hitbox.centerx += (self.target_x - self.hitbox.centerx) * 0.3
            self.hitbox.centery += (self.target_y - self.hitbox.centery) * 0.3
        else:
            if self.on_ground:
                self.vel_x *= 0.8
                self.jump_timer -= 1
                if self.jump_timer <= 0:
                    self.vel_y = -6
                    self.jump_timer = random.randint(40, 80)
                    if self.is_aggro:
                        dist_x = cat.hitbox.centerx - self.hitbox.centerx
                        self.vel_x = 3.0 if dist_x > 0 else -3.0
                    else:
                        self.vel_x = random.choice([-2.0, 2.0])
                        
            self.update_physics()
        
        # Draw slime
        self.image.fill((0,0,0,0))
        cx, cy = self.size//2, self.size//2
        color = (200, 50, 50, 200) if self.hurt_timer > 0 else (50, 200, 50, 200)
        
        squish = 0
        if not self.on_ground:
            squish = -4 # Stretch vertically
        elif self.jump_timer < 10:
            squish = 4 # Squish horizontally
            
        pygame.draw.rect(self.image, color, (cx-10-squish//2, cy-10+squish, 20+squish, 20-squish), border_radius=6)
        # Eyes
        pygame.draw.circle(self.image, WHITE, (cx-4, cy-4+squish), 3)
        pygame.draw.circle(self.image, WHITE, (cx+4, cy-4+squish), 3)
        pygame.draw.circle(self.image, BLACK, (cx-4, cy-4+squish), 1)
        pygame.draw.circle(self.image, BLACK, (cx+4, cy-4+squish), 1)

class ZombieCat(Mob):
    def __init__(self, x, y, world, drops_group):
        super().__init__(x, y, world, drops_group)
        self.hp = 25
        self.damage = 4 # Aggressive
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.hitbox = pygame.Rect(0, 0, 20, 36)
        self.hitbox.midbottom = self.rect.midbottom

    def die(self):
        for _ in range(random.randint(1, 2)):
            drop = ItemDrop(self.hitbox.x, self.hitbox.y, "zombie_brain", self.world)
            self.drops_group.add(drop)
        super().die()

    def update(self, cat):
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if self.hurt_timer > 0:
            self.hurt_timer -= 1
            
        if is_client:
            self.hitbox.centerx += (self.target_x - self.hitbox.centerx) * 0.3
            self.hitbox.centery += (self.target_y - self.hitbox.centery) * 0.3
        else:
            dist_x = cat.hitbox.centerx - self.hitbox.centerx
            dist_y = cat.hitbox.centery - self.hitbox.centery
            
            # Aggressive tracking
            if abs(dist_x) < TILE_SIZE * 15 and abs(dist_y) < TILE_SIZE * 10:
                if dist_x > 5:
                    self.vel_x = 1.5
                    self.facing_right = True
                elif dist_x < -5:
                    self.vel_x = -1.5
                    self.facing_right = False
            else:
                self.vel_x *= 0.5
                
            # Jump if blocked
            if self.on_ground and abs(self.vel_x) > 0.5:
                col = (self.hitbox.centerx + (20 if self.vel_x > 0 else -20)) // TILE_SIZE
                row = self.hitbox.centery // TILE_SIZE
                if self.world._in_bounds(row, col) and BLOCK_DEFS[self.world.grid[row][col]].get("solid", False):
                    self.vel_y = -6
                    
            self.update_physics()
        
        # Draw Zombie Cat
        self.image.fill((0,0,0,0))
        cx, cy = self.size//2, self.size//2
        color = (255, 100, 100) if self.hurt_timer > 0 else (60, 160, 60) # Green cat
        
        # Body
        pygame.draw.circle(self.image, color, (cx, cy+5), 14)
        
        # Left ear only (missing right ear)
        pygame.draw.polygon(self.image, color, [(cx-10, cy-5), (cx-15, cy-15), (cx-2, cy-8)])
        
        # Exposed brain (right side)
        pygame.draw.circle(self.image, (200, 50, 150), (cx+6, cy-6), 6)
        pygame.draw.circle(self.image, (255, 100, 180), (cx+8, cy-8), 4)
        
        # Eyes
        pygame.draw.circle(self.image, BLACK, (cx-4, cy+2), 2)
        pygame.draw.circle(self.image, BLACK, (cx+4, cy+2), 2)
        
        # Upside down smile
        pygame.draw.arc(self.image, BLACK, (cx-5, cy+6, 10, 6), 0, 3.14, 2)
        
        # Paws
        pygame.draw.circle(self.image, (40, 100, 40), (cx-8, cy+18), 4)
        pygame.draw.circle(self.image, (40, 100, 40), (cx+8, cy+18), 4)
        
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
