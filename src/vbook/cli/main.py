import click
from rich.console import Console
from .process import process

console = Console()

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """vbook - 将视频转换为知识文档"""
    pass

cli.add_command(process)