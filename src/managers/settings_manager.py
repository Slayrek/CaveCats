# ============================================================
#  settings_manager.py — Менеджер сейвів та налаштувань
# ============================================================

import pygame
import json
import os
import shutil
import sys
from src.core.settings import WIDTH, HEIGHT, FPS

SETTINGS_FILE = "settings.json"
SAVES_DIR = "saves"

class SettingsManager:
    def __init__(self):
        if not os.path.exists(SAVES_DIR):
            os.makedirs(SAVES_DIR)
        
        self.data = self._load()
        # Гарантуємо наявність папки для активного сейву
        self.ensure_active_save_exists()

    def _load(self):
        import random
        default_settings = {
            "music_on": True, 
            "sfx_on": True,
            "active_save": "default",
            "player_name": f"Cat_{random.randint(1000, 9999)}"
        }
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in default_settings.items():
                        if k not in data: data[k] = v
                    return data
            except: pass
        return default_settings

    def save(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4)

    def ensure_active_save_exists(self):
        path = os.path.join(SAVES_DIR, self.active_save)
        if not os.path.exists(path):
            os.makedirs(path)

    @property
    def music_on(self): return self.data["music_on"]
    @music_on.setter
    def music_on(self, val): 
        self.data["music_on"] = val
        self.save()

    @property
    def sfx_on(self): return self.data["sfx_on"]
    @sfx_on.setter
    def sfx_on(self, val): 
        self.data["sfx_on"] = val
        self.save()

    @property
    def active_save(self): return self.data["active_save"]
    @active_save.setter
    def active_save(self, val):
        self.data["active_save"] = val
        self.save()
        self.ensure_active_save_exists()

    def list_saves(self):
        return [d for d in os.listdir(SAVES_DIR) if os.path.isdir(os.path.join(SAVES_DIR, d))]

    def delete_save(self, name):
        if name == "default": return # Забороняємо видаляти дефолт
        path = os.path.join(SAVES_DIR, name)
        if os.path.exists(path):
            shutil.rmtree(path)
            if self.active_save == name:
                self.active_save = "default"

# ============================================================
#  ЕКРАН НАЛАШТУВАНЬ (Save System UI)
# ============================================================
class SettingsScreen:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.clock = pygame.time.Clock()
        
        self.font_title = pygame.font.SysFont("impact", 50)
        self.font_text = pygame.font.SysFont("arial", 24, bold=True)
        self.font_btn = pygame.font.SysFont("arial", 20, bold=True)

        self.btn_back_rect = pygame.Rect(20, 20, 100, 40)
        
        self.music_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 50, 30, 30)
        self.sfx_rect = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 + 50, 30, 30)

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            mouse_clicked = False
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_clicked = True

            if mouse_clicked:
                if self.btn_back_rect.collidepoint(mouse_pos): return "back"
                if self.music_rect.collidepoint(mouse_pos): self.manager.music_on = not self.manager.music_on
                if self.sfx_rect.collidepoint(mouse_pos): self.manager.sfx_on = not self.manager.sfx_on

            self.screen.fill((30, 30, 40))
            
            title = self.font_title.render("GAME SETTINGS", True, (255, 200, 50))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

            pygame.draw.rect(self.screen, (60, 60, 70), self.btn_back_rect, border_radius=10)
            bt = self.font_btn.render("Back", True, (255, 255, 255))
            self.screen.blit(bt, bt.get_rect(center=self.btn_back_rect.center))

            m_txt = self.font_text.render(f"Music: {'ON' if self.manager.music_on else 'OFF'}", True, (200, 220, 255))
            s_txt = self.font_text.render(f"SFX: {'ON' if self.manager.sfx_on else 'OFF'}", True, (200, 220, 255))
            self.screen.blit(m_txt, (self.music_rect.right + 20, self.music_rect.y))
            self.screen.blit(s_txt, (self.sfx_rect.right + 20, self.sfx_rect.y))
            pygame.draw.rect(self.screen, (100, 220, 100) if self.manager.music_on else (100,100,100), self.music_rect, border_radius=5)
            pygame.draw.rect(self.screen, (100, 220, 100) if self.manager.sfx_on else (100,100,100), self.sfx_rect, border_radius=5)

            pygame.display.flip()