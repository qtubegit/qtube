from PyQt6 import QtCore, QtGui, QtWidgets
import json
import typing

from YtTrackModel import YtTrackModel
from YtPlaylistManager import YtPlaylistManager
from YtPlaylist import YtPlaylist
from YtTrack import YtTrack
from YtTrackInfoWorker import YtTrackInfoWorker

class YtTrackView(QtWidgets.QTableView):
    findRelatedTracks = QtCore.pyqtSignal(YtTrack)

    def __init__(self, plManager: YtPlaylistManager):
        super().__init__()
        self.selectedPlaylist = None
        self.dragStart = None
        self.trackSelection = []
        self.trackCurrent = None
        self.clipboardTracks = []

        self.itemModel = YtTrackModel(plManager)
        self.setModel(self.itemModel)
        self.playlistManager = plManager
        self.playlistManager.tracksAdded.connect(self.tracksAdded)
        self.playlistManager.tracksRemoved.connect(self.tracksRemoved)
        self.playlistManager.trackActivated.connect(self.trackActivated)
        self.playlistManager.playlistRemoved.connect(self.playlistRemoved)
        self.playlistManager.playlistCleared.connect(self.playlistCleared)
        self.playlistManager.trackUpdated.connect(self.trackUpdated)
        self.itemModel.modelChanged.connect(self.refreshModel)

        self.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSortingEnabled(True)
        self.setEditTriggers(QtWidgets.QTableView.EditTrigger.EditKeyPressed)
        self.setIconSize(QtCore.QSize(72, 72))
        verticalHeader = self.verticalHeader()
        verticalHeader.setDefaultSectionSize(50)
        self.setColumnWidth(0, int(self.size().width() * .5))
        self.setWordWrap(True)
        self.setDragEnabled(True)
        self.setShowGrid(False)
        self.verticalHeader().setVisible(False)
        self.installEventFilter(self)
        self.setSelectionBehavior(self.SelectionBehavior.SelectRows)

        self.shortcutDeleteTrack = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+d'), self)
        self.shortcutDeleteTrack.activated.connect(self.removeTracks)
        self.shortcutContextMenu = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+g'), self)
        self.shortcutContextMenu.activated.connect(self.showContextMenuAtCurrentItem)
        self.shortcutCutTracks = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Cut, self)
        self.shortcutCutTracks.activated.connect(self.cutTracks)
        self.shortcutCopyTracks = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Copy, self)
        self.shortcutCopyTracks.activated.connect(self.copyTracks)
        self.shortcutPasteTracks = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Paste, self)
        self.shortcutPasteTracks.activated.connect(self.pasteTracks)

    def cutTracks(self):
        self.copyTracks()
        self.removeTracks()

    def copyTracks(self):
        self.clipboardTracks = self.selectedTracks()
    
    def pasteTracks(self):
        playlist = self.selectedPlaylist
        copyTracks = [track.makeCopy() for track in self.clipboardTracks]
        self.playlistManager.addTracks(playlist.name, copyTracks)

    def focus(self):
        self.setFocus()
        model = self.selectionModel()
        selected = model.selectedIndexes()
        if len(selected) > 0:
            return
        index = model.currentIndex()
        flags = QtCore.QItemSelectionModel.SelectionFlag.Select
        model.select(index, flags)

    def trackActivated(self, track: YtTrack):
        if self.selectedPlaylist == track.playlist:
            self.refreshView()

    def showPlaylist(self, playlist: YtPlaylist):
        self.selectedPlaylist = playlist
        self.itemModel.setActivePlaylist(playlist)
        index = self.itemModel.activeTrackIndex()
        if index != None:
            self.scrollTo(index)

    def refreshView(self):
        """ 
        Call this to update the track view, without reloading any of the track
        information. Do not reset the model, unless tracks have been added or
        removed. For example, if a different track becomes active, refreshing
        the view with this method is enough and faster than a model reset.
        """
        self.viewport().update()

    def arrangeTracks(self):
        self.resizeColumnsToContents()
        header = self.horizontalHeader()
        column = header.sortIndicatorSection()
        order = header.sortIndicatorOrder()
        self.itemModel.sort(column, order)

    def searchTriggered(self, term: str):
        self.itemModel.filter(term)
        self.itemModel.refreshModel()

    def searchStopped(self):
        self.itemModel.filter('')
        self.itemModel.refreshModel()

    def showContextMenuAtCurrentItem(self):
        index = self.currentIndex()
        rect = self.visualRect(index)
        center = rect.center()
        pos = self.mapToGlobal(center)
        self.showContextMenu(pos)

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        pointerPos = event.pos()
        globalPos = self.mapToGlobal(pointerPos)
        self.showContextMenu(globalPos)
        return super().contextMenuEvent(event)
        
    def showContextMenu(self, pos):
        menu = QtWidgets.QMenu()

        findSimilarTracks = QtGui.QAction('Find &similar tracks', self)
        menu.addAction(findSimilarTracks)
        removeDuplicates = QtGui.QAction('Remove &duplicate tracks', self)
        menu.addAction(removeDuplicates)
        refreshTracks = QtGui.QAction('Refresh track &info', self)
        menu.addAction(refreshTracks)
        refreshThumbnails = QtGui.QAction('Refresh &thumbnails', self)
        menu.addAction(refreshThumbnails)
        actionMap = {
            findSimilarTracks: self.findSimilar,
            removeDuplicates: self.removeDuplicates,
            refreshTracks: self.refreshTracks,
            refreshThumbnails: self.refreshThumbnails,
        }
        action = menu.exec(pos)
        if action != None:
            actionMap[action]()

    def findSimilar(self):
        track = self.selectedTracks()[0]
        self.findRelatedTracks.emit(track)

    def removeDuplicates(self):
        tracks = self.selectedTracks()
        self.playlistManager.removeDuplicates(self.selectedPlaylist, tracks)

    def refreshTracks(self):
        for track in self.selectedTracks():
            worker = YtTrackInfoWorker(track, refreshTitle = True)
            worker.trackUpdated.connect(self.playlistManager.updateTrack)
            threadPool = QtCore.QThreadPool.globalInstance()
            threadPool.start(worker)

    def refreshThumbnails(self):
        for track in self.selectedTracks():
            worker = YtTrackInfoWorker(track, refreshThumbnail = True)
            worker.trackUpdated.connect(self.playlistManager.updateTrack)
            threadPool = QtCore.QThreadPool.globalInstance()
            threadPool.start(worker)

    def trackUpdated(self, track: YtTrack):
        if track.playlist == self.selectedPlaylist:
            self.refreshView()

    def eventFilter(self, object: QtCore.QObject, event: QtCore.QEvent) -> bool:
        if (event.type() == QtCore.QEvent.Type.KeyPress
        and event.key() == QtGui.QKeySequence('Backspace')):
            self.removeTracks()
            return True
        if (event.type() == QtCore.QEvent.Type.KeyPress 
        and event.key() == QtGui.QKeySequence('Space')):
            track = self.currentTrack()
            self.playlistManager.activateTrack(track)
            return True
        return False

    def removeTracks(self):
        if self.selectedPlaylist == None:
            return
        tracks = self.selectedTracks()
        if len(tracks) == 0:
            return
        self.playlistManager.removeTracks(self.selectedPlaylist, tracks)

    def playlistCleared(self, playlist: YtPlaylist):
        if self.selectedPlaylist == playlist:
            self.refreshModel()

    def playlistRemoved(self, playlist: YtPlaylist):
        if self.selectedPlaylist == playlist:
            self.itemModel.setActivePlaylist(None)

    def selectionChanged(self, selected: QtCore.QItemSelection, deselected: QtCore.QItemSelection) -> None:
        self.trackSelection = self.selectedTracks()
        return super().selectionChanged(selected, deselected)

    def currentChanged(self, current: QtCore.QModelIndex, previous: QtCore.QModelIndex) -> None:
        self.trackCurrent = self.currentTrack()
        return super().currentChanged(current, previous)

    def tracksRemoved(self, playlist: YtPlaylist, tracks: typing.List[YtTrack]):
        if playlist == self.selectedPlaylist:
            self.refreshModel()

    def tracksAdded(self, playlist: YtPlaylist, tracks: typing.List[YtTrack]):
        if self.selectedPlaylist == playlist:
            self.refreshModel()        

    def refreshModel(self):
        """
        Reload current data in model from scratch and restore previous selection after.
        This is more expensive than a simple repaint and should only be used if there is
        no simple way to limit the refresh to the delta of the change. One example might
        be that several, non-contiguous cells would need to be added or removed. It would
        be faster to add and remove only those rows, but as long as a complete refresh is
        not too slow, data can be reloaded using this method.
        """
        self.itemModel.refreshModel()

        selectedIndexes = self.itemModel.trackIndexes(self.trackSelection)
        model = self.selectionModel()
        flags = QtCore.QItemSelectionModel.SelectionFlag.Select | QtCore.QItemSelectionModel.SelectionFlag.Rows
        selection = QtCore.QItemSelection()
        for index in selectedIndexes:
            selection.select(index, index)
        model.select(selection, flags)
        
        # Setting the current index will move the viewport so one 
        # also needs to restore the scrollbar position to prevent 
        # jumping when scrolling while tracks are being added.
        verticalScroll = self.verticalScrollBar()
        verticalPosition = verticalScroll.value()
        horizontalScroll = self.horizontalScrollBar()
        horizontalPosition = horizontalScroll.value()
        if self.trackCurrent == None:
            return
        currentIndexes = self.itemModel.trackIndexes([self.trackCurrent])
        if len(currentIndexes) > 0:
            model.setCurrentIndex(currentIndexes[0], flags)
        verticalScroll.setValue(verticalPosition)
        horizontalScroll.setValue(horizontalPosition)

    def currentTrack(self) -> YtTrack:
        # Remember that the current item is different from the selected items. The first one
        # determines from where selections extend when additional rows are selected. Restoring
        # only the selection has the effect of shift-clicking to extend the selection, for
        # example, to continue from a row other than the one before the model reset.
        model = self.selectionModel()
        index = model.currentIndex()
        return self.itemModel.getTrack(index)

    def getTrack(self, index) -> YtTrack:
        track = self.itemModel.getTrack(index)
        return track

    def selectedTracks(self) -> typing.List[YtTrack]:
        model = self.selectionModel()
        rows = model.selectedRows()
        tracks = [self.itemModel.getTrack(index) for index in rows]
        return tracks

    def mousePressEvent(self, e: QtGui.QMouseEvent):
        super().mousePressEvent(e)
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dragStart = e.pos()

    def mouseMoveEvent(self, e):
        if self.dragStart == None:
            return
        if not (e.buttons() and QtCore.Qt.MouseButton.LeftButton):
            return
        if (e.pos() - self.dragStart).manhattanLength() < QtWidgets.QApplication.startDragDistance():
            return

        tracks = self.selectedTracks()
        trackIds = [id(track) for track in tracks]
        mimeData = QtCore.QMimeData()
        mimeData.setText(json.dumps(trackIds))

        icon = self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        pixmap = icon.pixmap(QtCore.QSize(64, 64))

        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.exec(QtCore.Qt.DropAction.CopyAction)
