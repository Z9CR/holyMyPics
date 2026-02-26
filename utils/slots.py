from PySide6.QtWidgets import QListWidget, QLabel, QLineEdit
from PySide6.QtCore import Qt


def on_add_tag_clicked(tag_input: QLineEdit, tag_list_widget: QListWidget):
    print("addTag按钮被点击，接收到")
    tagStr = tag_input.text()
    # a,b,c,d,e,f,g
    if "," in tagStr:
        tags = tagStr.split(",")
        for tag in tags:
            # 比对每一个tag, 如果不重复则录入
            if not tag_list_widget.findItems(tag, Qt.MatchFlag.MatchExactly):
                tag_list_widget.addItem(tag)
    else:
        # 同上
        if not tag_list_widget.findItems(tagStr, Qt.MatchFlag.MatchExactly):
            tag_list_widget.addItem(tagStr)
    tag_input.clear()


def on_remove_tag_clicked(tag_list_widget: QListWidget):
    print("removeTag按钮被点击")
    tag_list_widget.takeItem(tag_list_widget.count() - 1)


def on_search_clicked(nickname_input: QLineEdit, result_label: QLabel):
    print("search按钮被点击，接收到")
