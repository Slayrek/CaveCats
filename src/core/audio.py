# ============================================================
#  audio.py — Глобальний аудіо-менеджер
# ============================================================

import pygame
import os
from src.core.utils import resource_path

class AudioManager:
    def __init__(self, settings_mgr):
        self.settings = settings_mgr
        self.sounds = {}
        self.current_music = None
        self.music_is_playing = False
        
        # --- СЛОВНИК SFX ---
        self.sfx_files = {
            "craft": "snd/craft.wav",
            "chest_open": "snd/chst_opn.wav",
            "chest_close": "snd/chst_cls.wav",
            "block_break": "snd/bl_br.wav",
            "block_place": "snd/bl_pl.wav",
            "attack": "snd/knf.wav",
            "cat_damage": "snd/cat_dmg.wav",
            "gargoyle_damage": "snd/gorg_dmg.wav",
            "pickaxe": "snd/pix.wav",
            "step": "snd/tiptop.wav"
        }
        
        # --- СЛОВНИК МУЗИКИ ---
        self.music_files = {
            "overworld": "music/overworld.wav",
            "cave": "music/cave.wav",
            "dungeon": "music/dungeon.wav"
        }
        
        # Безпечне завантаження (не крашить гру, якщо файлу ще немає)
        for name, path in self.sfx_files.items():
            full_path = resource_path(path)
            if os.path.exists(full_path):
                self.sounds[name] = pygame.mixer.Sound(full_path)
            else:
                self.sounds[name] = None
                
    def play_sfx(self, name):
        if self.settings.sfx_on and name in self.sounds and self.sounds[name]:
            self.sounds[name].play()
            
    def play_music(self, name):
        if self.current_music == name:
            return # Цей трек вже грає
        
        self.current_music = name
        path = resource_path(self.music_files.get(name, ""))
        
        if self.settings.music_on:
            if path and os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1) # -1 означає безкінечний цикл
                self.music_is_playing = True
            else:
                pygame.mixer.music.stop()
                self.music_is_playing = False
                
    def update(self):
        """Перевіряє, чи не змінилися налаштування музики в меню"""
        if not self.settings.music_on and self.music_is_playing:
            pygame.mixer.music.stop()
            self.music_is_playing = False
            
        elif self.settings.music_on and not self.music_is_playing and self.current_music:
            path = resource_path(self.music_files.get(self.current_music, ""))
            if path and os.path.exists(path):
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1)
                self.music_is_playing = True

# --- Глобальний інтерфейс ---
_mgr = None

def init(settings_mgr):
    global _mgr
    _mgr = AudioManager(settings_mgr)

def play_sfx(name):
    if _mgr: _mgr.play_sfx(name)

def play_music(name):
    if _mgr: _mgr.play_music(name)

def update():
    if _mgr: _mgr.update()