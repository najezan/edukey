"""
Dialog for displaying student information in RFID information mode.
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import os

class StudentInfoDialog(QDialog):
    def __init__(self, face_system, student_name, student_info, borrow_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Student Information: {student_name}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()
        self.face_system = face_system

        # Face image
        image_dir = self.face_system.config.get("dataset_dir", "data/dataset")
        single_image_path = os.path.join(image_dir, student_name, f"{student_name}_single.jpg")
        image_files = self.face_system.db_manager.get_person_images(student_name)
        
        if os.path.exists(single_image_path):
            pixmap = QPixmap(single_image_path)
        else:
            pixmap = QPixmap(image_files[0])
            
        if not pixmap.isNull():
            image_label = QLabel()
            image_label.setAlignment(Qt.AlignCenter)
            image_label.setPixmap(pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            layout.addWidget(image_label)

        # Name, class, point
        name_label = QLabel(f"<b>Name:</b> {student_name}")
        class_label = QLabel(f"<b>Class:</b> {student_info.get('class', 'Not set')}")
        point_label = QLabel(f"<b>Point:</b> {student_info.get('point', 100)}")
        for lbl in (name_label, class_label, point_label):
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)

        # Borrow list
        borrow_label = QLabel("<b>Borrowed Assets:</b>")
        layout.addWidget(borrow_label)
        borrow_table = QTableWidget()
        borrow_table.setColumnCount(3)
        borrow_table.setHorizontalHeaderLabels(["Asset Name", "Borrowed At", "Returned At"])
        borrow_table.setRowCount(len(borrow_list))
        for i, asset in enumerate(borrow_list):
            borrow_table.setItem(i, 0, QTableWidgetItem(asset['asset_name']))
            borrow_table.setItem(i, 1, QTableWidgetItem(asset['borrowed_at']))
            borrow_table.setItem(i, 2, QTableWidgetItem(asset.get('returned_at', '')))
        borrow_table.resizeColumnsToContents()
        layout.addWidget(borrow_table)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

        self.setLayout(layout)
