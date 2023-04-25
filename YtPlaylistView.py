import ctypes
import json
import typing
from PyQt6 import QtCore, QtGui, QtWidgets
from YtPlaylistManager import YtPlaylistManager
from YtPlaylist import YtPlaylist
from YtPlaylistModel import YtPlaylistModel
from YtTrack import YtTrack

class YtPlaylistView(QtWidgets.QListView):
    playlistSelected = QtCore.pyqtSignal(YtPlaylist)

    def __init__(self, plManager: YtPlaylistManager, parent = None):
        super().__init__(parent)
        self.itemModel = YtPlaylistModel(plManager)
        self.setModel(self.itemModel)
        self.clicked.connect(self.loadPlaylist)
        self.setAcceptDrops(True)
        self.selectedPlaylist = None
        self.playlistManager = plManager
        self.playlistManager.playlistCreated.connect(self.itemModel.refreshModel)
        self.playlistManager.trackActivated.connect(self.refreshView)
        self.playlistManager.tracksAdded.connect(self.refreshView)
        self.playlistManager.tracksRemoved.connect(self.refreshView)
        self.installEventFilter(self)
        self.setFlow(QtWidgets.QListView.Flow.TopToBottom)
        self.setResizeMode(QtWidgets.QListView.ResizeMode.Adjust)
        self.setWrapping(True)

    def focus(self):
        self.setFocus()
        model = self.selectionModel()
        selected = model.selectedIndexes()
        if len(selected) > 0:
            return
        index = model.currentIndex()
        flags = QtCore.QItemSelectionModel.SelectionFlag.Select
        model.select(index, flags)

    def eventFilter(self, object:QtCore.QObject, event:QtCore.QEvent) -> bool:
        if (event.type() == QtCore.QEvent.Type.KeyPress 
        and event.key() == QtGui.QKeySequence('Backspace')):
            self.removeSelectedPlaylists()
            return True
        if (event.type() == QtCore.QEvent.Type.KeyPress 
        and event.key() == QtGui.QKeySequence('Space')):
            model = self.selectionModel()
            index = model.currentIndex()
            self.loadPlaylist(index)
            return True
        return False

    def refreshView(self):
        self.model().layoutChanged.emit()

    def loadPlaylist(self, index: QtCore.QModelIndex):
        self.selectedPlaylist = self.itemModel.getPlaylist(index)
        self.playlistSelected.emit(self.selectedPlaylist)

    def removeSelectedPlaylists(self):
        model = self.selectionModel()
        for index in model.selectedIndexes():
            playlist = self.itemModel.getPlaylist(index)
            if playlist == self.selectedPlaylist:
                self.selectedPlaylist == None
            self.playlistManager.removePlaylist(playlist.name)
        self.itemModel.refreshModel()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
        pos = event.position().toPoint()
        index = self.indexAt(pos)
        model = self.selectionModel()
        flags = QtCore.QItemSelectionModel.SelectionFlag.ClearAndSelect
        model.select(index, flags)
        self.setFocus()

    def dropEvent(self, event: QtGui.QDropEvent):
        pos = event.position().toPoint()
        index = self.indexAt(pos)
        playlist = self.itemModel.getPlaylist(index)
        data = event.mimeData().text()
        tracksDragged = json.loads(data)
        tracksToAdd = []
        for track in tracksDragged:
            track = ctypes.cast(track, ctypes.py_object).value
            newTrack = track.makeCopy()
            tracksToAdd.append(newTrack)
        self.playlistManager.addTracks(playlist.name, tracksToAdd)