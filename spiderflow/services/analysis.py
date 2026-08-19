"""外汇牌价 Pandas 分析服务。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd
from sqlalchemy import Engine

from spiderflow.services.database import ExchangeRateService


@dataclass
class ExchangeRateAnalysisResult:
    """保存汇率分析产生的明细和汇总结果。"""

    detail: pd.DataFrame
    summary: pd.DataFrame


class ExchangeRateAnalysisService:
    """读取汇率历史数据并计算基础波动指标。"""

    REQUIRED_COLUMNS = {
        "code",
        "name",
        "middle_rate",
        "published_at",
    }

    def __init__(self, engine: Engine):
        """复用数据库引擎创建汇率查询服务。"""
        self.rate_service = ExchangeRateService(engine)

    @staticmethod
    def _empty_dataframe() -> pd.DataFrame:
        """返回包含标准列的空分析表。"""
        return pd.DataFrame(
            columns=[
                "id",
                "code",
                "name",
                "cash_buying_rate",
                "cash_selling_rate",
                "spot_buying_rate",
                "spot_selling_rate",
                "middle_rate",
                "published_at",
                "source_url",
                "crawled_at",
                "trade_date",
                "daily_change",
                "daily_change_pct",
                "moving_avg_7d",
            ]
        )

    def load_data(
        self,
        code: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> pd.DataFrame:
        """从数据库读取汇率记录并转换为标准 DataFrame。"""
        rows = self.rate_service.list(code=code, start_at=start_at, end_at=end_at)
        dataframe = pd.DataFrame(rows)
        if dataframe.empty:
            return self._empty_dataframe()

        missing_columns = self.REQUIRED_COLUMNS - set(dataframe.columns)
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"汇率数据缺少必要字段：{missing}")

        # 统一时间和数值类型，便于后续排序及指标计算。
        dataframe["published_at"] = pd.to_datetime(
            dataframe["published_at"], errors="coerce"
        )
        dataframe["middle_rate"] = pd.to_numeric(
            dataframe["middle_rate"], errors="coerce"
        )
        dataframe = dataframe.dropna(subset=["code", "published_at", "middle_rate"])
        if dataframe.empty:
            return self._empty_dataframe()

        dataframe["trade_date"] = dataframe["published_at"].dt.normalize()

        # 同一币种同一天可能存在多次采集，只保留发布时间最新的一条。
        dataframe = (
            dataframe.sort_values(["code", "trade_date", "published_at"])
            .drop_duplicates(subset=["code", "trade_date"], keep="last")
            .sort_values(["code", "trade_date"])
            .reset_index(drop=True)
        )
        return dataframe

    @staticmethod
    def calculate_daily_change(dataframe: pd.DataFrame) -> pd.DataFrame:
        """计算每个币种的日涨跌额和日涨跌幅。"""
        result = dataframe.copy()
        if result.empty:
            result["daily_change"] = pd.Series(dtype="float64")
            result["daily_change_pct"] = pd.Series(dtype="float64")
            return result

        result = result.sort_values(["code", "trade_date"]).reset_index(drop=True)
        previous_rate = result.groupby("code")["middle_rate"].shift(1)
        result["daily_change"] = result["middle_rate"] - previous_rate
        result["daily_change_pct"] = (
            result["daily_change"] / previous_rate.where(previous_rate.ne(0)) * 100
        )
        return result

    @staticmethod
    def calculate_moving_average(
        dataframe: pd.DataFrame,
        window: int = 7,
    ) -> pd.DataFrame:
        """计算每个币种最近 N 个有效数据日的移动平均值。"""
        if window <= 0:
            raise ValueError("移动平均窗口必须大于 0")

        result = dataframe.copy()
        if result.empty:
            result["moving_avg_7d"] = pd.Series(dtype="float64")
            return result

        result = result.sort_values(["code", "trade_date"]).reset_index(drop=True)
        column_name = f"moving_avg_{window}d"
        result[column_name] = result.groupby("code")["middle_rate"].transform(
            lambda values: values.rolling(window=window, min_periods=1).mean()
        )
        # 保持需求中约定的 7 日字段名，其他窗口仍保留动态字段名。
        if window == 7:
            result["moving_avg_7d"] = result[column_name]
        return result

    @staticmethod
    def calculate_extremes(dataframe: pd.DataFrame) -> pd.DataFrame:
        """统计各币种分析区间内的最高价、最低价及对应日期。"""
        if dataframe.empty:
            return pd.DataFrame(
                columns=["code", "name", "max_middle_rate", "max_date", "min_middle_rate", "min_date"]
            )

        rows: list[dict[str, Any]] = []
        for (code, name), group in dataframe.groupby(["code", "name"], dropna=False):
            max_index = group["middle_rate"].idxmax()
            min_index = group["middle_rate"].idxmin()
            rows.append(
                {
                    "code": code,
                    "name": name,
                    "max_middle_rate": group.loc[max_index, "middle_rate"],
                    "max_date": group.loc[max_index, "trade_date"],
                    "min_middle_rate": group.loc[min_index, "middle_rate"],
                    "min_date": group.loc[min_index, "trade_date"],
                }
            )
        return pd.DataFrame(rows).sort_values("code").reset_index(drop=True)

    def analyze(
        self,
        code: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> ExchangeRateAnalysisResult:
        """执行完整分析并返回明细表和区间极值汇总表。"""
        dataframe = self.load_data(code=code, start_at=start_at, end_at=end_at)
        dataframe = self.calculate_daily_change(dataframe)
        dataframe = self.calculate_moving_average(dataframe, window=7)
        summary = self.calculate_extremes(dataframe)
        return ExchangeRateAnalysisResult(detail=dataframe, summary=summary)

