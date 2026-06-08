import pygame
import math
from src.core.settings import TILE_SIZE, WHITE, BLACK

class PetSlime(pygame.sprite.Sprite):
    def __init__(self, cat, world):
        super().__init__()
        self.cat = cat
        self.world = world
        self.size = 16
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(cat.hitbox.centerx, cat.hitbox.centery))
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)
        self.offset_x = 30
        self.offset_y = -20
        
    def update(self):
        target_x = self.cat.hitbox.centerx + (self.offset_x if not self.cat.facing_right else -self.offset_x)
        target_y = self.cat.hitbox.centery + self.offset_y
        
        # Smooth follow
        self.pos_x += (target_x - self.pos_x) * 0.1
        self.pos_y += (target_y - self.pos_y) * 0.1
        
        # Bobbing
        t = pygame.time.get_ticks() * 0.005
        bob = math.sin(t) * 5
        
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y + bob)
        
        # Draw
        self.image.fill((0,0,0,0))
        cx, cy = self.size//2, self.size//2
        color = (50, 150, 255, 200) # Blue slime with some transparency
        
        squish = int(math.sin(t*2) * 2)
        pygame.draw.rect(self.image, color, (cx-8-squish, cy-8+squish, 16+squish*2, 16-squish*2), border_radius=4)
        
        # Eyes
        pygame.draw.circle(self.image, WHITE, (cx-3, cy-2+squish), 2)
        pygame.draw.circle(self.image, WHITE, (cx+3, cy-2+squish), 2)
        pygame.draw.circle(self.image, BLACK, (cx-3, cy-2+squish), 1)
        pygame.draw.circle(self.image, BLACK, (cx+3, cy-2+squish), 1)
