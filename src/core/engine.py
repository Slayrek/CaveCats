import sys
from src.core.utils import resource_path
import os
import shutil
import pygame
import random
import math
import json
from datetime import datetime

from src.core import audio
from src.core.settings import WIDTH, HEIGHT, FPS, TILE_SIZE, HOTBAR_SLOTS, ATTACK_COOLDOWN
from src.core.data_loader import data_manager
from src.modding.mod_loader import ModLoader

from src.world.world import World
from src.entities.entities import Cat, OtherPlayer
from src.entities.item_drop import ItemDrop
from src.entities.bosses import Gargoyle, AbyssalBehemoth
from src.entities.mobs import Bat, Slime, ZombieCat
from src.entities.projectiles import Arrow, HookProjectile
from src.items.inventory import Inventory
from src.ui.cursor import PawCursor
from src.world.chest_manager import ChestManager
from src.world.blocks import BLOCK_WORKBENCH, BLOCK_FURNACE, BLOCK_CHEST, BLOCK_WATER, BLOCK_ROCKET, BLOCK_CAVE, BLOCK_AIR, BLOCK_LAVA, BLOCK_BREWING_STAND, BLOCK_GOLD_ORE, BLOCK_RARE_CHEST
from src.ui.cheat_console import CheatConsole
from src.ui.ui_workbench import WorkbenchUI 
from src.ui.ui_alchemy import AlchemyUI
from src.ui.ui_chest import ChestUI
from src.world.furnace_manager import FurnaceManager
from src.ui.ui_furnace import FurnaceUI
from src.ui.ui_stats import StatsUI
from src.items.items import get_item_def
from src.ui.ui_creative import CreativeUI
from src.core.utils import resource_path
import os
import shutil
import pygame
import random
import math
import json
from datetime import datetime
try:
    import server.relay_server
except ImportError:
    pass

from src.core import audio
from src.core.settings import WIDTH, HEIGHT, FPS, TILE_SIZE, HOTBAR_SLOTS, ATTACK_COOLDOWN
from src.core.data_loader import data_manager
from src.modding.mod_loader import ModLoader

from src.world.world import World
from src.entities.entities import Cat
from src.entities.item_drop import ItemDrop
from src.entities.bosses import Gargoyle, AbyssalBehemoth
from src.entities.mobs import Bat, Slime, ZombieCat
from src.entities.projectiles import Arrow, HookProjectile
from src.items.inventory import Inventory
from src.ui.cursor import PawCursor
from src.world.chest_manager import ChestManager
from src.world.blocks import BLOCK_WORKBENCH, BLOCK_FURNACE, BLOCK_CHEST, BLOCK_WATER, BLOCK_ROCKET, BLOCK_CAVE, BLOCK_AIR, BLOCK_LAVA, BLOCK_BREWING_STAND, BLOCK_GOLD_ORE, BLOCK_RARE_CHEST
from src.ui.cheat_console import CheatConsole
from src.ui.ui_workbench import WorkbenchUI 
from src.ui.ui_alchemy import AlchemyUI
from src.ui.ui_chest import ChestUI
from src.world.furnace_manager import FurnaceManager
from src.ui.ui_furnace import FurnaceUI
from src.ui.ui_stats import StatsUI
from src.items.items import get_item_def
from src.ui.ui_creative import CreativeUI
from src.ui.main_menu import MainMenu
from src.ui.create_world_screen import CreateWorldScreen
from src.ui.worlds_screen import WorldsScreen
from src.ui.end_screen import EndScreen
from src.managers.settings_manager import SettingsManager, SettingsScreen
from src.managers.achievements import AchievementManager, AchievementsScreen
from src.ui.leaderboard_screen import LeaderboardScreen
from src.network.network_client import net_client
from src.ui.touch_controls import TouchController

