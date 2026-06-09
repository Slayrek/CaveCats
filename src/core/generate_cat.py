# ============================================================
#  generate_cat.py — Окремий скрипт для генерації PNG котика
# ============================================================
import pygame
import math
import os

def create_cat_image():
    # Ініціалізуємо рушій (без створення вікна)
    pygame.display.init()
    
    # Створюємо папку, якщо її немає
    os.makedirs("pics", exist_ok=True)
    
    # Створюємо полотно 64x64 з підтримкою прозорості (SRCALPHA)
    size = 64
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    cx, cy = size // 2, size // 2
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    
    # --- МАЛЮЄМО КОТИКА ---
    # Вуха
    pygame.draw.polygon(surf, WHITE, [(cx - 16, cy - 10), (cx - 4, cy - 18), (cx - 12, cy - 28)])
    pygame.draw.polygon(surf, WHITE, [(cx + 4,  cy - 18), (cx + 16, cy - 10),  (cx + 12, cy - 28)])
    
    # Голова/Тіло
    pygame.draw.circle(surf, WHITE, (cx, cy), 20)
    
    # Очі
    pygame.draw.circle(surf, BLACK, (cx - 6, cy - 4), 4)
    pygame.draw.circle(surf, BLACK, (cx + 8, cy - 4), 4)
    
    # Ротик
    my = cy + 2
    pygame.draw.arc(surf, BLACK, pygame.Rect(cx - 3, my, 8, 8), math.pi, 2 * math.pi, 2)
    pygame.draw.arc(surf, BLACK, pygame.Rect(cx + 5, my, 8, 8), math.pi, 2 * math.pi, 2)
    
    # Задні лапки
    pygame.draw.circle(surf, WHITE, (cx - 10, cy + 18), 6)
    pygame.draw.circle(surf, (200, 200, 200), (cx - 10, cy + 18), 6, 1)
    pygame.draw.circle(surf, WHITE, (cx + 10, cy + 18), 6)
    pygame.draw.circle(surf, (200, 200, 200), (cx + 10, cy + 18), 6, 1)

    # Зберігаємо у файл
    save_path = os.path.join("pics", "cat.png")
    pygame.image.save(surf, save_path)
    print(f"✅ Успіх! Картинку збережено: {save_path}")
    print("🎨 Тепер можеш відкрити її в Photoshop/Paint і відредагувати!")

if __name__ == "__main__":
    create_cat_image()