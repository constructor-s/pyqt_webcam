"""
Camera GUI classes using OpenCV and PyQt
"""
import sys
import time
import numpy as np
import cv2
from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QWidget, QLabel, QApplication, QSizePolicy, QHBoxLayout


class Camera(QThread):
    """
    See: https://docs.opencv.org/3.4.2/dd/d43/tutorial_py_video_display.html
    """
    def __init__(self, camera_id=0, gui=False):
        """

        :param camera_id:
        :param gui:
        """
        super(Camera, self).__init__()

        self._cap = cv2.VideoCapture(camera_id)

        # Trick to get full _camera resolution with OpenCV: Set a very large resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)

        self._gui = gui
        self.stop_flag = False

        self.frame = np.zeros((int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                               int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                               3), dtype=np.uint8)

    def run(self):
        while not self.stop_flag:
            # Capture frame-by-frame
            ret, frame = self._cap.read()

            if ret:
                self.frame = frame

                if self._gui:
                    pass
                else:
                    cv2.imshow('Preview', frame)
                    key = cv2.waitKey(1)
                    if key == ord('q'):
                        break

        # When everything done, release the capture
        self._cap.release()
        print('Camera released')

    def get(self, *args, **kwargs):
        return self._cap.get(*args, **kwargs)

    def set(self, *args, **kwargs):
        return self._cap.set(*args, **kwargs)


class App(QWidget):
    """
    """

    def __init__(self, camera):
        super(App, self).__init__()

        # Window
        self.setWindowTitle('Camera Feed')
        self.setGeometry(100, 100, 800, 600)

        # create a _label
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self._label.setText('Camera feed initializing or not available')

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
        image = self.numpy2qimage(self._camera.frame)
        pixmap = QPixmap.fromImage(image).scaled(self._label.width(), self._label.height(), Qt.KeepAspectRatio)
        self._label.setPixmap(pixmap)

        self._timer.singleShot(1000 // 30, self.renderPreview)

    @staticmethod
    def numpy2qimage(frame):
        rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        convertToQtFormat = QtGui.QImage(rgbImage.data, w, h, bytesPerLine, QtGui.QImage.Format_RGB888)
        return convertToQtFormat

    def closeEvent(self, a0):
        self._timer.stop()
        self._camera.stop_flag = True
        print('Waiting for _camera to finish...')
        while self._camera.isRunning():
            time.sleep(0.1)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

sys.excepthook = except_hook

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--brightness', default=None, type=float)
    args = parser.parse_args()

    cam = Camera(gui=args.gui)
    if args.brightness is not None:
        print('Setting brightness to', args.brightness)
        cam.set(cv2.CAP_PROP_BRIGHTNESS, args.brightness)

    if not args.gui:
        cam.run()
    else:
        app = QApplication(sys.argv)
        ex = App(cam)
        sys.exit(app.exec_())
