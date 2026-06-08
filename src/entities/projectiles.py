import pygame
import math
from src.core.settings import TILE_SIZE, GRAVITY
from src.world.blocks import BLOCK_DEFS

class Arrow(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, vel_x: float, vel_y: float, world):
        super().__init__()
        self.world = world
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.damage = 25
        self.life = 300 
        self.stuck = False
        
        self.size = 16
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 8, 8)
        self.hitbox.center = self.rect.center
        
        # Network sync
        import uuid
        self.net_id = str(uuid.uuid4())
        self.target_x = float(x)
        self.target_y = float(y)
        
        self._update_image()

    def _update_image(self):
        self.image.fill((0,0,0,0))
        cx, cy = self.size//2, self.size//2
        angle = math.atan2(-self.vel_y, self.vel_x)
        
        end_x = cx + math.cos(angle) * 8
        end_y = cy - math.sin(angle) * 8
        start_x = cx - math.cos(angle) * 8
        start_y = cy + math.sin(angle) * 8
        
        pygame.draw.line(self.image, (150, 100, 50), (start_x, start_y), (end_x, end_y), 2)
        pygame.draw.circle(self.image, (200, 200, 200), (int(end_x), int(end_y)), 2)

    def update(self):
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if is_client:
            self.x += (self.target_x - self.x) * 0.3
            self.y += (self.target_y - self.y) * 0.3
            self.hitbox.centerx = int(self.x)
            self.hitbox.centery = int(self.y)
            self.rect.center = self.hitbox.center
            self._update_image()
            return

        if self.stuck:
            self.life -= 1
            if self.life <= 0:
                self.kill()
            return

        self.vel_y += GRAVITY * 0.5
        self.x += self.vel_x
        self.y += self.vel_y
        self.hitbox.centerx = int(self.x)
        self.hitbox.centery = int(self.y)
        self.rect.center = self.hitbox.center
        
        col = self.hitbox.centerx // TILE_SIZE
        row = self.hitbox.centery // TILE_SIZE
        if self.world._in_bounds(row, col):
            if BLOCK_DEFS[self.world.grid[row][col]].get("solid", False):
                self.stuck = True
                self.vel_x = 0
                self.vel_y = 0
                return
                
        self._update_image()

class HookProjectile(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, vel_x: float, vel_y: float, world):
        super().__init__()
        self.world = world
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (100, 100, 100), (5, 5), 4)
        pygame.draw.circle(self.image, (200, 200, 200), (5, 5), 4, 1)
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect.copy()
        
        self.x = float(x)
        self.y = float(y)
        self.vel_x = vel_x
        self.vel_y = vel_y
        
        self.stuck = False
        
        # Network sync
        import uuid
        self.net_id = str(uuid.uuid4())
        self.target_x = float(x)
        self.target_y = float(y)
        
    def update(self):
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if is_client:
            self.x += (self.target_x - self.x) * 0.3
            self.y += (self.target_y - self.y) * 0.3
            self.hitbox.centerx = int(self.x)
            self.hitbox.centery = int(self.y)
            self.rect.center = self.hitbox.center
            return

        if self.stuck:
            return
            
        self.x += self.vel_x
        self.y += self.vel_y
        self.hitbox.centerx = int(self.x)
        self.hitbox.centery = int(self.y)
        self.rect.center = self.hitbox.center
        
        col = self.hitbox.centerx // TILE_SIZE
        row = self.hitbox.centery // TILE_SIZE
        
        if self.world._in_bounds(row, col):
            block_id = self.world.grid[row][col]
            if BLOCK_DEFS.get(block_id, {}).get("solid", False):
                self.stuck = True
        else:
            self.kill()


class AbyssalOrb(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, vel_x: float, vel_y: float, world):
        super().__init__()
        self.world = world
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.damage = 15
        self.life = 200
        self.stuck = False
        self.is_enemy = True
        
        self.size = 20
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (150, 0, 255), (self.size//2, self.size//2), self.size//2)
        pygame.draw.circle(self.image, (255, 0, 0), (self.size//2, self.size//2), self.size//4)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = pygame.Rect(0, 0, 12, 12)
        self.hitbox.center = self.rect.center

        # Network sync
        import uuid
        self.net_id = str(uuid.uuid4())
        self.target_x = float(x)
        self.target_y = float(y)

    def update(self):
        from src.network.network_client import net_client
        is_client = net_client.is_connected and not net_client.is_host

        if is_client:
            self.x += (self.target_x - self.x) * 0.3
            self.y += (self.target_y - self.y) * 0.3
            self.rect.centerx = int(self.x)
            self.rect.centery = int(self.y)
            self.hitbox.center = self.rect.center
            return

        if self.stuck:
            self.life -= 1
            if self.life <= 0: self.kill()
            return
            
        self.life -= 1
        if self.life <= 0:
            self.kill()
            return
            
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        self.hitbox.center = self.rect.center
        
        # basic block collision
        col = self.hitbox.centerx // TILE_SIZE
        row = self.hitbox.centery // TILE_SIZE
        if 0 <= row < self.world.rows and 0 <= col < self.world.cols:
            b_id = self.world.grid[row][col]
            if b_id in BLOCK_DEFS and BLOCK_DEFS[b_id].get('solid', False):
                self.stuck = True
                self.life = 10
