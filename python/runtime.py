import logging
import os
import sys
import threading
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

_ENGINE = None
_LOGGING_CONFIGURED = False
_DOTENV_LOADED = False
_RATE_LIMIT_STATE_LOCK = threading.Lock()
_RATE_LIMIT_LOCKS: dict[str, threading.Lock] = {}
_RATE_LIMIT_LAST_CALLED_AT: dict[str, float] = {}


def load_dotenv_if_exists() -> None:
    global _DOTENV_LOADED

    if _DOTENV_LOADED:
        return

    candidates = [
        Path(__file__).resolve().parent.parent / '.env',
        Path.cwd() / '.env',
    ]

    for dotenv_path in candidates:
        if not dotenv_path.exists():
            continue

        for raw_line in dotenv_path.read_text(encoding='utf-8').splitlines():
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue

            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()

            if not key or key in os.environ:
                continue

            if (
                (value.startswith('"') and value.endswith('"')) or
                (value.startswith("'") and value.endswith("'"))
            ):
                value = value[1:-1]

            os.environ[key] = value

    _DOTENV_LOADED = True


load_dotenv_if_exists()


def get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def configure_logging() -> None:
    global _LOGGING_CONFIGURED

    if _LOGGING_CONFIGURED:
        return

    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', 'INFO').upper(),
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    _LOGGING_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def wait_for_rate_limit(key: str, interval_seconds: int, logger: logging.Logger | None = None, label: str | None = None) -> None:
    if interval_seconds <= 0:
        return

    with _RATE_LIMIT_STATE_LOCK:
        rate_lock = _RATE_LIMIT_LOCKS.setdefault(key, threading.Lock())

    with rate_lock:
        now = time.monotonic()
        last_called_at = _RATE_LIMIT_LAST_CALLED_AT.get(key)
        if last_called_at is not None:
            wait_seconds = interval_seconds - (now - last_called_at)
            if wait_seconds > 0:
                if logger is not None:
                    logger.info('%s 触发频率限制，等待 %.1f 秒后继续', label or key, wait_seconds)
                time.sleep(wait_seconds)

        _RATE_LIMIT_LAST_CALLED_AT[key] = time.monotonic()


def get_db_engine():
    global _ENGINE

    if _ENGINE is not None:
        return _ENGINE

    db_config = {
        'host': os.getenv('DB_HOST', 'host.docker.internal'),
        'port': get_env_int('DB_PORT', 3306),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'stock'),
        'charset': os.getenv('DB_CHARSET', 'utf8mb4'),
    }

    connection_string = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        f"?charset={db_config['charset']}"
    )
    _ENGINE = create_engine(connection_string, pool_pre_ping=True, pool_recycle=1800)
    return _ENGINE


def sanitize_records(records: list[dict]) -> list[dict]:
    for row in records:
        for key, value in row.items():
            if pd.isna(value):
                row[key] = None
    return records


def dataframe_to_records(dataframe: pd.DataFrame) -> list[dict]:
    return sanitize_records(dataframe.to_dict(orient='records'))
