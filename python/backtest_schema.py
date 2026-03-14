from pathlib import Path

from sqlalchemy import text

from runtime import get_db_engine, get_logger

logger = get_logger('backtest_schema')


def _load_schema_statements() -> list[str]:
    schema_path = Path(__file__).resolve().parent / 'sql' / 'backtest_schema.sql'
    raw_sql = schema_path.read_text(encoding='utf-8')
    filtered_lines = [line for line in raw_sql.splitlines() if not line.strip().startswith('--')]
    return [statement.strip() for statement in '\n'.join(filtered_lines).split(';') if statement.strip()]


def ensure_backtest_schema() -> None:
    statements = _load_schema_statements()
    engine = get_db_engine()
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))

    logger.info('回测 schema 已确认，语句数=%s', len(statements))


if __name__ == '__main__':
    ensure_backtest_schema()
