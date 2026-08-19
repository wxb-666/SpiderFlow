"""币种、汇率和任务日志的命令行 CRUD 入口。"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.exc import IntegrityError

from spiderflow.config import get_settings
from spiderflow.db import create_database_engine
from spiderflow.services.database import (
    CurrencyService,
    ExchangeRateService,
    JobRunService,
)


def parse_datetime(value: str) -> datetime:
    """解析 ISO 格式时间参数。"""
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"时间格式错误：{value}，请使用 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS"
        ) from exc


def print_json(value: Any) -> None:
    """以适合中文阅读的 JSON 格式输出结果。"""
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


def require_confirm(args: argparse.Namespace) -> None:
    """校验删除命令的显式确认参数。"""
    if not args.confirm:
        raise SystemExit("删除操作需要显式传入 --confirm")


def build_parser() -> argparse.ArgumentParser:
    """创建统一的 CRUD 命令解析器。"""
    parser = argparse.ArgumentParser(description="SpiderFlow 数据库 CRUD 命令")
    groups = parser.add_subparsers(dest="resource", required=True)

    currency = groups.add_parser("currency", help="币种数据操作")
    currency_commands = currency.add_subparsers(dest="action", required=True)
    currency_list = currency_commands.add_parser("list", help="查询币种")
    currency_list.add_argument("--active-only", action="store_true")
    currency_create = currency_commands.add_parser("create", help="新增币种")
    currency_create.add_argument("--code", required=True)
    currency_create.add_argument("--name", required=True)
    currency_create.add_argument("--inactive", action="store_true")
    currency_status = currency_commands.add_parser("status", help="修改币种启用状态")
    currency_status.add_argument("--code", required=True)
    currency_status.add_argument("--active", choices=["0", "1"], required=True)
    currency_delete = currency_commands.add_parser("delete", help="删除币种")
    currency_delete.add_argument("--code", required=True)
    currency_delete.add_argument("--confirm", action="store_true")

    rate = groups.add_parser("rate", help="汇率数据操作")
    rate_commands = rate.add_subparsers(dest="action", required=True)
    rate_list = rate_commands.add_parser("list", help="查询汇率")
    rate_list.add_argument("--code")
    rate_list.add_argument("--start-at", type=parse_datetime)
    rate_list.add_argument("--end-at", type=parse_datetime)
    rate_create = rate_commands.add_parser("create", help="新增或更新汇率")
    rate_create.add_argument("--currency-name", required=True)
    rate_create.add_argument("--published-at", type=parse_datetime, required=True)
    rate_create.add_argument("--source-url", required=True)
    rate_create.add_argument("--cash-buying-rate")
    rate_create.add_argument("--cash-selling-rate")
    rate_create.add_argument("--spot-buying-rate")
    rate_create.add_argument("--spot-selling-rate")
    rate_create.add_argument("--middle-rate")
    rate_create.add_argument("--crawled-at", type=parse_datetime)
    rate_update = rate_commands.add_parser("update", help="修改汇率")
    rate_update.add_argument("--id", type=int, required=True)
    for field in (
        "cash-buying-rate",
        "cash-selling-rate",
        "spot-buying-rate",
        "spot-selling-rate",
        "middle-rate",
    ):
        rate_update.add_argument(f"--{field}")
    rate_update.add_argument("--published-at", type=parse_datetime)
    rate_update.add_argument("--source-url")
    rate_delete = rate_commands.add_parser("delete", help="按 ID 删除汇率")
    rate_delete.add_argument("--id", type=int, required=True)
    rate_delete.add_argument("--confirm", action="store_true")
    rate_delete_range = rate_commands.add_parser("delete-range", help="按日期范围删除汇率")
    rate_delete_range.add_argument("--start-at", type=parse_datetime, required=True)
    rate_delete_range.add_argument("--end-at", type=parse_datetime, required=True)
    rate_delete_range.add_argument("--code")
    rate_delete_range.add_argument("--confirm", action="store_true")

    job = groups.add_parser("job", help="任务日志操作")
    job_commands = job.add_subparsers(dest="action", required=True)
    job_list = job_commands.add_parser("list", help="查询任务日志")
    job_list.add_argument("--job-name")
    job_start = job_commands.add_parser("start", help="创建运行中的任务日志")
    job_start.add_argument("--job-name", required=True)
    job_finish = job_commands.add_parser("finish", help="完成任务日志")
    job_finish.add_argument("--id", type=int, required=True)
    job_finish.add_argument("--status", choices=["SUCCESS", "FAILED"], required=True)
    job_finish.add_argument("--record-count", type=int, default=0)
    job_finish.add_argument("--error-message")
    job_delete = job_commands.add_parser("delete", help="删除任务日志")
    job_delete.add_argument("--id", type=int, required=True)
    job_delete.add_argument("--confirm", action="store_true")

    return parser


def handle_currency(args: argparse.Namespace, service: CurrencyService) -> None:
    """处理币种相关命令。"""
    if args.action == "list":
        print_json(service.list(active_only=args.active_only))
    elif args.action == "create":
        print_json({"id": service.create(args.code, args.name, not args.inactive)})
    elif args.action == "status":
        print_json({"updated": service.update_status(args.code, args.active == "1")})
    elif args.action == "delete":
        require_confirm(args)
        try:
            print_json({"deleted": service.delete(args.code)})
        except IntegrityError as exc:
            raise SystemExit("该币种已有汇率记录，不能删除；请改为停用") from exc


def handle_rate(args: argparse.Namespace, service: ExchangeRateService) -> None:
    """处理汇率相关命令。"""
    if args.action == "list":
        print_json(service.list(args.code, args.start_at, args.end_at))
    elif args.action == "create":
        data = {
            "currency_name": args.currency_name,
            "published_at": args.published_at,
            "source_url": args.source_url,
            "crawled_at": args.crawled_at or datetime.now(),
            "cash_buying_rate": args.cash_buying_rate,
            "cash_selling_rate": args.cash_selling_rate,
            "spot_buying_rate": args.spot_buying_rate,
            "spot_selling_rate": args.spot_selling_rate,
            "middle_rate": args.middle_rate,
        }
        print_json({"saved": service.save_or_update(data)})
    elif args.action == "update":
        fields = {
            "cash_buying_rate": args.cash_buying_rate,
            "cash_selling_rate": args.cash_selling_rate,
            "spot_buying_rate": args.spot_buying_rate,
            "spot_selling_rate": args.spot_selling_rate,
            "middle_rate": args.middle_rate,
            "published_at": args.published_at,
            "source_url": args.source_url,
        }
        print_json({"updated": service.update(args.id, **{k: v for k, v in fields.items() if v is not None})})
    elif args.action == "delete":
        require_confirm(args)
        print_json({"deleted": service.delete(args.id)})
    elif args.action == "delete-range":
        require_confirm(args)
        if args.start_at > args.end_at:
            raise SystemExit("start-at 不能晚于 end-at")
        deleted = service.delete_by_date_range(args.start_at, args.end_at, args.code)
        print_json({"deleted_count": deleted})


def handle_job(args: argparse.Namespace, service: JobRunService) -> None:
    """处理任务日志相关命令。"""
    if args.action == "list":
        print_json(service.list(args.job_name))
    elif args.action == "start":
        print_json({"id": service.create_running(args.job_name)})
    elif args.action == "finish":
        print_json(
            {
                "updated": service.finish(
                    args.id,
                    args.status,
                    args.record_count,
                    args.error_message,
                )
            }
        )
    elif args.action == "delete":
        require_confirm(args)
        print_json({"deleted": service.delete(args.id)})


def main() -> None:
    """创建数据库服务并分发命令。"""
    args = build_parser().parse_args()
    engine = create_database_engine(get_settings())
    try:
        if args.resource == "currency":
            handle_currency(args, CurrencyService(engine))
        elif args.resource == "rate":
            handle_rate(args, ExchangeRateService(engine))
        elif args.resource == "job":
            handle_job(args, JobRunService(engine))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()

