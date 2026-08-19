"""SpiderFlow 数据库业务服务（可复用）"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Mapping

from sqlalchemy import Engine, text


class CurrencyService:
    """提供 currencies 表的增删改查操作。"""

    def __init__(self, engine: Engine):
        """保存可复用的 SQLAlchemy 数据库引擎。"""
        self.engine = engine

    def create(self, code: str, name: str, is_active: bool = True) -> int:
        """新增币种并返回主键 ID。"""
        insert_sql = text(
            """
            INSERT INTO currencies (code, name, is_active)
            VALUES (:code, :name, :is_active)
            """
        )
        with self.engine.begin() as connection:
            result = connection.execute(
                insert_sql,
                {
                    "code": code.strip().upper(),
                    "name": name.strip(),
                    "is_active": int(is_active),
                },
            )
            return int(result.lastrowid)

    def list(self, active_only: bool = False) -> list[dict[str, Any]]:
        """查询全部币种，可选只返回启用中的币种。"""
        where_clause = "WHERE is_active = 1" if active_only else ""
        query = text(
            f"""
            SELECT id, code, name, is_active, created_at, updated_at
            FROM currencies
            {where_clause}
            ORDER BY id
            """
        )
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(query).mappings()]

    def get_by_code(self, code: str) -> dict[str, Any] | None:
        """按币种编码查询一条币种记录。"""
        query = text(
            """
            SELECT id, code, name, is_active, created_at, updated_at
            FROM currencies
            WHERE code = :code
            """
        )
        with self.engine.connect() as connection:
            row = connection.execute(query, {"code": code.strip().upper()}).mappings().first()
            return dict(row) if row else None

    def update_status(self, code: str, is_active: bool) -> bool:
        """修改币种启用状态，并返回是否更新到记录。"""
        update_sql = text(
            """
            UPDATE currencies
            SET is_active = :is_active
            WHERE code = :code
            """
        )
        with self.engine.begin() as connection:
            result = connection.execute(
                update_sql,
                {"code": code.strip().upper(), "is_active": int(is_active)},
            )
            return result.rowcount > 0

    def delete(self, code: str) -> bool:
        """删除币种；已被汇率记录引用时会由外键约束阻止删除。"""
        delete_sql = text("DELETE FROM currencies WHERE code = :code")
        with self.engine.begin() as connection:
            result = connection.execute(delete_sql, {"code": code.strip().upper()})
            return result.rowcount > 0


class ExchangeRateService:
    """提供 exchange_rates 表的增删改查操作。"""

    def __init__(self, engine: Engine):
        """保存可复用的 SQLAlchemy 数据库引擎。"""
        self.engine = engine

    @staticmethod
    def _to_decimal(value: Any) -> Decimal | None:
        """将空值转换为 NULL，将牌价转换为 Decimal。"""
        return Decimal(str(value)) if value not in (None, "") else None

    def save_or_update(self, data: Mapping[str, Any]) -> bool:
        """按“币种名称 + 发布时间”幂等写入一条汇率记录。"""
        insert_sql = text(
            """
            INSERT INTO exchange_rates (
                currency_id,
                cash_buying_rate,
                cash_selling_rate,
                spot_buying_rate,
                spot_selling_rate,
                middle_rate,
                published_at,
                source_url,
                crawled_at
            )
            SELECT
                id,
                :cash_buying_rate,
                :cash_selling_rate,
                :spot_buying_rate,
                :spot_selling_rate,
                :middle_rate,
                :published_at,
                :source_url,
                :crawled_at
            FROM currencies
            WHERE name = :currency_name
              AND is_active = 1
            ON DUPLICATE KEY UPDATE
                cash_buying_rate = VALUES(cash_buying_rate),
                cash_selling_rate = VALUES(cash_selling_rate),
                spot_buying_rate = VALUES(spot_buying_rate),
                spot_selling_rate = VALUES(spot_selling_rate),
                middle_rate = VALUES(middle_rate),
                source_url = VALUES(source_url),
                crawled_at = VALUES(crawled_at)
            """
        )
        values = {
            "currency_name": data["currency_name"],
            "cash_buying_rate": self._to_decimal(data.get("cash_buying_rate")),
            "cash_selling_rate": self._to_decimal(data.get("cash_selling_rate")),
            "spot_buying_rate": self._to_decimal(data.get("spot_buying_rate")),
            "spot_selling_rate": self._to_decimal(data.get("spot_selling_rate")),
            "middle_rate": self._to_decimal(data.get("middle_rate")),
            "published_at": data["published_at"],
            "source_url": data["source_url"],
            "crawled_at": data.get("crawled_at", datetime.now()),
        }
        with self.engine.begin() as connection:
            result = connection.execute(insert_sql, values)
            return result.rowcount > 0

    def list(
        self,
        code: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """按币种编码和发布时间范围查询汇率记录。"""
        conditions = []
        params: dict[str, Any] = {}
        if code:
            conditions.append("c.code = :code")
            params["code"] = code.strip().upper()
        if start_at:
            conditions.append("e.published_at >= :start_at")
            params["start_at"] = start_at
        if end_at:
            conditions.append("e.published_at <= :end_at")
            params["end_at"] = end_at

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = text(
            f"""
            SELECT
                e.id, c.code, c.name,
                e.cash_buying_rate, e.cash_selling_rate,
                e.spot_buying_rate, e.spot_selling_rate,
                e.middle_rate, e.published_at,
                e.source_url, e.crawled_at
            FROM exchange_rates e
            JOIN currencies c ON c.id = e.currency_id
            {where_clause}
            ORDER BY e.published_at DESC, e.id DESC
            """
        )
        with self.engine.connect() as connection:
            return [dict(row) for row in connection.execute(query, params).mappings()]

    def update(self, rate_id: int, **fields: Any) -> bool:
        """按汇率记录 ID 更新允许修改的字段。"""
        allowed_fields = {
            "cash_buying_rate",
            "cash_selling_rate",
            "spot_buying_rate",
            "spot_selling_rate",
            "middle_rate",
            "published_at",
            "source_url",
        }
        updates = {key: value for key, value in fields.items() if key in allowed_fields}
        if not updates:
            raise ValueError("至少提供一个可更新的汇率字段")

        assignments = []
        params: dict[str, Any] = {"rate_id": rate_id}
        for field, value in updates.items():
            assignments.append(f"{field} = :{field}")
            params[field] = self._to_decimal(value) if field.endswith("rate") else value

        update_sql = text(
            f"UPDATE exchange_rates SET {', '.join(assignments)} WHERE id = :rate_id"
        )
        with self.engine.begin() as connection:
            result = connection.execute(update_sql, params)
            return result.rowcount > 0

    def delete(self, rate_id: int) -> bool:
        """按汇率记录 ID 删除一条记录。"""
        delete_sql = text("DELETE FROM exchange_rates WHERE id = :rate_id")
        with self.engine.begin() as connection:
            result = connection.execute(delete_sql, {"rate_id": rate_id})
            return result.rowcount > 0

    def delete_by_date_range(
        self,
        start_at: datetime,
        end_at: datetime,
        code: str | None = None,
    ) -> int:
        """删除指定发布时间范围内的汇率记录，并返回删除数量。"""
        conditions = [
            "e.published_at >= :start_at",
            "e.published_at <= :end_at",
        ]
        params: dict[str, Any] = {
            "start_at": start_at,
            "end_at": end_at,
        }
        if code:
            conditions.append("c.code = :code")
            params["code"] = code.strip().upper()

        delete_sql = text(
            f"""
            DELETE e
            FROM exchange_rates e
            JOIN currencies c ON c.id = e.currency_id
            WHERE {' AND '.join(conditions)}
            """
        )
        with self.engine.begin() as connection:
            result = connection.execute(delete_sql, params)
            return int(result.rowcount)


class JobRunService:
    """提供 job_runs 表的任务日志操作。"""

    VALID_STATUSES = {"RUNNING", "SUCCESS", "FAILED"}

    def __init__(self, engine: Engine):
        """保存可复用的 SQLAlchemy 数据库引擎。"""
        self.engine = engine

    def create_running(self, job_name: str, started_at: datetime | None = None) -> int:
        """创建 RUNNING 状态的任务日志并返回日志 ID。"""
        insert_sql = text(
            """
            INSERT INTO job_runs (job_name, started_at, status)
            VALUES (:job_name, :started_at, 'RUNNING')
            """
        )
        with self.engine.begin() as connection:
            result = connection.execute(
                insert_sql,
                {"job_name": job_name, "started_at": started_at or datetime.now()},
            )
            return int(result.lastrowid)

    def finish(
        self,
        run_id: int,
        status: str,
        record_count: int = 0,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> bool:
        """更新任务完成状态、处理数量和错误信息。"""
        status = status.upper()
        if status not in {"SUCCESS", "FAILED"}:
            raise ValueError("任务完成状态只能是 SUCCESS 或 FAILED")

        update_sql = text(
            """
            UPDATE job_runs
            SET finished_at = :finished_at,
                status = :status,
                record_count = :record_count,
                error_message = :error_message
            WHERE id = :run_id
            """
        )
        with self.engine.begin() as connection:
            result = connection.execute(
                update_sql,
                {
                    "run_id": run_id,
                    "finished_at": finished_at or datetime.now(),
                    "status": status,
                    "record_count": record_count,
                    "error_message": error_message,
                },
            )
            return result.rowcount > 0

    def list(self, job_name: str | None = None) -> list[dict[str, Any]]:
        """查询最近的任务日志。"""
        query = text(
            """
            SELECT id, job_name, started_at, finished_at,
                   status, record_count, error_message, created_at
            FROM job_runs
            WHERE (:job_name IS NULL OR job_name = :job_name)
            ORDER BY started_at DESC, id DESC
            """
        )
        with self.engine.connect() as connection:
            rows = connection.execute(query, {"job_name": job_name}).mappings()
            return [dict(row) for row in rows]

    def delete(self, run_id: int) -> bool:
        """按任务日志 ID 删除一条记录。"""
        delete_sql = text("DELETE FROM job_runs WHERE id = :run_id")
        with self.engine.begin() as connection:
            result = connection.execute(delete_sql, {"run_id": run_id})
            return result.rowcount > 0
