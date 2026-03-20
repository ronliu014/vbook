from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class MarkdownGenerator:
    def __init__(self):
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(templates_dir)))

    def render(self, analysis: dict, assets_dir: Path = Path("assets")) -> str:
        template = self.env.get_template("summary.md.j2")
        return template.render(analysis=analysis, assets_dir=assets_dir)