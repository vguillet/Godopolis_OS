

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
import numpy as np
import pandas as pd
import PySide6
from PySide6.QtCore import *
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QMessageBox
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QIcon

import plotly.express as px

# Local Imports
from ui_singleton import UiSingleton
from Widgets.DealersWidget import DealersWidget
from Widgets.PlayersWidget import PlayersWidget

##################################################################################################################


class Godopolis_OS:
    def __init__(self):
        # ----------------------------------- Load GUI
        app = QtWidgets.QApplication(sys.argv)

        # -> Load ui singleton
        self.ui = UiSingleton().interface

        root_path = str(os.getcwd())
        self.ui.setWindowIcon(QIcon(root_path + "/ros2_ws/src/gcs_mission_interface/gcs_mission_interface/resources/gcs_mission_interface_logo.jpeg"))
        self.ui.setWindowTitle("GCS Mission Interface")

        # ----------------------------------- Event meta
        self.event_variables = {
            "event_date": datetime(year=2024, month=11, day=30)
            }

        # ----------------------------------- Create widgets
        # ---- Dealers widget
        # -> Init
        # > Create the WebEngine view
        self.gantt_web_view = QWebEngineView()

        # > Create initial gantt
        self.update_gantt_chart()

        # > Start a timer to update the chart every minute
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gantt_chart)
        self.timer.start(60000)

        # -> Connect buttons
        self.ui.pushButton_refresh_schedule.clicked.connect(self.update_gantt_chart)
        self.ui.layout_gantt_dealers.addWidget(self.gantt_web_view)

        # ---- Players widget
        # -> Init
        self.players_dict = {}
        self.load_players()

        # -> Connect buttons
        self.ui.pushButton_refresh_players.clicked.connect(self.sync_players)
        self.ui.lineEdit_searchbox_player.returnPressed.connect(self.find_player)
        self.ui.pushButton_player_search.clicked.connect(self.find_player)
        self.ui.pushButton_player_add.clicked.connect(self.add_player)
        self.ui.pushButton_player_remove.clicked.connect(self.remove_player)
        self.ui.tableWidget_players_overview.selectionModel().selectionChanged.connect(self.select_player)

        # ----------------------------------- Final setup
        # -> Display windows
        self.ui.show()

        # ----------------------------------- Terminate ROS2 node on exit
        # self.ros_node.destroy_node()
        sys.exit(app.exec())

    # ========================================================== DealerWidget
    def update_gantt_chart(self):
        # -> Update the gantt chart
        chart_path = self.create_dealer_gantt_chart()
        self.gantt_web_view.setUrl(f"file://{chart_path}")

    def create_dealer_gantt_chart(self):
        # -> Load data from CSV
        # df = pd.read_csv("data/dealer_schedule.csv", sep="\t")

        # -> Convert Start_Time and End_Time to datetime
        # df["Start_Time"] = pd.to_datetime(df["Start_Time"], format="%d/%m/%Y %H:%M")
        # df["End_Time"] = pd.to_datetime(df["End_Time"], format="%d/%m/%Y %H:%M")

        df = pd.read_csv("data/gdealer_schedule.csv", sep="\t")
        df["Start_Time"] = pd.to_datetime(df["Start_Time"], format="%Y-%m-%d %H:%M:%S")
        df["End_Time"] = pd.to_datetime(df["End_Time"], format="%Y-%m-%d %H:%M:%S")

        # -> Create a Gantt chart using Plotly Express
        fig = px.timeline(
            df,
            x_start="Start_Time",
            x_end="End_Time",
            y="Game",
            color="Dealer",
            title="Dealer Assignments to Games Throughout the Night",
            labels={"Dealer": "Assigned Dealer"},
        )

        # -> Update layout for better readability
        fig.update_layout(
            xaxis_title="Time",
            yaxis_title="Games",
            xaxis_tickformat="%H:%M",
            bargap=0.2,
        )

        # -> Add a vertical line for the current time
        # > Define the current time line as a shape
        current_time = datetime.now().replace(second=0, microsecond=0)
        current_time = datetime(year=2024, month=11, day=30, hour=20, minute=random.randint(0, 59))

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
        # -> Get name
        name = self.ui.lineEdit_searchbox_player.text()

        if not name:
            return

        if name not in self.players_dict.keys():
            # -> Open warning dialog
            QMessageBox.warning(self.ui,
                                'Warning',
                                f"Player {name} not found.",
                                QMessageBox.Ok)

        else:
            # -> Find and select player row
            for i in range(self.ui.tableWidget_players_overview.rowCount()):
                item = self.ui.tableWidget_players_overview.verticalHeaderItem(i)
                if item.text() == name:
                    self.ui.tableWidget_players_overview.selectRow(i)
                    break

        return self.players_dict.get(name, None)

    def load_players(self):
        if os.path.exists("data/players.json"):
            with open("data/players.json", "r") as file:
                players_dict = loads(file.read())

            self.players_dict = players_dict

        self.sync_players()

    def save_players(self):
        with open("data/players.json", "w") as file:
            file.write(dumps(self.players_dict))

    def sync_players(self):
        pprint(self.players_dict, indent=4)

        self.save_players()
        self.refresh_players_table()

    def refresh_players_table(self):
        # -> Clear table
        self.ui.tableWidget_players_overview.setRowCount(0)

        # -> Construct pandas table from players_dict (or your DataFrame)
        df = pd.DataFrame(self.players_dict).T

        # -> Update table
        # > Set the column headers
        headers = ["Present", "Score"]
        self.ui.tableWidget_players_overview.setColumnCount(len(headers))
        self.ui.tableWidget_players_overview.setHorizontalHeaderLabels(headers)

        # > Set the ids (names) as the row headers
        self.ui.tableWidget_players_overview.setRowCount(len(df))
        self.ui.tableWidget_players_overview.setVerticalHeaderLabels(df.index.tolist())

        # > Enable word wrap for the row headers
        self.ui.tableWidget_players_overview.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents)

        # > Set the data
        for i, (index, row) in enumerate(df.iterrows()):
            for j, value in enumerate(row):
                self.ui.tableWidget_players_overview.setItem(i, j, QtWidgets.QTableWidgetItem(str(value)))

    def select_player(self):
        # -> Get the selected row (if any)
        selected_row = self.ui.tableWidget_players_overview.currentRow()

        if selected_row != -1:  # Check if a row is selected
            # Get the name of the selected player from the vertical header
            player_name_item = self.ui.tableWidget_players_overview.verticalHeaderItem(selected_row)
            player_name = player_name_item.text()

            # -> Update the search box
            self.ui.lineEdit_searchbox_player.setText(player_name)

    @property
    def player_template(self):
        template = {
            'Present': False,
            'Score': 0
        }

        return deepcopy(template)


if __name__ == '__main__':
    window = Godopolis_OS()
