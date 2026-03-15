import json
from pathlib import Path
from typing import Any


class Excel:
    def __init__(self) -> None:
        self.character_table: dict[str, Any] = {}
        self.item_table: dict[str, Any] = {}
        self.gacha_table: dict[str, Any] = {}

    def init(self, root: Path | None = None) -> None:
        base = (root or Path.cwd()) / "excel"
        self.character_table = json.loads((base / "character_table.json").read_text())
        self.item_table = json.loads((base / "item_table.json").read_text())
        self.gacha_table = json.loads((base / "gacha_table.json").read_text())
