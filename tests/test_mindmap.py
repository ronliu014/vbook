import pytest
from vbook.output.mindmap import generate_markmap


def test_generate_markmap_basic():
    analysis = {
        "title": "测试标题",
        "outline": [
            {"title": "章节1", "summary": "摘要1", "key_timestamps": [0]},
            {"title": "章节2", "summary": "摘要2", "key_timestamps": [100]},
        ],
        "keywords": ["关键词1", "关键词2"],
    }

    result = generate_markmap(analysis)

    assert "# 测试标题" in result
    assert "## 章节1" in result
    assert "> 摘要1" in result
    assert "## 关键词" in result
    assert "- 关键词1" in result
