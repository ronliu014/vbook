# src/vbook/utils/logger.py
import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from rich.logging import RichHandler

_LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_startup_time = datetime.now().strftime("%Y%m%d_%H%M%S")


def setup_logging(output_dir: Path, verbose: bool = False, level: str = "INFO") -> None:
    if verbose:
        resolved_level = logging.DEBUG
    else:
        resolved_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger("vbook")
    root.setLevel(resolved_level)

    if root.handlers:
        root.handlers.clear()

    # 终端：rich 格式化
    rich_handler = RichHandler(
        level=resolved_level,
        show_path=False,
        rich_tracebacks=True,
        markup=False,
    )
    root.addHandler(rich_handler)

    # 输出目录日志：按启动时间命名（DEBUG 级别）
    output_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(
        output_dir / f"vbook_{_startup_time}.log", encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    )
    root.addHandler(file_handler)

    # 项目根 logs/：按天轮转（INFO 级别）
    project_log_dir = Path.cwd() / "logs"
    project_log_dir.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    daily_handler = TimedRotatingFileHandler(
        project_log_dir / f"vbook_{today}.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    daily_handler.setLevel(logging.INFO)
    daily_handler.setFormatter(
        logging.Formatter(_LOG_FORMAT, _DATE_FORMAT)
    )
    root.addHandler(daily_handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
