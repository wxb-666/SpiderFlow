# AGENTS.MD

---

## 目标


---

## 仓库结构

- `spiderflow/`：Python 主应用包，包含 Scrapy 爬虫、数据处理、数据库访问和定时任务等业务代码。
- `spiderflow/spiders/`：Scrapy 爬虫目录，存放外汇牌价等数据源的 Spider 定义。
- `spiderflow/items.py`：Scrapy Item 数据结构定义，描述汇率采集结果字段。
- `spiderflow/pipelines.py`：Scrapy 数据管道，负责 Item 校验、转换和自动入库。
- `spiderflow/services/`：可复用业务服务目录，存放数据库服务、Pandas 分析和结果导出逻辑。
- `spiderflow/commands/`：命令行入口目录，存放手动执行的 CRUD 和数据维护命令。
- `spiderflow/scheduler/`：定时任务目录，存放 APScheduler 任务及任务编排代码。
- `spiderflow/config.py`：应用配置文件，统一读取和校验环境变量。
- `spiderflow/db.py`：数据库连接工具，负责创建和管理 MySQL 连接。
- `spiderflow/main.py`：应用容器入口，负责启动基础服务并检查数据库连接。
- `spiderflow/settings.py`：Scrapy 全局配置文件，配置爬虫模块、访问频率和日志级别。
- `docker/`：容器和数据库基础设施目录，不放业务代码。
- `docker/mysql/init/`：MySQL 首次启动时自动执行的初始化 SQL 脚本。
- `docs/`：项目文档目录，存放需求、设计、部署和开发说明，是实现依据。
- `data/`：运行生成的 CSV 等数据文件目录，不提交到版本库。
- `.idea/`：本地 IDE 项目配置目录，仅用于开发工具识别项目，不承载业务逻辑。
- `Dockerfile`：Python 应用镜像构建文件。
- `docker-compose.yml`：本地服务编排文件，负责启动应用和 MySQL。
- `requirements.txt`：Python 运行依赖清单。
- `scrapy.cfg`：Scrapy 项目入口配置文件。
- `.env` / `.env.example`：环境变量文件；`.env` 仅供本地使用，不提交到版本库。
- `AGENTS.MD`：AI 协作说明文件，记录项目目标、仓库结构和开发约束。

业务代码只能放在 `spiderflow/` 下，容器基础设施文件只能放在 `docker/` 下；Scrapy 自动处理逻辑放在 `items.py`、`pipelines.py` 和 `spiders/`，可复用业务逻辑放在 `services/`，手动命令入口放在 `commands/`；新增模块时应同步更新受影响的 `docs/` 文档。

---

## 开发约束

- 沟通语言：CN（中文，此为强约束，除非用户要求其他国家语言时再更改）
- 在修改代码或者增删改文件前，需要经过用户同意，用户明确同意后方可落地
- 在增/删/改代码时，需要对代码进行注释，注释语言也使用CN（中文）

---
