"""bot/ papkasidan ishga tushirish uchun.

Asosiy kirish: loyiha ildizida `python main.py`.
Agar siz `bot` ichida bo'lsangiz, shu fayl ildizdagi main.py ni ishga tushiradi.
"""

from pathlib import Path

import runpy

ROOT = Path(__file__).resolve().parent.parent
runpy.run_path(ROOT / "main.py", run_name="__main__")
