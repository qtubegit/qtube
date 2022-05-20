from PyQt5 import QtWebEngineWidgets, QtCore, QtWebChannel

import enum
import http.server
import pathlib
import random
import socketserver
import sys
import threading

from YtTrack import YtTrack

class YtPlayerState(enum.IntEnum):
    Unstarted = -1
    Ended = 0
    Playing = 1
    Paused = 2
    Buffering = 3
    Cued = 5

class YtYouTubePlayer(QtCore.QObject):
    playerStatusChanged = QtCore.pyqtSignal(YtPlayerState)
    positionChanged = QtCore.pyqtSignal(int)
    volumeChanged = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.webView = QtWebEngineWidgets.QWebEngineView()
        self.webpage = QtWebEngineWidgets.QWebEnginePage(self.webView)
        self.webpage.profile().setPersistentCookiesPolicy(
            QtWebEngineWidgets.QWebEngineProfile.ForcePersistentCookies)
        self.webpage.settings().setAttribute(
            QtWebEngineWidgets.QWebEngineSettings.PlaybackRequiresUserGesture, 
            False)
        self.webView.setPage(self.webpage)

        # Sometimes, the HTTP server hangs around for a little, blocking 
        # the port. Picking a random port is a workaround.
        self.port = random.randint(1000, 9999)
        threading.Thread(target=self.startServer, daemon=True).start()

        # The YouTube IFrame API refuses to load many videos when being
        # run from a local web page. We need to serve it.
        url = f'http://localhost:{self.port}/player.html'
        html = QtCore.QUrl(url)
        self.webView.load(html)

        self.channel = QtWebChannel.QWebChannel()
        self.channel.registerObject('qwebchannel', self)
        self.webView.page().setWebChannel(self.channel)
        self.playerState = None
        self.activeTrack = None
        self.waitingForVideoId = False

    def startServer(self):
        # For pyinstaller.
        if hasattr(sys, '_MEIPASS'):
            baseDirectory = sys._MEIPASS
        else:
            baseDirectory = '.'
        directory = str(pathlib.Path(baseDirectory, 'http'))
        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

        try:
            s = None
            s = socketserver.TCPServer(('', self.port), Handler)
            s.serve_forever()
        finally:
            if s != None:
                s.shutdown()
            
    def setVolume(self, volume):
        self.webView.page().runJavaScript(f'setVolume("{volume}")')
        self.volumeChanged.emit(volume)

    def seekVideo(self, position):
        self.webView.page().runJavaScript(f'seekTo("{position}")')

    def loadVideo(self, videoId):
        self.webView.page().runJavaScript(f'loadVideo("{videoId}")')

    def cueVideo(self, videoId, startPosition):
        self.webView.page().runJavaScript(f'cueVideo("{videoId}", {startPosition})')

    def trackUpdated(self, track):
        if track == self.activeTrack and self.waitingForVideoId:
            self.playTrack(track)

    def playTrack(self, track: YtTrack):
        self.activeTrack = track
        # Can we play this or do we need to wait for an updated?
        self.waitingForVideoId = track.videoId == None
        if self.waitingForVideoId:
            return
        if track.position == None or track.position < 3:
            self.loadVideo(track.videoId)
        else:
            self.cueVideo(track.videoId, track.position)

    def getActiveTrack(self) -> YtTrack:
        return self.activeTrack

    def play(self):
        self.webView.page().runJavaScript(f'playVideo()')

    def pause(self):
        self.webView.page().runJavaScript(f'pauseVideo()')

    def getState(self):
        return self.playerState
    
    @QtCore.pyqtSlot(int)
    def playerProgressChanged(self, position):
        self.positionChanged.emit(position)

    @QtCore.pyqtSlot(int)
    def playerStateChanged(self, state):
        self.playerState = state
        self.playerStatusChanged.emit(YtPlayerState(state))

