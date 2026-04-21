-- BTC助手K线数据表设计
-- 根据btc_quant_team工程需求定制
-- 数据库: btc_assistant
-- 创建日期: 2026-04-21

USE `btc_assistant`;

-- 1. 交易所表 (简化，匹配工程需求)
CREATE TABLE IF NOT EXISTS `exchanges` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(50) NOT NULL COMMENT '交易所名称',
    `code` VARCHAR(20) NOT NULL COMMENT '交易所代码',
    `api_url` VARCHAR(255) NOT NULL COMMENT 'API地址',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_code` (`code`),
    INDEX `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易所表';

-- 插入主要交易所
INSERT IGNORE INTO `exchanges` (`name`, `code`, `api_url`) VALUES
('Binance', 'BINANCE', 'https://api.binance.com'),
('Coinbase', 'COINBASE', 'https://api.coinbase.com'),
('OKX', 'OKX', 'https://www.okx.com');

-- 2. 交易对表 (简化，匹配工程需求)
CREATE TABLE IF NOT EXISTS `symbols` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `exchange_id` INT UNSIGNED NOT NULL COMMENT '交易所ID',
    `symbol` VARCHAR(20) NOT NULL COMMENT '交易对',
    `base_asset` VARCHAR(10) NOT NULL COMMENT '基础货币',
    `quote_asset` VARCHAR(10) NOT NULL COMMENT '计价货币',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否激活',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_exchange_symbol` (`exchange_id`, `symbol`),
    INDEX `idx_symbol` (`symbol`),
    INDEX `idx_active` (`is_active`),
    CONSTRAINT `fk_symbols_exchange` FOREIGN KEY (`exchange_id`) 
        REFERENCES `exchanges` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='交易对表';

-- 插入BTC主要交易对
INSERT IGNORE INTO `symbols` (`exchange_id`, `symbol`, `base_asset`, `quote_asset`) 
SELECT id, 'BTCUSDT', 'BTC', 'USDT' FROM `exchanges` WHERE code = 'BINANCE';

INSERT IGNORE INTO `symbols` (`exchange_id`, `symbol`, `base_asset`, `quote_asset`) 
SELECT id, 'BTC-USD', 'BTC', 'USD' FROM `exchanges` WHERE code = 'COINBASE';

-- 3. K线数据表 (核心表，完全匹配工程fetch.py的数据结构)
CREATE TABLE IF NOT EXISTS `klines` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `symbol_id` INT UNSIGNED NOT NULL COMMENT '交易对ID',
    
    -- 时间信息 (匹配fetch.py的timestamp字段)
    `timestamp` BIGINT NOT NULL COMMENT '开盘时间戳(毫秒)',
    `open_time` DATETIME NOT NULL COMMENT '开盘时间',
    `close_time` DATETIME NOT NULL COMMENT '收盘时间',
    `close_timestamp` BIGINT NOT NULL COMMENT '收盘时间戳(毫秒)',
    
    -- K线参数
    `timeframe` ENUM('1m','5m','15m','30m','1h','4h','1d','1w','1M') NOT NULL COMMENT '时间框架',
    
    -- 价格数据 (完全匹配fetch.py返回格式)
    `open` DECIMAL(20,8) NOT NULL COMMENT '开盘价',
    `high` DECIMAL(20,8) NOT NULL COMMENT '最高价',
    `low` DECIMAL(20,8) NOT NULL COMMENT '最低价',
    `close` DECIMAL(20,8) NOT NULL COMMENT '收盘价',
    
    -- 成交量数据 (匹配fetch.py字段名)
    `volume` DECIMAL(30,8) NOT NULL COMMENT '成交量(基础货币)',
    `quote_volume` DECIMAL(30,8) NOT NULL COMMENT '成交额(计价货币)',
    
    -- 交易信息
    `trades` INT UNSIGNED NOT NULL COMMENT '交易笔数',
    `taker_buy_base` DECIMAL(30,8) NOT NULL COMMENT '主动买入基础货币量',
    `taker_buy_quote` DECIMAL(30,8) NOT NULL COMMENT '主动买入报价货币量',
    
    -- 状态标志
    `is_closed` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否已收盘',
    `data_source` VARCHAR(20) NOT NULL DEFAULT 'BINANCE' COMMENT '数据来源',
    
    -- 系统字段
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (`id`),
    
    -- 唯一约束：防止重复数据
    UNIQUE KEY `uk_symbol_timeframe_timestamp` (`symbol_id`, `timeframe`, `timestamp`),
    
    -- 查询优化索引
    INDEX `idx_symbol_timeframe` (`symbol_id`, `timeframe`),
    INDEX `idx_timestamp` (`timestamp`),
    INDEX `idx_open_time` (`open_time`),
    INDEX `idx_close_time` (`close_time`),
    INDEX `idx_is_closed` (`is_closed`),
    
    -- 外键约束
    CONSTRAINT `fk_klines_symbol` FOREIGN KEY (`symbol_id`) 
        REFERENCES `symbols` (`id`) ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='K线数据表';

