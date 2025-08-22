from PyQt5 import QtCore, QtGui, QtWidgets

class AspectRatioLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # We do NOT want the built-in scaledContents because it will
        # stretch the label itself. Instead, we rely on heightForWidth.
        self.setScaledContents(False)
        # Allow the label to expand/shrink
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                           QtWidgets.QSizePolicy.Expanding)
        # Keep track of the pixmap
        self._pixmap = None

    def setPixmap(self, pixmap: QtGui.QPixmap):
        """Store the pixmap and update the widget geometry."""
        self._pixmap = pixmap
        super().setPixmap(pixmap)
        self.updateGeometry()  # Tells layout system to recalc size

    def hasHeightForWidth(self):
        """Tell Qt we use heightForWidth to maintain aspect ratio."""
        return True

    def heightForWidth(self, width):
        """Compute the correct height given a width, to keep aspect ratio."""
        if self._pixmap:
            aspect_ratio = self._pixmap.height() / self._pixmap.width()
            return int(width * aspect_ratio)
        return super().heightForWidth(width)

    def sizeHint(self):
        """Suggested size is the pixmap size, or fallback if none."""
        if self._pixmap:
            return self._pixmap.size()
        return super().sizeHint()
