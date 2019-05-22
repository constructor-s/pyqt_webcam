"""
CameraThread GUI classes using OpenCV and PyQt
"""
import argparse
import cv2
import logging
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox, QInputDialog

from camera.camera_app import CameraApp
from camera.camera_thread import CameraThread
from camera.preview import Preview

_logger = logging.getLogger(__name__)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--gui', action='store_true', help='Use GUI to display preview')
    parser.add_argument('--qt', action='store_true', help='Use full Qt GUI; must be used with --gui')
    parser.add_argument('-v', '--verbose', action='store_true', help='Increase output verbosity')
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if not args.gui:
        cam = CameraThread(gui=args.gui)
        cam.run()
    else:
        app = QApplication(sys.argv)

        devices = []
        for i in range(10):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                devices.append(i)
            cap.release()

        if len(devices) == 0:
            _logger.error('No camera device available')
            QMessageBox.critical(None, 'No camera', 'No camera device available')
            sys.exit()
        elif len(devices) == 1:
            device_id = devices[0]
        else:
            item, ok = QInputDialog.getItem(None, 'Select camera', 'Choose a camera:', [str(i) for i in devices], 0, False)
            if not ok:
                _logger.warning('Operation cancelled by user')
                sys.exit()
            else:
                device_id = int(item)

        cam = CameraThread(camera_id=device_id, gui=args.gui, parent=app)
        if not args.qt:
            widget = Preview(cam)
        else:
            widget = CameraApp(cam)
            widget.show()
        sys.exit(app.exec_())
