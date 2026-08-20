"""手动执行汇率分析并导出 CSV 的命令入口。"""

from __future__ import annotations

import argparse
from datetime import datetime

from spiderflow.config import get_settings
from spiderflow.db import create_database_engine
from spiderflow.services.analysis import ExchangeRateAnalysisService
from spiderflow.services.export import ExchangeRateExportService


def parse_datetime(value: str | None) -> datetime | None:
    """将命令行时间转换为 datetime；未传入时返回 None。"""
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"时间格式错误：{value}，请使用 YYYY-MM-DD 或 YYYY-MM-DDTHH:MM:SS"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    """创建分析导出命令的参数解析器。"""
    parser = argparse.ArgumentParser(description="分析汇率并导出 CSV 文件")
    # 支持按币种和发布时间范围筛选分析数据。
    parser.add_argument("--code", help="币种编码，例如 USD；不传则分析全部币种")
    parser.add_argument("--start-at", type=parse_datetime, help="起始时间")
    parser.add_argument("--end-at", type=parse_datetime, help="结束时间")
    parser.add_argument(
        "--output-dir",
        default="data",
        help="CSV 输出目录，默认是 data",
    )
    return parser


def main() -> None:
    """执行分析并输出生成文件路径。"""
    args = build_parser().parse_args()
    # 读取配置并创建数据库连接引擎。
    settings = get_settings()
    engine = create_database_engine(settings)

    try:
        # 先完成指标计算，再将明细和汇总结果导出为 CSV。
        analysis_service = ExchangeRateAnalysisService(engine)
        analysis_result = analysis_service.analyze(
            code=args.code,
            start_at=args.start_at,
            end_at=args.end_at,
        )
        export_result = ExchangeRateExportService(args.output_dir).export(analysis_result)
        print(f"明细 CSV：{export_result.detail_path}")
        print(f"汇总 CSV：{export_result.summary_path}")
        print(f"明细记录数：{len(analysis_result.detail)}")
        print(f"汇总记录数：{len(analysis_result.summary)}")
    finally:
        # 无论分析或导出是否发生异常，都释放数据库引擎资源。
        engine.dispose()


if __name__ == "__main__":
    main()
