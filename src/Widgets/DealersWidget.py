
##################################################################################################################
"""
"""

import os
import random
import sys
from typing import List, Optional
from json import loads, dumps
from copy import deepcopy
from functools import partial
from threading import Thread
import tempfile
from datetime import datetime, time

# Libs
import numpy as np
import pandas as pd
import PySide6
from PySide6.QtCore import *
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QIcon

import plotly.express as px

# Local Imports
from src.ui_singleton import UiSingleton

##################################################################################################################


class DealersWidget:
    def __init__(self):
        # -> Load ui singleton
        self.ui = UiSingleton().interface

        # ---- Overview Gantt chart


    # ============================================================== METHODS
