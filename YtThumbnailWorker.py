from PyQt6 import QtCore, QtGui, QtWidgets
import pathlib
import urllib, urllib.request

from YtSafeSignal import YtSafeSignal
from YtThumbnailCache import YtThumbnailCache
from YtTrackInfoSignals import YtTrackInfoSignals
from YtTrack import YtTrack

class YtThumbnailWorker(QtCore.QRunnable):
    def __init__(self, iconUrl: str, track: YtTrack, signals: YtTrackInfoSignals):
        super().__init__()
        self.iconUrl = iconUrl
        self.track = track
        self.signals = signals

    def run(self):
        try:
            icon = self.saveThumbnail(self.iconUrl)
            YtThumbnailCache.updateThumbnail(self.track.videoId, icon)
            if icon == None:
                return
            YtSafeSignal.emit(self.signals.trackUpdated, self.track)
        except Exception as e:
            # Can happen when the HTTP request returns a 404, for example.
            print(f'Could not retrieve icon "{self.iconUrl}":\n{e}')

    def saveThumbnail(self, url) -> QtGui.QIcon():
        if url == None:
            return None
        data = urllib.request.urlopen(url).read()

        # QPixmap requires a running QApplication. A worker running after application 
        # shutdown can trigger a SIGABORT and cause an unclean exit.
        if QtWidgets.QApplication.instance() == None:
            return
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        icon = QtGui.QIcon(pixmap)
        path = pathlib.Path(pathlib.Path.home(), '.qtube/thumbnails', self.track.videoId)
        with open(path, 'wb+') as fp:
            fp.write(data)
        return icon