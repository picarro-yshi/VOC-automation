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
port_in = 50070           ## backdoor, send data to fitter on analyzer
port_out = 40060          ## listener, get data from analyzer
rt = 2000                 ## ms, spectrum plot animation refresh time
spec_x = 1000             ## spectrum plot x axis data number

## Customized file/libraries
from alicat import FlowController     # pip install alicat
import CmdFIFO_py3 as CmdFIFO
from Listener_py3 import Listener
import StringPickler_py3 as StringPickler
import style
from spviewer import t8               ## spectrum animation

jupyterpath = '../2022.1.4jupyter/'   ## './' in same folder
sys.path.append(jupyterpath)          ## jupyternotebook re-write
from t5jup import *


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VOC Calibration")
        self.setGeometry(100, 80, 1200, 800)
        self.set_window_layout()
        if opsystem == 'Darwin':
            self.setMinimumSize(1200, 850)
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
        mainLayout=QVBoxLayout()
        self.tabs =QTabWidget()
        self.tab1=QWidget()
        self.tab2=QWidget()
        self.tab3=QWidget()
        self.tabs.addTab(self.tab1, "   ⬥ Experiment Settings   ")
        self.tabs.addTab(self.tab2, "     ⬥ Port Detection      ")
        self.tabs.addTab(self.tab3, " ⬥ Spectrum Plot Real Time ")
        # self.tab1.setStyleSheet('QTabBar::tab: selected { font-size: 18px; font-family: Courier; }')
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)
        self.show()


    ####################### tab1 layout ###################
        self.L11 = QVBoxLayout()
        self.L12 = QHBoxLayout()
        self.L13 = QHBoxLayout()
        self.L11.addLayout(self.L12, 40)   ## up
        self.L11.addLayout(self.L13, 60)   ## down
        self.tab1.setLayout(self.L11)

        self.L14 = QVBoxLayout()
        self.L15 = QVBoxLayout()           ## figure here
        self.box15 = QGroupBox("Weight Viewer Real Time")
        self.box15.setStyleSheet(style.box15())
        self.box15.setLayout(self.L15)
        self.L15.setContentsMargins(20, 30, 20, 10)   ##left, top, right, bottom

        self.L12.addLayout(self.L14, 10)
        self.L12.addWidget(self.box15, 90)

        self.L16 = QVBoxLayout()          ## scale, connection
        self.L17 = QVBoxLayout()          ## MFC
        self.box17 = QGroupBox("Master Flow Control - Alicat")
        self.box17.setStyleSheet(style.box17())
        self.box17.setLayout(self.L17)
        self.L17.setContentsMargins(10, 20, 10, 10)

        self.L18 = QVBoxLayout()          ## calibration
        self.box18 = QGroupBox("Calibration Factor")
        self.box18.setStyleSheet(style.box18())
        self.box18.setLayout(self.L18)
        self.L18.setContentsMargins(10, 20, 10, 10)

        self.L13.addLayout(self.L16, 25)
        self.L13.addWidget(self.box17, 40)
        self.L13.addWidget(self.box18, 35)

        self.L19 = QHBoxLayout()         ## scale
        self.L20 = QVBoxLayout()         ## connection
        self.box19 = QGroupBox("Scale")
        self.box19.setStyleSheet(style.box19())
        self.box19.setLayout(self.L19)
        self.L19.setContentsMargins(10, 20, 10, 10)

        self.box20 = QGroupBox("Test Equipment Connection")
        self.box20.setStyleSheet(style.box20())
        self.box20.setLayout(self.L20)
        self.L20.setContentsMargins(10, 30, 10, 10)

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
        self.img.setPixmap(self.pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb11 = QLabel('Yilin Shi | Version 1.0 | Spring 2022 | Santa Clara, CA')
        self.lb11.setFont(QFont('Arial', 8))
        self.lb11.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.lb12 = QLabel('Select data for plot:')
        self.e11 = QComboBox(self)
        combolist = ['broadband_gasConcs_280', 'broadband_gasConcs_962', 'H2O']
        self.e11.addItems(combolist)
        self.lb10 = QLabel(' ')

        self.b11 = QToolButton()
        self.b11.setIcon(QIcon("icons/list2.png"))
        self.b11.setIconSize(QSize(40, 40))
        self.b11.setToolTip("Get available data keys to plot.")
        self.b11.clicked.connect(self.func11)
        self.lb13 = QLabel('Get List')

        self.b12 = QToolButton()
        self.b12.setIcon(QIcon("icons/plot2.png"))
        self.b12.setIconSize(QSize(40, 40))
        self.b12.setToolTip("Plot selected data in extra window; may not work on Windows.\n"
                            "Cable connection is more stable than wifi for data transfer.")
        self.b12.clicked.connect(self.func12)  ## plot in extra window, use outside file
        self.lb14 = QLabel('  Plot +')

        self.b13 = QToolButton()
        self.b13.setIcon(QIcon("icons/plot1.png"))
        self.b13.setIconSize(QSize(40, 40))
        self.b13.setToolTip("Plot selected data on Tab 3.\n"
                            "Cable connection is more stable than wifi for data transfer.\n"
                            "Plot may pause with wifi connection")
        self.b13.clicked.connect(self.specplot)  #wifi connection may stop after 4 min; cable is fine
        self.lb15 = QLabel('    Plot')

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
        self.g1.addWidget(self.b11,  0, 0)
        self.g1.addWidget(self.b12,  0, 2)
        self.g1.addWidget(self.b13,  0, 4)
        self.g1.addWidget(self.b10,  0, 6)
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

        self.figure2 = plt.figure()
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
        self.rb21.setChecked(True)
        # self.rb21.toggled.connect(self.rb21_clicked)
        # self.rb22.toggled.connect(self.rb22_clicked)

        self.lb23 = QLabel("g  ")
        self.lb24 = QLabel("Time(s):")
        self.e21 =  QLineEdit('180')
        self.e21.setToolTip("Weigh sample for a time in seconds")
        self.e21.setStyleSheet("background: lightgrey")

        self.lb29 = QLabel("0.0000")
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
        self.lb26 = QLabel(' Start')
        # self.lb26.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.b22 = QToolButton()
        self.b22.setIcon(QIcon("icons/arrow.png"))
        self.b22.setIconSize(QSize(40, 40))
        self.b22.setToolTip("Get current measurement")
        self.b22.clicked.connect(self.func22)

        self.lb27 = QLabel(' Weigh')
        # self.lb27.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.b23=QPushButton("  Pause  ")
        self.b23.clicked.connect(self.func23)
        self.b23.setToolTip("Pause weight plot")
        self.b23.setEnabled(False)
        # self.b23.setStyleSheet("background-color: #f5ebe0")  ##shape changes??
        # self.b23.setStyleSheet("color: #774936")
        # self.b23.setStyleSheet("font: bold;background-color: #fdfcdc; border-radius : 5")
        self.b23.setStyleSheet("font: bold")
        self.b24=QPushButton("Resume")
        self.b24.clicked.connect(self.func24)
        self.b24.setToolTip("Resume current weight plot")
        self.b24.setStyleSheet("font: bold")
        self.b24.setEnabled(False)

        self.lb20 = QLabel(" ")
        self.lb20.setStyleSheet("background-color: lightgrey")
        self.lb20.setWordWrap(True)

        self.g2 = QGridLayout()
        self.g2.addWidget(self.rb21,  0, 0, 1, 2)
        self.g2.addWidget(self.rb22,  1, 0, 1, 2)
        self.g2.addWidget(self.lb29,  2, 0, 1, 2)
        self.g2.addWidget(self.lb23,  2, 2, 1, 1)    #g
        self.g2.addWidget(self.lb24,  3, 0, 1, 1)
        self.g2.addWidget(self.e21,   3, 1, 1, 1)

        self.g21 = QGridLayout()
        self.g21.addWidget(self.b21,   0, 0)
        self.g21.addWidget(self.lb26,  1, 0)
        self.g21.addWidget(self.b22,   0, 1)
        self.g21.addWidget(self.lb27,  1, 1)
        self.g21.addWidget(self.b23,   2, 0)
        self.g21.addWidget(self.b24,   2, 1)
        self.g21.addWidget(self.lb20,  3, 0, 1, 2)

        self.L22.addLayout(self.g2)
        self.L23.addLayout(self.g21)
        self.L19.addLayout(self.L22, 60)
        self.L19.addLayout(self.L23, 40)

    ################### Test Connection ############### 34
    def layout3(self):
        self.lb32 = QLabel("Analyzer port in")
        self.lb32.setToolTip("Send data to Analyzer port 50070")
        self.lb33 = QLabel(" ")   ## status
        self.lb34 = QLabel("Analyzer port out")
        self.lb34.setToolTip("Receiving data from Analyzer port 40060")
        self.lb35 = QLabel(" ")  ## status
        self.lb36 = QLabel("Alicat")
        self.lb37 = QLabel(" ")  ## status

        self.lb38 = QLabel("R/Data Drive")
        self.lb39 = QLabel(" ")
        self.lb41 = QLabel("US Solid Scale")
        self.lb42 = QLabel(" ")
        self.lb43 = QLabel("Mettler Toledo Scale")
        self.lb44 = QLabel(" ")

        self.b31=QPushButton("Test")
        self.b31.clicked.connect(self.func31)
        self.b32=QPushButton("Test")
        self.b32.clicked.connect(self.func32)
        self.b33=QPushButton("Test")
        self.b33.clicked.connect(self.func33)
        self.b34=QPushButton("Test")
        self.b34.clicked.connect(self.func34)
        self.b35=QPushButton("Test")
        self.b35.clicked.connect(self.func35)
        self.b36=QPushButton("Test")
        self.b36.clicked.connect(self.func36)

        self.b31.setStyleSheet("font: bold")
        self.b32.setStyleSheet("font: bold")
        self.b33.setStyleSheet("font: bold")
        self.b34.setStyleSheet("font: bold")
        self.b35.setStyleSheet("font: bold")
        self.b36.setStyleSheet("font: bold")

        self.g3 = QGridLayout()
        self.g3.addWidget(self.lb32,  2, 0)
        self.g3.addWidget(self.lb33,  2, 1)
        self.g3.addWidget(self.lb34,  3, 0)
        self.g3.addWidget(self.lb35,  3, 1)
        self.g3.addWidget(self.lb36,  4, 0)
        self.g3.addWidget(self.lb37,  4, 1)

        self.g3.addWidget(self.lb38,  5, 0)
        self.g3.addWidget(self.lb39,  5, 1)
        self.g3.addWidget(self.lb41,  6, 0)
        self.g3.addWidget(self.lb42,  6, 1)
        self.g3.addWidget(self.lb43,  7, 0)
        self.g3.addWidget(self.lb44,  7, 1)

        self.g3.addWidget(self.b31,   2, 2)
        self.g3.addWidget(self.b32,   3, 2)
        self.g3.addWidget(self.b33,   4, 2)
        self.g3.addWidget(self.b34,   5, 2)
        self.g3.addWidget(self.b35,   6, 2)
        self.g3.addWidget(self.b36,   7, 2)

        self.b30 = QToolButton()
        self.b30.setIcon(QIcon("icons/reset1.png"))
        self.b30.setIconSize(QSize(40, 40))
        self.b30.setToolTip("Test all equipment one by one")
        self.b30.clicked.connect(self.func30)
        self.lb45 = QLabel('Test ALL')
        self.lb45.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.lb30=QLabel(' ')
        self.lb30.setStyleSheet("background-color: lightgrey")

        self.g4 = QGridLayout()
        self.g4.addWidget(self.lb30,  0, 0, 1, 1)
        self.g4.addWidget(self.b30,   0, 1, 1, 1)
        self.g4.addWidget(self.lb45,  1, 1, 1, 1)

        self.L20.addLayout(self.g3)
        self.L20.addLayout(self.g4)

    ################### Alicat Flow Control ###############  567
    def layout4(self):
        i=0
        temp = ['14.9', '29', '1', '1', '14.9', '29', '50', '50', '0', '0', '0']

        ############# MFC1 ###############
        self.lb51=QLabel("MFC1: 1, Dilution line")
        self.lb52=QLabel("Pressure (psi)")
        self.lb53=QLabel(' ')
        self.e51 = QLineEdit(temp[i])
        self.e51.setDisabled(True)
        self.b51=QPushButton("Change")
        self.b51.clicked.connect(self.func51)
        self.b51.setEnabled(False)
        i += 1

        self.lb54=QLabel("Temperature (C)")
        self.lb55=QLabel(' ')
        self.e52 = QLineEdit(temp[i])
        self.e52.setDisabled(True)
        i += 1

        self.lb56=QLabel("Mass Flow (sccm)")
        self.lb57=QLabel(' ')
        self.lb57.setFixedWidth(50)
        self.e53 = QLineEdit(temp[i])
        self.b52=QPushButton("Change")
        self.b52.clicked.connect(self.func52)
        self.b52.setEnabled(False)
        i += 1

        self.lb58=QLabel("Set Point (sccm)")
        self.lb59=QLabel(' ')
        self.e54 = QLineEdit(temp[i])
        self.e54.setDisabled(True)
        self.b53=QPushButton("Change")
        self.b53.clicked.connect(self.func53)
        self.b53.setEnabled(False)
        i += 1

        #### MFC2 #######
        self.lb65=QLabel("MFC2: 50, Bubble Line")
        self.lb66=QLabel("Pressure (psi)")
        self.lb67=QLabel(' ')
        self.e55 = QLineEdit(temp[i])
        self.e55.setDisabled(True)
        self.b54=QPushButton("Change")
        self.b54.clicked.connect(self.func54)
        self.b54.setEnabled(False)
        i += 1

        self.lb68=QLabel("Temperature (C)")
        self.lb69=QLabel(' ')
        self.e56 = QLineEdit(temp[i])
        self.e56.setDisabled(True)
        i += 1

        self.lb71=QLabel("Mass Flow (sccm)")
        self.lb72=QLabel(' ')
        self.e57 = QComboBox()
        self.e57.addItems(["50", "20", "80", "100"])
        self.e57.setEditable(True)
        self.b55=QPushButton("Change", self)
        self.b55.clicked.connect(self.func55)
        self.b55.setStyleSheet("font: bold")
        i += 1

        self.lb73=QLabel("Set Point (sccm)")
        self.lb74=QLabel(' ')
        self.e58 = QLineEdit(temp[i])
        self.e58.setDisabled(True)
        self.b56=QPushButton("Change")
        self.b56.clicked.connect(self.func56)
        self.b56.setEnabled(False)
        i += 1

        self.lb50=QLabel(' \n ')
        self.lb50.setStyleSheet("background-color: lightgrey")

        self.g7 = QGridLayout()
        self.g7.addWidget(self.lb51,  0, 0, 1, 2)
        self.g7.addWidget(self.lb52,  1, 0)
        self.g7.addWidget(self.lb53,  1, 1)
        self.g7.addWidget(self.e51,   1, 2)
        self.g7.addWidget(self.b51,   1, 3)

        self.g7.addWidget(self.lb54,  2, 0)
        self.g7.addWidget(self.lb55,  2, 1)
        self.g7.addWidget(self.e52,   2, 2)

        self.g7.addWidget(self.lb56,  3, 0)
        self.g7.addWidget(self.lb57,  3, 1)
        self.g7.addWidget(self.e53,   3, 2)
        self.g7.addWidget(self.b52,   3, 3)

        self.g7.addWidget(self.lb58,  4, 0)
        self.g7.addWidget(self.lb59,  4, 1)
        self.g7.addWidget(self.e54,   4, 2)
        self.g7.addWidget(self.b53,   4, 3)

        self.g7.addWidget(self.lb65,  5, 0, 1, 2)
        self.g7.addWidget(self.lb66,  6, 0)
        self.g7.addWidget(self.lb67,  6, 1)
        self.g7.addWidget(self.e55,   6, 2)
        self.g7.addWidget(self.b54,   6, 3)

        self.g7.addWidget(self.lb68,  7, 0)
        self.g7.addWidget(self.lb69,  7, 1)
        self.g7.addWidget(self.e56,   7, 2)

        self.g7.addWidget(self.lb71,  8, 0)
        self.g7.addWidget(self.lb72,  8, 1)
        self.g7.addWidget(self.e57,   8, 2)
        self.g7.addWidget(self.b55,   8, 3)

        self.g7.addWidget(self.lb73,  9, 0)
        self.g7.addWidget(self.lb74,  9, 1)
        self.g7.addWidget(self.e58,   9, 2)
        self.g7.addWidget(self.b56,   9, 3)

        # self.g7.addWidget(self.b50,   12, 0, 1, 2)
        # self.g7.addWidget(self.b60,   12, 2, 1, 2)
        # self.g7.addWidget(self.b61,   12, 4, 1, 2)
        # self.g7.addWidget(self.lb50,  13, 0, 2, 6)

        self.b60 = QToolButton()
        self.b60.setIcon(QIcon("icons/start1.png"))
        self.b60.setIconSize(QSize(40, 40))
        self.b60.setToolTip("Start experiment: send Alicat data to analyzer, record start time.")
        self.b60.clicked.connect(self.func50)
        self.lb60 = QLabel('Start Exp.')
        self.lb60.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.b70 = QToolButton()
        self.b70.setIcon(QIcon("icons/zero.png"))
        self.b70.setIconSize(QSize(40, 40))
        self.b70.setToolTip("Stop Alicat flow.")
        self.b70.clicked.connect(self.func60)
        self.lb70 = QLabel('Stop Flow')
        self.lb70.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.b61 = QToolButton()
        self.b61.setIcon(QIcon("icons/stop.jpg"))
        self.b61.setIconSize(QSize(40, 40))
        self.b61.setToolTip("Stop experiment: stop sending Alicat data to analyzer, record end time.")
        self.b61.clicked.connect(self.func61)
        self.lb61 = QLabel('Stop Exp.')
        self.lb61.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.g6 = QGridLayout()
        self.g6.addWidget(self.b60,   0, 0)
        self.g6.addWidget(self.lb60,  1, 0)
        self.g6.addWidget(self.b70,   0, 1)
        self.g6.addWidget(self.lb70,  1, 1)
        self.g6.addWidget(self.b61,   0, 2)
        self.g6.addWidget(self.lb61,  1, 2)
        self.g6.addWidget(self.lb50,  0, 3, 1, 2)

        self.L17.addLayout(self.g7) #, 83
        self.L17.addLayout(self.g6) #, 17
        # self.L17.addStretch()       #*** will tight the space

        self.timer=QTimer()
        self.timer.setInterval(rt)
        self.timer.timeout.connect(self.refresh_label)


    ################### Calibration ###############
    def layout5(self):
        minute = []
        for i in range(60):
            if i<10:
                minute.append('0'+str(i))
            else:
                minute.append(str(i))

        hour = []
        for i in range(24):
            if i<10:
                hour.append('0'+str(i))
            else:
                hour.append(str(i))

        self.lb81=QLabel("Analyze data:")
        self.lb82=QLabel("R/Data drive\nlocation")
        self.lb83=QLabel("Sample")
        self.lb84=QLabel("Start yyyymmdd")
        self.lb85=QLabel("hh : mm")
        # self.lb85.setAlignment(Qt.AlignRight)  ## PyQt5
        self.lb85.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lb86=QLabel("  :  ")
        self.lb87=QLabel("End yyyymmdd")
        self.lb88=QLabel("hh : mm")
        # self.lb88.setAlignment(Qt.AlignRight)  ## PyQt5
        self.lb88.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lb89=QLabel("  :  ")
        self.lb91=QLabel("Suffix")

        self.e81 = QTextEdit()
        try:
            f = open('log/rdrive.txt', "r")
            temp = f.read()
            self.e81.setPlainText(temp)
            if opsystem == 'Windows':
                self.e81.setFixedHeight(60)        ## box won't expand!
        except:
            if opsystem == 'Windows':
                self.e81.setPlainText('R:\crd_G9000\AVXxx\3610-NUV1022\R&D\Calibration')    ## Windows
            elif opsystem == 'Darwin':
                self.e81.setPlainText('/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/')   ## Mac
            else:
                self.e81.setPlainText('/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/')  ## Linux
            print('failed to load R drive location')

        self.e82 = QLineEdit('176 - Acetic Acid')
        self.e83 = QLineEdit('')
        self.e84 = QComboBox()
        self.e84.addItems(hour)
        self.e85 = QComboBox()
        self.e85.addItems(minute)
        self.e86 = QLineEdit('')
        self.e87 = QComboBox()
        self.e87.addItems(hour)
        self.e88 = QComboBox()
        self.e88.addItems(minute)

        ## prefill time data
        try:
            fnr = self.e81.toPlainText()
            fnrt = os.path.join(fnr, 'time1.txt')
            f = open(fnrt, 'r')
            temp = f.read().splitlines()
            self.e83.setText(temp[0])
            self.e84.setCurrentText(temp[1])
            self.e85.setCurrentText(temp[2])
            self.e86.setText(temp[3])
            self.e87.setCurrentText(temp[4])
            self.e88.setCurrentText(temp[5])
        except:
            self.e83.setText('20220201')
            self.e84.setCurrentText('08')
            self.e85.setCurrentText('00')
            self.e86.setText('20220201')
            self.e87.setCurrentText('23')
            self.e88.setCurrentText('59')

        self.e89 = QLineEdit('')  #surfux
        self.lb92=QLabel("CID")
        self.lb93=QLabel("Volumn (ul)")
        self.lb94=QLabel("Weight (g)")
        self.lb95=QLabel("ρ (g/ml)")
        self.lb95.setToolTip("Density")
        self.lb96=QLabel("MW")
        self.lb96.setToolTip("Molecular Weight")

        self.e90 = QLineEdit('176')
        self.e91 = QLineEdit('10')
        self.e92 = QLineEdit('0.0090')
        self.e93 = QLineEdit('1.05')
        self.e94 = QLineEdit('60.052')
        self.lb98=QLabel(" ")

        self.b80 = QToolButton()
        self.b80.setIcon(QIcon("icons/start1.png"))
        self.b80.setIconSize(QSize(40, 40))
        self.b80.setToolTip("Calculate Calibration Factor")
        self.b80.clicked.connect(self.func80)
        self.lb99 = QLabel('Calculate')
        self.lb99.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.b81=QPushButton("Close All Calibration Plots", self)
        self.b81.clicked.connect(self.func81)
        self.b81.setEnabled(False)
        self.b81.setStyleSheet("font: bold")

        self.b82=QPushButton("Autofill Time", self)
        self.b82.clicked.connect(self.func82)
        self.b82.setStyleSheet("font: bold")
        self.b82.setToolTip("Automatic fill the time based on input start date")
        self.lb80=QLabel("  \n  ")
        self.lb80.setStyleSheet("background-color: lightgrey")
        self.lb80.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        self.g8 = QGridLayout()
        self.g8.addWidget(self.lb82,  0, 0, 2, 1)
        self.g8.addWidget(self.lb83,  2, 0, 1, 1)
        self.g8.addWidget(self.lb84,  3, 0, 1, 1)
        self.g8.addWidget(self.lb85,  4, 0, 1, 1)
        self.g8.addWidget(self.lb86,  4, 2, 1, 1)
        self.g8.addWidget(self.lb87,  5, 0, 1, 1)
        self.g8.addWidget(self.lb88,  6, 0, 1, 1)
        self.g8.addWidget(self.lb89,  6, 2, 1, 1)
        self.g8.addWidget(self.lb91,  7, 0, 1, 1)
        self.g8.addWidget(self.lb92,  7, 2, 1, 1)

        self.g8.addWidget(self.lb93,  9, 0, 1, 1)  #volume
        self.g8.addWidget(self.lb94, 10, 0, 1, 1)  #weight
        self.g8.addWidget(self.lb95,  9, 2, 1, 1)  #density
        self.g8.addWidget(self.lb96, 10, 2, 1, 1)  #MW

        self.g8.addWidget(self.e81,   0, 1, 2, 3)
        self.g8.addWidget(self.e82,   2, 1, 1, 3)
        self.g8.addWidget(self.e83,   3, 1, 1, 3)
        self.g8.addWidget(self.e84,   4, 1, 1, 1)
        self.g8.addWidget(self.e85,   4, 3, 1, 1)
        self.g8.addWidget(self.e86,   5, 1, 1, 3)
        self.g8.addWidget(self.e87,   6, 1, 1, 1)
        self.g8.addWidget(self.e88,   6, 3, 1, 1)
        self.g8.addWidget(self.e89,   7, 1, 1, 1)  #suffix
        self.g8.addWidget(self.e90,   7, 3, 1, 1)
        self.g8.addWidget(self.b82,   8, 2, 1, 2)  #autofill button

        self.g8.addWidget(self.e91,   9, 1, 1, 1)  #vol
        self.g8.addWidget(self.e92,  10, 1, 1, 1)  #weight
        self.g8.addWidget(self.e93,   9, 3, 1, 1)  #density
        self.g8.addWidget(self.e94,  10, 3, 1, 1)  #MW

        self.g8.addWidget(self.b80,  11, 0, 2, 1)
        self.g8.addWidget(self.lb99, 13, 0, 1, 1)
        self.g8.addWidget(self.lb80, 11, 1, 2, 3)
        self.g8.addWidget(self.b81,  13, 1, 1, 3)
        self.L18.addLayout(self.g8)
        self.L18.addStretch()


    ################### tab2  ###################
    def layout6(self):
        self.lb201=QLabel("Your system:")
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

        self.b200=QPushButton("Get serial port names", self)
        self.b200.clicked.connect(self.func200)
        self.b200.setStyleSheet("font: bold")
        self.b200.setToolTip("Available serial ports on this computer")
        self.e200 = QTextEdit()
        portlist = [p.device for p in ls.comports()]
        self.e200.setPlainText(str(portlist))

        self.lb211 = QLabel("Analyzer")
        self.lb212 = QLabel("IP Address:")
        self.e201 = QLineEdit('')    ## 10.100.4.20
        self.lb213=QLabel(" ")       ## port not found
        self.b201=QPushButton("Detect", self)
        self.b201.clicked.connect(self.func201)
        self.b201.setStyleSheet("font: bold")
        self.b201.setToolTip("Detect connection.")

        self.lb214=QLabel("Alicat:")
        self.lb215=QLabel("Serial Port:")
        self.e202 = QLineEdit()    #'/dev/cu.usbserial-A908UXOQ' '/dev/tty.usbserial-A908UXOQ'
        self.lb216=QLabel(" ")     ## port not found
        self.b202=QPushButton("Detect", self)
        self.b202.clicked.connect(self.func202)
        self.b202.setStyleSheet("font: bold")
        self.b202.setToolTip("Detect the name of the port connected to Alicat.")

        self.lb217=QLabel("US Solid Scale:")
        self.lb218=QLabel("Serial Port:")
        self.e203 = QLineEdit()      #'/dev/cu.usbserial-14310'
        self.lb219=QLabel(" ")
        self.b203=QPushButton("Detect", self)
        self.b203.clicked.connect(self.func203)
        self.b203.setStyleSheet("font: bold")
        self.b203.setToolTip("Detect the name of the port connected to US Solid Scale.")

        self.lb220=QLabel("Mettler Toledo Scale:")
        self.lb221=QLabel("IP address:")
        self.e204 = QLineEdit()        #'10.100.3.148'
        self.lb222=QLabel("Port:")     #'8001'
        self.e205 = QLineEdit()
        self.lb223=QLabel(" ")
        self.b204=QPushButton("Detect", self)
        self.b204.clicked.connect(self.func204)
        self.b204.setStyleSheet("font: bold")
        self.b204.setToolTip("Detect the name of the port connected to Mettler Toledo Scale.")

        try:
            f = open('log/analyzer.txt', "r")
            temp = f.read()   #.splitlines()
            self.e201.setText(temp)    # analyzer
            f = open('log/alicat.txt', "r")
            temp = f.read()
            self.e202.setText(temp)    # alicat
            f = open('log/scaleuso.txt', "r")
            temp = f.read()
            self.e203.setText(temp)     # us solid
            f = open('log/scalemt.txt', "r")
            temp = f.read().splitlines()
            self.e204.setText(temp[0])   # MT
            self.e205.setText(temp[1])   # MT
        except:
            print('failed to load port names')

        self.g21 = QGridLayout()
        self.g21.addWidget(self.lb201,  0, 0)
        self.g21.addWidget(self.rb201,  1, 0)
        self.g21.addWidget(self.rb202,  2, 0)
        self.g21.addWidget(self.rb203,  3, 0)
        self.g21.addWidget(self.b200,   4, 0)
        self.g21.addWidget(self.e200,   5, 0, 1, 3)

        self.g21.addWidget(self.lb211,  6, 0)
        self.g21.addWidget(self.lb212,  7, 0)
        self.g21.addWidget(self.e201,   7, 1)
        self.g21.addWidget(self.b201,   7, 2)
        self.g21.addWidget(self.lb213,  8, 1)

        self.g21.addWidget(self.lb214,  9, 0)
        self.g21.addWidget(self.lb215, 10, 0)
        self.g21.addWidget(self.e202,  10, 1)
        self.g21.addWidget(self.b202,  10, 2)
        self.g21.addWidget(self.lb216, 11, 1)

        self.g21.addWidget(self.lb217, 12, 0)
        self.g21.addWidget(self.lb218, 13, 0)
        self.g21.addWidget(self.e203,  13, 1)
        self.g21.addWidget(self.b203,  13, 2)
        self.g21.addWidget(self.lb219, 14, 1)

        self.g21.addWidget(self.lb220, 15, 0)
        self.g21.addWidget(self.lb221, 16, 0)
        self.g21.addWidget(self.e204,  16, 1)
        self.g21.addWidget(self.b204,  16, 2)
        self.g21.addWidget(self.lb222, 17, 0)
        self.g21.addWidget(self.e205,  17, 1)
        self.g21.addWidget(self.lb223, 18, 1)

        self.L201.addLayout(self.g21)
        self.L201.addStretch()       #*** will tight the space


    ################### tab3  ###################
    def layout7(self):
        # self.lb301=QLabel("Spectrum Plot Real Time")
        # self.lb301.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # self.L301.addWidget(self.lb301)
        self.lb302=QLabel(" ")

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
        self.L301.addWidget(self.toolbar1)   #*** matplotlib tool bar
        self.L301.addWidget(self.b301)
        self.L301.addWidget(self.b302)
        self.L301.addWidget(self.b303)
        self.L301.addWidget(self.lb302)


    ################### Tab1 Functions ###############
    def func11(self):
        try:
            host = self.e201.text()     ## '10.100.4.20' IP address
            socket.create_connection((host, port_out), 5)    # only try 5s time out   ## 40060
            dm_queue = Queue(180)       ## data manager
            listener = Listener(dm_queue, host, port_out, StringPickler.ArbitraryObject, retry=True)
            for i in range(6):
                dm = dm_queue.get(timeout=5)
                print(dm['source'])
                if dm['source'] == 'analyze_VOC_broadband_cal':
                    break

            key1 = list(dm['data'].keys())
            key2 = sorted(key1)
            # print(anakey)
            self.e11.clear()  # delete all items from comboBox
            self.e11.addItems(key2)
            self.lb10.setText(str(len(key2)) + ' data keys available for plot.')
        except:
            self.lb10.setText('Key error. Analyzer out port not ready.')

    def func12(self):   ## not working on Windows, plot not shown
        if self.func32():
            try:
                host = self.e201.text()
                socket.create_connection((host, port_out), 5)    # '10.100.4.20'   # 40060
                gas = self.e11.currentText()                     # 'broadband_gasConcs_280'
                self.lb10.setText('Plotting spectrum...')
                t8.specviewer(host, port_out, gas)
            except:
                self.lb10.setText('Error. Analyzer data out port not ready.')
        else:
            self.lb10.setText('Error. Analyzer data out port not ready.')

    def specplot(self):  ## may stop after a while on Wifi, but fine with Ethernet cable
        if self.func32():
            try:
                self.lb10.setText('Plotting spectrum on Tab 3...')
                self.canvas1.close_event()
                self.figure1.clear()
                self.plot1()
            except:
                self.lb10.setText('Error. Analyzer data out port not ready.')
        else:
            self.lb10.setText('Error. Analyzer data out port not ready.')

    def plot1(self):
        self.nn=0
        x = []   ## unix time 1641259801
        xt = []  ## real time 19:30\nJan-3-2022
        y = []
        xx = []  ## x labels that will be marked
        # gas = 'MFC2_flow'
        gas = 'broadband_gasConcs_280'
        host = self.e201.text()  ## '10.100.4.20' IP address
        dm_queue = Queue(180)  ## data manager
        listener = Listener(dm_queue, host, port_out, StringPickler.ArbitraryObject, retry=True)

        ax1 = self.figure1.add_subplot(111)
        # fig, ax1 = plt.subplots()

        ## add first element
        while True:
            dm = dm_queue.get(timeout=5)
            if dm['source'] == 'analyze_VOC_broadband_cal':
                t = dm['time']
                x.append(t)
                xt.append(time.ctime(t))
                y.append(dm['data'][gas])
            if len(y):
                break

        def animate(i):
            dm = dm_queue.get(timeout=5)
            if dm['source'] == 'analyze_VOC_broadband_cal':
                if len(y) == spec_x:     ## x-axis number
                    x.pop(0)
                    xt.pop(0)
                    y.pop(0)

                t = dm['time']
                x.append(t)
                xt.append(time.ctime(t))
                y.append(dm['data'][gas])

                a = time.ctime(x[-2])
                b = time.ctime(t)

                if ((a.split(":")[1] == '59' and b.split(":")[1] == '00') or
                        (a.split(":")[1] == '29' and b.split(":")[1] == '30')):
                    xx.append(t)

                if (len(xx) > 0) and (xx[0] < x[0]):
                    xx.pop(0)

                x1 = []  ## tick locations
                x2 = []  ## tick marker final format
                for j in xx:
                    x1.append(x.index(j))
                    xtime = time.ctime(j).split()
                    x2.append(xtime[3][:-3] + '\n' + xtime[1] + '-' + xtime[2] + '-' + xtime[4])
                # print(xx)
                # print(x1)
                # print(x2)

                ax1.clear()
                ax1.plot(xt, y, linewidth=0.5)
                ax1.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))  ## has to be inside

                if x1 == []:
                    ax1.set_xticklabels([])
                else:
                    ax1.set_xticks(x1, x2)
                print(self.nn)
                self.nn+=1

        ### format the plot
        # ax1.set_position([0.06, 0.1, 0.93, 0.88])  # left,bottom,width,height  ## axes position
        # ax1.tick_params(axis='x', which='major', labelsize=4)
        # ax1.tick_params(axis='y', which='major', labelsize=4, pad=-2)

        self.anim1 = FuncAnimation(self.figure1, animate, interval=1000)
        # plt.show()  ## don't add this, otherwise will have extra blank plot
        self.canvas1.draw()

    ##################### Weight ######################
    def func21(self):  ## continuously plot, for both scale
        self.canvas2.close_event()
        self.figure2.clear()
        try:
            w = self.e21.text()
            if not w.isdecimal():
                w = 180
                self.e21.setText('180')
            weightime = int(w)
            if self.rb21.isChecked():
                self.plot2(weightime)
            else:
                self.plot3(weightime)
            self.b23.setEnabled(True)
            self.b24.setEnabled(False)
        except:
            self.lb20.setText('Error, please re-try.')

    def gen(self, weightime):
        i = 0
        while i <weightime:
            i += 1
            yield i

    def plot2(self, weightime):   ## US solid scale
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
                    print("animation error")

            self.anim2 = FuncAnimation(self.figure2, animate, frames=self.gen(weightime), repeat=False)
            # plt.show()
            self.canvas2.draw()
            self.lb42.setText('\u2713')
        except:
            self.lb42.setText('\u2717')
            self.lb20.setText('!Scale not found.')

    def plot3(self, weightime):    ## Mettler Toledo
        self.lb20.setText(' ')
        self.lb44.setText(' ')
        TCP_IP = '10.100.3.148'
        TCP_PORT = 8001
        BUFFER_SIZE = 1024
        # weightime = int(self.e21.text())
        try:
            self.lb20.setText(' ')
            s = socket.create_connection((TCP_IP, TCP_PORT), 5)  # only try 5s time out
            s.settimeout(2)

            try:
                print(s.recv(BUFFER_SIZE))
                print('Mettler Toledo scale is ready.')
            except:
                print('Wake up the Mettler Toledo scale')
                s.send(b'@\r\n')     # Wake up scale
                k = s.recv(BUFFER_SIZE)  #= clear buffer
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
                    ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.4f'))  ## has to be inside

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

                    self.lb20.setText(w1[5:12])
                    time.sleep(1)

                except:
                    self.lb20.setText('Scale not found.')
                    print("animation error")

            self.anim2 = FuncAnimation(self.figure2, animate, frames=self.gen(weightime), repeat=False)
            # plt.show()
            self.canvas2.draw()
            self.lb44.setText('\u2713')
        except:
            self.lb44.setText('\u2717')
            self.lb20.setText('!Scale not found.')

    def func22(self):  ## read weight one time
        self.lb29.setText('')
        try:     # when animation is running, re-use lb20 value
            w2 = self.lb20.text()   ##string
            w3 = float(w2)          ## if cannot be converted to float, measure again
            w3 = round(w3,5)
            self.lb29.setText(str(w3))
            self.e92.setText(str(w3))
            print('use label lb20')
        except:   # when no animation is not run
            print('measure oneself')
            self.lb20.setText(' ')
            if self.rb21.isChecked():    ## US Solid scale
                print('US Solid scale')
                self.func25()
            else:    ## MT scale
                print('MT scale')
                self.func26()

    def func23(self):   ## pause
        try:
            if opsystem == 'Windows':  # close serial port
                self.serialPort.close()
            self.anim2.pause()
            self.b24.setEnabled(True)
            self.lb20.setText('')
        except:
            self.lb20.setText('Error. Restart weight figure.')

    def func24(self):   # resume
        try:
            if opsystem == 'Windows':   # need to reconnect serial port
                port_so = self.e203.text()
                self.serialPort = serial.Serial(port=port_so, baudrate=1200,
                                                bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
            self.anim2.resume()
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
            self.e92.setText(str(weight))
            self.lb42.setText('\u2713')

    def func26(self):  ## MT scale, read weight one time
        weight = self.func36()
        # print(weight)
        if weight is None:
            self.lb44.setText('\u2717')
            self.lb20.setText('!Scale not found.')
        else:
            self.lb29.setText(str(weight))
            self.e92.setText(str(weight))
            self.lb44.setText('\u2713')


    #############  connection functions #############
    def func31(self):
        try:
            host = self.e201.text()
            socket.create_connection((host, port_in), 5)    # '10.100.4.20'   ## 50070
            ipadd = 'http://'+host
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
                print(dm['source'])
                print(i)
                if dm['source'] == 'analyze_VOC_broadband_cal':
                    # print(i)
                    # print(dm)
                    self.lb35.setText('\u2713')
                    self.lb30.setText('Analyzer connected, port_out open.\nReceiving data in queue...')
                    return 1
                if i == 5:
                    self.lb35.setText('\u2717')
                    self.lb30.setText('analyze_VOC_broadband_cal not exist. \n'
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
            print(flow_controller1.get())  ## need get, Bose ear will connect too
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
            TCP_IP = '10.100.3.148'
            TCP_PORT = 8001
            BUFFER_SIZE = 1024

            s = socket.create_connection((TCP_IP, TCP_PORT), 5)  # only try 5s time out
            s.settimeout(2)
            print('Mettler Toledo Scale connected')

            try:
                print(s.recv(BUFFER_SIZE))
                print('Mettler Toledo scale is ready.')
            except:
                print('Wake up the Mettler Toledo scale')
                s.send(b'@\r\n')       # Wake up scale
            k = s.recv(BUFFER_SIZE)    # clear buffer

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
        if self.func35():   ##None has same effect as 0
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
            if len(eq)==5:
                self.lb30.setText('● All equipment available!')
            else:
                msg += '• Scale connected, ready to measurement weight.'
                self.lb30.setText(msg)
        else:
            msg += '• Scale not found, cannot measure weight.'  #●
            self.lb30.setText(msg)
        # print(msg)


    ############## Flow control #############
    def func51(self):
        self.lb50.setText("Button is active")

    def func52(self):
        self.lb50.setText("Button is active")

    def func53(self):
        self.lb50.setText("Button is active")

    def func54(self):
        self.lb50.setText("Button is active")

    def func55(self):
        try:
            port_ali = self.e202.text()
            F2 = int(self.e57.currentText())  # bubbler line
            # print(F2)
            F1 = 1 - F2 / 1000  # dilution
            flow_controller1 = FlowController(port=port_ali, address='A')
            flow_controller2 = FlowController(port=port_ali, address='C')
            flow_controller1.set_flow_rate(flow=F1)
            flow_controller2.set_flow_rate(flow=F2)
            # MeasSystem.Backdoor.SetData('my_var',F2)   ### test variable
            self.e53.setText(str(F1))
            self.lb50.setText('Bubble line set to ' + str(F2) + '\n')
        except:
            self.lb50.setText('Unable to set value. \nAlicat not connected.')

    def func56(self):
        self.lb50.setText("Button is active")

    def refresh_label(self):
        try:
            host = self.e201.text()    ## '10.100.4.20'   #port_in 50070
            port_ali = self.e202.text()
            ipadd = 'http://' + host

            flow_controller1 = FlowController(port=port_ali, address='A')
            flow_controller2 = FlowController(port=port_ali, address='C')
            fc1 = flow_controller1.get()
            fc2 = flow_controller2.get()
            MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection",IsDontCareConnection=False)
            # print ('MFC1: %.3f | MFC2: %.3f' % (fc1['mass_flow'], fc2['mass_flow']))

            ## sent measurement data on Alicat to analyzer fitting software
            MeasSystem.Backdoor.SetData('MFC1_P_amb', fc1['pressure'])
            MeasSystem.Backdoor.SetData('MFC1_flow', fc1['mass_flow'])
            MeasSystem.Backdoor.SetData('MFC1_flowset', fc1['setpoint'])

            MeasSystem.Backdoor.SetData('MFC2_P_amb', fc2['pressure'])
            MeasSystem.Backdoor.SetData('MFC2_T_amb', fc2['temperature'])
            MeasSystem.Backdoor.SetData('MFC2_flow', fc2['mass_flow'])
            MeasSystem.Backdoor.SetData('MFC2_flowset', fc2['setpoint'])

            self.lb53.setText(str(fc1['pressure']))
            self.lb55.setText(str(fc1['temperature']))
            self.lb57.setText(str(fc1['mass_flow']))
            self.lb59.setText(str(fc1['setpoint']))

            self.lb67.setText(str(fc2['pressure']))
            self.lb69.setText(str(fc2['temperature']))
            self.lb72.setText(str(fc2['mass_flow']))
            self.lb74.setText(str(fc2['setpoint']))
        except:
            self.lb50.setText("Error. Analyzer not ready.\nPlease check connection.")

    def func50(self):  ## start experiment, send Alicat data to analyzer, record time
        fnr = self.e81.toPlainText()
        fnrt = os.path.join(fnr, 'time1.txt')
        # port_ali = self.e202.text()
        if not os.path.isdir(fnr):
            self.lb50.setText('R/Data drive not connected.\nPlease attach R drive first.')
        else:
            try:
                # flow_controller1 = FlowController(port=port_ali, address='A')
                # flow_controller2 = FlowController(port=port_ali, address='C')

                self.timer.start()
                self.lb50.setText("Experiment started!\nData sent to analyzer.")

                a1 = time.strftime("%Y%m%d")
                a2 = time.strftime("%H")
                a3 = time.strftime("%M")
                self.e83.setText(a1)          ## '20211124'
                self.e84.setCurrentText(a2)   ## '08'
                self.e85.setCurrentText(a3)   ## '00'
                self.e86.setText(a1)          ## '20211124'
                self.e87.setCurrentText('23')
                self.e88.setCurrentText('59')

                if os.path.isfile(fnrt):
                    os.remove(fnrt)
                with open(fnrt, 'a') as f:
                    f.write(a1 + '\n')
                    f.write(a2 + '\n')
                    f.write(a3 + '\n')
                    f.write(a1 + '\n')
                    f.write('23' + '\n')
                    f.write('59' + '\n')
            except:
                self.lb50.setText('Alicat is not connected.\n')

    def func60(self):  ## stop flow
        try:
            port_ali = self.e202.text()
            F2 = 0  # bubbler line
            F1 = 1 - F2 / 1000  # dilution
            flow_controller1 = FlowController(port=port_ali, address='A')
            flow_controller2 = FlowController(port=port_ali, address='C')
            flow_controller1.set_flow_rate(flow=F1)
            flow_controller2.set_flow_rate(flow=F2)

            self.e53.setText(str(F1))
            self.e57.setCurrentText(str(F2))
            self.lb50.setText('Bubble line stopped.\n')
        except:
            self.lb50.setText('Unable to stop the flow. \nAlicat not connected.')

    def func61(self):    ## stop sending data to analyzer, record time
        fnr = self.e81.toPlainText()
        fnrt = os.path.join(fnr, 'time1.txt')
        if not os.path.isdir(fnr):
            self.lb50.setText('R/Data drive not connected.\nPlease attach R drive first.')
        else:
            try:
                self.timer.stop()
                a1 = time.strftime("%Y%m%d")
                a2 = time.strftime("%H")
                a3 = time.strftime("%M")
                self.e86.setText(a1)           ## '20211124'
                self.e87.setCurrentText(a2)
                self.e88.setCurrentText(a3)
                self.lb50.setText('Experiment stopped.\nTime recorded.')

                if os.path.isfile(fnrt):
                    os.remove(fnrt)
                with open(fnrt, 'a') as f:
                    f.write(self.e83.text() + '\n')
                    f.write(self.e84.currentText() + '\n')
                    f.write(self.e85.currentText() + '\n')
                    f.write(a1 + '\n')
                    f.write(a2 + '\n')
                    f.write(a3 + '\n')
                self.lb50.setText('Experiment stopped.\nTime recorded.')
            except:
                self.lb50.setText('Error stop.\n')

    ############## calculate calibration factor #############
    def func80(self):
        try:
            # fnr = '/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'  ## R driver, data
            # gas = '176 - Acetic Acid'
            # startTime = '20211124 08:00'
            # endTime = '20211124 23:59'
            # suffix = 'g'
            self.lb80.setText(" \n ")

            QApplication.processEvents()
            # fnla = '/home/picarro/I2000/Log/Archive/'  ## local driver Archive
            # fnlc = '/home/picarro/.combo_logger/ComboResults/'  ## local driver ComboResults

            fnr = self.e81.toPlainText()
            gas = self.e82.text()
            a1 = self.e83.text()         ## '20211124'
            a2 = self.e84.currentText()  ## '08'
            a3 = self.e85.currentText()  ## '00'
            startTime = a1 + ' ' + a2 + ':' + a3
            b1 = self.e86.text()         ## '20211124'
            b2 = self.e87.currentText()  ## '23'
            b3 = self.e88.currentText()  ## '59'
            endTime = b1 + ' ' + b2 + ':' + b3
            # print(startTime)
            # print(endTime)
            suffix = self.e89.text()     ## ''

            # fnr1 = fnr + gas + '/' + a1 + suffix  ## /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c
            fname = os.path.join(fnr, gas, a1 + suffix + '/')

            if (not a1.isdigit()) or (len(a1) != 8):
                self.lb80.setText('StartTime format is wrong.\n Please revise as all numbers: yyyymmdd')
            elif (not b1.isdigit()) or (len(b1) != 8):
                self.lb80.setText('End Time format is wrong.\n Please revise as all numbers: yyyymmdd')
            elif not os.path.exists(fnr):
                self.lb80.setText('Error, R drive not found. \nPlease check or attach the data/R drive.')
            else:
                ## epoch_time = datetime.datetime(2021,11,24,8,0).timestamp()
                epo1 = datetime.datetime(int(a1[:4]), int(a1[4:6]), int(a1[-2:]), int(a2), int(a3)).timestamp()
                epo2 = datetime.datetime(int(b1[:4]), int(b1[4:6]), int(b1[-2:]), int(b2), int(b3)).timestamp()
                epo11 = datetime.datetime(int(a1[:4]), int(a1[4:6]), int(a1[-2:]) + 1, int(b2), int(b3)).timestamp()
                # print(epo1)
                # print(epo2)
                if epo1 > epo2:
                    self.lb80.setText('Error: start time is after end time.\n')
                elif epo2 > epo11:
                    self.lb80.setText('Duration is more than 1 day, not supported here. \nPlease manually extra the files')
                elif not os.path.exists(fname):
                    self.lb80.setText('Error, data not found.\nPlease check file name')
                else:
                    #     # fname = r'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'        ##Linux
                    #     fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'    ##Mac
                    #     gas = '176 - Acetic Acid'
                    #     cid = 176
                    #     volume = 10       ## droplet in uL
                    #     weight = 0.0090   ## g
                    #     density = 1.05
                    #     MW = 60.052
                    #     startTime = '20211124 08:00'
                    #     endTime = '20211124 23:59'
                    #     suffix = 'h'    ## folder suffix 'g' or empty ''

                    cid = int(self.e90.text())
                    volume = float(self.e91.text())
                    weight = float(self.e92.text())
                    density = float(self.e93.text())
                    MW = float(self.e94.text())
                    self.F1, self.F2, self.F3, self.F4, self.F5, self.F6, self.F7, self.F8, self.F9 = \
                        jupyternotebook(fnr, gas, cid, volume, weight, density, MW, startTime, endTime, suffix)
                    # plt.waitforbuttonpress()  # any key to close all figure
                    # plt.close('all')

                    f = open(jupyterpath+'cal.txt', "r")
                    cal = f.read()

                    self.lb80.setText('Calibration factor is \n' + cal)
                    self.b81.setEnabled(True)

                    if os.path.isfile('log/rdrive.txt'):
                        os.remove('log/rdrive.txt')
                    with open('log/rdrive.txt', 'a') as f:
                        f.write(self.e81.toPlainText())
        except:
            self.lb80.setText('Error calculation.\n')

    def func81(self):  ## close all calibration plots
        try:
            plt.close(self.F1)
            plt.close(self.F2)
            plt.close(self.F3)
            plt.close(self.F4)
            plt.close(self.F5)
            plt.close(self.F6)
            plt.close(self.F7)
            plt.close(self.F8)
            plt.close(self.F9)
            self.b81.setEnabled(False)
        except:
            pass

    def func82(self):  ## autofill time
        try:
            fnr = self.e81.toPlainText()
            gas = self.e82.text()
            a1 = self.e83.text()  ## '20211124'
            suffix = self.e89.text()  ## ''
            fnrt = os.path.join(fnr, gas, a1 + suffix + '/time2.txt')
            f = open(fnrt, 'r')
            temp = f.read().splitlines()
            self.e84.setCurrentText(temp[1])
            self.e85.setCurrentText(temp[2])
            self.e86.setText(temp[3])
            self.e87.setCurrentText(temp[4])
            self.e88.setCurrentText(temp[5])
            self.lb80.setText('Time record found.\nTime filled.')
        except:
            self.lb80.setText('Time record not found.\nCannot auto-fill the time.')


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
            if os.path.isfile('log/analyzer.txt'):
                os.remove('log/analyzer.txt')
            with open('log/analyzer.txt', 'a') as f:
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
                print (i)
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
            if os.path.isfile('log/alicat.txt'):
                os.remove('log/alicat.txt')
            with open('log/alicat.txt', 'a') as f:
                f.write(self.e202.text())

    def func203(self):
        self.lb219.setText('...')
        port_so = self.e203.text()

        if port_so == '':
            portusb = [p.device for p in ls.comports()]
            bk=False
            for i in reversed(portusb):
                print (i)
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
                            bk =True
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
            if os.path.isfile('log/scaleuso.txt'):
                os.remove('log/scaleuso.txt')
            with open('log/scaleuso.txt', 'a') as f:
                f.write(self.e203.text())

    def func204(self):
        self.lb223.setText('')
        try:
            host = self.e204.text()
            port = self.e205.text()
            socket.create_connection((host, int(port)), 5)
            self.lb223.setText('Mettler Toledo scale connected')
            if os.path.isfile('log/scalemt.txt'):
                os.remove('log/scalemt.txt')
            with open('log/scalemt.txt', 'a') as f:
                f.write(host+'\n')
                f.write(port+'\n')
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
    app=QApplication(sys.argv)
    window = Window()
    app.setWindowIcon(QIcon('icons/logo.png'))
    window.show()
    app.exec()

if __name__=='__main__':
    main()



# @author: Yilin Shi   2022.2.1
# shiyilin890@gmail.com


