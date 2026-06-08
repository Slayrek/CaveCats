# ============================================================
#  main_menu.py — Головне меню (2.5D стиль за ескізом)
# ============================================================

import pygame
import sys
import math
from src.core.settings import WIDTH, HEIGHT, FPS, WHITE, BLACK

class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = (60, 60, 70)
        self.hover_color = (100, 150, 255)
        self.text_color = WHITE
        self.hover_text_color = (255, 255, 200)

    def draw(self, surface, mouse_pos):
        is_hovered = self.rect.collidepoint(mouse_pos)
        color = self.hover_color if is_hovered else self.base_color
        txt_color = self.hover_text_color if is_hovered else self.text_color
        
        # Трохи збільшуємо кнопку при наведенні
        if is_hovered:
            draw_rect = self.rect.inflate(10, 10)
        else:
            draw_rect = self.rect

        # Тінь
        shadow_rect = draw_rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(surface, (30, 30, 40), shadow_rect, border_radius=15)
        
        # Сама кнопка
        pygame.draw.rect(surface, color, draw_rect, border_radius=15)
        pygame.draw.rect(surface, WHITE, draw_rect, 2, border_radius=15)

        text_surf = self.font.render(self.text, True, txt_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos, mouse_pressed):
        return self.rect.collidepoint(mouse_pos) and mouse_pressed[0]

