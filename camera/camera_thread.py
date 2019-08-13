import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSlot


class CameraThread(QThread):
    """
    See: https://docs.opencv.org/3.4.2/dd/d43/tutorial_py_video_display.html
    """
    def __init__(self, camera_id=0, gui=False, parent=None):
        """

        :param camera_id:
        :param gui:
        """
        super(CameraThread, self).__init__(parent=parent)

        self._cap = cv2.VideoCapture(camera_id)

        # Trick to get full _camera resolution with OpenCV: Set a very large resolution
        self._cap.set(cv2.CAP_PROP_FPS, 0)
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
        print('CameraThread released')

    def get(self, *args, **kwargs):
        return self._cap.get(*args, **kwargs)

    def set(self, *args, **kwargs):
        return self._cap.set(*args, **kwargs)

    @pyqtSlot(int)
    def setBrightness(self, value):
        self._cap.set(cv2.CAP_PROP_BRIGHTNESS, value)

    @pyqtSlot(int)
    def setContrast(self, value):
        self._cap.set(cv2.CAP_PROP_CONTRAST, value)

    @pyqtSlot(int)
    def setGain(self, value):
        self._cap.set(cv2.CAP_PROP_GAIN, value)
