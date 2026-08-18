"""应用配置读取与校验。"""

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    """集中保存应用运行所需的环境变量。"""

    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    timezone: str

    @property
    def database_url(self) -> str:
        """生成 SQLAlchemy 使用的 MySQL 连接地址。"""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )


def get_settings() -> Settings:
    """读取环境变量，缺失必要配置时立即报错。"""
    required_values = {
        "MYSQL_DATABASE": os.getenv("MYSQL_DATABASE"),
        "MYSQL_USER": os.getenv("MYSQL_USER"),
        "MYSQL_PASSWORD": os.getenv("MYSQL_PASSWORD"),
    }
    missing_keys = [key for key, value in required_values.items() if not value]
    if missing_keys:
        raise RuntimeError(f"缺少必要环境变量：{', '.join(missing_keys)}")

    return Settings(
        db_host=os.getenv("DB_HOST", "mysql"),
        db_port=int(os.getenv("DB_PORT", "3306")),
        db_name=required_values["MYSQL_DATABASE"] or "",
        db_user=required_values["MYSQL_USER"] or "",
        db_password=required_values["MYSQL_PASSWORD"] or "",
        timezone=os.getenv("APP_TIMEZONE", "Asia/Shanghai"),
    )

