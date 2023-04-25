from PyQt6 import QtCore, QtWidgets, QtGui

class YtAspectRatioLabel(QtWidgets.QLabel):
    """
    A label that maintains its height to width ratio and limits
    its width to a given widget.
    """
    def __init__(self, widthWidget: QtCore.QObject):
        super().__init__()
        self.widthWidget = widthWidget
        self.setMinimumSize(1, 1)
        self.setScaledContents(True)
        self.setVisible(False)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Maximum)
        self.ratio = None
        self.icon = None

    def setIcon(self, icon: QtGui.QIcon) -> None:
        if icon == None: 
            return
        if icon == self.icon:
            return
        self.icon = icon
        maxSize = QtCore.QSize(1280, 720)
        size = icon.actualSize(maxSize)
        pixmap = icon.pixmap(size)
        self.setPixmap(pixmap)
        self.ratio = size.height() / size.width()
        aspectHeight = int(self.ratio * self.widthWidget.width())
        self.setMaximumHeight(aspectHeight)
        self.setVisible(True)

    def sizeHint(self) -> QtCore.QSize:
        aspectHeight = int(self.ratio * self.widthWidget.width())
        return QtCore.QSize(self.widthWidget.width(), aspectHeight)
        
    def resizeEvent(self, event: QtGui.QResizeEvent):
        aspectHeight = int(self.ratio * self.width())
        self.setMaximumHeight(aspectHeight)
