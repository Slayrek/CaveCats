# ============================================================
#  ui_furnace.py — Інтерфейс пічки (з Drag&Drop та розумним Shift)
# ============================================================

import pygame
from src.core.settings import WIDTH, HEIGHT, SLOT_SIZE, WHITE, UI_SLOT_BG, UI_SLOT_BORDER, UI_SLOT_HOVER, MAX_STACK
from src.items.items import get_item_def
from src.world.furnace_manager import SMELTING_RECIPES

# --- ДИНАМІЧНО ДОДАЄМО РЕЦЕПТИ (РИБА ТА МІДЬ) ---
if "raw_fish" not in SMELTING_RECIPES:
    SMELTING_RECIPES["raw_fish"] = {"result": "fried_fish", "time": 120} 
if "copper_ore" not in SMELTING_RECIPES:
    SMELTING_RECIPES["copper_ore"] = {"result": "copper_ingot", "time": 120} # Мідь плавиться 2 секунди

class FurnaceUI:
    def __init__(self, inventory, furnace_manager):
        self.inventory = inventory
        self.furnace_manager = furnace_manager
        self.is_open = False
        self.furnace_pos = None
        self.f_data = None
        
        self.drag_item = None
        self.drag_source = None 

    def open(self, col: int, row: int):
        self.is_open = True
        self.furnace_pos = (col, row)
        self.f_data = self.furnace_manager.get_furnace(row, col)
        self.inventory.show_full = True 

    def close(self):
        self.is_open = False
        self.furnace_pos = None
        self.f_data = None
        self.inventory.show_full = False
        self._return_drag()

    def _get_rects(self):
        cx, cy = WIDTH // 2, HEIGHT // 3
        return {
            "input":  pygame.Rect(cx - 60, cy - 40, SLOT_SIZE, SLOT_SIZE),
            "fuel":   pygame.Rect(cx - 60, cy + 30, SLOT_SIZE, SLOT_SIZE),
            "output": pygame.Rect(cx + 40, cy - 5,  SLOT_SIZE, SLOT_SIZE)
        }

    def _shift_transfer_from_inv(self, inv_idx: int):
        item = self.inventory.data[inv_idx]
        if not item["id"]: return

        target_slot_name = None
        if item["id"] == "coal":
            target_slot_name = "fuel"
        elif item["id"] in SMELTING_RECIPES:
            target_slot_name = "input"
            
        if target_slot_name:
            self._transfer_to_slot(item, self.f_data[target_slot_name])

    def _shift_transfer_from_furnace(self, slot_name: str):
        item = self.f_data[slot_name]
        if not item["id"]: return
        
        max_stack = get_item_def(item["id"]).get("max_stack", MAX_STACK)
        
        for tgt in self.inventory.data:
            if tgt["id"] == item["id"] and tgt["count"] < max_stack:
                space = max_stack - tgt["count"]
                added = min(item["count"], space)
                tgt["count"] += added
                item["count"] -= added
                if item["count"] == 0:
                    item["id"] = None
                    return
                    
        if item["count"] > 0:
            for tgt in self.inventory.data:
                if tgt["id"] is None:
                    tgt["id"] = item["id"]
                    tgt["count"] = item["count"]
                    item["id"] = None
                    item["count"] = 0
                    return

    def _transfer_to_slot(self, source_item: dict, target_slot: dict):
        max_stack = get_item_def(source_item["id"]).get("max_stack", MAX_STACK)
        if target_slot["id"] is None:
            target_slot["id"] = source_item["id"]
            target_slot["count"] = source_item["count"]
            source_item["id"] = None
            source_item["count"] = 0
        elif target_slot["id"] == source_item["id"]:
            space = max_stack - target_slot["count"]
            added = min(source_item["count"], space)
            target_slot["count"] += added
            source_item["count"] -= added
            if source_item["count"] == 0:
                source_item["id"] = None

    def _pickup_item(self, source_type: str, idx_or_name, data_container):
        slot = data_container[idx_or_name]
        if slot["id"]:
            self.drag_item = {"id": slot["id"], "count": slot["count"]}
            self.drag_source = (source_type, idx_or_name)
            slot["id"] = None
            slot["count"] = 0

    def _drop_item(self, pos: tuple[int, int]):
        target_type, target_idx, target_slot = None, None, None

        rects = self._get_rects()
        for name, rect in rects.items():
            if rect.collidepoint(pos):
                target_type, target_idx, target_slot = "furnace", name, self.f_data[name]
                break
        
        if not target_slot:
            for i in range(len(self.inventory.data)):
                if self.inventory._slot_rect(i).collidepoint(pos):
                    target_type, target_idx, target_slot = "inv", i, self.inventory.data[i]
                    break

        if target_slot:
            if target_type == "furnace":
                if target_idx == "output":
                    self._return_drag() 
                    return
                if target_idx == "fuel" and self.drag_item["id"] != "coal":
                    self._return_drag() 
                    return
                if target_idx == "input" and self.drag_item["id"] not in SMELTING_RECIPES:
                    self._return_drag() 
                    return

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
        
        if src_type == "furnace":
            src_slot = self.f_data[src_idx]
        else:
            src_slot = self.inventory.data[src_idx]
            
        if src_slot["id"] is None:
            src_slot["id"], src_slot["count"] = self.drag_item["id"], self.drag_item["count"]
        else:
            self._shift_transfer_to_inv_fallback(self.drag_item)
            
        self.drag_item, self.drag_source = None, None

    def _shift_transfer_to_inv_fallback(self, item: dict):
        max_stack = get_item_def(item["id"]).get("max_stack", MAX_STACK)
        for tgt in self.inventory.data:
            if tgt["id"] == item["id"] and tgt["count"] < max_stack:
                space = max_stack - tgt["count"]
                added = min(item["count"], space)
                tgt["count"] += added
                item["count"] -= added
                if item["count"] == 0: return
        if item["count"] > 0:
            for tgt in self.inventory.data:
                if tgt["id"] is None:
                    tgt["id"] = item["id"]
                    tgt["count"] = item["count"]
                    return

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.is_open: return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            mods = pygame.key.get_mods()
            is_shift = mods & pygame.KMOD_SHIFT

            rects = self._get_rects()

            for slot_name, rect in rects.items():
                if rect.collidepoint(pos):
                    if is_shift:
                        self._shift_transfer_from_furnace(slot_name)
                    else:
                        self._pickup_item("furnace", slot_name, self.f_data)
                    return True

            for i in range(len(self.inventory.data)):
                if self.inventory._slot_rect(i).collidepoint(pos):
                    if is_shift:
                        self._shift_transfer_from_inv(i)
                    else:
                        self._pickup_item("inv", i, self.inventory.data)
                    return True

            self.close()
            return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.drag_item:
                pos = pygame.mouse.get_pos()
                self._drop_item(pos)
            return True

        return False

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        if not self.is_open: return

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        font = pygame.font.SysFont(None, 32)
        txt = font.render("Furnace", True, WHITE)
        surface.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 3 - 90))

        rects = self._get_rects()

        for name, rect in rects.items():
            pygame.draw.rect(surface, UI_SLOT_BG, rect)
            color = UI_SLOT_HOVER if rect.collidepoint(mouse_pos) else UI_SLOT_BORDER
            pygame.draw.rect(surface, color, rect, 2)
            
            if self.f_data[name]["id"]:
                self.inventory._draw_item_at(surface, self.f_data[name], rect.x, rect.y)

        cx, cy = WIDTH // 2, HEIGHT // 3
        if self.f_data["burn_time"] > 0 and self.f_data["max_burn_time"] > 0:
            fire_height = int((self.f_data["burn_time"] / self.f_data["max_burn_time"]) * 20)
            pygame.draw.rect(surface, (255, 100, 0), (cx - 45, cy + 10 + (20 - fire_height), 14, fire_height))

        recipe = SMELTING_RECIPES.get(self.f_data["input"]["id"])
        if recipe:
            prog_width = int((self.f_data["smelt_progress"] / recipe["time"]) * 24)
            pygame.draw.rect(surface, (150, 150, 150), (cx - 10, cy, prog_width, 14))

        if self.drag_item:
            mx, my = mouse_pos
            self.inventory._draw_item_at(surface, self.drag_item, mx - SLOT_SIZE // 2, my - SLOT_SIZE // 2)