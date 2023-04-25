from PyQt6 import QtCore, QtGui
from YtPlaylist import YtPlaylist
from YtPlaylistManager import YtPlaylistManager

class YtPlaylistModel(QtCore.QAbstractListModel):
    def __init__(self, playlistManager: YtPlaylistManager):
        super().__init__()
        self.playlistManager = playlistManager
        self.modelData = []
        self.activePlaylist = None
        self.activeFont = QtGui.QFont()
        self.activeFont.setPointSize(17)
        self.activeFont.setBold(True)
        self.inactiveFont = QtGui.QFont()
        self.inactiveFont.setPointSize(13)
        self.refreshModel()

    def supportedDropActions(self) -> QtCore.Qt.DropAction:
        return QtCore.Qt.DropAction.CopyAction

    def canDropMimeData(self, data, action, row, column, parent) -> bool:
        return action == QtCore.Qt.DropAction.CopyAction

    def refreshModel(self):
        self.beginResetModel()
        playlists = self.playlistManager.playlists
        self.modelData = sorted(playlists, key = lambda pl: pl.name)
        self.endResetModel()

    def getPlaylist(self, index: QtCore.QModelIndex) -> YtPlaylist:
        playlist = self.modelData[index.row()]
        return playlist

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole):
        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self.getPlaylist(index)
    
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            playlist = self.getPlaylist(index)
            label = f'{playlist.name} ({len(playlist)})'
            return label
        
        if role == QtCore.Qt.ItemDataRole.FontRole:
            track = self.playlistManager.getActiveTrack()
            playlist = self.getPlaylist(index)
            if track != None and playlist == track.playlist:
                return self.activeFont
            return self.inactiveFont

    def rowCount(self, parent: QtCore.QModelIndex) -> int:
        return len(self.playlistManager.playlists)
