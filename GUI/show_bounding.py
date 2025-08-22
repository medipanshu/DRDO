# show_bounding.py
from PyQt5 import QtWidgets, QtCore, QtGui

def display_bbox(parent, image_path, boxLayout2, bounding_boxes, cf, cls):
    """
    Expects bounding_boxes to be a list of tuples: [(x, y, w, h), ...]
    Clears existing bounding box items and creates a new entry for each bounding box,
    with the checkbox above the coordinates.
    """
    # Dictionary to store colors for each bounding box
    if bounding_boxes=='--instructions--':
        while boxLayout2.count() > 0:
            child = boxLayout2.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Container for each row
        container = QtWidgets.QWidget()
        v_layout = QtWidgets.QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        # The checkbox
        select_all_checkbox = QtWidgets.QCheckBox("Select All")
        select_all_checkbox.setStyleSheet("font-size: 16px; color: blue;")
        select_all_checkbox.setObjectName("CheckBox_SelectAll")
        checkbox = QtWidgets.QCheckBox(f"Box: 1")
        checkbox.setObjectName("CheckBox_bbox")
        checkbox.setStyleSheet(f"font-size: 16px; color: red;")
        checkbox.setChecked(False)

        # Store the bounding box and defect class on the checkbox
        # checkbox.setProperty("bbox", (x, y, w, h))
        # checkbox.setProperty("defect_class", defect_class_name)
        # checkbox.setProperty("confidence", confidence)

        # The label showing coordinates, confidence, and defect type
        label = QtWidgets.QLabel(
            "<b>Instructions:</b><br>"
            "1. Select a folder containing images to begin.<br>"
            "2. The images will be displayed in the left image viewer panel.<br>"
            "3. Click on any image in the viewer to load it for analysis.<br>"
            "4. The selected image will appear in the first (original image) display box.<br>"
            "5. Choose a model from the model selection dropdown.<br>"
            "6. Adjust the detection threshold using the provided slider.<br>"
            "7. Click the <b>Detect Defects</b> button to run the defect detection algorithm.<br>"
            "8. The processed image with detected defects will be displayed in the second (detected image) box."
        )
        label.setWordWrap(True)
        label.setStyleSheet("margin: 0; padding: 0.5;")

        # Add the checkbox and label
        v_layout.addWidget(select_all_checkbox)
        v_layout.addWidget(checkbox)
        v_layout.addWidget(label)

        # Add the container to the layout
        boxLayout2.addWidget(container)
    
    else:

        bbox_colors = {}
        conf_scores = {}

        # Clear existing items in the layout.
        while boxLayout2.count() > 0:
            child = boxLayout2.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # If no bounding boxes, show a message and return early.
        if not bounding_boxes:
            no_defect_label = QtWidgets.QLabel("No defect detected")
            no_defect_label.setStyleSheet("font-size: 16px; color: red;")
            no_defect_label.setAlignment(QtCore.Qt.AlignCenter)
            boxLayout2.addWidget(no_defect_label)
            return

        class_names = ['crack', 'lof', 'lop', 'overlap', 'porosity', 'slag', 'spattering', 'undercut']
        class_colors = {
                'crack': (255, 0, 0),       # Red
                'lof': (0, 255, 0),         # Green
                'lop': (0, 0, 255),         # Blue
                'overlap': (255, 255, 0),   # Cyan
                'porosity': (255, 0, 255),  # Magenta
                'slag': (0, 255, 255),      # Yellow
                'spattering': (128, 0, 128),# Purple
                'undercut': (0, 128, 128)   # Teal
            }

        # Define the redraw function
        def redraw_all_rectangles():
            # Load the original image as QPixmap.
            original_pixmap = QtGui.QPixmap(image_path)

            # Begin painting on the original image.
            painter = QtGui.QPainter(original_pixmap)
            painter.setFont(QtGui.QFont("Arial", 12))  # Set font for the class text

            # Loop through each bounding-box checkbox and draw if it's checked.
            for i in range(1, boxLayout2.count()):
                item = boxLayout2.itemAt(i)
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
                        color = bbox_colors.get(bbox, (255, 255, 255))  # Default to white if not found
                        confidence = conf_scores.get(bbox, 0.0)  # Default to 0.0 if not found
                        pen = QtGui.QPen(QtGui.QColor(*color))  # Use the stored color
                        pen.setWidth(2)  # Set the rectangle border width
                        painter.setPen(pen)

                        # Draw the rectangle on the original image using original coordinates.
                        painter.drawRect(int(x), int(y), int(w - x), int(h - y))

                        # Draw the defect class text above the rectangle
                        # painter.drawText(int(x), int(y) - 5, defect_class)  # Position text slightly above the rectangle
                        txt = f"Class: {defect_class} (Cnf: {confidence:.2f})"
                        painter.drawText(int(x), int(y) - 5, txt)  # Position text slightly above the rectangle

            painter.end()

            # Now scale the whole image (with the drawn rectangles and text) to fit the display widget.
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

            # Update BoxEditImage using the parent's method.
            parent.show_eiditable_image_in_box3(scaled_pixmap)

        # Add "Select All" checkbox
        def toggle_all(state):
            for i in range(1, boxLayout2.count()):  # Skip the "Select All" row
                item = boxLayout2.itemAt(i)
                if not item:
                    continue
                widget = item.widget()
                if not widget:
                    continue

                checkbox = widget.findChild(QtWidgets.QCheckBox, "CheckBox_bbox")
                if checkbox:
                    checkbox.setChecked(state == QtCore.Qt.Checked)

            # After toggling them all, redraw
            redraw_all_rectangles()

        select_all_checkbox = QtWidgets.QCheckBox("Select All")
        select_all_checkbox.setStyleSheet("font-size: 16px; color: blue;")
        select_all_checkbox.setObjectName("CheckBox_SelectAll")
        select_all_checkbox.stateChanged.connect(toggle_all)
        boxLayout2.addWidget(select_all_checkbox)

        # Add each bounding box row
        for idx, (bbox, confidence, defect_class) in enumerate(zip(bounding_boxes, cf, cls), start=1):
            x, y, w, h = bbox
            try:
                defect_class_name = class_names[int(defect_class)]
            except ValueError:
                defect_class_name = defect_class
            
            color = class_colors[defect_class_name]

            # Store the color for this bounding box
            bbox_colors[bbox] = color
            conf_scores[bbox] = confidence

            # Container for each row
            container = QtWidgets.QWidget()
            v_layout = QtWidgets.QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(2)

            # The checkbox
            checkbox = QtWidgets.QCheckBox(f"Box: {idx}")
            checkbox.setObjectName("CheckBox_bbox")
            checkbox.setStyleSheet(f"font-size: 16px; color: red;")
            checkbox.setChecked(False)

            # Store the bounding box and defect class on the checkbox
            checkbox.setProperty("bbox", (x, y, w, h))
            checkbox.setProperty("defect_class", defect_class_name)
            checkbox.setProperty("confidence", confidence)

            # Connect the checkbox to the redraw function
            checkbox.stateChanged.connect(lambda state: redraw_all_rectangles())

            # The label showing coordinates, confidence, and defect type
            label = QtWidgets.QLabel(f"<b>Type of Defect:</b> {defect_class_name}<br>"
                                    f"<b>Confidence Scores</b>: {confidence}<br>"
                                    f"<b>x:</b> {x}<br>"
                                    f"<b>y:</b> {y}<br>"
                                    f"<b>w:</b> {w}<br>"
                                    f"<b>h:</b> {h}")
            label.setStyleSheet("margin: 0; padding: 0.5;")

            # Add the checkbox and label
            v_layout.addWidget(checkbox)
            v_layout.addWidget(label)

            # Add the container to the layout
            boxLayout2.addWidget(container)
