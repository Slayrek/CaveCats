# ============================================================
#  chest_manager.py — управління даними скриньок
# ============================================================

import json
import os
from src.core.settings import CHEST_SLOTS, MAX_STACK
from src.items.items import get_item_def

def _chest_id(row: int, col: int) -> str:
    """Формує рядковий ключ скриньки за координатами."""
    return f"{row}_{col}"

def _empty_chest() -> list[dict]:
    """Повертає порожні слоти для нової скриньки."""
    return [{"id": None, "count": 0} for _ in range(CHEST_SLOTS)]

class ChestManager:
    # --- НОВЕ: ПРИЙМАЄМО ШЛЯХ ДО ПАПКИ СЕЙВУ ---
    def __init__(self, folder="saves/default") -> None:
        self.folder = folder
        self._file = os.path.join(self.folder, "chests.json")
        self._data: dict = self._load()

    def _load(self) -> dict:
        if os.path.exists(self._file):
            try:
                with open(self._file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                if "chests" in raw and isinstance(raw["chests"], dict):
                    return raw
            except (json.JSONDecodeError, TypeError, KeyError):
                pass
        return {"chests": {}}

    def save(self) -> None:
        with open(self._file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def get_chest(self, row: int, col: int) -> list[dict]:
        cid = _chest_id(row, col)
        if cid not in self._data["chests"]:
            self._data["chests"][cid] = _empty_chest()
            self.save()
        slots = self._data["chests"][cid]
        # Вирівнюємо кількість слотів (захист при зміні CHEST_SLOTS)
        while len(slots) < CHEST_SLOTS:
            slots.append({"id": None, "count": 0})
        return slots[:CHEST_SLOTS]

    def set_chest(self, row: int, col: int, slots: list[dict]) -> None:
        cid = _chest_id(row, col)
        self._data["chests"][cid] = slots[:CHEST_SLOTS]
        self.save()

    def remove_chest(self, row: int, col: int) -> list[dict]:
        cid = _chest_id(row, col)
        if cid in self._data["chests"]:
            contents = self._data["chests"].pop(cid)
            self.save()
            return contents
        return []

    def chest_exists(self, row: int, col: int) -> bool:
        return _chest_id(row, col) in self._data["chests"]

    def add_item(self, row: int, col: int, item_id: str, count: int = 1) -> bool:
        slots     = self.get_chest(row, col)
        max_stack = get_item_def(item_id).get("max_stack", MAX_STACK)
        remaining = count

        for slot in slots:
            if slot["id"] == item_id and slot["count"] < max_stack:
                space = max_stack - slot["count"]
                added = min(remaining, space)
                slot["count"] += added
                remaining -= added
                if remaining == 0:
                    self.set_chest(row, col, slots)
                    return True

        for slot in slots:
            if slot["id"] is None:
                slot["id"]    = item_id
                slot["count"] = remaining
                self.set_chest(row, col, slots)
                return True

        return False 

    def remove_item(self, row: int, col: int, item_id: str, count: int = 1) -> bool:
        slots = self.get_chest(row, col)
        for slot in slots:
            if slot["id"] == item_id and slot["count"] >= count:
                slot["count"] -= count
                if slot["count"] == 0:
                    slot["id"] = None
                self.set_chest(row, col, slots)
                return True
        return False