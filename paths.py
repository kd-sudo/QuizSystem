import sys
from pathlib import Path


def get_db_path(db_name: str = "quiz_system.db") -> str:
    """Завжди повертає шлях до quiz_system.db поруч із .exe або поруч із кодом."""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parent
    return str(base_dir / db_name)