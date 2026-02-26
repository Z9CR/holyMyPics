import utils.fileworks as fw
import utils.database as db

if __name__ == "__main__":
    db.initDatabase()
    fw.addFile(
        "/home/z9cr/workspace/buf/1768920088258.jpeg", "aaa", ["luoxiaohei", "anime"]
    )
    fw.addFile(
        "/home/z9cr/workspace/buf/1768623070322.png", "bbb", ["luoxiaohei", "cat"]
    )
    fw.addFile("/home/z9cr/workspace/buf/OIP-C.webp", "bbb", ["gunmu", "anime"])
    print(db.fetchByTag(["anime"]))
    print(db.fetchByName("aaa"))
    print(db.fetchByName("bbb"))
    print(db.fetchByTag(["luoxiaohei", "cat"]))
