import sqlite3

DB_PATH = "pics.db"


def initDatabase():
    """初始化数据库，创建所需的表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 所有表以hash为主键
    # 文件主表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            hash TEXT PRIMARY KEY UNIQUE NOT NULL,-- 文件哈希(MD5)
            storageName TEXT UNIQUE NOT NULL, -- 哈希值+扩展名
            nickname TEXT NOT NULL,
            tags TEXT -- json格式存储
        )
    """)
    conn.commit()
    print("数据库初始化成功")
    conn.close()


def bHashInDB(hash: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM files WHERE hash = ?", (hash,))
    result = cursor.fetchone()
    conn.close()
    return result is not None
