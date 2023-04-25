from PyQt6 import QtCore, QtGui
import pathlib
import urllib, urllib.request
from YtThumbnailCache import YtThumbnailCache

from YtTrack import YtTrack
from YtTrackInfoSignals import YtTrackInfoSignals

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
            self.signals.trackUpdated.emit(self.track)
        except Exception as e:
            # Can happen when the HTTP request returns a 404, for example.
            print(f'Could not retrieve icon:\n{e}')

    def saveThumbnail(self, url) -> QtGui.QIcon():
        if url == None:
            return None
        data = urllib.request.urlopen(url).read()
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(data)
        icon = QtGui.QIcon(pixmap)
        path = pathlib.Path(pathlib.Path.home(), '.qtube/thumbnails', self.track.videoId)
        with open(path, 'wb+') as fp:
            fp.write(data)
        return icon