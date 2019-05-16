import time

from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QSizePolicy, QHBoxLayout

from . import opencv2qimage


class Preview(QWidget):
    """
    """

    def __init__(self, camera):
        super(Preview, self).__init__()

        # Window
        self.setWindowTitle('CameraThread Feed')
        self.setGeometry(100, 100, 800, 600)

        # create a _label
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._label.setText('CameraThread feed initializing or not available')

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self._label)
        self.setLayout(layout)

        self.show()

        # Use "singleShot"s to render
        self._timer = QTimer()
        self._timer.singleShot(0, self.renderPreview)

        self._camera = camera
        self._camera.start()

    @pyqtSlot()
    def renderPreview(self):
        image = opencv2qimage(self._camera.frame)
        pixmap = QPixmap.fromImage(image).scaled(self._label.width(), self._label.height(), Qt.KeepAspectRatio)
        self._label.setPixmap(pixmap)

        self._timer.singleShot(1000 // 30, self.renderPreview)

    def closeEvent(self, a0):
        self._timer.stop()
        self._camera.stop_flag = True
        print('Waiting for _camera to finish...')
        while self._camera.isRunning():
            time.sleep(0.1)
