import json
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..output.markdown import MarkdownGenerator

class GenerateStage(Stage):
    name = "generate"

    def __init__(self, output_dir: Path, cache_dir: Path):
        self.output_dir = output_dir
        self.cache_dir = cache_dir

    def run(self, context: dict) -> StageResult:
        analysis_path = context.get("analysis_path")
        analysis = json.loads(Path(analysis_path).read_text(encoding="utf-8"))

        self.output_dir.mkdir(parents=True, exist_ok=True)
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        gen = MarkdownGenerator()
        md_content = gen.render(analysis, assets_dir=Path("assets"))

        md_path = self.output_dir / "summary.md"
        md_path.write_text(md_content, encoding="utf-8")

        return StageResult(
            status=StageStatus.SUCCESS,
            output={"markdown_path": str(md_path)},
        )