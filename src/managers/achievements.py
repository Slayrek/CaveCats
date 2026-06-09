# ============================================================
#  achievements.py — Система досягнень
# ============================================================

import pygame
import sys
import json
import os
from src.core.settings import WIDTH, HEIGHT, FPS

ACHIEVEMENTS_FILE = "achievements.json"

# --- ТУТ ДУЖЕ ЛЕГКО ДОДАВАТИ НОВІ АЧІВКИ ---
DEFAULT_ACHIEVEMENTS = {
    "first_steps": {
        "name": "The beginning of a great journey!",
        "description": "Craft a Workbench and a Furnace.",
        "unlocked": False
    },
    "monster_hunter": {
        "name": "Monster Hunter",
        "description": "Defeat the Gargoyle boss.",
        "unlocked": False
    },
    "oneckaxe_cat": {
        "name": "Oneckaxe Cat!!!",
        "description": "Obtain a Titanium Pickaxe.",
        "unlocked": False
    },
    "absolute_power": {
        "name": "Absolute power!",
        "description": "Obtain a Ruby Helmet and a Ruby Sword.",
        "unlocked": False
    },
    "space_program": {
        "name": "Houston, we have a cat!",
        "description": "Successfully launch the spaceship.",
        "unlocked": False
    },
    "what_sword": {
        "name": "WHAT?!",
        "description": "How did you get this sword?!",
        "unlocked": False
    },
    "deep_miner": {
        "name": "Into the Abyss",
        "description": "Reach depth row 100 or deeper.",
        "unlocked": False
    },
    "gold_digger": {
        "name": "Midas",
        "description": "Mine 100 Gold Ore blocks.",
        "unlocked": False
    },
    "chest_looter": {
        "name": "Tomb Raider",
        "description": "Open a chest.",
        "unlocked": False
    },
    "slime_genocide": {
        "name": "Slime Terminator",
        "description": "Defeat 100 Slimes.",
        "unlocked": False
    },
    "zombie_slayer": {
        "name": "Cat-pocalypse Survivor",
        "description": "Defeat 50 Zombie Cats.",
        "unlocked": False
    },
    "alchemist": {
        "name": "Mad Chemist",
        "description": "Brew and drink a potion.",
        "unlocked": False
    },
    "pet_lover": {
        "name": "My Lil' Friend",
        "description": "Equip a pet.",
        "unlocked": False
    },
    "lava_fisherman": {
        "name": "Extremely Hot Catch",
        "description": "Catch a fish in lava.",
        "unlocked": False
    },
    "lava_survivor": {
        "name": "Floor is Lava",
        "description": "Stay in lava for 5 seconds without dying.",
        "unlocked": False
    }
}

