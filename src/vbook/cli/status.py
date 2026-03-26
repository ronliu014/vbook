from pathlib import Path
import click
import yaml
from rich.console import Console
from rich.table import Table

console = Console()

@click.command()
@click.argument("output_dir", type=click.Path(exists=True))
def status(output_dir):
    """查看视频处理状态

    \b
    OUTPUT_DIR 是视频处理后的输出目录（包含 .vbook_cache）。

    \b
    示例:
      vbook status ./output/video_name
    """
    cache_dir = Path(output_dir) / ".vbook_cache"
    status_file = cache_dir / "status.yaml"

    if not status_file.exists():
        console.print("[yellow]未找到处理状态[/yellow]")
        return

    data = yaml.safe_load(status_file.read_text())
    table = Table(title="处理状态")
    table.add_column("阶段", style="cyan")
    table.add_column("状态", style="green")

    for stage, info in data.items():
        status_str = info.get("status", "unknown")
        color = "green" if status_str == "success" else "red"
        table.add_row(stage, f"[{color}]{status_str}[/{color}]")

    console.print(table)