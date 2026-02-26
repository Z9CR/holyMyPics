from PySide6.QtWidgets import QListWidget, QLabel, QLineEdit
from PySide6.QtCore import Qt


def on_add_tag_clicked(tag_input: QLineEdit, tag_list_widget: QListWidget):
    print(
        f"""addTag按钮被点击，接收到
        {tag_input}, {tag_list_widget};
    """
    )
    tagStr = tag_input.text()
    # a,b,c,d,e,f,g
    if "," in tagStr:
        tags = tagStr.split(",")
        for tag in tags:
            if not tag_list_widget.findItems(tag, Qt.MatchFlag.MatchExactly):
                tag_list_widget.addItem(tag)
    else:
        if not tag_list_widget.findItems(tagStr, Qt.MatchFlag.MatchExactly):
            tag_list_widget.addItem(tagStr)
    tag_input.clear()


def on_remove_tag_clicked(tag_list_widget: QListWidget):
    print(
        f"""removeTag按钮被点击，接收到
        {tag_list_widget};
    """
    )


def on_search_clicked(nickname_input: QLineEdit, result_label: QLabel):
    print(
        f"""search按钮被点击，接收到
        {nickname_input}, {result_label};
    """
    )
