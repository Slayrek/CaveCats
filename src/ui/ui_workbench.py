# ============================================================
#  ui_workbench.py — Інтерфейс крафту
# ============================================================

import pygame
from src.core import audio # <--- ІМПОРТ АУДІО
from src.core.settings import WIDTH, HEIGHT, WHITE, UI_SLOT_BORDER
from src.items.items import get_item_def

BASIC_RECIPES = [
    {"result": "workbench", "yield": 1, "req": {"wood": 4}},
]

RECIPES = [
    {"result": "furnace",   "yield": 1, "req": {"stone": 8}},
    {"result": "chest",     "yield": 1, "req": {"wood": 8}},
    {"result": "ladder",    "yield": 3, "req": {"wood": 2}},
    {"result": "wooden_platform",  "yield": 4, "req": {"wood": 1}},
    
    {"result": "copper_wire",      "yield": 10, "req": {"copper_ingot": 1}},
    {"result": "gold_plated_wire", "yield": 10, "req": {"copper_wire": 10, "gold_ingot": 1}},
    
    {"result": "rocket_platform",  "yield": 1,  "req": {"titanium_ingot": 5, "iron_ingot": 20}},
    {"result": "rocket_turbine",   "yield": 1,  "req": {"quantum_engine": 1, "titanium_ingot": 10, "iron_ingot": 20, "ruby": 15, "copper_wire": 10, "gold_plated_wire": 20, }},
    {"result": "rocket_body",      "yield": 1,  "req": {"titanium_ingot": 20, "iron_ingot": 20, "copper_ingot": 50, "copper_wire": 20, "gold_plated_wire": 10}},
    {"result": "rocket_top",       "yield": 1,  "req": {"titanium_ingot": 10, "iron_ingot": 15, "ruby": 20, "copper_wire": 60, "gold_plated_wire": 30}},
    {"result": "rocket",           "yield": 1,  "req": {"rocket_turbine": 1, "rocket_body": 1, "rocket_top": 1, "copper_wire": 100, "gold_plated_wire": 150}},
    
    {"result": "iron_pickaxe",     "yield": 1, "req": {"iron_ingot": 2, "wood": 1}},
    {"result": "gold_pickaxe",     "yield": 1, "req": {"gold_ingot": 2, "wood": 1}},
    {"result": "titanium_pickaxe", "yield": 1, "req": {"titanium_ingot": 2, "wood": 1}},
    {"result": "fishing_rod",      "yield": 1, "req": {"wood": 3, "iron_ingot": 1}}, 
    
    {"result": "iron_helmet",     "yield": 1, "req": {"iron_ingot": 4}},
    {"result": "gold_helmet",     "yield": 1, "req": {"gold_ingot": 4}},
    {"result": "titanium_chestplate","yield": 1,"req": {"titanium_ingot": 8}},
    
    {"result": "abyssal_sigil",    "yield": 1, "req": {"suspicious_slime": 1, "ruby": 10, "titanium_ingot": 10, "zombie_brain": 5}},
    {"result": "ruby_helmet",     "yield": 1, "req": {"ruby": 4}},
    
    {"result": "iron_boots",     "yield": 1, "req": {"iron_ingot": 4}},
    {"result": "gold_boots",     "yield": 1, "req": {"gold_ingot": 4}},
    {"result": "titanium_boots", "yield": 1, "req": {"titanium_ingot": 4}},
    {"result": "ruby_boots",     "yield": 1, "req": {"ruby": 4}},
    
    {"result": "iron_sword",      "yield": 1, "req": {"iron_ingot": 3, "wood": 1}},
    {"result": "gold_sword",      "yield": 1, "req": {"gold_ingot": 3, "wood": 1}},
    {"result": "titanium_sword",  "yield": 1, "req": {"titanium_ingot": 3, "wood": 1}},
    {"result": "ruby_sword",      "yield": 1, "req": {"ruby": 3, "wood": 1}},
    
    {"result": "grappling_hook",  "yield": 1, "req": {"iron_ingot": 5, "slimeball": 3, "bat_wing": 1}},
    {"result": "OVERPOWERED_SWORD666",      "yield": 1, "req": {"ruby": 999, "wood": 999, "titanium_ingot": 999, "iron_ingot": 999, "gold_ingot": 999, "copper_ingot": 999}},
    {"result": "bow",             "yield": 1, "req": {"wood": 10, "slimeball": 5, "bat_wing": 2}},
    {"result": "lava_fishing_rod", "yield": 1, "req": {"magma_clot": 25, "fishing_rod": 1}},
]

