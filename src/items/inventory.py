# ============================================================
#  inventory.py — інвентар гравця (з підтримкою броні та сейвів)
# ============================================================

import pygame
import json
import os
from src.core.settings import WIDTH, HEIGHT, HOTBAR_SLOTS, SLOT_SIZE, SLOT_MARGIN, WHITE, UI_SLOT_BG, UI_SLOT_BORDER, UI_SLOT_HOVER, MAX_STACK
from src.items.items import get_item_def
from src.ui.ui_workbench import BASIC_RECIPES
from src.core.utils import resource_path

class Inventory:
    _icon_cache = {}
    
    PALETTE = {
        'B': (20, 20, 20),      # Black/Border
        'W': (240, 240, 240),   # White
        'G': (150, 150, 150),   # Gray
        'D': (100, 100, 100),   # Dark Gray
        'R': (220, 20, 20),     # Red
        'd': (130, 10, 10),     # Dark Red
        'O': (220, 120, 20),    # Orange
        'Y': (240, 220, 20),    # Yellow
        'y': (150, 130, 0),     # Dark Yellow/Gold
        'g': (30, 180, 30),     # Green
        'S': (80, 220, 80),     # Slime Green
        's': (40, 140, 40),     # Dark Slime Green
        'P': (150, 50, 200),    # Purple
        'p': (80, 20, 120),     # Dark Purple
        'c': (100, 60, 20),     # Brown (Wood/Handle)
        'w': (40, 100, 220),    # Water/Blue
        '1': (200, 150, 100),   # Wood light
        '2': (100, 50, 0),      # Wood dark
    }

    PROCEDURAL_TEXTURES = {
        "wooden_platform": [
            "        ",
            "        ",
            "  BBBB  ",
            " BccccB ",
            "  BBBB  ",
            "        ",
            "        ",
            "        "
        ],
        "bow": [
            "11  ",
            "2 1 ",
            "2  1",
            "2 1 ",
            "11  ",
        ],
        "abyssal_sigil": [
            "   BB   ",
            "  BpPB  ",
            " BpPPpB ",
            " BPPpPB ",
            " BpPPpB ",
            "  BpPB  ",
            "   BB   ",
            "        "
        ],
        "quantum_engine": [
            "  BBBB  ",
            " BwwWwB ",
            "BwWWwwWB",
            "BWwBwBwB",
            "BwwBwBwB",
            " BwWwwB ",
            "  BBBB  ",
            "        "
        ],
        "suspicious_slime": [
            "  BBBB  ",
            " BSSSSB ",
            "BSSssSSB",
            "BSsSSsSB",
            "BSSSSSSB",
            " BSSSSB ",
            "  BBBB  "
        ],
        "ruby": [
            "  BBBB  ",
            " BRRRRB ",
            "BRRRRRRB",
            "BRRddRRB",
            " BRddRB ",
            "  BBBB  "
        ],
        "titanium_ingot": [
            "        ",
            "  BBBB  ",
            " BWGGDB ",
            " BWGGDB ",
            "  BBBB  ",
            "        "
        ],
        "titanium_pickaxe": [
            "  BBB   ",
            " BGGGB  ",
            " BGWGBB ",
            "  BcB G ",
            "  c     ",
            " c      ",
            "c       "
        ],
        "ruby_sword": [
            "      B ",
            "     BRB",
            "    BRdB",
            " B  RdB ",
            " BcBdR  ",
            " BBcB   ",
            "B  B    "
        ],
        "potion_strength": [
            "   BB   ",
            "   cc   ",
            "  BRRB  ",
            " BRRRRB ",
            " BRRRRB ",
            "  BBBB  "
        ],
        "potion_fire_res": [
            "   BB   ",
            "   cc   ",
            "  BOOB  ",
            " BOOOOB ",
            " BOOOOB ",
            "  BBBB  "
        ],
        "potion_jump": [
            "   BB   ",
            "   cc   ",
            "  BggB  ",
            " BggggB ",
            " BggggB ",
            "  BBBB  "
        ],
        "magnum_opus": [
            "   BB   ",
            "  BYYB  ",
            " BWWYYB ",
            " BYyyYB ",
            "  BYYB  ",
            "   BB   "
        ],
        "lavacalibur": [
            "      B ",
            "    B YB",
            "   B ORB",
            " B  OR B",
            " BcBdO  ",
            " BBcB   ",
            "B  B    "
        ],
        "OVERPOWERED_SWORD666": [
            "       B",
            "     B p",
            "    B Pp",
            " B  PpB ",
            " BcBPp  ",
            " BBcB   ",
            "B  B    "
        ]
    }

    @staticmethod
    def _render_pixel_art(pattern: list[str], size: int) -> pygame.Surface:
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        if not pattern: return surf
        
        rows = len(pattern)
        cols = max(len(row) for row in pattern)
        pixel_w = size / cols
        pixel_h = size / rows
        
        for r, row in enumerate(pattern):
            for c, char in enumerate(row):
                if char in Inventory.PALETTE:
                    color = Inventory.PALETTE[char]
                    rect = (int(c * pixel_w), int(r * pixel_h), int(pixel_w + 1), int(pixel_h + 1))
                    pygame.draw.rect(surf, color, rect)
        return surf

    # --- ПРИЙМАЄМО ШЛЯХ ДО ПАПКИ СЕЙВУ ---
    def __init__(self, folder="saves/default"):
        self.folder = folder
        self.filepath = os.path.join(self.folder, "inventory.json")
        
        self.slots = 30
        self.data = [{"id": None, "count": 0} for _ in range(self.slots)]
        self.armor_slot = {"id": None, "count": 0} 
        self.boots_slot = {"id": None, "count": 0}
        self.hook_slot = {"id": None, "count": 0}
        self.pet_slot = {"id": None, "count": 0}
        
        self.selected_slot = 0
        self.show_full = False
        
        self.drag_item = None
        self.drag_source = None

        self._load()

    def _load(self) -> None:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    
                    loaded_slots = []
                    if isinstance(saved_data, dict):
                        loaded_slots = saved_data.get("slots", [])
                        self.armor_slot = saved_data.get("armor", {"id": None, "count": 0})
                        self.boots_slot = saved_data.get("boots", {"id": None, "count": 0})
                        self.hook_slot = saved_data.get("hook", {"id": None, "count": 0})
                        self.pet_slot = saved_data.get("pet", {"id": None, "count": 0})
                    else:
                        loaded_slots = saved_data
                        
                    for i in range(min(self.slots, len(loaded_slots))):
                        self.data[i] = loaded_slots[i]
            except:
                pass

    def save(self) -> None:
        save_dict = {
            "slots": self.data,
            "armor": self.armor_slot,
            "boots": self.boots_slot,
            "hook": self.hook_slot,
            "pet": self.pet_slot
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(save_dict, f)

    def add_item(self, item_id: str, count: int = 1) -> bool:
        max_s = get_item_def(item_id).get("max_stack", MAX_STACK)
        for slot in self.data:
            if slot["id"] == item_id and slot["count"] < max_s:
                space = max_s - slot["count"]
                added = min(count, space)
                slot["count"] += added
                count -= added
                if count == 0:
                    self.save()
                    return True

        for slot in self.data:
            if slot["id"] is None:
                slot["id"] = item_id
                slot["count"] = count
                self.save()
                return True
        return False

    def consume_item(self, item_id: str, count: int = 1) -> bool:
        if self.count_item(item_id) < count:
            return False
        
        for slot in self.data:
            if slot["id"] == item_id:
                if slot["count"] >= count:
                    slot["count"] -= count
                    if slot["count"] == 0:
                        slot["id"] = None
                    self.save()
                    return True
                else:
                    count -= slot["count"]
                    slot["count"] = 0
                    slot["id"] = None
        return False

    def count_item(self, item_id: str) -> int:
        return sum(slot["count"] for slot in self.data if slot["id"] == item_id)

    def get_selected_slot(self) -> dict:
        return self.data[self.selected_slot]

    def select_slot(self, index: int) -> None:
        if 0 <= index < HOTBAR_SLOTS:
            self.selected_slot = index

    def get_selected_item_place_info(self) -> tuple[str | None, int | None]:
        slot = self.get_selected_slot()
        if slot["id"]:
            item_def = get_item_def(slot["id"])
            if item_def.get("place_block") is not None:
                return slot["id"], item_def["place_block"]
        return None, None

    def toggle(self):
        self.show_full = not self.show_full
        if not self.show_full:
            self._return_drag_to_source()

    def drop_item_logic(self, slot_idx: int, all_stack: bool = False) -> tuple[str, int] | None:
        slot = self.data[slot_idx]
        if not slot["id"]: return None
        
        item_id = slot["id"]
        if all_stack:
            count = slot["count"]
            slot["id"], slot["count"] = None, 0
        else:
            count = 1
            slot["count"] -= 1
            if slot["count"] <= 0:
                slot["id"], slot["count"] = None, 0
        
        self.save()
        return item_id, count

    def _slot_rect(self, index: int) -> pygame.Rect:
        cols = HOTBAR_SLOTS
        col = index % cols
        row = index // cols

        hotbar_width = cols * (SLOT_SIZE + SLOT_MARGIN)
        start_x = (WIDTH - hotbar_width) // 2

        if row == 0:
            y = HEIGHT - SLOT_SIZE - SLOT_MARGIN
        else:
            y = HEIGHT - SLOT_SIZE - SLOT_MARGIN - row * (SLOT_SIZE + SLOT_MARGIN) - 20

        x = start_x + col * (SLOT_SIZE + SLOT_MARGIN)
        return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

    def _armor_rect(self) -> pygame.Rect:
        hotbar_width = HOTBAR_SLOTS * (SLOT_SIZE + SLOT_MARGIN)
        start_x = (WIDTH - hotbar_width) // 2
        x = start_x - SLOT_SIZE - 40
        y = HEIGHT - SLOT_SIZE - SLOT_MARGIN - 2 * (SLOT_SIZE + SLOT_MARGIN) - 20
        return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

    def _boots_rect(self) -> pygame.Rect:
        hotbar_width = HOTBAR_SLOTS * (SLOT_SIZE + SLOT_MARGIN)
        start_x = (WIDTH - hotbar_width) // 2
        x = start_x + hotbar_width + 40
        y = HEIGHT - SLOT_SIZE - SLOT_MARGIN - 2 * (SLOT_SIZE + SLOT_MARGIN) - 20
        return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

    def _hook_rect(self) -> pygame.Rect:
        hotbar_width = HOTBAR_SLOTS * (SLOT_SIZE + SLOT_MARGIN)
        start_x = (WIDTH - hotbar_width) // 2
        x = start_x - SLOT_SIZE - 40
        y = HEIGHT - SLOT_SIZE - SLOT_MARGIN - 1 * (SLOT_SIZE + SLOT_MARGIN) - 20
        return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

    def _pet_rect(self) -> pygame.Rect:
        hotbar_width = HOTBAR_SLOTS * (SLOT_SIZE + SLOT_MARGIN)
        start_x = (WIDTH - hotbar_width) // 2
        x = start_x + hotbar_width + 40
        y = HEIGHT - SLOT_SIZE - SLOT_MARGIN - 1 * (SLOT_SIZE + SLOT_MARGIN) - 20
        return pygame.Rect(x, y, SLOT_SIZE, SLOT_SIZE)

    def _craft_button_rect(self) -> pygame.Rect:
        hotbar_width = HOTBAR_SLOTS * (SLOT_SIZE + SLOT_MARGIN)
        start_x = (WIDTH - hotbar_width) // 2
        top_row_y = HEIGHT - SLOT_SIZE - SLOT_MARGIN - 2 * (SLOT_SIZE + SLOT_MARGIN) - 20
        y = top_row_y - 55
        return pygame.Rect(start_x, y, hotbar_width, 45)

    def on_mouse_down(self, pos: tuple[int, int]) -> bool:
        if not self.show_full: return False

        craft_rect = self._craft_button_rect()
        if craft_rect.collidepoint(pos):
            recipe = BASIC_RECIPES[0] 
            can_craft = all(self.count_item(item_id) >= cnt for item_id, cnt in recipe["req"].items())
            if can_craft:
                for item_id, cnt in recipe["req"].items():
                    self.consume_item(item_id, cnt)
                self.add_item(recipe["result"], recipe["yield"])
            return True

        a_rect = self._armor_rect()
        if a_rect.collidepoint(pos):
            if self.armor_slot["id"]:
                self.drag_item = self.armor_slot.copy()
                self.drag_source = "armor"
                self.armor_slot = {"id": None, "count": 0}
            return True

        b_rect = self._boots_rect()
        if b_rect.collidepoint(pos):
            if self.boots_slot["id"]:
                self.drag_item = self.boots_slot.copy()
                self.drag_source = "boots"
                self.boots_slot = {"id": None, "count": 0}
            return True

        h_rect = self._hook_rect()
        if h_rect.collidepoint(pos):
            if self.hook_slot["id"]:
                self.drag_item = self.hook_slot.copy()
                self.drag_source = "hook"
                self.hook_slot = {"id": None, "count": 0}
            return True

        p_rect = self._pet_rect()
        if p_rect.collidepoint(pos):
            if self.pet_slot["id"]:
                self.drag_item = self.pet_slot.copy()
                self.drag_source = "pet"
                self.pet_slot = {"id": None, "count": 0}
            return True

        for i in range(self.slots):
            rect = self._slot_rect(i)
            if rect.collidepoint(pos):
                if self.data[i]["id"]:
                    self.drag_item = self.data[i].copy()
                    self.drag_source = i
                    self.data[i]["id"] = None
                    self.data[i]["count"] = 0
                return True
        return False

    def on_mouse_up(self, pos: tuple[int, int]) -> bool:
        if not self.drag_item: return False

        if self.show_full:
            a_rect = self._armor_rect()
            if a_rect.collidepoint(pos):
                is_helmet = get_item_def(self.drag_item["id"]).get("is_helmet", False)
                if is_helmet:
                    temp = self.armor_slot.copy()
                    self.armor_slot = self.drag_item.copy()
                    if temp["id"]:
                        self.drag_item = temp
                    else:
                        self.drag_item = None
                        self.drag_source = None
                    self.save()
                    return True
                else:
                    self._return_drag_to_source()
                    return True

            b_rect = self._boots_rect()
            if b_rect.collidepoint(pos):
                is_boots = get_item_def(self.drag_item["id"]).get("is_boots", False)
                if is_boots:
                    temp = self.boots_slot.copy()
                    self.boots_slot = self.drag_item.copy()
                    if temp["id"]:
                        self.drag_item = temp
                    else:
                        self.drag_item = None
                        self.drag_source = None
                    self.save()
                    return True
                else:
                    self._return_drag_to_source()
                    return True

            h_rect = self._hook_rect()
            if h_rect.collidepoint(pos):
                is_hook = get_item_def(self.drag_item["id"]).get("is_hook", False)
                if is_hook:
                    temp = self.hook_slot.copy()
                    self.hook_slot = self.drag_item.copy()
                    if temp["id"]:
                        self.drag_item = temp
                    else:
                        self.drag_item = None
                        self.drag_source = None
                    self.save()
                    return True
                else:
                    self._return_drag_to_source()
                    return True

            p_rect = self._pet_rect()
            if p_rect.collidepoint(pos):
                is_pet = get_item_def(self.drag_item["id"]).get("is_pet", False)
                if is_pet:
                    temp = self.pet_slot.copy()
                    self.pet_slot = self.drag_item.copy()
                    if temp["id"]:
                        self.drag_item = temp
                    else:
                        self.drag_item = None
                        self.drag_source = None
                    self.save()
                    return True
                else:
                    self._return_drag_to_source()
                    return True

            for i in range(self.slots):
                rect = self._slot_rect(i)
                if rect.collidepoint(pos):
                    target = self.data[i]
                    if target["id"] is None:
                        target["id"], target["count"] = self.drag_item["id"], self.drag_item["count"]
                    elif target["id"] == self.drag_item["id"]:
                        max_s = get_item_def(self.drag_item["id"]).get("max_stack", MAX_STACK)
                        space = max_s - target["count"]
                        added = min(self.drag_item["count"], space)
                        target["count"] += added
                        self.drag_item["count"] -= added
                        if self.drag_item["count"] > 0:
                            self._return_drag_to_source()
                            return True
                    else:
                        temp_id, temp_count = target["id"], target["count"]
                        target["id"], target["count"] = self.drag_item["id"], self.drag_item["count"]
                        self.drag_item["id"], self.drag_item["count"] = temp_id, temp_count
                        self._return_drag_to_source()
                        return True
                    
                    self.drag_item = None
                    self.drag_source = None
                    self.save()
                    return True
                    
        self._return_drag_to_source()
        return True

    def _return_drag_to_source(self) -> None:
        if not self.drag_item: return

        if self.drag_source == "creative":
            self.drag_item = None
            self.drag_source = None
            return
        
        if self.drag_source == "armor":
            self.armor_slot = self.drag_item.copy()
        elif self.drag_source == "boots":
            self.boots_slot = self.drag_item.copy()
        elif self.drag_source == "hook":
            self.hook_slot = self.drag_item.copy()
        elif self.drag_source == "pet":
            self.pet_slot = self.drag_item.copy()
        elif isinstance(self.drag_source, int):
            self.data[self.drag_source] = self.drag_item.copy()
            
        self.drag_item = None
        self.drag_source = None
        self.save()

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]) -> None:
        visible_slots = self.slots if self.show_full else HOTBAR_SLOTS
        hovered_item_id = None

        if self.show_full:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            surface.blit(overlay, (0, 0))

            a_rect = self._armor_rect()
            pygame.draw.rect(surface, UI_SLOT_BG, a_rect)
            
            color = UI_SLOT_HOVER if a_rect.collidepoint(mouse_pos) else UI_SLOT_BORDER
            pygame.draw.rect(surface, color, a_rect, 2)
            
            font = pygame.font.SysFont(None, 24)
            lbl = font.render("Armor slot", True, WHITE)
            surface.blit(lbl, (a_rect.x - 5, a_rect.y - 25))

            if self.armor_slot["id"]:
                self._draw_item_at(surface, self.armor_slot, a_rect.x, a_rect.y)
                if a_rect.collidepoint(mouse_pos):
                    hovered_item_id = self.armor_slot["id"]

            b_rect = self._boots_rect()
            pygame.draw.rect(surface, UI_SLOT_BG, b_rect)
            
            b_color = UI_SLOT_HOVER if b_rect.collidepoint(mouse_pos) else UI_SLOT_BORDER
            pygame.draw.rect(surface, b_color, b_rect, 2)
            
            lbl_b = font.render("Boots slot", True, WHITE)
            surface.blit(lbl_b, (b_rect.x - 5, b_rect.y - 25))

            if self.boots_slot["id"]:
                self._draw_item_at(surface, self.boots_slot, b_rect.x, b_rect.y)
                if b_rect.collidepoint(mouse_pos):
                    hovered_item_id = self.boots_slot["id"]

            h_rect = self._hook_rect()
            pygame.draw.rect(surface, UI_SLOT_BG, h_rect)
            
            h_color = UI_SLOT_HOVER if h_rect.collidepoint(mouse_pos) else UI_SLOT_BORDER
            pygame.draw.rect(surface, h_color, h_rect, 2)
            
            lbl_h = font.render("Hook slot", True, WHITE)
            surface.blit(lbl_h, (h_rect.x - 5, h_rect.y - 25))

            if self.hook_slot["id"]:
                self._draw_item_at(surface, self.hook_slot, h_rect.x, h_rect.y)
                if h_rect.collidepoint(mouse_pos):
                    hovered_item_id = self.hook_slot["id"]

            p_rect = self._pet_rect()
            pygame.draw.rect(surface, UI_SLOT_BG, p_rect)
            
            p_color = UI_SLOT_HOVER if p_rect.collidepoint(mouse_pos) else UI_SLOT_BORDER
            pygame.draw.rect(surface, p_color, p_rect, 2)
            
            lbl_p = font.render("Pet slot", True, WHITE)
            surface.blit(lbl_p, (p_rect.x - 5, p_rect.y - 25))

            if self.pet_slot["id"]:
                self._draw_item_at(surface, self.pet_slot, p_rect.x, p_rect.y)
                if p_rect.collidepoint(mouse_pos):
                    hovered_item_id = self.pet_slot["id"]

            recipe = BASIC_RECIPES[0] 
            craft_rect = self._craft_button_rect()
            can_craft = all(self.count_item(item_id) >= cnt for item_id, cnt in recipe["req"].items())

            btn_color = (50, 90, 50) if can_craft else (70, 40, 40)
            if craft_rect.collidepoint(mouse_pos) and can_craft:
                btn_color = (70, 120, 70)

            pygame.draw.rect(surface, btn_color, craft_rect)
            pygame.draw.rect(surface, UI_SLOT_BORDER, craft_rect, 1)

            font_craft = pygame.font.SysFont(None, 24)
            result_def = get_item_def(recipe["result"])
            req_str = ", ".join(
                f"{get_item_def(iid).get('name', iid)}: {cnt}"
                for iid, cnt in recipe["req"].items()
            )
            label = f"[Craft] {result_def.get('name', recipe['result'])} x{recipe['yield']}  |  {req_str}"
            if not can_craft:
                label += "  (недостатньо ресурсів)"
            txt = font_craft.render(label, True, WHITE)
            surface.blit(txt, (craft_rect.x + 10, craft_rect.y + (craft_rect.height - txt.get_height()) // 2))

        for i in range(visible_slots):
            rect = self._slot_rect(i)
            pygame.draw.rect(surface, UI_SLOT_BG, rect)
            
            color = UI_SLOT_BORDER
            if i == self.selected_slot and not self.show_full:
                color = (255, 255, 0)
            elif rect.collidepoint(mouse_pos):
                if self.show_full:
                    color = UI_SLOT_HOVER
                if self.data[i]["id"]:
                    hovered_item_id = self.data[i]["id"]
            
            pygame.draw.rect(surface, color, rect, 2)

            if self.data[i]["id"]:
                self._draw_item_at(surface, self.data[i], rect.x, rect.y)

        if self.drag_item:
            mx, my = mouse_pos
            self._draw_item_at(surface, self.drag_item, mx - SLOT_SIZE // 2, my - SLOT_SIZE // 2)

        if hovered_item_id and not self.drag_item:
            item_name = get_item_def(hovered_item_id).get("name", hovered_item_id)
            font = pygame.font.SysFont(None, 26)
            text = font.render(item_name, True, WHITE)
            
            mx, my = mouse_pos
            bg_rect = pygame.Rect(mx + 15, my + 15, text.get_width() + 12, text.get_height() + 8)
            
            if bg_rect.right > WIDTH:
                bg_rect.x = WIDTH - bg_rect.width - 5
            if bg_rect.bottom > HEIGHT:
                bg_rect.y = HEIGHT - bg_rect.height - 5
                
            pygame.draw.rect(surface, (30, 30, 35), bg_rect)
            pygame.draw.rect(surface, (100, 100, 120), bg_rect, 1)
            surface.blit(text, (bg_rect.x + 6, bg_rect.y + 4))

    def _draw_item_at(self, surface: pygame.Surface, item: dict, x: int, y: int) -> None:
        item_id = item["id"]
        
        # --- 1. СПРОБА ЗАВАНТАЖИТИ PNG З ПАПКИ pics/sprites/ ---
        if item_id not in Inventory._icon_cache:
            path = resource_path(os.path.join("pics", "sprites", f"{item_id}.png"))
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (SLOT_SIZE - 8, SLOT_SIZE - 8))
                Inventory._icon_cache[item_id] = img
            elif item_id in Inventory.PROCEDURAL_TEXTURES:
                img = Inventory._render_pixel_art(Inventory.PROCEDURAL_TEXTURES[item_id], SLOT_SIZE - 8)
                Inventory._icon_cache[item_id] = img
            else:
                Inventory._icon_cache[item_id] = None # Позначаємо, що картинки нема
                
        img = Inventory._icon_cache[item_id]
        
        if img:
            surface.blit(img, (x + 4, y + 4))
        else:
            # --- 3. РЕЗЕРВНИЙ ВАРІАНТ (кольорові квадрати) ---
            item_def = get_item_def(item_id)
            color = item_def.get("color", (255, 0, 255))
            border = item_def.get("border_color", (0, 0, 0))

            m = 4
            pygame.draw.rect(surface, color, (x + m, y + m, SLOT_SIZE - m*2, SLOT_SIZE - m*2))
            pygame.draw.rect(surface, border, (x + m, y + m, SLOT_SIZE - m*2, SLOT_SIZE - m*2), 2)

        # Малюємо кількість (якщо більше 1)
        if item["count"] > 1:
            font = pygame.font.SysFont(None, 24)
            text = font.render(str(item["count"]), True, WHITE)
            surface.blit(text, (x + SLOT_SIZE - text.get_width() - 2, y + SLOT_SIZE - text.get_height() - 2))