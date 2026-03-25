-- ============================================================
-- 城市空气质量数据可视化与趋势预测系统 - 数据库初始化脚本
-- 数据库: air_quality_system
-- 字符集: utf8mb4
-- ============================================================

CREATE DATABASE IF NOT EXISTS air_quality_system
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE air_quality_system;

-- ============================================================
-- 表1: cities - 城市基础信息
-- ============================================================
CREATE TABLE cities (
    id          INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(50)     NOT NULL COMMENT '城市名称',
    province    VARCHAR(50)     NOT NULL COMMENT '所属省份',
    city_code   VARCHAR(20)     NOT NULL COMMENT '城市编码(如 110000)',
    latitude    DECIMAL(10, 6)  NOT NULL COMMENT '纬度',
    longitude   DECIMAL(10, 6)  NOT NULL COMMENT '经度',
    population  INT UNSIGNED    DEFAULT NULL COMMENT '常住人口(万)',
    city_level  ENUM('一线','新一线','二线','三线','其他') DEFAULT '其他' COMMENT '城市等级',
    created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_city_code (city_code),
    INDEX idx_province (province)
) ENGINE=InnoDB COMMENT='城市基础信息表';


-- ============================================================
-- 表2: monitoring_stations - 监测站点详情
-- ============================================================
CREATE TABLE monitoring_stations (
    id              INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    city_id         INT UNSIGNED    NOT NULL COMMENT '所属城市ID',
    station_name    VARCHAR(100)    NOT NULL COMMENT '站点名称',
    station_code    VARCHAR(30)     NOT NULL COMMENT '站点编码',
    address         VARCHAR(255)    DEFAULT NULL COMMENT '站点地址',
    latitude        DECIMAL(10, 6)  NOT NULL COMMENT '站点纬度',
    longitude       DECIMAL(10, 6)  NOT NULL COMMENT '站点经度',
    station_type    ENUM('国控','省控','市控') DEFAULT '国控' COMMENT '站点类型',
    status          ENUM('active','inactive','maintenance') DEFAULT 'active' COMMENT '运行状态',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_station_code (station_code),
    INDEX idx_city_id (city_id),
    CONSTRAINT fk_station_city FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='监测站点详情表';


-- ============================================================
-- 表3: air_quality_records - 空气质量数据记录
-- 存储每小时/每日的 AQI 及六项污染物浓度
-- ============================================================
CREATE TABLE air_quality_records (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    station_id          INT UNSIGNED    NOT NULL COMMENT '监测站点ID',
    city_id             INT UNSIGNED    NOT NULL COMMENT '城市ID(冗余,加速查询)',
    record_time         DATETIME        NOT NULL COMMENT '监测时间',
    record_type         ENUM('hourly','daily') DEFAULT 'daily' COMMENT '记录粒度',
    aqi                 SMALLINT UNSIGNED DEFAULT NULL COMMENT '空气质量指数',
    pm25                DECIMAL(8, 2)   DEFAULT NULL COMMENT 'PM2.5浓度(ug/m3)',
    pm10                DECIMAL(8, 2)   DEFAULT NULL COMMENT 'PM10浓度(ug/m3)',
    so2                 DECIMAL(8, 2)   DEFAULT NULL COMMENT 'SO2浓度(ug/m3)',
    no2                 DECIMAL(8, 2)   DEFAULT NULL COMMENT 'NO2浓度(ug/m3)',
    co                  DECIMAL(8, 2)   DEFAULT NULL COMMENT 'CO浓度(mg/m3)',
    o3                  DECIMAL(8, 2)   DEFAULT NULL COMMENT 'O3浓度(ug/m3)',
    temperature         DECIMAL(5, 1)   DEFAULT NULL COMMENT '温度(℃)',
    humidity            TINYINT UNSIGNED DEFAULT NULL COMMENT '相对湿度(%)',
    wind_speed          DECIMAL(5, 1)   DEFAULT NULL COMMENT '风速(m/s)',
    wind_direction      VARCHAR(10)     DEFAULT NULL COMMENT '风向(北/东北/东...)',
    rainfall            DECIMAL(6, 1)   DEFAULT 0   COMMENT '降水量(mm)',
    weather_condition   VARCHAR(20)     DEFAULT NULL COMMENT '天气状况(晴/多云/阴/雨...)',
    primary_pollutant   VARCHAR(20)     DEFAULT NULL COMMENT '首要污染物',
    quality_level       ENUM('优','良','轻度污染','中度污染','重度污染','严重污染') DEFAULT NULL COMMENT '空气质量等级',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_city_time (city_id, record_time),
    INDEX idx_station_time (station_id, record_time),
    INDEX idx_record_time (record_time),
    INDEX idx_aqi (aqi),
    CONSTRAINT fk_record_station FOREIGN KEY (station_id) REFERENCES monitoring_stations(id) ON DELETE CASCADE,
    CONSTRAINT fk_record_city FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='空气质量数据记录表';


-- ============================================================
-- 表4: prediction_results - 算法预测结果
-- ============================================================
CREATE TABLE prediction_results (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    city_id             INT UNSIGNED    NOT NULL COMMENT '城市ID',
    algorithm_type      VARCHAR(30)     NOT NULL DEFAULT 'moving_average' COMMENT '算法类型',
    metric_name         VARCHAR(20)     NOT NULL COMMENT '指标名(aqi/pm25/pm10等)',
    prediction_date     DATE            NOT NULL COMMENT '预测的目标日期',
    predicted_value     DECIMAL(10, 2)  NOT NULL COMMENT '预测值',
    confidence_upper    DECIMAL(10, 2)  DEFAULT NULL COMMENT '置信区间上界',
    confidence_lower    DECIMAL(10, 2)  DEFAULT NULL COMMENT '置信区间下界',
    actual_value        DECIMAL(10, 2)  DEFAULT NULL COMMENT '实际值(回填用)',
    window_size         INT UNSIGNED    DEFAULT 7 COMMENT '移动平均窗口大小',
    mape                DECIMAL(6, 2)   DEFAULT NULL COMMENT '平均绝对百分比误差(%)',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_city_metric_date (city_id, metric_name, prediction_date),
    INDEX idx_algorithm (algorithm_type),
    CONSTRAINT fk_prediction_city FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
) ENGINE=InnoDB COMMENT='算法预测结果表';


-- ============================================================
-- 表5: anomaly_events - IQR 异常事件记录
-- ============================================================
CREATE TABLE anomaly_events (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    city_id         INT UNSIGNED    NOT NULL COMMENT '城市ID',
    station_id      INT UNSIGNED    DEFAULT NULL COMMENT '站点ID(可为空表示城市级别)',
    metric_name     VARCHAR(20)     NOT NULL COMMENT '异常指标(aqi/pm25等)',
    record_time     DATETIME        NOT NULL COMMENT '异常发生时间',
    actual_value    DECIMAL(10, 2)  NOT NULL COMMENT '实际观测值',
    q1_value        DECIMAL(10, 2)  NOT NULL COMMENT '第一四分位数(Q1)',
    q3_value        DECIMAL(10, 2)  NOT NULL COMMENT '第三四分位数(Q3)',
    iqr_value       DECIMAL(10, 2)  NOT NULL COMMENT '四分位距(IQR=Q3-Q1)',
    lower_bound     DECIMAL(10, 2)  NOT NULL COMMENT '下界(Q1-1.5*IQR)',
    upper_bound     DECIMAL(10, 2)  NOT NULL COMMENT '上界(Q3+1.5*IQR)',
    anomaly_type    ENUM('high','low') NOT NULL COMMENT '异常方向',
    severity        ENUM('mild','moderate','severe') DEFAULT 'mild' COMMENT '严重程度',
    status          ENUM('pending','confirmed','dismissed') DEFAULT 'pending' COMMENT '处理状态',
    description     TEXT            DEFAULT NULL COMMENT '异常描述',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_city_metric (city_id, metric_name),
    INDEX idx_record_time (record_time),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    CONSTRAINT fk_anomaly_city FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE,
    CONSTRAINT fk_anomaly_station FOREIGN KEY (station_id) REFERENCES monitoring_stations(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='IQR异常事件记录表';


-- ============================================================
-- 表6: users - 用户信息
-- ============================================================
CREATE TABLE users (
    id              INT UNSIGNED    AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)     NOT NULL COMMENT '用户名',
    password_hash   VARCHAR(255)    NOT NULL COMMENT '密码哈希',
    nickname        VARCHAR(50)     DEFAULT NULL COMMENT '昵称',
    avatar_url      VARCHAR(500)    DEFAULT NULL COMMENT '头像URL',
    role            ENUM('admin','user') DEFAULT 'user' COMMENT '角色',
    openid          VARCHAR(100)    DEFAULT NULL COMMENT '微信小程序OpenID',
    phone           VARCHAR(20)     DEFAULT NULL COMMENT '手机号',
    last_login_at   DATETIME        DEFAULT NULL COMMENT '最后登录时间',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_openid (openid),
    INDEX idx_role (role)
) ENGINE=InnoDB COMMENT='用户信息表';


-- ============================================================
-- 表7: ai_interaction_logs - AI 对话日志
-- ============================================================
CREATE TABLE ai_interaction_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED    DEFAULT NULL COMMENT '用户ID',
    city_id         INT UNSIGNED    DEFAULT NULL COMMENT '关联城市ID',
    session_id      VARCHAR(64)     NOT NULL COMMENT '会话ID(前端生成的UUID)',
    user_message    TEXT            NOT NULL COMMENT '用户输入内容',
    ai_response     TEXT            DEFAULT NULL COMMENT 'AI返回内容',
    context_data    JSON            DEFAULT NULL COMMENT '传入AI的上下文(AQI数据/预测/异常等)',
    model_name      VARCHAR(50)     DEFAULT 'qwen-turbo' COMMENT '调用的模型名称',
    tokens_used     INT UNSIGNED    DEFAULT NULL COMMENT '本次消耗token数',
    response_time_ms INT UNSIGNED   DEFAULT NULL COMMENT '响应时间(毫秒)',
    source          ENUM('web','miniapp') DEFAULT 'web' COMMENT '请求来源',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_city_id (city_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_ailog_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_ailog_city FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='AI对话日志表';