class WorkbenchUI:
    def __init__(self, inventory, ach_manager=None):
        self.inventory = inventory
        self.ach_manager = ach_manager
        self.is_open = False
        
        self.width = 1100 
        self.row_height = 60 
        self.max_rows = 10
        self.recipes_per_page = self.max_rows * 2
        
        self.height = min(HEIGHT - 40, 80 + self.max_rows * self.row_height + 50) 
        
        self.rect = pygame.Rect(
            (WIDTH - self.width) // 2, 
            (HEIGHT - self.height) // 2, 
            self.width, self.height
        )
        
        self.page = 0
        self.btn_prev = pygame.Rect(self.rect.centerx - 120, self.rect.bottom - 40, 80, 30)
        self.btn_next = pygame.Rect(self.rect.centerx + 40, self.rect.bottom - 40, 80, 30)

    def toggle(self):
        self.is_open = not self.is_open

    def close(self):
        self.is_open = False

    def _can_craft(self, req: dict) -> bool:
        for item_id, count in req.items():
            if self.inventory.count_item(item_id) < count:
                return False
        return True

    def _craft(self, recipe: dict):
        if self._can_craft(recipe["req"]):
            for item_id, count in recipe["req"].items():
                self.inventory.consume_item(item_id, count)
            self.inventory.add_item(recipe["result"], recipe["yield"])
            audio.play_sfx("craft") # <--- ЗВУК КРАФТУ
            
            if self.ach_manager:
                self.ach_manager.check_event("craft", recipe["result"])

    def on_mouse_down(self, pos: tuple[int, int]) -> bool:
        if not self.is_open:
            return False

        if not self.rect.collidepoint(pos):
            self.close()
            return True

        total_pages = max(1, (len(RECIPES) + self.recipes_per_page - 1) // self.recipes_per_page)
        
        if self.page > 0 and self.btn_prev.collidepoint(pos):
            self.page -= 1
            return True
        if self.page < total_pages - 1 and self.btn_next.collidepoint(pos):
            self.page += 1
            return True

        start_idx = self.page * self.recipes_per_page
        end_idx = start_idx + self.recipes_per_page
        current_recipes = RECIPES[start_idx:end_idx]

        start_y = self.rect.y + 60
        for i, recipe in enumerate(current_recipes):
            col = i % 2     
            row = i // 2    
            row_rect = pygame.Rect(self.rect.x + 20 + col * 530, start_y + row * self.row_height, 510, self.row_height - 5)
            if row_rect.collidepoint(pos):
                self._craft(recipe)
                return True
        return True

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        if not self.is_open: return

        pygame.draw.rect(surface, (40, 40, 45), self.rect)
        pygame.draw.rect(surface, UI_SLOT_BORDER, self.rect, 2)

        font_title = pygame.font.SysFont(None, 36)
        font_text = pygame.font.SysFont(None, 24)
        font_req = pygame.font.SysFont(None, 18)

        title = font_title.render("Workbench Crafting", True, WHITE)
        surface.blit(title, (self.rect.centerx - title.get_width() // 2, self.rect.y + 15))

        total_pages = max(1, (len(RECIPES) + self.recipes_per_page - 1) // self.recipes_per_page)
        page_text = font_text.render(f"Page {self.page + 1} / {total_pages}", True, WHITE)
        surface.blit(page_text, (self.rect.centerx - page_text.get_width() // 2, self.rect.bottom - 33))

        if self.page > 0:
            bg = (120, 120, 120) if self.btn_prev.collidepoint(mouse_pos) else (80, 80, 80)
            pygame.draw.rect(surface, bg, self.btn_prev)
            pygame.draw.rect(surface, UI_SLOT_BORDER, self.btn_prev, 1)
            surface.blit(font_text.render("< Prev", True, WHITE), (self.btn_prev.x + 10, self.btn_prev.y + 7))
            
        if self.page < total_pages - 1:
            bg = (120, 120, 120) if self.btn_next.collidepoint(mouse_pos) else (80, 80, 80)
            pygame.draw.rect(surface, bg, self.btn_next)
            pygame.draw.rect(surface, UI_SLOT_BORDER, self.btn_next, 1)
            surface.blit(font_text.render("Next >", True, WHITE), (self.btn_next.x + 12, self.btn_next.y + 7))

        start_idx = self.page * self.recipes_per_page
        end_idx = start_idx + self.recipes_per_page
        current_recipes = RECIPES[start_idx:end_idx]

        start_y = self.rect.y + 60
        for i, recipe in enumerate(current_recipes):
            col = i % 2
            row = i // 2
            can_craft = self._can_craft(recipe["req"])
            
            row_rect = pygame.Rect(self.rect.x + 20 + col * 530, start_y + row * self.row_height, 510, self.row_height - 5)

            bg_color = (60, 90, 60) if can_craft else (90, 50, 50)
            if row_rect.collidepoint(mouse_pos) and can_craft:
                bg_color = (80, 110, 80)

            pygame.draw.rect(surface, bg_color, row_rect)
            pygame.draw.rect(surface, UI_SLOT_BORDER, row_rect, 1)

            res_def = get_item_def(recipe["result"])
            res_name = res_def.get("name", recipe["result"])
            txt_res = font_text.render(f"{res_name} (x{recipe['yield']})", True, WHITE)
            surface.blit(txt_res, (row_rect.x + 10, row_rect.y + 5))

            req_list = [f"{get_item_def(k).get('name', k)}: {v}" for k, v in recipe["req"].items()]
            line1 = ", ".join(req_list[:3])
            txt_req1 = font_req.render(line1, True, (220, 220, 220))
            surface.blit(txt_req1, (row_rect.x + 10, row_rect.y + 25))
            
            if len(req_list) > 3:
                line2 = ", ".join(req_list[3:])
                txt_req2 = font_req.render(line2, True, (220, 220, 220))
                surface.blit(txt_req2, (row_rect.x + 10, row_rect.y + 40))
