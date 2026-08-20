# SpiderFlow

SpiderFlow 是一个基于 Scrapy、Pandas、MySQL、APScheduler 和 Docker 的外汇牌价采集与分析项目。项目从中国银行公开外汇牌价页面采集美元、欧元、日元和英镑的汇率数据，完成清洗、幂等入库、历史分析、CSV 导出和工作日自动调度。

## 功能特性

- 使用 Scrapy 采集中国银行公开外汇牌价。
- 通过 Scrapy Pipeline 校验数据并写入 MySQL。
- 按“币种 + 发布时间”实现汇率幂等写入。
- 使用 Pandas 计算日涨跌额、日涨跌幅、7 日移动均值和区间极值。
- 导出汇率分析明细和汇总 CSV 文件。
- 提供币种、汇率和任务日志的命令行 CRUD。
- 使用 APScheduler 在工作日固定时间执行完整任务。
- 使用 Docker Compose 统一运行 Python 应用、调度器和 MySQL。

## 任务流程

```text
Scrapy 爬虫
    -> Item 校验与 Pipeline 入库
    -> 任务日志记录
    -> Pandas 分析
    -> CSV 导出
```

一次性任务入口会串联上述全部步骤，并将执行结果写入 `job_runs` 表。

## 技术栈

| 分类 | 技术 |
| --- | --- |
| 编程语言 | Python 3.11 |
| 爬虫 | Scrapy 2.11 |
| 数据处理 | Pandas 2.2 |
| 数据库 | MySQL 8.0 |
| 数据库访问 | SQLAlchemy、PyMySQL |
| 任务调度 | APScheduler 3.10 |
| 容器化 | Docker、Docker Compose |

## 环境要求

- Docker Desktop 或 Docker Engine
- Docker Compose V2
- 可访问中国银行外汇牌价页面：[https://www.boc.cn/sourcedb/whpj/](https://www.boc.cn/sourcedb/whpj/)

不要求在宿主机安装 Python、MySQL 或项目依赖。

## 快速启动

1. 复制环境变量模板：

   ```powershell
   Copy-Item .env.example .env
   ```

   根据本地环境修改 `.env` 中的数据库密码和调度时间。`.env` 不应提交到版本库。

2. 构建并启动全部服务：

   ```powershell
   docker compose up -d --build
   ```

3. 查看服务状态：

   ```powershell
   docker compose ps
   ```

   服务包括：

   - `mysql`：MySQL 数据库；
   - `app`：应用基础容器，可执行命令行任务；
   - `scheduler`：运行 APScheduler 的定时任务容器。

## 手动执行完整任务

手动执行一次采集、入库、分析和导出：

```powershell
docker compose exec app python -m spiderflow.scheduler.jobs
```

成功后会生成或更新：

- `data/exchange_rates.json`：本次爬虫输出；
- `data/exchange_rate_detail.csv`：汇率分析明细；
- `data/exchange_rate_summary.csv`：区间最高价和最低价汇总。

## 定时任务

调度器默认在工作日 `17:00`（`Asia/Shanghai`）执行。可在 `.env` 中修改：

```env
APP_TIMEZONE=Asia/Shanghai
SCHEDULE_HOUR=17
SCHEDULE_MINUTE=0
```

修改后重新创建调度器容器：

```powershell
docker compose up -d --force-recreate scheduler
```

查看调度器日志：

```powershell
docker compose logs -f scheduler
```

调度器不会在启动时立即执行任务；需要立即采集时，请使用一次性任务命令。

## CRUD 命令

查询币种：

```powershell
docker compose exec app python -m spiderflow.commands.crud currency list
```

查询汇率：

```powershell
docker compose exec app python -m spiderflow.commands.crud rate list --code USD
```

查询任务日志：

```powershell
docker compose exec app python -m spiderflow.commands.crud job list --job-name exchange_rate_daily
```

删除指定时间范围的测试数据：

```powershell
docker compose exec app python -m spiderflow.commands.crud rate delete-range --start-at 2026-01-01 --end-at 2026-01-02 --confirm
```

删除命令必须显式传入 `--confirm`。

## 单独运行爬虫和分析导出

只运行 Scrapy 爬虫：

```powershell
docker compose exec app scrapy crawl exchange_rate -O data/exchange_rates.json
```

只运行 Pandas 分析并导出 CSV：

```powershell
docker compose exec app python -m spiderflow.commands.export_analysis
```

## 数据库

首次启动 MySQL 时会自动执行 `docker/mysql/init/001_init.sql`，创建以下数据表：

- `currencies`：币种基础信息；
- `exchange_rates`：汇率快照；
- `job_runs`：任务运行日志。

MySQL 数据保存在 Docker 命名卷 `mysql_data` 中。普通停止和重启不会删除数据；谨慎使用 `docker compose down -v`，该命令会删除数据库卷。

## 项目结构

```text
SpiderFlow/
├── spiderflow/
│   ├── spiders/       # Scrapy 爬虫
│   ├── services/      # 数据库、分析和导出服务
│   ├── commands/      # CRUD 和分析导出命令
│   ├── scheduler/     # 一次性任务和 APScheduler 入口
│   ├── items.py       # Scrapy Item 定义
│   ├── pipelines.py   # 数据校验和入库管道
│   ├── config.py      # 环境变量配置
│   └── db.py          # 数据库连接工具
├── docker/mysql/init/ # MySQL 初始化脚本
├── docs/              # 项目文档
├── data/              # JSON 和 CSV 运行结果
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── scrapy.cfg
```

## 日志与故障排查

查询结构化任务日志：

```powershell
docker compose exec app python -m spiderflow.commands.crud job list
```

查看全部应用日志：

```powershell
docker compose logs app scheduler
```

常见问题：

- MySQL 尚未就绪：等待 `mysql` 健康检查通过后再执行任务；
- 数据库连接失败：检查 `.env` 中的 `DB_HOST`、数据库名称、用户名和密码；
- 没有定时执行：确认当前日期为工作日，并检查 `SCHEDULE_HOUR`、`SCHEDULE_MINUTE` 和时区；
- 爬虫没有数据：检查数据源页面是否可访问，以及容器网络连接是否正常。

## 相关文档

- [项目需求说明书](docs/SpiderFlow_需求说明书.md)
- [AI 协作说明](AGENTS.MD)

## 数据来源与使用边界

数据来源为中国银行公开外汇牌价页面，仅用于学习和技术实践。项目不提供交易、投资建议或汇率预测，不绕过登录、验证码和其他访问限制。使用数据时请遵守数据源网站的相关条款。
