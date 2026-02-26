from PySide6.QtWidgets import QListWidget, QLabel, QLineEdit


def on_add_tag_clicked(tag_input: QLineEdit, tag_list_widget: QListWidget):
    print(
        f"""addTag按钮被点击，接收到
        {tag_input}, {tag_list_widget};
    """
    )


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
