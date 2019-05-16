"""
CameraThread GUI classes using OpenCV and PyQt
"""
import sys

import cv2
from PyQt5.QtWidgets import QApplication

from camera.camera_app import CameraApp
from camera.camera_thread import CameraThread
from camera.preview import Preview


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


sys.excepthook = except_hook


if __name__ == '__main__':
    import argparse
    import logging
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--gui', action='store_true')
    parser.add_argument('--qt', action='store_true')
    parser.add_argument('--brightness', default=None, type=float)
    args = parser.parse_args()

    cam = CameraThread(gui=args.gui)
    if args.brightness is not None:
        print('Setting brightness to', args.brightness)
        cam.set(cv2.CAP_PROP_BRIGHTNESS, args.brightness)

    if not args.gui:
        cam.run()
    else:
        app = QApplication(sys.argv)
        if not args.qt:
            widget = Preview(cam)
        else:
            widget = CameraApp(cam)
            widget.show()
        sys.exit(app.exec_())
