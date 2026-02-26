import sqlite3
import json
from typing import List

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


def fetchByName(nickname: str) -> List[str]:
    """
    根据昵称查询匹配的文件哈希列表。
    :param nickname: 昵称
    :return: 哈希值字符串列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT hash FROM files WHERE nickname = ?", (nickname,))
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def fetchByTag(tags: List[str]) -> List[str]:
    """
    根据标签JSON数组查询包含所有给定标签的文件哈希列表。
    支持 AND 语义：文件必须包含所有传入的标签。
    :param tags: 标签列表的JSON字符串数组，例如 ["风景","旅行"]
    :return: 哈希值字符串列表
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if not tags:
        cursor.execute("SELECT hash FROM files")
    else:
        placeholders = ",".join(["?"] * len(tags))
        query = f"""
            SELECT f.hash
            FROM files f, json_each(f.tags) AS tag
            WHERE tag.value IN ({placeholders})
            GROUP BY f.hash
            HAVING COUNT(DISTINCT tag.value) = ?
        """
        cursor.execute(query, tags + [len(tags)])
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]


def fetchAll() -> List[str]:
    """
    :return: 所有数据库里的所有hash值
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT hash FROM files")
        res = cursor.fetchall()
        return res
    except Exception as e:
        print(f"遇到错误{e}")
        return
    finally:
        conn.close()


def bHashInDB(hash: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM files WHERE hash = ?", (hash,))
    result = cursor.fetchone()
    conn.close()
    return result is not None
