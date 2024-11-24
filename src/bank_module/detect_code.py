import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

def detect_qr_code(frame):
    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(frame)
    if bbox is not None and data:
        return data
    return None

class QRCodeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('QR Code Scanner')
        self.setGeometry(100, 100, 800, 600)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.capture = cv2.VideoCapture(0)  # Open webcam
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            # Detect QR code
            qr_data = detect_qr_code(frame)
            if qr_data:
                print(f"QR Code detected: {qr_data}")
                self.close_webcam()
                self.close()

            # Convert frame to QImage for displaying in PyQt5
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.label.setPixmap(QPixmap.fromImage(qt_image))

    def close_webcam(self):
        self.timer.stop()
        self.capture.release()
        cv2.destroyAllWindows()

    def closeEvent(self, event):
        self.close_webcam()
        event.accept()

def run_qr_code_scanner():
    app = QApplication(sys.argv)
    window = QRCodeWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_qr_code_scanner()
