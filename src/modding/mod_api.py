from src.core.data_loader import data_manager

class ModAPI:
    def __init__(self, mod_id: str):
        self.mod_id = mod_id
        
    def register_item(self, item_id: str, item_data: dict):
        """Register a new item or override an existing one."""
        data_manager.add_item_def(item_id, item_data)
        print(f"[{self.mod_id}] Registered item: {item_id}")
        
    def register_block(self, block_id: int, block_data: dict):
        """Register a new block or override an existing one."""
        data_manager.add_block_def(block_id, block_data)
        print(f"[{self.mod_id}] Registered block: {block_id}")
