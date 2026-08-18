-- SpiderFlow 数据库初始化脚本。
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS currencies (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    code VARCHAR(16) NOT NULL COMMENT '币种编码，例如 USD',
    name VARCHAR(64) NOT NULL COMMENT '币种中文名称',
    is_active TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用：1 启用，0 停用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_currencies_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='币种基础信息';

CREATE TABLE IF NOT EXISTS exchange_rates (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    currency_id BIGINT UNSIGNED NOT NULL COMMENT '关联币种主键',
    cash_buying_rate DECIMAL(12, 4) NULL COMMENT '现钞买入价',
    cash_selling_rate DECIMAL(12, 4) NULL COMMENT '现钞卖出价',
    spot_buying_rate DECIMAL(12, 4) NULL COMMENT '现汇买入价',
    spot_selling_rate DECIMAL(12, 4) NULL COMMENT '现汇卖出价',
    middle_rate DECIMAL(12, 4) NULL COMMENT '中行折算价',
    published_at DATETIME NOT NULL COMMENT '源站发布时间',
    source_url VARCHAR(500) NOT NULL COMMENT '数据来源地址',
    crawled_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '实际采集时间',
    PRIMARY KEY (id),
    UNIQUE KEY uk_exchange_rates_currency_published (currency_id, published_at),
    KEY idx_exchange_rates_published_at (published_at),
    CONSTRAINT fk_exchange_rates_currency
        FOREIGN KEY (currency_id) REFERENCES currencies (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='外汇牌价快照';

CREATE TABLE IF NOT EXISTS job_runs (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '主键',
    job_name VARCHAR(128) NOT NULL COMMENT '任务名称',
    started_at DATETIME NOT NULL COMMENT '开始时间',
    finished_at DATETIME NULL COMMENT '结束时间',
    status VARCHAR(32) NOT NULL COMMENT '执行状态：RUNNING、SUCCESS、FAILED',
    record_count INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '处理记录数',
    error_message TEXT NULL COMMENT '错误摘要',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    KEY idx_job_runs_job_started (job_name, started_at),
    KEY idx_job_runs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务运行日志';

INSERT INTO currencies (code, name) VALUES
    ('USD', '美元'),
    ('EUR', '欧元'),
    ('JPY', '日元'),
    ('GBP', '英镑')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    is_active = 1;

