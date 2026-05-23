-- VisDrone Detection Platform — Database Schema
-- Executed automatically on first PostgreSQL container start

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Users
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username    VARCHAR(50)  NOT NULL UNIQUE,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nickname    VARCHAR(50),
    role        VARCHAR(20)  DEFAULT 'user',
    avatar_url  VARCHAR(500),
    is_active   BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ============================================
-- Detection Records
-- ============================================
CREATE TABLE IF NOT EXISTS detection_records (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id             UUID REFERENCES users(id) ON DELETE SET NULL,
    type                VARCHAR(20)  NOT NULL,   -- single | batch | video | monitor
    status              VARCHAR(20)  DEFAULT 'completed',
    model_name          VARCHAR(50)  NOT NULL,
    model_version       VARCHAR(20)  DEFAULT '1.0.0',
    total_objects       INTEGER      DEFAULT 0,
    detection_time      FLOAT,
    original_image_key  VARCHAR(500),
    result_image_key    VARCHAR(500),
    error_message       TEXT,
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_records_user_id    ON detection_records(user_id);
CREATE INDEX IF NOT EXISTS idx_records_type       ON detection_records(type);
CREATE INDEX IF NOT EXISTS idx_records_created    ON detection_records(created_at DESC);

-- ============================================
-- Detection Results (per-box)
-- ============================================
CREATE TABLE IF NOT EXISTS detection_results (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    record_id   UUID         NOT NULL REFERENCES detection_records(id) ON DELETE CASCADE,
    x1          FLOAT        NOT NULL,
    y1          FLOAT        NOT NULL,
    x2          FLOAT        NOT NULL,
    y2          FLOAT        NOT NULL,
    confidence  FLOAT        NOT NULL,
    class_id    INTEGER      NOT NULL,
    class_name  VARCHAR(50)  NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_results_record ON detection_results(record_id);
CREATE INDEX IF NOT EXISTS idx_results_class  ON detection_results(class_name);

-- ============================================
-- Target Categories (VisDrone 10 classes)
-- ============================================
CREATE TABLE IF NOT EXISTS target_categories (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(50)  NOT NULL UNIQUE,
    chinese_name VARCHAR(50)  NOT NULL UNIQUE,
    description  TEXT,
    color        VARCHAR(20)  DEFAULT '#10b981',
    enabled      BOOLEAN      DEFAULT TRUE,
    sort_order   INTEGER      DEFAULT 0,
    created_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO target_categories (name, chinese_name, description, color, sort_order) VALUES
    ('pedestrian',       '行人',       '单个行人目标',               '#ef4444', 1),
    ('people',           '人群',       '密集人群目标',               '#dc2626', 2),
    ('bicycle',          '自行车',     '自行车及骑行者',             '#f59e0b', 3),
    ('car',              '汽车',       '小轿车、SUV等乘用车',        '#10b981', 4),
    ('van',              '面包车',     '厢式货车、面包车',           '#3b82f6', 5),
    ('truck',            '卡车',       '大型货运卡车',               '#8b5cf6', 6),
    ('tricycle',         '三轮车',     '人力或机动三轮车',           '#ec4899', 7),
    ('awning-tricycle',  '遮阳三轮车', '带遮阳棚的三轮车',           '#f97316', 8),
    ('bus',              '公交车',     '公共汽车、大巴客车',         '#84cc16', 9),
    ('motor',            '摩托车',     '摩托车、电动车',             '#6366f1', 10)
ON CONFLICT (name) DO UPDATE SET
    chinese_name = EXCLUDED.chinese_name,
    description  = EXCLUDED.description,
    color        = EXCLUDED.color,
    sort_order   = EXCLUDED.sort_order;
