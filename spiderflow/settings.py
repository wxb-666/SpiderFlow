"""Scrapy 项目的全局运行配置。"""

BOT_NAME = "spiderflow"

SPIDER_MODULES = ["spiderflow.spiders"]
NEWSPIDER_MODULE = "spiderflow.spiders"

# 遵守目标站点 robots 规则，并降低单域名访问频率。
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1.0
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# 统一导出编码和日志级别，方便后续数据处理与问题排查。
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"

