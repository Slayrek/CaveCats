import pygame
import sys
import os
import json
from src.core.settings import WIDTH, HEIGHT, FPS, WHITE
from src.ui.main_menu import Button

class LeaderboardScreen:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        
        self.font_title = pygame.font.SysFont("impact", 60)
        self.font_text = pygame.font.SysFont("arial", 24, bold=True)
        self.font_btn = pygame.font.SysFont("arial", 24, bold=True)
        self.font_item = pygame.font.SysFont("consolas", 22)

        self.btn_back = Button(20, 20, 100, 40, "Back", self.font_btn)
        
        self.records = []
        self.delete_buttons = []
        self.load_records()

    def load_records(self):
        lb_path = os.path.join("data", "leaderboard.json")
        if os.path.exists(lb_path):
            try:
                with open(lb_path, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except:
                self.records = []
        else:
            self.records = []
            
        # Sort by time
        self.records.sort(key=lambda x: x.get("time", 999999))
        self.update_buttons()

    def save_records(self):
        lb_path = os.path.join("data", "leaderboard.json")
        os.makedirs("data", exist_ok=True)
        with open(lb_path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=4)

    def update_buttons(self):
        self.delete_buttons = []
        start_y = 150
        for i in range(len(self.records)):
            # Delete button (small square)
            btn = Button(WIDTH - 150, start_y + i * 40, 30, 30, "X", self.font_btn)
            btn.base_color = (200, 50, 50)
            btn.hover_color = (255, 100, 100)
            self.delete_buttons.append(btn)

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        ms = int((seconds * 100) % 100)
        return f"{mins:02}:{secs:02}.{ms:02}"

    def run(self):
        self.load_records()
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
                if self.btn_back.rect.collidepoint(mouse_pos):
                    return "back"
                
                # Check delete buttons
                to_delete = -1
                for i, btn in enumerate(self.delete_buttons):
                    if btn.rect.collidepoint(mouse_pos):
                        to_delete = i
                        break
                
                if to_delete != -1:
                    self.records.pop(to_delete)
                    self.save_records()
                    self.update_buttons()

            self.screen.fill((30, 30, 40))
            
            title = self.font_title.render("SPEEDRUN RECORDS", True, (255, 200, 50))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
            
            # Header
            header = self.font_text.render(f"{'#':<5}{'World':<20}{'Date':<15}Time", True, (200, 200, 200))
            self.screen.blit(header, (150, 110))
            pygame.draw.line(self.screen, (100, 100, 100), (150, 140), (WIDTH - 150, 140), 2)

            # List
            start_y = 150
            if not self.records:
                empty_txt = self.font_text.render("No records yet! Finish a Speedrun world to appear here.", True, (150, 150, 150))
                self.screen.blit(empty_txt, (WIDTH//2 - empty_txt.get_width()//2, 250))
            else:
                for i, rec in enumerate(self.records[:10]): # Show top 10
                    rank_str = f"{i+1}."
                    world_name = rec.get("world", "Unknown")[:18]
                    date_str = rec.get("date", "----")
                    t_str = self.format_time(rec.get("time", 0))
                    
                    row_str = f"{rank_str:<5}{world_name:<20}{date_str:<15}{t_str}"
                    # Highlight top 3
                    color = WHITE
                    if i == 0: color = (255, 215, 0)
                    elif i == 1: color = (192, 192, 192)
                    elif i == 2: color = (205, 127, 50)
                        
                    txt = self.font_item.render(row_str, True, color)
                    self.screen.blit(txt, (150, start_y + i * 40 + 5))
                    
                    self.delete_buttons[i].draw(self.screen, mouse_pos)

            self.btn_back.draw(self.screen, mouse_pos)

            pygame.display.flip()
