import utils.fileworks as fw
import utils.database as db
import sys
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
splitter.addWidget(imgViewer)
#:filterFrame: 下半边文件筛选器
filterFrame = QWidget()
bottom_layout = QVBoxLayout(filterFrame)
# 分区
horizontal_splitter = QSplitter(Qt.Horizontal)
horizontal_splitter.setChildrenCollapsible(False)
# 左半边
filterLeft = QWidget()
left_layout = QVBoxLayout(filterLeft)
horizontal_splitter.addWidget(filterLeft)
# 右半边
filterRight = QWidget()
right_layout = QVBoxLayout(filterRight)
horizontal_splitter.addWidget(filterRight)
# 把水平分割器添加到 filterFrame 的布局中
bottom_layout.addWidget(horizontal_splitter)
splitter.addWidget(filterFrame)
# 将分割器设置为主窗口的布局
layout = QVBoxLayout(mainwindow)
layout.addWidget(splitter)


def main():
    mainwindow.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    db.initDatabase()
    main()
