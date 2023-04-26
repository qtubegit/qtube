import requests
import urllib

from YtSafeSignal import YtSafeSignal
from YtSearchWorker import YtSearchWorker
from YtTrack import YtTrack

class YtSearchWorkerLastFm(YtSearchWorker):
    def __init__(self, term, apiKey, trackLimit=350, relatedTrack=None):
        super().__init__()
        self.term = term
        self.apiKey = apiKey
        self.seenTracks = []
        self.relatedTrack = relatedTrack
        self.trackLimit = trackLimit

    def search(self):
        if self.relatedTrack != None:
            self.searchSimilar()
        else:
            self.searchTerm()

    def searchSimilar(self):
        artist = self.relatedTrack.artist
        if artist == None:
            artist = self.relatedTrack.title
        artist = urllib.parse.quote(artist)
        track = self.relatedTrack.track
        if track == None:
            track = self.relatedTrack.title
        track = urllib.parse.quote(track)
        url = f'http://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist={artist}&track={track}&api_key={self.apiKey}&limit={self.trackLimit}&format=json'
        # Is this really better? Instead of dealing with array indices, we now
        # need to call "hasattr" to check for existence of a field. We might be
        # wasting CPU time without benefit to code cleanliness.
        response = requests.get(url)
        parsed = response.json()
        if 'similartracks' not in parsed:
            return
        ytTracks = []
        for t in parsed['similartracks']['track']:
            duration = t['duration'] if 'duration' in t else None
            artist = t['artist']['name']
            track = t['name']
            ytTrack = YtTrack(f'{artist} - {track}', artist=artist, track=track, duration=duration)
            ytTracks.append(ytTrack)
        YtSafeSignal.emit(self.tracksFound, ytTracks)

    def searchTerm(self):
        page = 0
        while True:
            page = page + 1
            term = urllib.parse.quote(self.term)
            url = f'http://ws.audioscrobbler.com/2.0/?method=album.search&page={page}&album={term}&api_key={self.apiKey}&format=json'
            response = requests.get(url).json()
            try:
                albums = response['results']['albummatches']['album']
            except KeyError:
                return
            if len(albums) == 0:
                break
            for album in albums:
                artistName = album['artist']
                albumName = album['name']
                self.searchAlbumTracks(artistName, albumName)
                self.searchArtistTracks(artistName)
                if len(self.seenTracks) > self.trackLimit:
                    return

    def searchAlbumTracks(self, artist: str, album: str):
        q_artist = urllib.parse.quote(artist)
        q_album = urllib.parse.quote(album)
        url = f'http://ws.audioscrobbler.com/2.0/?method=album.getinfo&api_key={self.apiKey}&artist={q_artist}&album={q_album}&format=json'
        try: response = requests.get(url).json()
        except: return
        try: tracks = response['album']['tracks']['track']
        except KeyError: return
        artist = response['album']['artist']
        ytTracks = []
        for t in tracks:
            if type(t) == str:
                continue
            try:
                track = t['name']
            except KeyError:
                continue
            title = f'{artist} - {album} - {track}'
            ytTrack = YtTrack(title, artist=artist, album=album, track=track)
            if ytTrack.title not in self.seenTracks:
                self.seenTracks.append(ytTrack.title)
                if len(self.seenTracks) > self.trackLimit:
                    ytTracks.append(ytTrack)
                    break
        YtSafeSignal.emit(self.tracksFound, ytTracks)
            
    def searchArtistTracks(self, artist: str):
        artist = urllib.parse.quote(artist)
        url = f'http://ws.audioscrobbler.com/2.0/?method=artist.getTopTracks&artist={artist}&api_key={self.apiKey}&format=json'
        try:
            response = requests.get(url).json()
        except:
            return
        try:
            tracks = response['toptracks']['track']
        except KeyError:
            return
        ytTracks = []
        for t in tracks:
            try:
                track = t['name']
                artist = t['artist']['name']
            except KeyError:
                continue
            if 'album' in t:
                album = t['album']                
                title = f'{artist} - {album} - {track}'
                ytTrack = YtTrack(title, artist=artist, album=album, track=track)
            else:
                title = f'{artist} - {track}'
                ytTrack = YtTrack(title, artist=artist, track=track)

            if ytTrack.title not in self.seenTracks:
                self.seenTracks.append(ytTrack.title)
                ytTracks.append(ytTrack)
                if len(self.seenTracks) > self.trackLimit:
                    break

        YtSafeSignal.emit(self.tracksFound, ytTracks)


