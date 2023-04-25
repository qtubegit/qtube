import datetime
from PyQt6 import QtCore, QtGui, QtWidgets

class YtPositionLabel(QtWidgets.QLineEdit):
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(65)

    def update(self, position):
        # Don't update while user is editing the label. 
        if self.hasFocus():
            return
        try:
            sp = str(datetime.timedelta(seconds=position))
        except OverflowError:
            sp = '0:00'
        self.setText(sp)
