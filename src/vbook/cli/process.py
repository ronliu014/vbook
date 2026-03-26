from pathlib import Path
import sys
import click
from rich.console import Console

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from vbook.config.loader import load_config
from vbook.utils.logger import setup_logging, get_logger
from vbook.pipeline.engine import PipelineEngine
from vbook.utils.path import resolve_output_dir, get_cache_dir
from vbook.backends.stt.whisper import WhisperSTTBackend
from vbook.backends.stt.whisper_remote import WhisperRemoteBackend
from vbook.backends.llm.litellm_backend import LiteLLMBackend
from vbook.stages.audio_extract import AudioExtractStage
from vbook.stages.transcribe import TranscribeStage
from vbook.stages.proofread import ProofreadStage
from vbook.stages.analyze import AnalyzeStage
from vbook.stages.screenshot import ScreenshotStage
from vbook.stages.generate import GenerateStage
from vbook.utils.glossary import load_glossary, extract_hotwords

console = Console()
logger = get_logger(__name__)

@click.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default=None, help="输出目录")
@click.option("--config", "-c", type=click.Path(exists=True), default=None)
@click.option("--force", "-f", is_flag=True, help="强制重新处理所有阶段")
@click.option("--verbose", "-v", is_flag=True, help="启用详细日志输出")
def process(target, output, config, force, verbose):
    """处理视频文件或目录

    \b
    TARGET 可以是单个视频文件或包含视频的目录。
    支持 .mp4 和 .mkv 格式。

    \b
    示例:
      vbook process video.mp4 -c vbook.yaml
      vbook process video.mp4 -c vbook.yaml -o ./output
      vbook process ./videos/ -c vbook.yaml
      vbook process video.mp4 -c vbook.yaml --verbose --force

    \b
    注意:
      必须通过 -c 指定配置文件（如 vbook.yaml），否则使用内置默认值
      （默认连接 localhost，可能不是你想要的）。
      用 vbook init 生成初始配置文件。
    """
    target_path = Path(target)
    cfg = load_config(config_path=Path(config) if config else None)

    if target_path.is_file():
        _process_single(target_path, output, cfg, force, verbose)
    elif target_path.is_dir():
        videos = list(target_path.rglob("*.mp4")) + list(target_path.rglob("*.mkv"))
        console.print(f"[cyan]找到 {len(videos)} 个视频文件[/cyan]")
        for video in videos:
            _process_single(video, output, cfg, force, verbose)
    else:
        raise click.ClickException(f"Target not found: {target}")

def _process_single(video_path: Path, output: str, cfg, force: bool, verbose: bool = False):
    output_root = Path(output) if output else (cfg.output.root or video_path.parent / "vbook_output")
    source_root = video_path.parent
    output_dir = resolve_output_dir(video_path, source_root, output_root)
    cache_dir = get_cache_dir(output_dir, cfg.processing.intermediate_dir)

    setup_logging(output_dir=output_dir, verbose=verbose, level=cfg.logging.level)

    if force and cache_dir.exists():
        import shutil
        shutil.rmtree(cache_dir)

    if cfg.backends.stt == "whisper_remote":
        stt = WhisperRemoteBackend(**cfg.backends.whisper_remote)
    else:
        stt = WhisperSTTBackend(**cfg.backends.whisper_local)
    llm = LiteLLMBackend(
        model=f"ollama/{cfg.backends.ollama_qwen['model']}",
        base_url=cfg.backends.ollama_qwen.get("base_url"),
    )

    # Load glossary
    glossary = load_glossary(cfg.processing.glossary)
    hotwords = extract_hotwords(glossary)

    stages = [
        AudioExtractStage(video_path=video_path, cache_dir=cache_dir),
        TranscribeStage(stt_backend=stt, cache_dir=cache_dir, hotwords=hotwords),
        ProofreadStage(llm_backend=llm, cache_dir=cache_dir, glossary=glossary),
        AnalyzeStage(llm_backend=llm, cache_dir=cache_dir),
        ScreenshotStage(video_path=video_path, cache_dir=cache_dir),
        GenerateStage(output_dir=output_dir, cache_dir=cache_dir),
    ]

    engine = PipelineEngine(cache_dir=cache_dir, max_retries=cfg.processing.max_retries)
    logger.info("开始处理: %s", video_path.name)
    engine.run(stages, context={"video_path": str(video_path)})
    logger.info("完成: %s", output_dir / "summary.md")

if __name__ == "__main__":
    process()