# ============================================================
#  ui_creative.py — Креативний режим (Каталог предметів)
# ============================================================

import pygame
from src.core.settings import WIDTH, HEIGHT, SLOT_SIZE, SLOT_MARGIN, WHITE, UI_SLOT_BG, UI_SLOT_BORDER, MAX_STACK
from src.items.items import ITEM_DEFS, get_item_def

class CreativeUI:
    def __init__(self, inventory, cat):
        self.inventory = inventory
        self.cat = cat # Потрібен, щоб перевіряти, чи увімкнений noclip
        
        # Беремо ВСІ предмети з гри, ОКРІМ секретного меча 666
        self.items = [k for k in ITEM_DEFS.keys() if k != "OVERPOWERED_SWORD666"]
        
        self.cols = 12 # Робимо широку сітку на 12 колонок
        self.rows = (len(self.items) + self.cols - 1) // self.cols

    def _get_slot_rect(self, idx: int) -> pygame.Rect:
        row = idx // self.cols
        col = idx % self.cols
        
        # Відмальовуємо панель креативу вгорі екрана (над інвентарем)
        start_x = (WIDTH - self.cols * (SLOT_SIZE + SLOT_MARGIN)) // 2
        start_y = 80 
        
        x = start_x + col * (SLOT_SIZE + SLOT_MARGIN)
        y = start_y + row * (SLOT_SIZE + SLOT_MARGIN)
        return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

    def handle_event(self, event: pygame.event.Event) -> bool:
        # Працює ТІЛЬКИ якщо відкритий інвентар І увімкнений noclip
        if not self.inventory.show_full or not self.cat.noclip:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            for i, item_id in enumerate(self.items):
                if self._get_slot_rect(i).collidepoint(pos):
                    # Якщо ми вже щось тягнемо в лапці - знищуємо це (як кошик)
                    if self.inventory.drag_item:
                        self.inventory.drag_item = None
                        self.inventory.drag_source = None
                        return True
                        
                    # Беремо повний стак предмета з креативу
                    max_s = get_item_def(item_id).get("max_stack", MAX_STACK)
                    self.inventory.drag_item = {"id": item_id, "count": max_s}
                    # Спеціальна позначка, що ми взяли це з повітря
                    self.inventory.drag_source = "creative"
                    return True

        # Якщо відпустили будь-який предмет над креативним меню — видаляємо його
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.inventory.drag_item:
                pos = pygame.mouse.get_pos()
                for i, item_id in enumerate(self.items):
                    if self._get_slot_rect(i).collidepoint(pos):
                        self.inventory.drag_item = None
                        self.inventory.drag_source = None
                        return True
                        
        return False

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        if not self.inventory.show_full or not self.cat.noclip:
            return

        # Епічний заголовок
        font = pygame.font.SysFont("impact", 40)
        txt = font.render("CREATIVE MODE", True, (255, 200, 255))
        surface.blit(txt, (WIDTH // 2 - txt.get_width() // 2, 25))

        hovered_item_id = None

        # Малюємо слоти
        for i, item_id in enumerate(self.items):
            rect = self._get_slot_rect(i)
            pygame.draw.rect(surface, UI_SLOT_BG, rect)
            
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (255, 100, 255), rect, 2) # Рожева рамка
                hovered_item_id = item_id
            else:
                pygame.draw.rect(surface, UI_SLOT_BORDER, rect, 2)

            # Малюємо 1 штучку предмета для візуалу
            mock_item = {"id": item_id, "count": 1}
            self.inventory._draw_item_at(surface, mock_item, rect.x, rect.y)

        # Малюємо назву предмета, якщо навели мишку (і нічого не тягнемо)
        if hovered_item_id and not self.inventory.drag_item:
            item_name = get_item_def(hovered_item_id).get("name", hovered_item_id)
            font_tt = pygame.font.SysFont(None, 26)
            text = font_tt.render(item_name, True, WHITE)
            
            mx, my = mouse_pos
            bg_rect = pygame.Rect(mx + 15, my + 15, text.get_width() + 12, text.get_height() + 8)
            
            pygame.draw.rect(surface, (40, 20, 40), bg_rect)
            pygame.draw.rect(surface, (255, 100, 255), bg_rect, 1)
            surface.blit(text, (bg_rect.x + 6, bg_rect.y + 4))