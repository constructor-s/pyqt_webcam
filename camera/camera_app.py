from . import opencv2qimage, camera_gui

from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer, Qt

import cv2
import numpy as np

import re
import os
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

        self._clicks = []
        self._rotate_count = 0

        self._camera = camera
        self._camera.start()

        self._setupConnections()

        self._timer = QTimer()
        self._timer.singleShot(0, self.renderPreview)

        self.filename = os.path.join(os.path.expanduser('~'), 'image_001.png')
        self._ui.saveButton.setText('Save ' + self.filename)

        self._ui.previewLabel.mousePressEvent = self.getPos


    def _setupConnections(self):
        self._ui.rotatePushButton.clicked.connect(self.incrementRotateCount)
        self._ui.saveAsButton.clicked.connect(self.saveImageAs)
        self._ui.saveButton.clicked.connect(self.saveImage)

        self._ui.brightnessSlider.setValue(self._camera.get(cv2.CAP_PROP_BRIGHTNESS))
        self._ui.brightnessSlider.valueChanged.connect(self._camera.setBrightness)

        self._ui.contrastSlider.setValue(self._camera.get(cv2.CAP_PROP_CONTRAST))
        self._ui.contrastSlider.valueChanged.connect(self._camera.setContrast)

        self._ui.gainSlider.setValue(self._camera.get(cv2.CAP_PROP_GAIN))
        self._ui.gainSlider.valueChanged.connect(self._camera.setGain)

    def getImage(self):
        image = self._camera.frame

        for _ in range(self._rotate_count % 4):
            image = np.rot90(image)
        if self._isFlipud():
            image = np.flipud(image)
        if self._isFliplr():
            image = np.fliplr(image)

        if len(self._clicks) >= 2 and len(self._clicks) % 2 == 0:
            pt1, pt2 = (tuple(round(i) for i in pt) for pt in self._clicks[-2:])
            image = image.copy()
            cv2.rectangle(image, pt1, pt2, (0, 255, 0),
                          thickness=image.shape[0] // 100, lineType=cv2.LINE_AA)
        return image

    def getPos(self, event):
        x = event.pos().x()
        y = event.pos().y()
        print(self.getImage().shape)
        height_in, width_in = self.getImage().shape[:2]
        width_out = self._ui.previewLabel.width()
        height_out = self._ui.previewLabel.height()
        scale = min(height_out * 1.0 / height_in, width_out * 1.0 / width_in)
        width_offset = width_out - scale * width_in
        height_offset = height_out - scale * height_in
        image_x = (x - 0.5 * width_offset) * 1.0 / scale
        image_y = (y - 0.5 * height_offset) * 1.0 / scale

        _logger.debug('GUI coord: %g,%g; Image coord: %g,%g; Input: %g,%g', x, y,
              image_x,
              image_y,
              width_in, height_in)
        self._clicks.append((image_x, image_y))

    @pyqtSlot()
    def renderPreview(self):
        image = self.getImage()
        image = opencv2qimage(image)
        pixmap = QPixmap.fromImage(image).scaled(self._ui.previewLabel.width(), self._ui.previewLabel.height(), Qt.KeepAspectRatio)
        self._ui.previewLabel.setPixmap(pixmap)

        self._timer.singleShot(1000 // 30, self.renderPreview)

    @pyqtSlot(bool)
    def saveImageAs(self, checked=False):
        _logger.info('saveImageAs:')
        filename, _ = QFileDialog.getSaveFileName(
            parent=self, caption='Save As', directory=self.filename,
            filter="Images (*.bmp *.jpg *.jpeg *.png);;All files (*.*)"
        )
        if filename:
            self.filename = filename
            self.saveImage()
        else:
            QMessageBox.warning(self, 'Invalid File', 'The file chosen (%s) is invalid.' % filename)

    @pyqtSlot(bool)
    def saveImage(self, checked=False):
        _logger.info('saveImage:')
        cv2.imwrite(self.filename, self.getImage())
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

    def _isFlipud(self):
        return self._ui.flipUDCheckBox.isChecked()

    def _isFliplr(self):
        return self._ui.flipLRCheckBox.isChecked()

    @pyqtSlot(bool)
    def incrementRotateCount(self, checked=False):
        self._rotate_count += 1
