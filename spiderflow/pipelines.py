"""Scrapy 数据处理管道。"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from scrapy import Item, Spider
from scrapy.crawler import Crawler
from scrapy.exceptions import DropItem
from sqlalchemy import Engine

from spiderflow.config import get_settings
from spiderflow.db import create_database_engine
from spiderflow.services.database import ExchangeRateService


class ExchangeRatePipeline:
    """校验汇率数据并写入 MySQL。"""

    def __init__(self) -> None:
        # 引擎在爬虫启动后创建，因此初始化阶段允许为空。
        self.engine: Engine | None = None
        self.rate_service: ExchangeRateService | None = None

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> "ExchangeRatePipeline":
        """根据 Scrapy 配置创建 Pipeline。"""
        return cls()

    def open_spider(self, spider: Spider) -> None:
        """Spider 启动时建立数据库连接。"""
        settings = get_settings()
        self.engine = create_database_engine(settings)
        self.rate_service = ExchangeRateService(self.engine)

    def close_spider(self, spider: Spider) -> None:
        """Spider 关闭时释放数据库连接池。"""
        if self.engine is not None:
            self.engine.dispose()

    def process_item(self, item: Item, spider: Spider) -> Item:
        """处理一条汇率数据并执行幂等写入"""
        published_at = datetime.strptime(
            item["published_at"],
            "%Y/%m/%d %H:%M:%S",
        )

        crawled_at = datetime.fromisoformat(item["crawled_at"])
        if crawled_at.tzinfo is not None:
            # 如果带了时区信息，就将时间转化UTC零时区时间，并将时区信息去掉
            crawled_at = crawled_at.astimezone(timezone.utc).replace(tzinfo=None)

        def to_decimal(value: Any) -> Decimal | None:
            # 空牌价写入数据库 NULL，非空牌价转为Decimal（精度转化）
            return Decimal(str(value)) if value not in (None, "") else None

        values = {
            "currency_name": item["currency_name"],
            "cash_buying_rate": to_decimal(item["cash_buying_rate"]),
            "cash_selling_rate": to_decimal(item["cash_selling_rate"]),
            "spot_buying_rate": to_decimal(item["spot_buying_rate"]),
            "spot_selling_rate": to_decimal(item["spot_selling_rate"]),
            "middle_rate": to_decimal(item["middle_rate"]),
            "published_at": published_at,
            "source_url": item["source_url"],
            "crawled_at": crawled_at,
        }

        if self.rate_service is None:
            raise RuntimeError("汇率数据库服务尚未初始化")

        saved = self.rate_service.save_or_update(values)  # 将爬取并转化后的数据插入/更新到数据表

        if not saved:
            # 如果没变化，说明爬取到的数据中没有符合的币种（也有可能是完全相同的数据）
            raise DropItem(f"未找到启用中的币种：{item['currency_name']}")

        return item
