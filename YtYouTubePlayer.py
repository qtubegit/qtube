from PyQt6 import QtCore
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions 
from selenium.webdriver.support.ui import WebDriverWait
from selenium import webdriver

import enum
import http.server
import pathlib
import random
import socketserver
import sys
import threading

from YtTrack import YtTrack
from YtWebsocket import YtWebsocket

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

        # Sometimes, the HTTP server hangs around for a little, blocking 
        # the port. Picking a random port is a workaround.
        self.port = random.randint(1000, 9999)
        self.url = f'http://localhost:{self.port}/player.html'
        threading.Thread(target=self.startServer, daemon=True).start()

        # The YouTube IFrame API refuses to load many videos when being
        # run from a local web page. We need to serve it.
        self.playerState = None
        self.activeTrack = None
        self.waitingForVideoId = False
        self.isPlayerReady = False

        # Start Websocket server.
        self.webSocket = YtWebsocket('localhost', 8765)
        self.webSocket.add_callback('playerVolumeChanged', self.playerVolumeChanged)
        self.webSocket.add_callback('playerProgressChanged', self.playerProgressChanged)
        self.webSocket.add_callback('playerStateChanged', self.playerStateChanged)
        self.webSocket.add_callback('playerReady', self.playerReady)

    def start(self):
        # Start Selenium.
        options = Options()
        options.add_argument('--headless=new')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.url)

        body = self.driver.find_element(By.TAG_NAME, 'body')
        body.click()

        condition = expected_conditions.presence_of_element_located((By.ID, 'player'))
        WebDriverWait(self.driver, 0).until(condition)

    def quit(self):
        self.driver.quit()
        self.webServer.shutdown()

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
            self.webServer = None
            self.webServer = socketserver.TCPServer(('', self.port), Handler)
            self.webServer.serve_forever()
        finally:
            if self.webServer != None:
                self.webServer.shutdown()
    
    def tryRunJavascript(self, js):
        if not self.isPlayerReady:
            # Ignore all Javascript calls until player is ready.
            return
        try:
            self.driver.execute_script(js)
        except Exception:
            print(f'Unable to run javascript:\n{js}')

    def setVolume(self, volume):
        self.tryRunJavascript(f'setVolume("{volume}")')
        self.volumeChanged.emit(volume)

    def seekVideo(self, position):
        self.tryRunJavascript(f'seekTo("{position}")')

    def loadVideo(self, videoId):
        self.tryRunJavascript(f'loadVideo("{videoId}")')

    def cueVideo(self, videoId, startPosition):
        self.tryRunJavascript(f'cueVideo("{videoId}", {startPosition})')
        
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
        self.tryRunJavascript(f'playVideo()')

    def pause(self):
        self.tryRunJavascript(f'pauseVideo()')

    def getState(self):
        return self.playerState
    
    def playerVolumeChanged(self, volume):
        volume = int(volume)
        self.volumeChanged.emit(volume)

    def playerProgressChanged(self, position):
        position = int(float(position))
        self.positionChanged.emit(position)

    def playerStateChanged(self, state):
        state = int(state)
        self.playerState = state
        self.playerStatusChanged.emit(YtPlayerState(state))

    def playerReady(self, _):
        self.isPlayerReady = True
        if self.activeTrack != None:
            self.playTrack(self.activeTrack)

