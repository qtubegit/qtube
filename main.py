#!python3
import os
from PyQt5 import QtWidgets
import sys

from YtMainWindow import YtMainWindow

if __name__ == "__main__":
    # When being packaged with PyInstaller, these do not get set to
    # the user's shell environment, but to very basic defaults. So,
    # set them here so we can find youtube-dl / yt-dlp.
    os.environ['PATH'] = f'{os.environ["PATH"]}:/usr/local/bin'
    app = QtWidgets.QApplication(sys.argv)
    win = YtMainWindow()
    win.show()
    sys.exit(app.exec())