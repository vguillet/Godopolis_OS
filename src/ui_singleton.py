
##################################################################################################################
"""
"""

# Built-in/Generic Imports
import os

# Libs
from PySide6 import QtCore, QtGui, QtUiTools

# Own modules
from ui_loader import uic

##################################################################################################################


class Singleton(type):
    __instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]


class UiSingleton(metaclass=Singleton):
    def __init__(self):
        root_path = str(os.getcwd())
        self.interface = uic.loadUi(f"{root_path}/Assets/main.ui")
