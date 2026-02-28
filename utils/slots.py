import sqlite3
import json
from typing import List
from PySide6.QtWidgets import (
    QWidget,
    QListWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

DB_PATH = "pics.db"


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


def _QListWidgetToList(qlistwidget: QListWidget) -> List[str]:
    ret = []
    for i in range(qlistwidget.count()):
        ret.append(qlistwidget.item(i).text())
    return ret


def on_search_clicked(
    tag_list_widget: QListWidget, nickname_input: QLineEdit, result_label: QLabel
) -> List[str]:
    print("search按钮被点击")
    # 从widget获取值
    # 昵称
    nickname = nickname_input.text()
    # 标签
    tags = _QListWidgetToList(tag_list_widget)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    file_hashes = []  # 改名以反映存储的是hash
    try:
        if tags and nickname:
            # 既有标签又有昵称：需要同时匹配
            placeholders = ",".join(["?"] * len(tags))
            query = f"""
                SELECT f.hash
                FROM files f
                WHERE nickname = ? 
                AND EXISTS (
                    SELECT 1
                    FROM json_each(f.tags) AS tag
                    WHERE tag.value IN ({placeholders})
                    GROUP BY f.hash
                    HAVING COUNT(DISTINCT tag.value) = ?
                )
            """
            cursor.execute(query, [nickname] + tags + [len(tags)])

        elif tags and not nickname:
            # 只有标签，没有昵称
            placeholders = ",".join(["?"] * len(tags))
            query = f"""
                SELECT hash
                FROM files
                WHERE hash IN (
                    SELECT f.hash
                    FROM files f, json_each(f.tags) AS tag
                    WHERE tag.value IN ({placeholders})
                    GROUP BY f.hash
                    HAVING COUNT(DISTINCT tag.value) = ?
                )
            """
            cursor.execute(query, tags + [len(tags)])

        elif not tags and nickname:
            # 只有昵称，没有标签
            query = "SELECT hash FROM files WHERE nickname = ?"
            cursor.execute(query, [nickname])

        else:
            # 既没有标签也没有昵称：返回所有文件
            query = "SELECT hash FROM files"
            cursor.execute(query)
        # 获取所有匹配的 hash
        rows = cursor.fetchall()
        file_hashes = [row[0] for row in rows]  # row[0] 现在是 hash
        # 更新结果显示标签（仍然显示文件数量）
        result_label.setText(f"找到 {len(file_hashes)} 个文件")
        print(f"找到 {len(file_hashes)} 个文件: {file_hashes}")
    except Exception as e:
        print(f"搜索时出错: {e}")
        result_label.setText("搜索出错")
    finally:
        conn.close()
    print(f"~~~获取到的文件hash\n{file_hashes}\n~~~")
    return file_hashes  # 返回 hash 列表


def on_show_tags_clicked(mainwindow: QMainWindow):
    # TODO: 展示一个窗口，内部包含数据库里所有的标签
    print("show tags clicked")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT tags FROM files")
    tagsJson = cursor.fetchall()
    # tagsJson 为(tags, )样式的元组
    # allTheTags 为 List[str], 包含所有的标签
    filteredTags = []
    for tagStr in tagsJson:
        tagArr = json.loads(tagStr[0])
        if not tagArr:
            continue
        for tag in tagArr:
            if tag not in filteredTags:
                filteredTags.append(tag)
    tagViewWindow = QWidget()
    tagViewWindow.setWindowTitle("选择标签")
    tagViewWindow.resize(480, 360)
    # 设置为垂直布局
    layout = QVBoxLayout()
    tagViewWindow.setLayout(layout)
    # 检索器
    filterArea = QWidget()
    filtersLayout = QHBoxLayout()
    tagsFilterInput = QLineEdit()

    # TODO: 为tagsFIlterInput添加placehover和实时输入搜索
    def _tag_refresh():
        keyword = tagsFilterInput.text().strip()
        if not keyword:
            # 无关键字则显示全部
            tagsListViewer.clear()
            tagsListViewer.addItems(filteredTags)
        else:
            # 保留包含关键字的标签
            filtered = [tag for tag in filteredTags if keyword in tag]
            tagsListViewer.clear()
            tagsListViewer.addItems(filtered)

    tagsFilterInput.setPlaceholderText("搜索标签...")
    tagsFilterInput.textChanged.connect(_tag_refresh)
    filtersLayout.addWidget(tagsFilterInput)
    filterArea.setLayout(filtersLayout)
    layout.addWidget(filterArea)
    # TODO: 在下方展示标签
    tagsListViewer = QListWidget()
    tagsListViewer.addItems(filteredTags)
    tagsListViewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    # 使可多选
    tagsListViewer.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # 创建字体对象, 设置字号
    tagsListViewer.setFont(QFont("", 16))
    layout.addWidget(tagsListViewer)
    # 防gc
    mainwindow._tagViewWindow = tagViewWindow
    tagViewWindow.show()


def on_image_clicked(file_hash: str, nickname: str, storage_name: str):
    """图片点击事件的槽函数"""
    print(f"图片被点击: hash={file_hash}, nickname={nickname}, storage={storage_name}")
    # TODO: 弹出详情窗口
