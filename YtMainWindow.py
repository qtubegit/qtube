import datetime
import os
import pathlib
import time
from PyQt6 import QtCore, QtWidgets, QtGui
import typing

from YtAspectRatioLabel import YtAspectRatioLabel
from YtSearchWorkerGoogle import YtSearchWorkerGoogle
from YtInputWorker import YtInputWorker
from YtLineEdit import YtLineEdit
from YtPlaylistManager import YtPlayMode, YtPlaylistManager
from YtPlaylistWorker import YtPlaylistWorker
from YtPlaylistView import YtPlaylistView
from YtPlaylist import YtPlaylist
from YtPositionLabel import YtPositionLabel
from YtSearchWorkerYtdl import YtSearchWorkerYtdl
from YtTrackInfoWorker import YtTrackInfoWorker
from YtTrackView import YtTrackView
from YtTrack import YtTrack
from YtSearchWorkerLastFm import YtSearchWorkerLastFm
from YtYouTubePlayer import YtYouTubePlayer, YtPlayerState

class YtMainWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.configPath = pathlib.Path(pathlib.Path.home(), '.qtube')
        # View your keys: https://www.last.fm/api/accounts
        # Create one: https://www.last.fm/api/account/create
        self.lastFmApiKeyPath = pathlib.Path(self.configPath, 'lastfm_apikey')
        self.lastFmApiKey = None
        try:
            with open(self.lastFmApiKeyPath) as fp:
                self.lastFmApiKey = fp.read()
        except Exception as e:
            print(f'Could not read Last.fm API key: {e}')
            print('Last.fm search will be disabled.')

        self.googleKeys = None
        self.googleKeysPath = pathlib.Path(self.configPath, 'google_keys')
        try:
            with open(self.googleKeysPath) as fp:
                # Do not replace this with "readlines()": it will leave a 
                # newline character \n after each line element.
                self.googleKeys = fp.read().split('\n')
        except Exception as e:
            print(f'Could not read Google API keys: {e}')
            print('Google API search will be disabled.')

        self.searchResultsName = '# Search Results'
        self.playlistManager = YtPlaylistManager()

        self.threadPool = QtCore.QThreadPool.globalInstance()
        self.threadPool.setMaxThreadCount(os.cpu_count() * 10)

        self.searchThreads = []
        self.searchWorker = None
        self.trackThreads = []
        self.trackThread = None
        self.playingTrack = None
        self.timeSinceLastPlay = None
        self.playlistWorker = YtPlaylistWorker(self.playlistManager)
        self.threadPool.start(self.playlistWorker)
        self.setupUi()

        # Restore the last track that was playing when player quit.
        currentTrack = self.playlistManager.loadPlayingTrack()
        if currentTrack != None:
            self.playlistManager.activateTrack(currentTrack)
            self.trackView.showPlaylist(currentTrack.playlist)

    def setupUi(self):
        self.pauseIcon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPause)
        self.playIcon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaPlay)
        self.nextIcon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSkipForward)
        self.previousIcon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MediaSkipBackward)
        self.markerIcon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_ArrowRight)

        ## Widget Initialization
        self.player = YtYouTubePlayer()
        self.plNameEdit = QtWidgets.QLineEdit()
        self.trackView = YtTrackView(self.playlistManager)
        self.searchEdit = YtLineEdit()
        self.playlistView = YtPlaylistView(self.playlistManager)
        self.playlistView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.albumArt = YtAspectRatioLabel(self.playlistView)
        self.pauseButton = QtWidgets.QPushButton()
        self.pauseButton.setIcon(self.playIcon)
        self.nextButton = QtWidgets.QPushButton()        
        self.nextButton.setIcon(self.nextIcon)
        self.previousButton = QtWidgets.QPushButton()
        self.previousButton.setIcon(self.previousIcon)
        self.progressBar = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volumeSlider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setFixedWidth(100)
        self.playmodeButton = QtWidgets.QPushButton(YtPlayMode.Normal.value)
        self.playmodeButton.setFixedWidth(45)
        self.positionEdit = YtPositionLabel()
        self.positionEdit.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter)

        ## Signal Connections
        self.playlistManager.trackActivated.connect(self.playTrack)
        self.playlistManager.trackUpdated.connect(self.trackUpdated)
        self.playlistView.playlistSelected.connect(self.trackView.showPlaylist)
        self.trackView.doubleClicked.connect(self.playItem)
        self.trackView.findRelatedTracks.connect(self.findRelatedTracks)
        self.plNameEdit.returnPressed.connect(self.createPlaylist)
        self.searchEdit.returnPressed.connect(self.findTracks)
        self.searchEdit.searchTriggered.connect(self.trackView.searchTriggered)
        self.searchEdit.searchStopped.connect(self.trackView.searchStopped)
        self.previousButton.clicked.connect(self.playPrevious)
        self.nextButton.clicked.connect(self.playNext)
        self.pauseButton.clicked.connect(self.playPause)
        self.progressBar.valueChanged.connect(self.seekTrackPosition)
        self.volumeSlider.valueChanged.connect(self.changeVolume)
        self.playmodeButton.pressed.connect(self.playmodePressed)
        self.positionEdit.returnPressed.connect(self.positionEdited)
        self.player.playerStatusChanged.connect(self.playerStatusChanged)
        self.player.volumeChanged.connect(self.volumeChanged)
        self.playlistManager.trackUpdated.connect(self.player.trackUpdated)
        self.playlistManager.trackActivated.connect(self.player.playTrack)
        self.player.positionChanged.connect(self.positionEdit.update)
        self.player.positionChanged.connect(self.positionChanged)

        ## Layout
        self.leftSide = QtWidgets.QWidget()
        self.leftSideLayout = QtWidgets.QVBoxLayout(self.leftSide)
        self.leftSideLayout.addWidget(self.plNameEdit)
        self.leftSideLayout.addWidget(self.playlistView)
        self.leftSideLayout.addWidget(self.albumArt)
        self.leftSideLayout.setContentsMargins(0, 5, 0, 5)

        self.rightSide = QtWidgets.QWidget()
        self.rightSideLayout = QtWidgets.QVBoxLayout(self.rightSide)
        self.rightSideLayout.addWidget(self.searchEdit)
        self.rightSideLayout.addWidget(self.trackView)
        self.rightSideLayout.setContentsMargins(0, 5, 5, 5)

        self.splitter = QtWidgets.QSplitter(self)
        self.splitter.addWidget(self.leftSide)
        self.splitter.addWidget(self.rightSide)
        
        self.grid = QtWidgets.QGridLayout()
        self.grid.addWidget(self.splitter, 0, 0)
        self.grid.setContentsMargins(15, 15, 15, 15)
        self.setLayout(self.grid)
        
        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.addWidget(self.positionEdit)
        self.hlayout.addWidget(self.progressBar)
        self.hlayout.addWidget(self.previousButton)
        self.hlayout.addWidget(self.pauseButton)
        self.hlayout.addWidget(self.nextButton)
        self.hlayout.addWidget(self.volumeSlider)
        self.hlayout.addWidget(self.playmodeButton)
        self.grid.addLayout(self.hlayout, 1, 0, 1, 1)

        ## Main Window 
        self.setWindowTitle('QTube')
        initialSize = QtGui.QGuiApplication.primaryScreen().availableGeometry().size() * .65
        self.resize(initialSize)
        leftRatio = .25
        self.splitter.setSizes([
            int(initialSize.width() * leftRatio),
            int(initialSize.width() * (1 - leftRatio))])

        # Notifications
        self.appIcon = QtGui.QIcon('icon.ico')
        self.tray = QtWidgets.QSystemTrayIcon(self)
        self.tray.setIcon(self.appIcon)
        self.tray.setVisible(True)

        ## Media Keys
        self.inputThread = QtCore.QThread()
        self.inputWorker = YtInputWorker()
        self.inputWorker.moveToThread(self.inputThread)
        self.inputThread.started.connect(self.inputWorker.captureKeys)
        self.inputWorker.mediaPlayPause.connect(self.playPause)
        self.inputWorker.mediaPrevious.connect(self.playPrevious)
        self.inputWorker.mediaNext.connect(self.playNext)
        self.inputWorker.mediaShow.connect(self.showTrack)
        self.inputThread.start()

        # Shortcuts
        # I like this arrangement better than having to reach over to zero, which is
        # to the far right on the number row on most keyboards, to get to the track
        # beginning. As a future feature, make these configurable, perhaps.
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+1"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(0))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+2"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(10))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+3"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(20))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+4"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(30))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+5"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(40))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+6"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(50))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+7"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(60))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+8"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(70))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+9"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(80))
        self.shortcutSeek50 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+0"), self)
        self.shortcutSeek50.activated.connect(lambda: self.seekTrackPercent(90))
        self.shortcutSeekForward = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Left"), self)
        self.shortcutSeekForward.activated.connect(lambda: self.seekTrack(-10))
        self.shortcutSeekBackward = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+Right"), self)
        self.shortcutSeekBackward.activated.connect(lambda: self.seekTrack(10))
        self.shortcutFocusPlaylists = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+w"), self)
        self.shortcutFocusPlaylists.activated.connect(self.playlistView.focus)
        self.shortcutFocusTracks = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+e"), self)
        self.shortcutFocusTracks.activated.connect(self.trackView.focus)
        self.shortcutFocusSearch = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+f"), self)
        self.shortcutFocusSearch.activated.connect(self.searchEdit.setFocus)
        self.shortcutFocusPlaylistsName = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+s"), self)
        self.shortcutFocusPlaylistsName.activated.connect(self.plNameEdit.setFocus)
        self.shortcutFocusPosition = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+t"), self)
        self.shortcutFocusPosition.activated.connect(self.positionEdit.setFocus)
        self.shortcutFocusTrackView = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+r"), self)
        self.shortcutFocusTrackView.activated.connect(self.trackView.arrangeTracks)
        self.shortcutSwitchPlaymode = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+l"), self)
        self.shortcutSwitchPlaymode.activated.connect(self.playmodePressed)
        self.shortcutRefreshThumbnails = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+y"), self)
        self.shortcutRefreshThumbnails.activated.connect(self.trackView.refreshThumbnails)
        self.shortcutRemoveDuplicates = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+u"), self)
        self.shortcutRemoveDuplicates.activated.connect(self.trackView.removeDuplicates)
        self.shortcutRefreshTracks = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+i"), self)
        self.shortcutRefreshTracks.activated.connect(self.trackView.refreshTracks)
        self.shortcutFindSimilar = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+k"), self)
        self.shortcutFindSimilar.activated.connect(self.trackView.findSimilar)
        self.shortcutFullscreen = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.FullScreen, self)
        self.shortcutFullscreen.activated.connect(self.toggleFullscreen)

    def toggleFullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def showNotification(self, title, message, icon = None):
        if icon == None:
            icon = QtWidgets.QSystemTrayIcon.MessageIcon.NoIcon
        self.tray.showMessage(title, message, icon)

    def closeEvent(self, event):
        self.updatePlaytime()
        self.playlistManager.savePlaylists()
        self.playlistManager.savePlayingTrack()
        self.inputThread.quit()
        self.playlistWorker.quit()

    def playmodePressed(self):
        modes = [YtPlayMode.Normal, YtPlayMode.Shuffle, YtPlayMode.Loop]
        values = [m.value for m in modes]
        current = self.playmodeButton.text()
        index = values.index(current)
        mode = modes[(index + 1) % len(modes)]
        self.playmodeButton.setText(mode.value)
        self.playlistManager.setPlayMode(mode)

    def volumeChanged(self, volume):
        if not self.volumeSlider.isSliderDown():
            self.volumeSlider.setValue(volume)

    def changeVolume(self, position):
        self.player.volumeChanged.disconnect(self.volumeChanged)
        self.player.setVolume(position)
        self.player.volumeChanged.connect(self.volumeChanged)

    def playPause(self):
        isPlaying = self.player.getState() == YtPlayerState.Playing
        if isPlaying:
            self.pauseButton.setIcon(self.playIcon)
            self.player.pause()
        else:
            self.pauseButton.setIcon(self.pauseIcon)
            self.player.play()

    def seekTrackPosition(self, position):
        self.player.seekVideo(position)
    
    def seekTrack(self, offset):
        if self.playingTrack == None:
            return
        self.playingTrack.position += offset
        self.player.seekVideo(self.playingTrack.position)

    def seekTrackPercent(self, percent):
        track = self.playlistManager.getActiveTrack()
        if track != None and track.duration != None:
            position = track.duration * percent // 100
            self.player.seekVideo(position)

    def positionEdited(self):
        position = self.positionEdit.text()
        try:
            date = datetime.datetime.strptime(position, '%H:%M:%S')
        except:
            return
        delta = datetime.timedelta(
            hours=date.hour, 
            minutes=date.minute, 
            seconds=date.second)
        self.seekTrackPosition(delta.seconds)

    def positionChanged(self, position):
        self.progressBar.valueChanged.disconnect(self.seekTrackPosition)
        if not self.progressBar.isSliderDown():
            self.progressBar.setValue(position)
        self.progressBar.valueChanged.connect(self.seekTrackPosition)

        # Position changes for the previously playing video can keep being
        # received after requesting the player to start another track. In
        # order for position updates to not be written to the wrong track,
        # maintain the actually playing track separately. The track in the
        # playlist manager is always the target state and mismatches cannot
        # always be avoided.
        if self.playingTrack != None:
            self.playingTrack.position = position

    def findRelatedTracks(self, track: YtTrack):
        self.findTracks(track)

    def findTracks(self, relatedTrack = None):
        """
        If track is not None, search for music related to track.
        """
        if self.searchWorker != None:
            try: 
                self.searchWorker.tracksFound.disconnect(self.tracksFound)
            except: 
                pass
        term = self.searchEdit.text()
        ytPrefix = 'y:' # Search with youtube-dl.
        gApiPrefix = 'g:' # Search with Google API.
        if relatedTrack != None:
            if self.lastFmApiKey == None:
                self.showMessage(
                    f'No Last.fm key configured. Add one to {self.lastFmApiKeyPath}.')
                return
            self.searchWorker = YtSearchWorkerLastFm(
                term, self.lastFmApiKey, relatedTrack = relatedTrack)
        elif term.startswith(ytPrefix):
            self.searchWorker = YtSearchWorkerYtdl(term[len(ytPrefix):])
        elif term.startswith(gApiPrefix):
            if self.googleKeys == None:
                self.showMessage(
                    f'No Google keys configured. Add them to {self.googleKeysPath}.')
                return
            self.searchWorker = YtSearchWorkerGoogle(self.googleKeys, term[len(gApiPrefix):])
        else:
            if self.lastFmApiKey == None:
                self.showMessage(
                    f'No Last.fm key configured. Add one to {self.lastFmApiKeyPath}.')
                return
            self.searchWorker = YtSearchWorkerLastFm(term, self.lastFmApiKey)

        # A gray font means that a search is running. I do not know for sure if
        # this will look good on all system themes, e.g. light vs. dark mode.
        self.searchEdit.setStyleSheet('border: 1px solid yellow')
        self.searchWorker.tracksFound.connect(self.tracksFound)
        self.searchWorker.searchError.connect(self.showMessage)
        self.searchWorker.searchFinished.connect(self.searchFinished)
        self.threadPool.start(self.searchWorker)
        self.playlistManager.clearPlaylist(self.searchResultsName)
    
    def searchFinished(self, thread):
        # Other threads might still be running, but we are only interested in the
        # chronologically last one sent off.
        if thread == self.searchWorker:
            # Return style to normal to indicate that search has finished.
            self.searchEdit.setStyleSheet('')

    def showMessage(self, error):
        self.errorMessage = QtWidgets.QMessageBox()
        self.errorMessage.setText(error)
        self.errorMessage.show()

    def tracksFound(self, tracks: typing.List[YtTrack]):
        self.playlistManager.addTracks(self.searchResultsName, tracks)

    def playItem(self, index: QtCore.QModelIndex):
        track = self.trackView.getTrack(index)
        self.playlistManager.activateTrack(track)

    def updateAlbumArt(self, icon: QtGui.QIcon):
        self.albumArt.setIcon(icon)

    def playTrack(self, track: YtTrack):
        self.pauseButton.setIcon(self.pauseIcon)
        self.setWindowTitle(track.title)
        self.showNotification('Track Playing', track.title, track.icon)
        self.updateAlbumArt(track.icon)
        self.updateProgressBar(track)

        if None in [ track.duration, track.channel, track.videoId, track.icon ]:
            # Update track information in the background.
            worker = YtTrackInfoWorker(track)
            worker.trackUpdated.connect(self.playlistManager.updateTrack)
            worker.trackError.connect(self.showMessage)
            self.threadPool.start(worker)

    def updateProgressBar(self, track):
        if track.duration == None:
            return
        duration = track.duration if track.duration != None else 0
        self.progressBar.setMaximum(duration)

    def trackUpdated(self, track: YtTrack):
        if track != self.playlistManager.getActiveTrack():
            return
        # Track duration could have changed with an update.
        self.updateProgressBar(track)
        self.updateAlbumArt(track.icon)

    def playNext(self):
        self.playlistManager.activateNextTrack(loopOther = True)

    def playPrevious(self):
        self.playlistManager.activatePreviousTrack(loopOther = True)

    def updatePlaytime(self):
        if self.playingTrack == None or self.timeSinceLastPlay == None:
            return
        self.playTime = int(time.time() - self.timeSinceLastPlay)
        self.playingTrack.playTime += self.playTime
        self.playlistManager.updateTrack(self.playingTrack)
        self.timeSinceLastPlay = None

    def playerStatusChanged(self, status: YtPlayerState):
        if status == YtPlayerState.Unstarted:
            # Update previous track before switching to new one.
            self.updatePlaytime()
            # Position updates can keep coming in for the previous 
            # track until this status is signalled. This prevents
            # position updates from bleeding over across tracks.
            self.playingTrack = self.player.getActiveTrack()

        if status == YtPlayerState.Playing:
            self.pauseButton.setIcon(self.pauseIcon)
            self.timeSinceLastPlay = time.time()
        else:
            self.pauseButton.setIcon(self.playIcon)
            self.updatePlaytime()

        if status == YtPlayerState.Cued:
            self.player.play()

        if status == YtPlayerState.Ended:
            # A track that has finished should start off at the beginning.
            self.playingTrack.position = 0
            # Even when looping is disabled, the YouTube player will return 
            # to the beginning at times. Prevent that by pausing playback.
            self.player.pause()
            self.playlistManager.activateNextTrack()

    def createPlaylist(self):
        name = self.plNameEdit.text()
        self.playlistManager.createPlaylist(name)
        self.plNameEdit.clear()

    def showPlaylist(self, playlist: YtPlaylist):
        self.playlistSelected.emit(playlist)

    def showTrack(self):
        track = self.playlistManager.getActiveTrack()
        if track == None:
            self.showNotification('QTube', 'No track playing.')
        else:
            self.showNotification('Current Track', track.title, track.icon)
