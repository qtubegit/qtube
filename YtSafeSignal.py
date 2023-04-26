from PyQt6 import QtWidgets

# Signals emitted after closing the application main window can cause
# segmentation faults in some versions of Qt. This situation can occur 
# in background workers, which can keep running after the application 
# is closed. This provides wrappers for Qt signals to prevent this.
class YtSafeSignal:
    def emit(signal, *args):
        if QtWidgets.QApplication.instance() != None:
            signal.emit(*args)
        
