import pygame
import sys
import os
import json
from src.core.settings import WIDTH, HEIGHT, FPS, WHITE
from src.ui.main_menu import Button

class CreateWorldScreen:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.clock = pygame.time.Clock()
        
        self.font_title = pygame.font.SysFont("impact", 60)
        self.font_text = pygame.font.SysFont("arial", 24, bold=True)
        self.font_btn = pygame.font.SysFont("arial", 24, bold=True)

        self.btn_back = Button(20, 20, 100, 40, "Cancel", self.font_btn)
        
        cx = WIDTH // 2
        
        self.input_rect = pygame.Rect(cx - 150, 150, 300, 40)
        self.input_text = "NewWorld"
        self.input_active = False
        
        self.btn_ores = Button(cx - 150, 220, 300, 40, "Ores: Normal", self.font_btn)
        self.btn_hardcore = Button(cx - 150, 280, 300, 40, "Hardcore: OFF", self.font_btn)
        self.btn_mobs = Button(cx - 150, 340, 300, 40, "Mob Rate: 1 (Standard)", self.font_btn)
        self.btn_speedrun = Button(cx - 150, 400, 300, 40, "Speedrun: OFF", self.font_btn)
        
        self.btn_create = Button(cx - 100, 460, 200, 50, "Create!", self.font_btn)
        self.btn_create.base_color = (50, 150, 50)
        self.btn_create.hover_color = (100, 200, 100)


        self.ores = ["Normal", "High"]
        self.ore_idx = 0
        
        self.hardcore = False
        
        self.mobs = ["0 (Peaceful)", "1 (Standard)", "2 (Hardcore)", "3 (Apocalypse)"]
        self.mob_idx = 1
        
        self.speedrun = False

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            mouse_pressed = pygame.mouse.get_pressed()
            mouse_clicked = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_clicked = True
                    if self.input_rect.collidepoint(mouse_pos): self.input_active = True
                    else: self.input_active = False
                    
                if event.type == pygame.KEYDOWN and self.input_active:
                    if event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                    elif len(self.input_text) < 15 and event.unicode.isalnum(): 
                        self.input_text += event.unicode

            if mouse_clicked:
                if self.btn_back.rect.collidepoint(mouse_pos):
                    return "back"
                    
                if self.btn_ores.rect.collidepoint(mouse_pos):
                    self.ore_idx = (self.ore_idx + 1) % len(self.ores)
                    self.btn_ores.text = f"Ores: {self.ores[self.ore_idx]}"
                    
                if self.btn_hardcore.rect.collidepoint(mouse_pos):
                    self.hardcore = not self.hardcore
                    self.btn_hardcore.text = f"Hardcore: {'ON' if self.hardcore else 'OFF'}"
                    # Automatically set mob rate to Hardcore if turned on
                    if self.hardcore:
                        self.mob_idx = 2
                        self.btn_mobs.text = f"Mob Rate: {self.mobs[self.mob_idx]}"
                    
                if self.btn_mobs.rect.collidepoint(mouse_pos):
                    self.mob_idx = (self.mob_idx + 1) % len(self.mobs)
                    self.btn_mobs.text = f"Mob Rate: {self.mobs[self.mob_idx]}"
                    
                if self.btn_speedrun.rect.collidepoint(mouse_pos):
                    self.speedrun = not self.speedrun
                    self.btn_speedrun.text = f"Speedrun: {'ON' if self.speedrun else 'OFF'}"
                    
                if self.btn_create.rect.collidepoint(mouse_pos) and self.input_text.strip():
                    name = self.input_text.strip()
                    self.manager.active_save = name
                    save_path = os.path.join("saves", name)
                    os.makedirs(save_path, exist_ok=True)
                    
                    config = {
                        "ores": self.ores[self.ore_idx],
                        "hardcore": self.hardcore,
                        "mob_rate": self.mob_idx,
                        "speedrun": self.speedrun,
                        "play_time": 0.0
                    }
                    
                    with open(os.path.join(save_path, "world_config.json"), "w") as f:
                        json.dump(config, f, indent=4)
                        
                    return "play"

            self.screen.fill((30, 30, 40))
            
            title = self.font_title.render("CREATE NEW WORLD", True, (255, 200, 50))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

            self.btn_back.draw(self.screen, mouse_pos)

            self.screen.blit(self.font_text.render("World Name:", True, WHITE), (self.input_rect.x, self.input_rect.y - 35))
            pygame.draw.rect(self.screen, (20, 20, 30) if self.input_active else (40, 40, 50), self.input_rect, border_radius=5)
            pygame.draw.rect(self.screen, (255, 200, 50) if self.input_active else (100,100,100), self.input_rect, 2, border_radius=5)
            it = self.font_text.render(self.input_text, True, WHITE)
            self.screen.blit(it, (self.input_rect.x + 10, self.input_rect.y + 5))

            self.btn_ores.draw(self.screen, mouse_pos)
            self.btn_hardcore.draw(self.screen, mouse_pos)
            self.btn_mobs.draw(self.screen, mouse_pos)
            self.btn_speedrun.draw(self.screen, mouse_pos)
            
            if self.input_text.strip():
                self.btn_create.draw(self.screen, mouse_pos)

            pygame.display.flip()
