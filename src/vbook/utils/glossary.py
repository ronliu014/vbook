# src/vbook/utils/glossary.py
from pathlib import Path
from typing import Optional
import yaml
from .logger import get_logger

logger = get_logger(__name__)


def load_glossary(glossary_path: Optional[str]) -> Optional[dict]:
    if glossary_path is None:
        return None
    path = Path(glossary_path)
    if not path.exists():
        logger.warning("术语词表文件不存在: %s", glossary_path)
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    logger.info("加载术语词表: %s (%d 个术语)", data.get("domain", ""), len(data.get("terms", [])))
    return data


def extract_hotwords(glossary: Optional[dict]) -> list[str]:
    if glossary is None:
        return []
    return [t["term"] for t in glossary.get("terms", [])]
