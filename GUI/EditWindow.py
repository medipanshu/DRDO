import sys
from functools import partial

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QAction,
    QFileDialog, QColorDialog, QGraphicsTextItem, QInputDialog, QToolBar,
    QComboBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QWidget, QCheckBox, QPushButton, QMessageBox, QToolButton
)
from PyQt5.QtGui import (
    QPen, QBrush, QPixmap, QPainterPath, QFont, QImage, QPainter, QPolygonF,
    QColor, QCursor, QIcon
)
from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal


class PaintView(QGraphicsView):
    """
    Custom QGraphicsView to handle mouse events and forward them to the parent application.
    """
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.parent_app = parent
        self.setMouseTracking(True)  # Enable mouse tracking for continuous coordinate updates

    def mousePressEvent(self, event):
        """
        Handles mouse press events. Starts drawing or erasing based on the current mode.
        """
        pos = self.mapToScene(event.pos())
        if event.button() == Qt.LeftButton:
            self.parent_app.start_drawing(pos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handles mouse move events. Updates cursor coordinates and continues drawing if active.
        """
        pos = self.mapToScene(event.pos())
        if self.parent_app._inside_image(pos):
            self.parent_app.update_cursor_coords(pos)
        else:
            self.parent_app.update_cursor_coords(None)

        if self.parent_app.drawing:
            self.parent_app.continue_drawing(pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handles mouse release events. Finishes the current drawing operation.
        """
        if event.button() == Qt.LeftButton:
            pos = self.mapToScene(event.pos())
            self.parent_app.finish_drawing(pos)
        super().mouseReleaseEvent(event)


class PaintApp(QMainWindow):
    """
    Main application window for the PyQt5 Paint App.
    Allows loading images, drawing various shapes, erasing, and managing annotations.
    Includes a checklist for drawn items.
    """
    save_result = pyqtSignal(object, list)  # Signal to emit QPixmap and checklist on save

    def __init__(self, bbox_checklist=None):
        super().__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        self.setWindowTitle("PyQt5 Paint App (Image Annotation Tool)")
        self.setGeometry(0, 0, screen.width(), screen.height())

        self.scene = QGraphicsScene()
        self.view = PaintView(self.scene, parent=self)

        # --- Right column with Select All button and Checklist ---
        self.coord_list = QListWidget()
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setCheckable(True)
        self.select_all_btn.clicked.connect(self.toggle_select_all)

        right_col_widget = QWidget()
        right_col_layout = QVBoxLayout(right_col_widget)
        right_col_layout.setContentsMargins(0, 0, 0, 0)
        right_col_layout.setSpacing(4)
        right_col_layout.addWidget(self.select_all_btn)
        right_col_layout.addWidget(self.coord_list)

        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.addWidget(self.view)
        main_layout.addWidget(right_col_widget)
        main_layout.setStretch(0, 4)  # 4 parts of space to the view
        main_layout.setStretch(1, 1)  # 1 part of space to the checklist
        self.setCentralWidget(main_widget)

        # Drawing & style defaults
        self.mode = None
        self.drawing = False
        self.start_point = None
        self.temp_item = None
        self.current_path = None
        self.current_polygon = []
        self.pen_color, self.fill_color = Qt.black, Qt.transparent
        self.pen_width = 2
        self.pen = QPen(self.pen_color, self.pen_width)
        self.brush = QBrush(self.fill_color)

        self.image_loaded = False
        self.coord_label = QLabel("X: -, Y: -")
        self.statusBar().addPermanentWidget(self.coord_label)
        self.last_image_pos = None
        self.bbox_graphics_items = {}
        # Mapping between QGraphicsItem and QListWidgetItem for easy lookup
        self.item_to_listitem = {}  # QGraphicsItem -> QListWidgetItem

        # Predefined defect classes for annotations
        self.defect_classes = ['crack', 'lof', 'lop', 'overlap', 'porosity', 'slag', 'spattering', 'undercut']
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

        self._create_toolbar()
        if bbox_checklist:
            self.add_checklist_to_coord_list(bbox_checklist)

    def _create_toolbar(self):
        """
        Creates and populates the application's toolbar with tools and actions.
        """
        toolbar = QToolBar("Tools", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        save_act = QAction(QIcon("Assets/icons8-save-60.png"), "Save", self)
        save_act.triggered.connect(self.save_drawing)
        toolbar.addAction(save_act)
        toolbar.addSeparator()

        toolbar.addWidget(QLabel("<b>Drawing Tools</b>"))
        rect_act = QAction(QIcon("Assets/icons8-rectangle-50.png"), "Rectangle", self)
        rect_act.triggered.connect(lambda: self.set_mode("rectangle"))
        toolbar.addAction(rect_act)

        circle_act = QAction(QIcon("Assets/icons8-circle-50.png"), "Circle", self)
        circle_act.triggered.connect(lambda: self.set_mode("circle"))
        toolbar.addAction(circle_act)

        poly_act = QAction(QIcon("Assets/icons8-polygon-50.png"), "Polygon", self)
        poly_act.triggered.connect(lambda: self.set_mode("polygon"))
        toolbar.addAction(poly_act)

        # free_hand_act = QAction(QIcon("Assets/icons8-pencil-64.png"), "Freehand", self)
        # free_hand_act.triggered.connect(lambda: self.set_mode("freehand"))
        # toolbar.addAction(free_hand_act)

        eraser_act = QAction(QIcon("Assets/icons8-eraser-48.png"), "Eraser", self)
        eraser_act.triggered.connect(lambda: self.set_mode("eraser"))
        toolbar.addAction(eraser_act)
        toolbar.addSeparator()

        pen_act = QAction(QIcon("Assets/icons8-paint-palette-with-brush-48.png"), "Pen Color", self)
        pen_act.triggered.connect(self.select_pen_color)
        toolbar.addAction(pen_act)
        toolbar.addSeparator()

        toolbar.addWidget(QLabel("Width:"))
        self.width_combo = QComboBox()
        self.width_combo.addItems([str(i) for i in (1, 2, 4, 6, 8, 10)])
        self.width_combo.setCurrentText(str(self.pen_width))
        self.width_combo.currentTextChanged.connect(lambda w: self.change_width(int(w)))
        toolbar.addWidget(self.width_combo)
        toolbar.addSeparator()

        zoom_in_act = QAction(QIcon("Assets/icons8-zoom-in-64.png"), "Zoom In", self)
        zoom_in_act.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_act)

        zoom_out_act = QAction(QIcon("Assets/icons8-zoom-out-64.png"), "Zoom Out", self)
        zoom_out_act.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_act)
        toolbar.addSeparator()

    def set_mode(self, m):
        """Sets the current drawing mode and updates the cursor icon."""
        self.mode = m
        cursors = {
            "freehand": Qt.CrossCursor,
            "rectangle": Qt.SizeAllCursor,
            "circle": Qt.SizeBDiagCursor,
            "polygon": Qt.PointingHandCursor,
            "eraser": Qt.ForbiddenCursor
        }
        self.view.setCursor(cursors.get(m, Qt.ArrowCursor))
        if m == "freehand":
            self.current_path = QPainterPath()

    def change_width(self, w):
        """Changes the pen width."""
        self.pen_width = w
        self.pen.setWidth(w)

    def select_pen_color(self):
        """Opens a color dialog to select the pen color."""
        c = QColorDialog.getColor()
        if c.isValid():
            self.pen_color = c
            self.pen.setColor(c)

    def _inside_image(self, pos):
        """Checks if a QPointF is within the loaded image bounds."""
        return self.image_loaded and self.scene.sceneRect().contains(pos)

    def start_drawing(self, pos):
        """Initiates a drawing operation."""
        if not self._inside_image(pos):
            return
        self.drawing, self.start_point = True, pos
        m = self.mode

        if m == "freehand":
            self.current_path = QPainterPath(pos)
            self.temp_item = self.scene.addPath(self.current_path, self.pen)
        elif m == "polygon":
            self.current_polygon.append(pos)
            if len(self.current_polygon) > 1:
                if self.temp_item: self.scene.removeItem(self.temp_item)
                self.temp_item = self.scene.addPolygon(QPolygonF(self.current_polygon), self.pen, self.brush)
            
            if len(self.current_polygon) == 1:
                self.start_polygon(pos)
            elif len(self.current_polygon) >= 3:
                self.show_polygon_buttons(self.current_polygon[0])
        elif m == "eraser":
            self.erase_at(pos)

    def continue_drawing(self, pos):
        """Continues a drawing operation as the mouse moves."""
        if not self._inside_image(pos) or not self.drawing:
            return
        m, sp = self.mode, self.start_point

        if self.temp_item:
            self.scene.removeItem(self.temp_item)

        if m == "freehand":
            self.current_path.lineTo(pos)
            self.temp_item = self.scene.addPath(self.current_path, self.pen)
        elif m == "rectangle":
            rect = QRectF(sp, pos).normalized()
            self.temp_item = self.scene.addRect(rect, self.pen, self.brush)
            x0, y0, w, h = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
            self.update_cursor_coords(pos, (x0, y0, w, h))
        elif m == "circle":
            rect = QRectF(sp, pos).normalized()
            self.temp_item = self.scene.addEllipse(rect, self.pen, self.brush)
        elif m == "polygon":
            pts = self.current_polygon + [pos]
            self.temp_item = self.scene.addPolygon(QPolygonF(pts), self.pen, self.brush)
        
        if m not in ["rectangle"]: # Update coords for other shapes too
            self.update_cursor_coords(pos)


    def finish_drawing(self, pos):
        """Finalizes a drawing operation on mouse release."""
        if not self._inside_image(pos) or not self.drawing:
            return
        self.drawing = False
        m, sp = self.mode, self.start_point

        if self.temp_item:
            self.scene.removeItem(self.temp_item)
            self.temp_item = None
            
        if m == "rectangle":
            rect = QRectF(sp, pos).normalized()
            coords = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
            self.prompt_manual_model("rectangle", coords)
        elif m == "circle":
            rect = QRectF(sp, pos).normalized()
            coords = int(rect.x()), int(rect.y()), int(rect.width()), int(rect.height())
            self.prompt_manual_model("circle", coords)
        elif m == "freehand":
            points = [self.current_path.pointAtPercent(i / 100.0) for i in range(101)]
            self.prompt_manual_model("freehand", points)
        # Polygon finalization is handled by its own controls

    def keyPressEvent(self, ev):
        """Handles key press events for finalizing polygon drawing."""
        if self.mode == "polygon" and ev.key() == Qt.Key_Return and len(self.current_polygon) >= 3:
            self.finish_polygon_prompt()

    def load_image(self, fname):
        """Loads an image from a file path into the QGraphicsScene."""
        if fname:
            self.scene.clear()
            pix = QPixmap(fname)
            self.image_item = self.scene.addPixmap(pix)
            self.image_item.setZValue(0)
            self.scene.setSceneRect(QRectF(pix.rect()))
            self.image_loaded = True

    def save_drawing(self):
        """Saves the current drawing and checklist data."""
        rect = self.scene.sceneRect()
        image = QImage(rect.size().toSize(), QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        self.scene.render(painter)
        painter.end()
        pixmap = QPixmap.fromImage(image)

        checklist = []
        for i in range(self.coord_list.count()):
            widget = self.coord_list.itemWidget(self.coord_list.item(i))
            if widget:
                checkbox = widget.findChild(QCheckBox, "CheckBox_bbox")
                if checkbox:
                    checklist.append({
                        "bbox": checkbox.property("bbox"),
                        "defect_class": checkbox.property("defect_class"),
                        "confidence": checkbox.property("confidence"),
                        "text": checkbox.text(),
                        "checked": checkbox.isChecked(),
                        "points": checkbox.property("points"),  
                        "shape_type": checkbox.property("shape_type")
                    })

        self.save_result.emit(pixmap, checklist)
        self.close()

    def zoom_in(self):
        """Zooms in on the QGraphicsView."""
        self.view.scale(1.2, 1.2)

    def zoom_out(self):
        """Zooms out on the QGraphicsView."""
        self.view.scale(0.8, 0.8)

    def update_cursor_coords(self, pos, rect_info=None):
        """Updates the coordinate label in the status bar."""
        if pos and self._inside_image(pos):
            self.last_image_pos = pos
            msg = ""
            if rect_info:
                x0, y0, w, h = rect_info
                msg = f"Rectangle Start: ({x0}, {y0})  Width: {w}  Height: {h} | "
            msg += f"X: {int(pos.x())}, Y: {int(pos.y())}"
            self.coord_label.setText(msg)
        elif self.last_image_pos:
            self.coord_label.setText(f"X: {int(self.last_image_pos.x())}, Y: {int(self.last_image_pos.y())}")
        else:
            self.coord_label.setText("X: -, Y: -")
            
    def add_checklist_to_coord_list(self, checklist):
        """Populates the checklist from an external list of annotations."""
        self.coord_list.clear()
        self.bbox_graphics_items.clear()   # <-- add this
        self.item_to_listitem.clear()      # <-- add this

        for idx, item in enumerate(checklist, 1):
            container = QWidget()
            v_layout = QVBoxLayout(container)
            v_layout.setContentsMargins(0, 0, 0, 0)
            v_layout.setSpacing(2)

            top_row = QHBoxLayout()
            checkbox = QCheckBox()
            check_state = item.get("checked", False)
            checkbox.setChecked(not check_state)
            checkbox.setObjectName("CheckBox_bbox")
            top_row.addWidget(checkbox)
            
            box_label = QLabel(f"<b><span style='color:#d32f2f;'>Box: {idx}</span></b>")
            box_label.setTextFormat(Qt.RichText)
            box_label.setProperty("label_type", "box_number")
            top_row.addWidget(box_label)
            top_row.addStretch()
            v_layout.addLayout(top_row)

            defect = item.get("defect_class", "")
            conf = item.get("confidence", "")
            shape_type = item.get("shape_type", "rectangle")
            bbox = item.get("bbox", [0, 0, 0, 0]) if shape_type in ("rectangle", "circle") else None
            points = item.get("points", None)

            if shape_type in ("rectangle", "circle") and bbox is not None:
                x, y, w, h = bbox
                details = (
                    f"Type of Defect: {defect}<br>"
                    f"Confidence: {conf}<br>"
                    f"x: {x},<br>y: {y},<br>w: {w},<br>h: {h}"
                )
            elif shape_type in ("polygon", "freehand") and points:
                pts_list = [f"({int(p.x())},{int(p.y())})" for p in points]
                pts_wrapped = "<br>".join([", ".join(pts_list[i:i + 4]) for i in range(0, len(pts_list), 4)])
                details = (
                    f"Type of Defect: {defect}<br>"
                    f"Confidence: {conf}<br>"
                    f"{shape_type.capitalize()}:<br>{pts_wrapped}"
                )
            else:
                details = f"Type of Defect: {defect}<br>Confidence: {conf}"

            details_label = QLabel(f"<span style='color:white;'>{details}</span>")
            details_label.setTextFormat(Qt.RichText)
            details_label.setStyleSheet("background: #222; border-radius: 4px; padding: 4px;")
            v_layout.addWidget(details_label)

            lw_item = QListWidgetItem()
            lw_item.setSizeHint(container.sizeHint())
            self.coord_list.addItem(lw_item)
            self.coord_list.setItemWidget(lw_item, container)

            checkbox.stateChanged.connect(lambda state, cb=checkbox: self.toggle_bbox_rect(state, cb))

            checkbox.setProperty("bbox", bbox if shape_type in ("rectangle", "circle") else None)
            checkbox.setProperty("points", points if shape_type in ("polygon", "freehand") else None)
            checkbox.setProperty("manual", item.get("manual", False))
            checkbox.setProperty("defect_class", defect)
            checkbox.setProperty("shape_type", shape_type)
            checkbox.setProperty("confidence", conf)
            
            if check_state:
                if shape_type in ("rectangle", "circle"):
                    self.draw_bbox_rect(bbox, idx - 1, shape_type=shape_type)
                elif shape_type == "polygon" and points:
                    pen = QPen(QColor(*self.class_colors.get(defect, (255, 0, 0))), self.pen_width)
                    item_poly = self.scene.addPolygon(QPolygonF(points), pen, self.brush)
                    item_poly.setZValue(1)
                    self.bbox_graphics_items[idx - 1] = item_poly
                    self.item_to_listitem[item_poly] = lw_item
                elif shape_type == "freehand" and points:
                    pen = QPen(QColor(*self.class_colors.get(defect, (255, 0, 0))), self.pen_width)
                    path = QPainterPath(points[0])
                    for p in points[1:]:
                        path.lineTo(p)
                    item_path = self.scene.addPath(path, pen)
                    item_path.setZValue(1)
                    self.bbox_graphics_items[idx - 1] = item_path
                    self.item_to_listitem[item_path] = lw_item

    def draw_bbox_rect(self, bbox, idx, shape_type="rectangle"):
        """Draws a shape on the scene."""
        if not self.image_loaded or not (isinstance(bbox, (list, tuple)) and len(bbox) == 4):
            return

        if not hasattr(self, "bbox_graphics_items"):
            self.bbox_graphics_items = {}

        if old_item := self.bbox_graphics_items.pop(idx, None):
            if old_item.scene():
                self.scene.removeItem(old_item)

        x, y, w, h = bbox

        widget = self.coord_list.itemWidget(self.coord_list.item(idx))
        defect_class = widget.findChild(QCheckBox, "CheckBox_bbox").property("defect_class") if widget else ""
        is_manual = widget.findChild(QCheckBox, "CheckBox_bbox").property("manual") if widget else False
        color = self.class_colors.get(defect_class, (255, 0, 0))
        pen = QPen(QColor(*color), 2)

        new_item = None
        if shape_type == "circle":
            new_item = self.scene.addEllipse(x, y, int(w), int(h), pen)
        else:  # Default to rectangle
            new_item = self.scene.addRect(x, y, int(w), int(h), pen)

        if new_item:
            new_item.setZValue(1)
            self.bbox_graphics_items[idx] = new_item
            list_item = self.coord_list.item(idx)
            self.item_to_listitem[new_item] = list_item

    def remove_bbox_rect(self, idx):
        """Removes a shape from the scene."""
        if hasattr(self, "bbox_graphics_items"):
            if item := self.bbox_graphics_items.pop(idx, None):
                if item.scene():
                    self.scene.removeItem(item)
                self.item_to_listitem.pop(item, None)

    def toggle_bbox_rect(self, state, checkbox):
        """Toggles the visibility of the matching shape when the user (un)checks a box."""
        idx = None
        for i in range(self.coord_list.count()):
            widget = self.coord_list.itemWidget(self.coord_list.item(i))
            if widget and widget.findChild(QCheckBox, "CheckBox_bbox") is checkbox:
                idx = i
                break
        if idx is None:
            return

        shape_type = checkbox.property("shape_type") or "rectangle"

        defect_class = checkbox.property("defect_class") or ""
        color = self.class_colors.get(defect_class, (255, 0, 0))
        pen = QPen(QColor(*color), self.pen_width)

        if state == Qt.Checked:
            if shape_type == "polygon":
                coords = checkbox.property("points")
                if coords:
                    item = self.scene.addPolygon(QPolygonF(coords), pen, self.brush)
                    item.setZValue(1)
                    self.bbox_graphics_items[idx] = item
                    list_item = self.coord_list.item(idx)
                    self.item_to_listitem[item] = list_item
            elif shape_type == "freehand":
                coords = checkbox.property("points")
                if coords:
                    path = QPainterPath(coords[0])
                    for p in coords[1:]:
                        path.lineTo(p)
                    item = self.scene.addPath(path, pen)
                    item.setZValue(1)
                    self.bbox_graphics_items[idx] = item
                    list_item = self.coord_list.item(idx)
                    self.item_to_listitem[item] = list_item
            else:
                bbox = checkbox.property("bbox")
                self.draw_bbox_rect(bbox, idx, shape_type=shape_type)
        else:
            self.remove_bbox_rect(idx)

        # Reindex and update mapping
        self._reindex_checklist_items()
        new_map = {}
        for item, list_item in list(self.item_to_listitem.items()):
            row = self.coord_list.row(list_item)
            if item.scene():
                new_map[row] = item
        self.bbox_graphics_items = new_map


    def toggle_select_all(self):
        """Toggles the checked state of all checklist items."""
        is_checked = self.select_all_btn.isChecked()
        self.select_all_btn.setText("Unselect All" if is_checked else "Select All")

        for idx in range(self.coord_list.count()):
            widget = self.coord_list.itemWidget(self.coord_list.item(idx))
            if cb := widget.findChild(QCheckBox, "CheckBox_bbox"):
                cb.setChecked(is_checked)


    def prompt_manual_model(self, shape_type, coords):
        """Prompts for confirmation and defect type for a manually drawn shape."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Manual Annotation")
        msg_box.setText("Add this manual annotation?")
        ok_btn = msg_box.addButton("OK", QMessageBox.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        msg_box.exec_()

        if msg_box.clickedButton() == ok_btn:
            defect, ok = QInputDialog.getItem(self, "Type of Defect", "Select defect type:", self.defect_classes, 0, False)
            if ok:
                self.add_manual_checklist_item(shape_type, coords, defect)

    def add_manual_checklist_item(self, shape_type, coords, defect_class):
        """Adds a manually created annotation to the checklist and scene."""
        idx = self.coord_list.count()
        
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)

        top_row = QHBoxLayout()
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox.setObjectName("CheckBox_bbox")
        top_row.addWidget(checkbox)

        box_label = QLabel(f"<b><span style='color:#d32f2f;'>Box: {idx + 1}</span></b>")
        box_label.setTextFormat(Qt.RichText)
        box_label.setProperty("label_type", "box_number")
        top_row.addWidget(box_label)
        top_row.addStretch()
        v_layout.addLayout(top_row)
        
        details, bbox_data, current_drawing_item = "", None, None
        pen = QPen(QColor(*self.class_colors.get(defect_class, (255, 0, 0))), self.pen_width)

        if shape_type in ("rectangle", "circle"):
            x, y, w, h = coords
            details = f"Model: Manual Addition<br>Type: {defect_class}<br>x: {x},<br>y: {y},<br>w:{w},<br>h:{h}"
            bbox_data = coords
            if shape_type == "rectangle":
                current_drawing_item = self.scene.addRect(x, y, w, h, pen, self.brush)
            else:
                current_drawing_item = self.scene.addEllipse(x, y, w, h, pen, self.brush)
        
        elif shape_type in ("polygon", "freehand"):
            pts_list = [f"({int(p.x())},{int(p.y())})" for p in coords]
            pts_wrapped = "<br>".join([", ".join(pts_list[i:i + 4]) for i in range(0, len(pts_list), 4)])
            details = f"Model: Manual Addition<br>Type: {defect_class}<br>{shape_type.capitalize()}:<br>{pts_wrapped}"
            
            if shape_type == "polygon":
                current_drawing_item = self.scene.addPolygon(QPolygonF(coords), pen, self.brush)
            else: # freehand
                path = QPainterPath(coords[0])
                for p in coords[1:]: path.lineTo(p)
                current_drawing_item = self.scene.addPath(path, pen)

        details_label = QLabel(f"<span style='color:white;'>{details}</span>")
        details_label.setTextFormat(Qt.RichText)
        details_label.setStyleSheet("background: #222; border-radius: 4px; padding: 4px;")
        v_layout.addWidget(details_label)

        lw_item = QListWidgetItem()
        lw_item.setSizeHint(container.sizeHint())
        self.coord_list.addItem(lw_item)
        self.coord_list.setItemWidget(lw_item, container)
        
        if current_drawing_item:
            self.item_to_listitem[current_drawing_item] = lw_item
            current_drawing_item.setZValue(1)

        checkbox.setProperty("bbox", bbox_data)
        checkbox.setProperty("manual", True)
        checkbox.setProperty("defect_class", defect_class)
        checkbox.setProperty("shape_type", shape_type)
        checkbox.setProperty("points", coords)  # <-- ADD THIS LINE
        # checkbox.setProperty("confidence", 1.0)  # Default confidence for manual annotations
        idx = self.coord_list.row(lw_item)
        # checkbox.stateChanged.connect(partial(self.toggle_bbox_rect, checkbox=checkbox, idx=idx))
        checkbox.stateChanged.connect(lambda state, cb=checkbox: self.toggle_bbox_rect(state, cb))

        
        # Check the checkbox, which will trigger draw_bbox_rect (if applicable)
        checkbox.setChecked(True)

        self._reindex_checklist_items() # Re-index after adding a new item
        # return current_drawing_item, lw_item


    def start_polygon(self, start_point):
        """Initiates polygon drawing by showing control buttons."""
        self._polygon_buttons = []
        
        self.tick_btn = self._create_polygon_button("Assets/icons8-tick-24.png", self.finish_polygon_prompt)
        self.cross_btn = self._create_polygon_button("Assets/icons8-cross-24.png", self.cancel_polygon)
        
        self.show_polygon_buttons(start_point)
        self._polygon_buttons = [self.tick_btn, self.cross_btn]

    def _create_polygon_button(self, icon_path, on_click):
        """Helper to create a polygon control button."""
        btn = QToolButton(self)
        btn.setIcon(QIcon(icon_path))
        btn.setStyleSheet("background: #222; border-radius: 8px;")
        btn.setFixedSize(24, 24)
        btn.clicked.connect(on_click)
        btn.show()
        return btn

    def show_polygon_buttons(self, start_point):
        """Updates the position of polygon control buttons."""
        if hasattr(self, "_polygon_buttons") and self._polygon_buttons:
            view_pos = self.view.mapFromScene(start_point)
            global_pos = self.view.viewport().mapToGlobal(view_pos)
            self.tick_btn.move(global_pos.x(), global_pos.y() - 29)
            self.cross_btn.move(global_pos.x() + 28, global_pos.y() - 29)

    def finish_polygon_prompt(self):
        """Finalizes the polygon drawing process."""
        self._cleanup_polygon_drawing()
        coords = self.current_polygon
        if not coords or len(coords) < 3:
            self.current_polygon = []
            return

        self.prompt_manual_model("polygon", coords)
        self.current_polygon = []

    def cancel_polygon(self):
        """Cancels the current polygon drawing operation."""
        self._cleanup_polygon_drawing()
        self.current_polygon = []

    def _cleanup_polygon_drawing(self):
        """Hides buttons and removes the temporary polygon item."""
        for btn in getattr(self, "_polygon_buttons", []):
            btn.hide()
            btn.deleteLater()
        self._polygon_buttons = []
        if self.temp_item:
            self.scene.removeItem(self.temp_item)
            self.temp_item = None
            
    def erase_at(self, pos):
        """Erases a drawing at the given position."""
        items = self.scene.items(pos)
        for item in items:
            if item is self.image_item:
                continue
            
            if list_item := self.item_to_listitem.pop(item, None):
                self.scene.removeItem(item)
                row = self.coord_list.row(list_item)
                if row != -1:
                    self.coord_list.takeItem(row)
                self._reindex_checklist_items()
                break # Erase one item at a time

    def _reindex_checklist_items(self):
        """Re-indexes the box numbers in the checklist after any removal."""
        for i in range(self.coord_list.count()):
            list_item = self.coord_list.item(i)
            widget = self.coord_list.itemWidget(list_item)
            if widget:
                # Find the box label by property
                for child in widget.findChildren(QLabel):
                    if child.property("label_type") == "box_number":
                        child.setText(f"<b><span style='color:#d32f2f;'>Box: {i + 1}</span></b>")
                        break

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PaintApp()
    # Provide a path to a default image for testing if desired
    # win.load_image('path/to/your/image.jpg')
    win.show()
    sys.exit(app.exec())