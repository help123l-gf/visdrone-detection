"""
数据库连接层 — SQLite
使用 Python 内置 sqlite3，零配置，无需安装任何软件
数据库文件自动创建在 backend/data/visdrone.db
"""
import sqlite3
import os

# 数据库文件路径
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "visdrone.db")


def get_db() -> sqlite3.Connection:
    """获取数据库连接。每次调用返回新连接，用完需关闭。"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 让查询结果可以用 row["列名"] 访问
    conn.execute("PRAGMA journal_mode=WAL")  # 提升并发性能
    conn.execute("PRAGMA foreign_keys=ON")   # 启用外键约束
    return conn


def init_db():
    """初始化数据库表（如果表不存在则自动创建）"""
    conn = get_db()
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL UNIQUE,
            email VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            nickname VARCHAR(50) DEFAULT '',
            avatar_url VARCHAR(500) DEFAULT '',
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 检测记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detection_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            type VARCHAR(20) NOT NULL,
            model_name VARCHAR(50) NOT NULL,
            total_objects INTEGER DEFAULT 0,
            max_objects INTEGER DEFAULT 0,
            congestion_level VARCHAR(20) DEFAULT '',
            filename VARCHAR(255) DEFAULT '',
            image_url VARCHAR(500) DEFAULT '',
            result_image_url VARCHAR(500) DEFAULT '',
            detection_time FLOAT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"[数据库] SQLite 初始化完成 → {DB_PATH}")
