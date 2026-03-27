import json
import shutil
from pathlib import Path
from ..pipeline.stage import Stage, StageResult, StageStatus
from ..output.markdown import MarkdownGenerator
from ..output.mindmap import generate_markmap
from ..output.pptx_generator import generate_pptx

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

        screenshots_map = context.get("screenshots_map", {})
        if screenshots_map:
            screenshots_dir = Path(context.get("screenshots_dir", ""))
            for section_idx, filenames in screenshots_map.items():
                idx = int(section_idx)
                if idx < len(analysis.get("outline", [])):
                    analysis["outline"][idx]["screenshots"] = filenames
                for filename in filenames:
                    src = screenshots_dir / filename
                    if src.exists():
                        shutil.copy2(str(src), str(assets_dir / filename))

        gen = MarkdownGenerator()
        md_content = gen.render(analysis, assets_dir=Path("assets"))

        md_path = self.output_dir / "summary.md"
        md_path.write_text(md_content, encoding="utf-8")

        # Generate mindmap
        mindmap_content = generate_markmap(analysis)
        mindmap_path = self.output_dir / "mindmap.md"
        mindmap_path.write_text(mindmap_content, encoding="utf-8")

        # Generate PowerPoint
        pptx_path = self.output_dir / "summary.pptx"
        generate_pptx(analysis, assets_dir, pptx_path)

        return StageResult(
            status=StageStatus.SUCCESS,
            output={
                "markdown_path": str(md_path),
                "mindmap_path": str(mindmap_path),
                "pptx_path": str(pptx_path),
            },
        )