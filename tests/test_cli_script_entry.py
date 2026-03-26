"""Test that process.py can be run as a script directly"""
import subprocess
import sys
from pathlib import Path

def test_process_script_direct_execution():
    """After fix: running process.py directly should work"""
    script_path = Path(__file__).parent.parent / "src" / "vbook" / "cli" / "process.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "处理视频文件或目录" in result.stdout or "Usage:" in result.stdout