class AchievementManager:
    def __init__(self):
        self.data = self._load()
        
        self.active_popup = None
        self.popup_timer = 0
        self.popup_duration = 600  
        self.fade_duration = 60    
        
        self.font_title = pygame.font.SysFont("arial", 20, bold=True)
        self.font_desc = pygame.font.SysFont("arial", 15)

    def _load(self):
        if os.path.exists(ACHIEVEMENTS_FILE):
            try:
                with open(ACHIEVEMENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in DEFAULT_ACHIEVEMENTS.items():
                        if k not in data["achievements"]:
                            data["achievements"][k] = v
                    return data
            except:
                pass
        
        return {
            "achievements": DEFAULT_ACHIEVEMENTS.copy(),
            "progress": {} 
        }

    def save(self):
        with open(ACHIEVEMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def unlock(self, ach_id):
        ach = self.data["achievements"].get(ach_id)
        if ach and not ach["unlocked"]:
            ach["unlocked"] = True
            self.save()
            self._show_popup(ach)

    def check_event(self, event_type, value):
        prog = self.data["progress"]
        changed = False

        if event_type == "boss_kill" and value == "gargoyle":
            self.unlock("monster_hunter")
        elif event_type == "launch" and value == "rocket":
            self.unlock("space_program")
        elif event_type == "depth_reached":
            if value >= 100:
                self.unlock("deep_miner")
        elif event_type == "chest_opened":
            self.unlock("chest_looter")
        elif event_type == "potion_consumed":
            self.unlock("alchemist")
        elif event_type == "lava_fish":
            self.unlock("lava_fisherman")
        elif event_type == "lava_time":
            if value >= 5:
                self.unlock("lava_survivor")
        elif event_type == "mob_kill":
            if value == "slime":
                prog["slimes_killed"] = prog.get("slimes_killed", 0) + 1
                changed = True
                if prog["slimes_killed"] >= 100:
                    self.unlock("slime_genocide")
            elif value == "zombie_cat":
                prog["zombies_killed"] = prog.get("zombies_killed", 0) + 1
                changed = True
                if prog["zombies_killed"] >= 50:
                    self.unlock("zombie_slayer")
        elif event_type == "gold_mined":
            prog["gold_mined"] = prog.get("gold_mined", 0) + value
            changed = True
            if prog["gold_mined"] >= 100:
                self.unlock("gold_digger")

        if changed:
            self.save()

    def check_inventory(self, inventory):
        """НОВИЙ МЕТОД: Перевіряє інвентар і видає ачівки за наявність предметів"""
        prog = self.data["progress"]
        changed = False
        
        # Перевіряємо верстак
        if not prog.get("has_workbench") and inventory.count_item("workbench") > 0:
            prog["has_workbench"] = True
            changed = True
            
        # Перевіряємо пічку
        if not prog.get("has_furnace") and inventory.count_item("furnace") > 0:
            prog["has_furnace"] = True
            changed = True
            
        # Перевіряємо рубіновий шолом (може бути в інвентарі або вже одягнений)
        if not prog.get("has_ruby_helmet") and (inventory.count_item("ruby_helmet") > 0 or inventory.armor_slot["id"] == "ruby_helmet"):
            prog["has_ruby_helmet"] = True
            changed = True
            
        # Перевіряємо рубіновий меч
        if not prog.get("has_ruby_sword") and inventory.count_item("ruby_sword") > 0:
            prog["has_ruby_sword"] = True
            changed = True
            
        # Перевіряємо титанову кірку
        if not prog.get("has_titanium_pickaxe") and inventory.count_item("titanium_pickaxe") > 0:
            prog["has_titanium_pickaxe"] = True
            changed = True

        # --- НОВЕ: Перевіряємо OVERPOWERED_SWORD666 ---
        if not prog.get("has_op_sword") and inventory.count_item("OVERPOWERED_SWORD666") > 0:
            prog["has_op_sword"] = True
            changed = True

        if not prog.get("has_pet") and inventory.pet_slot.get("id"):
            prog["has_pet"] = True
            changed = True

        # Зберігаємо файл лише якщо знайшли щось нове
        if changed:
            self.save()
            
        # --- РОЗБЛОКУВАННЯ АЧІВОК ---
        if prog.get("has_workbench") and prog.get("has_furnace"):
            self.unlock("first_steps")
            
        if prog.get("has_ruby_helmet") and prog.get("has_ruby_sword"):
            self.unlock("absolute_power")
            
        if prog.get("has_titanium_pickaxe"):
            self.unlock("oneckaxe_cat")

        # --- РОЗБЛОКУВАННЯ СЕКРЕТНОЇ АЧІВКИ ---
        if prog.get("has_op_sword"):
            self.unlock("what_sword")

        if prog.get("has_pet"):
            self.unlock("pet_lover")

    def _show_popup(self, ach_data):
        self.active_popup = ach_data
        self.popup_timer = self.popup_duration

    def update(self):
        if self.popup_timer > 0:
            self.popup_timer -= 1

    def draw(self, surface):
        if self.popup_timer <= 0 or not self.active_popup:
            return

        alpha = 255
        if self.popup_timer < self.fade_duration:
            alpha = int(255 * (self.popup_timer / self.fade_duration))

        popup_w, popup_h = 320, 70
        x = WIDTH - popup_w - 20 
        y = 20                   

        surf = pygame.Surface((popup_w, popup_h), pygame.SRCALPHA)
        
        pygame.draw.rect(surf, (40, 40, 45, alpha), (0, 0, popup_w, popup_h), border_radius=10)
        pygame.draw.rect(surf, (255, 200, 50, alpha), (0, 0, popup_w, popup_h), 2, border_radius=10)

        pygame.draw.circle(surf, (255, 200, 50, alpha), (35, 35), 20)
        pygame.draw.circle(surf, (255, 255, 255, alpha), (35, 35), 16)
        
        font_icon = pygame.font.SysFont("arial", 24, bold=True)
        txt_star = font_icon.render("!", True, (255, 200, 50))
        txt_star.set_alpha(alpha)
        surf.blit(txt_star, (31, 20))

        txt_title = self.font_title.render(self.active_popup["name"], True, (255, 255, 255))
        txt_desc = self.font_desc.render(self.active_popup["description"], True, (200, 200, 200))
        
        txt_title.set_alpha(alpha)
        txt_desc.set_alpha(alpha)

        surf.blit(txt_title, (70, 15))
        surf.blit(txt_desc, (70, 40))

        surface.blit(surf, (x, y))

# ============================================================
#  ЕКРАН АЧІВОК (Вікно в меню)
# ============================================================
import math

class AchievementsScreen:
    def __init__(self, screen, ach_manager):
        self.screen = screen
        self.ach_manager = ach_manager
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("impact", 60)
        self.font_item_title = pygame.font.SysFont("arial", 24, bold=True)
        self.font_item_desc = pygame.font.SysFont("arial", 18)
        self.font_btn = pygame.font.SysFont("arial", 30, bold=True)
        self.font_progress = pygame.font.SysFont("arial", 22, bold=True)
        
        self.btn_back_rect = pygame.Rect(20, 20, 120, 50)
        
        # Pagination
        self.current_page = 0
        self.items_per_page = 5
        self.btn_prev_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT - 80, 100, 50)
        self.btn_next_rect = pygame.Rect(WIDTH//2 + 50, HEIGHT - 80, 100, 50)

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            
            achievements_dict = self.ach_manager.data.get("achievements", {})
            ach_items = list(achievements_dict.items())
            total_items = len(ach_items)
            total_pages = max(1, math.ceil(total_items / self.items_per_page))
            
            if self.current_page >= total_pages:
                self.current_page = max(0, total_pages - 1)
                
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        return "back"
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        if self.current_page > 0:
                            self.current_page -= 1
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if self.current_page < total_pages - 1:
                            self.current_page += 1
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_clicked = True
                    
            if mouse_clicked:
                if self.btn_back_rect.collidepoint(mouse_pos):
                    return "back"
                elif self.btn_prev_rect.collidepoint(mouse_pos) and self.current_page > 0:
                    self.current_page -= 1
                elif self.btn_next_rect.collidepoint(mouse_pos) and self.current_page < total_pages - 1:
                    self.current_page += 1
                
            self.screen.fill((30, 30, 40))
            
            # Draw Back Button
            color = (100, 150, 255) if self.btn_back_rect.collidepoint(mouse_pos) else (60, 60, 70)
            pygame.draw.rect(self.screen, (30, 30, 40), self.btn_back_rect.move(0, 4), border_radius=10)
            pygame.draw.rect(self.screen, color, self.btn_back_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255,255,255), self.btn_back_rect, 2, border_radius=10)
            btn_text = self.font_btn.render("Back", True, (255, 255, 255))
            self.screen.blit(btn_text, btn_text.get_rect(center=self.btn_back_rect.center))
            
            # Title
            title_surf = self.font_title.render("ACHIEVEMENTS", True, (255, 200, 50))
            self.screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 30))
            
            # Progress stats
            unlocked_count = sum(1 for _, a in ach_items if a.get("unlocked", False))
            prog_text = f"Unlocked: {unlocked_count} / {total_items} ({int(unlocked_count/total_items*100) if total_items > 0 else 0}%)"
            prog_surf = self.font_progress.render(prog_text, True, (200, 255, 200))
            self.screen.blit(prog_surf, (WIDTH//2 - prog_surf.get_width()//2, 100))
            
            # Progress Bar
            bar_w = 400
            bar_h = 10
            bar_x = WIDTH//2 - bar_w//2
            bar_y = 130
            pygame.draw.rect(self.screen, (50, 50, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=5)
            if total_items > 0:
                fill_w = int((unlocked_count / total_items) * bar_w)
                if fill_w > 0:
                    pygame.draw.rect(self.screen, (100, 255, 100), (bar_x, bar_y, fill_w, bar_h), border_radius=5)
            pygame.draw.rect(self.screen, (200, 200, 200), (bar_x, bar_y, bar_w, bar_h), 2, border_radius=5)

            # Draw Pagination Items
            start_idx = self.current_page * self.items_per_page
            end_idx = min(start_idx + self.items_per_page, total_items)
            page_items = ach_items[start_idx:end_idx]
            
            start_y = 170
            for i, (key, ach) in enumerate(page_items):
                box_rect = pygame.Rect(WIDTH//2 - 300, start_y + i * 90, 600, 80)
                
                unlocked = ach.get("unlocked", False)
                bg_col = (60, 90, 60) if unlocked else (50, 50, 55)
                border_col = (100, 200, 100) if unlocked else (80, 80, 90)
                
                pygame.draw.rect(self.screen, bg_col, box_rect, border_radius=10)
                pygame.draw.rect(self.screen, border_col, box_rect, 2, border_radius=10)
                
                title_col = (255, 255, 255) if unlocked else (150, 150, 150)
                desc_col = (200, 255, 200) if unlocked else (120, 120, 120)
                
                t_surf = self.font_item_title.render(ach["name"], True, title_col)
                d_surf = self.font_item_desc.render(ach["description"], True, desc_col)
                
                self.screen.blit(t_surf, (box_rect.x + 20, box_rect.y + 15))
                self.screen.blit(d_surf, (box_rect.x + 20, box_rect.y + 45))
                
                if unlocked:
                    pygame.draw.circle(self.screen, (255, 200, 50), (box_rect.right - 40, box_rect.centery), 22)
                    pygame.draw.circle(self.screen, (255, 255, 255), (box_rect.right - 40, box_rect.centery), 18)
                    star = self.font_item_title.render("!", True, (255, 200, 50))
                    self.screen.blit(star, star.get_rect(center=(box_rect.right - 40, box_rect.centery)))
                else:
                    pygame.draw.circle(self.screen, (80, 80, 90), (box_rect.right - 40, box_rect.centery), 22)
                    lock = self.font_item_title.render("?", True, (150, 150, 150))
                    self.screen.blit(lock, lock.get_rect(center=(box_rect.right - 40, box_rect.centery)))

            # Pagination Controls
            if total_pages > 1:
                # Prev
                prev_color = (100, 150, 255) if self.btn_prev_rect.collidepoint(mouse_pos) and self.current_page > 0 else (60, 60, 70)
                if self.current_page == 0: prev_color = (40, 40, 50)
                pygame.draw.rect(self.screen, prev_color, self.btn_prev_rect, border_radius=10)
                pygame.draw.rect(self.screen, (200, 200, 200), self.btn_prev_rect, 2, border_radius=10)
                prev_text = self.font_btn.render("◀", True, (255, 255, 255) if self.current_page > 0 else (100, 100, 100))
                self.screen.blit(prev_text, prev_text.get_rect(center=self.btn_prev_rect.center))
                
                # Next
                next_color = (100, 150, 255) if self.btn_next_rect.collidepoint(mouse_pos) and self.current_page < total_pages - 1 else (60, 60, 70)
                if self.current_page == total_pages - 1: next_color = (40, 40, 50)
                pygame.draw.rect(self.screen, next_color, self.btn_next_rect, border_radius=10)
                pygame.draw.rect(self.screen, (200, 200, 200), self.btn_next_rect, 2, border_radius=10)
                next_text = self.font_btn.render("▶", True, (255, 255, 255) if self.current_page < total_pages - 1 else (100, 100, 100))
                self.screen.blit(next_text, next_text.get_rect(center=self.btn_next_rect.center))
                
                # Page indicator
                page_text = f"Page {self.current_page + 1} of {total_pages}"
                page_surf = self.font_progress.render(page_text, True, (200, 200, 200))
                self.screen.blit(page_surf, page_surf.get_rect(center=(WIDTH//2, HEIGHT - 55)))

            pygame.display.flip()