import utils.fileworks as fw
import utils.database as db
import sys
import utils.slots as slots
import sqlite3
from PIL import Image, ImageQt
from utils.widgets import *
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QScrollArea,
)
from PySide6.QtCore import Qt

DB_PATH = "pics.db"
TARGET_DIR = "pics"
# 图像显示
app = QApplication(sys.argv)
mainwindow = QWidget()
mainwindow.setWindowTitle("HolyMyPics")  # 设置窗口标题
mainwindow.resize(800, 600)  # 设置窗口大小800x600
splitter = QSplitter(Qt.Vertical)  # Qt.Vertical 表示垂直分割
splitter.setChildrenCollapsible(False)  # 防止子窗口被折叠到看不见
#:imgViewer: 上半边文件预览器
imgViewer = QWidget()
top_layout = QVBoxLayout(imgViewer)
# 创建滚动区域
scroll_area = QScrollArea()
scroll_area.setWidgetResizable(True)
scroll_area.setAlignment(Qt.AlignCenter)
# 创建 ImageViewer 作为容器
container = ImageViewer(TARGET_DIR)
scroll_area.setWidget(container)
top_layout.addWidget(scroll_area)
#:imgViewer:加入布局
splitter.addWidget(imgViewer)
#:filterFrame: 下半边文件筛选器
filterFrame = QWidget()
bottom_layout = QVBoxLayout(filterFrame)
# :filterFrame:分区
horizontal_splitter = QSplitter(Qt.Horizontal)
horizontal_splitter.setChildrenCollapsible(False)
# :filterFrame:左半边
filterLeft = QWidget()
left_layout = QVBoxLayout(filterLeft)
# 标签输入行（水平布局）
tag_input_layout = QHBoxLayout()
# 标签输入框
tag_input = QLineEdit()
tag_input.setPlaceholderText("输入标签")
tag_input_layout.addWidget(tag_input)
# 添加标签按钮
add_tag_btn = QPushButton("添加")
add_tag_btn.clicked.connect(  # 连接槽函数
    lambda: slots.on_add_tag_clicked(tag_input, tag_list_widget)
)
tag_input_layout.addWidget(add_tag_btn)
# 移除最后一个标签按钮
remove_tag_btn = QPushButton("移除最后")
remove_tag_btn.clicked.connect(lambda: slots.on_remove_tag_clicked(tag_list_widget))
tag_input_layout.addWidget(remove_tag_btn)
# tag输入模块完成
left_layout.addLayout(tag_input_layout)
# 标签显示区域
left_layout.addWidget(QLabel("已添加的标签:"))
# 用于显示已添加标签的列表
tag_list_widget = QListWidget()
tag_list_widget.setMaximumHeight(150)  # 限制高度，避免占用太多空间
left_layout.addWidget(tag_list_widget)
# 添加弹性空间，让组件靠上排列
left_layout.addStretch()
# 左半边子组件加入布局
horizontal_splitter.addWidget(filterLeft)
# :filterFrame:右半边
filterRight = QWidget()
right_layout = QVBoxLayout(filterRight)
# 按昵称搜索
nickname_input = QLineEdit()
nickname_input.setPlaceholderText("输入昵称...")
right_layout.addWidget(nickname_input)
# 搜索按钮
search_btn = QPushButton("搜索")


# 迫于跨包，在main.py里实现按钮的搜索逻辑
def _on_search():
    hashs = slots.on_search_clicked(tag_list_widget, nickname_input, result_label)
    # 清空当前预览
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


# 连接槽函数
search_btn.clicked.connect(lambda: _on_search())
right_layout.addWidget(search_btn)
# 显示找到的文件数量的标签
result_label = QLabel("找到 0 个文件")
result_label.setStyleSheet("font-weight: bold; color: #2ecc71;")  # 可选样式
right_layout.addWidget(result_label)
# 添加弹性空间，让组件靠上排列
right_layout.addStretch()
# 子组件加入布局
horizontal_splitter.addWidget(filterRight)
# 把水平分割器添加到 filterFrame 的布局中
bottom_layout.addWidget(horizontal_splitter)
splitter.addWidget(filterFrame)
# 将分割器设置为主窗口的布局
layout = QVBoxLayout(mainwindow)
layout.addWidget(splitter)
# 设置分割器布局
splitter.setSizes([480, 320])  # 上半500px，下半150px


def main():
    mainwindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    db.initDatabase()
    main()
