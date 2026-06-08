# ============================================================
#  items.py — База даних усіх предметів
# ============================================================

from src.world.blocks import (
    BLOCK_STONE, BLOCK_WOOD_LOG,
    BLOCK_WORKBENCH, BLOCK_FURNACE, BLOCK_CHEST, BLOCK_LADDER,
    BLOCK_COAL_ORE, BLOCK_IRON_ORE, BLOCK_GOLD_ORE, BLOCK_TITANIUM_ORE,
    BLOCK_COPPER_ORE, 
    BLOCK_ROCKET_PAD_CENTER,
    BLOCK_ROCKET 
)

from src.core.data_loader import data_manager, get_item_def

ITEM_DEFS = data_manager.items