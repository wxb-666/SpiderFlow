"""SpiderFlow 一次性任务定义。"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from spiderflow.config import get_settings
from spiderflow.db import create_database_engine
from spiderflow.services.analysis import ExchangeRateAnalysisService
from spiderflow.services.database import JobRunService
from spiderflow.services.export import ExchangeRateExportService


logger = logging.getLogger(__name__)
JOB_NAME = "exchange_rate_daily"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ExchangeRateJobResult:
    """保存一次外汇牌价任务的执行结果。"""

    run_id: int
    record_count: int
    crawl_output_path: Path
    detail_path: Path
    summary_path: Path


def run_exchange_rate_spider(crawl_output_path: Path) -> None:
    """在独立子进程中运行 Scrapy 爬虫并输出 JSON 文件。"""
    command: list[str] = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "exchange_rate",
        "-O",
        str(crawl_output_path),
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        # 日志末尾通常包含最接近失败原因的 Scrapy 异常信息。
        error_output = (completed.stderr or completed.stdout)[-2000:]
        raise RuntimeError(f"爬虫执行失败，退出码为 {completed.returncode}：{error_output}")


def count_crawled_items(crawl_output_path: Path) -> int:
    """读取爬虫 JSON 输出并返回本次成功处理的记录数量。"""
    if not crawl_output_path.is_file():
        raise RuntimeError(f"未生成爬虫输出文件：{crawl_output_path}")

    with crawl_output_path.open("r", encoding="utf-8") as file:
        items = json.load(file)
    if not isinstance(items, list):
        raise RuntimeError("爬虫输出格式错误，预期为 JSON 数组")
    if not items:
        raise RuntimeError("本次爬虫未产生有效汇率记录")
    return len(items)


def run_exchange_rate_job(output_dir: str | Path | None = None) -> ExchangeRateJobResult:
    """执行采集、入库、分析、导出和任务日志记录的完整流程。"""
    resolved_output_dir = (
        Path(output_dir).resolve()
        if output_dir is not None
        else PROJECT_ROOT / "data"
    )
    resolved_output_dir.mkdir(parents=True, exist_ok=True)
    crawl_output_path = resolved_output_dir / "exchange_rates.json"

    engine = create_database_engine(get_settings())
    job_service = JobRunService(engine)
    run_id = job_service.create_running(JOB_NAME)

    try:
        logger.info("任务开始：run_id=%s", run_id)
        run_exchange_rate_spider(crawl_output_path)
        record_count = count_crawled_items(crawl_output_path)

        analysis_result = ExchangeRateAnalysisService(engine).analyze()
        export_result = ExchangeRateExportService(resolved_output_dir).export(analysis_result)
        job_service.finish(run_id, "SUCCESS", record_count=record_count)
        logger.info("任务成功：run_id=%s，采集记录数=%s", run_id, record_count)

        return ExchangeRateJobResult(
            run_id=run_id,
            record_count=record_count,
            crawl_output_path=crawl_output_path,
            detail_path=export_result.detail_path,
            summary_path=export_result.summary_path,
        )
    except Exception as exc:
        error_message = str(exc)[-2000:]
        job_service.finish(
            run_id,
            "FAILED",
            error_message=error_message,
        )
        logger.exception("任务失败：run_id=%s", run_id)
        raise
    finally:
        engine.dispose()


def main() -> None:
    """提供一次性任务的手动执行入口。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    result = run_exchange_rate_job()
    print(f"任务日志 ID：{result.run_id}")
    print(f"采集记录数：{result.record_count}")
    print(f"爬虫输出：{result.crawl_output_path}")
    print(f"分析明细：{result.detail_path}")
    print(f"分析汇总：{result.summary_path}")


if __name__ == "__main__":
    main()