-- 4. 创建实用视图
CREATE OR REPLACE VIEW `v_klines` AS
SELECT 
    k.id,
    k.symbol_id,
    s.symbol,
    s.base_asset,
    s.quote_asset,
    e.name as exchange_name,
    e.code as exchange_code,
    k.timestamp,
    k.open_time,
    k.close_time,
    k.close_timestamp,
    k.timeframe,
    k.open,
    k.high,
    k.low,
    k.close,
    k.volume,
    k.quote_volume,
    k.trades,
    k.taker_buy_base,
    k.taker_buy_quote,
    k.is_closed,
    k.data_source,
    k.created_at,
    k.updated_at
FROM `klines` k
JOIN `symbols` s ON k.symbol_id = s.id
JOIN `exchanges` e ON s.exchange_id = e.id;

-- 5. 创建数据质量检查函数
DELIMITER //
CREATE FUNCTION `check_kline_quality`(
    p_open DECIMAL(20,8),
    p_high DECIMAL(20,8),
    p_low DECIMAL(20,8),
    p_close DECIMAL(20,8)
) RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
    -- 检查价格合理性
    IF p_low > p_high THEN
        RETURN 'INVALID_PRICE';
    ELSEIF p_open <= 0 OR p_high <= 0 OR p_low <= 0 OR p_close <= 0 THEN
        RETURN 'ZERO_PRICE';
    ELSEIF p_high / p_low > 2 THEN  -- 价格波动过大
        RETURN 'HIGH_VOLATILITY';
    ELSE
        RETURN 'GOOD';
    END IF;
END //
DELIMITER ;

-- 6. 创建插入触发器（数据验证）
DELIMITER //
CREATE TRIGGER `trg_klines_before_insert`
BEFORE INSERT ON `klines`
FOR EACH ROW
BEGIN
    -- 自动设置时间字段
    SET NEW.open_time = FROM_UNIXTIME(NEW.timestamp / 1000);
    SET NEW.close_time = FROM_UNIXTIME(NEW.close_timestamp / 1000);
    
    -- 验证价格数据
    IF NEW.high < NEW.low THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = '最高价不能低于最低价';
    END IF;
    
    IF NEW.open <= 0 OR NEW.high <= 0 OR NEW.low <= 0 OR NEW.close <= 0 THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = '价格必须大于0';
    END IF;
END //
DELIMITER ;

-- 7. 显示创建结果
SELECT '✅ K线数据表创建完成!' as message;

SELECT 
    TABLE_NAME as '表名',
    TABLE_ROWS as '行数',
    DATA_LENGTH as '数据大小(字节)',
    INDEX_LENGTH as '索引大小(字节)',
    CREATE_TIME as '创建时间'
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = 'btc_assistant'
ORDER BY TABLE_NAME;

-- 8. 使用示例
SELECT '📊 使用示例:' as example_title;
SELECT '1. 查看最新BTC价格:' as example_1;
SELECT '   SELECT symbol, open_time, close, volume FROM v_klines WHERE symbol = ''BTCUSDT'' ORDER BY timestamp DESC LIMIT 5;' as query_1;
SELECT '';
SELECT '2. 插入测试数据:' as example_2;
SELECT '   INSERT INTO klines (symbol_id, timestamp, open_time, close_time, close_timestamp, timeframe, open, high, low, close, volume, quote_volume, trades, taker_buy_base, taker_buy_quote) VALUES (1, UNIX_TIMESTAMP()*1000, NOW(), DATE_ADD(NOW(), INTERVAL 1 HOUR), UNIX_TIMESTAMP()*1000+3600000, ''1h'', 70000, 71000, 69000, 70500, 100.5, 7050000, 5000, 60.3, 4200000);' as query_2;
SELECT '';
SELECT '3. 数据质量检查:' as example_3;
SELECT '   SELECT check_kline_quality(open, high, low, close) as quality, COUNT(*) as count FROM klines GROUP BY quality;' as query_3;