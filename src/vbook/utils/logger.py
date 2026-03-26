# src/vbook/utils/logger.py
import logging
from pathlib import Path
from rich.logging import RichHandler

_LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(output_dir: Path, verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    root = logging.getLogger("vbook")
    root.setLevel(level)

    # 避免重复添加 handler（多次调用时）
    if root.handlers:
        root.handlers.clear()

    # 终端：rich 格式化
    rich_handler = RichHandler(
        level=level,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    root.addHandler(rich_handler)

    # 输出目录日志（详细，DEBUG 级别）
    output_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        output_dir / "vbook.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    )
    root.addHandler(file_handler)

    # 项目根 logs/ 汇总日志（INFO 级别）
    project_log_dir = Path.cwd() / "logs"
    project_log_dir.mkdir(exist_ok=True)
    summary_handler = logging.FileHandler(
        project_log_dir / "vbook.log", encoding="utf-8"
    )
    summary_handler.setLevel(logging.INFO)
    summary_handler.setFormatter(
        logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    )
    root.addHandler(summary_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
