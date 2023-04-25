import datetime
from PyQt5 import QtCore, QtGui, QtWidgets

class YtPositionLabel(QtWidgets.QLineEdit):
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(65)

    def eventFilter(self, object:QtCore.QObject, event:QtCore.QEvent) -> bool:
        if event.type() == QtCore.QEvent.FocusIn:
            try: self.player.positionChanged.disconnect(self.parent.updatePositionLabel)
            except: pass
        if event.type() == QtCore.QEvent.FocusOut:
            self.player.positionChanged.connect(self.parent.updatePositionLabel)
        return False

    def update(self, position):
        # Don't update while user is editing the label. 
        if self.hasFocus():
            return
        try:
            sp = str(datetime.timedelta(seconds=position))
        except OverflowError:
            sp = '0:00'
        self.setText(sp)

