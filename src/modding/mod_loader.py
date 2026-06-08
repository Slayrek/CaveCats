import os
import sys
import importlib.util
import json
from src.modding.mod_api import ModAPI

class ModLoader:
    def __init__(self, mods_dir="mods"):
        self.mods_dir = mods_dir
        self.loaded_mods = []
        
    def init_mods(self):
        """Scans and loads all mods from the mods directory."""
        if not os.path.exists(self.mods_dir):
            os.makedirs(self.mods_dir)
            print(f"Created mods directory at: {self.mods_dir}")
            return
            
        for folder_name in os.listdir(self.mods_dir):
            mod_path = os.path.join(self.mods_dir, folder_name)
            if os.path.isdir(mod_path):
                self._load_mod(folder_name, mod_path)
                
    def _load_mod(self, folder_name, mod_path):
        mod_json_path = os.path.join(mod_path, "mod.json")
        main_py_path = os.path.join(mod_path, "main.py")
        
        if not os.path.exists(mod_json_path) or not os.path.exists(main_py_path):
            return
            
        with open(mod_json_path, "r", encoding="utf-8") as f:
            try:
                mod_meta = json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading mod.json for {folder_name}")
                return
                
        mod_id = mod_meta.get("id", folder_name)
        
        # Dynamically load main.py
        spec = importlib.util.spec_from_file_location(f"mods.{mod_id}.main", main_py_path)
        if spec and spec.loader:
            mod_module = importlib.util.module_from_spec(spec)
            sys.modules[f"mods.{mod_id}.main"] = mod_module
            try:
                spec.loader.exec_module(mod_module)
                api = ModAPI(mod_id)
                if hasattr(mod_module, "load_mod"):
                    mod_module.load_mod(api)
                    self.loaded_mods.append(mod_id)
                    print(f"Successfully loaded mod: {mod_id}")
                else:
                    print(f"Mod {mod_id} has no load_mod(api) function.")
            except Exception as e:
                print(f"Error executing mod {mod_id}: {e}")
