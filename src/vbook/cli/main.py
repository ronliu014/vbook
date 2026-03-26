import click
from rich.console import Console
from .process import process
from .init_cmd import init_cmd
from .status import status

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """vbook - 将视频转换为知识文档

    \b
    快速开始:
      1. 初始化配置:  vbook init -s ./videos -o ./output
      2. 编辑配置文件: 修改 vbook.yaml 中的后端地址
      3. 处理视频:     vbook process ./video.mp4 -c vbook.yaml
      4. 查看状态:     vbook status ./output/video_name
    """
    pass

cli.add_command(process)
cli.add_command(init_cmd)
cli.add_command(status)