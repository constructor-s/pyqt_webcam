import re

import cv2
import os

from PyQt5.QtCore import pyqtSlot, QTimer, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget

from . import opencv2qimage, camera_gui

import logging
_logger = logging.getLogger(__name__)

class CameraApp(QWidget):
    def __init__(self, camera, *args, **kwargs):
        """

        :type camera: camera.camera_thread.CameraThread
        :param camera:
        :param args:
        :param kwargs:
        """
        super(CameraApp, self).__init__(*args, **kwargs)

        self._ui = camera_gui.Ui_Camera()
        self._ui.setupUi(self)
        self.show()

        self._camera = camera
        self._camera.start()

        self._setupConnections()

        self._timer = QTimer()
        self._timer.singleShot(0, self.renderPreview)

        self.filename = os.path.join(os.path.expanduser('~'), 'image_001.png')
        self._ui.saveButton.setText('Save ' + self.filename)

    def _setupConnections(self):
        self._ui.saveAsButton.clicked.connect(self.saveImageAs)
        self._ui.saveButton.clicked.connect(self.saveImage)

        self._ui.brightnessSlider.setValue(self._camera.get(cv2.CAP_PROP_BRIGHTNESS))
        self._ui.brightnessSlider.valueChanged.connect(self._camera.setBrightness)

        self._ui.contrastSlider.setValue(self._camera.get(cv2.CAP_PROP_CONTRAST))
        self._ui.contrastSlider.valueChanged.connect(self._camera.setContrast)

        print(self._camera.get(cv2.CAP_PROP_GAIN))
        self._ui.gainSlider.setValue(self._camera.get(cv2.CAP_PROP_GAIN))
        self._ui.gainSlider.valueChanged.connect(self._camera.setGain)

    @pyqtSlot()
    def renderPreview(self):
        image = opencv2qimage(self._camera.frame)
        pixmap = QPixmap.fromImage(image).scaled(self._ui.previewLabel.width(), self._ui.previewLabel.height(), Qt.KeepAspectRatio)
        self._ui.previewLabel.setPixmap(pixmap)

        self._timer.singleShot(1000 // 30, self.renderPreview)

    @pyqtSlot(bool)
    def saveImageAs(self, checked):
        _logger.info('saveImageAs:')


    @pyqtSlot(bool)
    def saveImage(self, checked):
        _logger.info('saveImage:')
        cv2.imwrite(self.filename, self._camera.frame)
        self.incrementFilename()

    def incrementFilename(self):
        match_list = tuple(re.finditer(r'(\d+)', self.filename))
        if match_list:
            # Get last match of digits
            match = match_list[-1]
            index = int(self.filename[slice(*match.span())])
            index += 1
            index = str(index)
            index = index.zfill(match.span()[1] - match.span()[0])
            self.filename = self.filename[:match.span()[0]] + index + self.filename[match.span()[1]:]
        else:
            file, ext = os.path.splitext(self.filename)
            self.filename = file + '_001' + ext
        self._ui.saveButton.setText('Save ' + self.filename)
