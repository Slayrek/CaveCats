import json
import os
from src.core.utils import resource_path

class DataLoader:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.blocks = {}
        self.items = {}

    def load_all(self):
        blocks_path = resource_path(os.path.join(self.data_dir, "blocks.json"))
        items_path = resource_path(os.path.join(self.data_dir, "items.json"))
        
        if os.path.exists(blocks_path):
            with open(blocks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.blocks.clear()
                self.blocks.update({int(k): v for k, v in data.items()})
        
        if os.path.exists(items_path):
            with open(items_path, "r", encoding="utf-8") as f:
                self.items.clear()
                self.items.update(json.load(f))

    def get_block_def(self, block_id: int) -> dict:
        return self.blocks.get(block_id, {})

    def get_item_def(self, item_id: str) -> dict:
        return self.items.get(item_id, {})
        
    def add_item_def(self, item_id: str, item_def: dict):
        self.items[item_id] = item_def
        
    def add_block_def(self, block_id: int, block_def: dict):
        self.blocks[block_id] = block_def

# Singleton instance to be used across the codebase
data_manager = DataLoader()

# For backwards compatibility with old code during transition
def get_item_def(item_id: str) -> dict:
    return data_manager.get_item_def(item_id)
