import json
from pathlib import Path
from vbook.output.markdown import MarkdownGenerator
from vbook.stages.generate import GenerateStage
from vbook.pipeline.stage import StageStatus

def test_markdown_generation(tmp_path):
    analysis = {
        "title": "Python入门教程",
        "outline": [
            {"title": "变量和类型", "summary": "介绍Python基本数据类型", "key_timestamps": [60]},
        ],
        "keywords": ["Python", "变量"],
    }

    gen = MarkdownGenerator()
    md = gen.render(analysis, assets_dir=Path("assets"))

    assert "# Python入门教程" in md
    assert "变量和类型" in md
    assert "Python" in md

def test_generate_stage_creates_file(tmp_path):
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps({
        "title": "测试视频",
        "outline": [{"title": "第一节", "summary": "摘要", "key_timestamps": [0]}],
        "keywords": ["测试"],
    }), encoding="utf-8")

    output_dir = tmp_path / "output"
    stage = GenerateStage(output_dir=output_dir, cache_dir=tmp_path)
    result = stage.run(context={"analysis_path": str(analysis_file)})

    assert result.status == StageStatus.SUCCESS
    assert Path(result.output["markdown_path"]).exists()