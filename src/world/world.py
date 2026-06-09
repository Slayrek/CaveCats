# ============================================================
#  world.py — клас World: генерація, фізика, малювання
# ============================================================

import pygame
import json
import os
import random
import math # <--- ПОТРІБЕН ДЛЯ АНІМАЦІЇ ВОГНЮ
from src.core.settings import *
from src.world.blocks import (
    BLOCK_AIR, BLOCK_DIRT, BLOCK_GRASS, BLOCK_HOUSE,
    BLOCK_CAVE, BLOCK_STONE, BLOCK_WOOD_LOG,
    BLOCK_WORKBENCH, BLOCK_FURNACE, BLOCK_CHEST,
    NON_SOLID_BLOCKS, WORK_BLOCKS, BLOCK_DEFS, 
    BLOCK_LADDER, BLOCK_DOOR,
    BLOCK_COAL_ORE, BLOCK_IRON_ORE, BLOCK_GOLD_ORE, BLOCK_TITANIUM_ORE,
    BLOCK_ARENA_WALL, BLOCK_WATER, BLOCK_UNBREAKABLE_DIRT,
    BLOCK_COPPER_ORE,
    BLOCK_ROCKET_PAD_LEFT, BLOCK_ROCKET_PAD_CENTER, BLOCK_ROCKET_PAD_RIGHT,
    BLOCK_ROCKET, BLOCK_ROCKET_PART, BLOCK_LAVA, BLOCK_RARE_CHEST, BLOCK_BREWING_STAND,
    BLOCK_PLATFORM
)

