import pygame
from src.core import audio
from src.core.settings import WIDTH, HEIGHT, WHITE, UI_SLOT_BORDER
from src.items.items import get_item_def

BREWING_RECIPES = [
    {"result": "potion_strength", "yield": 1, "req": {"magnum_opus": 1, "zombie_brain": 1}},
    {"result": "potion_fire_res", "yield": 1, "req": {"magnum_opus": 1, "magma_clot": 1}},
    {"result": "potion_jump",     "yield": 1, "req": {"magnum_opus": 1, "slimeball": 1}},
]

class AlchemyUI:
    def __init__(self, inventory):
        self.inventory = inventory
        self.is_open = False
        
        self.width = 650 
        self.row_height = 80 
        self.height = min(HEIGHT - 40, 80 + len(BREWING_RECIPES) * self.row_height + 20) 
        
        self.rect = pygame.Rect(
            (WIDTH - self.width) // 2, 
            (HEIGHT - self.height) // 2, 
            self.width, self.height
        )

    def toggle(self):
        self.is_open = not self.is_open

    def close(self):
        self.is_open = False

    def _can_brew(self, req: dict) -> bool:
        for item_id, count in req.items():
            if self.inventory.count_item(item_id) < count:
                return False
        return True

    def _brew(self, recipe: dict):
        if self._can_brew(recipe["req"]):
            for item_id, count in recipe["req"].items():
                self.inventory.consume_item(item_id, count)
            self.inventory.add_item(recipe["result"], recipe["yield"])
            audio.play_sfx("craft")

    def on_mouse_down(self, pos: tuple[int, int]) -> bool:
        if not self.is_open:
            return False

        if not self.rect.collidepoint(pos):
            self.close()
            return True

        start_y = self.rect.y + 60
        for i, recipe in enumerate(BREWING_RECIPES):
            row_rect = pygame.Rect(self.rect.x + 20, start_y + i * self.row_height, self.width - 40, self.row_height - 10)
            if row_rect.collidepoint(pos):
                self._brew(recipe)
                return True
        return True

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        if not self.is_open: return

        # Main background
        pygame.draw.rect(surface, (45, 30, 60), self.rect)
        pygame.draw.rect(surface, (150, 50, 200), self.rect, 3)
        pygame.draw.rect(surface, (80, 20, 100), self.rect, 1)

        font_title = pygame.font.SysFont(None, 42)
        font_text = pygame.font.SysFont(None, 24)

        title = font_title.render("Brewing Stand", True, (255, 200, 255))
        surface.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 15))

        start_y = self.rect.y + 60
        for i, recipe in enumerate(BREWING_RECIPES):
            can_brew = self._can_brew(recipe["req"])
            row_rect = pygame.Rect(self.rect.x + 20, start_y + i * self.row_height, self.width - 40, self.row_height - 10)

            bg_color = (60, 40, 90) if can_brew else (90, 50, 50)
            if row_rect.collidepoint(mouse_pos) and can_brew:
                bg_color = (80, 50, 110)

            pygame.draw.rect(surface, bg_color, row_rect)
            pygame.draw.rect(surface, (150, 50, 200), row_rect, 1)

            # Draw ingredients
            x_offset = row_rect.x + 20
            y_offset = row_rect.y + (row_rect.height - 40) // 2
            
            req_items = list(recipe["req"].items())
            for idx, (req_id, req_count) in enumerate(req_items):
                # Draw slot background
                slot_rect = pygame.Rect(x_offset, y_offset, 40, 40)
                pygame.draw.rect(surface, (30, 20, 40), slot_rect)
                pygame.draw.rect(surface, (100, 50, 150), slot_rect, 1)
                
                mock_item = {"id": req_id, "count": req_count}
                # inventory._draw_item_at expects an x, y and it draws 48x48 usually, but we'll adapt.
                # Actually _draw_item_at uses SLOT_SIZE which is 48.
                self.inventory._draw_item_at(surface, mock_item, x_offset - 4, y_offset - 4)
                
                x_offset += 55
                
                if idx < len(req_items) - 1:
                    plus = font_text.render("+", True, WHITE)
                    surface.blit(plus, (x_offset - 5, row_rect.y + row_rect.height // 2 - 10))
                    x_offset += 20

            # Draw arrow
            arrow = font_text.render("----->", True, (200, 150, 255))
            surface.blit(arrow, (x_offset + 10, row_rect.y + row_rect.height // 2 - 10))
            x_offset += 80

            # Draw result
            res_rect = pygame.Rect(x_offset, y_offset, 40, 40)
            pygame.draw.rect(surface, (50, 20, 80), res_rect)
            pygame.draw.rect(surface, (200, 100, 255), res_rect, 2)
            
            mock_res = {"id": recipe["result"], "count": recipe["yield"]}
            self.inventory._draw_item_at(surface, mock_res, x_offset - 4, y_offset - 4)
            
            # Result name
            res_def = get_item_def(recipe["result"])
            res_name = res_def.get("name", recipe["result"])
            txt_res = font_text.render(res_name, True, (255, 200, 255))
            surface.blit(txt_res, (x_offset + 55, row_rect.y + row_rect.height // 2 - 10))
