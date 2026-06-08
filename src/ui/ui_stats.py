# ============================================================
#  ui_stats.py — Інтерфейс здоров'я та броні
# ============================================================

import pygame
from src.core.settings import WIDTH, HEIGHT, HOTBAR_SLOTS, SLOT_SIZE, SLOT_MARGIN

# Малюємо піксель-арт прямо в коді (X - колір, . - контур)
HEART_PATTERN = [
    "  ..  ..  ",
    " .XX..XX. ",
    ".XXXXXXXX.",
    ".XXXXXXXX.",
    " .XXXXXX. ",
    "  .XXXX.  ",
    "   .XX.   ",
    "    ..    "
]

SHIELD_PATTERN = [
    "..........",
    ".XXXXXXXX.",
    ".XXXXXXXX.",
    ".XXXXXXXX.",
    " .XXXXXX. ",
    "  .XXXX.  ",
    "   .XX.   ",
    "    ..    "
]

class StatsUI:
    def __init__(self):
        self.scale = 2 # Збільшуємо пікселі у 2 рази
        
        # Генеруємо картинки сердечок
        self.img_heart_f = self._render_icon(HEART_PATTERN, (220, 20, 20), (50, 0, 0), "full")
        self.img_heart_h = self._render_icon(HEART_PATTERN, (220, 20, 20), (50, 0, 0), "half")
        self.img_heart_e = self._render_icon(HEART_PATTERN, (40, 40, 40), (20, 20, 20), "empty")

        # Генеруємо картинки броні
        self.img_shield_f = self._render_icon(SHIELD_PATTERN, (100, 150, 255), (20, 30, 80), "full")
        self.img_shield_h = self._render_icon(SHIELD_PATTERN, (100, 150, 255), (20, 30, 80), "half")
        self.img_shield_e = self._render_icon(SHIELD_PATTERN, (40, 40, 40), (20, 20, 20), "empty")

    def _render_icon(self, pattern, main_color, outline_color, state):
        width = len(pattern[0])
        height = len(pattern)
        surf = pygame.Surface((width * self.scale, height * self.scale), pygame.SRCALPHA)
        
        for r in range(height):
            for c in range(width):
                char = pattern[r][c]
                if char == ' ': continue
                
                color = (0, 0, 0, 0)
                if char == '.':
                    color = outline_color
                elif char == 'X':
                    if state == "empty":
                        color = (40, 40, 40) # Темно-сірий для порожнього
                    elif state == "half" and c >= width // 2:
                        color = (40, 40, 40) # Права половина порожня
                    else:
                        color = main_color
                        
                pygame.draw.rect(surf, color, (c * self.scale, r * self.scale, self.scale, self.scale))
        return surf

    def draw(self, surface: pygame.Surface, cat):
        # Розраховуємо позицію: рівно над хотбаром
        hotbar_width = HOTBAR_SLOTS * (SLOT_SIZE + SLOT_MARGIN)
        start_x = (WIDTH - hotbar_width) // 2
        
        hearts_y = HEIGHT - SLOT_SIZE - SLOT_MARGIN - 25
        armor_y = hearts_y - 20 # Броня вище за здоров'я

        # Малюємо 9 сердечок (макс 18 HP)
        self._draw_bar(surface, start_x, hearts_y, cat.hp, cat.max_hp, 
                       self.img_heart_f, self.img_heart_h, self.img_heart_e)

        # Малюємо броню (макс 18 Armor), якщо вона є
        if cat.armor > 0:
            self._draw_bar(surface, start_x, armor_y, cat.armor, cat.max_armor,
                           self.img_shield_f, self.img_shield_h, self.img_shield_e)

    def _draw_bar(self, surface, start_x, y, value, max_value, img_f, img_h, img_e):
        total_icons = max_value // 2
        
        for i in range(total_icons):
            x = start_x + i * 22 # 22 - це ширина іконки + відступ
            icon_val = i * 2
            
            if value >= icon_val + 2:
                surface.blit(img_f, (x, y))
            elif value == icon_val + 1:
                surface.blit(img_h, (x, y))
            else:
                surface.blit(img_e, (x, y))