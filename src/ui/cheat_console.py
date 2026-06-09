# ============================================================
#  cheat_console.py — Консоль розробника
# ============================================================

import pygame
from src.items.items import ITEM_DEFS

class CheatConsole:
    def __init__(self, inventory):
        self.inventory = inventory
        self.cat = None  
        self.bosses_group = None 
        self.mobs_group = None # <--- Група мобів
        self.is_open = False
        self.input_text = ""
        self.font = pygame.font.SysFont("consolas", 24)

    def toggle(self):
        self.is_open = not self.is_open
        if self.is_open:
            self.input_text = ""

    def handle_event(self, event):
        if not self.is_open: return False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.execute(self.input_text)
                self.input_text = ""
                self.is_open = False
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.is_open = False
            else:
                self.input_text += event.unicode
        return True

    def execute(self, command):
        parts = command.split()
        if not parts: return
        cmd = parts[0].lower()

        # Старий добрий give
        if cmd == "give" and len(parts) >= 3:
            item_id = parts[1]
            try:
                count = int(parts[2])
                if item_id in ITEM_DEFS:
                    self.inventory.add_item(item_id, count)
                    print(f"[Console] Gave {count}x {item_id}")
            except ValueError:
                pass
                
        # --- ЧІТ: ШВИДКІСТЬ ---
        elif cmd == "speed" and len(parts) >= 2:
            if self.cat:
                try:
                    new_speed = float(parts[1])
                    self.cat.speed = new_speed
                    print(f"[Console] Speed set to {new_speed}")
                except ValueError:
                    pass
                    
        # --- ЧІТ: ПОЛІТ (NOCLIP) ---
        elif cmd == "noclip" and len(parts) >= 2:
            if self.cat:
                mode = parts[1].lower()
                if mode == "on":
                    self.cat.noclip = True
                    print("[Console] Noclip ON")
                elif mode == "off":
                    self.cat.noclip = False
                    print("[Console] Noclip OFF")
                    
        # --- НОВИЙ ЧІТ: SPAWN ---
        elif cmd == "spawn" and len(parts) >= 2:
            mob = parts[1].lower()
            if not self.cat: return
            
            spawn_x = self.cat.hitbox.centerx + 150
            spawn_y = self.cat.hitbox.centery - 200
            
            if mob == "gargoyle" and self.bosses_group is not None:
                from src.entities.bosses import Gargoyle 
                boss = Gargoyle(spawn_x, spawn_y, self.cat.world, self.cat.drops_group)
                self.bosses_group.add(boss)
                print("[Console] Spawned Gargoyle!")
                
            elif self.mobs_group is not None:
                from src.entities.mobs import Bat, Slime, ZombieCat
                if mob == "bat":
                    self.mobs_group.add(Bat(spawn_x, spawn_y, self.cat.world, self.cat.drops_group))
                    print("[Console] Spawned Bat!")
                elif mob == "slime":
                    self.mobs_group.add(Slime(spawn_x, spawn_y, self.cat.world, self.cat.drops_group))
                    print("[Console] Spawned Slime!")
                elif mob in ("zombie", "zombie_cat"):
                    self.mobs_group.add(ZombieCat(spawn_x, spawn_y, self.cat.world, self.cat.drops_group))
                    print("[Console] Spawned Zombie Cat!")

    def update(self):
        pass

    def draw(self, surface):
        if not self.is_open: return
        pygame.draw.rect(surface, (30, 30, 40, 220), (0, 0, surface.get_width(), 40))
        txt_surf = self.font.render("> " + self.input_text, True, (100, 255, 100))
        surface.blit(txt_surf, (10, 10))