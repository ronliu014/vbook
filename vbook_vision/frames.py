"""Frame candidate extraction helpers."""

from __future__ import annotations

import hashlib
import subprocess
import shutil
from dataclasses import replace
from pathlib import Path
from typing import Callable

from vbook_common.types import FilterStatus, FrameCandidate

FrameCommandRunner = Callable[[list[str]], None]
FrameCopier = Callable[[Path, Path], object]


def build_ffmpeg_frame_command(
    video_path: Path | str,
    candidate_dir: Path | str,
    interval_seconds: float,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    """Build the ffmpeg command used to extract candidate frames."""
    interval = _require_positive_interval(interval_seconds)
    output_pattern = Path(candidate_dir) / "frame_%06d.jpg"
    fps = _format_fps_interval(interval)
    return [
        ffmpeg_bin,
        "-y",
        "-i",
        Path(video_path).as_posix(),
        "-vf",
        f"fps=1/{fps}",
        output_pattern.as_posix(),
    ]


def discover_frame_candidates(
    candidate_dir: Path | str,
    video_id: str,
    interval_seconds: float,
    image_size: tuple[int, int] = (0, 0),
) -> list[FrameCandidate]:
    """Discover candidate frame files and infer timestamps from sorted order."""
    interval = _require_positive_interval(interval_seconds)
    directory = Path(candidate_dir)
    width, height = image_size
    frames = sorted(directory.glob("*.jpg"))
    return [
        FrameCandidate(
            id=f"frame-{index:06d}",
            video_id=video_id,
            timestamp=(index - 1) * interval,
            image_path=frame_path,
            width=width,
            height=height,
        )
        for index, frame_path in enumerate(frames, start=1)
    ]


def extract_frame_candidates(
    video_path: Path | str,
    candidate_dir: Path | str,
    video_id: str,
    interval_seconds: float,
    runner: FrameCommandRunner | None = None,
    ffmpeg_bin: str = "ffmpeg",
) -> list[FrameCandidate]:
    """Run frame extraction and return discovered candidate metadata."""
    directory = Path(candidate_dir)
    directory.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_frame_command(
        video_path=video_path,
        candidate_dir=directory,
        interval_seconds=interval_seconds,
        ffmpeg_bin=ffmpeg_bin,
    )
    command_runner = runner if runner is not None else _run_subprocess
    command_runner(command)
    return discover_frame_candidates(
        candidate_dir=directory,
        video_id=video_id,
        interval_seconds=interval_seconds,
    )


def select_frame_candidates(
    candidates: list[FrameCandidate],
    selected_dir: Path | str,
    min_interval_seconds: float,
    copier: FrameCopier = shutil.copy2,
) -> tuple[list[FrameCandidate], list[FrameCandidate]]:
    """Select candidate frames using a deterministic minimum interval rule."""
    min_interval = _require_positive_interval(min_interval_seconds)
    directory = Path(selected_dir)
    directory.mkdir(parents=True, exist_ok=True)
    selected: list[FrameCandidate] = []
    rejected: list[FrameCandidate] = []
    last_selected_timestamp: float | None = None
    selected_hashes: set[str] = set()

    for frame in sorted(candidates, key=lambda item: item.timestamp):
        if (
            last_selected_timestamp is None
            or frame.timestamp - last_selected_timestamp >= min_interval
        ):
            frame_hash = _file_sha256(frame.image_path)
            if frame_hash in selected_hashes:
                rejected.append(
                    replace(
                        frame,
                        filter_status=FilterStatus.REJECTED,
                        filter_reason="duplicate_content",
                    )
                )
                continue
            target = directory / frame.image_path.name
            copier(frame.image_path, target)
            selected_hashes.add(frame_hash)
            selected.append(
                replace(
                    frame,
                    image_path=target,
                    filter_status=FilterStatus.SELECTED,
                    filter_reason=None,
                )
            )
            last_selected_timestamp = frame.timestamp
        else:
            rejected.append(
                replace(
                    frame,
                    filter_status=FilterStatus.REJECTED,
                    filter_reason="within_min_interval",
                )
            )

    return selected, rejected


def _run_subprocess(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_positive_interval(interval_seconds: float) -> float:
    interval = float(interval_seconds)
    if interval <= 0:
        raise ValueError("frame interval must be positive")
    return interval


def _format_fps_interval(interval_seconds: float) -> str:
    if interval_seconds.is_integer():
        return str(int(interval_seconds))
    return str(interval_seconds)
