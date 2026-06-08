# ============================================================
#  settings.py — глобальні константи гри
# ============================================================

# --- Екран ---
WIDTH  = 1200
HEIGHT = 800
FPS    = 60

# --- Сітка ---
TILE_SIZE = 40

# --- Фізика ---
GRAVITY       = 0.5
JUMP_POWER    = -10
MAX_FALL_SPEED = 12
PLAYER_SPEED  = 5

# --- Ігрова логіка ---
GROUND_LEVEL    = 3   # рядок, де починається земля
ATTACK_COOLDOWN = 15  # кількість кадрів між ударами / будівництвом

# --- Інвентар ---
INVENTORY_SLOTS = 20
HOTBAR_SLOTS    = 10
MAX_STACK       = 100
CHEST_SLOTS     = 20

# --- UI інвентаря ---
SLOT_SIZE     = 40
SLOT_MARGIN   = 5

# ============================================================
#  Кольори (RGB)
# ============================================================

WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)

# Світ
SKY_BLUE   = (135, 206, 235)
GRASS_GREEN = (34, 139, 34)
DARK_DIRT  = (50,  35,  20)
CAVE_BG    = (25,  15,  10)
STONE_GRAY = (130, 130, 130)
STONE_DARK = (100, 100, 100)
HOUSE_COLOR = (200, 100, 100)

# Дерево
WOOD_BROWN = (139, 90,  43)
WOOD_DARK  = (100, 60,  20)

# Робочі блоки
WORKBENCH_COLOR  = (180, 120, 60)
FURNACE_COLOR    = (80,  80,  90)
FURNACE_ORANGE   = (200, 80,  20)
CHEST_COLOR      = (160, 110, 40)

# UI слоти
UI_SLOT_BG       = (50,  50,  50)
UI_SLOT_BORDER   = (200, 200, 200)
UI_SLOT_SELECTED = (255, 220, 0)
UI_SLOT_HOVER    = (120, 120, 120)
UI_TOOLTIP_BG    = (20,  20,  20, 200)