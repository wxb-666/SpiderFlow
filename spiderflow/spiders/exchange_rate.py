"""中国银行外汇牌价爬虫"""

from datetime import datetime, timezone
import scrapy
from spiderflow.items import ExchangeRateItem


class ExchangeRateSpider(scrapy.Spider):
    """采集中国银行公开外汇牌价表"""

    name = "exchange_rate"
    allowed_domains = ["boc.cn"]
    start_urls = ["https://www.boc.cn/sourcedb/whpj/"]

    target_currencies = {"美元", "欧元", "日元", "英镑"}  # 首期目标只看四种常见货币

    def parse(self, response):
        """解析牌价表，并生成 ExchangeRateItem。"""
        tables = response.css("table")
        if len(tables) <= 1:
            self.logger.error("未找到外汇牌价表")
            return

        rows = tables[1].css("tr")

        for row in rows[1:]:
            cells = row.css("td")
            values = [
                cell.xpath("normalize-space(string(.))").get() or ""
                for cell in cells
            ]

            if values[0] not in self.target_currencies:
            # 如果不是指定的那四种货币就跳过
                continue

            if len(values) != 8 or not values[0]:
                self.logger.warning("跳过字段数量异常的数据行：%s", values)
                continue

            yield ExchangeRateItem(
                currency_name=values[0],
                spot_buying_rate=values[1] or None,
                cash_buying_rate=values[2] or None,
                spot_selling_rate=values[3] or None,
                cash_selling_rate=values[4] or None,
                middle_rate=values[5] or None,
                published_at=values[6],
                source_url=response.url,
                crawled_at=datetime.now(timezone.utc).isoformat(),
            )