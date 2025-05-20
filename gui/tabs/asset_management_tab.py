"""
Asset management tab for tracking asset borrowing and returns.
"""

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDateEdit, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QDate

class AssetManagementTab(QWidget):
    """Tab for tracking asset borrowing and returns."""
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.init_ui()
        self.load_assets()

    def init_ui(self):
        layout = QVBoxLayout()
        controls_layout = QHBoxLayout()

        self.asset_name_input = QLineEdit()
        self.asset_name_input.setPlaceholderText("Asset Name")
        self.borrower_input = QLineEdit()
        self.borrower_input.setPlaceholderText("Borrower's Name")
        self.borrower_class = QLineEdit()
        self.borrower_class.setPlaceholderText("Borrower's Class")
        self.borrow_btn = QPushButton("Borrow Asset")
        self.return_btn = QPushButton("Return Asset")
        self.refresh_btn = QPushButton("Refresh")

        controls_layout.addWidget(self.asset_name_input)
        controls_layout.addWidget(self.borrower_input)
        controls_layout.addWidget(self.borrower_class)
        controls_layout.addWidget(self.borrow_btn)
        controls_layout.addWidget(self.return_btn)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()

        self.borrow_btn.clicked.connect(self.borrow_asset)
        self.return_btn.clicked.connect(self.return_asset)
        self.refresh_btn.clicked.connect(self.load_assets)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Asset Name", "Borrower", "Class","Borrowed At", "Returned At"
        ])
        header = self.table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        layout.addLayout(controls_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)

    def load_assets(self):
        assets = self.db_manager.get_assets() if hasattr(self.db_manager, 'get_assets') else {}
        self.table.setRowCount(len(assets))
        for row, (asset, record) in enumerate(sorted(assets.items())):
            self.table.setItem(row, 0, QTableWidgetItem(asset))
            self.table.setItem(row, 1, QTableWidgetItem(record.get("borrower", "")))
            self.table.setItem(row, 2, QTableWidgetItem(record.get("class", "")))
            self.table.setItem(row, 3, QTableWidgetItem(record.get("borrowed_at", "")))
            self.table.setItem(row, 4, QTableWidgetItem(record.get("returned_at", "")))

    def borrow_asset(self):
        asset = self.asset_name_input.text().strip()
        borrower = self.borrower_input.text().strip()
        classes = self.borrower_input.text().strip()
        if not asset or not borrower or not classes:
            QMessageBox.warning(self, "Warning", "Please enter asset name/borrower's name/borrower's class.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self.db_manager, 'borrow_asset'):
            success = self.db_manager.borrow_asset(asset, borrower, classes, now)
            if success:
                self.load_assets()
                QMessageBox.information(self, "Success", f"{asset} borrowed by {borrower}.")
            else:
                QMessageBox.warning(self, "Error", "Failed to borrow asset.")

    def return_asset(self):
        asset = self.asset_name_input.text().strip()
        if not asset:
            QMessageBox.warning(self, "Warning", "Please enter asset name to return.")
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self.db_manager, 'return_asset'):
            success = self.db_manager.return_asset(asset, now)
            if success:
                self.load_assets()
                QMessageBox.information(self, "Success", f"{asset} returned.")
            else:
                QMessageBox.warning(self, "Error", "Failed to return asset.")

