"""数据库连接工具。"""

from sqlalchemy import Engine, create_engine, text

from spiderflow.config import Settings


def create_database_engine(settings: Settings) -> Engine:
    """创建带连接预检的数据库引擎。"""
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
    )


def verify_database_connection(engine: Engine) -> None:
    """执行轻量查询，确认数据库已准备就绪。"""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

