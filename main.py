import fileworks as fw
import database as db

DB_PATH = "pics.db"
TARGET_DIR = "pics"


def main():
    pass


def debug():
    src = input("*dbg 源")
    fw.addFile(src, "aaa", ["taga", "tagb"])


if __name__ == "__main__":
    db.initDatabase()
    #    main()
    debug()
