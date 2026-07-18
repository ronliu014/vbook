import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TranscriptJsonPackage:
    json_path: Path
    segment_count: int


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create coarse timestamped transcript JSON from a vtext vBook bundle."
    )
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--duration-seconds", type=float)
    parser.add_argument("--max-segment-chars", type=int, default=280)
    parser.add_argument("--language", default="zh")
    args = parser.parse_args(argv)

    package = write_transcript_json_from_bundle(
        bundle_dir=args.bundle_dir,
        output=args.output,
        duration_seconds=args.duration_seconds,
        max_segment_chars=args.max_segment_chars,
        language=args.language,
    )
    print(str(package.json_path))
    return 0


def write_transcript_json_from_bundle(
    *,
    bundle_dir: Path | str,
    output: Path | str,
    duration_seconds: float | None = None,
    max_segment_chars: int = 280,
    language: str = "zh",
) -> TranscriptJsonPackage:
    bundle = Path(bundle_dir)
    manifest = _read_json(bundle / "manifest.json")
    text_path = _bundle_output_path(bundle, manifest, "clean_txt")
    text_source = "clean_txt"
    if not text_path.is_file():
        text_path = _bundle_output_path(bundle, manifest, "raw_txt")
        text_source = "raw_txt"
    if not text_path.is_file():
        raise FileNotFoundError(f"vtext bundle transcript text does not exist: {text_path}")

    duration = (
        float(duration_seconds)
        if duration_seconds is not None
        else _probe_video_duration(_source_video_path(manifest))
    )
    if duration <= 0:
        raise ValueError("duration_seconds must be greater than 0")
    chunks = _chunk_text(text_path.read_text(encoding="utf-8-sig"), max_segment_chars)
    segments = _segments_from_chunks(chunks, duration, language=language)
    payload = {
        "schema_version": "1",
        "kind": "vbook_coarse_transcript_json",
        "source": {
            "strategy": "coarse_uniform_from_vtext_clean_text",
            "bundle_dir": str(bundle),
            "source_video": str(_source_video_path(manifest)),
            "text_source": text_source,
            "text_path": str(text_path),
            "duration_seconds": duration,
            "quality": "coarse_timing_for_visual_lesson_output",
        },
        "segments": segments,
    }
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return TranscriptJsonPackage(json_path=output_path, segment_count=len(segments))


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return data


def _bundle_output_path(bundle: Path, manifest: dict[str, Any], key: str) -> Path:
    outputs = manifest.get("outputs")
    if not isinstance(outputs, dict):
        return bundle / key
    value = outputs.get(key)
    if not isinstance(value, str) or not value:
        return bundle / key
    return bundle / value


def _source_video_path(manifest: dict[str, Any]) -> Path:
    source = manifest.get("source_video")
    if not isinstance(source, str) or not source:
        raise ValueError("vtext bundle manifest requires source_video")
    return Path(source)


def _probe_video_duration(video_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ValueError(f"ffprobe failed for {video_path}: {detail}")
    try:
        return float(result.stdout.strip())
    except ValueError as exc:
        raise ValueError(f"ffprobe returned invalid duration for {video_path}") from exc


def _chunk_text(text: str, max_segment_chars: int) -> list[str]:
    if max_segment_chars <= 0:
        raise ValueError("max_segment_chars must be greater than 0")
    words = [word for word in text.split() if word]
    if not words:
        compact = "".join(text.split())
        return [
            compact[index : index + max_segment_chars]
            for index in range(0, len(compact), max_segment_chars)
            if compact[index : index + max_segment_chars]
        ]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        extra = len(word) + (1 if current else 0)
        if current and current_len + extra > max_segment_chars:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
            continue
        current.append(word)
        current_len += extra
    if current:
        chunks.append(" ".join(current))
    return chunks


def _segments_from_chunks(
    chunks: list[str],
    duration_seconds: float,
    *,
    language: str,
) -> list[dict[str, Any]]:
    if not chunks:
        return []
    weights = [max(len(chunk), 1) for chunk in chunks]
    total_weight = sum(weights)
    segments = []
    cursor = 0.0
    for index, (chunk, weight) in enumerate(zip(chunks, weights), start=1):
        if index == len(chunks):
            end = duration_seconds
        else:
            end = cursor + duration_seconds * weight / total_weight
        segments.append(
            {
                "start": round(cursor, 3),
                "end": round(max(end, cursor), 3),
                "text": chunk,
                "language": language,
                "confidence": None,
            }
        )
        cursor = end
    return segments


if __name__ == "__main__":
    raise SystemExit(main())