class MainMenu:
    def __init__(self, screen, settings_manager=None):
        self.screen = screen
        self.settings_manager = settings_manager
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("impact", 90)
        self.font_btn = pygame.font.SysFont("arial", 36, bold=True)
        
        self.player_name = "Player"
        if self.settings_manager:
            self.player_name = self.settings_manager.data.get("player_name", "Player")
            
        btn_w, btn_h = 260, 55
        cx = WIDTH // 2 - btn_w // 2
        cy = HEIGHT // 2
        
        # Calculate starting Y to center the block of 6 buttons
        start_y = HEIGHT // 2 - 100
        gap = 70
        
        self.btn_start = Button(cx, start_y, btn_w, btn_h, "Singleplayer", self.font_btn)
        self.btn_multiplayer = Button(cx, start_y + gap, btn_w, btn_h, "Multiplayer", self.font_btn)
        self.btn_settings = Button(cx, start_y + gap*2, btn_w, btn_h, "Settings", self.font_btn)
        self.btn_achievements = Button(cx, start_y + gap*3, btn_w, btn_h, "Achievements", self.font_btn)
        self.btn_leaderboard = Button(cx, start_y + gap*4, btn_w, btn_h, "Records", self.font_btn)
        self.btn_exit = Button(cx, start_y + gap*5, btn_w, btn_h, "Exit Game", self.font_btn)
        
        self.show_exit_confirm = False
        self.btn_confirm_yes = Button(cx - 80, cy + 100, 120, 50, "Yes", self.font_btn)
        self.btn_confirm_no = Button(cx + 160, cy + 100, 120, 50, "No", self.font_btn)
        
        self.state = "main" # main, multiplayer, enter_code, enter_name
        self.btn_name = Button(cx, cy - 80, btn_w, btn_h, f"Name: {self.player_name}", self.font_btn)
        self.btn_host = Button(cx, cy, btn_w, btn_h, "Host Game", self.font_btn)
        self.btn_join = Button(cx, cy + 80, btn_w, btn_h, "Join Game", self.font_btn)
        self.btn_back = Button(cx, cy + 160, btn_w, btn_h, "Back", self.font_btn)
        
        self.room_code_input = ""
        self.name_input = ""

    def draw_topdown_tree(self, x, y):
        # Стовбур (помаранчево-коричневий)
        pygame.draw.rect(self.screen, (210, 105, 30), (x - 15, y, 30, 80), border_radius=10)
        # Листя (світло-зелене)
        pygame.draw.ellipse(self.screen, (120, 220, 120), (x - 40, y - 20, 80, 50))
        pygame.draw.ellipse(self.screen, (100, 200, 100), (x - 30, y - 30, 60, 40))

    def draw_topdown_cat(self, x, y):
        # Тіло
        pygame.draw.circle(self.screen, (150, 150, 160), (x, y), 25)
        # Вуха
        pygame.draw.polygon(self.screen, (150, 150, 160), [(x-15, y-15), (x-25, y-35), (x-5, y-22)])
        pygame.draw.polygon(self.screen, (150, 150, 160), [(x+15, y-15), (x+25, y-35), (x+5, y-22)])
        # Лапки
        pygame.draw.circle(self.screen, (130, 130, 140), (x-25, y+5), 8)
        pygame.draw.circle(self.screen, (130, 130, 140), (x+25, y+5), 8)
        pygame.draw.circle(self.screen, (130, 130, 140), (x-15, y+25), 8)
        pygame.draw.circle(self.screen, (130, 130, 140), (x+15, y+25), 8)
        # Очі і ротик
        pygame.draw.circle(self.screen, BLACK, (x-8, y-5), 4)
        pygame.draw.circle(self.screen, BLACK, (x+8, y-5), 4)
        pygame.draw.line(self.screen, BLACK, (x-4, y+5), (x-2, y+8), 2)
        pygame.draw.line(self.screen, BLACK, (x-2, y+8), (x, y+5), 2)
        pygame.draw.line(self.screen, BLACK, (x, y+5), (x+2, y+8), 2)
        pygame.draw.line(self.screen, BLACK, (x+2, y+8), (x+4, y+5), 2)

    def draw_background(self):
        # Трава
        self.screen.fill((70, 160, 100))
        
        # Ставок (помаранчевий берег + синя вода)
        pond_rect = pygame.Rect(WIDTH//2 - 250, HEIGHT//4 - 100, 500, 200)
        pygame.draw.ellipse(self.screen, (240, 130, 30), pond_rect)
        pygame.draw.ellipse(self.screen, (20, 100, 200), pond_rect.inflate(-40, -40))
        
        # 4 Дерева по кутах (як на ескізі)
        self.draw_topdown_tree(100, 100)
        self.draw_topdown_tree(WIDTH - 100, 100)
        self.draw_topdown_tree(100, HEIGHT - 200)
        self.draw_topdown_tree(WIDTH - 100, HEIGHT - 200)
        
        # Котик
        self.draw_topdown_cat(250, HEIGHT - 150)

    def run(self):
        running = True
        mouse_clicked = False

        while running:
            self.clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.TEXTINPUT:
                    if self.state == "enter_code":
                        if len(self.room_code_input) < 15 and all(c.isdigit() or c == '.' for c in event.text):
                            self.room_code_input += event.text
                    elif self.state == "enter_name":
                        if len(self.name_input) < 12 and event.text.isprintable():
                            self.name_input += event.text
                if event.type == pygame.KEYDOWN:
                    if self.state == "enter_code":
                        if event.key == pygame.K_BACKSPACE:
                            self.room_code_input = self.room_code_input[:-1]
                        elif event.key == pygame.K_RETURN:
                            if len(self.room_code_input) > 0:
                                try: pygame.key.stop_text_input()
                                except: pass
                                return f"join_{self.room_code_input}"
                        else:
                            if not hasattr(pygame, 'TEXTINPUT') and (event.unicode.isdigit() or event.unicode == '.') and len(self.room_code_input) < 15:
                                self.room_code_input += event.unicode
                    elif self.state == "enter_name":
                        if event.key == pygame.K_BACKSPACE:
                            self.name_input = self.name_input[:-1]
                        elif event.key == pygame.K_RETURN:
                            if self.name_input.strip():
                                self.player_name = self.name_input.strip()[:12]
                                if self.settings_manager:
                                    self.settings_manager.data["player_name"] = self.player_name
                                    self.settings_manager.save()
                                self.btn_name.text = f"Name: {self.player_name}"
                            self.state = "multiplayer"
                            try: pygame.key.stop_text_input()
                            except: pass
                        else:
                            if not hasattr(pygame, 'TEXTINPUT') and len(self.name_input) < 12 and event.unicode.isprintable():
                                self.name_input += event.unicode
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_clicked = True

            self.draw_background()

            # --- АНІМОВАНА ТА ХОВЕР НАЗВА ---
            t = pygame.time.get_ticks()
            title_text = "CAVE CATS"
            title_surf = self.font_title.render(title_text, True, WHITE)
            title_rect = title_surf.get_rect(center=(WIDTH//2, 120))
            
            # Якщо миша поруч із назвою - підсвічуємо і збільшуємо
            is_hovered = title_rect.inflate(50, 50).collidepoint(mouse_pos)
            if is_hovered:
                title_surf = self.font_title.render(title_text, True, (255, 200, 50))
                scale_bounce = 1.0 + math.sin(t * 0.01) * 0.05
                new_size = (int(title_rect.width * scale_bounce), int(title_rect.height * scale_bounce))
                title_surf = pygame.transform.scale(title_surf, new_size)
            else:
                # Звичайне плавне погойдування
                offset_y = math.sin(t * 0.003) * 10
                title_rect.y += offset_y
            
            # Тінь для назви
            shadow_surf = self.font_title.render(title_text, True, (40, 40, 40))
            if is_hovered:
                 shadow_surf = pygame.transform.scale(shadow_surf, new_size)
            
            shadow_rect = shadow_surf.get_rect(center=(title_rect.centerx + 4, title_rect.centery + 4))
            self.screen.blit(shadow_surf, shadow_rect)
            self.screen.blit(title_surf, title_surf.get_rect(center=title_rect.center))

            if self.show_exit_confirm:
                # Малюємо затемнення
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 180))
                self.screen.blit(overlay, (0, 0))
                
                # Попап
                popup_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 100, 400, 200)
                pygame.draw.rect(self.screen, (50, 50, 60), popup_rect, border_radius=15)
                pygame.draw.rect(self.screen, WHITE, popup_rect, 2, border_radius=15)
                
                text_surf = self.font_btn.render("Are you sure?", True, WHITE)
                text_rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 40))
                self.screen.blit(text_surf, text_rect)
                
                self.btn_confirm_yes.draw(self.screen, mouse_pos)
                self.btn_confirm_no.draw(self.screen, mouse_pos)
                
            elif self.state == "main":
                self.btn_start.draw(self.screen, mouse_pos)
                self.btn_multiplayer.draw(self.screen, mouse_pos)
                self.btn_settings.draw(self.screen, mouse_pos)
                self.btn_achievements.draw(self.screen, mouse_pos)
                self.btn_leaderboard.draw(self.screen, mouse_pos)
                self.btn_exit.draw(self.screen, mouse_pos)
                
            elif self.state == "multiplayer":
                self.btn_name.draw(self.screen, mouse_pos)
                self.btn_host.draw(self.screen, mouse_pos)
                self.btn_join.draw(self.screen, mouse_pos)
                self.btn_back.draw(self.screen, mouse_pos)
                
            elif self.state == "enter_code":
                # Popup for code entry
                popup_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 120, 400, 260)
                pygame.draw.rect(self.screen, (50, 50, 60), popup_rect, border_radius=15)
                pygame.draw.rect(self.screen, WHITE, popup_rect, 2, border_radius=15)
                
                prompt = self.font_btn.render("Enter Host IP:", True, WHITE)
                text_rect = prompt.get_rect(center=(WIDTH//2, HEIGHT//2 - 70))
                self.screen.blit(prompt, text_rect)
                
                code_surf = self.font_title.render(self.room_code_input + ("_" if (t//500)%2==0 else " "), True, (255, 200, 50))
                code_rect = code_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
                self.screen.blit(code_surf, code_rect)
                
                # Connect Button
                if not hasattr(self, 'btn_connect'):
                    self.btn_connect = Button(WIDTH//2 - 130, HEIGHT//2 + 60, 120, 50, "Connect", self.font_btn)
                self.btn_connect.draw(self.screen, mouse_pos)
                
                # Back Button
                self.btn_back.rect.x = WIDTH//2 + 10
                self.btn_back.rect.y = HEIGHT//2 + 60
                self.btn_back.rect.width = 120
                self.btn_back.rect.height = 50
                self.btn_back.draw(self.screen, mouse_pos)
                
            elif self.state == "enter_name":
                # Popup for name entry
                popup_rect = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 120, 400, 260)
                pygame.draw.rect(self.screen, (50, 50, 60), popup_rect, border_radius=15)
                pygame.draw.rect(self.screen, WHITE, popup_rect, 2, border_radius=15)
                
                text_surf = self.font_btn.render("Enter Nickname:", True, WHITE)
                text_rect = text_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 70))
                self.screen.blit(text_surf, text_rect)
                
                name_surf = self.font_btn.render(self.name_input + ("_" if (t//500)%2==0 else " "), True, (255, 200, 50))
                name_rect = name_surf.get_rect(center=(WIDTH//2, HEIGHT//2))
                self.screen.blit(name_surf, name_rect)
                
                # Save Button
                if not hasattr(self, 'btn_save_name'):
                    self.btn_save_name = Button(WIDTH//2 - 60, HEIGHT//2 + 60, 120, 50, "Save", self.font_btn)
                self.btn_save_name.draw(self.screen, mouse_pos)

            if mouse_clicked:
                if self.show_exit_confirm:
                    if self.btn_confirm_yes.rect.collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                    elif self.btn_confirm_no.rect.collidepoint(mouse_pos):
                        self.show_exit_confirm = False
                elif self.state == "main":
                    if self.btn_start.rect.collidepoint(mouse_pos):
                        return "start"
                    if self.btn_multiplayer.rect.collidepoint(mouse_pos):
                        self.state = "multiplayer"
                    if self.btn_achievements.rect.collidepoint(mouse_pos):
                        return "achievements"
                    if self.btn_settings.rect.collidepoint(mouse_pos):
                        return "settings"
                    if self.btn_leaderboard.rect.collidepoint(mouse_pos):
                        return "leaderboard"
                    if self.btn_exit.rect.collidepoint(mouse_pos):
                        self.show_exit_confirm = True
                elif self.state == "multiplayer":
                    if self.btn_name.rect.collidepoint(mouse_pos):
                        self.state = "enter_name"
                        self.name_input = self.player_name
                        try: pygame.key.start_text_input()
                        except: pass
                    if self.btn_host.rect.collidepoint(mouse_pos):
                        return "host"
                    if self.btn_join.rect.collidepoint(mouse_pos):
                        self.state = "enter_code"
                        try: pygame.key.start_text_input()
                        except: pass
                    if self.btn_back.rect.collidepoint(mouse_pos):
                        self.state = "main"
                elif self.state == "enter_code":
                    if hasattr(self, 'btn_connect') and self.btn_connect.rect.collidepoint(mouse_pos):
                        if len(self.room_code_input) == 5:
                            try: pygame.key.stop_text_input()
                            except: pass
                            return f"join_{self.room_code_input.upper()}"
                    if self.btn_back.rect.collidepoint(mouse_pos):
                        self.btn_back.rect.x = WIDTH // 2 - 130 # restore roughly
                        self.btn_back.rect.y = HEIGHT//2 + 160
                        self.btn_back.rect.width = 260
                        self.state = "multiplayer"
                        try: pygame.key.stop_text_input()
                        except: pass
                elif self.state == "enter_name":
                    if hasattr(self, 'btn_save_name') and self.btn_save_name.rect.collidepoint(mouse_pos):
                        if self.name_input.strip():
                            self.player_name = self.name_input.strip()[:12]
                            if self.settings_manager:
                                self.settings_manager.data["player_name"] = self.player_name
                                self.settings_manager.save()
                            self.btn_name.text = f"Name: {self.player_name}"
                        self.state = "multiplayer"
                        try: pygame.key.stop_text_input()
                        except: pass
                
                mouse_clicked = False

            pygame.display.flip()