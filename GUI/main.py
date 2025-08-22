# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'App.ui'
#
# Created by: PyQt5 UI code generator 5.15.10

from PyQt5 import QtCore, QtGui, QtWidgets
import os
from utils.OriginalImage import OriginalImageWindow
from utils.DetectedImage import DetectedImageWindow
import sys
import subprocess
from PIL import Image
import ast
import re
from show_bounding import display_bbox

class Ui_WeldingDefectDetection(object):
    def setupUi(self, WeldingDefectDetection):
        WeldingDefectDetection.setObjectName("WeldingDefectDetection")
        
        # 2) Get the available screen geometry
        screen = QtWidgets.QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        WeldingDefectDetection.resize(screen_width, screen_height)


        # Make window expandable
        WeldingDefectDetection.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        WeldingDefectDetection.setMinimumSize(800, 600)

        # Central widget
        self.centralwidget = QtWidgets.QWidget(WeldingDefectDetection)
        self.centralwidget.setObjectName("centralwidget")

        # Create a stacked layout to switch between welcome and main UI
        self.stackedLayout = QtWidgets.QStackedLayout(self.centralwidget)

        # Welcome widget
        self.welcomeWidget = QtWidgets.QWidget(self.centralwidget)
        self.welcomeLayout = QtWidgets.QVBoxLayout(self.welcomeWidget)
        self.welcomeWidget.setObjectName("WelcomeWidget")
        self.logoLabel = QtWidgets.QLabel()
        self.logoLabel.setPixmap(QtGui.QPixmap("Assets/DRDOLogo.png"))
        self.logoLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.logoLabel.setObjectName("WelcomeLogo")
        self.descLabel = QtWidgets.QLabel("Welcome to Welding Defect Detection!\n" \
        "Please select a folder to begin.\n" \
        "File -> Open Folder")
        self.descLabel.setObjectName("WelcomeDescription")
        self.descLabel.setAlignment(QtCore.Qt.AlignCenter)
        # self.descLabel.setStyleSheet("font-size: 20px; color: red;")
        self.welcomeLayout.addWidget(self.logoLabel,stretch=6)
        self.welcomeLayout.addWidget(self.descLabel,stretch=4)

        # ============= MAIN LAYOUT (Horizontal) =============
        #  We will have three columns:
        #   1) Left column -> Scrollable image list
        #   2) Center column -> FileName label + Grid of images + model row
        #   3) Right column -> Bounding boxes
        self.mainWidget = QtWidgets.QWidget(self.centralwidget)
        self.mainLayout = QtWidgets.QHBoxLayout(self.mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        # -- Left column layout --
        self.leftLayout = QtWidgets.QVBoxLayout()
        self.leftLayout.setSpacing(0)

        # -- Center column layout --
        self.centerLayout = QtWidgets.QVBoxLayout()
        self.centerLayout.setSpacing(0)

        # -- Right column layout --
        self.rightLayout = QtWidgets.QVBoxLayout()
        self.rightLayout.setSpacing(0)

        # Add them to the main layout
        self.mainLayout.addLayout(self.leftLayout)
        self.mainLayout.addLayout(self.centerLayout)
        self.mainLayout.addLayout(self.rightLayout)


        # 1. Create the buttons
        self.LeftButtonFrame = QtWidgets.QFrame(self.centralwidget)
        self.LeftButtonFrame.setObjectName("LeftButtonFrame")
        self.LeftTopButton1 = QtWidgets.QPushButton("Button 1", self.LeftButtonFrame)
        self.LeftTopButton2 = QtWidgets.QPushButton("Button 2", self.LeftButtonFrame)
        # self.LeftTopButton1.setFixedWidth(10)
        # self.LeftTopButton2.setFixedWidth(10)   
        self.LeftTopButton1.setIconSize(QtCore.QSize(24, 24))
        self.LeftTopButton2.setIconSize(QtCore.QSize(24, 24))
        self.LeftTopButton1.setObjectName("LeftTopButton1")
        self.LeftTopButton2.setObjectName("LeftTopButton2")

        # 2. Create a horizontal layout for the buttons
        self.leftTopButtonsLayout = QtWidgets.QHBoxLayout(self.LeftButtonFrame)
        self.leftTopButtonsLayout.setObjectName("leftTopButtonsLayout")
        self.leftTopButtonsLayout.setSpacing(0)
        self.leftTopButtonsLayout.setContentsMargins(0, 0, 0, 0)
        self.leftTopButtonsLayout.addWidget(self.LeftTopButton1)
        self.leftTopButtonsLayout.addWidget(self.LeftTopButton2)
        self.leftTopButtonsLayout.setAlignment(QtCore.Qt.AlignLeft)
        self.LeftTopButton1.setIcon(QtGui.QIcon("Assets/icons8-menu-30.png"))
        self.LeftTopButton1.setIconSize(QtCore.QSize(20, 20))  # Adjust size as needed
        self.LeftTopButton1.setText("Gallery Images")  # Optional: remove text if you want icon only

        self.LeftTopButton2.setIcon(QtGui.QIcon("Assets/icons8-menu-30.png"))
        self.LeftTopButton2.setIconSize(QtCore.QSize(20, 20))  # Adjust size as needed
        self.LeftTopButton2.setText("Patches")  # Optional: remove text if you want icon only

        # 3. Add the button layout to the leftLayout before ListPhotoGallery
        self.leftLayout.addWidget(self.LeftButtonFrame)



        # ============= LEFT COLUMN: ScrollArea for Image List =============
        self.ListPhotoGallery = QtWidgets.QScrollArea()
        self.ListPhotoGallery.setWidgetResizable(True)
        self.ListPhotoGallery.setObjectName("ListPhotoGallery")
        self.ListPhotoGallery.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.scrollAreaWidgetContents_1 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_1.setObjectName("scrollAreaWidgetContents_1")
        self.imageListLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_1)

        self.BoxList1 = QtWidgets.QListView(self.scrollAreaWidgetContents_1)
        self.BoxList1.setObjectName("BoxList1")
        # Add the QListView to the scroll area layout
        self.imageListLayout.addWidget(self.BoxList1)

        self.ListPhotoGallery.setWidget(self.scrollAreaWidgetContents_1)
        self.leftLayout.addWidget(self.ListPhotoGallery)

        # ============= CENTER COLUMN =============
        # 1) FileName label at the top
        self.TextFileName = QtWidgets.QLabel(self.centralwidget)
        self.TextFileName.setAlignment(QtCore.Qt.AlignCenter)
        self.TextFileName.setObjectName("TextFileName")
        self.centerLayout.addWidget(self.TextFileName)

        # 2) A 3-row × 2-column grid for images + model row
        self.imagesGrid = QtWidgets.QGridLayout()
        self.imagesGrid.setSpacing(0)

        # ---- Top row: BoxOriginalImage (col 0), BoxDetectedImage (col 1) ----
        self.BoxOriginalImage = QtWidgets.QLabel(self.centralwidget)
        self.BoxOriginalImage.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.BoxOriginalImage.setObjectName("BoxOriginalImage")
        self.BoxOriginalImage.setProperty("class", "imageBox")

        self.BoxDetectedImage = QtWidgets.QLabel(self.centralwidget)
        self.BoxDetectedImage.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.BoxDetectedImage.setObjectName("BoxDetectedImage")
        self.BoxDetectedImage.setProperty("class", "imageBox")

        self.imagesGrid.addWidget(self.BoxOriginalImage, 0, 0)
        self.imagesGrid.addWidget(self.BoxDetectedImage, 0, 1)

        self.BoxOriginalImage.setAlignment(QtCore.Qt.AlignCenter)
        self.BoxDetectedImage.setAlignment(QtCore.Qt.AlignCenter)

        # ---- Middle row: Side-by-side control panels ----
        # Left control panel (aligned with BoxOriginalImage)
        self.controlLeftLayout = QtWidgets.QHBoxLayout()
        self.ButtonSelectModel = QtWidgets.QComboBox()
        self.ButtonSelectModel.setView(QtWidgets.QListView())
        self.ButtonSelectModel.setObjectName("ButtonSelectModel")
        # self.ButtonSelectModel.addItem("")
        # self.ButtonSelectModel.addItem("")
        # self.ButtonSelectModel.addItem("")
        
        self.ButtonDetectDefect = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonDetectDefect.setObjectName("ButtonDetectDefect")
        
        # Add the two control panels into the grid layout:
        self.controlLeftLayout.addWidget(self.ButtonSelectModel)
        self.controlLeftLayout.addWidget(self.ButtonDetectDefect)



        ############## Right control panel (aligned with BoxDetectedImage) ##############
        self.controlRightLayout = QtWidgets.QHBoxLayout()

        # Create a frame to wrap the ThresholdSlider and ThresholdTextLabel
        self.ThresholdFrame = QtWidgets.QFrame(self.centralwidget)
        self.ThresholdFrame.setObjectName("ThresholdFrame")
        self.ThresholdFrame.setProperty("class", "controlFrame")
        # Decrease the height of the ThresholdFrame
        self.ThresholdFrame.setFixedHeight(38)  # Set a fixed height (adjust as needed)
        self.ThresholdFrameLayout = QtWidgets.QHBoxLayout(self.ThresholdFrame)
        self.ThresholdFrameLayout.setContentsMargins(0, 0, 0, 0)  # Remove margins

        # Add the ThresholdSlider to the frame
        self.ThresholdSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self.ThresholdFrame)
        self.ThresholdSlider.setObjectName("ThresholdSlider")
        self.ThresholdSlider.setMinimum(0)  # Minimum value
        self.ThresholdSlider.setMaximum(100)  # Maximum value (scaled to 0-1 later)
        self.ThresholdSlider.setValue(50)  # Initial value (scaled to 0.5 later)
        # Add the ThresholdTextLabel to the frame
        self.ThresholdTextLabel = QtWidgets.QLabel(self.ThresholdFrame)
        self.ThresholdTextLabel.setObjectName("ThresholdTextLabel")
        self.ThresholdTextLabel.setText(f"Threshold: {self.ThresholdSlider.value() / 100:.2f}")  # Initial value
        self.ThresholdTextLabel.setProperty("class", "thresholdLabel")
        self.ThresholdFrameLayout.addWidget(self.ThresholdTextLabel)
        self.ThresholdFrameLayout.addWidget(self.ThresholdSlider)
        # Connect the slider to update the label
        self.ThresholdSlider.valueChanged.connect(self.update_threshold_text_label)
        # Add the frame to the controlRightLayout
        self.controlRightLayout.addWidget(self.ThresholdFrame)


        #  Add the Edit Image button to the right control panel 
        self.ButtonEditImage = QtWidgets.QRadioButton(self.centralwidget)
        self.ButtonEditImage.setObjectName("ButtonEditImage")
        self.controlRightLayout.addWidget(self.ButtonEditImage)

        # Add the two control panels into the grid layout:
        self.imagesGrid.addLayout(self.controlLeftLayout, 1, 0)
        self.imagesGrid.addLayout(self.controlRightLayout, 1, 1)

        # ---- Bottom row: BoxMetadataImage (col 0), BoxEditImage (col 1) ----
        self.BoxMetadataImage = QtWidgets.QLabel(self.centralwidget)
        self.BoxMetadataImage.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.BoxMetadataImage.setObjectName("BoxMetadataImage")
        self.BoxMetadataImage.setProperty("class", "imageBox")
        self.BoxEditImage = QtWidgets.QLabel(self.centralwidget)

        self.BoxEditImage.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.BoxEditImage.setObjectName("BoxEditImage")
        self.BoxEditImage.setProperty("class", "imageBox")

        self.imagesGrid.addWidget(self.BoxMetadataImage, 2, 0)
        self.imagesGrid.addWidget(self.BoxEditImage, 2, 1)

        # 3) Add the grid to the center layout
        self.centerLayout.addLayout(self.imagesGrid)

        # ---- Fullscreen/Maximize buttons in corners of each image (optional) ----
        self.ButtonMaximize1 = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonMaximize1.setIcon(QtGui.QIcon("Assets/icons8-expand-50.png"))
        self.ButtonMaximize1.setObjectName("ButtonMaximize1")
        self.ButtonMaximize1.setProperty("class", "maximizeButton")
        self.imagesGrid.addWidget(self.ButtonMaximize1, 0, 0, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        self.ButtonMaximize2 = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonMaximize2.setIcon(QtGui.QIcon("Assets/icons8-expand-50.png"))
        self.ButtonMaximize2.setObjectName("ButtonMaximize2")
        self.ButtonMaximize2.setProperty("class", "maximizeButton")
        self.imagesGrid.addWidget(self.ButtonMaximize2, 0, 1, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        self.ButtonMaximize3 = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonMaximize3.setIcon(QtGui.QIcon("Assets/icons8-expand-50.png"))
        self.ButtonMaximize3.setObjectName("ButtonMaximize3")
        self.ButtonMaximize3.setProperty("class", "maximizeButton")
        self.imagesGrid.addWidget(self.ButtonMaximize3, 2, 1, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        self.ButtonMaximize4 = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonMaximize4.setIcon(QtGui.QIcon("Assets/icons8-expand-50.png"))
        self.ButtonMaximize4.setObjectName("ButtonMaximize4")
        self.ButtonMaximize4.setProperty("class", "maximizeButton")
        self.imagesGrid.addWidget(self.ButtonMaximize4, 2, 0, alignment=QtCore.Qt.AlignTop | QtCore.Qt.AlignRight)

        # ============= RIGHT COLUMN: Bounding Boxes & Copy/Delete =============
        self.TextBoundingBox = QtWidgets.QLabel(self.centralwidget)
        self.TextBoundingBox.setAlignment(QtCore.Qt.AlignCenter)
        self.TextBoundingBox.setObjectName("TextBoundingBox")
        self.rightLayout.addWidget(self.TextBoundingBox)

        # Upper bounding box scroll area
        self.ListBoundingBoxRightUpper = QtWidgets.QScrollArea(self.centralwidget)
        self.ListBoundingBoxRightUpper.setWidgetResizable(True)
        self.ListBoundingBoxRightUpper.setObjectName("ListBoundingBoxRightUpper")
        self.ListBoundingBoxRightUpper.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # Add a widget to the scroll area
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.boxLayout2 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.BoxList2 = QtWidgets.QListView(self.scrollAreaWidgetContents_2)
        self.BoxList2.setObjectName("BoxList2")
        self.boxLayout2.addWidget(self.BoxList2)
        self.ListBoundingBoxRightUpper.setWidget(self.scrollAreaWidgetContents_2)
        self.rightLayout.addWidget(self.ListBoundingBoxRightUpper)

        # Copy / Delete buttons in one row
        copyDeleteLayout = QtWidgets.QHBoxLayout()
        self.ButtonCopy = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonCopy.setObjectName("ButtonCopy")
        self.ButtonDelete = QtWidgets.QPushButton(self.centralwidget)
        self.ButtonDelete.setObjectName("ButtonDelete")
        copyDeleteLayout.addWidget(self.ButtonCopy)
        copyDeleteLayout.addWidget(self.ButtonDelete)
        self.rightLayout.addLayout(copyDeleteLayout)

        # Lower bounding box scroll area
        self.ListBoundingBoxRightLower = QtWidgets.QScrollArea(self.centralwidget)
        self.ListBoundingBoxRightLower.setWidgetResizable(True)
        self.ListBoundingBoxRightLower.setObjectName("ListBoundingBoxRightLower")
        self.ListBoundingBoxRightLower.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.scrollAreaWidgetContents_3 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_3.setObjectName("scrollAreaWidgetContents_3")
        boxLayout3 = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents_3)
        self.BoxList3 = QtWidgets.QListView(self.scrollAreaWidgetContents_3)
        self.BoxList3.setObjectName("BoxList3")
        boxLayout3.addWidget(self.BoxList3)
        self.ListBoundingBoxRightLower.setWidget(self.scrollAreaWidgetContents_3)
        self.rightLayout.addWidget(self.ListBoundingBoxRightLower)

        # ============= STRETCH FACTORS =============
        # Make left column narrower, center wider, right medium
        self.mainLayout.setStretch(0, 1)  # left
        self.mainLayout.setStretch(1, 3)  # center
        self.mainLayout.setStretch(2, 1)  # right

        # Set the central widget layout
        WeldingDefectDetection.setCentralWidget(self.centralwidget)


        # ====== Add both widgets to the stacked layout =========
        self.stackedLayout.addWidget(self.welcomeWidget)  # index 0
        self.stackedLayout.addWidget(self.mainWidget)     # index 1

        # Show welcome screen initially
        self.stackedLayout.setCurrentIndex(0)

        # ============= MENUBAR, STATUSBAR =============
        self.menubar = QtWidgets.QMenuBar(WeldingDefectDetection)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1173, 20))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuGenerateReport = QtWidgets.QMenu(self.menubar)
        self.menuGenerateReport.setObjectName("menuGenerateReport")
        WeldingDefectDetection.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(WeldingDefectDetection)
        self.statusbar.setObjectName("statusbar")
        WeldingDefectDetection.setStatusBar(self.statusbar)

        # Create Open File action
        self.actionOpenFile = QtWidgets.QAction(WeldingDefectDetection)
        self.actionOpenFile.setObjectName("actionOpenFile")
        self.menuFile.addAction(self.actionOpenFile)  # Add Open File to the File menu
        # Create Open Folder action
        self.actionOpen = QtWidgets.QAction(WeldingDefectDetection)
        self.actionOpen.setObjectName("actionOpen")
        self.menuFile.addAction(self.actionOpen)
        
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuGenerateReport.menuAction())

        # Add a theme toggle switch to the menu bar
        self.ButtonToggleTheme = QtWidgets.QPushButton(WeldingDefectDetection)
        self.ButtonToggleTheme.setObjectName("ButtonToggleTheme")
        self.ButtonToggleTheme.setCheckable(True)  # Make it toggleable
        self.ButtonToggleTheme.setChecked(False)  # Default to dark theme
        self.ButtonToggleTheme.setText("Dark Theme  ")  # Add text to the button
        self.ButtonToggleTheme.setIcon(QtGui.QIcon("Assets/icons8-night-50.png"))  # Default icon for dark theme
        self.ButtonToggleTheme.setIconSize(QtCore.QSize(18, 18))  # Adjust icon size
        self.ButtonToggleTheme.setLayoutDirection(QtCore.Qt.RightToLeft)  # Place icon before text
        self.menubar.setCornerWidget(self.ButtonToggleTheme, QtCore.Qt.TopRightCorner)

        # Connect the toggle button to the theme toggle method
        self.ButtonToggleTheme.clicked.connect(self.toggle_theme)

        # Set the menu bar to adjust its height automatically
        self.menubar.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        self.menubar.setMinimumHeight(0)  # Allow the height to shrink if needed
        self.menubar.setFixedHeight(41)  # Adjust the height as needed

        # ============= CONNECT SIGNALS =============
        self.actionOpen.triggered.connect(self.open_directory)
        self.ButtonMaximize1.clicked.connect(lambda: self.open_sub_window(getattr(self, "current_image_path", ""), OriginalImageWindow))
        self.ButtonMaximize2.clicked.connect(lambda: self.open_sub_window(getattr(self, "detected_image_path", ""), DetectedImageWindow))
        self.ButtonMaximize3.clicked.connect(self.maximize_image)
        self.ButtonMaximize4.clicked.connect(self.maximize_image)
        self.ListPhotoGallery.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.ButtonSelectModel.currentIndexChanged.connect(self.select_model)
        self.ButtonDetectDefect.clicked.connect(self.execute_model)
        self.ButtonCopy.clicked.connect(self.copy_coordinates)
        self.ButtonDelete.clicked.connect(self.delete_selected_coordinates)
        self.actionOpenFile.triggered.connect(self.open_file)  # Connect Open File action to a method
        self.ButtonToggleTheme.clicked.connect(self.toggle_theme)  # Connect theme toggle button

        # Keep track of images for lazy loading
        self.image_paths = []
        self.loaded_images_count = 0
        self.chunk_size = 20
        self.selected_model = None

        self.retranslateUi(WeldingDefectDetection)
        QtCore.QMetaObject.connectSlotsByName(WeldingDefectDetection)

    def retranslateUi(self, WeldingDefectDetection):
        _translate = QtCore.QCoreApplication.translate
        WeldingDefectDetection.setWindowTitle(_translate("WeldingDefectDetection", "Welding Defect Detection"))
        # self.BoxOriginalImage.setText(_translate("WeldingDefectDetection", "Original Image"))
        self.show_original_image_in_box1("Assets/box1.png")
        self.TextFileName.setText(_translate("WeldingDefectDetection", "FileName"))
        # self.BoxDetectedImage.setText(_translate("WeldingDefectDetection", "Detected Image"))
        self.BoxMetadataImage.setText(_translate("WeldingDefectDetection", "Metadata Window"))
        self.BoxEditImage.setText(_translate("WeldingDefectDetection", "Edit Window"))
        self.show_detected_image_in_box2("Assets/box2.png")
        self.show_eiditable_image_in_box3('Assets/box3.png')
        display_bbox(self, '_', boxLayout2=self.boxLayout2, bounding_boxes='--instructions--', cls='_', cf='_')
        # self.ButtonSelectModel.setItemText(0, _translate("WeldingDefectDetection", "Model 1"))
        # self.ButtonSelectModel.setItemText(1, _translate("WeldingDefectDetection", "Model 2"))
        # self.ButtonSelectModel.setItemText(2, _translate("WeldingDefectDetection", "Model 3"))
        self.ButtonSelectModel.addItems(["Model 1", "Model 2", "Model 3"])
        self.ButtonDetectDefect.setText(_translate("WeldingDefectDetection", "Detect Defects"))
        self.ButtonEditImage.setText(_translate("WeldingDefectDetection", "Edit"))
        self.TextBoundingBox.setText(_translate("WeldingDefectDetection", "Bounding Boxes"))
        self.ButtonCopy.setText(_translate("WeldingDefectDetection", "Copy"))
        self.ButtonDelete.setText(_translate("WeldingDefectDetection", "Delete"))
        self.menuFile.setTitle(_translate("WeldingDefectDetection", "File"))
        self.menuGenerateReport.setTitle(_translate("WeldingDefectDetection", "Generate Report"))
        # self.actionOpen.setText(_translate("WeldingDefectDetection", "Open"))
        self.actionOpenFile.setText(_translate("WeldingDefectDetection", "Open File"))  # Add Open File option
        self.actionOpen.setText(_translate("WeldingDefectDetection", "Open Folder        "))  # Rename Open to Open Folder
        # 4. After all widgets are created, match button height to TextFileName
        self.LeftButtonFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        button_height = self.TextFileName.sizeHint().height()
        # width = self.ListPhotoGallery.width()
        # self.LeftButtonFrame.setMinimumWidth(width)
        # self.LeftButtonFrame.setMaximumWidth(width)
        self.LeftTopButton1.setFixedHeight(button_height)
        self.LeftTopButton2.setFixedHeight(button_height)




    def update_threshold_text_label(self, value):
        """Updates the Threshold text label based on the slider value."""
        threshold = value / 100.0  # Scale the slider value to 0-1
        self.ThresholdTextLabel.setText(f"Threshold: {threshold:.2f}")  # Update the label text
        
    # ---------------------------------------------------------
    #                METHODS FOR FILE OPERATIONS
    # ---------------------------------------------------------
    def open_directory(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(None, "Select Folder")
        if folder:
            self.stackedLayout.setCurrentIndex(1)  # Show main UI
            self.load_images(folder)

    def load_images(self, folder):
        # Clear previous thumbnails
        while self.imageListLayout.count():
            child = self.imageListLayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif'}
        self.image_paths = [
            os.path.join(folder, filename)
            for filename in os.listdir(folder)
            if any(filename.lower().endswith(ext) for ext in image_extensions)
        ]
        self.loaded_images_count = 0
        self.load_next_chunk()
    
    def on_scroll(self):
        if self.ListPhotoGallery.verticalScrollBar().value() == self.ListPhotoGallery.verticalScrollBar().maximum():
            self.load_next_chunk()

    def load_next_chunk(self):
        for _ in range(self.chunk_size):
            if self.loaded_images_count < len(self.image_paths):
                image_path = self.image_paths[self.loaded_images_count]
                self.add_thumbnail(image_path)
                self.loaded_images_count += 1

    def add_thumbnail(self, image_path):
        pixmap = QtGui.QPixmap(image_path)
        size = self.ListPhotoGallery.size()
        width = size.width()-60
        pixmap = pixmap.scaled(width, width, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.label = QtWidgets.QLabel()
        self.label.setObjectName("thumbnailLabel")
        self.label.setPixmap(pixmap)
        # self.label.setStyleSheet("background-color: rgba(255, 238, 223, 0.5);")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.mousePressEvent = lambda event, path=image_path: self.show_original_image_in_box1(path)
        self.imageListLayout.addWidget(self.label)

    # def show_original_image_in_box1(self, image_path):
    #     self.current_image_path = image_path
    #     pixmap = QtGui.QPixmap(image_path)
    #     pixmap = pixmap.scaled(self.BoxOriginalImage.width(), self.BoxOriginalImage.height(),
    #                            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
    #     self.BoxOriginalImage.setScaledContents(True)
    #     self.BoxOriginalImage.setSizePolicy(QtWidgets.QSizePolicy.Expanding, 
    #                                 QtWidgets.QSizePolicy.Expanding)
    #     self.BoxOriginalImage.setPixmap(pixmap)

    #     file_name = os.path.basename(image_path)
    #     path = os.path.dirname(image_path)
    #     self.TextFileName.setText(f"{path} ({file_name})")

    def show_original_image_in_box1(self, image_path):
        self.current_image_path = image_path
        pixmap = QtGui.QPixmap(image_path)
        original_width = pixmap.width()
        original_height = pixmap.height()

        # Get maximum available dimensions from the container
        # max_width = self.BoxOriginalImage.width()
        # max_height = self.BoxOriginalImage.height()

        max_width = 490
        max_height = 446

        # Calculate the scale factor to fit the pixmap within the container
        scale_factor = min(max_width / original_width, max_height / original_height)

        # Compute the new dimensions keeping the aspect ratio intact
        container_width = int(original_width * scale_factor)
        container_height = int(original_height * scale_factor)

        # Wrap dimensions in a QSize and scale the pixmap.
        scaled_pixmap = pixmap.scaled(
            QtCore.QSize(container_width, container_height),
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.BoxOriginalImage.setPixmap(scaled_pixmap)
        self.BoxOriginalImage.setAlignment(QtCore.Qt.AlignCenter)  # Align the pixmap to the center
        # Scale the pixmap to the computed dimensions
        # scaled_pixmap = pixmap.scaled(container_width, container_height,
        #                             # QtCore.Qt.KeepAspectRatio, 
        #                             QtCore.Qt.SmoothTransformation)

        file_name = os.path.basename(image_path)
        path = os.path.dirname(image_path)
        self.TextFileName.setText(f"{path} ({file_name})")

    def show_detected_image_in_box2(self, image):
        self.detected_image_path = image
        if isinstance(image, Image.Image):
            image = image.convert("RGBA")
            data = image.tobytes("raw", "RGBA")
            qimage = QtGui.QImage(data, image.width, image.height, QtGui.QImage.Format_RGBA8888)
            pixmap = QtGui.QPixmap.fromImage(qimage)
        else:
            pixmap = QtGui.QPixmap(image)

        max_width = 490
        max_height = 446
        original_width = pixmap.width()
        original_height = pixmap.height()
        # Calculate the scale factor to fit the pixmap within the container
        scale_factor = min(max_width / original_width, max_height / original_height)

        # Compute the new dimensions keeping the aspect ratio intact
        container_width = int(original_width * scale_factor)
        container_height = int(original_height * scale_factor)

        # Wrap dimensions in a QSize and scale the pixmap.
        scaled_pixmap = pixmap.scaled(
            QtCore.QSize(container_width, container_height),
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.BoxDetectedImage.setPixmap(scaled_pixmap)
        self.BoxDetectedImage.setAlignment(QtCore.Qt.AlignCenter)  # Align the pixmap to the center


    def show_eiditable_image_in_box3(self, pixmap_or_path):
        # If it's a QPixmap, just scale it
        if isinstance(pixmap_or_path, QtGui.QPixmap):
            pixmap = pixmap_or_path
        else:
            pixmap = QtGui.QPixmap(pixmap_or_path)

        max_width = 490
        max_height = 446

        original_width = pixmap.width()
        original_height = pixmap.height()
        scale_factor = min(max_width / original_width, max_height / original_height)

        container_width = int(original_width * scale_factor)
        container_height = int(original_height * scale_factor)

        scaled_pixmap = pixmap.scaled(
            QtCore.QSize(container_width, container_height),
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.BoxEditImage.setPixmap(scaled_pixmap)
        self.BoxEditImage.setAlignment(QtCore.Qt.AlignCenter)

    def maximize_image(self):
        if hasattr(self, 'current_image_path'):
            self.fullscreen_window = QtWidgets.QWidget()
            self.fullscreen_window.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
            self.fullscreen_window.showFullScreen()

            layout = QtWidgets.QVBoxLayout(self.fullscreen_window)
            label = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(self.current_image_path)
            label.setPixmap(pixmap)
            label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(label)

            button_layout = QtWidgets.QHBoxLayout()
            close_button = QtWidgets.QPushButton("Close")
            close_button.clicked.connect(self.close_fullscreen)
            resize_button = QtWidgets.QPushButton("Resize")
            resize_button.clicked.connect(self.resize_fullscreen)
            button_layout.addWidget(close_button)
            button_layout.addWidget(resize_button)
            layout.addLayout(button_layout)

            self.fullscreen_window.show()

    def close_fullscreen(self):
        self.fullscreen_window.close()

    def resize_fullscreen(self):
        self.fullscreen_window.showNormal()

    def open_sub_window(self, image_path, window_class):
        self.sub_window = window_class(image_path)
        self.sub_window.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.sub_window.show()

    def select_model(self, index):
        model_name = self.ButtonSelectModel.itemText(index)
        if model_name == "Model1":
            self.selected_model = "yolo"
        elif model_name == "Model2":
            self.selected_model = "model2"
        elif model_name == "Model3":
            self.selected_model = "model3"
        else:
            self.selected_model = None

    def execute_model(self):
        if not hasattr(self, 'current_image_path') or not self.current_image_path:
            print("Error: No image selected. Please select an image first.")
            return

        if not self.selected_model:
            result = self.run_yolo_model(self.current_image_path)
            try:
                original, detected, bbox = result
            except Exception as e:
                print("Failed to parse model output:", e)
                return

            if original and detected:
                self.show_detected_image_in_box2(detected)
                self.show_eiditable_image_in_box3(self.current_image_path)
            else:
                print("Failed to detect defects.")
            return

        if self.selected_model == "yolo":
            result = self.run_yolo_model(self.current_image_path)
            try:
                original, detected, bbox = result
            except Exception as e:
                print("Failed to parse model output:", e)
                return

            if original and detected:
                self.show_detected_image_in_box2(detected)
                self.show_eiditable_image_in_box3(self.current_image_path)
            else:
                print("Failed to detect defects.")
        elif self.selected_model == "model2":
            print("Model2 execution not implemented.")
        elif self.selected_model == "model3":
            print("Model3 execution not implemented.")


    


    def run_yolo_model(self, input_image_path):
        command = [
            'conda', 'run', '-n', 'yolo', 'python', '-c',
            (
                'from models.model import DefectDetector; '
                'detector = DefectDetector(); '
                f'original, detected, bbox, confidence, classs = detector.run(r"{input_image_path}"); '
                'pass'
            )
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        stdout = result.stdout.strip()
        if not stdout:
            print("No output from subprocess. Error:", result.stderr)
            return None, None, None

        lines = stdout.splitlines()
        file_line = None
        for line in reversed(lines):
            if '/' in line:
                file_line = line.strip()
                break

        if not file_line:
            print("No valid file path line found in output.")
            return None, None, None
        
        # Extract confidence scores
        confidence_scores = []
        # Use regex to find the confidence scores in the last line of output
        conf_match = re.search(r'(\[[\d.,\s]+\])\s+\[[\d.,\s]+\]$', stdout.strip(), re.MULTILINE)
        if conf_match:
            conf_str = conf_match.group(1)
            confidence_scores = ast.literal_eval(conf_str)
            print("Confidence Scores:", confidence_scores)

        # Extract class labels
        class_labels = []
        # Use regex to find the class labels in the last line of output
        class_match = re.search(r'\[[\d.,\s]+\]\s+(\[[\d.,\s]+\])$', stdout.strip(), re.MULTILINE)
        if class_match:
            class_str = class_match.group(1)
            class_labels = ast.literal_eval(class_str)
            print("Class Labels:", class_labels)
        
        # Extract bounding boxes
        match = re.search(r'(\[\[.*\]\])', stdout)
        if match:
            bbox_str = match.group(1)
            # Convert the string representation to a Python list safely
            bboxes = ast.literal_eval(bbox_str)
            print(bboxes)
            bboxes_tuple = [tuple(i) for i in bboxes]
            # for i in bboxes:

            display_bbox(self, self.current_image_path, boxLayout2=self.boxLayout2, bounding_boxes=bboxes_tuple, cls=class_labels, cf=confidence_scores)
        else:
            bboxes_tuple = []
            class_labels = []
            display_bbox(self, self.current_image_path, boxLayout2=self.boxLayout2, bounding_boxes=bboxes_tuple, cls=class_labels, cf=confidence_scores)
            print("No bounding boxes found.")
            

        try:
            orig_path, det_path = file_line.split()[:2]
        except Exception as e:
            print("Error parsing file paths:", e)
            return None, None, None

        try:
            original_image = Image.open(orig_path)
            detected_image = Image.open(det_path)
        except Exception as e:
            print("Error loading images with PIL:", e)
            return None, None, None

        return orig_path, det_path, bboxes_tuple
    
    def copy_coordinates(self):
        # Clear existing items in boxLayout3
        while self.ListBoundingBoxRightLower.widget().layout().count() > 0:
            child = self.ListBoundingBoxRightLower.widget().layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Iterate through boxLayout2 and copy coordinates to boxLayout3
        for i in range(1, self.boxLayout2.count()):  # Skip the "Select All" checkbox
            item = self.boxLayout2.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if not widget:
                continue

            # Find the checkbox and label in the widget
            checkbox = widget.findChild(QtWidgets.QCheckBox, "CheckBox_bbox")
            label = widget.findChild(QtWidgets.QLabel)

            if checkbox and label:
                # Create a new container for boxLayout3
                container = QtWidgets.QWidget()
                v_layout = QtWidgets.QVBoxLayout(container)
                v_layout.setContentsMargins(0, 0, 0, 0)
                v_layout.setSpacing(2)

                # Create a new checkbox with the same properties
                new_checkbox = QtWidgets.QCheckBox(checkbox.text())
                new_checkbox.setObjectName("CheckBox_bbox")
                new_checkbox.setStyleSheet(checkbox.styleSheet())
                new_checkbox.setChecked(checkbox.isChecked())
                new_checkbox.setProperty("bbox", checkbox.property("bbox"))
                new_checkbox.setProperty("defect_class", checkbox.property("defect_class"))
                new_checkbox.setProperty("confidence", checkbox.property("confidence"))  # Add confidence if stored

                # Create a new label with the same text
                new_label = QtWidgets.QLabel(label.text())
                new_label.setStyleSheet(label.styleSheet())

                # Add the checkbox and label to the new container
                v_layout.addWidget(new_checkbox)
                v_layout.addWidget(new_label)

                # Add the container to boxLayout3
                self.ListBoundingBoxRightLower.widget().layout().addWidget(container)

    def remove_bbox_from_image(self, bbox_to_remove):
        # Collect all remaining bounding boxes
        remaining_bboxes = []
        remaining_confidences = []
        remaining_classes = []

        # Iterate through the items in boxLayout3 to collect remaining bounding boxes
        layout = self.ListBoundingBoxRightLower.widget().layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if not widget:
                continue

            checkbox = widget.findChild(QtWidgets.QCheckBox, "CheckBox_bbox")
            if checkbox:
                current_bbox = checkbox.property("bbox")
                defect_class = checkbox.property("defect_class")
                confidence = checkbox.property("confidence")  # Add confidence if stored
                if current_bbox and current_bbox != bbox_to_remove:
                    remaining_bboxes.append(current_bbox)
                    remaining_classes.append(defect_class)
                    remaining_confidences.append(confidence)

        # Use display_bbox to redraw the image with the remaining bounding boxes
        display_bbox(
            parent=self,
            image_path=self.current_image_path,
            boxLayout2=self.ListBoundingBoxRightLower.widget().layout(),
            bounding_boxes=remaining_bboxes,
            cf=remaining_confidences,
            cls=remaining_classes
        )

    def delete_selected_coordinates(self):
        # Get the layout of boxLayout3
        layout = self.ListBoundingBoxRightLower.widget().layout()

        # Iterate through the items in reverse order to avoid index shifting issues
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if not widget:
                continue

            # Find the checkbox in the widget
            checkbox = widget.findChild(QtWidgets.QCheckBox, "CheckBox_bbox")
            if checkbox and checkbox.isChecked():
                # Remove the widget from the layout and delete it
                layout.takeAt(i)
                widget.deleteLater()

                # Optionally, update the image to remove the corresponding bounding box
                bbox = checkbox.property("bbox")
                if bbox:
                    self.remove_bbox_from_image(bbox)

    def open_file(self):
        """Opens a single file."""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select File", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.show_original_image_in_box1(file_path)  # Display the selected file in the Original Image box

    def toggle_theme(self):
        """Toggles the theme between dark and light."""
        if self.ButtonToggleTheme.isChecked():
            # Switch to light theme
            new_stylesheet = "new.qss"
            self.ButtonToggleTheme.setIcon(QtGui.QIcon("Assets/icons8-sun-50.png"))  # Light theme icon
            self.ButtonToggleTheme.setText("Light Theme  ")  # Update text to Day Theme
        else:
            # Switch to dark theme
            new_stylesheet = "styled.qss"
            self.ButtonToggleTheme.setIcon(QtGui.QIcon("Assets/icons8-night-50.png"))  # Dark theme icon
            self.ButtonToggleTheme.setText("Dark Theme  ")  # Update text to Night Theme

        style_path = os.path.join(os.path.dirname(__file__), "utils", new_stylesheet)

        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                stylesheet = f.read()
                QtWidgets.QApplication.instance().setStyleSheet(stylesheet)
                print(f"Switched to {new_stylesheet}")
                self.current_stylesheet = new_stylesheet
        else:
            print(f"Error: {new_stylesheet} not found.")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Apply stylesheet
    style_path = os.path.join(os.path.dirname(__file__), "utils", "styled.qss")
    if os.path.exists(style_path):
        with open(style_path, "r") as f:
            stylesheet = f.read()
            print("Applying stylesheet...")
            app.setStyleSheet(stylesheet)

    # app.setStyleSheet(APP_STYLE)

    WeldingDefectDetection = QtWidgets.QMainWindow()
    ui = Ui_WeldingDefectDetection()
    ui.setupUi(WeldingDefectDetection)
    WeldingDefectDetection.show()
    sys.exit(app.exec_())