import os
import hashlib
import sqlite3
import json
import shutil
from typing import List

TARGET_DIR = "pics"
DB_PATH = "pics.db"


def ensureFile(path: str) -> bool:
    """
    保证文件存在
    """
    return os.path.isfile(path)


def arrayToJson(tagsList: List[str]) -> str:
    """
    将字符串数组转换为 JSON 格式的
    """
    return json.dumps(tagsList, ensure_ascii=False)


def getFullExtensions(filepath: str) -> str:
    """
    @return: 全扩展名
    """
    filename = os.path.basename(filepath)
    if "." not in filename:
        return ""
    # 找到第一个点之后的所有内容
    first_dot = filename.find(".")
    return filename[first_dot:]


def getHashOf(filepath: str, chunkSize=8192):
    """
    获取文件hash
    @param filepath: 文件路径
    @param chunkSize: 每次读取的大小(K)
    """
    if not ensureFile(filepath):
        print(f"无法验证{filepath}的hash, \n{filepath} 可能非文件")
        return -1
    md5 = hashlib.md5()
    try:
        with open(filepath, "rb") as f:
            while True:
                data = f.read(chunkSize)
                if not data:
                    break
                md5.update(data)
        return md5.hexdigest()
    except (IOError, OSError) as e:
        print(f"获取hash值时遇到问题:\n{e}")
        return -1


def addFile(filepath: str, nickname: str, tagsList: List[str]) -> bool:
    """
    把filepath所指向的文件加入到文件库里
    @param filepath: 字符串, 文件的路径
    @param nickname: 字符串, 录入的昵称
    @param tagsList: 字符串数组, 将要打上的tag
    @return: bool类型, True为正常, False为异常
    """
    if not ensureFile(filepath):
        print(f"{filepath} 非文件!")
        return False
    filehash = getHashOf(filepath)
    storageName = filehash + getFullExtensions(filepath)
    tagsJson = arrayToJson(tagsList)
    print(
        f"即将把{filepath}存入db\n存储名: {storageName}\nhash: {filehash}\n昵称: {nickname}\n 标签json: {tagsJson}"
    )
    # filehash: 当前文件的hash值
    # extension: 全扩展名(如.tar.gz)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO files (hash, storageName, nickname, tags) VALUES (?, ?, ?, ?)",
            (filehash, storageName, nickname, tagsJson),
        )
        conn.commit()
        conn.close()

        src_path = filepath
        dest_path = os.path.join(TARGET_DIR, storageName)
        shutil.copy2(src_path, dest_path)
    except Exception as e:
        print(f"添加文件失败:\n{e}")
        conn.rollback()
        conn.close()
        return False


def deleteFile(hash: str):
    """
    在DB_PATH数据库里的files删除键为hash的项
    在TARGET_DIR里删除数据库里对应的文件
    @param hash: 给定hash值
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM files WHERE hash = ?", (hash,))
    result = cursor.fetchone()
    print(f"即将删除: {result}")
    # result is a tuple,
    # like (hash, storageName, nickname, taglist)
    cursor.execute("DELETE FROM files WHERE hash = ?", (hash,))
    conn.commit()
    deletePath = os.path.join(TARGET_DIR, result[1])
    try:
        os.remove(deletePath)
    except Exception as e:
        print(f"删除文件时遇到错误: {e}")
    finally:
        conn.close()
