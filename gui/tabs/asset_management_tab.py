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
        
        # Filter layout
        filter_layout = QHBoxLayout()
        self.filter_asset_name = QLineEdit()
        self.filter_asset_name.setPlaceholderText("Filter by Asset Name")
        self.filter_borrower = QLineEdit()
        self.filter_borrower.setPlaceholderText("Filter by Borrower")
        self.filter_class = QLineEdit()
        self.filter_class.setPlaceholderText("Filter by Class")
        
        filter_layout.addWidget(self.filter_asset_name)
        filter_layout.addWidget(self.filter_borrower)
        filter_layout.addWidget(self.filter_class)
        filter_layout.addStretch()
        
        # Controls layout
        controls_layout = QHBoxLayout()

        self.asset_name_input = QLineEdit()
        self.asset_name_input.setPlaceholderText("Asset Name")
        self.borrower_input = QLineEdit()
        self.borrower_input.setPlaceholderText("Borrower's Name")
        self.borrower_class = QLineEdit()
        self.borrower_class.setPlaceholderText("Borrower's Class")
        self.borrow_btn = QPushButton("Borrow Asset")
        self.return_btn = QPushButton("Return Asset")
        self.delete_btn = QPushButton("Delete Asset")
        self.refresh_btn = QPushButton("Refresh")

        controls_layout.addWidget(self.asset_name_input)
        controls_layout.addWidget(self.borrower_input)
        controls_layout.addWidget(self.borrower_class)
        controls_layout.addWidget(self.borrow_btn)
        controls_layout.addWidget(self.return_btn)
        controls_layout.addWidget(self.delete_btn)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()

        self.borrow_btn.clicked.connect(self.borrow_asset)
        self.return_btn.clicked.connect(self.return_asset)
        self.delete_btn.clicked.connect(self.delete_asset)
        self.refresh_btn.clicked.connect(self.load_assets)
        
        # Connect filter inputs to filter function
        self.filter_asset_name.textChanged.connect(self.filter_assets)
        self.filter_borrower.textChanged.connect(self.filter_assets)
        self.filter_class.textChanged.connect(self.filter_assets)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Asset Name", "Borrower", "Class", "Borrowed At", "Returned At"
        ])
        header = self.table.horizontalHeader()
        for i in range(5):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        layout.addLayout(filter_layout)
        layout.addLayout(controls_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)


    def load_assets(self):
        self.all_assets = self.db_manager.get_assets() if hasattr(self.db_manager, 'get_assets') else {}
        self.filter_assets()

    def filter_assets(self):
        filter_asset = self.filter_asset_name.text().strip().lower()
        filter_borrower = self.filter_borrower.text().strip().lower()
        filter_class = self.filter_class.text().strip().lower()

        filtered_assets = {}
        for asset, record in self.all_assets.items():
            if (filter_asset in asset.lower() and
                filter_borrower in record.get("borrower", "").lower() and
                filter_class in record.get("class", "").lower()):
                filtered_assets[asset] = record

        self.table.setRowCount(len(filtered_assets))
        for row, (asset, record) in enumerate(sorted(filtered_assets.items())):
            self.table.setItem(row, 0, QTableWidgetItem(asset))
            self.table.setItem(row, 1, QTableWidgetItem(record.get("borrower", "")))
            self.table.setItem(row, 2, QTableWidgetItem(record.get("class", "")))
            borrowed_at_item = QTableWidgetItem(record.get("borrowed_at", ""))
            returned_at_item = QTableWidgetItem(record.get("returned_at", ""))
            borrowed_at_item.setTextAlignment(Qt.AlignCenter)
            returned_at_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, borrowed_at_item)
            self.table.setItem(row, 4, returned_at_item)


    def borrow_asset(self):
        asset = self.asset_name_input.text().strip()
        borrower = self.borrower_input.text().strip()
        classes = self.borrower_class.text().strip()
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

    def delete_asset(self):
        """Delete an asset record."""
        asset = self.asset_name_input.text().strip()
        if not asset:
            QMessageBox.warning(self, "Warning", "Please enter asset name to delete.")
            return
            
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete the asset record for '{asset}'?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes and hasattr(self.db_manager, 'delete_asset'):
            success = self.db_manager.delete_asset(asset)
            if success:
                self.load_assets()
                QMessageBox.information(self, "Success", f"Asset record for '{asset}' has been deleted.")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete asset record.")
