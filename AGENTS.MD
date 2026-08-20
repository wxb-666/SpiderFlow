# AGENTS.MD

---

## 目标


---

## 仓库结构

- `spiderflow/`：Python 主应用包。
- `spiderflow/spiders/`：Scrapy 爬虫代码。
- `spiderflow/services/`：可复用业务服务代码。
- `spiderflow/commands/`：手动执行的命令行入口。
- `spiderflow/scheduler/`：一次性任务和定时任务代码。
- `docker/`：Docker 与 MySQL 基础设施配置。
- `docs/`：需求、设计和部署文档。
- `data/`：运行生成的数据和导出文件，不提交到版本库。
- `.idea/`：本地 IDE 配置。
- `Dockerfile`、`docker-compose.yml`：容器构建与服务编排文件。
- `requirements.txt`、`scrapy.cfg`：Python 和 Scrapy 项目配置文件。
- `.env` / `.env.example`：环境变量文件；`.env` 仅供本地使用，不提交到版本库。
- `AGENTS.MD`：项目协作说明文件。

业务代码只能放在 `spiderflow/` 下，容器基础设施文件只能放在 `docker/` 下；Scrapy 自动处理逻辑放在 `items.py`、`pipelines.py` 和 `spiders/`，可复用业务逻辑放在 `services/`，手动命令入口放在 `commands/`；新增模块时应同步更新受影响的 `docs/` 文档。

---

## 开发约束

- 沟通语言：CN（中文，此为强约束，除非用户要求其他国家语言时再更改）
- 在修改代码或者增删改文件前，需要经过用户同意，用户明确同意后方可落地
- 在增/删/改代码时，需要对代码进行注释，注释语言也使用CN（中文）
- 代码中的参数需添加类型标注
- 函数前面应该声明返回值类型
- `AGENTS.MD`中的`仓库结构`部分应当作为项目的大致结构，不应详细说明各个文件的具体职能

---
