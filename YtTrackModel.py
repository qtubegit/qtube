import datetime
import typing

from YtPlaylistManager import YtPlaylistManager
from YtPlaylist import YtPlaylist
from PyQt6 import QtCore, QtGui

class YtColumn():
    def __init__(
    self, 
    name: str, 
    attribute: str, 
    default: typing.Any,
    flags: QtCore.Qt.ItemFlag = QtCore.Qt.ItemFlag.NoItemFlags,
    sort: typing.Callable = None, 
    display: typing.Callable = None):
        self.name = name
        self.attribute = attribute
        self.default = default
        self.flags = flags
        self.sort = sort if sort != None else lambda k: k
        self.display = display if display != None else lambda k: k

    def getSortKey(self, value: typing.Any):
        if value == None:
            return self.default
        return self.sort(value)

    def getDisplayKey(self, value: typing.Any):
        if value == None:
            return ''
        return str(self.display(value))

class YtTrackModel(QtCore.QAbstractTableModel):
    modelChanged = QtCore.pyqtSignal()

    def __init__(self, playlistManager: YtPlaylistManager):
        super().__init__()
        self.playlistManager = playlistManager
        self.activePlaylist: YtPlaylist = None
        self.activeFont = QtGui.QFont()
        self.activeFont.setPointSize(18)
        self.activeFont.setBold(True)
        self.inactiveFont = QtGui.QFont()
        self.inactiveFont.setPointSize(14)
        
        # The following dictionary is used to map column numbers to various properties, such as from which 
        # class attribute of a track to get the value being displayed or how to sort and display them.
        self.columnMap: typing.Dict[int, YtColumn] = {
            0: YtColumn('Title', 'title', '', flags = QtCore.Qt.ItemFlag.ItemIsEditable, sort = lambda k: k.casefold()),
            1: YtColumn('Duration', 'duration', 0, display = lambda k: datetime.timedelta(seconds = k)),
            2: YtColumn('Play Time', 'playTime', 0, display = lambda k: datetime.timedelta(seconds = k)),
            3: YtColumn('Channel', 'channel', '', sort = lambda k: k.casefold()),
            4: YtColumn('ID', 'videoId', '', flags = QtCore.Qt.ItemFlag.ItemIsEditable),
        }
        self.filterTerm = ''

    def columnCount(self, parent: QtCore.QModelIndex = None):
        return len(self.columnMap)

    def rowCount(self, parent: QtCore.QModelIndex = None):
        if self.activePlaylist == None:
            return 0
        return len(self.modelData)

    def headerData(self, column, orientation, role):
        if role != QtCore.Qt.ItemDataRole.DisplayRole:
            return QtCore.QVariant()
        if orientation == QtCore.Qt.Orientation.Horizontal:
            return self.columnMap[column].name

    def getTrack(self, index):
        return self.data(index, QtCore.Qt.ItemDataRole.UserRole)

    def data(self, index, role: QtCore.Qt.ItemDataRole):
        if not index.isValid():
            return QtCore.QVariant()

        if role == QtCore.Qt.ItemDataRole.UserRole:
            return self.modelData[index.row()]

        if role == QtCore.Qt.ItemDataRole.FontRole:
            activeTrack = self.playlistManager.getActiveTrack()
            if self.modelData[index.row()] == activeTrack:
                return self.activeFont
            return self.inactiveFont

        if role == QtCore.Qt.ItemDataRole.DecorationRole and index.column() == 0:
           return self.modelData[index.row()].icon

        if role == QtCore.Qt.ItemDataRole.DisplayRole or role == QtCore.Qt.ItemDataRole.EditRole:
            track = self.modelData[index.row()]
            mapping = self.columnMap[index.column()]
            value = track.__getattr__(mapping.attribute)
            key = mapping.getDisplayKey(value)
            return key

        return QtCore.QVariant()

    def setData(self, index, value, role) -> bool:
        attribute = self.columnMap[index.column()].attribute
        track = self.modelData[index.row()]
        track.__setattr__(attribute, value)
        self.playlistManager.updateTrack(track)
        return True

    def flags(self, index) -> QtCore.Qt.ItemFlag:
        flags = super().flags(index)
        mapping = self.columnMap[index.column()]
        return flags | mapping.flags

    def refreshModel(self):
        # This is expensive. Only call this when the underlying data has changed.
        # For visual updates, repaint the view instead.
        self.beginResetModel()
        self.filter(self.filterTerm)
        self.endResetModel()

    def sort(self, column: int, direction: QtCore.Qt.SortOrder):
        if self.activePlaylist == None:
            return
        mapping = self.columnMap[column]
        attribute = mapping.attribute
        key = lambda track: mapping.getSortKey(track.__getattr__(attribute))
        self.activePlaylist.tracks = sorted(
            self.activePlaylist.tracks,
            reverse = (direction == QtCore.Qt.SortOrder.DescendingOrder),
            key = key)
        self.filter(self.filterTerm)
        self.modelChanged.emit()
        self.playlistManager.saveCurrentTrack()

    def setActivePlaylist(self, playlist: YtPlaylist):
        self.beginResetModel()
        self.activePlaylist = playlist
        self.modelData = playlist
        self.endResetModel()

    def trackIndexes(self, tracks) -> typing.List[QtCore.QModelIndex]:
        if self.modelData == None:
            return []
        indices = [
            self.index(row, 0) for (row, track) 
            in enumerate(self.modelData) 
            if track in tracks ]
        return indices

    def activeTrackIndex(self) -> QtCore.QModelIndex:
        activeTrack = self.playlistManager.getActiveTrack()
        indices = self.trackIndexes([activeTrack])
        if len(indices) > 0:
            return indices[0]
        return None

    def filter(self, term: str):
        # There is a builtin class QSortFilterProxyModel that can do
        # filtering of models. However, a previous attempt to use it
        # had resulted in performance issues.
        self.filterTerm = term
        if self.activePlaylist == None:
            return
        self.modelData = [
            track for track in self.activePlaylist 
            if term.casefold() in track.title.casefold() ]
