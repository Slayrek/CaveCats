# ============================================================
#  end_screen.py — Фінальний екран (Космос і літаючий котик)
# ============================================================

import pygame
import sys
import math
import random
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
        
        if is_hovered:
            draw_rect = self.rect.inflate(10, 10)
        else:
            draw_rect = self.rect

        shadow_rect = draw_rect.copy()
        shadow_rect.y += 4
        pygame.draw.rect(surface, (30, 30, 40), shadow_rect, border_radius=15)
        pygame.draw.rect(surface, color, draw_rect, border_radius=15)
        pygame.draw.rect(surface, WHITE, draw_rect, 2, border_radius=15)

        text_surf = self.font.render(self.text, True, txt_color)
        text_rect = text_surf.get_rect(center=draw_rect.center)
        surface.blit(text_surf, text_rect)

class EndScreen:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("impact", 90)
        self.font_subtitle = pygame.font.SysFont("arial", 30, bold=True)
        self.font_btn = pygame.font.SysFont("arial", 36, bold=True)
        
        btn_w, btn_h = 240, 60
        cx = WIDTH // 2 - btn_w // 2
        cy = HEIGHT // 2 + 50
        
        self.btn_restart = Button(cx, cy, btn_w, btn_h, "Restart", self.font_btn)
        self.btn_main_menu = Button(cx, cy + 80, btn_w, btn_h, "Main Menu", self.font_btn)
        
        # Фізика котика "DVD Logo"
        self.cat_x = WIDTH // 2
        self.cat_y = HEIGHT // 2
        # Повільна хаотична швидкість (від 0.5 до 1.5 пікселів за кадр)
        self.cat_vx = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        self.cat_vy = random.choice([-1, 1]) * random.uniform(0.5, 1.5)
        
        # Генерація зірок
        self.stars = [(random.randint(0, WIDTH), random.randint(0, HEIGHT), random.randint(1, 3)) for _ in range(150)]

    def draw_space_cat(self):
        x, y = int(self.cat_x), int(self.cat_y)
        
        # Малюємо котика (як в головному меню)
        pygame.draw.circle(self.screen, (150, 150, 160), (x, y), 25)
        pygame.draw.polygon(self.screen, (150, 150, 160), [(x-15, y-15), (x-25, y-35), (x-5, y-22)])
        pygame.draw.polygon(self.screen, (150, 150, 160), [(x+15, y-15), (x+25, y-35), (x+5, y-22)])
        pygame.draw.circle(self.screen, (130, 130, 140), (x-25, y+5), 8)
        pygame.draw.circle(self.screen, (130, 130, 140), (x+25, y+5), 8)
        pygame.draw.circle(self.screen, (130, 130, 140), (x-15, y+25), 8)
        pygame.draw.circle(self.screen, (130, 130, 140), (x+15, y+25), 8)
        pygame.draw.circle(self.screen, BLACK, (x-8, y-5), 4)
        pygame.draw.circle(self.screen, BLACK, (x+8, y-5), 4)
        pygame.draw.line(self.screen, BLACK, (x-4, y+5), (x-2, y+8), 2)
        pygame.draw.line(self.screen, BLACK, (x-2, y+8), (x, y+5), 2)
        pygame.draw.line(self.screen, BLACK, (x, y+5), (x+2, y+8), 2)
        pygame.draw.line(self.screen, BLACK, (x+2, y+8), (x+4, y+5), 2)
        
        # Малюємо скляну кульку скафандра
        bubble = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(bubble, (200, 240, 255, 60), (50, 50), 45) # Напівпрозора заливка
        pygame.draw.circle(bubble, (255, 255, 255, 180), (50, 50), 45, 3) # Контур скла
        pygame.draw.arc(bubble, (255, 255, 255, 150), (10, 10, 80, 80), math.pi/2 + 0.5, math.pi - 0.5, 4) # Відблиск
        self.screen.blit(bubble, (x - 50, y - 50))

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
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    mouse_clicked = True

            # Рух "DVD лого"
            self.cat_x += self.cat_vx
            self.cat_y += self.cat_vy
            
            # Відбивання від країв екрану (радіус скафандра 45)
            if self.cat_x < 45 or self.cat_x > WIDTH - 45:
                self.cat_vx *= -1
            if self.cat_y < 45 or self.cat_y > HEIGHT - 45:
                self.cat_vy *= -1

            # Малюємо космос і зірки
            self.screen.fill((5, 5, 15)) 
            for sx, sy, s_size in self.stars:
                if random.random() < 0.02: # Ефект мерехтіння
                    pygame.draw.circle(self.screen, WHITE, (sx, sy), s_size + 1)
                else:
                    pygame.draw.circle(self.screen, (150, 150, 180), (sx, sy), s_size)

            self.draw_space_cat()

            # Анімована Назва (з hover ефектом)
            t = pygame.time.get_ticks()
            title_text = "CAVE CATS"
            title_surf = self.font_title.render(title_text, True, WHITE)
            title_rect = title_surf.get_rect(center=(WIDTH//2, 100))
            
            if title_rect.inflate(50, 50).collidepoint(mouse_pos):
                title_surf = self.font_title.render(title_text, True, (255, 200, 50))
                scale_bounce = 1.0 + math.sin(t * 0.01) * 0.05
                new_size = (int(title_rect.width * scale_bounce), int(title_rect.height * scale_bounce))
                title_surf = pygame.transform.scale(title_surf, new_size)
            else:
                title_rect.y += math.sin(t * 0.003) * 10
            
            shadow_surf = self.font_title.render(title_text, True, (60, 60, 80))
            shadow_rect = shadow_surf.get_rect(center=(title_rect.centerx + 4, title_rect.centery + 4))
            if title_rect.inflate(50, 50).collidepoint(mouse_pos):
                 shadow_surf = pygame.transform.scale(shadow_surf, new_size)
                 shadow_rect = shadow_surf.get_rect(center=(title_rect.centerx + 4, title_rect.centery + 4))
            
            self.screen.blit(shadow_surf, shadow_rect)
            self.screen.blit(title_surf, title_surf.get_rect(center=title_rect.center))
            
            # Підзаголовок
            sub_surf = self.font_subtitle.render("MISSION ACCOMPLISHED!", True, (150, 255, 150))
            self.screen.blit(sub_surf, sub_surf.get_rect(center=(WIDTH//2, title_rect.bottom + 40)))

            # Кнопки
            self.btn_restart.draw(self.screen, mouse_pos)
            self.btn_main_menu.draw(self.screen, mouse_pos)

            if mouse_clicked:
                if self.btn_restart.rect.collidepoint(mouse_pos):
                    return "restart"
                if self.btn_main_menu.rect.collidepoint(mouse_pos):
                    return "main_menu"
                mouse_clicked = False
                
            pygame.display.flip()