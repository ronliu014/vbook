from pathlib import Path
import click
from rich.console import Console
from ..config.loader import load_config
from ..pipeline.engine import PipelineEngine
from ..utils.path import resolve_output_dir, get_cache_dir
from ..backends.stt.whisper import WhisperSTTBackend
from ..backends.llm.litellm_backend import LiteLLMBackend
from ..stages.audio_extract import AudioExtractStage
from ..stages.transcribe import TranscribeStage
from ..stages.analyze import AnalyzeStage
from ..stages.generate import GenerateStage

console = Console()

@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="输出目录")
@click.option("--config", "-c", type=click.Path(exists=True), default=None)
@click.option("--force", "-f", is_flag=True, help="强制重新处理所有阶段")
def process(target, output, config, force):
    """处理视频文件或目录"""
    target_path = Path(target)
    cfg = load_config(config_path=Path(config) if config else None)

    if target_path.is_file():
        _process_single(target_path, output, cfg, force)
    elif target_path.is_dir():
        videos = list(target_path.rglob("*.mp4")) + list(target_path.rglob("*.mkv"))
        console.print(f"[cyan]找到 {len(videos)} 个视频文件[/cyan]")
        for video in videos:
            _process_single(video, output, cfg, force)
    else:
        raise click.ClickException(f"Target not found: {target}")

def _process_single(video_path: Path, output: str, cfg, force: bool):
    output_root = Path(output) if output else (cfg.output.root or video_path.parent / "vbook_output")
    source_root = video_path.parent
    output_dir = resolve_output_dir(video_path, source_root, output_root)
    cache_dir = get_cache_dir(output_dir, cfg.processing.intermediate_dir)

    if force and cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)

    stt = WhisperSTTBackend(**cfg.backends.whisper_local)
    llm = LiteLLMBackend(
        model=f"ollama/{cfg.backends.ollama_qwen['model']}",
        base_url=cfg.backends.ollama_qwen.get("base_url"),
    )

    stages = [
        AudioExtractStage(video_path=video_path, cache_dir=cache_dir),
        TranscribeStage(stt_backend=stt, cache_dir=cache_dir),
        AnalyzeStage(llm_backend=llm, cache_dir=cache_dir),
        GenerateStage(output_dir=output_dir, cache_dir=cache_dir),
    ]

    engine = PipelineEngine(cache_dir=cache_dir, max_retries=cfg.processing.max_retries)
    console.print(f"[green]处理: {video_path.name}[/green]")
    engine.run(stages, context={"video_path": str(video_path)})
    console.print(f"[green]完成: {output_dir / 'summary.md'}[/green]")