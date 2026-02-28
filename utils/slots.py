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
    ##structure of imgInfoWindowRight:
    #   nickname: QLineEdit + submit: QPushButton; 20% of vh !DONE
    #   tags: QLineEdit + submit: QPushButton;     40% of vh !DONE
    #   pathToFile: QLabel + copy: QPushButton;    10% of vh !DONE
    #   hash: QLabel;                              10% of vh !DONE
    #   size: QLabel;                              10% of vh !DONE
    #   Finish: QPushBtn   + DeleteBtn;            10% of vh
    imgInfoWindowRightLayout = QVBoxLayout()
    # :右: nicknameArea
    nicknameArea = QWidget()
    nicknameAreaLayout = QHBoxLayout()
    nicknameArea.setLayout(nicknameAreaLayout)

    nicknameHinter = QLabel("更改名称")
    nicknameModifier = QLineEdit()
    nicknameModifier.setText(nickname)
    nicknameModifier.setPlaceholderText("输入新的名称")
    nicknameModifierSubmiter = QPushButton("提交")

    def on_nicknameModifierSubmiter_clicked(file_hash: str, newNickname: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM files WHERE hash = ?", (file_hash,))
            oldProperties = cursor.fetchone()
            # oldProperties: (hash,  storageName, nickname, tagsJson)
            cursor.execute("DELETE FROM files WHERE hash = ?", (file_hash,))
            cursor.execute(
                "INSERT INTO files (hash, storageName, nickname, tags) VALUES (?, ?, ?, ?)",
                (oldProperties[0], oldProperties[1], newNickname, oldProperties[3]),
            )
            conn.commit()
        except Exception as e:
            print(f"在更改名称时遇到问题:\n{e}")
            raise
        finally:
            conn.close()

    nicknameModifierSubmiter.clicked.connect(
        lambda: on_nicknameModifierSubmiter_clicked(file_hash, nicknameModifier.text())
    )
    # 加入昵称输入组件到区域内
    nicknameAreaLayout.addWidget(nicknameHinter)
    nicknameAreaLayout.addWidget(nicknameModifier)
    nicknameAreaLayout.addWidget(nicknameModifierSubmiter)
    # :右: tagsArea
    tagsArea = QWidget()
    tagsAreaLayout = QHBoxLayout()
    tagsArea.setLayout(tagsAreaLayout)
    # :右: tagsArea组件
    tagsHinter = QLabel("更改标签")
    tagsModifier = QLineEdit()
    tagsModifier.setPlaceholderText("输入新的标签, 以','分割")
    try:
        _tmpConn = sqlite3.connect(DB_PATH)
        _tmpCursor = _tmpConn.cursor()
        _tmpCursor.execute("SELECT * FROM files WHERE hash = ?", (file_hash,))
        _tmpJsonTag = _tmpCursor.fetchone()[3]
        _tmpTagsList = json.loads(_tmpJsonTag)
        if not _tmpTagsList:
            raise
        tagsStr = ""
        for t in _tmpTagsList:
            tagsStr += t
            tagsStr += ","
        tagsStr = tagsStr[:-1]
        print(tagsStr)
        tagsModifier.setText(tagsStr)
    except Exception as e:
        print(f"获取tags遇到错误:\n{e}")
    finally:
        _tmpConn.close()
    tagsModifierSubmiter = QPushButton("提交")

    def on_tagsModifierSubmiter_clicked(file_hash: str, newTags: str):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE hash = ?", (file_hash,))
            oldProperties = cursor.fetchone()
            # oldProperties: (hash,  storageName, nickname, tagsJson)
            cursor.execute("DELETE FROM files WHERE hash = ?", (file_hash,))
            # 去除" "
            if " " in newTags:
                newTags = newTags.replace(" ", "")
            newTagsList = newTags.split(",")
            newTagsJson = json.dumps(newTagsList)
            cursor.execute(
                "INSERT INTO files (hash, storageName, nickname, tags) VALUES (?, ?, ?, ?)",
                (oldProperties[0], oldProperties[1], oldProperties[2], newTagsJson),
            )
            conn.commit()
        except Exception as e:
            print(f"更改标签时遇到问题:\n{e}")
        finally:
            conn.close()

    tagsModifierSubmiter.clicked.connect(
        lambda: on_tagsModifierSubmiter_clicked(file_hash, tagsModifier.text())
    )
    # :tagsArea: 加入组件
    tagsAreaLayout.addWidget(tagsHinter)
    tagsAreaLayout.addWidget(tagsModifier)
    tagsAreaLayout.addWidget(tagsModifierSubmiter)
    # :pathToFileArea:
    pathToFileArea = QWidget()
    pathToFileAreaLayout = QHBoxLayout()
    pathToFileArea.setLayout(pathToFileAreaLayout)
    # 获取路径
    filePath = ""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE hash = ?", (file_hash,))
        _path = cursor.fetchone()[1]
        filePath = os.path.abspath(os.path.join(TARGET_DIR, _path))
    except Exception as e:
        print(f"获取路径失败:\n{e}")
    finally:
        conn.close()
    pathToFileHinter = QLabel("文件路径")
    pathLabel = QLabel(filePath)
    copyPathBtn = QPushButton("复制")
    copyPathBtn.clicked.connect(lambda: pyperclip.copy(filePath))
    # :pathToFileArea: addWidget
    pathToFileAreaLayout.addWidget(pathToFileHinter)
    pathToFileAreaLayout.addWidget(pathLabel)
    pathToFileAreaLayout.addWidget(copyPathBtn)
    # :hashArea:
    hashArea = QWidget()
    hashAreaLayout = QHBoxLayout()
    hashArea.setLayout(hashAreaLayout)
    hashCode = QLabel("哈希代码 " + file_hash)
    copyHashBtn = QPushButton("复制")
    copyHashBtn.clicked.connect(lambda: pyperclip.copy(file_hash))
    hashAreaLayout.addWidget(hashCode)
    hashAreaLayout.addWidget(copyHashBtn)
    # :size:
    sizeArea = QWidget()
    sizeAreaLayout = QHBoxLayout()
    sizeArea.setLayout(sizeAreaLayout)
    pathOfFile = os.path.join(TARGET_DIR, storage_name)

    def convertSize(bytes_size):
        units = ["Byte", "KiB", "MiB", "GiB", "TiB"]
        index = 0
        while bytes_size >= 1024 and index < len(units) - 1:
            bytes_size /= 1024
            index += 1
        return f"{bytes_size:.2f} {units[index]}"

    fileSize = os.path.getsize(pathOfFile)  # unit: bytes
    fileSize = convertSize(fileSize)  # 现在是一个字符串 自带单位
    sizeLabel = QLabel("文件大小 " + fileSize)
    sizeAreaLayout.addWidget(sizeLabel)
    # :functionBtns:
    functionBtnsArea = QWidget()
    functionBtnsAreaLayout = QHBoxLayout()
    functionBtnsArea.setLayout(functionBtnsAreaLayout)
    finishBtn = QPushButton("完成")
    finishBtn.clicked.connect(imgInfoWindow.close)
    deleteBtn = QPushButton("删除")

    def on_deleteBtn_clicked():
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE hash = ?", (file_hash,))
            oldProperties = cursor.fetchone()
            # oldProperties: (hash,  storageName, nickname, tagsJson)
            cursor.execute("DELETE FROM files WHERE hash = ?", (file_hash,))
            filePath = os.path.join(TARGET_DIR, oldProperties[1])
            os.remove(filePath)
            conn.commit()
            imgInfoWindow.close()
        except Exception as e:
            print(f"删除文件时异常:\n{e}")
        finally:
            conn.close()

    deleteBtn.clicked.connect(on_deleteBtn_clicked)
    functionBtnsAreaLayout.addWidget(finishBtn)
    functionBtnsAreaLayout.addWidget(deleteBtn)
    # 加入组件到布局
    imgInfoWindowRightLayout.addWidget(nicknameArea)
    imgInfoWindowRightLayout.addWidget(tagsArea)
    imgInfoWindowRightLayout.addWidget(pathToFileArea)
    imgInfoWindowRightLayout.addWidget(hashArea)
    imgInfoWindowRightLayout.addWidget(sizeArea)
    imgInfoWindowRightLayout.addWidget(functionBtnsArea)
    # :右: 设置布局
    imgInfoWindowRight.setLayout(imgInfoWindowRightLayout)
    # :右: 加入布局
    imgInfoWindowLayout.addWidget(imgInfoWindowRight)
    # show
    imgInfoWindow.setLayout(imgInfoWindowLayout)
    imgInfoWindow.show()