class World:
    def __init__(self, folder="saves/default"):
        self.folder = folder
        self.filepath = os.path.join(self.folder, "world.json")
        self.config_path = os.path.join(self.folder, "world_config.json")
        
        self.config = {
            "ores": "Normal",
            "hardcore": False,
            "mob_rate": 1
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config.update(json.load(f))
            except: pass
            
        self.cols = WIDTH // TILE_SIZE
        self.rows = HEIGHT // TILE_SIZE
        self.cave_worms = []
        self.pending_boss_spawns = [] 
        
        self.grid: list[list[int]] = self._load_world()
        self.block_health: dict[tuple[int, int], int] = {}
        
    def _load_world(self) -> list[list[int]]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        grid = data["grid"]
                        if grid: self.cols = len(grid[0])
                        self.cave_worms = data.get("worms", [])
                        self.pending_boss_spawns = data.get("boss_spawns", [])
                        return grid
                    else:
                        # Fallback for old save format
                        if data: self.cols = len(data[0]) 
                        return data
            except (json.JSONDecodeError, TypeError):
                pass
        return self._generate_world()

    def save(self) -> None:
        data = {
            "grid": self.grid,
            "worms": self.cave_worms,
            "boss_spawns": self.pending_boss_spawns
        }
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
    def save_config(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def _generate_world(self) -> list[list[int]]:
        grid = [[BLOCK_AIR] * self.cols for _ in range(self.rows)]
        gl = GROUND_LEVEL

        for row in range(self.rows):
            for col in range(self.cols):
                if row == gl:
                    grid[row][col] = BLOCK_GRASS
                elif row == gl + 1:
                    grid[row][col] = BLOCK_DIRT
                elif row > gl + 1:
                    if row >= self.rows - 2 or col < 2:
                        grid[row][col] = BLOCK_DIRT
                    else:
                        chance = random.random()
                        ore_mult = 1.5 if self.config["ores"] == "High" else 1.0
                        if chance < 0.05 * ore_mult:     grid[row][col] = BLOCK_COAL_ORE
                        elif chance < 0.08 * ore_mult:   grid[row][col] = BLOCK_COPPER_ORE
                        elif chance < 0.10 * ore_mult:   grid[row][col] = BLOCK_IRON_ORE
                        elif chance < 0.11 * ore_mult:   grid[row][col] = BLOCK_GOLD_ORE
                        elif chance < 0.115 * ore_mult:  grid[row][col] = BLOCK_TITANIUM_ORE
                        else:                 grid[row][col] = BLOCK_STONE

        # Spawn initial worms
        num_worms = max(2, self.cols // 20)
        for _ in range(num_worms):
            r = random.randint(gl + 4, self.rows - 5)
            c = random.randint(5, self.cols - 5)
            w_type = random.choices(["tunnel", "cavern", "dead_end"], weights=[0.6, 0.2, 0.2])[0]
            if w_type == "tunnel":
                self.cave_worms.append({"r": r, "c": c, "life": random.randint(80, 250), "radius": random.uniform(1.2, 2.2), "dr": 0, "dc": 0, "type": w_type})
            elif w_type == "cavern":
                self.cave_worms.append({"r": r, "c": c, "life": random.randint(20, 50), "radius": random.uniform(3.0, 5.0), "dr": 0, "dc": 0, "type": w_type})
            else:
                self.cave_worms.append({"r": r, "c": c, "life": random.randint(10, 30), "radius": random.uniform(1.5, 2.5), "dr": 0, "dc": 0, "type": w_type})
            
        self._simulate_worms(grid, 0, self.cols)

        center = self.cols // 2
        
        # Clear out a spawn area for the house and cat
        for r in range(gl - 3, gl + 3):
            for c in range(center - 5, center + 5):
                if r < gl: grid[r][c] = BLOCK_AIR
                elif r == gl: grid[r][c] = BLOCK_GRASS
                else: grid[r][c] = BLOCK_DIRT

        if self._in_bounds(gl - 2, center - 1): grid[gl - 2][center - 1] = BLOCK_HOUSE
        if self._in_bounds(gl - 2, center):     grid[gl - 2][center] = BLOCK_HOUSE
        if self._in_bounds(gl - 1, center - 1): grid[gl - 1][center - 1] = BLOCK_STONE
        if self._in_bounds(gl - 1, center):     grid[gl - 1][center] = BLOCK_DOOR

        tree_cols = [5, 8, 20, 22]
        for tc in tree_cols:
            for dr in range(1, 4):
                r = gl - dr
                if self._in_bounds(r, tc):
                    grid[r][tc] = BLOCK_WOOD_LOG

        # Ensure the ladder goes all the way down through solid stone if needed
        for r in range(gl, self.rows - 2):
            if self._in_bounds(r, center):
                grid[r][center] = BLOCK_LADDER
                # Clear blocks around ladder so it's accessible
                if self._in_bounds(r, center - 1) and grid[r][center - 1] == BLOCK_STONE: grid[r][center - 1] = BLOCK_CAVE
                if self._in_bounds(r, center + 1) and grid[r][center + 1] == BLOCK_STONE: grid[r][center + 1] = BLOCK_CAVE

        pond_start = center + 15
        pond_end = pond_start + 5
        for c in range(pond_start - 1, pond_end + 2):
            if c < self.cols:
                is_bank = (c == pond_start - 1 or c == pond_end + 1)
                if is_bank:
                    grid[gl][c] = BLOCK_UNBREAKABLE_DIRT
                    grid[gl + 1][c] = BLOCK_UNBREAKABLE_DIRT
                    grid[gl + 2][c] = BLOCK_UNBREAKABLE_DIRT
                else:
                    grid[gl][c] = BLOCK_WATER
                    grid[gl + 1][c] = BLOCK_WATER
                    grid[gl + 2][c] = BLOCK_UNBREAKABLE_DIRT
                    for r in range(gl - 1, -1, -1):
                        grid[r][c] = BLOCK_AIR

        # --- LAVA GENERATION ---
        for _ in range(self.cols // 20):
            if random.random() < 0.4:
                p_w = random.randint(4, 8)
                pond_start = random.randint(5, self.cols - p_w - 2)
                pond_end = pond_start + p_w
                min_r = gl + 5
                max_r = self.rows - 4
                start_r = random.randint(min_r, max_r) if min_r <= max_r else min_r
                
                for c in range(pond_start - 1, pond_end + 2):
                    if c < self.cols:
                        is_bank = (c == pond_start - 1 or c == pond_end + 1)
                        if is_bank:
                            grid[start_r][c] = BLOCK_UNBREAKABLE_DIRT
                            grid[start_r + 1][c] = BLOCK_UNBREAKABLE_DIRT
                            grid[start_r + 2][c] = BLOCK_UNBREAKABLE_DIRT
                        else:
                            grid[start_r][c] = BLOCK_LAVA
                            grid[start_r + 1][c] = BLOCK_LAVA
                            grid[start_r + 2][c] = BLOCK_UNBREAKABLE_DIRT
                            for r in range(start_r - 1, start_r - 4, -1):
                                if self._in_bounds(r, c) and grid[r][c] == BLOCK_STONE:
                                    grid[r][c] = BLOCK_CAVE

        return grid

    def _simulate_worms(self, grid, min_col, max_col):
        active_worms = []
        for worm in self.cave_worms:
            w_type = worm.get("type", "tunnel") # For backward compatibility
            while worm["life"] > 0:
                wr, wc = int(worm["r"]), int(worm["c"])
                rad = worm["radius"]
                
                # Carve circle
                for dr in range(-int(rad)-1, int(rad)+2):
                    for dc in range(-int(rad)-1, int(rad)+2):
                        if dr*dr + dc*dc <= rad*rad:
                            cr = wr + dr
                            cc = wc + dc
                            # Enforce min_col to prevent carving backwards into previously generated chunks
                            if GROUND_LEVEL + 2 <= cr < self.rows - 2 and min_col <= cc < max_col:
                                # Don't overwrite indestructible things or ladders
                                if grid[cr][cc] not in (BLOCK_UNBREAKABLE_DIRT, BLOCK_LADDER, BLOCK_RARE_CHEST):
                                    grid[cr][cc] = BLOCK_CAVE
                                    
                                    # Ultra-rare chest generation
                                    if cr > GROUND_LEVEL + 40 and dr == int(rad) and random.random() < 0.002:
                                        grid[cr][cc] = BLOCK_RARE_CHEST
                
                # Randomize direction based on type
                if w_type == "tunnel":
                    if random.random() < 0.2: worm["dr"] = random.choice([-1, 0, 1])
                    if random.random() < 0.2: worm["dc"] = random.choice([-1, 1, 1, 1])
                elif w_type == "cavern":
                    if random.random() < 0.5: worm["dr"] = random.choice([-1, 0, 1])
                    if random.random() < 0.5: worm["dc"] = random.choice([-1, 0, 1])
                else: # dead_end
                    if random.random() < 0.3: worm["dr"] = random.choice([-1, 0, 1])
                    if random.random() < 0.3: worm["dc"] = random.choice([-1, 0, 1])
                
                worm["r"] += worm["dr"]
                worm["c"] += worm["dc"]
                worm["life"] -= 1
                
                # Pause worm if it reaches edge
                if worm["c"] >= max_col - 1:
                    break
            
            if worm["life"] > 0:
                active_worms.append(worm)
                
        self.cave_worms = active_worms

    def expand_right(self, amount: int = 20) -> None:
        gl = GROUND_LEVEL
        old_cols = self.cols
        
        for row in range(self.rows):
            for _ in range(amount):
                if row < gl:
                    self.grid[row].append(BLOCK_AIR)
                elif row == gl:
                    self.grid[row].append(BLOCK_GRASS)
                elif row == gl + 1:
                    self.grid[row].append(BLOCK_DIRT)
                elif row >= self.rows - 2:
                    self.grid[row].append(BLOCK_DIRT)
                else:
                    chance = random.random()
                    ore_mult = 1.5 if self.config["ores"] == "High" else 1.0
                    if chance < 0.05 * ore_mult:     self.grid[row].append(BLOCK_COAL_ORE)
                    elif chance < 0.08 * ore_mult:   self.grid[row].append(BLOCK_COPPER_ORE)
                    elif chance < 0.10 * ore_mult:   self.grid[row].append(BLOCK_IRON_ORE)
                    elif chance < 0.11 * ore_mult:   self.grid[row].append(BLOCK_GOLD_ORE)
                    elif chance < 0.115 * ore_mult:  self.grid[row].append(BLOCK_TITANIUM_ORE)
                    else:                 self.grid[row].append(BLOCK_STONE) 
                    
        self.cols += amount
        
        # Spawn new worms for the expanded chunk
        num_new_worms = max(1, amount // 20)
        for _ in range(num_new_worms):
            r = random.randint(gl + 4, self.rows - 5)
            c = random.randint(old_cols, self.cols - 1)
            w_type = random.choices(["tunnel", "cavern", "dead_end"], weights=[0.6, 0.2, 0.2])[0]
            if w_type == "tunnel":
                self.cave_worms.append({"r": r, "c": c, "life": random.randint(80, 250), "radius": random.uniform(1.2, 2.2), "dr": 0, "dc": 0, "type": w_type})
            elif w_type == "cavern":
                self.cave_worms.append({"r": r, "c": c, "life": random.randint(20, 50), "radius": random.uniform(3.0, 5.0), "dr": 0, "dc": 0, "type": w_type})
            else:
                self.cave_worms.append({"r": r, "c": c, "life": random.randint(10, 30), "radius": random.uniform(1.5, 2.5), "dr": 0, "dc": 0, "type": w_type})
            
        self._simulate_worms(self.grid, old_cols, self.cols)

        if old_cols > 20 and random.random() < 0.25: 
            p_w = random.randint(4, 8) 
            pond_start = random.randint(old_cols + 2, self.cols - p_w - 2)
            pond_end = pond_start + p_w
            
            for c in range(pond_start - 1, pond_end + 2):
                is_bank = (c == pond_start - 1 or c == pond_end + 1)
                if is_bank:
                    self.grid[gl][c] = BLOCK_UNBREAKABLE_DIRT
                    self.grid[gl + 1][c] = BLOCK_UNBREAKABLE_DIRT
                    self.grid[gl + 2][c] = BLOCK_UNBREAKABLE_DIRT
                else:
                    self.grid[gl][c] = BLOCK_WATER
                    self.grid[gl + 1][c] = BLOCK_WATER
                    self.grid[gl + 2][c] = BLOCK_UNBREAKABLE_DIRT
                    for r in range(gl - 1, -1, -1):
                        self.grid[r][c] = BLOCK_AIR

        if old_cols > 20 and random.random() < 0.4: 
            p_w = random.randint(4, 8) 
            pond_start = random.randint(old_cols + 2, self.cols - p_w - 2)
            pond_end = pond_start + p_w
            min_r = gl + 5
            max_r = self.rows - 4
            start_r = random.randint(min_r, max_r) if min_r <= max_r else min_r
            
            for c in range(pond_start - 1, pond_end + 2):
                is_bank = (c == pond_start - 1 or c == pond_end + 1)
                if is_bank:
                    self.grid[start_r][c] = BLOCK_UNBREAKABLE_DIRT
                    self.grid[start_r + 1][c] = BLOCK_UNBREAKABLE_DIRT
                    self.grid[start_r + 2][c] = BLOCK_UNBREAKABLE_DIRT
                else:
                    self.grid[start_r][c] = BLOCK_LAVA
                    self.grid[start_r + 1][c] = BLOCK_LAVA
                    self.grid[start_r + 2][c] = BLOCK_UNBREAKABLE_DIRT
                    for r in range(start_r - 1, start_r - 4, -1):
                        if self._in_bounds(r, c) and self.grid[r][c] == BLOCK_STONE:
                            self.grid[r][c] = BLOCK_CAVE

        if old_cols > 40 and random.random() < 0.15: 
            room_w = 10 
            room_h = 7  
            start_c = random.randint(old_cols + 2, self.cols - room_w - 2)
            min_r = gl + 5
            max_r = self.rows - room_h - 2
            start_r = random.randint(min_r, max_r) if max_r > min_r else min_r
            
            for r in range(start_r, start_r + room_h):
                for c in range(start_c, start_c + room_w):
                    if r < self.rows and c < self.cols:
                        is_wall = (r == start_r or r == start_r + room_h - 1 or 
                                   c == start_c or c == start_c + room_w - 1)
                        if is_wall:
                            is_door = (c == start_c or c == start_c + room_w - 1) and (r == start_r + room_h - 2 or r == start_r + room_h - 3)
                            if is_door:
                                self.grid[r][c] = BLOCK_DOOR
                            else:
                                self.grid[r][c] = BLOCK_ARENA_WALL
                        else:
                            self.grid[r][c] = BLOCK_CAVE
                            
            self.pending_boss_spawns.append(((start_c + 4) * TILE_SIZE, (start_r + 3) * TILE_SIZE))

    def random_tick(self) -> None:
        if random.random() < 0.0005:
            col = random.randint(0, self.cols - 1)
            gl = GROUND_LEVEL
            
            if self.grid[gl][col] == BLOCK_GRASS:
                can_grow = True
                for dr in range(1, 4):
                    r = gl - dr
                    if not self._in_bounds(r, col) or self.grid[r][col] != BLOCK_AIR:
                        can_grow = False
                        break
                
                if can_grow:
                    for dc in range(-2, 3):
                        c = col + dc
                        if self._in_bounds(gl - 1, c) and self.grid[gl - 1][c] == BLOCK_WOOD_LOG:
                            can_grow = False
                            break
                            
                if can_grow:
                    for dr in range(1, 4):
                        self.grid[gl - dr][col] = BLOCK_WOOD_LOG

    def _in_bounds(self, row: int, col: int) -> bool:
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_solid_rects(self) -> list[pygame.Rect]:
        rects = []
        for row in range(self.rows):
            for col in range(self.cols):
                block_id = self.grid[row][col]
                if BLOCK_DEFS[block_id]["solid"]:
                    rects.append(pygame.Rect(
                        col * TILE_SIZE, row * TILE_SIZE,
                        TILE_SIZE, TILE_SIZE,
                    ))
        return rects

    def get_ladder_rects(self) -> list[pygame.Rect]:
        rects = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == BLOCK_LADDER:
                    rects.append(pygame.Rect(
                        col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    ))
        return rects

    def get_work_block_at(self, col: int, row: int) -> int | None:
        if not self._in_bounds(row, col):
            return None
        block_id = self.grid[row][col]
        if BLOCK_DEFS[block_id]["is_work_block"]:
            return block_id
        return None

    def hit_block(self, col: int, row: int, damage: int = 1) -> str | None:
        if not self._in_bounds(row, col):
            return None

        block_id  = self.grid[row][col]
        block_def = BLOCK_DEFS.get(block_id, {})

        if not block_def.get("breakable", False):
            return None

        key = (row, col)
        if key not in self.block_health:
            self.block_health[key] = block_def["max_health"]

        self.block_health[key] -= damage

        if self.block_health[key] <= 0:
            del self.block_health[key]
            replacement = block_def.get("broken_becomes", BLOCK_AIR)
            self.grid[row][col] = replacement
            drops = block_def.get("drops", [])
            
            if block_id in (BLOCK_ROCKET_PAD_LEFT, BLOCK_ROCKET_PAD_CENTER, BLOCK_ROCKET_PAD_RIGHT):
                for dc in (-2, -1, 1, 2):
                    if self._in_bounds(row, col + dc):
                        neighbor_id = self.grid[row][col + dc]
                        if neighbor_id in (BLOCK_ROCKET_PAD_LEFT, BLOCK_ROCKET_PAD_CENTER, BLOCK_ROCKET_PAD_RIGHT):
                            self.grid[row][col + dc] = BLOCK_AIR
                            if (row, col + dc) in self.block_health:
                                del self.block_health[(row, col + dc)]
                if block_id != BLOCK_ROCKET_PAD_CENTER:
                    drops = ["rocket_platform"]

            # --- ЗРУЙНУВАННЯ РАКЕТИ ---
            if block_id in (BLOCK_ROCKET, BLOCK_ROCKET_PART):
                drops = []
                for r in range(max(0, row - 6), min(self.rows, row + 6)):
                    for c in range(max(0, col - 3), min(self.cols, col + 3)):
                        if self._in_bounds(r, c):
                            if self.grid[r][c] == BLOCK_ROCKET:
                                drops.append("rocket")
                                self.grid[r][c] = BLOCK_AIR
                                if (r, c) in self.block_health: del self.block_health[(r, c)]
                            elif self.grid[r][c] == BLOCK_ROCKET_PART:
                                self.grid[r][c] = BLOCK_AIR
                                if (r, c) in self.block_health: del self.block_health[(r, c)]
                return drops[0] if drops else None

            return drops[0] if drops else None

        return None

    def place_block(self, col: int, row: int, block_id: int) -> bool:
        if not self._in_bounds(row, col): return False

        current = self.grid[row][col]
        if current not in (BLOCK_AIR, BLOCK_CAVE): return False

        # ПЕРЕВІРКА ПЛАТФОРМИ
        if block_id == BLOCK_ROCKET_PAD_CENTER:
            if not (self._in_bounds(row, col - 1) and self._in_bounds(row, col + 1)): return False
            if self.grid[row][col-1] not in (BLOCK_AIR, BLOCK_CAVE): return False
            if self.grid[row][col+1] not in (BLOCK_AIR, BLOCK_CAVE): return False
            self.grid[row][col-1] = BLOCK_ROCKET_PAD_LEFT
            self.grid[row][col]   = BLOCK_ROCKET_PAD_CENTER
            self.grid[row][col+1] = BLOCK_ROCKET_PAD_RIGHT
            return True

        # --- РОЗГОРТАННЯ РАКЕТИ ---
        if block_id == BLOCK_ROCKET:
            # 1. Перевіряємо, чи під нами є центр платформи
            if row + 1 >= self.rows or self.grid[row + 1][col] != BLOCK_ROCKET_PAD_CENTER:
                return False
            # 2. Перевіряємо, чи вільне повітря 3х5
            for r in range(row - 4, row + 1):
                for c in range(col - 1, col + 2):
                    if not self._in_bounds(r, c) or self.grid[r][c] not in (BLOCK_AIR, BLOCK_CAVE):
                        return False
            # 3. Ставимо ракету
            for r in range(row - 4, row + 1):
                for c in range(col - 1, col + 2):
                    if r == row and c == col:
                        self.grid[r][c] = BLOCK_ROCKET
                    else:
                        self.grid[r][c] = BLOCK_ROCKET_PART
            return True

        self.grid[row][col] = block_id
        return True

    def draw(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0) -> None:
        surface.fill(SKY_BLUE)

        cave_y = (GROUND_LEVEL + 1) * TILE_SIZE - camera_y
        if cave_y < surface.get_height():
            pygame.draw.rect(surface, CAVE_BG, (0, max(0, cave_y), surface.get_width(), surface.get_height() - max(0, cave_y)))

        start_col = max(0, camera_x // TILE_SIZE)
        end_col = min(self.cols, (camera_x + surface.get_width()) // TILE_SIZE + 2)
        
        start_row = max(0, camera_y // TILE_SIZE)
        end_row = min(self.rows, (camera_y + surface.get_height()) // TILE_SIZE + 2)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                self._draw_tile(surface, col, row, camera_x, camera_y)

    def _draw_tile(self, surface: pygame.Surface, col: int, row: int, camera_x: int, camera_y: int) -> None:
        block_id  = self.grid[row][col]
        block_def = BLOCK_DEFS.get(block_id)

        if block_def is None or block_def["draw"] is None:
            # Якщо це центральний блок ракети, малюємо величезний спрайт
            if block_id == BLOCK_ROCKET:
                self._draw_rocket_icon(surface, col * TILE_SIZE - camera_x, row * TILE_SIZE - camera_y)
            return

        x = col * TILE_SIZE - camera_x
        y = row * TILE_SIZE - camera_y
        draw = block_def["draw"]
        color  = draw.get("color")
        border = draw.get("border")
        bwidth = draw.get("border_width", 1)

        if block_id == BLOCK_PLATFORM:
            # Only draw top part
            if color: pygame.draw.rect(surface, color, (x, y, TILE_SIZE, 8))
            if border: pygame.draw.rect(surface, border, (x, y, TILE_SIZE, 8), bwidth)
        else:
            if color: pygame.draw.rect(surface, color, (x, y, TILE_SIZE, TILE_SIZE))
            if border: pygame.draw.rect(surface, border, (x, y, TILE_SIZE, TILE_SIZE), bwidth)

        if block_id == BLOCK_WOOD_LOG: self._draw_wood_rings(surface, x, y)
        elif block_id == BLOCK_WORKBENCH: self._draw_workbench_icon(surface, x, y)
        elif block_id == BLOCK_FURNACE: self._draw_furnace_icon(surface, x, y)
        elif block_id == BLOCK_CHEST: self._draw_chest_icon(surface, x, y)
        elif block_id == BLOCK_RARE_CHEST: self._draw_rare_chest_icon(surface, x, y)
        elif block_id == BLOCK_LADDER: self._draw_ladder_icon(surface, x, y)
        elif block_id == BLOCK_DOOR: self._draw_door_icon(surface, x, y)
        elif block_id == BLOCK_BREWING_STAND: self._draw_brewing_stand_icon(surface, x, y)
            
        elif block_id == BLOCK_ROCKET_PAD_LEFT:
            pygame.draw.polygon(surface, (200, 150, 0), [(x, y+TILE_SIZE), (x+TILE_SIZE, y), (x+TILE_SIZE, y+10), (x+10, y+TILE_SIZE)])
        elif block_id == BLOCK_ROCKET_PAD_CENTER:
            pygame.draw.circle(surface, (50, 200, 255), (x + TILE_SIZE//2, y + TILE_SIZE//2), 12, 4)
            pygame.draw.circle(surface, (50, 200, 255), (x + TILE_SIZE//2, y + TILE_SIZE//2), 4)
        elif block_id == BLOCK_ROCKET_PAD_RIGHT:
            pygame.draw.polygon(surface, (200, 150, 0), [(x, y), (x+TILE_SIZE, y+TILE_SIZE), (x+TILE_SIZE-10, y+TILE_SIZE), (x, y+10)])

        if block_def["breakable"] and block_def["max_health"] > 0:
            hp  = self.block_health.get((row, col), block_def["max_health"])
            if hp < block_def["max_health"]:
                self._draw_cracks(surface, x, y, hp, max_hp=block_def["max_health"])

    def _draw_brewing_stand_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        # Base
        pygame.draw.rect(surface, (80, 80, 80), (x + 4, y + TILE_SIZE - 8, TILE_SIZE - 8, 8))
        # Stand
        pygame.draw.rect(surface, (200, 150, 50), (x + TILE_SIZE//2 - 2, y + 8, 4, TILE_SIZE - 16))
        # Arms
        pygame.draw.rect(surface, (200, 150, 50), (x + 8, y + 16, TILE_SIZE - 16, 4))
        # Potions
        pygame.draw.rect(surface, (200, 50, 50), (x + 8, y + 20, 8, 12))
        pygame.draw.rect(surface, (50, 200, 50), (x + TILE_SIZE - 16, y + 20, 8, 12))

    def _draw_rocket_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        rx = x - TILE_SIZE
        ry = y - 4 * TILE_SIZE
        
        pygame.draw.rect(surface, (100, 100, 110), (rx + TILE_SIZE, ry + 4*TILE_SIZE, TILE_SIZE, TILE_SIZE))
        
        t = pygame.time.get_ticks()
        fire_h = 10 + int(math.sin(t * 0.01) * 5)
        pygame.draw.polygon(surface, (255, 100, 0), [
            (rx + TILE_SIZE + 4, ry + 5*TILE_SIZE),
            (rx + TILE_SIZE + TILE_SIZE//2, ry + 5*TILE_SIZE + fire_h),
            (rx + 2*TILE_SIZE - 4, ry + 5*TILE_SIZE)
        ])
        
        pygame.draw.rect(surface, (220, 220, 230), (rx + int(0.5*TILE_SIZE), ry + TILE_SIZE, 2*TILE_SIZE, 3*TILE_SIZE), border_radius=10)
        
        pygame.draw.polygon(surface, (200, 150, 0), [
            (rx + int(0.5*TILE_SIZE), ry + 3*TILE_SIZE),
            (rx, ry + 5*TILE_SIZE),
            (rx + int(0.5*TILE_SIZE), ry + 4.5*TILE_SIZE)
        ])
        pygame.draw.polygon(surface, (200, 150, 0), [
            (rx + int(2.5*TILE_SIZE), ry + 3*TILE_SIZE),
            (rx + 3*TILE_SIZE, ry + 5*TILE_SIZE),
            (rx + int(2.5*TILE_SIZE), ry + 4.5*TILE_SIZE)
        ])
        
        pygame.draw.polygon(surface, (220, 50, 50), [
            (rx + int(0.5*TILE_SIZE), ry + TILE_SIZE),
            (rx + int(1.5*TILE_SIZE), ry),
            (rx + int(2.5*TILE_SIZE), ry + TILE_SIZE)
        ])
        
        pygame.draw.circle(surface, (50, 200, 255), (int(rx + 1.5*TILE_SIZE), int(ry + 2*TILE_SIZE)), TILE_SIZE//2)
        pygame.draw.circle(surface, (200, 240, 255), (int(rx + 1.5*TILE_SIZE), int(ry + 2*TILE_SIZE)), TILE_SIZE//2 - 4)

    def _draw_cracks(self, surface: pygame.Surface, x: int, y: int, hp: int, max_hp: int) -> None:
        damage = max_hp - hp
        color  = (60, 60, 60)
        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        if damage >= 1: pygame.draw.line(surface, color, (x + 5, y + 5), (cx, cy), 2)
        if damage >= 2: pygame.draw.line(surface, color, (x + TILE_SIZE - 5, y + TILE_SIZE - 10), (cx, cy), 2)
        if damage >= 3: pygame.draw.line(surface, color, (x + 10, y + TILE_SIZE - 5), (cx, cy), 2)
        if damage >= 4: pygame.draw.line(surface, color, (x + TILE_SIZE - 5, y + 8), (cx, cy), 2)

    def _draw_wood_rings(self, surface: pygame.Surface, x: int, y: int) -> None:
        cx, cy = x + TILE_SIZE // 2, y + TILE_SIZE // 2
        pygame.draw.circle(surface, WOOD_DARK, (cx, cy), 14, 2)
        pygame.draw.circle(surface, WOOD_DARK, (cx, cy),  8, 1)
        pygame.draw.circle(surface, WOOD_DARK, (cx, cy),  3)

    def _draw_workbench_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        pygame.draw.rect(surface, WOOD_DARK, (x + 4,  y + 10, TILE_SIZE - 8, 5))
        pygame.draw.rect(surface, WOOD_DARK, (x + 5,  y + 15, 5, 18))
        pygame.draw.rect(surface, WOOD_DARK, (x + TILE_SIZE - 10, y + 15, 5, 18))

    def _draw_furnace_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        pygame.draw.rect(surface, FURNACE_ORANGE, (x + 8,  y + 12, TILE_SIZE - 16, 20))
        pygame.draw.rect(surface, (255, 160, 40),  (x + 12, y + 16, TILE_SIZE - 24, 12))

    def _draw_chest_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        mid = TILE_SIZE // 2
        pygame.draw.rect(surface, WOOD_DARK, (x + 4, y + 4, TILE_SIZE - 8, 4))
        pygame.draw.rect(surface, WOOD_DARK, (x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 10), 2)
        pygame.draw.rect(surface, (200, 160, 30), (x + mid - 4, y + 18, 8, 6))

    def _draw_rare_chest_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        mid = TILE_SIZE // 2
        # Base magical purple color
        pygame.draw.rect(surface, (90, 30, 120), (x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 10))
        # Top lid line
        pygame.draw.rect(surface, (140, 50, 180), (x + 4, y + 4, TILE_SIZE - 8, 4))
        # Gold borders
        pygame.draw.rect(surface, (255, 215, 0), (x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 10), 2)
        # Gold lock
        pygame.draw.rect(surface, (255, 215, 0), (x + mid - 4, y + 18, 8, 6))
        
        # Shiny effect
        t = pygame.time.get_ticks()
        if (x + y + t) % 1000 < 100:
            pygame.draw.circle(surface, (255, 255, 255), (x + mid, y + mid), 3)

    def _draw_ladder_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        pygame.draw.rect(surface, WOOD_DARK, (x + 6, y, 4, TILE_SIZE))
        pygame.draw.rect(surface, WOOD_DARK, (x + TILE_SIZE - 10, y, 4, TILE_SIZE))
        for i in range(1, 4):
            pygame.draw.rect(surface, WOOD_BROWN, (x + 6, y + i * 10, TILE_SIZE - 12, 4))

    def _draw_door_icon(self, surface: pygame.Surface, x: int, y: int) -> None:
        pygame.draw.circle(surface, (200, 150, 50), (x + TILE_SIZE - 8, y + TILE_SIZE // 2), 4)