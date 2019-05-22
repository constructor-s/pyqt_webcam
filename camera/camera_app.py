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

        self._roi_start = None
        self._roi_end = None
        self.zoomReset()

        self._rotate_count = 0

        self._camera = camera
        self._camera.start()

        self._setupConnections()

        self._timer = QTimer()
        self._timer.singleShot(0, self.renderPreview)

        self.filename = os.path.join(os.path.expanduser('~'), 'image_001.png')
        self._ui.saveButton.setText('Save ' + self.filename)

        self._ui.previewLabel.mousePressEvent = self.labelMousePressEvent
        self._ui.previewLabel.mouseReleaseEvent = self.labelMouseReleaseEvent
        self._ui.previewLabel.mouseMoveEvent = self.labelMouseMoveEvent


    def _setupConnections(self):
        self._ui.rotatePushButton.clicked.connect(self.incrementRotateCount)
        self._ui.saveAsButton.clicked.connect(self.saveImageAs)
        self._ui.saveButton.clicked.connect(self.saveImage)
        self._ui.zoomResetButton.clicked.connect(self.zoomReset)

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

        image = self.drawROIRectange(image, self._roi_start, self._roi_end, (0, 255, 0))

        if not self._zoom_released:
            image = self.drawROIRectange(image, self._zoom_start, self._zoom_end, (0, 0, 255))
        if self._zoom_released and self._zoom_start is not None and self._zoom_end is not None:
            (x1, y1), (x2, y2) = (tuple(round(i) for i in pt) for pt in (self._zoom_start, self._zoom_end))
            if x1 != x2 and y1 != y2:
                self.x1, self.x2 = sorted([x1, x2])
                self.y1, self.y2 = sorted([y1, y2])
        if self.x1 is not None and self.x2 is not None and self.y1 is not None and self.y2 is not None:
            image = image[self.y1:self.y2, self.x1:self.x2]

        return image

    @staticmethod
    def drawROIRectange(image, pt1, pt2, color=(0, 255, 0)):
        if (pt1 is not None and pt2 is not None and
                not np.allclose(pt1, pt2, rtol=0, atol=1)):
            image = image.copy()
            pt1, pt2 = [tuple(round(i) for i in j) for j in (pt1, pt2)]
            cv2.rectangle(image, pt1, pt2, color,
                          thickness=2, lineType=cv2.LINE_AA)

        return image

    def labelMousePressEvent(self, event):
        image_x, image_y = self.getPos(event)
        if self._ui.roiButton.isChecked():
            self._roi_start = (image_x, image_y)
            self._roi_end = None
        elif self._ui.zoomButton.isChecked():
            self._zoom_start = (image_x, image_y)
            self._zoom_end = None
            self._zoom_released = False
        else:
            _logger.error('Invalid selection mode')

    def labelMouseReleaseEvent(self, event):
        image_x, image_y = self.getPos(event)
        if self._ui.roiButton.isChecked():
            self._roi_end = (image_x, image_y)
        elif self._ui.zoomButton.isChecked():
            self._zoom_end = (image_x, image_y)
            self._zoom_released = True
        else:
            _logger.error('Invalid selection mode')

    def labelMouseMoveEvent(self, event):
        image_x, image_y = self.getPos(event)
        if self._ui.roiButton.isChecked():
            self._roi_end = (image_x, image_y)
        elif self._ui.zoomButton.isChecked():
            self._zoom_end = (image_x, image_y)
            self._zoom_released = False
        else:
            _logger.error('Invalid selection mode')

    def getPos(self, event):
        x = event.pos().x()
        y = event.pos().y()
        if self.x1 is None or self.x2 is None or self.y1 is None or self.y2 is None:
            height_in, width_in = self.getImage().shape[:2]
        else:
            height_in, width_in = self.y2 - self.y1, self.x2 - self.x1
        width_out = self._ui.previewLabel.width()
        height_out = self._ui.previewLabel.height()
        scale = min(height_out * 1.0 / height_in, width_out * 1.0 / width_in)
        width_offset = width_out - scale * width_in
        height_offset = height_out - scale * height_in
        image_x = (x - 0.5 * width_offset) * 1.0 / scale
        image_y = (y - 0.5 * height_offset) * 1.0 / scale
        if self.x1 is not None:
            image_x += self.x1
        if self.x2 is not None:
            image_y += self.y1

        _logger.debug('GUI coord: %g,%g; Image coord: %g,%g; Input: %g,%g', x, y,
              image_x,
              image_y,
              width_in, height_in)

        return image_x, image_y

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

    @pyqtSlot(bool)
    def zoomReset(self, checked=False):
        self._zoom_start = None
        self._zoom_end = None
        self._zoom_released = False

        self.x1 = None
        self.x2 = None
        self.y1 = None
        self.y2 = None
        _logger.debug('Zoom variables reset')
