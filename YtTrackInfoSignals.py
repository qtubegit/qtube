from PyQt5 import QtCore
from YtTrack import YtTrack

class YtTrackInfoSignals(QtCore.QObject):
    threadFinished = QtCore.pyqtSignal()
    trackUpdated = QtCore.pyqtSignal(YtTrack)
    trackError = QtCore.pyqtSignal(str)
    def __init__(self):
        super(QtCore.QObject, self).__init__()
