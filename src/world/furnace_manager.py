# ============================================================
#  furnace_manager.py — логіка плавки для всіх пічок у світі
# ============================================================

import json
import os
from src.core.settings import FPS, MAX_STACK
from src.items.items import get_item_def

# Рецепти (час вказано в секундах, ми множимо на FPS для кадрів)
SMELTING_RECIPES = {
    "iron_ore":     {"result": "iron_ingot",     "time": 5 * FPS},
    "gold_ore":     {"result": "gold_ingot",     "time": 10 * FPS},
    "titanium_ore": {"result": "titanium_ingot", "time": 15 * FPS},
}

# 1 вугілля горить 20 секунд
COAL_BURN_TIME = 20 * FPS 

def _furnace_id(row: int, col: int) -> str:
    return f"{row}_{col}"

def _empty_furnace() -> dict:
    return {
        "input":  {"id": None, "count": 0},
        "fuel":   {"id": None, "count": 0},
        "output": {"id": None, "count": 0},
        "burn_time": 0,         # Скільки кадрів ще горітиме поточне вугілля
        "max_burn_time": 1,     # Для відмальовки вогника
        "smelt_progress": 0,    # Скільки кадрів вже плавиться руда
    }

class FurnaceManager:
    # --- НОВЕ: ПРИЙМАЄМО ШЛЯХ ДО ПАПКИ СЕЙВУ ---
    def __init__(self, folder="saves/default"):
        self.folder = folder
        self._file = os.path.join(self.folder, "furnaces.json")
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"furnaces": {}}

    def save(self) -> None:
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get_furnace(self, row: int, col: int) -> dict:
        fid = _furnace_id(row, col)
        if fid not in self._data["furnaces"]:
            self._data["furnaces"][fid] = _empty_furnace()
            self.save()
        return self._data["furnaces"][fid]

    def remove_furnace(self, row: int, col: int) -> list[dict]:
        """Коли пічку ламають, повертаємо всі ресурси з неї."""
        fid = _furnace_id(row, col)
        if fid in self._data["furnaces"]:
            f_data = self._data["furnaces"].pop(fid)
            self.save()
            return [f_data["input"], f_data["fuel"], f_data["output"]]
        return []

    def update_ticks(self) -> None:
        """Цей метод треба буде викликати в головному циклі (main.pyw) кожен кадр."""
        for fid, f in self._data["furnaces"].items():
            inp = f["input"]
            fuel = f["fuel"]
            out = f["output"]

            # Чи є що плавити і чи є місце на виході?
            recipe = SMELTING_RECIPES.get(inp["id"])
            can_smelt = False
            
            if recipe:
                if out["id"] is None or (out["id"] == recipe["result"] and out["count"] < MAX_STACK):
                    can_smelt = True

            # Якщо можемо плавити, але пічка не горить і є вугілля — підпалюємо!
            if can_smelt and f["burn_time"] <= 0 and fuel["id"] == "coal" and fuel["count"] > 0:
                fuel["count"] -= 1
                if fuel["count"] == 0: fuel["id"] = None
                f["burn_time"] = COAL_BURN_TIME
                f["max_burn_time"] = COAL_BURN_TIME

            # Якщо пічка горить — витрачаємо паливо
            if f["burn_time"] > 0:
                f["burn_time"] -= 1
                
                # Якщо ще й є що плавити — прогрес іде
                if can_smelt:
                    f["smelt_progress"] += 1
                    if f["smelt_progress"] >= recipe["time"]:
                        # ПЛАВКА ЗАВЕРШЕНА!
                        f["smelt_progress"] = 0
                        inp["count"] -= 1
                        if inp["count"] == 0: inp["id"] = None
                        
                        out["id"] = recipe["result"]
                        out["count"] += 1
                else:
                    # Якщо немає що плавити, прогрес скидається
                    f["smelt_progress"] = 0
            else:
                # Згасла — прогрес охолоджується (скидається)
                f["smelt_progress"] = 0