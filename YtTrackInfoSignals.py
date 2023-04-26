from PyQt6 import QtCore
from YtTrack import YtTrack

class YtTrackInfoSignals(QtCore.QObject):
    trackUpdated = QtCore.pyqtSignal(YtTrack)
    trackError = QtCore.pyqtSignal(str)
    def __init__(self):
        super(QtCore.QObject, self).__init__()
