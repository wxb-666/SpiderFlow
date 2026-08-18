"""外汇牌价数据项定义。"""

import scrapy


class ExchangeRateItem(scrapy.Item):
    """保存一条从公开牌价页面采集的汇率记录"""

    currency_name = scrapy.Field()
    cash_buying_rate = scrapy.Field()
    cash_selling_rate = scrapy.Field()
    spot_buying_rate = scrapy.Field()
    spot_selling_rate = scrapy.Field()
    middle_rate = scrapy.Field()
    published_at = scrapy.Field()
    source_url = scrapy.Field()
    crawled_at = scrapy.Field() # 实际爬取时间