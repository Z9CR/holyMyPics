import fileworks as fw
import database as db

DB_PATH = "pics.db"
TARGET_DIR = "pics"


def main():
    pass


def debug():
    """
    用于测试程序
    """
    # src = input("*dbg 文件源")
    # fw.addFile(src, "aaa", ["taga", "tagb"])
    fw.deleteFile("1b81d534dc51b4089fd40976a87992b4")


if __name__ == "__main__":
    db.initDatabase()
    #    main()
    debug()
