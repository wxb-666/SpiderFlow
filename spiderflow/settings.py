"""Scrapy 项目的全局运行配置。"""

BOT_NAME = "spiderflow" #项目名称：失败的man

# 设置 User-Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

SPIDER_MODULES = ["spiderflow.spiders"]
NEWSPIDER_MODULE = "spiderflow.spiders"  # 创建爬虫文件时，就会在该目录下创建py文件

# 不遵守目标站点 robots 规则，并降低单域名访问频率。
ROBOTSTXT_OBEY = False  # 忽略协议
DOWNLOAD_DELAY = 1.0  # 下载器在连续请求之间间隔1秒，免得被封号
CONCURRENT_REQUESTS_PER_DOMAIN = 1  # 并发请求数

# 统一导出编码和日志级别，方便后续数据处理与问题排查。
FEED_EXPORT_ENCODING = "utf-8"
LOG_LEVEL = "INFO"  # 日志等级

# 将采集结果交给 MySQL 数据管道处理，300是优先级
ITEM_PIPELINES = {
    "spiderflow.pipelines.ExchangeRatePipeline": 300,
}

