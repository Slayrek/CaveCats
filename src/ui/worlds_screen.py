import pygame
import sys
from src.core.settings import WIDTH, HEIGHT, FPS, WHITE
from src.ui.main_menu import Button

class WorldsScreen:
    def __init__(self, screen, manager):
        self.screen = screen
        self.manager = manager
        self.clock = pygame.time.Clock()
        
        self.font_title = pygame.font.SysFont("impact", 60)
        self.font_text = pygame.font.SysFont("arial", 24, bold=True)
        self.font_btn = pygame.font.SysFont("arial", 24, bold=True)

        self.btn_back = Button(20, 20, 100, 40, "Back", self.font_btn)
        
        self.save_list_rect = pygame.Rect(WIDTH//2 - 250, 150, 500, 300)
        
        btn_y = 480
        self.btn_play = Button(WIDTH//2 - 250, btn_y, 150, 50, "Play", self.font_btn)
        self.btn_new = Button(WIDTH//2 - 80, btn_y, 160, 50, "New World", self.font_btn)
        self.btn_delete = Button(WIDTH//2 + 100, btn_y, 150, 50, "Delete", self.font_btn)
        
        self.selected_save = manager.active_save

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

            saves = self.manager.list_saves()
            if self.selected_save not in saves and saves:
                self.selected_save = saves[0]

            if mouse_clicked:
                if self.btn_back.rect.collidepoint(mouse_pos):
                    return "back"
                
                if self.btn_play.rect.collidepoint(mouse_pos) and self.selected_save:
                    self.manager.active_save = self.selected_save
                    return "play"
                    
                if self.btn_new.rect.collidepoint(mouse_pos):
                    return "new_world"
                    
                if self.btn_delete.rect.collidepoint(mouse_pos) and self.selected_save:
                    if self.selected_save != "default":
                        self.manager.delete_save(self.selected_save)
                        if saves: self.selected_save = saves[0]
                        else: self.selected_save = None

                for i, s_name in enumerate(saves):
                    s_rect = pygame.Rect(self.save_list_rect.x + 10, self.save_list_rect.y + 10 + i*40, self.save_list_rect.width - 20, 35)
                    if s_rect.collidepoint(mouse_pos):
                        self.selected_save = s_name

            self.screen.fill((30, 30, 40))
            
            title = self.font_title.render("SELECT WORLD", True, (255, 200, 50))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

            self.btn_back.draw(self.screen, mouse_pos)

            pygame.draw.rect(self.screen, (45, 45, 55), self.save_list_rect, border_radius=10)
            pygame.draw.rect(self.screen, (100, 100, 120), self.save_list_rect, 2, border_radius=10)

            for i, s_name in enumerate(saves):
                s_rect = pygame.Rect(self.save_list_rect.x + 10, self.save_list_rect.y + 10 + i*40, self.save_list_rect.width - 20, 35)
                color = (80, 120, 200) if s_name == self.selected_save else (60, 60, 70)
                pygame.draw.rect(self.screen, color, s_rect, border_radius=5)
                st = self.font_btn.render(s_name, True, WHITE)
                self.screen.blit(st, (s_rect.x + 10, s_rect.y + 5))

            self.btn_play.draw(self.screen, mouse_pos)
            self.btn_new.draw(self.screen, mouse_pos)
            self.btn_delete.draw(self.screen, mouse_pos)

            pygame.display.flip()
