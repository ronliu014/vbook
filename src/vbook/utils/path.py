from pathlib import Path

def resolve_output_dir(
    video_path: Path,
    source_root: Path,
    output_root: Path,
    structure: str = "mirror",
) -> Path:
    relative = video_path.relative_to(source_root)
    stem_path = relative.parent / relative.stem
    return output_root / stem_path

def get_cache_dir(output_dir: Path, cache_dir_name: str = ".vbook_cache") -> Path:
    return output_dir / cache_dir_name