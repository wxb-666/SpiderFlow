"""外汇牌价分析结果导出服务。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from spiderflow.services.analysis import ExchangeRateAnalysisResult


@dataclass(frozen=True)
class ExchangeRateExportResult:
    """保存两类 CSV 文件的输出路径。"""

    detail_path: Path
    summary_path: Path


class ExchangeRateExportService:
    """将汇率分析结果导出为便于查看和二次处理的 CSV 文件。"""

    def __init__(
        self,
        output_dir: str | Path = "data",
        file_prefix: str = "exchange_rate",
    ) -> None:
        """初始化输出目录和文件名前缀。"""
        self.output_dir = Path(output_dir)
        self.file_prefix = file_prefix

    def export_detail(self, dataframe: pd.DataFrame) -> Path:
        """导出分析明细表并返回文件路径。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{self.file_prefix}_detail.csv"
        # utf-8-sig 方便 Windows Excel 正确识别中文表头和币种名称。
        dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    def export_summary(self, dataframe: pd.DataFrame) -> Path:
        """导出区间极值汇总表并返回文件路径。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"{self.file_prefix}_summary.csv"
        dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")
        return output_path

    def export(self, result: ExchangeRateAnalysisResult) -> ExchangeRateExportResult:
        """同时导出分析明细和区间汇总结果。"""
        return ExchangeRateExportResult(
            detail_path=self.export_detail(result.detail),
            summary_path=self.export_summary(result.summary),
        )

