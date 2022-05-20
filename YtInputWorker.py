import pynput.keyboard
from PyQt5 import QtCore

class YtInputWorker(QtCore.QObject):
    mediaPlayPause = QtCore.pyqtSignal()
    mediaPrevious = QtCore.pyqtSignal()
    mediaNext = QtCore.pyqtSignal()
    mediaShow = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def playPause(self):
        self.mediaPlayPause.emit()

    def playNext(self):
        self.mediaNext.emit()

    def playPrevious(self):
        self.mediaPrevious.emit()

    def showTrack(self):
        self.mediaShow.emit()

    # FIXME: There were some issue with the YouTube Player grabbing 
    # the media keys. It might be better to just have our own set of
    # global shortcuts.
    def captureKeys(self):
        with pynput.keyboard.GlobalHotKeys({
            '<ctrl>+<shift>+o': self.showTrack,
            '<ctrl>+<shift>+\\': self.playPause,
            '<ctrl>+<shift>+]': self.playNext,
            '<ctrl>+<shift>+[': self.playPrevious}) as thread:
            thread.join()
