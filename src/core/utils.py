"""
Helper utilities shared across the extraction pipeline.
"""

import json
from pathlib import Path
from typing import Any, Union

def slugify(text: str) -> str:
    """Convert text to a safe URL/file path string."""
    if not text:
        return "unknown"
    return text.replace("/", "-").replace(" ", "-").replace("(", "").replace(")", "").replace("\\", "-")


def save_json(filepath: Union[str, Path], data: Any) -> None:
    """Safely saves JSON data to a file, ensuring parents exist."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def load_json(filepath: Union[str, Path], default: Any = None) -> Any:
    """Loads JSON data from file, falling back to default if impossible."""
    path = Path(filepath)
    if not path.exists():
        return default if default is not None else {}
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}
