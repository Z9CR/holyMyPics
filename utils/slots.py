import sqlite3
import os
import json
import pyperclip
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
from PySide6.QtGui import QFont, QPixmap
from PIL import Image, ImageQt
from utils.widgets import ImageViewer

DB_PATH = "pics.db"
TARGET_DIR = "pics"


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


def on_show_tags_clicked(
    mainwindow: QMainWindow,
    tag_list_widget: QListWidget,
    nickname_input: QLineEdit,
    result_label: QLabel,
    container: ImageViewer,
):
    # 展示一个窗口，内部包含数据库里所有的标签
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
    tagsFilterInput = QLineEdit()

    # 为tagsFIlterInput添加placehover和实时输入搜索
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
    layout.addWidget(tagsFilterInput)
    # 在下方展示标签
    tagsListViewer = QListWidget()
    tagsListViewer.addItems(filteredTags)
    tagsListViewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    # 使可多选
    tagsListViewer.setSelectionMode(QAbstractItemView.ExtendedSelection)
    # 创建字体对象, 设置字号
    tagsListViewer.setFont(QFont("", 16))
    layout.addWidget(tagsListViewer)
    # 复制为文本 与 搜索所选的 按钮
    operationButtonsArea = QWidget()
    operationButtonsAreaLayout = QHBoxLayout()
    copy_selected_btn = QPushButton("复制所选")
    search_selected_btn = QPushButton("搜索所选")

    # DONE: 添加傻逼槽函数
    # FUCKIT, from Feb to March, damn shit GUI!!!!
    # I hate Qt, not [kju:t] any more
    def _copy_selected_btn_on_clicked():
        print("copy_selected_btn被点击")
        formatedTagStr = ""
        tagsList = tagsListViewer.selectedItems()
        if not tagsList:
            return
        else:
            for tag in tagsList:
                formatedTagStr += tag.text()
                formatedTagStr += ","
        formatedTagStr = formatedTagStr[:-1]
        pyperclip.copy(formatedTagStr)

    def _search_selected_btn_on_clicked(
        mainwindow: QMainWindow,
        tag_list_widget: QListWidget,
        nickname_input: QLineEdit,
        result_label: QLabel,
        container: ImageViewer,
    ):
        print("search_selected_btn被点击")
        originTagList = tagsListViewer.selectedItems()
        tagsList = []
        for t in originTagList:
            tagsList.append(t.text())
        tag_list_widget.clear()
        tag_list_widget.addItems(tagsList)
        # 复用主窗口的search函数实现, 此函数返回获取到的文件的hash
        hashs = on_search_clicked(tag_list_widget, nickname_input, result_label)
        container.clear_images()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for hashKey in hashs:
            cursor.execute("SELECT * FROM files WHERE hash = ?", (hashKey,))
            searchResult = cursor.fetchone()
            # searchResult是以(hash, storageName, nickname, tags)格式的元组
            # tags是一个json格式的数组
            container.add_image(searchResult[0], searchResult[1], searchResult[2])
        conn.close()

    copy_selected_btn.clicked.connect(_copy_selected_btn_on_clicked)
    search_selected_btn.clicked.connect(
        lambda: _search_selected_btn_on_clicked(
            mainwindow, tag_list_widget, nickname_input, result_label, container
        )
    )
    # 把两个按钮加入到opteration....里
    operationButtonsAreaLayout.addWidget(copy_selected_btn)
    operationButtonsAreaLayout.addWidget(search_selected_btn)
    # 加入operationButtonArea至布局
    operationButtonsArea.setLayout(operationButtonsAreaLayout)
    layout.addWidget(operationButtonsArea)
    # 防gc
    mainwindow._tagViewWindow = tagViewWindow
    tagViewWindow.show()


def on_image_clicked(
    mainwindow: QMainWindow, file_hash: str, nickname: str, storage_name: str
):
    """图片点击事件的槽函数"""
    print(f"图片被点击: hash={file_hash}, nickname={nickname}, storage={storage_name}")
    # TODO: 弹出详情窗口
    imgInfoWindow = QWidget()
    # 将imgInfoWindow作为mainwindow的成员以防止gc
    mainwindow.imgInfoWindow = imgInfoWindow
    # 左图片右信息
    imgInfoWindowLayout = QHBoxLayout()
    imgLabel = QLabel()
    imgLabel.setFixedSize(360, 360)  # 固定显示区域
    imgLabel.setAlignment(Qt.AlignCenter)
    image_path = os.path.join("pics", storage_name)
    try:
        pil_image = Image.open(image_path)
        original_width, original_height = pil_image.size

        # 计算缩放尺寸：使长边缩放到 360
        if original_width >= original_height:
            # 横图或正方形：宽度为长边
            new_width = 360
            new_height = int(original_height * 360 / original_width)
        else:
            # 竖图：高度为长边
            new_height = 360
            new_width = int(original_width * 360 / original_height)

        # 使用高质量缩放
        pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        qimage = ImageQt.ImageQt(pil_image)
        pixmap = QPixmap.fromImage(qimage)
        imgLabel.setPixmap(pixmap)
    except Exception as e:
        print(f"加载图片失败: {e}")
        imgLabel.setText("无法加载图片")

    imgInfoWindowLayout.addWidget(imgLabel)
    # :右:
    imgInfoWindowRight = QWidget()

    # :右: 加入布局
    imgInfoWindowLayout.addWidget(imgInfoWindowRight)
    # show
    imgInfoWindow.setLayout(imgInfoWindowLayout)
    imgInfoWindow.show()
