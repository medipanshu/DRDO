from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QAction,
    QFileDialog, QColorDialog, QGraphicsTextItem, QInputDialog, QToolBar,
    QComboBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout, QWidget, QCheckBox, QPushButton, QMessageBox, QToolButton
)
from PyQt5.QtGui import (
    QPen, QBrush, QPixmap, QPainterPath, QFont, QImage, QPainter, QPolygonF,QColor, QCursor, QIcon
)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
import sys
from functools import partial

class PaintView(QGraphicsView):
    """
    Custom QGraphicsView to handle mouse events and forward them to the parent application.
    """
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.parent_app = parent
        self.setMouseTracking(True) # Enable mouse tracking for continuous coordinate updates

    def mousePressEvent(self, event):
        """
        Handles mouse press events. Starts drawing or erasing based on the current mode.
        """
        pos = self.mapToScene(event.pos()) # Map cursor position to scene coordinates
        if event.button() == Qt.LeftButton:
            self.parent_app.start_drawing(pos) # Call start_drawing in the main app
        super().mousePressEvent(event) # Call base class method

    def mouseMoveEvent(self, event):
        """
        Handles mouse move events. Updates cursor coordinates and continues drawing if active.
        """
        pos = self.mapToScene(event.pos()) # Map cursor position to scene coordinates
        # Always update coordinates if inside image
        if self.parent_app._inside_image(pos):
            self.parent_app.update_cursor_coords(pos)
        else:
            self.parent_app.update_cursor_coords(None)
        # Only call continue_drawing if a drawing operation is in progress
        if self.parent_app.drawing:
            self.parent_app.continue_drawing(pos)
        super().mouseMoveEvent(event) # Call base class method

    def mouseReleaseEvent(self, event):
        """
        Handles mouse release events. Finishes the current drawing operation.
        """
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos()) # Map cursor position to scene coordinates
            self.parent_app.finish_drawing(pos) # Call finish_drawing in the main app
        super().mouseReleaseEvent(event) # Call base class method

