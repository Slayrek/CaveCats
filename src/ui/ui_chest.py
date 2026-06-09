# ============================================================
#  ui_chest.py — Інтерфейс скриньки
# ============================================================

import pygame
from src.core.settings import WIDTH, HEIGHT, SLOT_SIZE, SLOT_MARGIN, WHITE, BLACK, UI_SLOT_BG, UI_SLOT_BORDER, UI_SLOT_HOVER, CHEST_SLOTS, MAX_STACK
from src.items.items import get_item_def

class ChestUI:
    def __init__(self, inventory, chest_manager):
        self.inventory = inventory
        self.chest_manager = chest_manager
        self.is_open = False
        self.chest_pos = None     # (col, row)
        self.chest_data = None    # list[dict]

        self.drag_item = None
        self.drag_source = None   # ("chest", idx) або ("inv", idx)

    def open(self, col: int, row: int):
        self.is_open = True
        self.chest_pos = (col, row)
        # Отримуємо масив слотів скрині з ChestManager
        self.chest_data = self.chest_manager.get_chest(row, col)
        # Примусово відкриваємо повний інвентар гравця
        self.inventory.show_full = True 

    def close(self):
        self.is_open = False
        self.chest_pos = None
        self.chest_data = None
        self.inventory.show_full = False
        self._return_drag()

    # ------------------------------------------------------------------
    #  Геометрія слотів скрині
    # ------------------------------------------------------------------
    def _get_chest_slot_rect(self, idx: int) -> pygame.Rect:
        cols = 10
        row = idx // cols
        col = idx % cols
        start_x = (WIDTH - cols * (SLOT_SIZE + SLOT_MARGIN)) // 2
        start_y = HEIGHT // 4  # Скриня малюється у верхній частині екрана
        x = start_x + col * (SLOT_SIZE + SLOT_MARGIN)
        y = start_y + row * (SLOT_SIZE + SLOT_MARGIN)
        return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

    # ------------------------------------------------------------------
    #  Логіка перекидання (Shift-клік)
    # ------------------------------------------------------------------
    def _shift_transfer(self, src_list: list[dict], src_idx: int, tgt_list: list[dict]):
        item = src_list[src_idx]
        if not item["id"]: return

        max_stack = get_item_def(item["id"]).get("max_stack", MAX_STACK)

        # 1. Спробувати додати до існуючих неповних стаків
        for tgt in tgt_list:
            if tgt["id"] == item["id"] and tgt["count"] < max_stack:
                space = max_stack - tgt["count"]
                added = min(item["count"], space)
                tgt["count"] += added
                item["count"] -= added
                if item["count"] == 0:
                    item["id"] = None
                    return

        # 2. Якщо ще лишилося, шукаємо порожній слот
        if item["count"] > 0:
            for tgt in tgt_list:
                if tgt["id"] is None:
                    tgt["id"] = item["id"]
                    tgt["count"] = item["count"]
                    item["id"] = None
                    item["count"] = 0
                    return

    # ------------------------------------------------------------------
    #  Обробка миші
    # ------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_open:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            mods = pygame.key.get_mods()
            is_shift = mods & pygame.KMOD_SHIFT

            # Перевіряємо клік по скрині
            for i in range(len(self.chest_data)):
                if self._get_chest_slot_rect(i).collidepoint(pos):
                    if is_shift:
                        self._shift_transfer(self.chest_data, i, self.inventory.data)
                    else:
                        self._pickup_item("chest", i, self.chest_data)
                    return True

            # Перевіряємо клік по інвентарю гравця
            for i in range(len(self.inventory.data)):
                if self.inventory._slot_rect(i).collidepoint(pos):
                    if is_shift:
                        self._shift_transfer(self.inventory.data, i, self.chest_data)
                    else:
                        self._pickup_item("inv", i, self.inventory.data)
                    return True

            # Якщо клікнули повз інтерфейс — закриваємо
            self.close()
            return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_item:
                pos = pygame.mouse.get_pos()
                self._drop_item(pos)
            return True

        return False

    # ------------------------------------------------------------------
    #  Drag & Drop
    # ------------------------------------------------------------------
    def _pickup_item(self, source_type: str, idx: int, data_list: list[dict]):
        slot = data_list[idx]
        if slot["id"]:
            self.drag_item = {"id": slot["id"], "count": slot["count"]}
            self.drag_source = (source_type, idx)
            slot["id"] = None
            slot["count"] = 0

    def _drop_item(self, pos: tuple[int, int]):
        target_type, target_idx, target_list = None, None, None

        # Шукаємо, куди відпустили
        for i in range(len(self.chest_data)):
            if self._get_chest_slot_rect(i).collidepoint(pos):
                target_type, target_idx, target_list = "chest", i, self.chest_data
                break
        
        if not target_list:
            for i in range(len(self.inventory.data)):
                if self.inventory._slot_rect(i).collidepoint(pos):
                    target_type, target_idx, target_list = "inv", i, self.inventory.data
                    break

        if target_list:
            target_slot = target_list[target_idx]
            if target_slot["id"] is None:
                target_slot["id"], target_slot["count"] = self.drag_item["id"], self.drag_item["count"]
            elif target_slot["id"] == self.drag_item["id"]:
                max_stack = get_item_def(self.drag_item["id"]).get("max_stack", MAX_STACK)
                space = max_stack - target_slot["count"]
                added = min(self.drag_item["count"], space)
                target_slot["count"] += added
                self.drag_item["count"] -= added
                if self.drag_item["count"] > 0:
                    self._return_drag()
                    return
            else:
                # Обмін місцями
                temp_id, temp_count = target_slot["id"], target_slot["count"]
                target_slot["id"], target_slot["count"] = self.drag_item["id"], self.drag_item["count"]
                self.drag_item["id"], self.drag_item["count"] = temp_id, temp_count
                self._return_drag()
                return

            self.drag_item, self.drag_source = None, None
        else:
            self._return_drag()

    def _return_drag(self):
        if not self.drag_item: return
        src_type, src_idx = self.drag_source
        src_list = self.chest_data if src_type == "chest" else self.inventory.data
        
        src_slot = src_list[src_idx]
        if src_slot["id"] is None:
            src_slot["id"], src_slot["count"] = self.drag_item["id"], self.drag_item["count"]
        else:
            # Якщо з якоїсь причини зайнято, пхаємо куди влізе
            self._shift_transfer([self.drag_item], 0, src_list)
        
        self.drag_item, self.drag_source = None, None

    # ------------------------------------------------------------------
    #  Малювання
    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        if not self.is_open: return

        # Затемнення фону
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        font = pygame.font.SysFont(None, 32)
        txt = font.render("Chest", True, WHITE)
        surface.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 4 - 40))

        # Малюємо слоти скрині
        for i in range(len(self.chest_data)):
            rect = self._get_chest_slot_rect(i)
            pygame.draw.rect(surface, UI_SLOT_BG, rect)
            border = UI_SLOT_HOVER if rect.collidepoint(mouse_pos) else UI_SLOT_BORDER
            pygame.draw.rect(surface, border, rect, 2)

            slot = self.chest_data[i]
            if slot["id"]:
                self.inventory._draw_item_at(surface, slot, rect.x, rect.y)

        # Інвентар гравця намалюється сам (бо show_full = True),
        # але ми малюємо предмет, який тягнемо, поверх усього:
        if self.drag_item:
            mx, my = mouse_pos
            self.inventory._draw_item_at(surface, self.drag_item, mx - SLOT_SIZE//2, my - SLOT_SIZE//2)