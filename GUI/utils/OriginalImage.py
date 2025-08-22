from PyQt5 import QtCore, QtGui, QtWidgets
import os

class Ui_MainWindow(object):  # Change to object (not QMainWindow)
    def setupUi(self, MainWindow):
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(screen_width, screen_height)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(0, 0, 791, 551))
        self.label.setStyleSheet(
            "border: 0.5px solid black;\n"
            # "border-radius: 5px;\n"
            "padding: 5px;\n"
            "background-color: white;"
        )
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Original Image"))
        self.label.setText(_translate("MainWindow", "No Image Loaded"))


class OriginalImageWindow(QtWidgets.QMainWindow):  # Now this is a proper window class
    def __init__(self, image_path=None):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.image_path = image_path
        if image_path:
            self.set_image_path(image_path)

    def set_image_path(self, image_path):
        """Sets the image and updates the UI."""
        self.image_path = image_path
        self.update_image()

    def update_image(self):
        """Updates the image display.
        
        This method loads the image from the provided path and calculates the scale factor.
        If the label’s size is smaller than the original image, it scales down the image.
        If the label’s size is larger (for example, in a maximized window) and would upscale the image,
        it displays the image at its original size to avoid quality degradation.
        """
        if hasattr(self, 'image_path') and self.image_path:
            pixmap = QtGui.QPixmap(self.image_path)
            if not pixmap.isNull():
                target_width = self.ui.label.width()
                target_height = self.ui.label.height()
                # Compute the scale factor to keep aspect ratio
                scale_factor = min(target_width / pixmap.width(), target_height / pixmap.height())
                # Only scale down if needed; do not upscale the image.
                if scale_factor < 1:
                    scaled_pixmap = pixmap.scaled(
                        target_width,
                        target_height,
                        QtCore.Qt.KeepAspectRatio,
                        QtCore.Qt.SmoothTransformation
                    )
                else:
                    scaled_pixmap = pixmap
                self.ui.label.setPixmap(scaled_pixmap)
            else:
                self.ui.label.setText("Image Load Failed")
        else:
            self.ui.label.setText("No Image Selected")

    def resizeEvent(self, event):
        """Ensures image resizes correctly with the window."""
        self.ui.label.setGeometry(0, 0, self.ui.centralwidget.width(), self.ui.centralwidget.height())
        self.update_image()
        super().resizeEvent(event)
