import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QTableWidget,
    QTableWidgetItem, QAbstractItemView, QDialog, QLabel, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QImage, QPixmap, QIntValidator


class WebcamWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Webcam Feed")
        self.setGeometry(100, 100, 640, 480)
        self.label = QLabel(self)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow for camera capture
        self.timer.start(20)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(image).scaled(self.size(), Qt.KeepAspectRatio))

    def closeEvent(self, event):
        self.timer.stop()
        self.cap.release()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Custom Layout")
        self.setGeometry(100, 100, 1920, 1080)
        # Initialize guest list
        self.guest_list = [
            "John Doe", "Jane Smith", "Alice Johnson", "Robert Brown",
            "Michael Clark", "Sarah Davis"
        ]
        self.initUI()


    def initUI(self):
        # Main layout (horizontal split between left and right sections)
        main_layout = QHBoxLayout(self)
        self.setStyleSheet("background-color: black; color: white;")

        # Left section layout
        left_layout = QVBoxLayout()

        # Input text bar (disabled initially)
        self.input_text = QLineEdit(self)
        self.input_text.setPlaceholderText("Search for Guest")
        self.input_text.setEnabled(False)  # Disabled initially
        self.input_text.textChanged.connect(self.search_guest)
        left_layout.addWidget(self.input_text)
        left_layout.setAlignment(self.input_text, Qt.AlignTop)  # Ensure search bar stays at the top

        # Table with alternating gray and white rows for guests list
        self.table = QTableWidget(self)
        self.table.setRowCount(len(self.guest_list))
        self.table.setColumnCount(1)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setShowGrid(False)
        self.table.setVisible(False)
        self.table.cellClicked.connect(self.select_guest)

        # Populate table with guest names and ensure proper contrast
        for row, guest in enumerate(self.guest_list):
            item = QTableWidgetItem(guest)
            if row % 2 == 0:
                item.setBackground(QColor(211, 211, 211))  # Light gray for even rows
                item.setForeground(QColor(0, 0, 0))  # Black text on gray background
            else:
                item.setBackground(QColor(50, 50, 50))  # Dark gray for odd rows
                item.setForeground(QColor(255, 255, 255))  # White text on dark gray background
            self.table.setItem(row, 0, item)

        left_layout.addWidget(self.table)

        # Right section layout
        right_layout = QVBoxLayout()

        # Add 8 large buttons with lighter dark color
        button_style = "background-color: #444444; color: white; font-size: 18px;"

        button1 = QPushButton("Open Webcam", self)
        button1.setStyleSheet(button_style)
        button1.setFixedHeight(100)
        button1.clicked.connect(self.show_webcam)
        right_layout.addWidget(button1)

        button2 = QPushButton("Print Message", self)
        button2.setStyleSheet(button_style)
        button2.setFixedHeight(100)
        button2.clicked.connect(self.print_message)
        right_layout.addWidget(button2)

        button3 = QPushButton("Show Guest List", self)
        button3.setStyleSheet(button_style)
        button3.setFixedHeight(100)
        button3.clicked.connect(self.show_guest_list)
        right_layout.addWidget(button3)

        button4 = QPushButton("Assign Credit", self)
        button4.setStyleSheet(button_style)
        button4.setFixedHeight(100)
        button4.clicked.connect(self.assign_credit)
        right_layout.addWidget(button4)

        for i in range(5, 9):
            button = QPushButton(f"Button {i}", self)
            button.setStyleSheet(button_style)
            button.setFixedHeight(100)
            right_layout.addWidget(button)

        # Add layouts to main layout
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)

    def assign_credit(self):
        # Show the guest list and allow search (same as Button 3 functionality)
        self.input_text.setEnabled(True)
        self.input_text.setText("")
        self.table.setVisible(True)
        self.table.cellClicked.connect(self.show_credit_popup)

    def show_credit_popup(self, row, column):
        guest_name = self.table.item(row, column).text()
        
        # Create the credit input popup
        credit_dialog = QDialog(self)
        credit_dialog.setWindowTitle(f"Assign Credit to {guest_name}")
        
        layout = QVBoxLayout()

        # Label
        label = QLabel(f"Enter Credit Amount for {guest_name}:")
        layout.addWidget(label)

        # Credit input (digits only)
        credit_input = QLineEdit(self)
        credit_input.setPlaceholderText("Credit Amount (Digits Only)")
        credit_input.setValidator(QIntValidator(0, 999999))  # Restrict to digits only
        layout.addWidget(credit_input)

        # Add buttons for validate and cancel
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.validate_credit(guest_name, credit_input.text(), credit_dialog))
        button_box.rejected.connect(credit_dialog.reject)
        layout.addWidget(button_box)

        credit_dialog.setLayout(layout)
        credit_dialog.exec_()

    def validate_credit(self, guest_name, credit_value, dialog):
        if credit_value.isdigit():
            # Print the guest name and associated credit value to the console
            print(f"Guest: {guest_name}, Credit: {credit_value}")
            dialog.accept()  # Close the popup
        else:
            print("Invalid input. Please enter digits only.")
    def show_webcam(self):
        self.webcam_window = WebcamWindow()
        self.webcam_window.exec_()

    def print_message(self):
        print("Button 2: Printing message to the console")

    def show_guest_list(self):
        # Enable typing in the input text bar
        self.input_text.setEnabled(True)
        self.input_text.setText("")
        self.table.setVisible(True)

    def search_guest(self, text):
        # Filter guest list based on the text entered
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            guest_name = item.text()
            # Show or hide the row depending on whether the search text matches
            self.table.setRowHidden(row, text.lower() not in guest_name.lower())

    def select_guest(self, row, column):
        # Get selected guest name and print it to the console
        guest_name = self.table.item(row, column).text()
        print(f"Selected Guest: {guest_name}")
        self.input_text.setText("")  # Clear the text input
        self.input_text.setEnabled(False)  # Disable the input again
        self.table.setVisible(False)  # Hide the guest list table


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
