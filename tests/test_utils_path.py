from pathlib import Path
from vbook.utils.path import resolve_output_dir, get_cache_dir

def test_mirror_structure():
    source_root = Path("/videos")
    output_root = Path("/output")
    video = Path("/videos/course1/lesson1.mp4")
    result = resolve_output_dir(video, source_root, output_root, structure="mirror")
    assert result == Path("/output/course1/lesson1")

def test_mirror_nested():
    source_root = Path("/videos")
    output_root = Path("/output")
    video = Path("/videos/course1/section2/lesson3.mp4")
    result = resolve_output_dir(video, source_root, output_root, structure="mirror")
    assert result == Path("/output/course1/section2/lesson3")

def test_get_cache_dir():
    output_dir = Path("/output/course1/lesson1")
    cache = get_cache_dir(output_dir, ".vbook_cache")
    assert cache == Path("/output/course1/lesson1/.vbook_cache")