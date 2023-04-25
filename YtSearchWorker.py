import abc
from PyQt5 import QtCore

class YtSearchSignals(QtCore.QObject):
    tracksFound = QtCore.pyqtSignal(list)
    searchFinished = QtCore.pyqtSignal(object)
    searchError = QtCore.pyqtSignal(str)
    def __init__(self):
        super(QtCore.QObject, self).__init__()

class YtSearchWorker(QtCore.QRunnable):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super().__init__()
        self.signals = YtSearchSignals()
        self.tracksFound = self.signals.tracksFound
        self.searchFinished = self.signals.searchFinished
        self.searchError = self.signals.searchError

    def run(self):
        try:
            self.search()
        except Exception as e:
            self.searchError.emit(f'An error occurred during search:\n{e}')
        finally:
            self.searchFinished.emit(self)

    @abc.abstractmethod
    def search(self):
        raise NotImplementedError()
