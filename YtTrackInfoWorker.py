from PyQt5 import QtCore
import json
import shlex

from YtShell import YtShell
from YtThumbnailWorker import YtThumbnailWorker
from YtTrackInfoSignals import YtTrackInfoSignals

class YtTrackInfoWorker(QtCore.QRunnable):
    def __init__(self, track, refreshTitle = False, refreshThumbnail = False):
        super(QtCore.QRunnable, self).__init__()
        self.track = track
        self.signals = YtTrackInfoSignals()
        self.threadFinished = self.signals.threadFinished
        self.trackUpdated = self.signals.trackUpdated
        self.trackError = self.signals.trackError
        self.refreshTitle = refreshTitle
        self.refreshThumbnail = refreshThumbnail

    def run(self):
        errors = None
        try:
            if self.track.videoId:
                cmd = f'youtube-dl -j -- {shlex.quote(self.track.videoId)}'
                results, errors = YtShell.pipeOutput(cmd)                
            else:
                cmd = f'youtube-dl -j -- ytsearch1:{shlex.quote(self.track.title)}'
                results, errors = YtShell.pipeOutput(cmd)
            results = results.strip()
            jvid = json.loads(results)
            duration = int(jvid['duration'])
            self.track.duration = int(duration)
            self.track.videoId = jvid['id']
            self.track.channel = jvid['uploader']
            
            if self.refreshTitle:
                self.track.title = jvid['title']

            if self.refreshThumbnail:
                # Assume the last icon in the list is the high quality one. This seems to be
                # reliable currently, but a better method would go through the resolution 
                # information that is present in the JSON for each thumbnail and sort them.
                iconUrl = jvid['thumbnails'][-1]['url']
            else:
                # Retrieve low quality icons unless we are doing an explicit refresh.
                # This will cause first plays of a track to be faster.
                iconUrl = jvid['thumbnails'][0]['url']

            self.trackUpdated.emit(self.track)
            if self.refreshThumbnail or self.track.icon == None:
                worker = YtThumbnailWorker(iconUrl, self.track, self.signals)
                threadPool = QtCore.QThreadPool.globalInstance()
                threadPool.start(worker)

        except Exception as e:
            # Some of the immediate exceptions here are issues parsing the JSON returned above.
            # But this can have different causes. For example, when the channel of a video has
            # been deleted, youtube-dl will not return any JSON. Instead of passing on the exception
            # from the JSON parser, which is not very informative, pass on the error message from 
            # youtube-dl, which contains error messages more useful to the user. If we did not get
            # any error information from youtube-dl, pass on the error message from the exception, 
            # which might be more less inelligible, but better than nothing.
            if errors == None:
                errors = f'There was a problem retrieving track information:\n{e}'
            self.trackError.emit(errors)
        finally: 
            self.threadFinished.emit()
