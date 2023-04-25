from PyQt5 import QtCore, QtWidgets, QtGui

# Subclassed to handle key press events. There appears to currently 
# be no signal for this and this is the proper way to catch them.
class YtLineEdit(QtWidgets.QLineEdit):
    searchTriggered = QtCore.pyqtSignal(str)
    searchStopped = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        super().keyPressEvent(e)
        if self.text().startswith('/'):
            self.searchTriggered.emit(self.text()[1:])
        else:
            self.searchStopped.emit()
