import json
import os

from YtShell import YtShell
from YtPlaylistManager import YtTrack
from YtSearchWorker import YtSearchWorker

class YtSearchWorkerYtdl(YtSearchWorker):
    def __init__(self, term):
        super().__init__()
        self.term = term

    def search(self):
        errors = None
        try:
            results, errors = YtShell.pipeOutput(f'youtube-dl -j -f "mp4" "ytsearch10:{self.term}"')
            results = results.strip()
            results = results.split('\n')
            for r in results:
                jvid = json.loads(r)
                title = jvid['fulltitle']
                videoId = jvid['id']
                channel = jvid['uploader']
                duration = jvid['duration']
                track = YtTrack(title, url=videoId, duration=duration, channel=channel)
                self.tracksFound.emit([track]) 
        except Exception as e:
            if errors != None:
                e = Exception(errors)
            raise(e)