import os
import sys

# Ensure src is in pythonpath
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.engine import GameEngine
from src.ui.main_menu import MainMenu
from src.ui.worlds_screen import WorldsScreen
from src.ui.create_world_screen import CreateWorldScreen
from src.ui.end_screen import EndScreen
from src.ui.leaderboard_screen import LeaderboardScreen

if __name__ == "__main__":
    game = GameEngine()

    import sys
    if "--auto-host" in sys.argv:
        from src.network.network_client import net_client
        net_client.connect()
        net_client.create_room()
        game.state = "worlds"
    elif any(arg.startswith("--auto-join=") for arg in sys.argv):
        room = next(arg.split("=")[1] for arg in sys.argv if arg.startswith("--auto-join="))
        from src.network.network_client import net_client
        net_client.connect()
        net_client.join_room(room)
        game.settings_manager.active_save = "multiplayer_client"
        game.state = "game"

    game.run()