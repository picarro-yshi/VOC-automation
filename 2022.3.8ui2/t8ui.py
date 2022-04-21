## VOC Automation: Calibration, experiment and calculation
## Yilin Shi | Picarro | 2022.2.8

## basic library
import sys
import os
import re
import time
import numpy as np
import datetime
import socket
from queue import Queue

import platform

opsystem = platform.system()  # 'Linux', 'Windows', 'Darwin'
print(opsystem)

import serial
import serial.tools.list_ports as ls

print([p.device for p in ls.comports()])

## for plots
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

## Qt GUI
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import *
from PyQt6 import QtCore, QtGui, QtWidgets

# from PyQt6.QtWidgets import QDialog, QApplication, QPushButton, QVBoxLayout
# from PyQt6.QtCore import QTimer, QSize, Qt

## hard-coded global parameters
port_in = 50070  ## backdoor, send data to fitter on analyzer
port_out = 40060  ## listener, get data from analyzer
analyzer_source = 'analyze_VOC_broadband_custom'  ## listener data key
rt = 2000  ## ms, Alicat label refresh time
spec_xt = 360  ## min, spectrum plot animation: x axis time window duration 400'=6h40', 500'=8h20'
baseline_time = 20  ## min, 20 min sample baseline time
MT_IP = '10.100.3.148'  ## Mettler Toledo scale TCP_IP
MT_PORT = 8001  ## Mettler Toledo scale TCP_PORT

## Customized file/libraries
from alicat import FlowController  # pip install alicat
import CmdFIFO_py3 as CmdFIFO
from Listener_py3 import Listener
import StringPickler_py3 as StringPickler
import style
from spviewer import t8  ## spectrum animation

