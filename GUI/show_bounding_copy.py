from PyQt5 import QtWidgets, QtGui, QtCore


class BoundingBoxDisplay:
    def __init__(self, parent, image_path, boxLayout2):
        self.parent = parent
        self.image_path = image_path
        self.boxLayout2 = boxLayout2

        self.bbox_colors = {}
        self.conf_scores = {}

        self.class_names = ['crack', 'lof', 'lop', 'overlap', 'porosity', 'slag', 'spattering', 'undercut']
        self.class_colors = {
            'crack': (255, 0, 0),
            'lof': (0, 255, 0),
            'lop': (0, 0, 255),
            'overlap': (255, 255, 0),
            'porosity': (255, 0, 255),
            'slag': (0, 255, 255),
            'spattering': (128, 0, 128),
            'undercut': (0, 128, 128)
        }

    def display_bbox(self, bounding_boxes, cf, cls):
        self.clear_layout()

        if bounding_boxes == '--instructions--':
            self.display_instructions()
            return

        if not bounding_boxes:
            self.show_no_defect_message()
            return

        # Add "Select All" checkbox
        select_all_checkbox = QtWidgets.QCheckBox("Select All")
        select_all_checkbox.setStyleSheet("font-size: 16px; color: red;")
        select_all_checkbox.setObjectName("CheckBox_SelectAll")
        select_all_checkbox.stateChanged.connect(self.toggle_all)
        self.boxLayout2.addWidget(select_all_checkbox)

        for idx, (bbox, confidence, defect_class) in enumerate(zip(bounding_boxes, cf, cls), start=1):
            x, y, w, h = bbox

            try:
                defect_class_idx = int(defect_class)
                defect_class_name = self.class_names[defect_class_idx]
            except (ValueError, IndexError, TypeError):
                defect_class_name = str(defect_class).strip().lower()

            color = self.class_colors.get(defect_class_name, (255, 255, 255))  # white fallback
            self.bbox_colors[bbox] = color
            self.conf_scores[bbox] = confidence

            container = QtWidgets.QWidget()
            v_layout = QtWidgets.QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(2)

            checkbox = QtWidgets.QCheckBox(f"Box: {idx}")
            checkbox.setObjectName("CheckBox_bbox")
            checkbox.setStyleSheet("font-size: 16px; color: red;")
            checkbox.setChecked(False)

            checkbox.setProperty("bbox", (x, y, w, h))
            checkbox.setProperty("defect_class", defect_class_name)
            checkbox.setProperty("confidence", confidence)
            checkbox.setProperty("model_delected",1)

            checkbox.stateChanged.connect(lambda state, cb=checkbox: self.redraw_all_rectangles())

            label = QtWidgets.QLabel(
                f"<b> <span style='color:blue'>Type of Defect: </span></b> {defect_class_name}<br>"
                f"<b><span style='color:blue'>Confidence:</span></b> {confidence:.2f}<br>"
                f"<b><span style='color:blue'>x: </span></b> {x}<br>"
                f"<b><span style='color:blue'>y: </span></b> {y}<br>"
                f"<b><span style='color:blue'>w: </span></b> {w}<br>"
                f"<b><span style='color:blue'>h: </span></b> {h}"
            )
            # label.setStyleSheet("margin: 0; padding: 0.5; color: black;")
            label.setObjectName("checkBoxLabel")

            v_layout.addWidget(checkbox)
            v_layout.addWidget(label)

            self.boxLayout2.addWidget(container)

    def redraw_all_rectangles(self):
        original_pixmap = QtGui.QPixmap(self.image_path)
        painter = QtGui.QPainter(original_pixmap)
        painter.setFont(QtGui.QFont("Arial", 12))

        for i in range(1, self.boxLayout2.count()):
            item = self.boxLayout2.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if not widget:
                continue

            checkbox = widget.findChild(QtWidgets.QCheckBox, "CheckBox_bbox")
            if checkbox and checkbox.isChecked():
                bbox = checkbox.property("bbox")
                if bbox:
                    x, y, w, h = bbox
                    defect_class = checkbox.property("defect_class")
                    confidence = checkbox.property("confidence")
                    color = self.bbox_colors.get(bbox, (255, 255, 255))

                    pen = QtGui.QPen(QtGui.QColor(*color))
                    pen.setWidth(2)
                    painter.setPen(pen)

                    painter.drawRect(int(x), int(y), int(w), int(h))
                    txt = f"Class: {defect_class} (Cnf: {confidence:.2f})"
                    painter.drawText(int(x), int(y) - 5, txt)

        painter.end()

        max_width = 490
        max_height = 446
        original_width = original_pixmap.width()
        original_height = original_pixmap.height()
        scale_factor = min(max_width / original_width, max_height / original_height)

        scaled_pixmap = original_pixmap.scaled(
            QtCore.QSize(int(original_width * scale_factor), int(original_height * scale_factor)),
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation
        )

        self.parent.show_eiditable_image_in_box3(scaled_pixmap)

    def toggle_all(self, state):
        for i in range(1, self.boxLayout2.count()):
            item = self.boxLayout2.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if not widget:
                continue

            checkbox = widget.findChild(QtWidgets.QCheckBox, "CheckBox_bbox")
            if checkbox:
                checkbox.setChecked(state == QtCore.Qt.Checked)

        self.redraw_all_rectangles()
    
    def redraw_from_layout(self, layout):
        original_pixmap = QtGui.QPixmap(self.image_path)
        painter = QtGui.QPainter(original_pixmap)
        painter.setFont(QtGui.QFont("Arial", 12))

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not item:
                continue
            widget = item.widget()
            if not widget:
                continue

            checkbox = widget.findChild(QtWidgets.QCheckBox, "CheckBox_bbox")
            if checkbox and checkbox.isChecked():
                bbox = checkbox.property("bbox")
                defect_class = checkbox.property("defect_class")
                confidence = checkbox.property("confidence")
                if not bbox:
                    continue

                x, y, w, h = bbox
                color = self.class_colors.get(str(defect_class).lower(), (255, 255, 255))

                pen = QtGui.QPen(QtGui.QColor(*color))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(int(x), int(y), int(w), int(h))
                txt = f"Class: {defect_class} (Cnf: {confidence:.2f})"
                painter.drawText(int(x), int(y) - 5, txt)

        painter.end()

        # Scale to fit the display
        original_width = original_pixmap.width()
        original_height = original_pixmap.height()
        scale_factor = min(490 / original_width, 446 / original_height)

        scaled_pixmap = original_pixmap.scaled(
            QtCore.QSize(int(original_width * scale_factor), int(original_height * scale_factor)),
            QtCore.Qt.IgnoreAspectRatio,
            QtCore.Qt.SmoothTransformation
        )

        self.parent.show_eiditable_image_in_box3(scaled_pixmap)


    def clear_layout(self):
        while self.boxLayout2.count() > 0:
            child = self.boxLayout2.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def show_no_defect_message(self):
        label = QtWidgets.QLabel("No defect detected")
        # label.setStyleSheet("font-size: 16px; color: red;")
        label.setObjectName("checkBoxLabel")
        label.setAlignment(QtCore.Qt.AlignCenter)
        self.boxLayout2.addWidget(label)

    def _show_instructions(self):
        container = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        select_all_checkbox = QtWidgets.QCheckBox("Select All")
        select_all_checkbox.setStyleSheet("font-size: 16px; color: blue;")
        select_all_checkbox.setObjectName("CheckBox_SelectAll")

        checkbox = QtWidgets.QCheckBox("Box: 1")
        checkbox.setObjectName("CheckBox_bbox")
        checkbox.setStyleSheet("font-size: 16px; color: red;")

        label = QtWidgets.QLabel(
            "<b>Instructions:</b><br>"
            "1. Select a folder containing images to begin.<br>"
            "2. Images will appear in the left panel.<br>"
            "3. Click an image to load it for analysis.<br>"
            "4. Choose a model and adjust threshold.<br>"
            "5. Click <b>Detect Defects</b> to run detection.<br>"
            "6. Detected image will appear on the right."
        )
        label.setWordWrap(True)
        # label.setStyleSheet("margin: 0; padding: 0.5;")
        label.setObjectName("checkBoxLabel")

        v_layout.addWidget(select_all_checkbox)
        v_layout.addWidget(checkbox)
        v_layout.addWidget(label)

        self.boxLayout2.addWidget(container)
