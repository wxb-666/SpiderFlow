"""应用容器入口。"""

import logging
import time

from spiderflow.config import get_settings
from spiderflow.db import create_database_engine, verify_database_connection


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """验证基础运行环境，并保持容器等待后续任务接入。"""
    settings = get_settings()
    engine = create_database_engine(settings)
    verify_database_connection(engine)
    logger.info("数据库连接成功，SpiderFlow 基础环境已就绪")

    # 定时任务由独立的 scheduler 容器负责，基础应用容器仅保持运行。
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
