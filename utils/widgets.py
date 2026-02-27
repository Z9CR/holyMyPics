import os
from PIL import Image, ImageQt
from PySide6.QtWidgets import QLabel, QWidget, QGridLayout
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap
from typing import List, Callable

THUMBNAIL_SIZE = 128


class ImageLabel(QLabel):
    """可点击的图片标签"""

    def __init__(self, file_hash: str, nickname: str, storage_name: str, parent=None):
        super().__init__(parent)
        self.file_hash = file_hash
        self.nickname = nickname
        self.storage_name = storage_name
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                background-color: white;
            }
            QLabel:hover {
                border: 2px solid #2ecc71;
            }
        """)

    def load_image(self, image_path: str) -> bool:
        """加载图片到标签"""
        if not os.path.exists(image_path):
            print(f"图片不存在: {image_path}")
            return False

        try:
            # 使用 Pillow 打开图片
            pil_image = Image.open(image_path)
            # 计算缩略图尺寸（保持宽高比）
            pil_image.thumbnail(
                (THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS
            )
            # 转换为 QPixmap
            qimage = ImageQt.ImageQt(pil_image)
            pixmap = QPixmap.fromImage(qimage)
            self.setPixmap(pixmap)
            return True
        except Exception as e:
            print(f"加载图片失败 {image_path}: {e}")
            return False

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 发出信号，但这里我们通过回调函数处理
            from utils.slots import on_image_clicked

            on_image_clicked(self.file_hash, self.nickname, self.storage_name)
        super().mousePressEvent(event)


class ImageViewer(QWidget):
    """图片查看器，使用网格布局自动换行"""

    def __init__(self, target_dir: str, parent=None):
        super().__init__(parent)
        self.target_dir = target_dir
        self.image_labels = []  # 保存所有图片标签
        self.cols = 3
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(self.grid_layout)

    def add_image(self, file_hash: str, storage_name: str, nickname: str) -> bool:
        """添加图片到预览区"""
        image_path = os.path.join(self.target_dir, storage_name)

        # 创建图片标签
        label = ImageLabel(file_hash, nickname, storage_name)

        # 加载图片
        if not label.load_image(image_path):
            label.deleteLater()
            return False

        self.image_labels.append(label)
        self._relayout()
        return True

    def add_images_from_list(self, image_list: List[tuple]):
        """批量添加图片，image_list 元素为 (storage_name, file_hash, nickname)"""
        self.clear_images()
        for storage_name, file_hash, nickname in image_list:
            self.add_image(storage_name, file_hash, nickname)

    def clear_images(self):
        """清空所有图片"""
        for label in self.image_labels:
            label.deleteLater()
        self.image_labels.clear()
        self._relayout()

    def _relayout(self):
        """重新计算布局"""
        # 清除现有布局中的所有项
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        if not self.image_labels:
            return
        # 计算列数
        viewport_width = self.width()
        if viewport_width <= 0:
            viewport_width = 600
        item_width = THUMBNAIL_SIZE + self.grid_layout.spacing()
        self.cols = max(1, viewport_width // item_width)
        # 重新添加标签到网格
        for i, label in enumerate(self.image_labels):
            row = i // self.cols
            col = i % self.cols
            self.grid_layout.addWidget(label, row, col)
        # 设置拉伸因子
        if self.image_labels:
            last_row = (len(self.image_labels) - 1) // self.cols
            self.grid_layout.setRowStretch(last_row, 0)
            self.grid_layout.setRowStretch(last_row + 1, 1)

    def resizeEvent(self, event):
        """窗口大小改变时重新布局"""
        super().resizeEvent(event)
        self._relayout()

    def count(self) -> int:
        """返回当前显示的图片数量"""
        return len(self.image_labels)
