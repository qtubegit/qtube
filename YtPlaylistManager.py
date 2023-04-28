import json
import numpy
import pathlib
from PyQt6 import QtCore
import enum

from YtPlaylist import YtPlaylist
from YtTrack import YtTrack

class YtPlayMode(enum.Enum):
    Normal = 'N'
    Shuffle = 'S'
    Loop = 'L'

class YtPlaylistManager(QtCore.QObject):
    """
    Responsible for all changes to playlist and track data. Any components
    that depend on being up-to-date on that data are to be notified through
    these signals. This reduces the need for there to be a central component 
    that coordinates updates to different components that rely on this data.
    For example, there are currently components for displaying playlists, to
    view tracks, or to show album art. 
    """
    playlistRemoved = QtCore.pyqtSignal(YtPlaylist)
    playlistCreated = QtCore.pyqtSignal(YtPlaylist)
    playlistCleared = QtCore.pyqtSignal(YtPlaylist)
    trackActivated = QtCore.pyqtSignal(YtTrack)
    trackUpdated = QtCore.pyqtSignal(YtTrack)
    tracksAdded = QtCore.pyqtSignal(YtPlaylist, list)
    tracksRemoved = QtCore.pyqtSignal(YtPlaylist, list)

    def __init__(self):
        super().__init__()
        self.activePlaylist = None
        self.activeTrack = None
        self.playlists = []
        self.playMode = YtPlayMode.Normal
        self.isDirty = False
        self.configPath = pathlib.Path(pathlib.Path.home(), '.qtube')
        self.currentTrackPath = pathlib.Path(self.configPath,  'currentTrack.json')
        self.playlistPath = pathlib.Path(self.configPath,  'playlists.json')
        self.thumbnailPath = pathlib.Path(self.configPath, 'thumbnails')
        self.thumbnailPath.mkdir(parents=True, exist_ok=True)
        self.iconCache = {}
        self.loadPlaylists()

    def updateTrack(self, track):
        self.trackUpdated.emit(track)
        self.setDirty()
        
    def setPlayMode(self, playMode: YtPlayMode):
        self.playMode = playMode

    def setDirty(self):
        self.isDirty = True
        
    def getActiveTrack(self) -> YtTrack:
        return self.activeTrack
    
    def clearPlaylist(self, plName: str):
        playlist = self.playlistByName(plName)
        if playlist == None:
            return
        if self.activeTrack and self.activeTrack.playlist == playlist:
            self.activeTrack.playlist = None
        playlist.tracks = []
        self.playlistCleared.emit(playlist)
        self.isDirty = True

    def removePlaylist(self, name: str):
        tmp = YtPlaylist(name)
        if tmp not in self.playlists:
            return
        index = self.playlists.index(tmp)
        pl = self.playlists[index]
        del(self.playlists[index])
        self.playlistRemoved.emit(pl)
        self.isDirty = True

    def setPlaylists(self, playlists: list):
        self.playlists = playlists

    def loadPlaylists(self):
        pl = {}
        try:
            with open(self.playlistPath, 'r+') as fp:
                pl = json.load(fp)
        except FileNotFoundError:
            return
        except Exception as e:
            print(f'Could not load playlists: {e}')
            print(f'As a safeguard, I am refusing to start. Fix or delete your playlist.')
            quit()

        self.playlists = []
        for name in pl:
            playlist = YtPlaylist(name)
            for track in pl[name]:
                # Avoid passing title multiple times.
                tags = {tag: track[tag] for tag in track if tag != 'title'}
                ytTrack = YtTrack(track['title'], playlist, **tags)
                playlist.tracks.append(ytTrack)
            self.playlists.append(playlist)

    def savePlaylists(self):
        playlists = { pl.name: [t.getTags() for t in pl] for pl in self.playlists }
        serialized = json.dumps(playlists)
        with open(self.playlistPath, 'w+') as fp:
            fp.write(serialized)
        self.isDirty = False

    # This must be called every time a track's index in a playlist changes,
    # because the current track is identified by playlist name and index.
    def savePlayingTrack(self):
        '''Saves the currently playing track.'''
        fd = open(self.currentTrackPath, 'w+')
        if self.activeTrack == None:
            fd.truncate()
            fd.close()
            return
        playlistName = None
        trackIndex = None
        playlist = self.activeTrack.playlist
        if playlist != None:
            playlistName = playlist.name
            trackIndex = playlist.trackIndex(self.activeTrack)
        playingTrack = {
            'playlist': playlistName,
            'trackIndex': trackIndex,
            'tags': self.activeTrack.getTags()
        }
        serialized = json.dumps(playingTrack)
        fd.write(serialized)
        fd.close()

    def loadPlayingTrack(self) -> YtTrack:
        '''Returns the last track that was playing when the player was last running.'''
        try:
            with open(self.currentTrackPath, 'r+') as fp:
                savedTrack = json.load(fp)
        except json.decoder.JSONDecodeError:
            return None
        except FileNotFoundError:
            return None

        playlistName = savedTrack['playlist']
        if playlistName == None:
            tags = savedTrack['tags']
            track = YtTrack(tags['title'])
            track._tags = tags
            return track
        playlist = self.getPlaylist(playlistName)
        return playlist[savedTrack['trackIndex']]

    def getPlaylists(self) -> list:
        return self.playlists

    def getPlaylist(self, name: str) -> YtPlaylist:
        for pl in self.playlists:
            if pl.name == name:
                return pl
        return None

    def createPlaylist(self, plName: str) -> YtPlaylist:
        for playlist in self.playlists:
            if playlist.name == plName:
                return None
        playlist = YtPlaylist(plName)
        self.playlists.append(playlist)
        self.playlistCreated.emit(playlist)
        self.isDirty = True
        return playlist

    def playlistByName(self, plName: str) -> YtPlaylist:
        for pl in self.playlists:
            if pl.name == plName:
                return pl
        return None

    def addTracks(self, plName: str, tracks: list):
        playlist = self.playlistByName(plName)
        if playlist == None:
            playlist = self.createPlaylist(plName)
        playlist.tracks.extend(tracks)
        for track in tracks:
            track.playlist = playlist
        self.tracksAdded.emit(playlist, tracks)
        self.isDirty = True
        self.savePlayingTrack()

    def removeTracks(self, playlist: YtPlaylist, tracks: list):
        if playlist == None:
            return
        saveTrack = (self.activeTrack != None and 
                     playlist == self.activeTrack.playlist)
        for track in tracks:
            if self.activeTrack == track:
                self.activeTrack.playlist = None
            track.playlist = None
            del(playlist[track])
        self.tracksRemoved.emit(playlist, tracks)
        self.isDirty = True
        if saveTrack:
            self.savePlayingTrack()

    def activateTrack(self, track: YtTrack):
        self.activeTrack = track
        self.trackActivated.emit(track)
        self.addTracks('# History', [track.makeCopy()])
        self.savePlayingTrack()

    def activateNextTrack(self, loopOther: bool = False):
        self.jumpPlaylistBy(1, loopOther)

    def activatePreviousTrack(self, loopOther: bool = False):
        self.jumpPlaylistBy(-1, loopOther)

    def jumpPlaylistBy(self, direction: int, loopOther: bool = False):
        """
        loopNext: whether to keep looping but still switching tracks.
        """
        if self.activeTrack == None:
            return None
        if self.activeTrack.playlist == None:
            return None
        playlist = self.activeTrack.playlist
        trackIndex = playlist.trackIndex(self.activeTrack)
        
        if self.playMode == YtPlayMode.Shuffle:
            index = numpy.random.choice([
                i for i in range(len(playlist.tracks)) 
                if i != trackIndex])
            nextTrack = playlist[index]
        # Skip to the next track even in loop mode if manually invoked.
        elif self.playMode == YtPlayMode.Normal or loopOther:
            nextTrack = playlist[trackIndex + direction]
        elif self.playMode == YtPlayMode.Loop:
            self.activeTrack.position = 0
            nextTrack = self.activeTrack

        self.activateTrack(nextTrack)

    def removeDuplicates(self, playlist: YtPlaylist, tracks: list):
        # Be careful which tracks to view as duplicates. Two tracks might
        # have the same titles, but if one has a video ID and was renamed
        # after resolving to a video ID, then another track with the same
        # title might still end up being a different track. But don't put
        # titles and video IDs into the same sets: although odd, the title
        # of a video can match the ID of another video.
        duplicateTitles = set()
        duplicateIds = set()
        remove = []
        for track in tracks:
            if track.videoId == None:
                if track.title in duplicateTitles:
                    remove.append(track)
                else:
                    duplicateTitles.add(track.title)
            else:
                if track.videoId in duplicateIds:
                    remove.append(track)
                else:
                    duplicateIds.add(track.videoId)
        self.removeTracks(playlist, remove)
