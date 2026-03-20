from pathlib import Path
import click
import yaml
from rich.console import Console

console = Console()

@click.command("init")
@click.option("--source", "-s", required=True, type=click.Path(), help="视频源目录")
@click.option("--output", "-o", required=True, type=click.Path(), help="输出根目录")
@click.option("--config", "-c", default="vbook.yaml", help="配置文件路径")
def init_cmd(source, output, config):
    """初始化 vbook 配置文件"""
    config_data = {
        "source": {"video_dirs": [str(Path(source).resolve())]},
        "output": {"root": str(Path(output).resolve()), "structure": "mirror"},
        "processing": {"intermediate_dir": ".vbook_cache", "keep_intermediate": True},
        "backends": {
            "stt": "whisper_local",
            "llm": "ollama_qwen",
            "whisper_local": {"model": "medium", "device": "cpu"},
            "ollama_qwen": {"base_url": "http://localhost:11434", "model": "qwen2.5:14b"},
        },
    }
    config_path = Path(config)
    config_path.write_text(yaml.dump(config_data, allow_unicode=True), encoding="utf-8")
    console.print(f"[green]配置已写入: {config_path}[/green]")
    console.print(f"[yellow]请修改配置后运行: vbook process --all[/yellow]")