from PyQt6 import QtCore
import time

from YtPlaylistManager import YtPlaylistManager

class YtPlaylistWorker(QtCore.QRunnable):
    def __init__(self, playlistManager: YtPlaylistManager):
        super().__init__()
        self.playlistManager = playlistManager
        self.shouldQuit = False

    def run(self):
        while not self.shouldQuit:
            if self.playlistManager.isDirty == True:
                self.playlistManager.savePlaylists()
            time.sleep(1)

    def quit(self):
        self.shouldQuit = True