class GameEngine:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Cave Cats")

        icon_path = resource_path(os.path.join("pics", "cat.png"))
        if os.path.exists(icon_path):
            pygame.display.set_icon(pygame.image.load(icon_path))

        # --- Load Data & Mods ---
        data_manager.load_all()
        self.mod_loader = ModLoader()
        self.mod_loader.init_mods()

        self.ach_manager = AchievementManager()
        self.settings_manager = SettingsManager()
        audio.init(self.settings_manager)

        self.state = "main_menu"

    def run(self):
        while True:
            audio.update()
            
            if self.state == "main_menu":
                self.state = self._state_main_menu()
            elif self.state == "achievements":
                self.state = self._state_achievements()
            elif self.state == "settings":
                self.state = self._state_settings()
            elif self.state == "worlds":
                self.state = self._state_worlds()
            elif self.state == "create_world":
                self.state = self._state_create_world()
            elif self.state == "game":
                self.state = self._state_game()
            elif self.state == "end_screen":
                self.state = self._state_end_screen()
            elif self.state == "leaderboard":
                self.state = self._state_leaderboard()
            else:
                break
                
        pygame.quit()
        sys.exit()

    def _state_main_menu(self):
        pygame.mouse.set_visible(True)
        audio.play_music("overworld")
        
        # Disconnect from any previous multiplayer sessions
        if net_client.is_connected:
            net_client.disconnect()
            
        action = MainMenu(self.screen).run()
        if action == "start": return "worlds"
        if action == "host":
            try:
                from server.relay_server import start_server
                import threading
                threading.Thread(target=start_server, daemon=True).start()
                import time
                time.sleep(0.5) # Wait for server to bind
            except Exception as e:
                print("Could not start internal server:", e)
                
            net_client.host = "127.0.0.1"
            net_client.port = 7777
            if net_client.connect():
                net_client.send({"cmd": "create_room"})
                return "worlds"
            else:
                return "main_menu"
                
        if action and action.startswith("join_"):
            ip_address = action.split("_")[1]
            net_client.host = ip_address
            net_client.port = 7777
            if net_client.connect():
                net_client.join_room("ANY")
                self.settings_manager.active_save = "multiplayer_client"
                return "game" 
            else:
                return "main_menu"
        
        if action == "achievements": return "achievements"
        if action == "settings": return "settings"
        if action == "leaderboard": return "leaderboard"
        return "quit"

    def _state_achievements(self):
        pygame.mouse.set_visible(True)
        action = AchievementsScreen(self.screen, self.ach_manager).run()
        if action == "back": return "main_menu"
        return "quit"

    def _state_settings(self):
        pygame.mouse.set_visible(True)
        action = SettingsScreen(self.screen, self.settings_manager).run()
        if action == "back": return "main_menu"
        return "quit"
        
    def _state_leaderboard(self):
        pygame.mouse.set_visible(True)
        screen = LeaderboardScreen(self.screen)
        action = screen.run()
        if action == "back": return "main_menu"
        return "quit"

    def _state_end_screen(self):
        pygame.mouse.set_visible(True)
        action = EndScreen(self.screen).run()
        if action == "restart": return "worlds"
        if action == "main_menu": return "main_menu"
        return "quit"

    def _state_worlds(self):
        pygame.mouse.set_visible(True)
        action = WorldsScreen(self.screen, self.settings_manager).run()
        if action == "back": return "main_menu"
        if action == "new_world": return "create_world"
        if action == "play": return "game"
        return "quit"
        
    def _state_create_world(self):
        pygame.mouse.set_visible(True)
        action = CreateWorldScreen(self.screen, self.settings_manager).run()
        if action == "back": return "worlds"
        if action == "play": return "game"
        return "quit"

    def _state_game(self):
        self.screen.fill((30, 30, 30))
        font = pygame.font.SysFont(None, 64)
        txt = font.render("Generating World... Please wait.", True, (255, 255, 255))
        self.screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//2)))
        pygame.display.flip()
        
        pygame.mouse.set_visible(False)
        clock = pygame.time.Clock()

        print("DEBUG: Checking save path")
        save_path = os.path.join("saves", self.settings_manager.active_save)
        if not os.path.exists(save_path): 
            os.makedirs(save_path)

        print("DEBUG: Init World")
        world           = World(folder=save_path)
        print("DEBUG: Init Inventory")
        inventory       = Inventory(folder=save_path)
        print("DEBUG: Init ChestManager")
        chest_manager   = ChestManager(folder=save_path)
        print("DEBUG: Init FurnaceManager")
        furnace_manager = FurnaceManager(folder=save_path)
        
        chest_ui        = ChestUI(inventory, chest_manager)
        furnace_ui      = FurnaceUI(inventory, furnace_manager)
        stats_ui        = StatsUI() 
        
        drops_group     = pygame.sprite.Group()
        bosses_group    = pygame.sprite.Group() 
        mobs_group      = pygame.sprite.Group()
        projectiles_group = pygame.sprite.Group()
        all_sprites     = pygame.sprite.Group()
        
        respawn_queue   = []

        workbench_ui    = WorkbenchUI(inventory, self.ach_manager)
        alchemy_ui      = AlchemyUI(inventory)
        cheat_console   = CheatConsole(inventory)

        print("DEBUG: Init Cat")
        spawn_x = WIDTH // 2
        spawn_y = TILE_SIZE * 7
        cat = Cat(spawn_x, spawn_y, world, drops_group, inventory, chest_manager)
        all_sprites.add(cat)

        cheat_console.cat = cat
        cheat_console.bosses_group = bosses_group
        cheat_console.mobs_group = mobs_group

        print("DEBUG: Init UIs")
        creative_ui = CreativeUI(inventory, cat)
        paw_cursor = PawCursor()
        
        active_pet = None
        touch_ctrl = TouchController()
        
        camera_x = 0
        zoom_level = 1.0
        running = True
        game_won = False 
        return_to_menu = False
        lava_timer = 0
        font_timer = pygame.font.SysFont("consolas", 28, bold=True)
        
        other_players = {} # id -> OtherPlayer
        network_sync_timer = 0

        print("DEBUG: Entering main loop")
        while running:
            dt_ms = clock.tick(FPS)
            mouse_pos = pygame.mouse.get_pos()
            current_w, current_h = self.screen.get_size()
            touch_ctrl.update_resolution(current_w, current_h)
            ui_is_open = cheat_console.is_open or chest_ui.is_open or furnace_ui.is_open or workbench_ui.is_open or alchemy_ui.is_open or inventory.show_full
            
            # --- NETWORK SYNC ---
            if net_client.is_connected:
                network_sync_timer += dt_ms
                if network_sync_timer >= 50: # 20 ticks per second
                    network_sync_timer = 0
                    net_client.send({
                        "cmd": "sync",
                        "name": self.settings_manager.data.get("player_name", "Player"),
                        "x": cat.hitbox.centerx,
                        "y": cat.hitbox.centery,
                        "facing_right": cat.facing_right,
                        "tool": cat._cached_tool,
                        "armor": cat._cached_armor,
                        "boots": cat._cached_boots,
                        "attacking": cat.attack_cooldown > 0
                    })
                    
                    if net_client.is_host:
                        mobs_data = [{"id": m.net_id, "type": type(m).__name__, "x": m.hitbox.centerx, "y": m.hitbox.centery, "hp": getattr(m, 'hp', 10), "facing_right": m.facing_right} for m in mobs_group if hasattr(m, 'net_id')]
                        bosses_data = [{"id": b.net_id, "type": type(b).__name__, "x": b.hitbox.centerx, "y": b.hitbox.centery, "hp": getattr(b, 'hp', 10), "facing_right": b.facing_right} for b in bosses_group if hasattr(b, 'net_id')]
                        drops_data = [{"id": d.net_id, "item_id": d.item_id, "x": d.hitbox.centerx, "y": d.hitbox.centery} for d in drops_group if hasattr(d, 'net_id')]
                        projs_data = [{"id": p.net_id, "type": type(p).__name__, "x": p.hitbox.centerx, "y": p.hitbox.centery, "vel_x": p.vel_x, "vel_y": p.vel_y} for p in projectiles_group if hasattr(p, 'net_id')]
                        
                        net_client.send({
                            "cmd": "entity_sync",
                            "mobs": mobs_data,
                            "bosses": bosses_data,
                            "drops": drops_data,
                            "projs": projs_data
                        })
                    
                for msg in net_client.get_messages():
                    cmd = msg.get("cmd")
                    sender = msg.get("sender")
                    
                    if cmd == "player_joined":
                        pid = msg.get("player_id")
                        if pid and pid not in other_players:
                            op = OtherPlayer(cat.hitbox.centerx, cat.hitbox.centery)
                            other_players[pid] = op
                            all_sprites.add(op)
                            
                            # Host sends world state to the new player
                            if net_client.is_host:
                                net_client.send({
                                    "cmd": "world_sync",
                                    "grid": world.grid,
                                    "target_id": pid
                                })
                    
                    elif cmd == "player_left":
                        pid = msg.get("player_id")
                        if pid in other_players:
                            op = other_players.pop(pid)
                            op.kill()
                            
                    elif cmd == "sync":
                        pid = sender
                        if pid and pid not in other_players:
                            op = OtherPlayer(cat.hitbox.centerx, cat.hitbox.centery)
                            other_players[pid] = op
                            all_sprites.add(op)
                            
                        if pid in other_players:
                            op = other_players[pid]
                            op.name = msg.get("name", "Player")
                            op.target_x = msg.get("x", op.target_x)
                            op.target_y = msg.get("y", op.target_y)
                            op.facing_right = msg.get("facing_right", True)
                            op.tool_id = msg.get("tool", None)
                            op.armor_id = msg.get("armor", None)
                            op.boots_id = msg.get("boots", None)
                            op.attacking = msg.get("attacking", False)
                            
                    elif cmd == "world_sync":
                        grid_data = msg.get("grid")
                        if grid_data:
                            world.grid = grid_data
                            
                    elif cmd == "block_break":
                        r, c = msg.get("r"), msg.get("c")
                        if 0 <= r < world.rows and 0 <= c < world.cols:
                            world.grid[r][c] = 0
                        
                    elif cmd == "block_place":
                        r, c = msg.get("r"), msg.get("c")
                        b_id = msg.get("id")
                        if 0 <= r < world.rows and 0 <= c < world.cols:
                            if isinstance(b_id, str):
                                from src.items.items import get_item_def
                                item_def = get_item_def(b_id)
                                if item_def and "place_block" in item_def:
                                    world.grid[r][c] = item_def["place_block"]
                            else:
                                world.grid[r][c] = b_id
                                
                    elif cmd == "pickup_request" and net_client.is_host:
                        req_net_id = msg.get("net_id")
                        for drop in drops_group:
                            if getattr(drop, "net_id", None) == req_net_id:
                                net_client.send({"cmd": "pickup_approve", "target_id": sender, "item_id": drop.item_id})
                                drop.kill()
                                break
                    
                    elif cmd == "pickup_approve":
                        item_id = msg.get("item_id")
                        if inventory.add_item(item_id, 1):
                            pass
                            
                    elif cmd == "entity_sync" and not net_client.is_host:
                        from src.entities.mobs import Bat, Slime, ZombieCat
                        from src.entities.bosses import Gargoyle, AbyssalBehemoth
                        from src.entities.item_drop import ItemDrop
                        from src.entities.projectiles import Arrow, HookProjectile, AbyssalOrb
                        
                        # Process mobs
                        mobs_data = msg.get("mobs", [])
                        current_mobs = {m.net_id: m for m in mobs_group if hasattr(m, 'net_id')}
                        for m_data in mobs_data:
                            net_id = m_data["id"]
                            if net_id in current_mobs:
                                m = current_mobs.pop(net_id)
                                m.target_x = m_data["x"]
                                m.target_y = m_data["y"]
                                m.hp = m_data["hp"]
                                m.facing_right = m_data["facing_right"]
                            else:
                                t = m_data["type"]
                                cls = Bat if t == "Bat" else Slime if t == "Slime" else ZombieCat if t == "ZombieCat" else Bat
                                m = cls(m_data["x"], m_data["y"], world, drops_group)
                                m.net_id = net_id
                                m.target_x = m_data["x"]
                                m.target_y = m_data["y"]
                                m.hp = m_data["hp"]
                                m.facing_right = m_data["facing_right"]
                                mobs_group.add(m)
                        for m in current_mobs.values():
                            m.kill()
                            
                        # Process bosses
                        bosses_data = msg.get("bosses", [])
                        current_bosses = {b.net_id: b for b in bosses_group if hasattr(b, 'net_id')}
                        for b_data in bosses_data:
                            net_id = b_data["id"]
                            if net_id in current_bosses:
                                b = current_bosses.pop(net_id)
                                b.target_x = b_data["x"]
                                b.target_y = b_data["y"]
                                b.hp = b_data["hp"]
                                b.facing_right = b_data["facing_right"]
                            else:
                                t = b_data["type"]
                                cls = Gargoyle if t == "Gargoyle" else AbyssalBehemoth
                                b = cls(b_data["x"], b_data["y"], world, drops_group, projectiles_group)
                                b.net_id = net_id
                                b.target_x = b_data["x"]
                                b.target_y = b_data["y"]
                                b.hp = b_data["hp"]
                                b.facing_right = b_data["facing_right"]
                                bosses_group.add(b)
                        for b in current_bosses.values():
                            b.kill()
                            
                        # Process drops
                        drops_data = msg.get("drops", [])
                        current_drops = {d.net_id: d for d in drops_group if hasattr(d, 'net_id')}
                        for d_data in drops_data:
                            net_id = d_data["id"]
                            if net_id in current_drops:
                                d = current_drops.pop(net_id)
                                d.target_x = d_data["x"]
                                d.target_y = d_data["y"]
                            else:
                                d = ItemDrop(d_data["x"], d_data["y"], d_data["item_id"], world)
                                d.net_id = net_id
                                d.target_x = d_data["x"]
                                d.target_y = d_data["y"]
                                drops_group.add(d)
                        for d in current_drops.values():
                            d.kill()
                            
                        # Process projectiles
                        projs_data = msg.get("projs", [])
                        current_projs = {p.net_id: p for p in projectiles_group if hasattr(p, 'net_id')}
                        for p_data in projs_data:
                            net_id = p_data["id"]
                            if net_id in current_projs:
                                p = current_projs.pop(net_id)
                                p.target_x = p_data["x"]
                                p.target_y = p_data["y"]
                            else:
                                t = p_data["type"]
                                if t == "Arrow":
                                    p = Arrow(p_data["x"], p_data["y"], p_data["vel_x"], p_data["vel_y"], world)
                                elif t == "AbyssalOrb":
                                    p = AbyssalOrb(p_data["x"], p_data["y"], p_data["vel_x"], p_data["vel_y"], world)
                                else:
                                    p = HookProjectile(p_data["x"], p_data["y"], p_data["vel_x"], p_data["vel_y"], world)
                                p.net_id = net_id
                                p.target_x = p_data["x"]
                                p.target_y = p_data["y"]
                                projectiles_group.add(p)
                        for p in current_projs.values():
                            p.kill()
            # --------------------
            
            cat_col, cat_row = cat.tile_pos
            block_at_cat_temp = world.get_work_block_at(cat_col, cat_row)
            if block_at_cat_temp in (BLOCK_CHEST, BLOCK_RARE_CHEST, BLOCK_WORKBENCH, BLOCK_BREWING_STAND, BLOCK_FURNACE):
                touch_ctrl.set_interact_visible(True)
            else:
                touch_ctrl.set_interact_visible(False)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if ui_is_open:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        close_rect = pygame.Rect(20, 20, 40, 40)
                        if close_rect.collidepoint(event.pos):
                            if chest_ui.is_open: chest_ui.close()
                            elif workbench_ui.is_open: workbench_ui.close()
                            elif alchemy_ui.is_open: alchemy_ui.close()
                            elif furnace_ui.is_open: furnace_ui.close()
                            elif inventory.show_full: inventory.toggle()
                            elif cheat_console.is_open: cheat_console.toggle()
                            continue

                if touch_ctrl.handle_event(event, ui_is_open): continue

                if cheat_console.handle_event(event): continue
                if chest_ui.handle_event(event): continue
                if furnace_ui.handle_event(event): continue
                if creative_ui.handle_event(event): continue

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_l:
                        cheat_console.toggle()
                        continue
                    elif event.key == pygame.K_ESCAPE:
                        if workbench_ui.is_open: workbench_ui.close()
                        elif alchemy_ui.is_open: alchemy_ui.close()
                        elif chest_ui.is_open: chest_ui.close()
                        elif furnace_ui.is_open: furnace_ui.close()
                        else: 
                            return_to_menu = True 
                            running = False
                    elif event.key == pygame.K_o:
                        cat_col, cat_row = cat.tile_pos
                        near_rocket = False
                        for r in range(max(0, cat_row - 5), min(world.rows, cat_row + 5)):
                            for c in range(max(0, cat_col - 3), min(world.cols, cat_col + 3)):
                                if world.grid[r][c] == BLOCK_ROCKET:
                                    near_rocket = True
                                    break
                        if near_rocket:
                            game_won = True
                            running = False 
                    elif event.key == pygame.K_e:
                        if chest_ui.is_open: chest_ui.close()
                        elif workbench_ui.is_open: workbench_ui.close()
                        elif alchemy_ui.is_open: alchemy_ui.close()
                        elif furnace_ui.is_open: furnace_ui.close()
                        else:
                            touch_ctrl.interact_pressed = True
                            cat_col, cat_row = cat.tile_pos
                            block_at_cat = world.get_work_block_at(cat_col, cat_row)
                            
                            if block_at_cat in (BLOCK_CHEST, BLOCK_RARE_CHEST): 
                                if block_at_cat == BLOCK_RARE_CHEST and not chest_manager.chest_exists(cat_row, cat_col):
                                    loot_pool = [
                                        "suspicious_slime", "ruby", "titanium_ingot", "titanium_pickaxe",
                                        "ruby_sword", "potion_strength", "potion_fire_res", "potion_jump", "magnum_opus"
                                    ]
                                    slots = [{"id": None, "count": 0} for _ in range(15)]
                                    num_items = random.randint(3, 7)
                                    for i in range(num_items):
                                        item = random.choice(loot_pool)
                                        count = 1
                                        if item in ("ruby", "titanium_ingot", "potion_strength", "potion_fire_res", "potion_jump", "magnum_opus"):
                                            count = random.randint(1, 5)
                    elif event.key == pygame.K_t:
                        mods = pygame.key.get_mods()
                        is_ctrl = mods & pygame.KMOD_CTRL
                        
                        drop_info = inventory.drop_item_logic(inventory.selected_slot, all_stack=is_ctrl)
                        if drop_info:
                            item_id, count = drop_info
                            for _ in range(count):
                                drop = ItemDrop(cat.hitbox.x, cat.hitbox.y, item_id, world)
                                drop.vel_x = random.uniform(3.0, 6.0) if cat.facing_right else random.uniform(-6.0, -3.0)
                                drop.vel_y = random.uniform(-6.0, -3.0)
                                drops_group.add(drop)
                    elif event.key == pygame.K_f:
                        hook_id = inventory.hook_slot.get("id")
                        if hook_id == "grappling_hook" and cat.active_hook is None:
                            world_x = mouse_pos[0] + int(camera_x)
                            world_y = mouse_pos[1] + int(camera_y)
                            dx = world_x - cat.hitbox.centerx
                            dy = world_y - cat.hitbox.centery
                            dist = math.hypot(dx, dy)
                            if dist > 0:
                                vel_x = (dx / dist) * 20
                                vel_y = (dy / dist) * 20
                                hook = HookProjectile(cat.hitbox.centerx, cat.hitbox.centery, vel_x, vel_y, world)
                                projectiles_group.add(hook)
                                cat.active_hook = hook
                    elif event.key == pygame.K_b:
                        world_x = mouse_pos[0] + int(camera_x)
                        world_y = mouse_pos[1] + int(camera_y)
                        boss = Gargoyle(world_x, world_y, world, drops_group)
                        bosses_group.add(boss)
                    else:
                        hotbar_map = {
                            pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2,
                            pygame.K_4: 3, pygame.K_5: 4, pygame.K_6: 5,
                            pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8, pygame.K_0: 9,
                        }
                        if event.key in hotbar_map:
                            inventory.select_slot(hotbar_map[event.key])

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    handled = workbench_ui.on_mouse_down(pos)
                    if not handled: handled = alchemy_ui.on_mouse_down(pos)
                    if not handled: inventory.on_mouse_down(pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    inventory.on_mouse_up(event.pos)

            if touch_ctrl.interact_pressed:
                touch_ctrl.interact_pressed = False
                if chest_ui.is_open: chest_ui.close()
                elif workbench_ui.is_open: workbench_ui.close()
                elif alchemy_ui.is_open: alchemy_ui.close()
                elif furnace_ui.is_open: furnace_ui.close()
                else:
                    cat_col, cat_row = cat.tile_pos
                    block_at_cat = world.get_work_block_at(cat_col, cat_row)
                    
                    if block_at_cat in (BLOCK_CHEST, BLOCK_RARE_CHEST): 
                        if block_at_cat == BLOCK_RARE_CHEST and not chest_manager.chest_exists(cat_row, cat_col):
                            loot_pool = [
                                "suspicious_slime", "ruby", "titanium_ingot", "titanium_pickaxe",
                                "ruby_sword", "potion_strength", "potion_fire_res", "potion_jump", "magnum_opus"
                            ]
                            slots = [{"id": None, "count": 0} for _ in range(15)]
                            num_items = random.randint(3, 7)
                            for i in range(num_items):
                                item = random.choice(loot_pool)
                                count = 1
                                if item in ("ruby", "titanium_ingot", "potion_strength", "potion_fire_res", "potion_jump", "magnum_opus"):
                                    count = random.randint(1, 5)
                                if random.random() < 0.05: item = "lavacalibur"
                                if random.random() < 0.01: item = "OVERPOWERED_SWORD666"
                                slots[i] = {"id": item, "count": count}
                            chest_manager.set_chest(cat_row, cat_col, slots)

                        chest_ui.open(cat_col, cat_row)
                        self.ach_manager.check_event("chest_opened", True)
                    elif block_at_cat == BLOCK_WORKBENCH: workbench_ui.toggle()
                    elif block_at_cat == BLOCK_BREWING_STAND: alchemy_ui.toggle()
                    elif block_at_cat == BLOCK_FURNACE: furnace_ui.open(cat_col, cat_row)
                    else: inventory.toggle()
            
            if touch_ctrl.inv_clicked:
                touch_ctrl.inv_clicked = False
                if cheat_console.is_open: cheat_console.toggle()
                elif chest_ui.is_open: chest_ui.close()
                elif workbench_ui.is_open: workbench_ui.close()
                elif alchemy_ui.is_open: alchemy_ui.close()
                elif furnace_ui.is_open: furnace_ui.close()
                else: inventory.toggle()
                
            if touch_ctrl.menu_clicked:
                touch_ctrl.menu_clicked = False
                return_to_menu = True
                running = False
                    
            if touch_ctrl.zoom_in_clicked:
                zoom_level = min(2.0, zoom_level + 0.1)
                touch_ctrl.zoom_in_clicked = False
            if touch_ctrl.zoom_out_clicked:
                zoom_level = max(0.5, zoom_level - 0.1)
                touch_ctrl.zoom_out_clicked = False

            # --- Speedrun timer ---
            if world.config.get("speedrun", False) and not cheat_console.is_open:
                world.config["play_time"] = world.config.get("play_time", 0.0) + (dt_ms / 1000.0)


            cheat_console.update()
            furnace_manager.update_ticks()
            world.random_tick()
            
            cat_x = cat.hitbox.centerx
            cat_y = cat.hitbox.centery
            
            in_dungeon = False
            dungeon_radius = TILE_SIZE * 10
            
            for boss in bosses_group:
                if math.hypot(cat_x - boss.spawn_pos[0], cat_y - boss.spawn_pos[1]) < dungeon_radius:
                    in_dungeon = True
                    break
                    
            if not in_dungeon:
                for r in respawn_queue:
                    if math.hypot(cat_x - r[0], cat_y - r[1]) < dungeon_radius:
                        in_dungeon = True
                        break

            if in_dungeon:
                audio.play_music("dungeon")
            elif cat_y < TILE_SIZE * 50:
                audio.play_music("overworld")
            else:
                audio.play_music("cave")
                
            audio.update()
            
            # --- MOB SPAWNING ---
            mob_rate = world.config.get("mob_rate", 1)
            
            for mob in list(mobs_group):
                dist = math.hypot(mob.hitbox.centerx - cat.hitbox.centerx, mob.hitbox.centery - cat.hitbox.centery)
                if dist > TILE_SIZE * 50:
                    mob.kill()
                    
            base_chance = 0.05
            if mob_rate == 0: base_chance = 0.02
            elif mob_rate == 2: base_chance = 0.08
            elif mob_rate == 3: base_chance = 0.15
            
            if random.random() < base_chance and len(mobs_group) < 40:
                if not net_client.is_connected or net_client.is_host:
                    spawn_col = int(camera_x // TILE_SIZE) + random.choice([-5, int(WIDTH/TILE_SIZE) + 5])
                    spawn_row = cat.tile_pos[1] + random.randint(-10, 10)
                    if world._in_bounds(spawn_row, spawn_col) and world.grid[spawn_row][spawn_col] in (BLOCK_CAVE, BLOCK_AIR):
                        if spawn_row > 10: 
                            if mob_rate == 0: weights = [1.0, 0.0, 0.0]
                            elif mob_rate == 1: weights = [0.4, 0.4, 0.2]
                            elif mob_rate == 2: weights = [0.2, 0.5, 0.3]
                            else: weights = [0.1, 0.3, 0.6]
                            
                            mob_class = random.choices([Bat, Slime, ZombieCat], weights=weights)[0]
                            mob = mob_class(spawn_col * TILE_SIZE, spawn_row * TILE_SIZE, world, drops_group)
                            mobs_group.add(mob)
            
            if cat.dead:
                save_path = os.path.join("saves", self.settings_manager.active_save)
                if os.path.exists(save_path):
                    shutil.rmtree(save_path)
                self.settings_manager.active_save = "default"
                return "main_menu"
            
            if not cheat_console.is_open and not chest_ui.is_open and not furnace_ui.is_open and not workbench_ui.is_open and not alchemy_ui.is_open:
                mouse_buttons = pygame.mouse.get_pressed()
                if (mouse_buttons[0] or mouse_buttons[2]) and not touch_ctrl.active:
                    # Legacy PC mouse controls
                    action_pos = mouse_pos
                    hovering_hotbar = any(inventory._slot_rect(i).collidepoint(action_pos) for i in range(HOTBAR_SLOTS))
                    is_action = not hovering_hotbar
                elif touch_ctrl.action_hold:
                    # Touch screen / unified action controls
                    action_pos = touch_ctrl.action_hold
                    hovering_hotbar = any(inventory._slot_rect(i).collidepoint(action_pos) for i in range(HOTBAR_SLOTS))
                    is_action = not hovering_hotbar
                    
                    sel_id = inventory.get_selected_slot()["id"]
                    item_def = get_item_def(sel_id) if sel_id else {}
                    if item_def.get("place_block") or sel_id == "bow" or "potion_effect" in item_def or "heal_amount" in item_def or "spawn_boss" in item_def:
                        mouse_buttons = (False, False, True) # Sim right click
                    else:
                        mouse_buttons = (True, False, False) # Sim left click
                else:
                    is_action = False
                    
                if is_action:
                    world_x = (action_pos[0] / zoom_level) + camera_x
                    world_y = (action_pos[1] / zoom_level) + camera_y
                    target_col = int(world_x // TILE_SIZE)
                    target_row = int(world_y // TILE_SIZE)
                    
                    if mouse_buttons[0]:
                        hit_boss = False
                        for boss in bosses_group:
                            dist = math.hypot(boss.hitbox.centerx - cat.hitbox.centerx, boss.hitbox.centery - cat.hitbox.centery)
                            if dist < TILE_SIZE * 3 and cat.attack_cooldown == 0:
                                tool_id = cat._cached_tool
                                dmg = 1 
                                if tool_id:
                                    if "sword" in tool_id: dmg = get_item_def(tool_id).get("damage", 1)
                                    elif "pickaxe" in tool_id: dmg = 0 
                                if cat.active_potion == "strength": dmg *= 2
                                if dmg > 0:
                                    is_dead = boss.take_damage(dmg, cat.hitbox.centerx)
                                    if is_dead:
                                        self.ach_manager.check_event("boss_kill", "gargoyle")
                                        respawn_queue.append([boss.spawn_pos[0], boss.spawn_pos[1], 7200])
                                cat.facing_right = (boss.hitbox.centerx > cat.hitbox.centerx)
                                cat.attack_cooldown = ATTACK_COOLDOWN
                                hit_boss = True
                                
                        hit_mob = False
                        if not hit_boss:
                            for mob in list(mobs_group):
                                dist = math.hypot(mob.hitbox.centerx - cat.hitbox.centerx, mob.hitbox.centery - cat.hitbox.centery)
                                if dist < TILE_SIZE * 3 and cat.attack_cooldown == 0:
                                    tool_id = cat._cached_tool
                                    dmg = 1 
                                    if tool_id:
                                        if "sword" in tool_id: dmg = get_item_def(tool_id).get("damage", 1)
                                        elif "pickaxe" in tool_id: dmg = 0 
                                    if cat.active_potion == "strength": dmg *= 2
                                    if dmg > 0:
                                        is_dead = mob.take_damage(dmg, cat.hitbox.centerx)
                                        if is_dead:
                                            if isinstance(mob, Slime): self.ach_manager.check_event("mob_kill", "slime")
                                            elif isinstance(mob, ZombieCat): self.ach_manager.check_event("mob_kill", "zombie_cat")
                                    cat.facing_right = (mob.hitbox.centerx > cat.hitbox.centerx)
                                    cat.attack_cooldown = ATTACK_COOLDOWN
                                    hit_mob = True
                                
                        if not hit_boss and not hit_mob:
                            sel_id = inventory.get_selected_slot()["id"]
                            if sel_id in ("fishing_rod", "lava_fishing_rod") and world.grid[target_row][target_col] in (BLOCK_WATER, BLOCK_LAVA):
                                fish_res = cat.try_fish(target_col, target_row)
                                if fish_res == "lava_fish": self.ach_manager.check_event("lava_fish", True)
                            else:
                                broken_id = cat.try_break_block(target_col, target_row)
                                if broken_id is not None:
                                    if broken_id == BLOCK_GOLD_ORE: self.ach_manager.check_event("gold_mined", 1)
                                    if net_client.is_connected:
                                        net_client.send({"cmd": "block_break", "r": target_row, "c": target_col})
                            
                    elif mouse_buttons[2]: 
                        sel_id = inventory.get_selected_slot()["id"]
                        item_def = get_item_def(sel_id) if sel_id else {}
                        if sel_id == "bow" and cat.attack_cooldown == 0:
                            dx = world_x - cat.hitbox.centerx
                            dy = world_y - cat.hitbox.centery
                            dist = math.hypot(dx, dy)
                            if dist > 0:
                                vel_x = (dx / dist) * 15
                                vel_y = (dy / dist) * 15
                                arrow = Arrow(cat.hitbox.centerx, cat.hitbox.centery, vel_x, vel_y, world)
                                projectiles_group.add(arrow)
                                cat.attack_cooldown = int(ATTACK_COOLDOWN * 2.5)
                        elif "heal_amount" in item_def and cat.hp < cat.max_hp:
                            if cat.attack_cooldown == 0:
                                cat.heal(item_def["heal_amount"])
                                inventory.consume_item(sel_id, 1)
                                cat.attack_cooldown = ATTACK_COOLDOWN
                        elif "potion_effect" in item_def:
                            if cat.attack_cooldown == 0:
                                cat.apply_potion(item_def["potion_effect"])
                                inventory.consume_item(sel_id, 1)
                                cat.attack_cooldown = ATTACK_COOLDOWN
                                self.ach_manager.check_event("potion_consumed", True)
                        elif "spawn_boss" in item_def:
                            if cat.attack_cooldown == 0:
                                boss_type = item_def["spawn_boss"]
                                if boss_type == "abyssal_behemoth":
                                    b = AbyssalBehemoth(target_col * TILE_SIZE, target_row * TILE_SIZE, world, drops_group, projectiles_group)
                                    bosses_group.add(b)
                                    audio.play_sfx("boss_spawn")
                                cat.attack_cooldown = ATTACK_COOLDOWN * 2
                        elif sel_id != "bow":
                            placed = cat.try_place_block(target_col, target_row)
                            if placed and net_client.is_connected:
                                net_client.send({"cmd": "block_place", "r": target_row, "c": target_col, "id": sel_id})
                
                for drop in list(drops_group):
                    can_pickup = getattr(drop, "pickup_delay", 0) <= 0
                    if can_pickup and cat.hitbox.colliderect(drop.rect):
                        if net_client.is_connected and not net_client.is_host:
                            net_client.send({"cmd": "pickup_request", "net_id": getattr(drop, "net_id", "")})
                            drop.pickup_delay = 30
                        else:
                            if inventory.add_item(drop.item_id): drop.kill()
                            
                drops_group.update()
                bosses_group.update(cat) 
                mobs_group.update(cat)
                projectiles_group.update()
                all_sprites.update(touch_ctrl=touch_ctrl)
                
                pet_id = inventory.pet_slot["id"]
                if pet_id == "suspicious_slime":
                    if not active_pet:
                        from src.entities.pets import PetSlime
                        active_pet = PetSlime(cat, world)
                    active_pet.update()
                else:
                    if active_pet:
                        active_pet.kill()
                        active_pet = None
                
                for p in list(projectiles_group):
                    if not p.stuck:
                        if getattr(p, "is_enemy", False):
                            if p.hitbox.colliderect(cat.hitbox):
                                cat.take_damage(p.damage, p.hitbox.centerx)
                                p.kill()
                        else:
                            for boss in list(bosses_group):
                                if p.hitbox.colliderect(boss.hitbox):
                                    boss.take_damage(p.damage, p.hitbox.centerx)
                                    p.kill()
                                    break
                            if p.alive():
                                for mob in list(mobs_group):
                                    if p.hitbox.colliderect(mob.hitbox):
                                        is_dead = mob.take_damage(p.damage, p.hitbox.centerx)
                                        if is_dead:
                                            if isinstance(mob, Slime): self.ach_manager.check_event("mob_kill", "slime")
                                            elif isinstance(mob, ZombieCat): self.ach_manager.check_event("mob_kill", "zombie_cat")
                                        p.kill()
                                        break

                # Lava damage
                cat_in_lava = False
                for sprite in list(bosses_group) + list(mobs_group) + [cat]:
                    if hasattr(sprite, "hitbox") and hasattr(sprite, "take_damage"):
                        col = sprite.hitbox.centerx // TILE_SIZE
                        row = sprite.hitbox.centery // TILE_SIZE
                        if world._in_bounds(row, col) and world.grid[row][col] == BLOCK_LAVA:
                            if sprite == cat:
                                cat_in_lava = True
                                if cat.active_potion == "fire_res": continue
                            sprite.take_damage(3, sprite.hitbox.centerx + random.choice([-10, 10]))
                
                if cat_in_lava:
                    lava_timer += 1
                    if lava_timer >= FPS * 5:
                        self.ach_manager.check_event("lava_time", 5)
                else:
                    lava_timer = 0
                
                if cat.tile_pos[1] >= 100:
                    self.ach_manager.check_event("depth_reached", cat.tile_pos[1])
                
                for boss in bosses_group:
                    if boss.hitbox.colliderect(cat.hitbox):
                        cat.take_damage(boss.damage, boss.hitbox.centerx)
                        
                for mob in mobs_group:
                    if mob.damage > 0 and mob.hitbox.colliderect(cat.hitbox):
                        cat.take_damage(mob.damage, mob.hitbox.centerx)



            cat_col, cat_row = cat.tile_pos
            block_at_cat     = world.get_work_block_at(cat_col, cat_row)
            
            if block_at_cat != BLOCK_WORKBENCH and workbench_ui.is_open: workbench_ui.close()
            if block_at_cat != BLOCK_BREWING_STAND and alchemy_ui.is_open: alchemy_ui.close()
            if block_at_cat not in (BLOCK_CHEST, BLOCK_RARE_CHEST) and chest_ui.is_open: chest_ui.close()
            if block_at_cat != BLOCK_FURNACE and furnace_ui.is_open: furnace_ui.close()

            target_camera_x = cat.hitbox.centerx - (current_w / zoom_level) // 2
            max_camera_x = max(0, (world.cols * TILE_SIZE) - (current_w / zoom_level))
            camera_x = max(0, min(target_camera_x, max_camera_x))

            target_camera_y = cat.hitbox.centery - (current_h / zoom_level) // 2
            max_camera_y = max(0, (world.rows * TILE_SIZE) - (current_h / zoom_level))
            camera_y = max(0, min(target_camera_y, max_camera_y))

            if cat.hitbox.right > (world.cols - 15) * TILE_SIZE:
                world.expand_right(20)
                
            if not net_client.is_connected or net_client.is_host:
                while world.pending_boss_spawns:
                    bx, by = world.pending_boss_spawns.pop()
                    boss = Gargoyle(bx, by, world, drops_group)
                    bosses_group.add(boss)
                    
                for r in respawn_queue[:]:
                    r[2] -= 1
                    if r[2] <= 0:
                        bosses_group.add(Gargoyle(r[0], r[1], world, drops_group))
                        respawn_queue.remove(r)

            # --- SCALED RENDERING ---
            game_surf = pygame.Surface((int(current_w / zoom_level), int(current_h / zoom_level)))
            game_surf.fill((135, 206, 235)) # Sky color (if needed, world.draw does it)
            world.draw(game_surf, int(camera_x), int(camera_y))
            
            for drop in drops_group:
                game_surf.blit(drop.image, (drop.rect.x - int(camera_x), drop.rect.y - int(camera_y)))
                
            for projectile in projectiles_group:
                game_surf.blit(projectile.image, (projectile.rect.x - int(camera_x), projectile.rect.y - int(camera_y)))
                
            for mob in mobs_group:
                game_surf.blit(mob.image, (mob.rect.x - int(camera_x), mob.rect.y - int(camera_y)))
                
            for boss in bosses_group:
                game_surf.blit(boss.image, (boss.rect.x - int(camera_x), boss.rect.y - int(camera_y)))
                
            for sprite in all_sprites:
                if getattr(sprite, "invuln_timer", 0) > 0 and (sprite.invuln_timer // 5) % 2 == 0:
                    pass 
                else:
                    game_surf.blit(sprite.image, (sprite.rect.x - int(camera_x), sprite.rect.y - int(camera_y)))
                    
            if active_pet:
                game_surf.blit(active_pet.image, (active_pet.rect.x - int(camera_x), active_pet.rect.y - int(camera_y)))
            
            if cat.active_hook:
                start_pos = (cat.rect.centerx - int(camera_x), cat.rect.centery - int(camera_y))
                end_pos = (cat.active_hook.rect.centerx - int(camera_x), cat.active_hook.rect.centery - int(camera_y))
                pygame.draw.line(game_surf, (139, 69, 19), start_pos, end_pos, 2)
            
            scaled_surf = pygame.transform.scale(game_surf, (current_w, current_h))
            self.screen.blit(scaled_surf, (0, 0))
            
            # --- UI RENDERING ---
            stats_ui.draw(self.screen, cat)
            inventory.draw(self.screen, mouse_pos)
            creative_ui.draw(self.screen, mouse_pos)
            workbench_ui.draw(self.screen, mouse_pos)
            alchemy_ui.draw(self.screen, mouse_pos)
            
            if world.config.get("speedrun", False):
                pt = world.config.get("play_time", 0.0)
                mins = int(pt // 60)
                secs = int(pt % 60)
                ms = int((pt * 100) % 100)
                timer_str = f"{mins:02}:{secs:02}.{ms:02}"
                timer_surf = font_timer.render(timer_str, True, (255, 255, 255))
                shadow_surf = font_timer.render(timer_str, True, (0, 0, 0))
                self.screen.blit(shadow_surf, (current_w // 2 - shadow_surf.get_width() // 2 + 2, 12))
                self.screen.blit(timer_surf, (current_w // 2 - timer_surf.get_width() // 2, 10))

            if net_client.is_connected:
                if net_client.is_host:
                    if not hasattr(net_client, '_cached_host_ip'):
                        import socket
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.settimeout(0)
                        try:
                            s.connect(('10.254.254.254', 1))
                            net_client._cached_host_ip = s.getsockname()[0]
                        except Exception:
                            net_client._cached_host_ip = "127.0.0.1"
                        finally:
                            s.close()
                    rc_str = f"Host IP: {net_client._cached_host_ip}"
                else:
                    rc_str = f"Connected to: {net_client.host}"
                    
                rc_surf = font_timer.render(rc_str, True, (255, 200, 50))
                rc_bg = pygame.Rect(20, 20, rc_surf.get_width() + 10, rc_surf.get_height() + 10)
                pygame.draw.rect(self.screen, (30, 30, 30), rc_bg, border_radius=5)
                pygame.draw.rect(self.screen, (255, 200, 50), rc_bg, 2, border_radius=5)
                self.screen.blit(rc_surf, (rc_bg.x + 5, rc_bg.y + 5))

            chest_ui.draw(self.screen, mouse_pos)
            furnace_ui.draw(self.screen, mouse_pos)
            
            cheat_console.draw(self.screen)
            touch_ctrl.draw(self.screen)
            
            if ui_is_open:
                close_rect = pygame.Rect(20, 20, 40, 40)
                pygame.draw.rect(self.screen, (200, 50, 50), close_rect, border_radius=5)
                pygame.draw.rect(self.screen, (100, 20, 20), close_rect, 2, border_radius=5)
                cross_font = pygame.font.SysFont(None, 36)
                cross_txt = cross_font.render("X", True, (255, 255, 255))
                self.screen.blit(cross_txt, cross_txt.get_rect(center=close_rect.center))
                
            paw_cursor.draw(self.screen, mouse_pos)

            self.ach_manager.check_inventory(inventory)
            self.ach_manager.update()
            self.ach_manager.draw(self.screen)

            pygame.display.flip()
        inventory.save()
        chest_manager.save()
        furnace_manager.save()
        world.save()
        world.save_config()
        
        if game_won:
            self.ach_manager.check_event("launch", "rocket") 
            if world.config.get("speedrun", False):
                lb_path = os.path.join("data", "leaderboard.json")
                os.makedirs("data", exist_ok=True)
                records = []
                if os.path.exists(lb_path):
                    with open(lb_path, "r", encoding="utf-8") as f:
                        records = json.load(f)
                records.append({
                    "world": self.manager.active_save,
                    "time": world.config.get("play_time", 0.0),
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
                with open(lb_path, "w", encoding="utf-8") as f:
                    json.dump(records, f, indent=4)
                    
            return "end_screen"
        elif return_to_menu:
            return "main_menu"
        return "quit"
