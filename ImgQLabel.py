from PyQt5 import QtCore
from PyQt5.QtWidgets import QLabel


class ImgQLabel(QLabel):
    clicked = QtCore.pyqtSignal()
    released = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(ImgQLabel, self).__init__(parent)

    def mousePressEvent(self, ev):
        self.clicked.emit()

    def mouseReleaseEvent(self, ev):
        self.released.emit()