class PaintApp(QMainWindow):
    """
    Main application window for the PyQt5 Paint App.
    Allows loading images, drawing various shapes, erasing, and managing annotations.
    Includes undo/redo functionality and a checklist for drawn items.
    """
    save_result = pyqtSignal(object, list)  # Signal to emit QPixmap and checklist on save

    def __init__(self, bbox_checklist=None):
        super().__init__()
        # Get screen dimensions for fullscreen window
        screen = QApplication.primaryScreen().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        self.setWindowTitle("PyQt5 Paint App (Image Annotation Tool)")
        self.setGeometry(0, 0, screen_width, screen_height)

        self.scene = QGraphicsScene() # Graphics scene to hold drawing items and image
        self.view = PaintView(self.scene, parent=self) # Custom view for scene interaction

        # --- Right column with Select All button and Checklist ---
        self.coord_list = QListWidget() # Widget to display the list of drawn coordinates/annotations
        self.select_all_btn = QPushButton("Select All") # Button to select/unselect all annotations
        self.select_all_btn.setCheckable(True)
        self.select_all_btn.clicked.connect(self.toggle_select_all) # Connect to toggle function

        right_col_widget = QWidget() # Container for the right column layout
        right_col_layout = QVBoxLayout(right_col_widget)
        right_col_layout.setContentsMargins(0, 0, 0, 0)
        right_col_layout.setSpacing(4)
        right_col_layout.addWidget(self.select_all_btn)
        right_col_layout.addWidget(self.coord_list)

        main_widget = QWidget() # Main container for the central layout
        main_layout = QHBoxLayout(main_widget)
        main_layout.addWidget(self.view)
        main_layout.addWidget(right_col_widget)
        main_layout.setStretch(0, 4) # Allocate 4 parts of space to the view
        main_layout.setStretch(1, 1) # Allocate 1 part of space to the checklist
        self.setCentralWidget(main_widget)

        # Drawing & style defaults
        self.mode = None # Current drawing mode (e.g., "rectangle", "eraser")
        self.drawing = False # Flag to indicate if a drawing operation is in progress
        self.start_point = None # Starting point of a drawing operation
        self.temp_item = None # Temporary graphics item for live drawing preview
        self.current_path = None # For freehand drawing
        self.current_polygon = [] # For polygon drawing points
        self.pen_color, self.fill_color = Qt.black, Qt.transparent # Default pen and fill colors
        self.pen_width = 2 # Default pen width
        self.pen = QPen(self.pen_color, self.pen_width) # Pen object
        self.brush = QBrush(self.fill_color) # Brush object

        self.undo_stack = [] # Stack to store actions for undo functionality
        self.redo_stack = [] # Stack to store actions for redo functionality

        self.image_loaded = False # Flag to track if an image is loaded

        self.coord_label = QLabel("X: -, Y: -") # Label to display cursor coordinates
        self.statusBar().addPermanentWidget(self.coord_label) # Add to status bar

        self.last_image_pos = None # Stores the last valid cursor position within the image

        # Mapping between QGraphicsItem and QListWidgetItem for easy lookup
        self.item_to_listitem = {}  # QGraphicsItem -> QListWidgetItem

        # Predefined defect classes for annotations
        self.defect_classes = ['crack', 'lof', 'lop', 'overlap', 'porosity', 'slag', 'spattering', 'undercut']

        # Colors associated with each defect class
        self.class_colors = {
            'crack': (255, 0, 0),       # Red
            'lof': (0, 255, 0),         # Green
            'lop': (0, 0, 255),         # Blue
            'overlap': (255, 255, 0),   # Yellow
            'porosity': (255, 0, 255),  # Magenta
            'slag': (0, 255, 255),      # Cyan
            'spattering': (128, 0, 128),# Purple
            'undercut': (0, 128, 128)   # Teal
        }

        self._create_toolbar() # Initialize the toolbar
        # If a checklist is provided on initialization, add it to the coord_list
        if bbox_checklist:
            self.add_checklist_to_coord_list(bbox_checklist)

    def _create_toolbar(self):
        """
        Creates and populates the application's toolbar with various drawing tools and actions.
        """
        toolbar = QToolBar("Tools", self)
        toolbar.setMovable(False) # Prevent toolbar from being moved by the user
        self.addToolBar(toolbar)

        # Save action
        save_act = QAction(QIcon("Assets/icons8-save-60.png"), "Save", self)
        save_act.triggered.connect(self.save_drawing)
        toolbar.addAction(save_act)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("<b>Drawing Tools</b>")) # Label for drawing tools section

        # Rectangle drawing tool
        rect_act = QAction(QIcon("Assets/icons8-rectangle-50.png"), "Rectangle", self)
        rect_act.triggered.connect(lambda: self.set_mode("rectangle"))
        toolbar.addAction(rect_act)

        # Circle drawing tool
        circle_act = QAction(QIcon("Assets/icons8-circle-50.png"), "Circle", self)
        circle_act.triggered.connect(lambda: self.set_mode("circle"))
        toolbar.addAction(circle_act)

        # Polygon drawing tool
        poly_act = QAction(QIcon("Assets/icons8-polygon-50.png"), "Polygon", self)
        poly_act.triggered.connect(lambda: self.set_mode("polygon"))
        toolbar.addAction(poly_act)

        # Freehand drawing tool
        free_hand_act = QAction(QIcon("Assets/icons8-pencil-64.png"), "Freehand", self)
        free_hand_act.triggered.connect(lambda: self.set_mode("freehand"))
        toolbar.addAction(free_hand_act)

        # Eraser tool
        eraser_act = QAction(QIcon("Assets/icons8-eraser-48.png"), "Eraser", self)
        eraser_act.triggered.connect(lambda: self.set_mode("eraser"))
        toolbar.addAction(eraser_act)

        toolbar.addSeparator()

        # Pen color selection tool
        pen_act = QAction(QIcon("Assets/icons8-paint-palette-with-brush-48.png"), "Pen Color", self)
        pen_act.triggered.connect(self.select_pen_color)
        toolbar.addAction(pen_act)

        toolbar.addSeparator()
        toolbar.addWidget(QLabel("Width:")) # Label for pen width selection
        self.width_combo = QComboBox() # Dropdown for pen width
        self.width_combo.addItems([str(i) for i in (1,2,4,6,8,10)]) # Available pen widths
        self.width_combo.setCurrentText(str(self.pen_width)) # Set initial width
        self.width_combo.currentTextChanged.connect(lambda w: self.change_width(int(w))) # Connect to change_width
        toolbar.addWidget(self.width_combo)

        toolbar.addSeparator()

        # Zoom In button
        zoom_in_act = QAction(QIcon("Assets/icons8-zoom-in-64.png"), "Zoom In", self)
        zoom_in_act.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_act)

        # Zoom Out button
        zoom_out_act = QAction(QIcon("Assets/icons8-zoom-out-64.png"), "Zoom Out", self)
        zoom_out_act.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_act)

        toolbar.addSeparator()

        # Undo button
        undo_act = QAction(QIcon("Assets/icons8-undo-64 (1).png"), "Undo", self)
        undo_act.triggered.connect(self.undo)
        toolbar.addAction(undo_act)

        # Redo button
        redo_act = QAction(QIcon("Assets/icons8-redo-64.png"), "Redo", self)
        redo_act.triggered.connect(self.redo)
        toolbar.addAction(redo_act)

        self.addToolBar(toolbar)

    def set_mode(self, m):
        """
        Sets the current drawing mode and updates the cursor icon accordingly.
        """
        self.mode = m
        cursors = {
            "freehand": Qt.CrossCursor,
            "rectangle": Qt.SizeAllCursor,
            "circle": Qt.SizeBDiagCursor,
            "polygon": Qt.PointingHandCursor,
            "eraser": Qt.ForbiddenCursor,
            "text": Qt.IBeamCursor # Currently not used for text, but good to have
        }
        self.view.setCursor(cursors.get(m, Qt.ArrowCursor)) # Set cursor based on mode
        if m == "freehand":
            self.current_path = QPainterPath() # Initialize path for freehand drawing

    def change_width(self, w):
        """
        Changes the pen width.
        """
        self.pen_width = w
        self.pen.setWidth(w)

    def select_pen_color(self):
        """
        Opens a color dialog to select the pen color.
        """
        c = QColorDialog.getColor() # Get color from dialog
        if c.isValid(): # Check if a valid color was selected
            self.pen_color = c
            self.pen.setColor(c)

    def select_fill_color(self):
        """
        Opens a color dialog to select the fill color.
        """
        c = QColorDialog.getColor() # Get color from dialog
        if c.isValid(): # Check if a valid color was selected
            self.fill_color = c
            self.brush.setColor(c)
            # Set brush style to solid if alpha is > 0, otherwise no brush
            self.brush.setStyle(Qt.SolidPattern if c.alpha() > 0 else Qt.NoBrush)

    def _inside_image(self, pos):
        """
        Checks if a given QPointF is within the bounds of the loaded image.
        """
        if not self.image_loaded:
            return False # No image loaded, so no "inside"
        return self.scene.sceneRect().contains(pos) # Check if point is within scene rect

    def start_drawing(self, pos):
        """
        Initiates a drawing operation based on the current mode and mouse press position.
        """
        if not self._inside_image(pos):
            return # Do nothing if click is outside the image
        self.drawing, self.start_point = True, pos # Set drawing flag and start point
        m = self.mode # Get current mode

        if m == "freehand":
            self.current_path = QPainterPath(pos) # Start new path
            self.temp_item = self.scene.addPath(self.current_path, self.pen) # Add temp item for preview
        elif m == "polygon":
            self.current_polygon.append(pos) # Add point to polygon list
            if len(self.current_polygon) > 1:
                if self.temp_item: self.scene.removeItem(self.temp_item) # Remove previous temp poly
                poly = QPolygonF(self.current_polygon)
                self.temp_item = self.scene.addPolygon(poly, self.pen, self.brush) # Add new temp poly
            # Show polygon control buttons (tick/cross) if enough points are drawn
            if len(self.current_polygon) == 1:
                self.start_polygon(pos)
            elif len(self.current_polygon) >= 3:
                self.show_polygon_buttons(self.current_polygon[0]) # Update button position
        elif m == "eraser":
            self.erase_at(pos) # Immediately erase at the clicked position

    def continue_drawing(self, pos):
        """
        Continues a drawing operation as the mouse moves, updating the temporary item.
        """
        if not self._inside_image(pos) or not self.drawing:
            return # Do nothing if outside image or not drawing
        m, sp = self.mode, self.start_point # Get mode and start point

        if m == "freehand":
            self.current_path.lineTo(pos) # Extend freehand path
            if self.temp_item: self.scene.removeItem(self.temp_item) # Remove old temp path
            self.temp_item = self.scene.addPath(self.current_path, self.pen) # Add new temp path
            self.update_cursor_coords(pos)
        elif m == "rectangle":
            if self.temp_item: self.scene.removeItem(self.temp_item) # Remove old temp rect
            rect = QRectF(sp, pos).normalized() # Create normalized rectangle
            self.temp_item = self.scene.addRect(rect, self.pen, self.brush) # Add new temp rect
            x0, y0 = int(rect.x()), int(rect.y())
            w, h = int(rect.width()), int(rect.height())
            self.update_cursor_coords(pos, (x0, y0, w, h)) # Update coords with rect info
        elif m == "circle":
            if self.temp_item: self.scene.removeItem(self.temp_item) # Remove old temp circle
            rect = QRectF(sp, pos).normalized() # Create normalized bounding rect
            self.temp_item = self.scene.addEllipse(rect, self.pen, self.brush) # Add new temp circle
            self.update_cursor_coords(pos)
        elif m == "polygon":
            if self.temp_item: self.scene.removeItem(self.temp_item) # Remove old temp poly
            pts = self.current_polygon + [pos] # Add current mouse pos to polygon points
            self.temp_item = self.scene.addPolygon(QPolygonF(pts), self.pen, self.brush) # Add new temp poly
            self.update_cursor_coords(pos)

    def finish_drawing(self, pos):
        """
        Finalizes a drawing operation on mouse release.
        """
        if not self._inside_image(pos) or not self.drawing:
            return # Do nothing if outside image or not drawing
        self.drawing = False # Reset drawing flag
        m, sp = self.mode, self.start_point # Get mode and start point

        if m == "rectangle":
            if self.temp_item: self.scene.removeItem(self.temp_item) # Remove temp item
            rect = QRectF(sp, pos).normalized() # Get final rectangle
            x0, y0 = int(rect.x()), int(rect.y())
            w, h = int(rect.width()), int(rect.height())
            # Prompt user for defect type and confirm
            if not self.prompt_manual_model(None, "rectangle", (x0, y0, w, h)):
                return # If canceled, do not add to scene or undo stack
            self.temp_item = None
        elif m == "circle":
            if self.temp_item: self.scene.removeItem(self.temp_item) # Remove temp item
            rect = QRectF(sp, pos).normalized() # Get final bounding rect
            x0, y0 = int(rect.x()), int(rect.y())
            w, h = int(rect.width()), int(rect.height())
            if not self.prompt_manual_model(None, "circle", (x0, y0, w, h)):
                return # If canceled, do not add to scene or undo stack
            self.temp_item = None
        elif m == "freehand" and self.temp_item:
            points = [self.current_path.pointAtPercent(i/100.0) for i in range(101)] # Get points from path
            if not self.prompt_manual_model(self.temp_item, "freehand", points):
                return # If canceled, remove temp item (which is already done in prompt_manual_model)
            self.temp_item = None
        # Polygon drawing is finalized via the Enter key or control buttons

    def keyPressEvent(self, ev):
        """
        Handles key press events, specifically for finalizing polygon drawing with Enter key.
        """
        if self.mode == "polygon" and ev.key() == Qt.Key_Return and len(self.current_polygon) >= 3:
            # If in polygon mode, Enter key is pressed, and there are at least 3 points
            self.finish_polygon_prompt() # Finalize the polygon

    def add_text(self):
        """
        Adds a text item to the scene (currently not fully integrated into workflow).
        """
        if not self.image_loaded: return
        text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
        if ok and text:
            pos = self.view.mapToScene(self.view.mapFromGlobal(self.cursor().pos()))
            if not self._inside_image(pos): return
            itm = QGraphicsTextItem(text)
            itm.setFont(QFont("Arial", 16))
            itm.setDefaultTextColor(self.pen_color)
            itm.setPos(pos)
            self.scene.addItem(itm)
            self.undo_stack.append(("add", itm, None)) # Text items don't have checklist items
            

    def load_image(self, fname):
        """
        Loads an image from the given file path into the QGraphicsScene.
        """
        if fname:
            self.scene.clear() # Clear existing items from the scene
            pix = QPixmap(fname) # Create QPixmap from file
            self.image_item = self.scene.addPixmap(pix) # Add pixmap to scene
            self.image_item.setZValue(0) # Set image Z-value to 0 (background)
            rect = pix.rect()
            self.scene.setSceneRect(QRectF(rect)) # Set scene rectangle to image dimensions
            self.image_loaded = True # Set image loaded flag

    def save_drawing(self):
        """
        Saves the current state of the drawing (image + annotations) and the checklist data.
        """
        # Render the scene to a QPixmap
        rect = self.scene.sceneRect()
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.transparent) # Ensure transparent background
        painter = QPainter(image)
        self.scene.render(painter) # Render scene onto the image
        painter.end()
        pixmap = QPixmap.fromImage(image) # Convert QImage to QPixmap

        # Gather the checklist data
        checklist = []
        for i in range(self.coord_list.count()):
            widget = self.coord_list.itemWidget(self.coord_list.item(i))
            if not widget:
                continue
            checkbox = widget.findChild(QCheckBox, "CheckBox_bbox")
            if checkbox:
                checklist.append({
                    "bbox": checkbox.property("bbox"),
                    "defect_class": checkbox.property("defect_class"),
                    "confidence": checkbox.property("confidence"),
                    "text": checkbox.text(),
                    "checked": checkbox.isChecked()
                })

        self.save_result.emit(pixmap, checklist) # Emit the result
        self.close() # Close the window

    def undo(self):
        """
        Undoes the last action performed (drawing addition or deletion).
        """
        if self.undo_stack: # Check if there are actions to undo
            action, itm, list_item = self.undo_stack.pop() # Get last action from stack
            if action == "add": # If the last action was adding an item
                self.scene.removeItem(itm) # Remove item from scene
                if list_item: # If there's a corresponding list item
                    row = self.coord_list.row(list_item)
                    if row != -1:
                        self.coord_list.takeItem(row) # Remove it from the checklist
                self.item_to_listitem.pop(itm, None) # Remove mapping
                self.redo_stack.append(("remove", itm, list_item)) # Push to redo stack
                self._reindex_checklist_items() # Re-index after removal
            elif action == "remove": # If the last action was removing an item
                self.scene.addItem(itm) # Add graphic item back to scene
                if list_item:
                    # Re-add the QListWidgetItem to the coord_list
                    self.coord_list.addItem(list_item)
                    self.item_to_listitem[itm] = list_item

                    # Get the widget from the re-added list item
                    container_widget = self.coord_list.itemWidget(list_item)
                    if container_widget:
                        checkbox = container_widget.findChild(QCheckBox, "CheckBox_bbox")
                        if checkbox:
                            # Explicitly set checkbox to checked and then redraw the bbox
                            checkbox.blockSignals(True) # Prevent recursive calls
                            checkbox.setChecked(True)
                            checkbox.blockSignals(False)

                            # Get the current index of the list_item in coord_list
                            current_idx = self.coord_list.row(list_item)
                            bbox = checkbox.property("bbox")
                            is_manual = checkbox.property("manual") or False
                            shape_type = checkbox.property("shape_type") or "rectangle"
                            flag = 1 if is_manual else 0
                            # Redraw the item using its stored properties
                            self.draw_bbox_rect(bbox, current_idx, flag=flag, shape_type=shape_type)

                self.redo_stack.append(("add", itm, list_item))
                self._reindex_checklist_items() # Re-index after adding back

    def redo(self):
        """
        Redoes the last undone action.
        """
        if self.redo_stack: # Check if there are actions to redo
            action, itm, list_item = self.redo_stack.pop() # Get last action from stack
            if action == "add": # If the last action was re-adding an item
                self.scene.addItem(itm) # Add item back to scene
                if list_item:
                    self.coord_list.addItem(list_item)
                    self.item_to_listitem[itm] = list_item

                    container_widget = self.coord_list.itemWidget(list_item)
                    if container_widget:
                        checkbox = container_widget.findChild(QCheckBox, "CheckBox_bbox")
                        if checkbox:
                            checkbox.blockSignals(True)
                            checkbox.setChecked(True) # Ensure it's checked when re-added by redo
                            checkbox.blockSignals(False)

                            current_idx = self.coord_list.row(list_item)
                            bbox = checkbox.property("bbox")
                            is_manual = checkbox.property("manual") or False
                            shape_type = checkbox.property("shape_type") or "rectangle"
                            flag = 1 if is_manual else 0
                            self.draw_bbox_rect(bbox, current_idx, flag=flag, shape_type=shape_type)

                self.undo_stack.append(("add", itm, list_item))
                self._reindex_checklist_items()
            elif action == "remove": # If the last action was re-removing an item
                self.scene.removeItem(itm)
                if list_item:
                    row = self.coord_list.row(list_item)
                    if row != -1:
                        self.coord_list.takeItem(row)

                    # When re-removing, explicitly uncheck the checkbox.
                    container_widget = self.coord_list.itemWidget(list_item)
                    if container_widget:
                        checkbox = container_widget.findChild(QCheckBox, "CheckBox_bbox")
                        if checkbox:
                            checkbox.blockSignals(True)
                            checkbox.setChecked(False) # Ensure it's unchecked when removed by redo
                            checkbox.blockSignals(False)


                self.item_to_listitem.pop(itm, None)
                self.undo_stack.append(("remove", itm, list_item))
                self._reindex_checklist_items()

    def zoom_in(self):
        """ Zooms in on the QGraphicsView. """
        self.view.scale(1.2, 1.2)

    def zoom_out(self):
        """ Zooms out on the QGraphicsView. """
        self.view.scale(0.8, 0.8)

    def update_cursor_coords(self, pos, rect_info=None):
        """
        Updates the coordinate label in the status bar.
        """
        if pos is not None and self._inside_image(pos):
            self.last_image_pos = pos
            msg = ""
            if rect_info: # If rectangle info is provided (for rectangle drawing)
                x0, y0, w, h = rect_info
                msg = f"Rectangle Start: ({x0}, {y0})  Width: {w}  Height: {h} | "
            msg += f"X: {int(pos.x())}, Y: {int(pos.y())}" # Current cursor coordinates
            self.coord_label.setText(msg)
        elif self.last_image_pos is not None:
            # Display last known coordinates if mouse leaves image area
            msg = f"X: {int(self.last_image_pos.x())}, Y: {int(self.last_image_pos.y())}"
            self.coord_label.setText(msg)
        else:
            self.coord_label.setText("X: -, Y: -") # Default text if no image or no position

    def add_shape_coords(self, shape_type, coords):
        """
        Adds coordinate information of a drawn shape to the checklist (legacy/manual).
        This is now primarily handled by add_manual_checklist_item.
        """
        if shape_type == "rectangle":
            x, y, w, h = coords
            self.coord_list.addItem(f"Rect: ({x}, {y}, {w}, {h})")
        elif shape_type == "circle":
            x, y, w, h = coords
            self.coord_list.addItem(f"Circle: ({x}, {y}, {w}, {h})")
        elif shape_type == "polygon":
            pts = ", ".join([f"({int(p.x())},{int(p.y())})" for p in coords])
            self.coord_list.addItem(f"Polygon: {pts}")
        elif shape_type == "freehand":
            pts = ", ".join([f"({int(p.x())},{int(p.y())})" for p in coords])
            self.coord_list.addItem(f"Freehand: {pts}")

    def add_checklist_to_coord_list(self, checklist):
        """
        Populates the checklist from an external list of bounding boxes/annotations.
        """
        self.coord_list.clear() # Clear existing items
        self.bbox_graphics_items = {} # Reset mapping for graphics items

        for idx, item in enumerate(checklist, 1):
            container = QWidget() # Container widget for each checklist item
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(2)

            top_row = QHBoxLayout() # Horizontal layout for checkbox and box label
            checkbox = QCheckBox()
            check_state = item.get("checked", False)
            checkbox.setChecked(not check_state) # Invert the initial check state (unchecked means visible)
            checkbox.setObjectName("CheckBox_bbox") # Unique object name for lookup
            top_row.addWidget(checkbox)

            # Assign a property to the box label for easy access during re-indexing
            box_label = QLabel(f"<b><span style='color:#d32f2f;'>Box: {idx}</span></b>")
            box_label.setTextFormat(Qt.RichText)
            box_label.setProperty("label_type", "box_number") # Custom property to identify this label
            top_row.addWidget(box_label)
            top_row.addStretch()
            v_layout.addLayout(top_row)

            defect = item.get("defect_class", "")
            conf = item.get("confidence", "")
            bbox = item.get("bbox", None)
            if bbox and isinstance(bbox, (list, tuple)) and len(bbox) == 4:
                x, y, w, h = bbox
            else:
                x = y = w = h = ""
            details = ( # Detailed information for the annotation
                f"Type of Defect: {defect}<br>"
                f"Confidence: {conf}<br>"
                f"x: {x}<br>"
                f"y: {y}<br>"
                f"w: {w}<br>"
                f"h: {h}"
            )
            details_label = QLabel(f"<span style='color:white;'>{details}</span>")
            details_label.setTextFormat(Qt.RichText)
            details_label.setStyleSheet("background: #222; border-radius: 4px; padding: 4px;")
            v_layout.addWidget(details_label)

            lw_item = QListWidgetItem() # Create a QListWidgetItem
            lw_item.setSizeHint(container.sizeHint()) # Set size hint based on container
            self.coord_list.addItem(lw_item) # Add item to the list widget
            self.coord_list.setItemWidget(lw_item, container) # Set custom widget for the item

            # Connect checkbox to drawing function (partial applies arguments)
            checkbox.stateChanged.connect(partial(self.toggle_bbox_rect, checkbox=checkbox, idx=idx-1))
            # Store properties directly on the checkbox for easy access
            checkbox.setProperty("bbox", bbox)
            checkbox.setProperty("manual", False) # This is a loaded (not manual) item
            checkbox.setProperty("defect_class", defect)
            checkbox.setProperty("shape_type", "rectangle") # Assume rectangle for loaded boxes

            # If the original "checked" was True, draw the rectangle initially
            if check_state:
                self.draw_bbox_rect(bbox, idx-1, flag=0, shape_type="rectangle")


    def draw_bbox_rect(self, bbox, idx, flag=0, shape_type="rectangle"):
        """
        Draws a bounding box or shape on the QGraphicsScene.
        `flag=0` for loaded bboxes (x1,y1,x2,y2), `flag=1` for manual (x,y,w,h).
        """
        if not getattr(self, 'image_loaded', False):
            return # Do nothing if no image is loaded

        if not hasattr(self, "bbox_graphics_items"):
            self.bbox_graphics_items = {} # Initialize if not exists

        # Remove any existing graphic item for this index before redrawing
        old = self.bbox_graphics_items.pop(idx, None)
        if old and old.scene():
            self.scene.removeItem(old)

        if not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
            return # Invalid bbox format

        x, y, w, h = bbox # Unpack bbox coordinates

        # Get defect class and color for the pen
        widget = self.coord_list.itemWidget(self.coord_list.item(idx))
        defect_class = None
        if widget:
            cb = widget.findChild(QCheckBox, "CheckBox_bbox")
            if cb:
                defect_class = cb.property("defect_class")
        color = self.class_colors.get(defect_class, (255, 0, 0)) # Default to red if class not found
        pen = QPen(Qt.red, 2)
        pen.setColor(QColor(*color))

        rect_item = None
        if shape_type == "circle":
            rect_item = self.scene.addEllipse(x, y, int(w), int(h), pen)
        else: # Default to rectangle if shape_type is not "circle"
            if flag == 1: # Manual drawings are already (x,y,w,h)
                rect_item = self.scene.addRect(x, y, int(w), int(h), pen)
            else: # Loaded bboxes might be (x1,y1,x2,y2) so calculate width/height
                rect_item = self.scene.addRect(x, y, int(w-x), int(h-y), pen)

        if rect_item:
            rect_item.setZValue(1) # Ensure drawing is above the image
            self.bbox_graphics_items[idx] = rect_item # Store reference to the graphics item
            # Map graphics item to its QListWidgetItem for easy removal/lookup
            list_item = self.coord_list.item(idx)
            self.item_to_listitem[rect_item] = list_item


    def remove_bbox_rect(self, idx):
        """
        Removes a bounding box/shape from the QGraphicsScene.
        """
        if hasattr(self, "bbox_graphics_items"):
            item = self.bbox_graphics_items.get(idx) # Get item by index
            if item and item.scene(): # Check if item exists and is in scene
                self.scene.removeItem(item) # Remove from scene
                self.item_to_listitem.pop(item, None) # Remove from mapping
            self.bbox_graphics_items.pop(idx, None) # Remove from bbox_graphics_items dict


    def toggle_bbox_rect(self, state, checkbox, idx):
        """
        Toggles the visibility of a bounding box/shape based on checkbox state.
        """
        bbox = checkbox.property("bbox")
        is_manual = checkbox.property("manual") or False
        shape_type = checkbox.property("shape_type") or "rectangle"
        flag = 1 if is_manual else 0 # Determine flag for draw_bbox_rect
        if state == Qt.Checked:
            self.draw_bbox_rect(bbox, idx, flag=flag, shape_type=shape_type)
        else:
            self.remove_bbox_rect(idx)

    def toggle_select_all(self):
        """
        Toggles the checked state of all checkboxes in the checklist,
        thereby showing or hiding all corresponding drawings on the image.
        """
        select_all = self.select_all_btn.isChecked() # True if "Select All", False if "Unselect All"
        self.select_all_btn.setText("Unselect All" if select_all else "Select All") # Update button text

        for idx in range(self.coord_list.count()): # Iterate through all checklist items
            widget = self.coord_list.itemWidget(self.coord_list.item(idx))
            if not widget:
                continue
            cb = widget.findChild(QCheckBox, "CheckBox_bbox") # Find the checkbox
            if not cb:
                continue

            cb.blockSignals(True) # Block signals to prevent recursive calls
            cb.setChecked(select_all) # Set checkbox state
            cb.blockSignals(False) # Re-enable signals

            # Manually trigger the drawing/removal based on the new state
            state = Qt.Checked if select_all else Qt.Unchecked
            self.toggle_bbox_rect(state, cb, idx)

    def prompt_manual_model(self, drawing_item_to_remove, shape_type, coords):
        """
        Prompts the user for confirmation and defect type for a manually drawn annotation.
        """
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Manual Annotation")
        msg_box.setText("Model: Manual")
        ok_btn = msg_box.addButton("OK", QMessageBox.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        msg_box.setDefaultButton(ok_btn)
        msg_box.exec_()

        if msg_box.clickedButton() == cancel_btn:
            # If user cancels, remove the temporary drawing item from scene if it exists
            if drawing_item_to_remove and drawing_item_to_remove.scene():
                self.scene.removeItem(drawing_item_to_remove)
            return False # Return False if canceled
        else:
            # Prompt for defect type
            defect, ok = QInputDialog.getItem(
                self, "Type of Defect", "Select defect type:",
                self.defect_classes, 0, False # Default to first item, not editable
            )
            if not ok:
                # If defect selection is canceled, remove temporary drawing
                if drawing_item_to_remove and drawing_item_to_remove.scene():
                    self.scene.removeItem(drawing_item_to_remove)
                return False # Return False if canceled
            
            # Remove the temporary/manual-drawn item before adding the official one
            if drawing_item_to_remove and drawing_item_to_remove.scene():
                 self.scene.removeItem(drawing_item_to_remove)
            
            # Add the permanent checklist item and graphic item
            new_item, new_list_item = self.add_manual_checklist_item(shape_type, coords, defect)
            # Add the action to the undo stack
            if new_item and new_list_item:
                self.undo_stack.append(("add", new_item, new_list_item))
            return True # Return True if successfully added

    def add_manual_checklist_item(self, shape_type, coords, defect_class="Manual"):
        """
        Adds a manually created annotation to the checklist and draws it on the scene.
        """
        idx = self.coord_list.count() # Use current count as index for the new item
        
        container = QWidget() # Container for checklist item
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        top_row = QHBoxLayout()
        checkbox = QCheckBox()
        checkbox.setChecked(True) # Manually added items are checked by default
        checkbox.setObjectName("CheckBox_bbox")
        top_row.addWidget(checkbox)

        box_label = QLabel(f"<b><span style='color:#d32f2f;'>Box: {idx + 1}</span></b>") # Update box label
        box_label.setTextFormat(Qt.RichText)
        box_label.setProperty("label_type", "box_number") # Custom property to identify this label
        top_row.addWidget(box_label)
        top_row.addStretch()
        v_layout.addLayout(top_row)

        bbox_data = None
        current_drawing_item = None

        # Populate details and draw item based on shape type
        if shape_type in ("rectangle", "circle"):
            x, y, w, h = coords
            details = (
                f"Model: Manual Addition<br>"
                f"Type of Defect: {defect_class}<br>"
                f"Confidence: -<br>"
                f"x: {x}<br>"
                f"y: {y}<br>"
                f"w: {w}<br>"
                f"h: {h}"
            )
            bbox_data = (x, y, w, h) # Store bbox data
            pen = QPen(QColor(*self.class_colors.get(defect_class, (255, 0, 0))), self.pen_width)
            if shape_type == "rectangle":
                current_drawing_item = self.scene.addRect(x, y, w, h, pen, self.brush)
            elif shape_type == "circle":
                current_drawing_item = self.scene.addEllipse(x, y, w, h, pen, self.brush)

        elif shape_type == "polygon":
            # Format polygon points for display
            pts_list = [f"({int(p.x())},{int(p.y())})" for p in coords]
            lines = [", ".join(pts_list[i:i+4]) for i in range(0, len(pts_list), 4)]
            pts_wrapped = "<br>".join(lines)

            details = (
                f"Model: Manual Addition<br>"
                f"Type of Defect: {defect_class}<br>"
                f"{shape_type.capitalize()}:<br>{pts_wrapped}"
            )
            pen = QPen(QColor(*self.class_colors.get(defect_class, (255, 0, 0))), self.pen_width)
            current_drawing_item = self.scene.addPolygon(QPolygonF(coords), pen, self.brush)
            bbox_data = None # Polygons don't have a simple bbox tuple

        elif shape_type == "freehand":
            # Format freehand points for display
            pts_list = [f"({int(p.x())},{int(p.y())})" for p in coords]
            lines = [", ".join(pts_list[i:i+4]) for i in range(0, len(pts_list), 4)]
            pts_wrapped = "<br>".join(lines)
            
            details = (
                f"Model: Manual Addition<br>"
                f"Type of Defect: {defect_class}<br>"
                f"Freehand: {pts_wrapped}"
            )
            # Reconstruct the QPainterPath for the actual item
            path = QPainterPath(coords[0])
            for p in coords[1:]:
                path.lineTo(p)
            pen = QPen(QColor(*self.class_colors.get(defect_class, (255, 0, 0))), self.pen_width)
            current_drawing_item = self.scene.addPath(path, pen)
            bbox_data = None
        else:
            details = f"Type of Defect: {defect_class}"
            bbox_data = None

        details_label = QLabel(f"<span style='color:white;'>{details}</span>")
        details_label.setTextFormat(Qt.RichText)
        details_label.setStyleSheet("background: #222; border-radius: 4px; padding: 4px;")
        v_layout.addWidget(details_label)

        lw_item = QListWidgetItem()
        lw_item.setSizeHint(container.sizeHint())
        self.coord_list.addItem(lw_item)
        self.coord_list.setItemWidget(lw_item, container)
        
        # Link the QGraphicsItem to its QListWidgetItem for easy lookup
        if current_drawing_item:
            self.item_to_listitem[current_drawing_item] = lw_item
            current_drawing_item.setZValue(1) # Ensure drawing is above image

        # Store properties on the checkbox
        checkbox.setProperty("bbox", bbox_data)
        checkbox.setProperty("manual", True)
        checkbox.setProperty("defect_class", defect_class)
        checkbox.setProperty("shape_type", shape_type)
        checkbox.stateChanged.connect(partial(self.toggle_bbox_rect, checkbox=checkbox, idx=idx))

        # Check the checkbox, which will trigger draw_bbox_rect (if applicable)
        checkbox.setChecked(True)

        self._reindex_checklist_items() # Re-index after adding a new item
        return current_drawing_item, lw_item


    def start_polygon(self, start_point):
        """
        Initiates polygon drawing by showing control buttons at the starting point.
        """
        self._polygon_start_point = start_point
        self._polygon_buttons = []

        # Create "Tick" (finish) button
        self.tick_btn = QToolButton(self)
        self.tick_btn.setIcon(QIcon("Assets/icons8-tick-24.png"))
        self.tick_btn.setStyleSheet("background: #222; border-radius: 8px;")
        self.tick_btn.setFixedSize(24, 24)
        self.tick_btn.clicked.connect(self.finish_polygon_prompt)
        self.tick_btn.show()

        # Create "Cross" (cancel) button
        self.cross_btn = QToolButton(self)
        self.cross_btn.setIcon(QIcon("Assets/icons8-cross-24.png"))
        self.cross_btn.setStyleSheet("background: #222; border-radius: 8px;")
        self.cross_btn.setFixedSize(24, 24)
        self.cross_btn.clicked.connect(self.cancel_polygon)
        self.cross_btn.show()

        # Position buttons relative to the scene start point
        scene_pos = start_point
        view_pos = self.view.mapFromScene(scene_pos)
        global_pos = self.view.viewport().mapToGlobal(view_pos)
        self.tick_btn.move(global_pos.x(), global_pos.y() - 29)
        self.cross_btn.move(global_pos.x() + 28, global_pos.y() - 29)

        self._polygon_buttons = [self.tick_btn, self.cross_btn]

    def show_polygon_buttons(self, start_point):
        """
        Updates the position of polygon control buttons if they already exist,
        or creates them if they don't (called when polygon has >= 3 points).
        """
        if hasattr(self, "_polygon_buttons") and self._polygon_buttons:
            # Update button position to the current start_point of the polygon
            scene_pos = start_point
            view_pos = self.view.mapFromScene(scene_pos)
            global_pos = self.view.viewport().mapToGlobal(view_pos)
            self.tick_btn.move(global_pos.x(), global_pos.y() - 29)
            self.cross_btn.move(global_pos.x() + 28, global_pos.y() - 29)
            return # Buttons already exist, just reposition

        # If buttons don't exist, create them
        self._polygon_buttons = []

        self.tick_btn = QToolButton(self)
        self.tick_btn.setIcon(QIcon("Assets/icons8-tick-24.png"))
        self.tick_btn.setStyleSheet("background: #222; border-radius: 8px;")
        self.tick_btn.setFixedSize(24, 24)
        self.tick_btn.clicked.connect(self.finish_polygon_prompt)
        self.tick_btn.show()

        self.cross_btn = QToolButton(self)
        self.cross_btn.setIcon(QIcon("Assets/icons8-cross-24.png"))
        self.cross_btn.setStyleSheet("background: #222; border-radius: 8px;")
        self.cross_btn.setFixedSize(24, 24)
        self.cross_btn.clicked.connect(self.cancel_polygon)
        self.cross_btn.show()

        scene_pos = start_point
        view_pos = self.view.mapFromScene(scene_pos)
        global_pos = self.view.viewport().mapToGlobal(view_pos)
        self.tick_btn.move(global_pos.x(), global_pos.y() - 29)
        self.cross_btn.move(global_pos.x() + 28, global_pos.y() - 29)

        self._polygon_buttons = [self.tick_btn, self.cross_btn]

    def finish_polygon_prompt(self):
        """
        Finalizes the polygon drawing process by prompting for defect type and adding to checklist.
        """
        # Hide and delete polygon control buttons
        for btn in getattr(self, "_polygon_buttons", []):
            btn.hide()
            btn.deleteLater()
        self._polygon_buttons = []

        coords = self.current_polygon
        if not coords or len(coords) < 3:
            self.remove_temp_polygon() # Remove temporary polygon
            self.current_polygon = [] # Clear polygon points
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Manual Annotation")
        msg_box.setText("Model: Manual")
        ok_btn = msg_box.addButton("OK", QMessageBox.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        msg_box.setDefaultButton(ok_btn)
        msg_box.exec_()

        if msg_box.clickedButton() == cancel_btn:
            self.remove_temp_polygon()
            self.current_polygon = []
            return

        defect, ok = QInputDialog.getItem(
            self, "Type of Defect", "Select defect type:",
            self.defect_classes, 0, False
        )
        if not ok:
            self.remove_temp_polygon()
            self.current_polygon = []
            return

        self.remove_temp_polygon() # Remove temporary polygon from scene
        # Add the polygon to the scene and checklist, and push to undo stack
        self.add_manual_checklist_item("polygon", coords, defect) 
        self.current_polygon = [] # Clear polygon points

    def cancel_polygon(self):
        """
        Cancels the current polygon drawing operation, removing temporary elements.
        """
        # Hide and delete polygon control buttons
        for btn in getattr(self, "_polygon_buttons", []):
            btn.hide()
            btn.deleteLater()
        self._polygon_buttons = []
        self.remove_temp_polygon() # Remove temporary polygon
        self.current_polygon = [] # Clear polygon points

    def remove_temp_polygon(self):
        """
        Removes the temporary polygon item from the scene.
        """
        if hasattr(self, "temp_item") and self.temp_item:
            self.scene.removeItem(self.temp_item)
            self.temp_item = None

    def draw_polygon(self, coords, defect_class):
        """
        Draws a polygon on the scene with a specific color.
        This function is generally used for internal drawing, `add_manual_checklist_item` handles the full workflow.
        """
        polygon = QPolygonF(coords)
        pen = QPen(Qt.red, 2)
        color = self.class_colors.get(defect_class, (255, 0, 0))
        pen.setColor(QColor(*color))
        poly_item = self.scene.addPolygon(polygon, pen)
        poly_item.setZValue(1)

    def erase_at(self, pos):
        """
        Erases a drawing at the given position from the scene and its corresponding
        entry from the checklist. Pushes the action to the undo stack.
        """
        items = self.scene.items(pos) # Get all items at the click position
        for item in items:
            if item is self.image_item:
                continue  # Don't erase the background image
            
            self.scene.removeItem(item) # Remove the drawing from the scene
            
            # Remove from checklist if it has a corresponding list item
            list_item = self.item_to_listitem.get(item) # Get without popping yet
            if list_item:
                # Explicitly uncheck the checkbox before removing the list item
                container_widget = self.coord_list.itemWidget(list_item)
                if container_widget:
                    checkbox = container_widget.findChild(QCheckBox, "CheckBox_bbox")
                    if checkbox:
                        checkbox.blockSignals(True) # Block signals to prevent redrawing
                        checkbox.setChecked(False) # Set to unchecked
                        checkbox.blockSignals(False)

                # Now remove from checklist and mapping
                row = self.coord_list.row(list_item)
                if row != -1:
                    self.coord_list.takeItem(row) # This line actually removes the QListWidgetItem
                self.item_to_listitem.pop(item) # Now pop from the mapping

            self.undo_stack.append(("remove", item, list_item)) # Add to undo stack for eraser
            self._reindex_checklist_items() # Re-index after removal
            break  # Erase only one item at a time per click

    def _reindex_checklist_items(self):
        """
        Re-indexes the box numbers in the checklist after an item is added or removed.
        """
        for i in range(self.coord_list.count()):
            list_item = self.coord_list.item(i)
            widget = self.coord_list.itemWidget(list_item)
            if widget:
                # Find the QLabel with the "box_number" property
                for child_widget in widget.findChildren(QLabel):
                    if child_widget.property("label_type") == "box_number":
                        child_widget.setText(f"<b><span style='color:#d32f2f;'>Box: {i + 1}</span></b>")
                        break # Found and updated the label, move to next list item


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PaintApp()
    # Load a default image on startup for testing. Adjust the path as needed.
    win.load_image('/home/vulture/Desktop/DRDO/Images/unfused05_jpg.rf.ae736f84d406cf170b5f1df48ff6e90c.jpg')
    win.show()
    sys.exit(app.exec())