jupyterpath = '../2022.2.18jupyter2/'  ## './' in same folder
sys.path.append(jupyterpath)  ## jupyternotebook re-write
from t6ju import *  ## droplet test
from t7tk import *  ## gas tank


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VOC Calibration")
        self.setGeometry(850, 50, 1200, 800)
        self.set_window_layout()
        if opsystem == 'Darwin':
            self.setMinimumSize(1200, 850)
        elif opsystem == 'Windows':
            self.setFixedSize(1200, 800)
        else:
            self.setMinimumSize(1200, 800)

    def set_window_layout(self):
        self.mainlayout()
        self.layout1()
        self.layout2()
        self.layout3()
        self.layout4()
        self.layout5()
        self.layout6()
        self.layout7()

    def mainlayout(self):
        mainLayout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tabs.addTab(self.tab1, "   ⬥ Experiment Settings   ")
        self.tabs.addTab(self.tab2, "     ⬥ Port Detection      ")
        self.tabs.addTab(self.tab3, " ⬥ Spectrum View Real Time ")
        # self.tab1.setStyleSheet('QTabBar::tab: selected { font-size: 18px; font-family: Courier; }')
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)
        self.show()

        ## initialize parameters
        self.baseline = []
        self.view_point = 0  # total points plotted in spectrum viewer window
        self.total_point = 0  # total points processed, for all three analyzer data source

        ####################### tab1 layout ###################
        self.L11 = QVBoxLayout()
        self.L12 = QHBoxLayout()
        self.L13 = QHBoxLayout()
        self.L11.addLayout(self.L12, 40)  ## up
        self.L11.addLayout(self.L13, 60)  ## down
        self.tab1.setLayout(self.L11)

        self.L14 = QVBoxLayout()
        self.L15 = QVBoxLayout()  ## figure here
        self.box15 = QGroupBox("Weight View Real Time")
        self.box15.setStyleSheet(style.box15())
        self.box15.setLayout(self.L15)
        self.L15.setContentsMargins(20, 25, 20, 10)  ##left, top, right, bottom

        self.L12.addLayout(self.L14, 10)
        self.L12.addWidget(self.box15, 90)

        self.L16 = QVBoxLayout()  ## scale, connection
        self.L17 = QVBoxLayout()  ## MFC
        self.box17 = QGroupBox("Master Flow Control - Alicat")
        self.box17.setStyleSheet(style.box17())
        self.box17.setLayout(self.L17)
        self.L17.setContentsMargins(10, 25, 10, 10)

        self.L18 = QVBoxLayout()  ## calibration
        self.box18 = QGroupBox("Calibration Factor")
        self.box18.setStyleSheet(style.box18())
        self.box18.setLayout(self.L18)
        self.L18.setContentsMargins(10, 25, 10, 10)

        self.L13.addLayout(self.L16, 25)
        self.L13.addWidget(self.box17, 40)
        self.L13.addWidget(self.box18, 35)

        self.L19 = QHBoxLayout()  ## scale
        self.L20 = QVBoxLayout()  ## connection
        self.box19 = QGroupBox("Scale")
        self.box19.setStyleSheet(style.box19())
        self.box19.setLayout(self.L19)
        self.L19.setContentsMargins(10, 20, 10, 10)

        self.box20 = QGroupBox("Test Equipment Connection")
        self.box20.setStyleSheet(style.box20())
        self.box20.setLayout(self.L20)
        self.L20.setContentsMargins(10, 25, 10, 10)

        self.L16.addWidget(self.box19, 30)
        self.L16.addWidget(self.box20, 70)

        ## tab2
        self.L201 = QVBoxLayout()
        self.tab2.setLayout(self.L201)

        ## tab3
        self.L301 = QVBoxLayout()
        self.tab3.setLayout(self.L301)

    ################### Spectrum plot window ############### numbered by 1
    def layout1(self):
        self.img = QLabel()
        self.pixmap = QPixmap('icons/picarro.png')
        self.img.setPixmap(
            self.pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb11 = QLabel('Yilin Shi | Version 2.0 | Spring 2022 | Santa Clara, CA    ')
        self.lb11.setFont(QFont('Arial', 9))
        self.lb11.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.lb12 = QLabel('Select data for plot:')
        self.e11 = QComboBox(self)
        combolist = ['broadband_gasConcs_176', 'broadband_gasConcs_280', 'broadband_gasConcs_962', 'broadband_gasConcs_3776','H2O']
        try:
            f = open(os.path.join('par1', 'datakey.txt'), 'r')
            temp = f.read()
            if temp not in combolist:
                combolist.insert(0, temp)
        except:
            print('error loading last used data key.')
        self.e11.addItems(combolist)
        self.lb10 = QLabel(' ')
        self.lb10.setStyleSheet('color: grey')

        self.b11 = QToolButton()
        self.b11.setIcon(QIcon("icons/list2.png"))
        self.b11.setIconSize(QSize(40, 40))
        self.b11.setToolTip("Get available data keys for plot.")
        self.b11.clicked.connect(self.func11)
        self.lb13 = QLabel('Get List')

        self.b12 = QToolButton()
        self.b12.setIcon(QIcon("icons/plot2.png"))
        self.b12.setIconSize(QSize(40, 40))
        self.b12.setToolTip("Plot selected data in extra window; may not work on Windows.\n"
                            "Cable connection is more stable than wifi for data transfer.\n"
                            "Maximum plot time is 6hx2, to prevent program crash.\n"
                            "Restart the program to plot again")
        self.b12.clicked.connect(self.func12)  ## plot in extra window, use outside file
        self.lb14 = QLabel('  View +')

        self.b13 = QToolButton()
        self.b13.setIcon(QIcon("icons/plot1.png"))
        self.b13.setIconSize(QSize(40, 40))
        self.b13.setToolTip("Plot selected data on Tab 3.\n"
                            "Cable connection is more stable than wifi for data transfer.\n"
                            "Plot may pause with wifi connection")
        self.b13.clicked.connect(self.specplot)  # wifi connection may stop after 4 min; cable is fine
        self.lb15 = QLabel('   View')

        self.b10 = QToolButton()
        self.b10.setIcon(QIcon("icons/stop1.png"))
        self.b10.setIconSize(QSize(40, 40))
        self.b10.setToolTip("Close")
        self.b10.clicked.connect(self.exitFunc)
        self.lb16 = QLabel('  Close')

        self.lb17 = QLabel(' ')
        self.lb18 = QLabel(' ')
        self.lb19 = QLabel(' ')

        self.g1 = QGridLayout()
        self.g1.addWidget(self.b11, 0, 0)
        self.g1.addWidget(self.b12, 0, 2)
        self.g1.addWidget(self.b13, 0, 4)
        self.g1.addWidget(self.b10, 0, 6)
        self.g1.addWidget(self.lb13, 1, 0)
        self.g1.addWidget(self.lb14, 1, 2)
        self.g1.addWidget(self.lb15, 1, 4)
        self.g1.addWidget(self.lb16, 1, 6)

        self.g1.addWidget(self.lb17, 0, 1)
        self.g1.addWidget(self.lb18, 0, 3)
        self.g1.addWidget(self.lb19, 0, 5)

        self.L21 = QHBoxLayout()
        self.L21.addLayout(self.g1)

        self.L14.addWidget(self.img)
        self.L14.addWidget(self.lb11)
        self.L14.addWidget(self.lb12)
        self.L14.addWidget(self.e11)
        self.L14.addWidget(self.lb10)
        self.L14.addLayout(self.L21)

        self.figure2 = plt.figure()  # weight plot on tab1
        self.canvas2 = FigureCanvas(self.figure2)
        self.toolbar2 = NavigationToolbar(self.canvas2, self)
        self.L15.addWidget(self.canvas2)
        # self.L15.addWidget(self.toolbar2)   #*** matplotlib tool bar

    ################### Scale, weight measurement ############### 2
    def layout2(self):
        self.L22 = QVBoxLayout()
        self.L23 = QVBoxLayout()

        self.rb21 = QRadioButton("US Solid Scale", self)
        self.rb22 = QRadioButton("Mettler Toledo Scale", self)
        self.rb22.setChecked(True)
        # self.rb21.toggled.connect(self.rb21_clicked)
        # self.rb22.toggled.connect(self.rb22_clicked)

        self.lb23 = QLabel("g  ")
        self.lb24 = QLabel("Time(s):")
        self.e21 = QLineEdit('180')
        self.e21.setToolTip("Weigh sample for a time (in seconds).")
        self.e21.setStyleSheet("background: lightgrey")

        self.lb29 = QLabel("0.00000")
        self.lb29.setFont(QFont('Times', 24))
        self.lb29.setStyleSheet("background-color: white")
        # self.lb29.setTextInteractionFlags(Qt.TextSelectableByMouse)   ##**** Pyqt5
        self.lb29.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.b21 = QToolButton()
        self.b21.setIcon(QIcon("icons/start1.png"))
        self.b21.setIconSize(QSize(40, 40))
        if opsystem == 'Windows':
            self.b21.setToolTip("Continuously measure and plot weight for a time.\n"
                                "Click 'Pause' first to re-start.")
        else:
            self.b21.setToolTip("Continuously measure and plot weight for a time")
        self.b21.clicked.connect(self.func21)
        self.lb26 = QLabel('   Start')

        self.b22 = QToolButton()
        self.b22.setIcon(QIcon("icons/arrow.png"))
        self.b22.setIconSize(QSize(40, 40))
        self.b22.setToolTip("Get current weight measurement")
        self.b22.clicked.connect(self.func22)
        self.lb27 = QLabel('  Weigh')

        self.b23 = QPushButton("  Pause  ")
        self.b23.clicked.connect(self.func23)
        self.b23.setToolTip("Pause weight plot.")
        self.b23.setEnabled(False)
        self.b23.setStyleSheet("font: bold")

        self.b24 = QPushButton("Resume")
        self.b24.clicked.connect(self.func24)
        self.b24.setToolTip("Resume current weight plot.")
        self.b24.setStyleSheet("font: bold")
        self.b24.setEnabled(False)

        self.lb20 = QLabel(" ")
        self.lb20.setStyleSheet("background-color: lightgrey")
        self.lb20.setWordWrap(True)

        self.g2 = QGridLayout()
        self.g2.addWidget(self.rb21, 0, 0, 1, 2)
        self.g2.addWidget(self.rb22, 1, 0, 1, 2)
        self.g2.addWidget(self.lb29, 2, 0, 1, 2)  # 0.00000
        self.g2.addWidget(self.lb23, 2, 2, 1, 1)  # g
        self.g2.addWidget(self.lb24, 3, 0, 1, 1)
        self.g2.addWidget(self.e21, 3, 1, 1, 1)

        self.g21 = QGridLayout()
        self.g21.addWidget(self.b21, 0, 0)
        self.g21.addWidget(self.lb26, 1, 0)
        self.g21.addWidget(self.b22, 0, 1)
        self.g21.addWidget(self.lb27, 1, 1)
        self.g21.addWidget(self.b23, 2, 0)
        self.g21.addWidget(self.b24, 2, 1)
        self.g21.addWidget(self.lb20, 3, 0, 1, 2)

        self.L22.addLayout(self.g2)
        self.L23.addLayout(self.g21)
        self.L19.addLayout(self.L22, 60)
        self.L19.addLayout(self.L23, 40)

    ################### Test Connection ############### 34
    def layout3(self):
        self.lb32 = QLabel("Analyzer port in")
        self.lb32.setToolTip("Send data to Analyzer port 50070 (backdoor).")
        self.lb33 = QLabel(" ")  ## status
        self.lb34 = QLabel("Analyzer port out")
        self.lb34.setToolTip("Receiving data from Analyzer port 40060 (listener).")
        self.lb35 = QLabel(" ")  ## status
        self.lb36 = QLabel("Alicat")
        self.lb37 = QLabel(" ")  ## status

        self.lb38 = QLabel("R/Data Drive")
        self.lb39 = QLabel(" ")
        self.lb41 = QLabel("US Solid Scale")
        self.lb42 = QLabel(" ")
        self.lb43 = QLabel("Mettler Toledo Scale")
        self.lb44 = QLabel(" ")

        self.b31 = QPushButton("Test")
        self.b31.clicked.connect(self.func31)
        self.b32 = QPushButton("Test")
        self.b32.clicked.connect(self.func32)
        self.b33 = QPushButton("Test")
        self.b33.clicked.connect(self.func33)
        self.b34 = QPushButton("Test")
        self.b34.clicked.connect(self.func34)
        self.b35 = QPushButton("Test")
        self.b35.clicked.connect(self.func35)
        self.b36 = QPushButton("Test")
        self.b36.clicked.connect(self.func36)

        self.b31.setStyleSheet("font: bold")
        self.b32.setStyleSheet("font: bold")
        self.b33.setStyleSheet("font: bold")
        self.b34.setStyleSheet("font: bold")
        self.b35.setStyleSheet("font: bold")
        self.b36.setStyleSheet("font: bold")

        self.g3 = QGridLayout()
        self.g3.addWidget(self.lb32, 2, 0)
        self.g3.addWidget(self.lb33, 2, 1)
        self.g3.addWidget(self.lb34, 3, 0)
        self.g3.addWidget(self.lb35, 3, 1)
        self.g3.addWidget(self.lb36, 4, 0)
        self.g3.addWidget(self.lb37, 4, 1)

        self.g3.addWidget(self.lb38, 5, 0)
        self.g3.addWidget(self.lb39, 5, 1)
        self.g3.addWidget(self.lb41, 6, 0)
        self.g3.addWidget(self.lb42, 6, 1)
        self.g3.addWidget(self.lb43, 7, 0)
        self.g3.addWidget(self.lb44, 7, 1)

        self.g3.addWidget(self.b31, 2, 2)
        self.g3.addWidget(self.b32, 3, 2)
        self.g3.addWidget(self.b33, 4, 2)
        self.g3.addWidget(self.b34, 5, 2)
        self.g3.addWidget(self.b35, 6, 2)
        self.g3.addWidget(self.b36, 7, 2)

        self.b30 = QToolButton()
        self.b30.setIcon(QIcon("icons/reset1.png"))
        self.b30.setIconSize(QSize(40, 40))
        self.b30.setToolTip("Test all equipment one by one")
        self.b30.clicked.connect(self.func30)
        self.lb45 = QLabel('Test ALL')
        self.lb45.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lb30 = QLabel(' ')
        self.lb30.setStyleSheet("background-color: lightgrey")

        self.g4 = QGridLayout()
        self.g4.addWidget(self.lb30, 0, 0, 1, 1)
        self.g4.addWidget(self.b30, 0, 1, 1, 1)
        self.g4.addWidget(self.lb45, 1, 1, 1, 1)

        self.L20.addLayout(self.g3)
        self.L20.addLayout(self.g4)

    ################### Alicat Flow Control ###############  567
    def layout4(self):
        minute = []
        for i in range(60):
            if i < 10:
                minute.append('0' + str(i))
            else:
                minute.append(str(i))

        hour = []
        for i in range(24):
            if i < 10:
                hour.append('0' + str(i))
            else:
                hour.append(str(i))

        self.lb51 = QLabel("Pressure (psi)")
        self.lb52 = QLabel(" ")
        self.lb52.setStyleSheet("background-color: lightgrey")
        self.lb60 = QLabel(" ")  # gap
        self.e51 = QLineEdit('14.9')
        self.e51.setDisabled(True)
        self.b51 = QPushButton("Change")
        self.b51.clicked.connect(self.func51)
        self.b51.setEnabled(False)

        self.lb53 = QLabel("Temp. (°C)")
        self.lb54 = QLabel(' ')
        self.lb54.setStyleSheet("background-color: lightgrey")
        self.e52 = QLineEdit('29')
        self.e52.setDisabled(True)

        self.lb55 = QLabel("MFC1 (SLPM)")
        self.lb56 = QLabel(' ')
        self.lb56.setStyleSheet("background-color: lightgrey")
        self.lb56.setFixedWidth(50)
        self.e53 = QLineEdit('0.95')
        self.e53.setToolTip('Dilution line\n1 SLPM Alicat')
        self.b52 = QPushButton("Change")
        self.b52.clicked.connect(self.func52)
        # self.b52.setEnabled(False)

        self.lb57 = QLabel("MFC2 (SCCM)")
        self.lb58 = QLabel(' ')
        self.lb58.setStyleSheet("background-color: lightgrey")
        self.e54 = QComboBox()
        self.e54.addItems(["50", "5", "10", "20", "30", "40", "80", "100"])
        self.e54.setEditable(True)
        self.e54.setToolTip('Bubble line\n100 SCCM Alicat')
        self.b53 = QPushButton("Change", self)
        self.b53.clicked.connect(self.func53)
        self.b53.setStyleSheet("font: bold")

        self.rb51 = QRadioButton("Droplet Test", self)
        self.rb52 = QRadioButton("Gas Tank Test", self)
        self.rb51.setChecked(True)     ## follow immediate after all radiobutton, otherwise python clapse

        self.rb51.setStyleSheet('color: red')
        self.rb52.setStyleSheet('color: black')
        self.rb51.toggled.connect(self.func54)
        self.rb52.toggled.connect(self.func55)

        self.g5 = QGridLayout()
        self.g5.addWidget(self.lb51, 0, 0)
        self.g5.addWidget(self.lb60, 0, 1)  ##gap
        self.g5.addWidget(self.lb52, 0, 2)
        self.g5.addWidget(self.e51, 0, 3)
        self.g5.addWidget(self.b51, 0, 4)

        self.g5.addWidget(self.lb53, 1, 0)
        self.g5.addWidget(self.lb54, 1, 2)
        self.g5.addWidget(self.e52, 1, 3)

        self.g5.addWidget(self.lb55, 2, 0)
        self.g5.addWidget(self.lb56, 2, 2)
        self.g5.addWidget(self.e53, 2, 3)
        self.g5.addWidget(self.b52, 2, 4)

        self.g5.addWidget(self.lb57, 3, 0)
        self.g5.addWidget(self.lb58, 3, 2)
        self.g5.addWidget(self.e54, 3, 3)
        self.g5.addWidget(self.b53, 3, 4)
        self.g5.addWidget(self.rb51, 4, 0, 1, 3)
        self.g5.addWidget(self.rb52, 4, 3, 1, 2)

        self.b61 = QToolButton()
        self.b61.setIcon(QIcon("icons/start1.png"))
        self.b61.setIconSize(QSize(40, 40))
        if self.rb51.isChecked():
            self.b61.setToolTip("Start experiment, send Alicat data to analyzer.\n"
                                "Record start time, format, yyyymmdd hh:mm.\n"
                                "You can change start time and will be saved again\n"
                                "when you click End Exp. button.")
        else:
            self.b61.setToolTip("Start experiment, record start time.\n"
                                "format, yyyymmdd hh:mm.\n"
                                "You can change start time\nand will be saved again\n"
                                "when you click End Exp. button.")
        self.b61.clicked.connect(self.func_start)
        self.b61.setEnabled(False)
        self.lb61 = QLabel('Start Exp.')
        self.lb61.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.b62 = QToolButton()
        self.b62.setIcon(QIcon("icons/zero.png"))
        self.b62.setIconSize(QSize(40, 40))
        self.b62.setToolTip("Stop Alicat flow.")
        self.b62.clicked.connect(self.func62)
        self.lb62 = QLabel('Stop Flow')
        self.lb62.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.b63 = QToolButton()
        self.b63.setIcon(QIcon("icons/droplet2.png"))
        self.b63.setIconSize(QSize(40, 40))
        if self.rb51.isChecked():
            self.b63.setToolTip("Steps:Stop flow\n->add sample \n->restore flow\n"
                                "->click this button to record time\n"
                                "(format, yyyymmdd hh:mm)\nand weight.")
        else:
            self.b63.setToolTip("Steps:disconnect Zero Air line\n-> connect sample line\n"
                                "-> wait until spike pass on spectrum viewer\n"
                                "-> click this button to record time\n"
                                "(format, yyyymmdd hh:mm)\nand tank concentration.")
        self.b63.clicked.connect(self.func_add)
        self.b63.setEnabled(False)
        self.lb63 = QLabel('Add Sample')
        self.lb63.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.b64 = QToolButton()
        self.b64.setIcon(QIcon("icons/stop.jpg"))
        self.b64.setIconSize(QSize(40, 40))
        if self.rb51.isChecked():
            self.b64.setToolTip("End this experiment,\nstop sending Alicat data to analyzer.\n"
                                "Record current time or\nyour input time as the end time.\n"
                                "Save start and add sample time again.\n"
                                "format, yyyymmdd hh:mm.")
        else:
            self.b64.setToolTip("End this experiment.\n"
                                "Record current time or\nyour input time as the end time.\n"
                                "Save start and add sample time again.\n"
                                "format, yyyymmdd hh:mm.")
        self.b64.clicked.connect(self.func_end)
        self.b64.setEnabled(False)
        self.lb64 = QLabel('End Exp.')
        self.lb64.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.lb70 = QLabel("  (suffix)")
        self.e70 = QLineEdit('')  # '' suffix
        self.e70.setToolTip('You may want to add a suffix to\nthe start date as your folder name.\n'
                            'Leave blank if not needed.')
        try:
            f = open(os.path.join('par1', 'suffix.txt'), 'r')
            temp = f.read()
            self.e70.setText(temp)
        except:
            print('error loading suffix.')

        self.e71 = QLineEdit('')  # 20220222' start
        self.e71.setToolTip('Experiment start date.\nFormat: yyyymmdd\nThis is used as folder name.')
        self.e72 = QComboBox()  # '08'
        self.e72.addItems(hour)
        self.e73 = QComboBox()  # '11'
        self.e73.addItems(minute)
        try:
            f = open(os.path.join('par1', 'start_date.txt'), 'r')
            temp = f.read()
            self.e71.setText(temp)
        except:
            print('error loading start time.')

        self.e74 = QLineEdit('')  # 20220222' add
        self.e74.setToolTip('Date when sample is added.\nFormat: yyyymmdd')
        self.e75 = QComboBox()  # '09'
        self.e75.addItems(hour)
        self.e76 = QComboBox()  # '11'
        self.e76.addItems(minute)

        self.e77 = QLineEdit('')  # 20220222' end
        self.e77.setToolTip('Date when experiment ends.\nFormat: yyyymmdd')
        self.e78 = QComboBox()  # '23'
        self.e78.addItems(hour)
        self.e79 = QComboBox()  # '59'
        self.e79.addItems(minute)

        self.b65 = QPushButton("Create New Exp.", self)
        self.b65.clicked.connect(self.func_create)
        self.b65.setStyleSheet("font: bold")
        self.b65.setToolTip("Create a folder named with today's date\n"
                            "+suffix (if needed) on the R drive,\n"
                            "for a new experiment and store values.")

        self.b66 = QPushButton("Terminate Current Exp.", self)
        self.b66.clicked.connect(self.func66)
        self.b66.setStyleSheet("font: bold")
        self.b66.setToolTip("Abandon current experiment without saving data.\n")
        self.b66.setEnabled(False)

        self.lb50 = QLabel(' \n  \n  ')
        self.lb50.setStyleSheet("background-color: lightgrey")

        self.box51 = QGroupBox()
        self.box52 = QGroupBox()
        self.box53 = QGroupBox()
        self.box54 = QGroupBox()
        self.box51.setStyleSheet(style.box51())
        self.box52.setStyleSheet(style.box52())
        self.box53.setStyleSheet(style.box53())
        self.box54.setStyleSheet(style.box54())

        self.L51 = QVBoxLayout()
        self.L52 = QVBoxLayout()
        self.L53 = QVBoxLayout()
        self.L54 = QVBoxLayout()
        self.L55 = QHBoxLayout()

        self.L51.addWidget(self.b61)
        self.L51.addWidget(self.lb61)
        self.L51.addWidget(self.e71)
        self.L51.addWidget(self.e72)
        self.L51.addWidget(self.e73)
        self.L51.addStretch()

        self.L52.addWidget(self.b62)
        self.L52.addWidget(self.lb62)
        self.L52.addWidget(self.e70)
        self.L52.addWidget(self.lb70)
        self.L52.addStretch()

        self.L53.addWidget(self.b63)
        self.L53.addWidget(self.lb63)
        self.L53.addWidget(self.e74)
        self.L53.addWidget(self.e75)
        self.L53.addWidget(self.e76)
        self.L53.addStretch()

        self.L54.addWidget(self.b64)
        self.L54.addWidget(self.lb64)
        self.L54.addWidget(self.e77)
        self.L54.addWidget(self.e78)
        self.L54.addWidget(self.e79)
        self.L54.addStretch()

        self.box51.setLayout(self.L51)
        self.box52.setLayout(self.L52)
        self.box53.setLayout(self.L53)
        self.box54.setLayout(self.L54)
        self.L51.setContentsMargins(1, 1, 1, 1)
        self.L52.setContentsMargins(1, 1, 1, 1)
        self.L53.setContentsMargins(1, 1, 1, 1)
        self.L54.setContentsMargins(1, 1, 1, 1)

        self.L55.addWidget(self.box51)
        self.L55.addWidget(self.box52)
        self.L55.addWidget(self.box53)
        self.L55.addWidget(self.box54)

        self.g7 = QGridLayout()
        self.g7.addWidget(self.b65, 0, 0, 1, 2)
        self.g7.addWidget(self.b66, 0, 2, 1, 2)
        self.g7.addWidget(self.lb50, 1, 0, 1, 4)

        self.L17.addLayout(self.g5)
        self.L17.addLayout(self.L55)
        self.L17.addLayout(self.g7)
        self.L17.addStretch()  # *** will tight the space

        ## refresh Alicat label
        self.timer = QTimer()
        self.timer.setInterval(rt)
        self.timer.timeout.connect(self.refresh_label)

        ## monitor baseline for droplet
        self.timer2 = QTimer()
        self.timer2.setInterval(600000)  ## ms, check baseline every 10 mins
        self.timer2.timeout.connect(self.track_baseline1)

        ## monitor baseline for gas tank
        self.timer3 = QTimer()
        self.timer3.setInterval(300000)  ## ms, check baseline every 5 mins
        self.timer3.timeout.connect(self.track_baseline2)

    ################### Calibration ###############
    def layout5(self):
        self.lb81 = QLabel("R/Data drive\nlocation")
        self.lb82 = QLabel("Sample")
        self.lb83 = QLabel("CID")
        self.lb84 = QLabel("Check ComboResults and verify spectrum shape:")
        self.lb85 = QLabel("Row")
        self.lb86 = QLabel("  ")

        self.lb87 = QLabel("Weight (g)")
        self.lb88 = QLabel("Molecular Weight")
        self.lb89 = QLabel("Baseline+n*σ \n(1 - 5)")
        self.lb90 = QLabel("Tank conc (ppm)")

        self.e81 = QTextEdit()
        self.e81.setFixedHeight(60)  ## box won't expand!
        try:
            f = open(os.path.join('par1', 'r_drive.txt'), "r")
            temp = f.read()
            self.e81.setPlainText(temp)
        except:
            if opsystem == 'Windows':
                self.e81.setPlainText('R:\crd_G9000\AVXxx\3610-NUV1022\R&D\Calibration')  ## Windows
            elif opsystem == 'Darwin':
                self.e81.setPlainText('/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/')  ## Mac
            else:
                self.e81.setPlainText('/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/')  ## Linux
            print('failed to load R drive location.')

        self.e82 = QLineEdit()  # '176 - Acetic Acid'
        try:
            f = open(os.path.join('par1', 'gas.txt'), "r")
            temp = f.read()
            if temp == '':
                self.e82.setText('176 - Acetic Acid')
                print('failed to load sample name.')
            else:
                self.e82.setText(temp)
        except:
            self.e82.setText('176 - Acetic Acid')
            print('failed to load sample name.')

        self.e83 = QLineEdit()  # '176'
        try:
            f = open(os.path.join('par1', 'cid.txt'), "r")
            temp = f.read()
            self.e83.setText(temp)
        except:
            self.e83.setText('176')
            print('failed to load sample name.')

        self.e84 = QLineEdit()  # '' row
        self.e84.setToolTip('Used for verify ComboLog files and view RMSE.\n'
                            'Row number in series of spectra that has the\n'
                            'same shape as the actual spectrum of the compound.\n'
                            'Leave black if unknow.')
        self.e85 = QLineEdit()  # weight '0.0090'

        self.e86 = QLineEdit()  # MW '60.052'
        try:
            f = open(os.path.join('par1', 'molecular_weight.txt'), "r")
            temp = f.read()
            self.e86.setText(temp)
        except:
            # self.e86.setText('60.052')
            print('No molecular weight value available.')

        self.e87 = QLineEdit('2')  # zero 2 < zero1 + pct*sigma
        self.e87.setToolTip('Input value between 1 and 5.\n'
                            'When baseline after peak is n*σ \n'
                            'more than the baseline before peak,\n'
                            'end the experiment.')

        self.e88 = QLineEdit()  # '4.97'
        self.e88.setToolTip('Actual gas tank concentration, ppm\nfound on tank label.')
        try:
            f = open(os.path.join('par1', 'tankconc.txt'), "r")
            temp = f.read()
            self.e88.setText(temp)
        except:
            print('No tank concentration value available.')

        # self.rb51.setChecked(True)
        self.lb90.setDisabled(True)
        self.e88.setDisabled(True)

        self.b83 = QPushButton("Test Row#", self)
        self.b83.clicked.connect(self.func83)
        self.b83.setStyleSheet("font: bold")
        self.b83.setToolTip("Search for row number.")
        self.b83.setEnabled(False)

        self.b84 = QPushButton("Pause", self)
        self.b84.clicked.connect(self.func84)
        self.b84.setStyleSheet("font: bold")
        self.b84.setToolTip("Pause the search for row number.")
        self.b84.setEnabled(False)

        self.b85 = QPushButton("Resume", self)
        self.b85.clicked.connect(self.func85)
        self.b85.setStyleSheet("font: bold")
        self.b85.setToolTip("Resume the search for row number.")
        self.b85.setEnabled(False)

        self.lb80 = QLabel("  \n  ")
        self.lb80.setStyleSheet("background-color: lightgrey")
        self.lb80.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.g8 = QGridLayout()
        self.g8.addWidget(self.lb81, 0, 0)
        self.g8.addWidget(self.lb82, 1, 0)
        self.g8.addWidget(self.lb83, 2, 0)
        self.g8.addWidget(self.lb84, 3, 0, 1, 3)  # 'verify spectrum'
        self.g8.addWidget(self.lb85, 4, 0)  # row
        self.g8.addWidget(self.b83, 5, 0)  # search
        self.g8.addWidget(self.b84, 5, 1)  # pause
        self.g8.addWidget(self.b85, 5, 2)  # resume
        self.g8.addWidget(self.lb87, 6, 0)  # weight
        self.g8.addWidget(self.lb88, 7, 0)  # MW
        self.g8.addWidget(self.lb89, 8, 0)  # sigma
        self.g8.addWidget(self.lb90, 9, 0)  # tank conc

        self.g8.addWidget(self.e81, 0, 1, 1, 2)  # r drive
        self.g8.addWidget(self.e82, 1, 1, 1, 2)  # '176 - Acetic Acid'
        self.g8.addWidget(self.e83, 2, 1, 1, 2)  # '176'
        self.g8.addWidget(self.e84, 4, 1, 1, 2)  # row 7600
        self.g8.addWidget(self.e85, 6, 1, 1, 2)  # weight
        self.g8.addWidget(self.e86, 7, 1, 1, 2)  # MW
        self.g8.addWidget(self.e87, 8, 1, 1, 2)  # sigma
        self.g8.addWidget(self.e88, 9, 1, 1, 2)  # tank conc

        self.b82 = QToolButton()
        self.b82.setIcon(QIcon("icons/list2.png"))
        self.b82.setIconSize(QSize(40, 40))
        self.b82.setToolTip("Fill in the start date (+suffix) to \nload parameters for this experiment.")
        self.b82.clicked.connect(self.func82)
        self.lb91 = QLabel('Load Exp.')

        self.b80 = QToolButton()
        self.b80.setIcon(QIcon("icons/start1.png"))
        self.b80.setIconSize(QSize(40, 40))
        self.b80.setToolTip("Calculate the Calibration factor.")
        self.b80.clicked.connect(self.func80)
        self.b80.setEnabled(False)
        self.lb92 = QLabel('Calculate')

        self.b81 = QPushButton("Close All Calibration Plots", self)
        self.b81.clicked.connect(self.func81)
        self.b81.setEnabled(False)
        self.b81.setStyleSheet("font: bold")

        self.g9 = QGridLayout()
        self.g9.addWidget(self.b82, 0, 0, 2, 1)
        self.g9.addWidget(self.lb91, 2, 0, 1, 1)
        self.g9.addWidget(self.b80, 0, 1, 2, 1)
        self.g9.addWidget(self.lb92, 2, 1, 1, 1)
        self.g9.addWidget(self.lb80, 0, 2, 2, 2)
        self.g9.addWidget(self.b81, 2, 2, 1, 2)

        self.L18.addLayout(self.g8)
        self.L18.addLayout(self.g9)
        self.L18.addStretch()

    ################### tab2  ###################
    def layout6(self):
        self.lb201 = QLabel("Your system:")
        self.rb201 = QRadioButton("Windows", self)
        self.rb202 = QRadioButton("Mac", self)
        self.rb203 = QRadioButton("Linux", self)

        if opsystem == 'Darwin':
            self.rb202.setChecked(True)
            self.rb201.setEnabled(False)
            self.rb203.setEnabled(False)
        elif opsystem == 'Linux':
            self.rb203.setChecked(True)
            self.rb201.setEnabled(False)
            self.rb202.setEnabled(False)
        else:
            self.rb201.setChecked(True)
            self.rb202.setEnabled(False)
            self.rb203.setEnabled(False)

        self.b200 = QPushButton("Get serial port names", self)
        self.b200.clicked.connect(self.func200)
        self.b200.setStyleSheet("font: bold")
        self.b200.setToolTip("Available serial ports on this computer")
        self.e200 = QTextEdit()
        portlist = [p.device for p in ls.comports()]
        self.e200.setPlainText(str(portlist))

        self.lb211 = QLabel("Analyzer")
        self.lb212 = QLabel("IP Address:")
        self.e201 = QLineEdit('')  ## 10.100.4.20
        self.lb213 = QLabel(" ")  ## port not found
        self.b201 = QPushButton("Detect", self)
        self.b201.clicked.connect(self.func201)
        self.b201.setStyleSheet("font: bold")
        self.b201.setToolTip("Detect connection.")

        self.lb214 = QLabel("Alicat:")
        self.lb215 = QLabel("Serial Port:")
        self.e202 = QLineEdit()  # '/dev/cu.usbserial-A908UXOQ' '/dev/tty.usbserial-A908UXOQ'
        self.lb216 = QLabel(" ")  ## port not found
        self.b202 = QPushButton("Detect", self)
        self.b202.clicked.connect(self.func202)
        self.b202.setStyleSheet("font: bold")
        self.b202.setToolTip("Detect the name of the port connected to Alicat.")

        self.lb217 = QLabel("US Solid Scale:")
        self.lb218 = QLabel("Serial Port:")
        self.e203 = QLineEdit()  # '/dev/cu.usbserial-14310'
        self.lb219 = QLabel(" ")
        self.b203 = QPushButton("Detect", self)
        self.b203.clicked.connect(self.func203)
        self.b203.setStyleSheet("font: bold")
        self.b203.setToolTip("Detect the name of the port connected to US Solid Scale.")

        self.lb220 = QLabel("Mettler Toledo Scale:")
        self.lb221 = QLabel("IP address:")
        self.e204 = QLineEdit()  # '10.100.3.148'
        self.lb222 = QLabel("Port:")  # '8001'
        self.e205 = QLineEdit()
        self.lb223 = QLabel(" ")
        self.b204 = QPushButton("Detect", self)
        self.b204.clicked.connect(self.func204)
        self.b204.setStyleSheet("font: bold")
        self.b204.setToolTip("Detect the name of the port connected to Mettler Toledo Scale.")

        try:
            f = open('par1/analyzer.txt', "r")
            temp = f.read()  # .splitlines()
            self.e201.setText(temp)  # analyzer
            f = open('par1/alicat.txt', "r")
            temp = f.read()
            self.e202.setText(temp)  # alicat
            f = open('par1/scale_uso.txt', "r")
            temp = f.read()
            self.e203.setText(temp)  # us solid
            f = open('par1/scale_mt.txt', "r")
            temp = f.read().splitlines()
            self.e204.setText(temp[0])  # MT
            self.e205.setText(temp[1])  # MT
        except:
            print('failed to load port names')

        self.g21 = QGridLayout()
        self.g21.addWidget(self.lb201, 0, 0)
        self.g21.addWidget(self.rb201, 1, 0)
        self.g21.addWidget(self.rb202, 2, 0)
        self.g21.addWidget(self.rb203, 3, 0)
        self.g21.addWidget(self.b200, 4, 0)
        self.g21.addWidget(self.e200, 5, 0, 1, 3)

        self.g21.addWidget(self.lb211, 6, 0)
        self.g21.addWidget(self.lb212, 7, 0)
        self.g21.addWidget(self.e201, 7, 1)
        self.g21.addWidget(self.b201, 7, 2)
        self.g21.addWidget(self.lb213, 8, 1)

        self.g21.addWidget(self.lb214, 9, 0)
        self.g21.addWidget(self.lb215, 10, 0)
        self.g21.addWidget(self.e202, 10, 1)
        self.g21.addWidget(self.b202, 10, 2)
        self.g21.addWidget(self.lb216, 11, 1)

        self.g21.addWidget(self.lb217, 12, 0)
        self.g21.addWidget(self.lb218, 13, 0)
        self.g21.addWidget(self.e203, 13, 1)
        self.g21.addWidget(self.b203, 13, 2)
        self.g21.addWidget(self.lb219, 14, 1)

        self.g21.addWidget(self.lb220, 15, 0)
        self.g21.addWidget(self.lb221, 16, 0)
        self.g21.addWidget(self.e204, 16, 1)
        self.g21.addWidget(self.b204, 16, 2)
        self.g21.addWidget(self.lb222, 17, 0)
        self.g21.addWidget(self.e205, 17, 1)
        self.g21.addWidget(self.lb223, 18, 1)

        self.L201.addLayout(self.g21)
        self.L201.addStretch()  # *** will tight the space

    ################### tab3  ###################
    def layout7(self):
        # self.lb301=QLabel("Spectrum Plot Real Time")
        # self.lb301.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.L301.addWidget(self.lb301)
        self.lb302 = QLabel(" ")

        self.b301 = QPushButton("Plot", self)
        self.b301.clicked.connect(self.specplot)
        self.b301.setStyleSheet("font: bold")
        # self.b301.setToolTip("Pause")

        self.b302 = QPushButton("Pause", self)
        self.b302.clicked.connect(self.func301)
        self.b302.setStyleSheet("font: bold")
        # self.b302.setToolTip("Pause")

        self.b303 = QPushButton("Resume", self)
        self.b303.clicked.connect(self.func302)
        self.b303.setStyleSheet("font: bold")

        self.figure1 = plt.figure()
        self.canvas1 = FigureCanvas(self.figure1)
        self.toolbar1 = NavigationToolbar(self.canvas1, self)
        self.L301.addWidget(self.canvas1)
        self.L301.addWidget(self.toolbar1)  # *** matplotlib tool bar
        self.L301.addWidget(self.b301)
        self.L301.addWidget(self.b302)
        self.L301.addWidget(self.b303)
        self.L301.addWidget(self.lb302)

    ################### Tab1 Functions ###############
    def func11(self):   # get key list
        try:
            host = self.e201.text()  ## IP address
            socket.create_connection((host, port_out), 5)  # only try 5s time out   ## 40060
            dm_queue = Queue(180)  ## data manager
            listener = Listener(dm_queue, host, port_out, StringPickler.ArbitraryObject, retry=True)
            for i in range(6):
                dm = dm_queue.get(timeout=5)
                print(dm['source'])
                if dm['source'] == analyzer_source:
                    break

            key1 = list(dm['data'].keys())
            key2 = sorted(key1)
            self.e11.clear()  # delete all items from comboBox
            self.e11.addItems(key2)
            self.lb10.setText(str(len(key2)) + ' data keys available for plot.')
        except:
            self.lb10.setText('Key error. Analyzer out port not ready.')

    def func12(self):  ## not working on Windows, plot not shown
        if self.func32():
            try:
                host = self.e201.text()
                socket.create_connection((host, port_out), 5)  # '10.100.4.20'   # 40060
                gas = self.e11.currentText()       # 'broadband_gasConcs_280'
                self.lb10.setText('Plotting spectrum...')
                t8.specviewer(host, port_out, gas, analyzer_source, self.view_point)
            except:
                self.lb10.setText('Error. Analyzer data out port not ready.')
        else:
            self.lb10.setText('Error. Analyzer data out port not ready.')

    def specplot(self):  ## may stop after a while on Wifi, but fine with Ethernet cable
        try:
            if self.func32():
                try:
                    self.canvas1.close_event()
                    self.figure1.clear()
                    self.plot1()
                    self.baseline = []  ## 20 min baseline value storage, restart when plot restarts
                    self.lb10.setText('Plotting spectrum on Tab 3. (Max. duration 6h x2)')
                except:
                    self.lb10.setText('Plot error.')
            else:
                self.lb10.setText('Error. Analyzer data out port not ready.')
        except:
            self.lb10.setText('Plotting failed, litto fitter may crashed.')

    def gen_spec(self):
        for i in range(self.total_point):
            yield i
        self.lb10.setText('Plot on Tab 3 has finished. Click View to start again.')
        self.anim1.pause()  # pause to prevent Python clapse. Queue will not stop and gen will restart

    def plot1(self):  # plot spectrum and retain baseline list
        try:
            self.nn = 0
            x = []     ## epoch time 1641259801
            xx = []    ## epoch time, x labels that will be marked
            xmak = []  ## clock time x label
            y = []
            jj = []    ## count of total points sent from listener

            host = self.e201.text()    ## IP address
            gas = self.e11.currentText()   # 'MFC2_flow'  'broadband_gasConcs_280'
            dm_queue = Queue(180)  ## data manager
            listener = Listener(dm_queue, host, port_out, StringPickler.ArbitraryObject, retry=True)

            ax1 = self.figure1.add_subplot(111)
            # fig, ax1 = plt.subplots()

            ## add some elements, measure speed time/point
            for j in range(20):
                dm = dm_queue.get(timeout=5)
                print(j)
                print(dm['source'])
                if dm['source'] == analyzer_source:
                    t = dm['time']    ## epoch time
                    x.append(t)
                    if len(xx) == 0:   # only add one element
                        xx.append(t)
                        xmak.append(time.strftime('%H:%M', time.localtime(t)))
                    y.append(dm['data'][gas])
                    jj.append(j)
                if len(y) == 4:
                    print('break. fitter data speed (s/pt), view window points, total points:')
                    break

            sec_pt = int(x[-1] - x[-2])  # speed, s/pt, typical 5, 6
            print(sec_pt)
            if sec_pt < 5:
                sec_pt = 5  # set uplimt of points, faster speed may have too many points
            self.view_point = int(spec_xt * 60 / sec_pt)
            print(self.view_point)
            ## total data points in animation, stop by then to prevent Python clapse
            self.total_point = self.view_point * (jj[-1] - jj[-2])
            print(self.total_point)  # 6h, 5s/pt is 4320 pt, 17280 total pt

            # def gen_spec():
            #     for i in range(20):
            #         yield i
            #     # i=0
            #     # while i<self.total_point:
            #     #     yield i
            #     #     i+=1
            #     self.lb10.setText('Plot on Tab 3 has finished. Click View to start new plot.')

            def animate(i):
                dm = dm_queue.get(timeout=5)
                print(i)
                if dm['source'] == analyzer_source:
                    if len(y) == self.view_point:  ## x-axis number
                        x.pop(0)
                        y.pop(0)

                    t = dm['time']
                    x.append(t)
                    y.append(dm['data'][gas])

                    baseline_pt = int(baseline_time * 60 / sec_pt)
                    if len(self.baseline) == baseline_pt:  ## baseline points
                        self.baseline.pop(0)
                    self.baseline.append(dm['data'][gas])

                    clock = time.strftime('%H:%M', time.localtime(t))       # current time
                    clock0 = time.strftime('%H:%M', time.localtime(x[-2]))  # previous time string
                    if ((clock0[-2:] == '59' and clock[-2:] == '00') or
                            (clock0[-2:] == '14' and clock[-2:] == '15') or
                            (clock0[-2:] == '44' and clock[-2:] == '45') or
                            (clock0[-2:] == '29' and clock[-2:] == '30')):
                        xx.append(t)
                        xmak.append(clock)

                    if (len(xx) > 0) and (xx[0] < x[0]):
                        xx.pop(0)
                        xmak.pop(0)

                    ax1.clear()
                    ax1.plot(x, y, linewidth=0.5)
                    ax1.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))  ## has to be inside
                    ax1.set_xticks(xx, xmak)
                    t1 = time.strftime("%Y%m%d")  # current time
                    ax1.set_xlabel('Clock Time (Y-M-D), %s-%s-%s' % (t1[:4], t1[4:6], t1[-2:]), fontsize=11)
                    ax1.set_ylabel('Concentration', fontsize=11)
                    ax1.set_title(gas)

                    print(self.nn)
                    print(time.ctime(t))
                    self.nn += 1

            ### format the plot
            # ax1.set_position([0.06, 0.1, 0.93, 0.88])  # left,bottom,width,height  ## axes position
            # ax1.tick_params(axis='x', which='major', labelsize=4)
            # ax1.tick_params(axis='y', which='major', labelsize=4, pad=-2)

            # self.anim1 = FuncAnimation(self.figure1, animate, interval=1000)
            self.anim1 = FuncAnimation(self.figure1, animate, frames=self.gen_spec(), interval=1000)
            # plt.show()  ## don't add this, otherwise will have extra blank plot
            self.canvas1.draw()

            ## save info local for the gui
            p = os.path.join('par1', 'datakey.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(gas)
        except:
            self.lb10.setText('Error, queue might be empty. Please restart.')

    ##################### Weight ######################
    def func21(self):  ## continuously plot, for both scale
        self.canvas2.close_event()
        self.figure2.clear()
        try:
            try:
                weightime = int(self.e21.text())
            except:
                weightime = 180
                self.e21.setText('180')
            if self.rb21.isChecked():
                self.plot2(weightime)
            else:
                self.plot3(weightime)
            self.b23.setEnabled(True)
            self.b24.setEnabled(False)
        except:
            self.lb20.setText('Error, please re-try.')

    def gen(self, weightime):
        for i in range(weightime):
            yield i
        self.b23.setEnabled(False)
        self.b24.setEnabled(False)

    def plot2(self, weightime):  ## US solid scale
        self.lb20.setText(' ')
        self.lb42.setText(' ')
        port_so = self.e203.text()
        # weightime = int(self.e21.text())
        try:
            self.lb20.setText(' ')
            self.serialPort = serial.Serial(port=port_so, baudrate=1200,
                                            bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
            # serialString = ""  # Used to hold data coming over UART

            xus = []
            yus = []
            ax2 = self.figure2.add_subplot(111)

            # def gen(n):
            #     i = 0
            #     while i <= n:
            #         i += 1
            #         yield i

            def animate(i):
                try:
                    serialString = self.serialPort.readline()
                    w1 = serialString.decode("utf-8")  ## Mac
                    weight = float(w1[5:12])
                    xus.append(i)
                    yus.append(weight)

                    ax2.clear()
                    ax2.plot(xus, yus, linewidth=0.5)
                    ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.4f'))  ## has to be inside

                    # plt.ticklabel_format(axis="x", style="sci", scilimits=(0, 0))
                    # plt.title('Single Species Calibration') ## has to be inside
                    # plt.xlabel('Time', fontsize=4)
                    # plt.ylabel('Weight, g', fontsize=4)
                    # plt.xlabel('Time')
                    # plt.ylabel('Weight, g')  ## will set all animation
                    ax2.set_ylabel('Weight, g', fontsize=6)
                    ax2.set_xlabel('Time, s', fontsize=6)
                    ax2.tick_params(axis='x', labelsize=6)
                    ax2.tick_params(axis='y', labelsize=6)

                    # plt.tight_layout()
                    # plt.xticks(fontsize=4)
                    # plt.yticks(fontsize=4)  ## equivalent to below ax.
                    # ax2.xaxis.set_tick_params(width=0.5) ## equivalent to below
                    # ax2.yaxis.set_tick_params(width=0.5)

                    plt.setp(ax2.xaxis.get_ticklines(), 'markersize', 1)
                    plt.setp(ax2.xaxis.get_ticklines(), 'markeredgewidth', 0.5)
                    plt.setp(ax2.yaxis.get_ticklines(), 'markersize', 1)
                    plt.setp(ax2.yaxis.get_ticklines(), 'markeredgewidth', 0.5)

                    ax2.spines["top"].set_linewidth(0.5)
                    ax2.spines["bottom"].set_linewidth(0.5)
                    ax2.spines["left"].set_linewidth(0.5)
                    ax2.spines["right"].set_linewidth(0.5)

                    self.lb20.setText(w1[5:12])
                    time.sleep(1)

                except:
                    self.lb20.setText('!Scale not found.')
                    print("US Solid scale animation error")

            self.anim2 = FuncAnimation(self.figure2, animate, frames=self.gen(weightime), repeat=False)
            # plt.show()
            self.canvas2.draw()
            self.lb42.setText('\u2713')
        except:
            self.lb42.setText('\u2717')
            self.lb20.setText('!Scale not found.')

    def plot3(self, weightime):  ## Mettler Toledo
        self.lb20.setText(' ')
        self.lb44.setText(' ')
        BUFFER_SIZE = 1024
        # weightime = int(self.e21.text())
        try:
            self.lb20.setText(' ')
            s = socket.create_connection((MT_IP, MT_PORT), 5)  # only try 5s time out
            s.settimeout(2)

            try:
                print(s.recv(BUFFER_SIZE))
                print('Mettler Toledo scale is ready.')
            except:
                print('Wake up the Mettler Toledo scale')
                s.send(b'@\r\n')  # Wake up scale
                k = s.recv(BUFFER_SIZE)  # = clear buffer
                # time.sleep(1)

            xus = []
            yus = []
            ax2 = self.figure2.add_subplot(111)

            # def gen(n):
            #     i = 0
            #     while i <= n:
            #         i += 1
            #         yield i

            def animate(i):
                try:
                    w1 = s.recv(BUFFER_SIZE)
                    w1 = w1.decode("utf-8")
                    weight = round(float(w1[3:15]), 5)
                    # print(weight)
                    xus.append(i)
                    yus.append(weight)

                    ax2.clear()
                    ax2.plot(xus, yus, linewidth=0.5)
                    ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.5f'))  ## has to be inside

                    ax2.set_ylabel('Weight, g', fontsize=6)
                    ax2.set_xlabel('Time, s', fontsize=6)
                    ax2.tick_params(axis='x', labelsize=6)
                    ax2.tick_params(axis='y', labelsize=6)

                    plt.setp(ax2.xaxis.get_ticklines(), 'markersize', 1)
                    plt.setp(ax2.xaxis.get_ticklines(), 'markeredgewidth', 0.5)
                    plt.setp(ax2.yaxis.get_ticklines(), 'markersize', 1)
                    plt.setp(ax2.yaxis.get_ticklines(), 'markeredgewidth', 0.5)

                    ax2.spines["top"].set_linewidth(0.5)
                    ax2.spines["bottom"].set_linewidth(0.5)
                    ax2.spines["left"].set_linewidth(0.5)
                    ax2.spines["right"].set_linewidth(0.5)

                    self.lb20.setText(w1[3:15])
                    time.sleep(1)

                except:
                    self.lb20.setText('Scale not found.')
                    print("Mettler Toledo scale animation error")

            self.anim2 = FuncAnimation(self.figure2, animate, frames=self.gen(weightime), repeat=False)
            # plt.show()
            self.canvas2.draw()
            self.lb44.setText('\u2713')
        except:
            self.lb44.setText('\u2717')
            self.lb20.setText('!Scale not found.')

    def func22(self):  ## read weight one time
        self.lb29.setText('')
        try:  # when animation is running, re-use lb20 value
            w2 = self.lb20.text()  ##string
            w3 = float(w2)  ## if cannot be converted to float, measure again
            w3 = round(w3, 5)
            self.lb29.setText(str(w3))
            self.e85.setText(str(w3))
            print('use label lb20')
        except:  # when no animation is not run
            print('measure oneself')
            self.lb20.setText(' ')
            if self.rb21.isChecked():  ## US Solid scale
                print('US Solid scale')
                self.func25()
            else:  ## MT scale
                print('MT scale')
                self.func26()

    def func23(self):  ## pause
        try:
            # if opsystem == 'Windows':  # close serial port
            #     self.serialPort.close()
            self.anim2.pause()
            self.lb20.setText('')
            self.b23.setEnabled(False)
            self.b24.setEnabled(True)
        except:
            self.lb20.setText('Error. Restart weight figure.')

    def func24(self):  # resume
        try:
            # if opsystem == 'Windows':   # need to reconnect serial port
            #     port_so = self.e203.text()
            #     self.serialPort = serial.Serial(port=port_so, baudrate=1200,
            #                                     bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
            self.anim2.resume()
            self.b23.setEnabled(True)
            self.b24.setEnabled(False)
        except:
            self.lb20.setText('Error. Restart weight figure.')

    def func25(self):  ## US Solid, read weight one time
        weight = self.func35()
        # print(weight)
        if weight is None:
            self.lb42.setText('\u2717')
            self.lb20.setText('!Scale not found.')
        else:
            self.lb29.setText(str(weight))
            self.e85.setText(str(weight))
            self.lb42.setText('\u2713')

    def func26(self):  ## MT scale, read weight one time
        weight = self.func36()
        # print(weight)
        if weight is None:
            self.lb44.setText('\u2717')
            self.lb20.setText('!Scale not found.')
        else:
            self.lb29.setText(str(weight))
            self.e85.setText(str(weight))
            self.lb44.setText('\u2713')

    #############  connection functions #############
    def func31(self):
        try:
            host = self.e201.text()
            socket.create_connection((host, port_in), 5)  # '10.100.3.123'   ## 50070
            ipadd = 'http://' + host
            MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection",
                                                    IsDontCareConnection=False)
            print(MeasSystem.GetStates())
            self.lb33.setText('\u2713')
            self.lb30.setText('Analyzer connected, port_in open.\nListening to data.')
            return 1
        except:
            self.lb33.setText('\u2717')
            self.lb30.setText('Analyzer not connected.\n')
            return 0

    def func32(self):
        try:
            host = self.e201.text()
            socket.create_connection((host, port_out), 5)
            dm_queue = Queue(180)  ## data manager
            listener = Listener(dm_queue, host, port_out, StringPickler.ArbitraryObject, retry=True)

            for i in range(10):
                dm = dm_queue.get(timeout=5)
                print(i)
                print(dm['source'])
                if dm['source'] == analyzer_source:
                    # print(i)
                    # print(dm)
                    self.lb35.setText('\u2713')
                    self.lb30.setText('Analyzer connected, port_out open.\nReceiving data in queue...')
                    return 1
                if i == 5:
                    self.lb35.setText('\u2717')
                    self.lb30.setText(analyzer_source + ' not exist. \n'
                                                        'litho_fitter on the analyzer may stop running.\n'
                                                        'Please start the fitter and try again.')
                    return 0
        except:
            self.lb35.setText('\u2717')
            self.lb30.setText('Analyzer not connected.\n')
            return 0

    def func33(self):
        try:
            port_ali = self.e202.text()
            flow_controller1 = FlowController(port=port_ali, address='A')
            flow_controller2 = FlowController(port=port_ali, address='C')
            print(flow_controller1.get())  ## need get, Bose AE2 soundlink will connect too
            print(flow_controller2.get())
            self.lb37.setText('\u2713')
            self.lb30.setText('Alicat is connected.\n')
            return 1
        except:
            self.lb37.setText('\u2717')
            self.lb30.setText('Alicat not connected.\n')
            return 0

    def func34(self):
        fnr = self.e81.toPlainText()
        if os.path.exists(fnr):
            self.lb39.setText('\u2713')
            self.lb30.setText('R/data drive is connected.')
            return 1
        else:
            self.lb39.setText('\u2717')
            self.lb30.setText('R/data drive not found. \n'
                              'Please attach the drive or check location \nin the calibration factor section.')
            return 0

    def func35(self):
        w2 = None
        try:
            port_so = self.e203.text()
            print(port_so)
            serialPort = serial.Serial(port=port_so, baudrate=1200,
                                       bytesize=8, timeout=5, stopbits=serial.STOPBITS_ONE)
            time.sleep(1)
            for i in range(8):
                # while (1):
                #     # Wait until there is data waiting in the serial buffer
                #     if serialPort.in_waiting > 0:
                #         # Read data out of the buffer until a carraige return / new line is found
                serialString = serialPort.readline()
                w1 = serialString.decode("utf-8")
                if w1[0] == 'G':
                    weight = float(w1[5:12])
                    w2 = round(weight, 5)
                    self.lb42.setText('\u2713')
                    self.lb30.setText('US Solid Scale connected.')
                    break
        except:
            self.lb42.setText('\u2717')
            self.lb30.setText('US Solid scale not found.')
        return w2

    def func36(self):
        weight = None
        try:
            BUFFER_SIZE = 1024
            s = socket.create_connection((MT_IP, MT_PORT), 5)  # only try 5s time out
            s.settimeout(2)
            print('Mettler Toledo Scale connected')

            try:
                print(s.recv(BUFFER_SIZE))
                print('Mettler Toledo scale is ready.')
            except:
                print('Wake up the Mettler Toledo scale')
                s.send(b'@\r\n')  # Wake up scale
            k = s.recv(BUFFER_SIZE)  # clear buffer

            k = s.recv(BUFFER_SIZE)
            k = k.decode("utf-8")
            weight = round(float(k[3:15]), 5)
            self.lb44.setText('\u2713')
            self.lb30.setText('Mettler Toledo Scale connected.')
        except:
            self.lb44.setText('\u2717')
            self.lb30.setText('Mettler Toledo Scale not connected.')
        return weight

    def func30(self):
        msg = ''
        eq = []
        if self.func31():
            eq.append('sender')
        if self.func32():
            eq.append('receiver')
        if self.func33():
            eq.append('ali')
        if self.func34():
            eq.append('rd')
        if self.func35():  ##None has same effect as 0
            eq.append('scales')
        if self.func36():
            eq.append('scalemt')

        if 'ali' not in eq:
            msg += '• Alicat not connected, cannot run experiment. \n'
        elif 'sender' in eq and 'receiver' in eq:
            msg += '• Analyzer and Alicat found, ready to start experiment! \n'
        else:
            msg += '• Analyzer not ready, cannot run experiment.\n'

        if 'rd' in eq:
            msg += '• R/data drive connected, ready to analyze data.\n'
        else:
            msg += '• R/data drive not found, cannot analyze data.\n'

        if 'scales' in eq or 'scalemt' in eq:
            if len(eq) == 5:
                self.lb30.setText('● All equipment available!')
            else:
                msg += '• Scale connected, ready to measurement weight.'
                self.lb30.setText(msg)
        else:
            msg += '• Scale not found, cannot measure weight.'  # ●
            self.lb30.setText(msg)
        # print(msg)

    ############## Flow control #############
    def func51(self):  # MFC2 pressure
        self.lb50.setText("change MFC2 pressure.\n\n")

    def func52(self):  ## change MFC1
        try:
            F1 = float(self.e53.text())  # dilution line
            if F1>1 or F1<0:
                self.lb50.setText('Input a value between 0-1.\n\n')
            else:
                port_ali = self.e202.text()
                flow_controller1 = FlowController(port=port_ali, address='A')
                flow_controller1.set_flow_rate(flow=F1)
                self.lb50.setText('Dilution line set to ' + str(F1) + '\n\n')
        except:
            self.lb50.setText('Unable to set MFC1 flow rate.\n\n')

    def func53(self):  ## change MFC2
        try:
            F2 = int(self.e54.currentText())  # bubbler line
            # print(F2)
            if F2>100 or F2<0:
                self.lb50.setText('Input a value between 0-100.\n\n')
            else:
                port_ali = self.e202.text()
                F1 = 1 - F2 / 1000  # dilution
                flow_controller1 = FlowController(port=port_ali, address='A')
                flow_controller2 = FlowController(port=port_ali, address='C')
                flow_controller1.set_flow_rate(flow=F1)
                flow_controller2.set_flow_rate(flow=F2)
                self.e53.setText(str(F1))
                self.lb50.setText('Bubble line set to ' + str(F2) + '\n\n')
        except:
            self.lb50.setText('Unable to set MFC2 flow rate. \n\n')

    def refresh_label(self):
        try:
            host = self.e201.text()
            port_ali = self.e202.text()
            ipadd = 'http://' + host

            flow_controller1 = FlowController(port=port_ali, address='A')
            flow_controller2 = FlowController(port=port_ali, address='C')
            fc1 = flow_controller1.get()
            fc2 = flow_controller2.get()
            MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection", IsDontCareConnection=False)
            # print ('MFC1: %.3f | MFC2: %.3f' % (fc1['mass_flow'], fc2['mass_flow']))

            ## sent measurement data on Alicat to analyzer fitting software
            # MeasSystem.Backdoor.SetData('MFC1_P_amb', fc1['pressure'])
            MeasSystem.Backdoor.SetData('MFC1_flow', fc1['mass_flow'])
            # MeasSystem.Backdoor.SetData('MFC1_flowset', fc1['setpoint'])

            MeasSystem.Backdoor.SetData('MFC2_P_amb', fc2['pressure'])
            MeasSystem.Backdoor.SetData('MFC2_T_amb', fc2['temperature'])
            MeasSystem.Backdoor.SetData('MFC2_flow', fc2['mass_flow'])
            # MeasSystem.Backdoor.SetData('MFC2_flowset', fc2['setpoint'])

            # self.lb53.setText(str(fc1['pressure']))
            # self.lb55.setText(str(fc1['temperature']))
            self.lb56.setText(str(fc1['mass_flow']))
            # self.lb59.setText(str(fc1['setpoint']))

            self.lb52.setText(str(fc2['pressure']))
            self.lb54.setText(str(fc2['temperature']))
            self.lb58.setText(str(fc2['mass_flow']))
            # self.lb74.setText(str(fc2['setpoint']))
        except:
            self.lb50.setText("Error. Analyzer not ready.\nPlease check connection.\n")

    def func54(self):  # rb51 clicked
        self.rb51.setStyleSheet('color: red')
        self.rb52.setStyleSheet('color: black')
        self.lb90.setDisabled(True)
        self.e88.setDisabled(True)
        self.lb87.setDisabled(False)
        # self.lb88.setDisabled(False)  #MW
        self.lb89.setDisabled(False)
        self.e85.setDisabled(False)
        # self.e86.setDisabled(False)
        self.e87.setDisabled(False)

        ## button tips
        self.b61.setToolTip("Start experiment, send Alicat data to analyzer.\n"
                            "Record start time, format, yyyymmdd hh:mm.\n"
                            "You can change start time and will be saved again\n"
                            "when you click End Exp. button.")
        self.b63.setToolTip("Steps:Stop flow ->add sample ->restore flow\n"
                            "->click this button to record time and weight.\n"
                            "time format, yyyymmdd hh:mm")
        self.b64.setToolTip("End this experiment, stop sending Alicat data to analyzer.\n"
                            "Record current time or your input time as the end time.\n"
                            "Save start and add sample time again.\n"
                            "format, yyyymmdd hh:mm.")

    def func55(self):  # rb52 clicked
        self.rb52.setStyleSheet('color: red')
        self.rb51.setStyleSheet('color: black')
        self.lb90.setDisabled(False)
        self.e88.setDisabled(False)
        self.lb87.setDisabled(True)
        # self.lb88.setDisabled(True)
        self.lb89.setDisabled(True)
        self.e85.setDisabled(True)
        # self.e86.setDisabled(True)
        self.e87.setDisabled(True)

        ## button tips
        self.b61.setToolTip("Start experiment.\n"
                            "Record start time, format, yyyymmdd hh:mm.\n"
                            "You can change start time and will be saved again\n"
                            "when you click End Exp. button.")
        self.b63.setToolTip("Steps:disconnect Zero Air line-> connect sample line\n"
                            "->click this button to record time and tank concentration.\n"
                            "time format, yyyymmdd hh:mm")
        self.b64.setToolTip("End this experiment.\n"
                            "Record current time or your input time as the end time.\n"
                            "Save start and add sample time again.\n"
                            "format, yyyymmdd hh:mm.")

    ############## Record experiment time #############
    def func_create(self):
        # clear entry fields
        self.e72.setCurrentText('00')
        self.e73.setCurrentText('00')
        self.e74.setText('')
        self.e75.setCurrentText('00')
        self.e76.setCurrentText('00')
        self.e77.setText('')
        self.e78.setCurrentText('00')
        self.e79.setCurrentText('00')
        self.e85.setText('')  # weight
        self.e88.setText('')  # tank conc

        if self.rb51.isChecked():
            self.func65()
        else:
            self.func71()

    def func_start(self):
        self.baseline = []  # reset
        if self.rb51.isChecked():
            self.func61()
        else:
            self.func72()

    def func_add(self):
        if self.rb51.isChecked():
            self.func63()
        else:
            self.func73()

    def func_end(self):
        if self.rb51.isChecked():
            self.func64()
        else:
            self.func74()

    ## input should be valid before sending to the function
    def func61(self):  ## start experiment, send Alicat data to analyzer, record time
        try:
            self.timer.start()  # send alicat data
            self.b65.setEnabled(False)

            fname = self.e81.toPlainText()
            gas = self.e82.text()
            ta1 = self.e71.text()
            suffix = self.e70.text()
            fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't1.txt')

            # ta1 = time.strftime("%Y%m%d")
            t2 = time.strftime("%H")
            t3 = time.strftime("%M")
            # self.e71.setText(ta1)       ## '20211124'
            self.e72.setCurrentText(t2)  ## '08'
            self.e73.setCurrentText(t3)  ## '00'

            if os.path.isfile(fnrt):
                os.remove(fnrt)
            with open(fnrt, 'a') as f:
                f.write(ta1 + '\n')
                f.write(t2 + '\n')
                f.write(t3 + '\n')

            self.b63.setEnabled(True)
            self.b66.setEnabled(True)
            self.epoch2 = int(time.time()) + baseline_time * 60 + 660  ##30 min later: 20 min baseline+10 min, see spike when turn on bubble line
            ep = time.strftime('%Y%m%d %H:%M:%S', time.localtime(self.epoch2))
            self.lb50.setText("Experiment started at %s:%s!\nPlease wait at least until %s:%s to add sample.\n\n"
                              % (t2, t3, ep[9:11], ep[12:14]))
        except:
            self.lb50.setText('Error start experiment.\n\n')

    ## parameters should be valid before sent to function
    def func62(self):  ## stop flow
        try:
            port_ali = self.e202.text()
            F2 = 0  # bubbler line
            F1 = 1 - F2 / 1000  # dilution
            flow_controller1 = FlowController(port=port_ali, address='A')
            flow_controller2 = FlowController(port=port_ali, address='C')
            flow_controller1.set_flow_rate(flow=F1)
            flow_controller2.set_flow_rate(flow=F2)

            self.e53.setText(str(F1))
            # self.e54.setCurrentText(str(F2))
            self.lb50.setText('MFC2 Bubble line stopped.\n\n')
        except:
            self.lb50.setText('Unable to stop the flow.\n\n')

    ## parameters should be valid before sent to function
    def func63(self):  ## add sample, record time, weight, get baseline 1 from animation function
        try:
            weight = self.e85.text()
            if int(time.time()) < self.epoch2:
                ep = time.strftime('%Y%m%d %H:%M:%S', time.localtime(self.epoch2))
                self.lb50.setText('Please wait at least 30 min,\nuntil %s:%s to add sample.\n' % (ep[9:11], ep[12:14]))
            elif weight == '':
                self.lb50.setText('Please type in sample weight.\n\n')
            else:
                self.timer2.start()  # track baseline
                ## get baseline 1:
                t1 = time.strftime("%Y%m%d")
                t2 = time.strftime("%H")
                t3 = time.strftime("%M")
                self.zero1 = np.mean(self.baseline[:-20])
                self.sigma1 = np.std(self.baseline[:-20])
                print('zero1')
                print(self.zero1)
                print(self.sigma1)

                fname = self.e81.toPlainText()
                gas = self.e82.text()
                ta1 = self.e71.text()
                suffix = self.e70.text()
                fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't2.txt')

                self.e74.setText(t1)  ## '20211124'
                self.e75.setCurrentText(t2)  ## '08'
                self.e76.setCurrentText(t3)  ## '00'

                if os.path.isfile(fnrt):
                    os.remove(fnrt)
                with open(fnrt, 'a') as f:
                    f.write(t1 + '\n')
                    f.write(t2 + '\n')
                    f.write(t3 + '\n')

                # user is allowed to change start time and will be saved again now
                fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't1.txt')
                if os.path.isfile(fnrt):
                    os.remove(fnrt)
                with open(fnrt, 'a') as f:
                    f.write(self.e71.text() + '\n')
                    f.write(self.e72.currentText() + '\n')
                    f.write(self.e73.currentText() + '\n')

                p = os.path.join(fname, gas, ta1 + suffix, 'par', 'weight.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(weight)

                self.b61.setEnabled(False)
                self.b64.setEnabled(True)
                self.lb50.setText("Sample added at %s:%s.\n"
                                  "Baseline before sample is about %.6E\n" % (t2, t3, self.zero1))
        except:
            self.lb50.setText('Error record add sample time.\n\n')

    def track_baseline1(self):  # monitor baseline for droplet, data sent by animation
        try:
            pct = float(self.e87.text())
            zero2 = np.mean(self.baseline)
            print('zero2')
            print(zero2)

            if zero2 < self.zero1 + self.sigma1 * pct:  # record value when sees baseline+n*sigma
                fname = self.e81.toPlainText()
                gas = self.e82.text()
                ta1 = self.e71.text()
                suffix = self.e70.text()
                fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't3.txt')

                t1 = time.strftime("%Y%m%d")
                t2 = time.strftime("%H")
                t3 = time.strftime("%M")
                self.e77.setText(t1)  ## '20211124'
                self.e78.setCurrentText(t2)
                self.e79.setCurrentText(t3)

                if os.path.isfile(fnrt):
                    os.remove(fnrt)
                with open(fnrt, 'a') as f:
                    f.write(t1 + '\n')
                    f.write(t2 + '\n')
                    f.write(t3 + '\n')

                self.lb50.setText('Concentration has dropped below baseline+%s sigma.\n'
                                  'You may stop experiment now.\n'
                                  'Baseline before: %.6E, now: %.6E' % (int(pct), self.zero1, zero2))
        except:
            self.lb50.setText('Cannot monitor baseline.\n'
                              'Check if real time spectrum plot on Tab 3 is running.')

    ## parameters should be valid before sent to function
    def func64(self):  ## stop sending data to analyzer, record time
        try:
            t1 = self.e77.text()
            self.timer2.stop()  # track baseline
            fname = self.e81.toPlainText()
            gas = self.e82.text()
            ta1 = self.e71.text()
            suffix = self.e70.text()
            fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't3.txt')

            if t1 == '':  # end time no data, write current time
                t1 = time.strftime("%Y%m%d")
                t2 = time.strftime("%H")
                t3 = time.strftime("%M")
                self.e77.setText(t1)  ## '20211124'
                self.e78.setCurrentText(t2)
                self.e79.setCurrentText(t3)
                self.lb50.setText('Experiment ended.\n'
                                  'Your baseline may still be higher than before experiment start.\n')
            else:  # use current data, user can input
                # t1 = self.e77.text()
                t2 = self.e78.currentText()
                t3 = self.e79.currentText()
                self.lb50.setText('Experiment ended at %s:%s.\n\n' % (t2, t3))

            if os.path.isfile(fnrt):
                os.remove(fnrt)
            with open(fnrt, 'a') as f:
                f.write(t1 + '\n')
                f.write(t2 + '\n')
                f.write(t3 + '\n')

            self.b61.setEnabled(False)
            self.b63.setEnabled(False)
            self.b64.setEnabled(False)
            self.b65.setEnabled(True)
            self.b66.setEnabled(False)
            self.timer.stop()  # stop send alicat data
        except:
            self.lb50.setText('Error end.\n\n')

    def func65(self):
        # check R, alicat connection, fill in time, create folder,enable buttons; start tab 3 plot for [baseline]
        fname = self.e81.toPlainText()
        gas = self.e82.text()
        cid = self.e83.text()
        MW = self.e86.text()
        pct = self.e87.text()

        if fname == '':
            self.lb50.setText('Please type in R drive location.\n\n')
        elif gas == '':
            self.lb50.setText('Please type in sample name.\n\n')
        elif cid == '':
            self.lb50.setText('Please type in CID number.\n\n')
        elif MW == '':
            self.lb50.setText('Please type in sample molecular weight.\n\n')
        elif pct == '':
            self.lb50.setText('Please type in number of sigmas.\n\n')

        elif len(self.baseline) == 0:
            self.lb50.setText('Error, please start the spectrum view real time on Tab 3 first.\n\n')
        elif not os.path.exists(fname):
            self.lb50.setText('Error, R/Data drive not found.\nPlease attach or check location.\n')
        elif not self.func33():  # alicat
            self.lb50.setText('Error, Alicat not connected.\n\n')
        elif not self.func31():
            self.lb50.setText('Error, analyzer backdoor not ready.\n\n')
        elif not self.func32():
            self.lb50.setText('Error, analyzer listener not ready.\n\n')

        else:
            try:
                ta1 = time.strftime("%Y%m%d")
                self.e71.setText(ta1)  ## '20211124'
                suffix = self.e70.text()
                fnr = os.path.join(fname, gas, ta1 + suffix)
                if os.path.exists(fnr):
                    self.lb50.setText('Error, folder %s already exists.\n'
                                      'Please delete folder or change suffix and try again.\n'% (ta1 + suffix))
                else:
                    os.mkdir(fnr)
                    fnrp = os.path.join(fnr, 'par')
                    os.mkdir(fnrp)

                    ## save info local for the gui
                    p = os.path.join('par1', 'r_drive.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e81.toPlainText())

                    p = os.path.join('par1', 'gas.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e82.text())

                    p = os.path.join('par1', 'cid.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e83.text())

                    p = os.path.join('par1', 'molecular_weight.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e86.text())

                    p = os.path.join('par1', 'start_date.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e71.text())

                    p = os.path.join('par1', 'suffix.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e70.text())

                    ## save info on R drive for this experiment
                    p = os.path.join(fnrp, 'gas.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e82.text())

                    p = os.path.join(fnrp, 'cid.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e83.text())

                    p = os.path.join(fnrp, 'molecular_weight.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e86.text())

                    self.b61.setEnabled(True)
                    self.lb50.setText('Experiment %s created!\nYou may start the experiment now.\n' % (ta1 + suffix))
            except:
                self.lb50.setText('Error creating experiment.\n\n')

    def func66(self):  # abandon current experiment
        reply = QMessageBox.question(self, 'Warning',
                                     "Are you sure to abandon current experiment?\n No data will be saved.",
                                     QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.rb51.isChecked():
                    try:
                        self.timer.stop()
                        self.timer2.stop()
                    except:
                        pass

                self.b61.setEnabled(False)
                self.b63.setEnabled(False)
                self.b64.setEnabled(False)
                self.b65.setEnabled(True)
                self.b66.setEnabled(False)

                if self.e74.text() != '' and self.e77.text() == "":
                    self.lb50.setText('Experiment terminated. You may stop the flow too.\n'
                                      'Warning: there might still be sample left in the system.\n'
                                      'Baseline is still higher than before experiment started.')
                else:
                    self.lb50.setText('Experiment terminated. You may stop the flow too.\n'
                                      'You can create a new experiment now.\n')
            except:
                self.lb50.setText('Error abandon the experiment.')

    ########## gas tank experiments
    def func71(self):
        # check R, fill in time, create folder,enable buttons
        fname = self.e81.toPlainText()
        gas = self.e82.text()
        cid = self.e83.text()

        if fname == '':
            self.lb50.setText('Please type in R drive location.\n\n')
        elif gas == '':
            self.lb50.setText('Please type in sample name.\n\n')
        elif cid == '':
            self.lb50.setText('Please type in CID number.\n\n')
        elif not os.path.exists(fname):
            self.lb50.setText('Error, R/Data drive not found.\nPlease attach or check location.\n')
        elif len(self.baseline) == 0:
            self.lb50.setText('Error, please start the spectrum view real time on Tab 3 first.\n\n')

        else:
            try:
                ta1 = time.strftime("%Y%m%d")
                self.e71.setText(ta1)  ## '20211124'
                suffix = self.e70.text()
                fnr = os.path.join(fname, gas, ta1 + suffix)
                if os.path.exists(fnr):
                    self.lb50.setText(
                        'Error, folder %s already exists.\nPlease delete or change suffix and try again.\n' % (
                                    ta1 + suffix))
                else:
                    os.mkdir(fnr)
                    fnrp = os.path.join(fnr, 'par')
                    os.mkdir(fnrp)

                    ## save info local for the gui
                    p = os.path.join('par1', 'r_drive.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e81.toPlainText())

                    p = os.path.join('par1', 'gas.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e82.text())

                    p = os.path.join('par1', 'cid.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e83.text())

                    if self.e86.text != '':
                        try:
                            p = os.path.join('par1', 'molecular_weight.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e86.text())
                        except:
                            pass

                    p = os.path.join('par1', 'start_date.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e71.text())

                    p = os.path.join('par1', 'suffix.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e70.text())

                    ## save info on R drive for this experiment
                    p = os.path.join(fnrp, 'gas.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e82.text())

                    p = os.path.join(fnrp, 'cid.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e83.text())

                    if self.e86.text != '':
                        try:
                            p = os.path.join(fnrp, 'molecular_weight.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e86.text())
                        except:
                            pass

                    self.b61.setEnabled(True)
                    self.lb50.setText('Experiment %s created!\nYou may start the experiment now.\n' % (ta1 + suffix))
            except:
                self.lb50.setText('Error creating experiment.\n\n')

    def func72(self):  ## start experiment, half hour baseline, record time
        try:
            self.b65.setEnabled(False)

            fname = self.e81.toPlainText()
            gas = self.e82.text()
            ta1 = self.e71.text()
            suffix = self.e70.text()
            fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't1.txt')

            # ta1 = time.strftime("%Y%m%d")
            t2 = time.strftime("%H")
            t3 = time.strftime("%M")
            # self.e71.setText(ta1)       ## '20211124'
            self.e72.setCurrentText(t2)  ## '08'
            self.e73.setCurrentText(t3)  ## '00'
            if os.path.isfile(fnrt):
                os.remove(fnrt)
            with open(fnrt, 'a') as f:
                f.write(ta1 + '\n')
                f.write(t2 + '\n')
                f.write(t3 + '\n')

            self.b63.setEnabled(True)
            self.b66.setEnabled(True)
            self.epoch2 = int(time.time()) + baseline_time * 60 + 660  ##30 min baseline, see spike when turn on tank
            ep = time.strftime('%Y%m%d %H:%M:%S', time.localtime(self.epoch2))
            self.lb50.setText("Experiment started at %s:%s!\nPlease wait at least 30 min, until %s:%s\n"
                              "to disconnect ZA and add sample." % (t2, t3, ep[9:11], ep[12:14]))
        except:
            self.lb50.setText('Error start experiment.\n\n')

    ## parameters should be valid before sent to function
    def func73(self):  ## switch tank, record time
        try:
            tank_conc = self.e88.text()
            if tank_conc == '':
                self.lb50.setText('Please type in tank concentration.\n\n')
            elif int(time.time()) < self.epoch2:  # current time < epoch2
                ep = time.strftime('%Y%m%d %H:%M:%S', time.localtime(self.epoch2))
                self.lb50.setText('Please wait at least 30 min,\nuntil %s:%s to add sample.\n' % (ep[9:11], ep[12:14]))
            else:
                self.timer3.start()  # track baseline
                # idx = self.baseline.index(self.epoch2)
                # self.zero1 = np.mean(self.baseline[:idx])
                # self.sigma1 = np.std(self.baseline[:idx])

                self.zero1 = np.mean(self.baseline[:-60])
                self.sigma1 = np.std(self.baseline[:-60])
                print('zero1')
                print(len(self.baseline))
                print(self.zero1)
                print(self.sigma1)

                fname = self.e81.toPlainText()
                gas = self.e82.text()
                ta1 = self.e71.text()
                suffix = self.e70.text()
                fnrp = os.path.join(fname, gas, ta1 + suffix, 'par')
                p = os.path.join(fnrp, 'tankconc.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e88.text())

                self.b61.setEnabled(False)
                self.b64.setEnabled(True)
                self.epoch3 = time.strftime("%H:%M")
                self.lb50.setText("Sample added at %s! Please run until baseline is stable.\n"
                                  "You will be notified by then.\n" % (self.epoch3))
        except:
            self.lb50.setText('Error record add sample time.\n\n')

    def track_baseline2(self):  # monitor baseline for gas tank, data sent by animation
        try:
            sigma2 = np.std(self.baseline)
            print('zero2')
            print(sigma2)
            # if zero2 > self.zero1*1.05:   ## inside value inside loop triggers python error, cannot use zero2
            #     self.zero1 = zero2

            if sigma2 > self.sigma1*1.05:   #1.02
                if self.e74.text() == '':
                    self.lb50.setText("Sample added at %s! Please run until baseline is stable.\n"
                                      "You will be notified by then.\n"
                                      "std before: %.6E, now: %.6E"%(self.epoch3, self.sigma1, sigma2))
                print('not leveled yet')
            # elif self.e74.text() == '':
            #     # save 30 min before as sample add time
            #     print('leveled for the first time')
            else:
                print('leveled')
                # past 30 min is sample time
                ep = time.strftime('%Y%m%d %H:%M:%S', time.localtime(int(time.time()-1800))) #20220329 11:02:15
                tb1 = ep[:8]
                tb2 = ep[9:11]
                tb3 = ep[12:14]
                self.e74.setText(tb1)  ## '20211124'
                self.e75.setCurrentText(tb2)  ## '08'
                self.e76.setCurrentText(tb3)  ## '00'

                fname = self.e81.toPlainText()
                gas = self.e82.text()
                ta1 = self.e71.text()
                suffix = self.e70.text()
                fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't2.txt')

                if os.path.isfile(fnrt):
                    os.remove(fnrt)
                with open(fnrt, 'a') as f:
                    f.write(tb1 + '\n')
                    f.write(tb2 + '\n')
                    f.write(tb3 + '\n')

                ## save current time as end time
                fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't3.txt')
                if os.path.isfile(fnrt):
                    os.remove(fnrt)
                with open(fnrt, 'a') as f:
                    f.write(time.strftime("%Y%m%d") + '\n')
                    f.write(time.strftime("%H") + '\n')
                    f.write(time.strftime("%M") + '\n')

                self.lb50.setText("Baseline is stable for the past 30 min.\n"
                                  "You may end the experiment now.\n"
                                  "std before: %.6E, now: %.6E"%(self.sigma1, sigma2))
        except:
            self.lb50.setText('Cannot monitor baseline.\n')

    ## parameters should be valid before sent to function
    def func74(self):  ## stop, record time, must be clicked
        try:
            tc1 = self.e77.text()
            if tc1 != '':  # user can input a time for end time
                t1 = self.e77.text()
                t2 = self.e78.currentText()
                t3 = self.e79.currentText()
            else:         # user current time for end time
                t1 = time.strftime("%Y%m%d")
                t2 = time.strftime("%H")
                t3 = time.strftime("%M")

            self.timer3.stop()  # track baseline
            fname = self.e81.toPlainText()
            gas = self.e82.text()
            ta1 = self.e71.text()
            suffix = self.e70.text()
            fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't3.txt')
            if tc1 == '':
                self.e77.setText(t1)  ## '20211124'
                self.e78.setCurrentText(t2)
                self.e79.setCurrentText(t3)

            if os.path.isfile(fnrt):
                os.remove(fnrt)
            with open(fnrt, 'a') as f:
                f.write(t1 + '\n')
                f.write(t2 + '\n')
                f.write(t3 + '\n')

            # user is allowed to change start, sample time and will be saved again now
            fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't1.txt')
            if os.path.isfile(fnrt):
                os.remove(fnrt)
            with open(fnrt, 'a') as f:
                f.write(self.e71.text() + '\n')
                f.write(self.e72.currentText() + '\n')
                f.write(self.e73.currentText() + '\n')

            fnrt = os.path.join(fname, gas, ta1 + suffix, 'par', 't2.txt')
            if os.path.isfile(fnrt):
                os.remove(fnrt)
            with open(fnrt, 'a') as f:
                f.write(self.e74.text() + '\n')
                f.write(self.e75.currentText() + '\n')
                f.write(self.e76.currentText() + '\n')

            self.b61.setEnabled(False)
            self.b63.setEnabled(False)
            self.b64.setEnabled(False)
            self.b65.setEnabled(True)
            self.b66.setEnabled(False)
            self.lb50.setText('Experiment ended at %s:%s.\n\n' % (t2, t3))
        except:
            self.lb50.setText('Error end.\n\n')

    ############## calculate calibration factor #############
    def func80(self):
        try:
            self.lb80.setText(" \n ")
            QApplication.processEvents()
            # fnla = '/home/picarro/I2000/Log/Archive/'  ## local drive Archive
            # fnlc = '/home/picarro/.combo_logger/ComboResults/'  ## local drive ComboResults

            ta1 = self.e71.text()  ## '20211124'
            ta2 = self.e72.currentText()  ## '08'
            ta3 = self.e73.currentText()  ## '00'
            tb1 = self.e74.text()  ## '20211124'
            tb2 = self.e75.currentText()  ## '23'
            tb3 = self.e76.currentText()  ## '59'
            tc1 = self.e77.text()  ## '20211124'
            tc2 = self.e78.currentText()  ## '23'
            tc3 = self.e79.currentText()  ## '59'

            fname = self.e81.toPlainText()
            gas = self.e82.text()
            suffix = self.e70.text()  ## ''
            fnr = os.path.join(fname, gas, ta1 + suffix)
            fnzip1 = os.path.join(fnr, 'RDFs')
            fnzip2 = os.path.join(fnr, 'PrivateData')
            fnzip3 = os.path.join(fnr, 'ComboResults')

            if (not ta1.isdigit()) or (len(ta1) != 8):
                self.lb80.setText('Start time format is wrong.\n Please revise as all numbers: yyyymmdd')
            elif (not tb1.isdigit()) or (len(tb1) != 8):
                self.lb80.setText('Sample time format is wrong.\n Please revise as all numbers: yyyymmdd')
            elif (not tc1.isdigit()) or (len(tc1) != 8):
                self.lb80.setText('End time format is wrong.\n Please revise as all numbers: yyyymmdd')
            elif not os.path.isdir(fname):
                self.lb80.setText('Error, R drive not found. \nPlease check or attach the data/R drive.')
            elif not os.path.isdir(fnr):
                self.lb80.setText('Error, folder %s not found. \nPlease check data folder name.' % (ta1 + suffix))
            elif not os.path.isdir(fnzip1):
                self.lb80.setText('Error, RDF files not found.')
            elif not os.path.isdir(fnzip2):
                self.lb80.setText('Error, PrivateData not found.')
            elif not os.path.isdir(fnzip3):
                self.lb80.setText('Error, ComboResults not found.')

            else:
                print('start calculating')
                cid = int(self.e83.text())
                row = self.e84.text()
                if row == '':
                    row1 = 500
                else:
                    row1 = int(row)  ## need to be int

                # print(ta1,ta2,ta3)
                # print(tb1,tb2,tb3)
                # print(tc1,tc2,tc3)
                # print(row1)

                if self.rb51.isChecked():
                    print('droplet test')
                    weight = float(self.e85.text())
                    MW = float(self.e86.text())
                    pct = float(self.e87.text())
                    # print(weight, MW, pct)

                    self.F1, self.F2, self.F3, self.F4 = \
                        jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3,
                                           row1, savefig=True)
                    # plt.waitforbuttonpress()  # any key to close all figure
                    # plt.close('all')

                    p = os.path.join(fnr, 'par', 'n_sigma.txt')
                    if os.path.isfile(p):
                        os.remove(p)
                    with open(p, 'a') as f:
                        f.write(self.e87.text())
                else:
                    print('gas tank')
                    tank_conc = float(self.e88.text())
                    self.F1, self.F2, self.F3, self.F4 = \
                        jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3,
                                           row1, savefig=True)

                ## write on R drive
                p = os.path.join(fnr, 'par', 'row.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e84.text())

                ## write on local for the gui
                p = os.path.join('par1', 'r_drive.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e81.toPlainText())

                p = os.path.join('par1', 'gas.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e82.text())

                p = os.path.join('par1', 'cid.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e83.text())

                if self.e86.text != '':
                    try:
                        p = os.path.join('par1', 'molecular_weight.txt')
                        if os.path.isfile(p):
                            os.remove(p)
                        with open(p, 'a') as f:
                            f.write(self.e86.text())
                    except:
                        pass

                p = os.path.join('par1', 'start_date.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e71.text())

                p = os.path.join('par1', 'suffix.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e70.text())

                f = open(os.path.join(fnr, 'par', 'calibration_factor.txt'), "r")
                cal = f.read()
                print(cal)
                self.lb80.setText('Calibration factor is \n' + cal)
                self.b81.setEnabled(True)

        except:
            self.lb80.setText('Error calculation.\nPlease run script to diagnose.')

    def func81(self):  ## close all calibration plots
        try:
            plt.close(self.F1)
            plt.close(self.F2)
            plt.close(self.F3)
            plt.close(self.F4)
            self.b81.setEnabled(False)
        except:
            pass

    def func82(self):  ## load parameters for an exisiting experiment
        ta1 = self.e71.text()  ## '20211124'
        if ta1 == '':
            self.lb80.setText('Please fill in the date (and suffix) \nfor your experiment first.')
        else:
            suffix = self.e70.text()  ## ''
            fname = self.e81.toPlainText()
            gas = self.e82.text()
            fnrp = os.path.join(fname, gas, ta1 + suffix, 'par')
            print(fnrp)

            if not os.path.isdir(fname):
                self.lb80.setText('Error, data not found. Check\nfolder name, R drive connection.')
            elif not os.path.isdir(fnrp):
                self.lb80.setText('Error, parameters not found.\n')
            else:
                try:
                    f = open(os.path.join(fnrp, 't1.txt'), 'r')
                    temp = f.read().splitlines()
                    print(temp)
                    self.e72.setCurrentText(temp[1])
                    self.e73.setCurrentText(temp[2])

                    f = open(os.path.join(fnrp, 't2.txt'), 'r')
                    temp = f.read().splitlines()
                    self.e74.setText(temp[0])
                    self.e75.setCurrentText(temp[1])
                    self.e76.setCurrentText(temp[2])

                    f = open(os.path.join(fnrp, 't3.txt'), 'r')
                    temp = f.read().splitlines()
                    self.e77.setText(temp[0])
                    self.e78.setCurrentText(temp[1])
                    self.e79.setCurrentText(temp[2])

                    f = open(os.path.join(fnrp, 'cid.txt'), 'r')
                    temp = f.read()
                    self.e83.setText(temp)

                    try:
                        f = open(os.path.join(fnrp, 'row.txt'), 'r')
                        temp = f.read()
                        self.e84.setText(temp)

                        f = open(os.path.join(fnrp, 'n_sigma.txt'), 'r')
                        temp = f.read()
                        self.e87.setText(temp)
                    except:
                        pass

                    if self.rb51.isChecked():
                        print('load droplet')
                        f = open(os.path.join(fnrp, 'weight.txt'), 'r')  # w, MW not required for gas tank
                        temp = f.read()
                        self.e85.setText(temp)
                        f = open(os.path.join(fnrp, 'molecular_weight.txt'), 'r')
                        temp = f.read()
                        self.e86.setText(temp)
                    else:
                        print('load gastank')
                        f = open(os.path.join(fnrp, 'tankconc.txt'), 'r')
                        temp = f.read()
                        self.e88.setText(temp)

                    self.b80.setEnabled(True)
                    self.b83.setEnabled(True)
                    self.lb80.setText('Parameters for experiment \n%s are loaded.' % (ta1 + suffix))
                except:
                    self.lb80.setText('Error loading experiment \n%s parameters.' % (ta1 + suffix))

    def func83(self):  ## test row
        try:
            ta1 = self.e71.text()  ## '20211124'
            suffix = self.e70.text()  ## ''
            fname = self.e81.toPlainText()
            gas = self.e82.text()
            row = self.e84.text()

            from spectral_logger1 import SpectralLogReader as slog
            fnr = os.path.join(fname, gas, ta1 + suffix)
            viewtime = 1000  ##ms, animation interval
            read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
            _, _, max_row = read.get_spectra_row('broadband', 100, pull_results=True)
            print('max row: ' + str(max_row))

            if row == '':
                rowrange = np.arange(100, int(max_row / 100) * 100, 100)
                self.lb80.setText('Click Pause \nwhen you see the spectrum')
                self.b84.setEnabled(True)
                self.b85.setEnabled(True)
                figure3 = plt.figure()
                ax3 = figure3.add_subplot(111)

                def gen():
                    for i in rowrange:
                        yield i

                def animate(i):
                    data = read.get_spectra_row('broadband', i, pull_results=True)
                    nu = data[0]['nu']
                    k = data[0]['absorbance']
                    model = data[0]['model']
                    ax3.clear()
                    ax3.plot(nu, k, linewidth=0.5)
                    ax3.plot(nu, model, linewidth=0.5)
                    ax3.set_ylabel('absorbance')
                    ax3.set_xlabel('nu, cm-1')
                    ax3.set_title('row: ' + str(i))

                self.anim3 = FuncAnimation(figure3, animate, frames=gen(), repeat=False, interval=viewtime)
                plt.show()

            else:
                self.b84.setEnabled(False)
                self.b85.setEnabled(False)
                data = read.get_spectra_row('broadband', int(row), pull_results=True)
                nu = data[0]['nu']
                k = data[0]['absorbance']
                model = data[0]['model']

                fig, ax = plt.subplots()
                ax.plot(nu, k)
                ax.plot(nu, model)
                ax.set_xlabel('nu, cm-1')
                ax.set_ylabel('absorbance')
                ax.set_title('row: ' + row)
                plt.show()
        except:
            self.lb80.setText('Error plotting ComboResults.')

    def func84(self):  ## pause
        try:
            self.anim3.pause()
        except:
            pass

    def func85(self):  ## resume
        try:
            self.anim3.resume()
        except:
            pass

    ################### Tab2 Functions ###############
    def func200(self):
        portusb = [p.device for p in ls.comports()]
        # print(portusb)
        self.e200.setPlainText(str(portusb))

    def func201(self):
        self.lb213.setText('')
        try:
            host = self.e201.text()
            socket.create_connection((host, port_out), 5)
            socket.create_connection((host, port_in), 5)
            self.lb213.setText('Analyzer connected')
            p = os.path.join('par1', 'analyzer.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(host)
        except:
            self.lb213.setText('!Analyzer not connected.')

    def func202(self):
        self.lb216.setText('...')
        QApplication.processEvents()
        port_ali = self.e202.text()

        if port_ali == '':
            portusb = [p.device for p in ls.comports()]  ## get current equipment list
            for i in reversed(portusb):
                print(i)
                try:
                    flow_controller1 = FlowController(port=i, address='A')
                    flow_controller2 = FlowController(port=i, address='C')
                    print(flow_controller1.get())  ## need get
                    print(flow_controller2.get())
                    port_ali = i
                    break
                except:
                    pass
        else:
            try:
                flow_controller1 = FlowController(port=port_ali, address='A')
                flow_controller2 = FlowController(port=port_ali, address='C')
                print(flow_controller1.get())
                print(flow_controller2.get())
            except:
                port_ali = ''

        if port_ali == '':
            self.lb216.setText('Port not found.')
        else:
            self.e202.setText(port_ali)
            self.lb216.setText('Port found.')

            p = os.path.join('par1', 'alicat.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(self.e202.text())

    def func203(self):
        self.lb219.setText('...')
        port_so = self.e203.text()

        if port_so == '':
            portusb = [p.device for p in ls.comports()]
            bk = False
            for i in reversed(portusb):
                print(i)
                try:
                    serialPort = serial.Serial(port=i, baudrate=1200,
                                               bytesize=8, timeout=5, stopbits=serial.STOPBITS_ONE)
                    time.sleep(1)
                    for j in range(4):  ## avoid infinity while loop
                        serialString = serialPort.readline()
                        w1 = serialString.decode("utf-8")
                        print(w1)
                        if any(s.isdigit() for s in w1):
                            port_so = i
                            bk = True
                            break
                    if bk:
                        break
                except:
                    pass
        else:
            try:
                serialPort = serial.Serial(port=port_so, baudrate=1200,
                                           bytesize=8, timeout=10, stopbits=serial.STOPBITS_ONE)
                serialString = serialPort.readline()
                w1 = serialString.decode("utf-8")
                print(w1)
            except:
                port_so = ''

        if port_so == '':
            self.lb219.setText('Port not found.')
        else:
            self.e203.setText(port_so)
            self.lb219.setText('Port found.')
            p = os.path.join('par1', 'scale_uso.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(self.e203.text())

    def func204(self):
        self.lb223.setText('')
        try:
            host = self.e204.text()
            port = self.e205.text()
            socket.create_connection((host, int(port)), 5)
            self.lb223.setText('Mettler Toledo scale connected')
            p = os.path.join('par1', 'scale_mt.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(host + '\n')
                f.write(port + '\n')
        except:
            self.lb223.setText('!Scale not connected.')

    ################### Tab3 Functions ###############
    def func301(self):
        try:
            self.anim1.pause()
            self.lb302.setText('Paused.')
        except:
            self.lb302.setText('Error.')

    def func302(self):
        try:
            self.anim1.resume()
            self.lb302.setText('Resumed.')
        except:
            self.lb302.setText('Error.')

    def exitFunc(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)

        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            # sys.exit()  ## not good, red warning message

    # def exitFunc(self):    ## Pyqt5
    #     mbox = QMessageBox.information(self, "Warning", "Are you sure to exit?", QMessageBox.No | QMessageBox.Yes,
    #                                    QMessageBox.Yes)
    #     if mbox == QMessageBox.Yes:
    #         # if os.path.isfile('par/par0.txt'):
    #         #     os.remove('par/par0.txt')
    #         # with open('par/par0.txt', 'a') as f:
    #         #     f.write(str(self.tabs.currentIndex()) + '\n')
    #         #     f.write(self.l04.text() + '\n')
    #         sys.exit()


def main():
    app = QApplication(sys.argv)
    window = Window()
    app.setWindowIcon(QIcon('icons/logo.png'))
    window.show()
    app.exec()


if __name__ == '__main__':
    main()

# @author: Yilin Shi   2022.2.1
# shiyilin890@gmail.com
