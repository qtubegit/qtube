import html
import requests

from YtSafeSignal import YtSafeSignal
from YtSearchWorker import YtSearchWorker
from YtTrack import YtTrack

class YtSearchWorkerGoogle(YtSearchWorker):
    def __init__(self, apiKeys, query, trackLimit=350):
        super().__init__()
        self.apiKeys = apiKeys
        self.query = query
        self.trackLimit = trackLimit
        self.currentKey = 0

    def _makeParams(self, query):
        params = {
            'maxResults': self.trackLimit,
            # We could get more details than just "snippet" but, from 
            # what I understand, this will also cost more quota points.
            # This part type will not give us video durations, but those
            # will be later retrieved when tracks are being played. Also,
            # it would require another roundtrip for each track returned
            # by the initial query, which would slow down searches.
            'part': 'snippet',
            'type': 'video',
            'q': query
        }
        return params

    def _makeRequest(self, url, params):
        keyCount = len(self.apiKeys)
        for _ in range(keyCount):
            key = self.apiKeys[self.currentKey]
            params['key'] = key
            response = requests.get(url, params)
            parsed = response.json()
            if 'error' in parsed:
                self.currentKey = (self.currentKey + 1) % keyCount
            else:
                return parsed
        return None

    def search(self):
        url = "https://www.googleapis.com/youtube/v3/search"
        params = self._makeParams(self.query)
        results = self._makeRequest(url, params)
        tracks = []
        for item in results['items']:
            tags = {
                'videoId': item['id']['videoId'],
                'iconUrl': item['snippet']['thumbnails']['default']['url'],
                'channel': item['snippet']['channelTitle'],
            }
            title = html.unescape(item['snippet']['title'])
            track = YtTrack(title, **tags)
            tracks.append(track)

        YtSafeSignal.emit(self.tracksFound, tracks)

