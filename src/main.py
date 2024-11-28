

##################################################################################################################
"""
"""

import os
import sys
from typing import List, Optional
from json import loads, dumps
from copy import deepcopy
from functools import partial
from threading import Thread
import tempfile
from datetime import datetime, time
import random
from pprint import pprint

# Libs
from plyer import notification
import numpy as np
import pandas as pd
import PySide6
from PySide6.QtCore import *
from PySide6.QtCore import Qt
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QGridLayout, QVBoxLayout, QWidget, QLabel, QMessageBox
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QIcon

import plotly.express as px

# Local Imports
from ui_singleton import UiSingleton
from Widgets.DealersWidget import DealersWidget
from Widgets.PlayersWidget import PlayersWidget
# from printing_module.pdf_receipt_gen import generate_pos_ticket, pdf_path
# from printing_module.print_pdf import print_pdf_landscape

##################################################################################################################


START_AMOUNT = 1000


class Godopolis_OS:
    def __init__(self):
        # ----------------------------------- Load GUI
        app = QtWidgets.QApplication(sys.argv)

        # -> Load ui singleton
        self.ui = UiSingleton().interface

        root_path = str(os.getcwd())
        self.ui.setWindowIcon(QIcon(root_path + "/ros2_ws/src/gcs_mission_interface/gcs_mission_interface/resources/gcs_mission_interface_logo.jpeg"))
        self.ui.setWindowTitle("Godopolis Casino OS")

        # ----------------------------------- Event meta
        self.event_variables = {
            "event_date": datetime(year=2024, month=11, day=30)
            }

        # ----------------------------------- Create widgets
        self.init_dashboard()
        self.init_dealer_widget()
        self.init_player_widget()
        self.init_timeline_widget()

        # ----------------------------------- Final setup
        # -> Display windows
        self.ui.show()

        # ----------------------------------- Terminate ROS2 node on exit
        # self.ros_node.destroy_node()
        sys.exit(app.exec())

    # ========================================================== Misc
    def send_dealer_change_notification(self, dealer_name, game):
        print(f"{dealer_name.capitalize()} is scheduled for: {game}.")
        try:
            notification.notify(
                title="Dealer Change Notification",
                message=f"{dealer_name.capitalize()} is scheduled for: {game}.",
                timeout=10  # Time in seconds the notification will be visible
            )
        except Exception as e:
            print(f"Error sending notification: {e}")

    # ========================================================== Dashboard
    def init_dashboard(self):
        # Label to display status
        self.label = QLabel("Godopolis Casino")
        self.label.setStyleSheet("font-size: 18px;")
        self.label.setAlignment(Qt.AlignCenter)
        self.ui.verticalLayout_tickets.addWidget(self.label)

        # Input field for value
        self.value_input = QLineEdit()
        self.value_input.setReadOnly(True)  # Prevent typing, only number pad input
        self.value_input.setAlignment(Qt.AlignCenter)
        self.value_input.setStyleSheet("font-size: 24px; height: 50px; padding: 15px;")
        self.value_input.setPlaceholderText("Enter amount...")
        self.ui.verticalLayout_tickets.addWidget(self.value_input)

        # Number pad
        number_pad_layout = QGridLayout()
        buttons = {
            "7": (0, 0), "8": (0, 1), "9": (0, 2),
            "4": (1, 0), "5": (1, 1), "6": (1, 2),
            "1": (2, 0), "2": (2, 1), "3": (2, 2),
            "0": (3, 1), ".": (3, 0), "C": (3, 2),
        }

        for btn_text, pos in buttons.items():
            button = QPushButton(btn_text)
            button.clicked.connect(partial(self.handle_number_pad_input, btn_text))
            button.setStyleSheet("font-size: 18px; padding: 20px;")
            number_pad_layout.addWidget(button, pos[0], pos[1])

        self.ui.verticalLayout_tickets.addLayout(number_pad_layout)

        # Action buttons
        action_layout_1 = QHBoxLayout()

        print_button = QPushButton("Print ticket")
        print_button.setStyleSheet("font-size: 18px; padding: 15px;")
        print_button.clicked.connect(self.print_ticket)
        action_layout_1.addWidget(print_button)

        clear_button = QPushButton("Clear")
        clear_button.setStyleSheet("font-size: 18px; padding: 15px;")
        clear_button.clicked.connect(self.clear_value)
        action_layout_1.addWidget(clear_button)

        self.ui.verticalLayout_tickets.addLayout(action_layout_1)

        action_layout_2 = QHBoxLayout()

        credit_to_card_button = QPushButton("Credit to Card")
        credit_to_card_button.setStyleSheet("font-size: 18px; padding: 15px;")
        credit_to_card_button.clicked.connect(self.credit_to_card)
        action_layout_2.addWidget(credit_to_card_button)

        load_from_card_button = QPushButton("Load from Card")
        load_from_card_button.setStyleSheet("font-size: 18px; padding: 15px;")
        load_from_card_button.clicked.connect(self.load_from_card)
        action_layout_2.addWidget(load_from_card_button)

        self.ui.verticalLayout_tickets.addLayout(action_layout_2)

        # -> Load logs
        self.load_logs()

    def load_logs(self):
        # -> Clear plainTextEdit_bank_logs
        self.ui.plainTextEdit_bank_logs.clear()

        # -> Load logs from txt file
        with open("data/bank_logs.txt", "r") as file:
            logs = file.read()

        # -> Display logs
        self.ui.plainTextEdit_bank_logs.setPlainText(logs)
        self.ui.plainTextEdit_bank_logs.moveCursor(QtGui.QTextCursor.End)  # Scroll to the bottom

    def log_action(self, action, amount):
        # -> Log the action
        with open("data/bank_logs.txt", "a") as file:
            timestamp = datetime.now()
            timestamp = timestamp.replace(microsecond=0)

            file.write(f"{timestamp} - {action} - {amount}\n")

        # -> Reload logs
        self.load_logs()

    def handle_number_pad_input(self, btn_text):
        if btn_text == "C":  # Clear the last character
            current_text = self.value_input.text()
            self.value_input.setText(current_text[:-1])
        else:
            self.value_input.setText(self.value_input.text() + btn_text)

    def clear_value(self):
        # Clear the input field
        self.value_input.clear()

    def print_ticket(self):
        # Retrieve the value and perform the print action
        value = self.value_input.text()
        if value.strip():  # Ensure the value is not empty
            # -> Generate radio ticket id
            ticket_id = str(random.randint(100000, 999999))

            # TODO: Uncomment
            # generate_pos_ticket(ticket_id, "John Doe", amount=value)
            # print_pdf_landscape(pdf_path)
            pass

        # -> Clear the input field
        self.value_input.clear()

        # -> Log the action
        self.log_action(f"Printed ticket {ticket_id}", value)

    def credit_to_card(self):
        value = self.value_input.text()
        if value.strip():

            # TODO: Finish logic
            # > Open credit dialog
            reply = QMessageBox.question(self.ui,
                                         'Credit to card',
                                         f"Present card to credit: \n{value}",
                                         QMessageBox.Cancel|QMessageBox.Ok)

            if reply == QMessageBox.Cancel:
                pass

            else:
                self.value_input.clear()

                # -> Log the action
                self.log_action("Credited card", value)

    def load_from_card(self):
        value = random.randint(0, 1000)

        # TODO: Finish logic
        # > Open load dialog
        reply = QMessageBox.question(self.ui,
                                        'Load from card',
                                        f"Present card to load credits",
                                        QMessageBox.Cancel|QMessageBox.Ok)

        if reply == QMessageBox.Cancel:
            pass

        else:
            self.value_input.setText(str(value))

            # -> Log the action
            self.log_action("Loaded from card", value)

    # ========================================================== DealerWidget
    def init_dealer_widget(self):
        # > Create the WebEngine view
        self.gantt_web_view = QWebEngineView()

        # > Create initial gantt
        self.update_gantt_chart()

        # > Start a timer to update the chart every minute
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gantt_chart)
        self.timer.start(60000)

        # -> Connect buttons
        self.ui.pushButton_refresh_gantts.clicked.connect(self.update_gantt_chart)
        self.ui.layout_gantt_dealers.addWidget(self.gantt_web_view)

    def update_gantt_chart(self):
        # -> Update the gantt chart
        chart_path = self.create_dealer_gantt_chart()
        self.gantt_web_view.setUrl(f"file://{chart_path}")

        # -> Load data from CSV
        df = pd.read_csv("data/dealer_schedule.csv")

        # -> Convert Start_Time and End_Time to datetime
        df["Start_Time"] = pd.to_datetime(df["Start_Time"], format="%d/%m/%Y %H:%M")
        df["End_Time"] = pd.to_datetime(df["End_Time"], format="%d/%m/%Y %H:%M")

        # -> For each game, check if previous minute's dealer was different. If so, send a notification
        current_time = datetime.now().replace(second=0, microsecond=0)
        # current_time = datetime(year=2024, month=11, day=30, hour=16, minute=7, second=0)

        for index, row in df.iterrows():
            # Check if the current time is within the start and end time for the dealer shift and is within a minute of the start time
            if row['Start_Time'] <= current_time <= row['End_Time'] and current_time - row['Start_Time'] < pd.Timedelta(minutes=1):
                # Send a notification if the game is scheduled at the current time
                self.send_dealer_change_notification(row['Dealer'], row['Game'])

    def create_dealer_gantt_chart(self):
        # -> Load data from CSV
        df = pd.read_csv("data/dealer_schedule.csv")

        # -> Convert Start_Time and End_Time to datetime
        df["Start_Time"] = pd.to_datetime(df["Start_Time"], format="%d/%m/%Y %H:%M")
        df["End_Time"] = pd.to_datetime(df["End_Time"], format="%d/%m/%Y %H:%M")

        df = df.sort_values(by="Start_Time")

        # -> Create a Gantt chart using Plotly Express
        fig = px.timeline(
            df,
            x_start="Start_Time",
            x_end="End_Time",
            y="Activity",
            color="Dealer",
            title="Dealer Schedule",
            labels={"Dealer": "Dealers"},
            text="Activity"
        )

        # -> Update layout for better readability
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Activities",
            xaxis_tickformat="%H:%M",
            bargap=0.2,
            xaxis_range=["2024-11-30 18:45", "2024-12-01 00:45"],
            yaxis = dict(
                showticklabels=False,  # Hide the y-axis labels
                title=None,
                side="right",  # Position y-axis on the right
            ),
            legend=dict(
                orientation="h",  # Make the legend horizontal
                yanchor="bottom",  # Anchor the legend to the bottom
                y=1.05,  # Position it below the plot
                xanchor="center",  # Center the legend horizontally
                x=0.5,  # Align the legend to the center of the plot
            ),
            margin=dict(l=10, r=10, b=10)
        )

        # -> Add a vertical line for the current time
        # > Define the current time line as a shape
        current_time = datetime.now().replace(second=0, microsecond=0)

        # -> Change the day to the 30th
        current_time = current_time.replace(day=30)

        fig.add_shape(
            type="line",
            x0=current_time,
            y0=0,
            x1=current_time,
            y1=1,
            xref="x",
            yref="paper",  # "paper" makes it span vertically across the plot area
            line=dict(
                # color="red",
                width=1,
                dash="dash"
            ),
        )

        # > Add an annotation for the current time
        fig.add_annotation(
            x=current_time,
            y=1,
            text="Current Time",
            showarrow=False,
            xref="x",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            font=dict(color="red"),
        )

        # -> Save chart to a temporary HTML file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        fig.write_html(temp_file.name)
        return temp_file.name

    # ========================================================== TimelineWidget
    def init_timeline_widget(self):
        # > Create the WebEngine view
        self.timeline_web_view = QWebEngineView()

        # > Create initial timeline
        self.update_timeline_chart()

        # > Start a timer to update the chart every minute
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timeline_chart)
        self.timer.start(60000)

        # -> Connect buttons
        self.ui.pushButton_refresh_gantts.clicked.connect(self.update_timeline_chart)
        self.ui.layout_gantt_timeline.addWidget(self.timeline_web_view)

    def update_timeline_chart(self):
        # -> Update the timeline chart
        chart_path = self.create_timeline_chart()
        self.timeline_web_view.setUrl(f"file://{chart_path}")

    def create_timeline_chart(self):
        df = pd.read_csv("data/event_timeline.csv")

        # -> Convert Start_Time and End_Time to datetime
        df["Start_Time"] = pd.to_datetime(df["Start_Time"], format="%d/%m/%Y %H:%M")
        df["End_Time"] = pd.to_datetime(df["End_Time"], format="%d/%m/%Y %H:%M")

        # -> Create a Gantt chart using Plotly Express
        fig = px.timeline(
            df,
            x_start="Start_Time",
            x_end="End_Time",
            y="Activity",
            color="Activity",
            title="Evening Timeline",
            text="Activity",
        )

        # -> Update layout for better readability
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Activities",
            xaxis_tickformat="%H:%M",
            bargap=0.2,
            showlegend=False,
            xaxis_range=["2024-11-30 18:45", "2024-12-01 00:45"],
            yaxis=dict(
                showticklabels=False,  # Hide the y-axis labels
                title=None,  # Hide the y-axis title
                side="right",  # Position y-axis on the right
            ),
            margin=dict(l=10, r=10, b=10, t=35),
        )

        # -> Add a vertical line for the current time
        # > Define the current time line as a shape
        current_time = datetime.now().replace(second=0, microsecond=0)

        # -> Change the day to the 30th
        current_time = current_time.replace(day=30)

        fig.add_shape(
            type="line",
            x0=current_time,
            y0=0,
            x1=current_time,
            y1=1,
            xref="x",
            yref="paper",  # "paper" makes it span vertically across the plot area
            line=dict(
                # color="red",
                width=1,
                dash="dash"
            ),
        )

        # > Add an annotation for the current time
        fig.add_annotation(
            x=current_time,
            y=1,
            text="Current Time",
            showarrow=False,
            xref="x",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            font=dict(color="red"),
        )

        # -> Save chart to a temporary HTML file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        fig.write_html(temp_file.name)
        return temp_file.name

    # ========================================================== PlayerWidget
    def init_player_widget(self):
        self.load_players()
        self.sync_players()

        # -> Select the first player by default
        if self.ui.tableWidget_players_overview.rowCount() > 0:
            self.ui.tableWidget_players_overview.selectRow(0)

        # -> Connect buttons
        self.ui.pushButton_refresh_players.clicked.connect(self.sync_players)
        self.ui.lineEdit_searchbox_player.returnPressed.connect(self.find_player)
        self.ui.lineEdit_searchbox_player.textChanged.connect(self.filter_players)
        self.ui.pushButton_player_search.clicked.connect(self.find_player)
        self.ui.pushButton_player_add.clicked.connect(self.add_player)
        self.ui.pushButton_player_remove.clicked.connect(self.remove_player)
        self.ui.tableWidget_players_overview.selectionModel().selectionChanged.connect(self.select_player)
        # -> Connect double-click signal
        self.ui.tableWidget_players_overview.cellDoubleClicked.connect(self.fill_search_box)

    def add_player(self):
        # -> Get name
        name = self.ui.lineEdit_searchbox_player.text()

        if not name:
            return

        # -> Open confirmation dialog
        reply = QMessageBox.question(self.ui,
                                     'Confirmation',
                                     f"Add new player: {name}?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            # -> Add to dict
            self.players_dict[name] = self.player_template

            # -> Refresh table
            self.sync_players()

    def remove_player(self):
        # -> Get name
        name = self.ui.lineEdit_searchbox_player.text()

        if name not in self.players_dict.keys():
            return

        # -> Open confirmation dialog
        reply = QMessageBox.question(self.ui,
                                     'Confirmation',
                                     f"Remove player: {name}?",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            # -> Remove from dict
            self.players_dict.pop(name, None)

            # -> Refresh table
            self.sync_players()

    def find_player(self) -> Optional[dict]:
        # Get the input text from the search box
        name_fragment = self.ui.lineEdit_searchbox_player.text().strip().lower()

        if not name_fragment:
            return None

        # Find the closest match
        closest_match = None
        closest_distance = float('inf')

        for i in range(self.ui.tableWidget_players_overview.rowCount()):
            # Get the player name for the current row
            player_name = self.ui.tableWidget_players_overview.verticalHeaderItem(i).text()
            player_name_lower = player_name.lower()

            # Calculate the "distance" using simple substring containment or Levenshtein distance
            if name_fragment in player_name_lower:
                distance = len(player_name_lower) - len(name_fragment)
            else:
                # Fallback to Levenshtein distance (useful for fuzzy matching)
                distance = self.levenshtein_distance(name_fragment, player_name_lower)

            # Update the closest match if this is a better match
            if distance < closest_distance:
                closest_distance = distance
                closest_match = i

        if closest_match is not None:
            # Select the closest match in the table
            self.ui.tableWidget_players_overview.selectRow(closest_match)

            # Fill the search box with the closest match's name
            player_name = self.ui.tableWidget_players_overview.verticalHeaderItem(closest_match).text()
            self.ui.lineEdit_searchbox_player.clear()

            # Return the corresponding player data from the dictionary
            return self.players_dict.get(player_name, None)

        # If no match is found, show a warning
        QMessageBox.warning(self.ui,
                            'Warning',
                            f"No match found for '{name_fragment}'.",
                            QMessageBox.Ok)
        return None

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        # Create a distance matrix
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Initialize the matrix
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        # Fill the matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])

        return dp[m][n]

    def load_players(self):
        if os.path.exists("data/players.json"):
            with open("data/players.json", "r") as file:
                players_dict = loads(file.read())

            self.players_dict = players_dict

        else:
            self.players_dict = {}

    def save_players(self):
        with open("data/players.json", "w") as file:
            file.write(dumps(self.players_dict))

    def sync_players(self):
        # pprint(self.players_dict, indent=4)
        self.save_players()
        self.load_players()

        self.refresh_players_table()

    def fill_search_box(self, row, column):
        # Get the name of the player from the vertical header of the clicked row
        player_name_item = self.ui.tableWidget_players_overview.verticalHeaderItem(row)
        if player_name_item:  # Ensure the item exists
            player_name = player_name_item.text()
            # Set the name in the search box
            self.ui.lineEdit_searchbox_player.setText(player_name)

    def refresh_players_table(self):
        # -> Clear table
        self.ui.tableWidget_players_overview.setRowCount(0)

        # -> Construct pandas table from players_dict (or your DataFrame)
        df = pd.DataFrame(self.players_dict).T

        # -> Sort players by index
        df = df.sort_index()

        # -> Update table
        # > Set the column headers
        headers = ["Present", "Paid", "Chips ticket collected", "Final money", "Kill count"]
        self.ui.tableWidget_players_overview.setColumnCount(len(headers))
        self.ui.tableWidget_players_overview.setHorizontalHeaderLabels(headers)

        # > Set the ids (names) as the row headers
        self.ui.tableWidget_players_overview.setRowCount(len(df))
        self.ui.tableWidget_players_overview.setVerticalHeaderLabels(df.index.tolist())

        # > Enable word wrap for the row headers
        self.ui.tableWidget_players_overview.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        # > Set the data
        for i, (player_name, player_data) in enumerate(df.iterrows()):
            for j, value in enumerate(player_data):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make the cell read-only
                self.ui.tableWidget_players_overview.setItem(i, j, item)

        # > Resize columns to contents
        self.ui.tableWidget_players_overview.resizeColumnsToContents()

        # > Set last column elastic
        self.ui.tableWidget_players_overview.horizontalHeader().setStretchLastSection(True)

    def filter_players(self):
        # Get the current text from the search box
        filter_text = self.ui.lineEdit_searchbox_player.text().lower()

        # Show or hide rows based on the filter text
        for row in range(self.ui.tableWidget_players_overview.rowCount()):
            player_name = self.ui.tableWidget_players_overview.verticalHeaderItem(row).text().lower()
            is_match = filter_text in player_name
            self.ui.tableWidget_players_overview.setRowHidden(row, not is_match)

    def select_player(self):
        # -> Get the selected row (if any)
        selected_row = self.ui.tableWidget_players_overview.currentRow()

        if selected_row != -1:  # Check if a row is selected
            # Get the name of the selected player from the vertical header
            player_name_item = self.ui.tableWidget_players_overview.verticalHeaderItem(selected_row)
            player_name = player_name_item.text()

            # -> Clear the search box
            self.ui.lineEdit_searchbox_player.clear()

            # -> Set selected player name label
            self.ui.label_player_selected.setText(player_name)

            # -> Set the player data in the input fields
            # > Present checkbox
            self.ui.checkBox_player_present.setChecked(self.players_dict[player_name]["Present"])

            # > Paid checkbox
            self.ui.checkBox_player_paid.setChecked(self.players_dict[player_name]["Paid"])

            # > Chips ticket collected checkbox
            self.ui.checkBox_chips_ticket.setChecked(self.players_dict[player_name]["Chips ticket collected"])
            self.ui.pushButton_print_chips_ticket.setEnabled(not self.players_dict[player_name]["Chips ticket collected"])

            # > Connect signals
            self.ui.checkBox_player_present.clicked.connect(self.set_player_present)
            self.ui.checkBox_player_paid.clicked.connect(self.set_player_paid)
            self.ui.checkBox_chips_ticket.clicked.connect(self.set_chips_ticket_collected)
            self.ui.pushButton_print_chips_ticket.clicked.connect(self.print_chips_ticket)

            # > Final money spinbox
            self.ui.spinBox_final_money.setValue(self.players_dict[player_name]["Final money"])
            self.ui.spinBox_final_money.valueChanged.connect(self.set_player_final_money)

            # > Kill count spinbox
            self.ui.spinBox_kill_count.setValue(self.players_dict[player_name]["Kill count"])
            self.ui.spinBox_kill_count.valueChanged.connect(self.set_player_kill_count)

    def set_player_present(self):
        # -> Get the selected player name
        player_name = self.ui.label_player_selected.text()

        # -> Update the player data
        self.players_dict[player_name]["Present"] = self.ui.checkBox_player_present.isChecked()

        # -> Refresh table
        self.sync_players()

        # -> Log the action
        # self.log_action("Set player present", player_name)

    def set_player_paid(self):
        # -> Get the selected player name
        player_name = self.ui.label_player_selected.text()

        # -> Update the player data
        self.players_dict[player_name]["Paid"] = self.ui.checkBox_player_paid.isChecked()

        # -> Refresh table
        self.sync_players()

        # -> Log the action
        # self.log_action("Set player paid", player_name)

    def set_chips_ticket_collected(self):
        # -> Get the selected player name
        player_name = self.ui.label_player_selected.text()

        # -> Update the player data
        self.players_dict[player_name]["Chips ticket collected"] = self.ui.checkBox_chips_ticket.isChecked()

        # -> If the chips ticket is collected, disable the print button
        self.ui.pushButton_print_chips_ticket.setEnabled(not self.players_dict[player_name]["Chips ticket collected"])

        # -> Refresh table
        self.sync_players()

        # -> Log the action
        # self.log_action("Set chips ticket collected", player_name)

    def print_chips_ticket(self):
        # -> Get the selected player name
        player_name = self.ui.label_player_selected.text()

        # -> Print the chips ticket
        # > Generate radio ticket id
        ticket_id = str(random.randint(100000, 999999))
        # TODO: Uncomment
        # generate_pos_ticket(ticket_id, "John Doe", amount=START_AMOUNT)
        # print_pdf_landscape(pdf_path)

        # -> Set the chips ticket collected checkbox to True
        self.ui.checkBox_chips_ticket.setChecked(True)
        self.set_chips_ticket_collected()

        # -> Refresh table
        self.sync_players()

        # -> Log the action
        # self.log_action("Printed chips ticket", player_name)

    def set_player_final_money(self):
        # -> Get the selected player name
        player_name = self.ui.label_player_selected.text()

        # -> Update the player data
        self.players_dict[player_name]["Final money"] = self.ui.spinBox_final_money.value()

        # -> Refresh table
        self.sync_players()

    def set_player_kill_count(self):
        # -> Get the selected player name
        player_name = self.ui.label_player_selected.text()

        # -> Update the player data
        self.players_dict[player_name]["Kill count"] = self.ui.spinBox_kill_count.value()

        # -> Refresh table
        self.sync_players()

    @property
    def player_template(self):
        template = {
            'Present': False,
            'Paid': False,
            'Chips ticket collected': False,
            'Final money': 0,
            'Kill count': 0,
        }

        return deepcopy(template)


if __name__ == '__main__':
    window = Godopolis_OS()
