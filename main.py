#!/home/mujin/.pyenv/versions/3.12.4/envs/selenium-test/bin/python 
import os
from PyQt6 import QtGui, QtWidgets
import sys

from YtMainWindow import YtMainWindow

if __name__ == "__main__":
    mainPath = os.path.dirname(os.path.realpath(__file__))
    os.chdir(mainPath)

    # When being packaged with PyInstaller, these do not get set to
    # the user's shell environment, but to very basic defaults. So,
    # set them here so we can find youtube-dl / yt-dlp.
    os.environ['PATH'] = f'{os.environ["PATH"]}:/usr/local/bin'
    app = QtWidgets.QApplication(sys.argv)
    icon = QtGui.QIcon('icon.ico')
    app.setWindowIcon(icon)
    win = YtMainWindow()
    win.show()
    sys.exit(app.exec())
