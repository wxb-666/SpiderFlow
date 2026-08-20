"""SpiderFlow APScheduler 定时任务入口。"""

from __future__ import annotations

import logging

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from spiderflow.config import get_settings
from spiderflow.scheduler.jobs import run_exchange_rate_job


logger = logging.getLogger(__name__)
SCHEDULED_JOB_ID = "exchange_rate_weekday"


def execute_scheduled_job() -> None:
    """执行一次定时采集任务。异常交由 APScheduler 记录并继续调度。"""
    result = run_exchange_rate_job()
    logger.info(
        "定时任务完成：run_id=%s，采集记录数=%s",
        result.run_id,
        result.record_count,
    )


def log_job_event(event: JobExecutionEvent) -> None:
    """记录 APScheduler 的执行结果事件。"""
    if event.code == EVENT_JOB_EXECUTED:
        logger.info("调度任务执行事件完成：job_id=%s", event.job_id)
    elif event.code == EVENT_JOB_ERROR:
        logger.error("调度任务执行事件异常：job_id=%s", event.job_id)


def create_scheduler() -> BlockingScheduler:
    """创建并配置工作日定时调度器。"""
    settings = get_settings()
    scheduler = BlockingScheduler(timezone=settings.timezone)
    trigger = CronTrigger(
        day_of_week="mon-fri",
        hour=settings.schedule_hour,
        minute=settings.schedule_minute,
        timezone=settings.timezone,
    )
    scheduler.add_job(
        execute_scheduled_job,
        trigger=trigger,
        id=SCHEDULED_JOB_ID,
        name="工作日外汇牌价采集任务",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    scheduler.add_listener(log_job_event, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    return scheduler


def main() -> None:
    """启动阻塞式调度器并持续等待下一次触发。"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    settings = get_settings()
    scheduler = create_scheduler()
    logger.info(
        "调度器已启动：工作日 %02d:%02d（时区：%s）",
        settings.schedule_hour,
        settings.schedule_minute,
        settings.timezone,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("调度器正在停止")
        scheduler.shutdown(wait=False)


if __name__ == "__main__":
    main()
