import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget,
    QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
import paho.mqtt.client as mqtt

mqtt_topic = "casino/tickets"
MQTT_PORT = 1883
MQTT_ADRESS = "192.168.1.177"
MQTT_ADRESS = "localhost"

class MqttClient(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, broker=MQTT_ADRESS, port=1883, topic="casino/tickets"):
        super().__init__()
        self.broker = broker
        self.port = port
        self.topic = topic
        self.client = mqtt.Client()
        self.running = False

    def run(self):
        self.client.on_message = self.on_message
        self.client.connect(self.broker, self.port, 60)
        self.client.subscribe(self.topic)
        self.running = True
        self.client.loop_forever()

    def stop(self):
        self.running = False
        self.client.disconnect()

    def on_message(self, client, userdata, msg):
        message = msg.payload.decode()
        self.message_received.emit(message)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt MQTT Demo")

        # MQTT client thread
        self.mqtt_client = MqttClient()
        self.mqtt_client.message_received.connect(self.add_message)
        self.mqtt_client.start()

        # Layouts
        main_layout = QHBoxLayout()
        button_layout = QVBoxLayout()

        # Buttons
        self.buttons = [QPushButton(f"Button {i + 1}") for i in range(4)]
        for i, button in enumerate(self.buttons):
            button.clicked.connect(lambda _, x=i: self.show_button_popup(x + 1))
            button_layout.addWidget(button)

        # Message List
        self.message_list = QListWidget()
        self.message_list.itemClicked.connect(self.show_message_popup)

        # Add widgets to layout
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.message_list)

        # Set central widget
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def show_button_popup(self, button_number):
        popup = QMessageBox(self)
        popup.setWindowTitle("Button Pressed")
        popup.setText(f"You pressed Button {button_number}")
        popup.setStandardButtons(QMessageBox.Ok)
        QTimer.singleShot(1000, popup.accept)  # Auto-close after 1 second
        popup.exec_()

    def add_message(self, message):
        # Parse the message and format for display
        try:
            data = json.loads(message)
            name = data.get("prenom", "Unknown")[:4]  # First 4 letters of the name
            amount = data.get("montant", "0")
            # To add the other variables of the message, missing reason and target client
            display_text = f"{name}, {amount}"
            self.message_list.addItem(display_text)
        except json.JSONDecodeError:
            print("Error decoding message")

    def show_message_popup(self, item: QListWidgetItem):
        message = item.text()
        popup = QMessageBox(self)
        popup.setWindowTitle("Message Action")
        popup.setText(f"Do you want to print the message: {message}?")
        popup.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        popup.button(QMessageBox.Cancel).setText("Remove")
        result = popup.exec_()

        if result == QMessageBox.Yes:
            print(f"Printing message: {message}")
            self.message_list.takeItem(self.message_list.row(item))  # Remove message
        elif result == QMessageBox.Cancel:
            print(f"Removing message: {message}")
            self.message_list.takeItem(self.message_list.row(item))  # Remove message

    def closeEvent(self, event):
        self.mqtt_client.stop()
        self.mqtt_client.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
