## SAM Automation: Sample Analyze Module
## Yilin Shi | Picarro | 2022.4.8

## basic library
import sys
import os
import time
import numpy as np
import datetime
import socket
from queue import Queue
import pandas as pd
import shutil
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
import matplotlib

matplotlib.use('ps')
from matplotlib import rc

## Qt GUI
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor
from PyQt6.QtCore import *
from PyQt6 import QtWidgets, QtGui

## Customized file/libraries
import style
from alicat import FlowController  # pip install alicat
import CmdFIFO_py3 as CmdFIFO

## hard-coded global parameters
port_in = 50070  ## backdoor, send data to fitter on analyzer
port_out = 40060  ## listener, get data from analyzer
tr = 2000  ## ms, Alicat label refresh time
spec_xt = 180  ## min, spectrum plot animation x axis time window duration 400'=6h40', 500'=8h20'
ti = 1000  ## 1s animation time interval


# c2Acetone = 10.42    # 400 ppm
# c3IPA = 1.11          # 500 ppm
# c4PGME = 399.3        # 500 ppm

# port_ali = 'COM7'  ## '/dev/tty.usbserial-A908UXOQ'
# fc1 = FlowController(port=port_ali, address='A')
# fc2 = FlowController(port=port_ali, address='B')
# fc3 = FlowController(port=port_ali, address='C')
# fc4 = FlowController(port=port_ali, address='D')
# fc5 = FlowController(port=port_ali, address='E')
# fc6 = FlowController(port=port_ali, address='F')
# fc7 = FlowController(port=port_ali, address='G')
# fc8 = FlowController(port=port_ali, address='H')
# fc9 = FlowController(port=port_ali, address='I')
# fc10 = FlowController(port=port_ali, address='J')

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Picarro - S A M")
        self.setGeometry(600, 50, 990, 780)
        self.set_window_layout()
        # if opsystem == 'Darwin':
        #     self.setMinimumSize(1000, 650)
        # elif opsystem == 'Windows':
        #     self.setFixedSize(1000, 600)
        # else:
        #     self.setMinimumSize(1000, 600)

    def set_window_layout(self):
        self.mainlayout()
        self.layout1()  # title
        self.layout2()  # MFC control
        self.layout3()  # table
        self.layout4()  # bottom row
        self.layout5()  # tab 2  sample1 viewer
        self.layout6()  # tab 3  sample2 viewer
        self.layout7()  # tab 4
        self.layout8()  # tab 5

    def mainlayout(self):
        mainLayout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        self.tab3 = QWidget()
        self.tab4 = QWidget()
        self.tab5 = QWidget()
        self.tabs.addTab(self.tab1, "   ⬥ Experiment Settings   ")
        self.tabs.addTab(self.tab2, "   ⬥ Sample 1 Real Time   ")
        self.tabs.addTab(self.tab3, "  ⬥ Sample 2 Real Time  ")
        self.tabs.addTab(self.tab4, "   ⬥ SAM Design Diagram    ")
        self.tabs.addTab(self.tab5, "     ⬥ Port Detection      ")
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)
        self.show()

        ## initialize parameters
        # self.baseline = []
        # self.view_point = 0   #total points plotted in spectrum viewer window
        # self.total_point = 0  #total points processed, for all three analyzer data source
        self.conn = 0  # check if all MFCs are connected
        self.anaip = 0  # check analyzer IP, in port=backdoor

        ###### tabs ###########
        self.L1 = QVBoxLayout()
        self.L11 = QHBoxLayout()
        self.L12 = QHBoxLayout()
        self.L13 = QHBoxLayout()
        self.L14 = QHBoxLayout()
        self.L1.addLayout(self.L11, 10)
        self.L1.addLayout(self.L12, 20)
        self.L1.addLayout(self.L13, 60)
        self.L1.addLayout(self.L14, 10)

        self.tab1.setLayout(self.L1)

        self.L201 = QVBoxLayout()
        self.tab2.setLayout(self.L201)

        self.L301 = QVBoxLayout()
        self.tab3.setLayout(self.L301)

        self.L401 = QVBoxLayout()
        self.tab4.setLayout(self.L401)

        self.L501 = QVBoxLayout()
        self.tab5.setLayout(self.L501)

    ################### tab1  ###################
    def layout1(self):  # title
        self.img = QLabel()
        self.pixmap = QPixmap('icons/picarro.png')
        self.img.setPixmap(
            self.pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.img2 = QLabel()
        self.pixmap = QPixmap('icons/sam2.png')
        self.img2.setPixmap(
            self.pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.L11.addStretch()
        self.L11.addWidget(self.img)
        self.L11.addWidget(self.img2)
        self.L11.addStretch()

    def redbox(self, e):
        e.setStyleSheet('border: 2px solid red')  #set entry box border red

    def greybox(self, e):
        e.setStyleSheet('border: 1px solid grey')  #restore to grey


    def layout2(self):  # MFC control
        self.box12 = QGroupBox()
        self.box12.setStyleSheet(style.box12())

        self.lb21 = QLabel('  MFC#  ')
        self.lb21.setToolTip('Click to plot real time flow rate on Tab 2, 3.'
                             '\nUnclick to not plot, to reduce overhead time.')
        self.lb22 = QLabel('  Flow  ')
        self.lb23 = QLabel('Conc.ppb')
        self.lb24 = QLabel('Tank.ppm')
        self.lb25 = QLabel('  Set   ')
        self.lb26 = QLabel('  Max.  ')

        self.lb31 = QLabel('1-ZAG')
        self.lb32 = QLabel('2-Act')
        self.lb33 = QLabel('3-IPA')
        self.lb34 = QLabel('4-PGME')
        self.lb35 = QLabel('5-Bubbler1')
        self.lb36 = QLabel('6-Bubbler2')
        self.lb37 = QLabel('7-ZAG')
        self.lb38 = QLabel('8-Act')
        self.lb39 = QLabel('9-Bubbler3')
        self.lb30 = QLabel('10-ZA')

        self.lb31.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb32.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb33.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb34.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb35.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb36.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb37.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb38.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb39.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb30.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lb41 = QLabel('  ')  # real time label
        self.lb42 = QLabel('  ')
        self.lb43 = QLabel('  ')
        self.lb44 = QLabel('  ')
        self.lb45 = QLabel('  ')
        self.lb46 = QLabel('  ')
        self.lb47 = QLabel('  ')
        self.lb48 = QLabel('  ')
        self.lb49 = QLabel('  ')
        self.lb40 = QLabel('  ')

        self.lb41.setStyleSheet("background-color: lightgrey")
        self.lb42.setStyleSheet("background-color: lightgrey")
        self.lb43.setStyleSheet("background-color: lightgrey")
        self.lb44.setStyleSheet("background-color: lightgrey")
        self.lb45.setStyleSheet("background-color: lightgrey")
        self.lb46.setStyleSheet("background-color: lightgrey")
        self.lb47.setStyleSheet("background-color: lightgrey")
        self.lb48.setStyleSheet("background-color: lightgrey")
        self.lb49.setStyleSheet("background-color: lightgrey")
        self.lb40.setStyleSheet("background-color: lightgrey")

        self.e11 = QLineEdit('')
        self.e12 = QLineEdit('')
        self.e13 = QLineEdit('')
        self.e14 = QLineEdit('')
        self.e15 = QLineEdit('')
        self.e16 = QLineEdit('')
        self.e17 = QLineEdit('')
        self.e18 = QLineEdit('')
        self.e19 = QLineEdit('')
        self.e10 = QLineEdit('')

        self.lb51 = QLabel(' 10 SLPM')
        self.lb52 = QLabel(' 50 SCCM')
        self.lb53 = QLabel('100 SCCM')
        self.lb54 = QLabel(' 50 SCCM')
        self.lb55 = QLabel(' 10 SCCM')
        self.lb56 = QLabel(' 10 SCCM')
        self.lb57 = QLabel(' 10 SLPM')
        self.lb58 = QLabel(' 50 SCCM')
        self.lb59 = QLabel(' 10 SCCM')
        self.lb50 = QLabel('200 SCCM')

        self.lb51.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb52.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb53.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb54.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb55.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb56.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb57.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb58.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb59.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb50.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.b11 = QPushButton("Set")
        self.b11.clicked.connect(self.func11)
        self.b12 = QPushButton("Set")
        self.b12.clicked.connect(self.func12)
        self.b13 = QPushButton("Set")
        self.b13.clicked.connect(self.func13)
        self.b14 = QPushButton("Set")
        self.b14.clicked.connect(self.func14)
        self.b15 = QPushButton("Set")
        self.b15.clicked.connect(self.func15)
        self.b16 = QPushButton("Set")
        self.b16.clicked.connect(self.func16)
        self.b17 = QPushButton("Set")
        self.b17.clicked.connect(self.func17)
        self.b18 = QPushButton("Set")
        self.b18.clicked.connect(self.func18)
        self.b19 = QPushButton("Set")
        self.b19.clicked.connect(self.func19)
        self.b10 = QPushButton("Set")
        self.b10.clicked.connect(self.func10)

        self.lb61 = QLabel('  ')  # 2 Acetone concentration
        self.lb62 = QLabel('  ')  # 3 IPA
        self.lb63 = QLabel('  ')  # 4 PGME
        self.lb64 = QLabel('  ')  # 8 Acetone
        self.lb65 = QLabel('(chemical name)')  # 5 Bubbler1
        self.lb66 = QLabel('(chemical name)')  # 5 Bubbler1
        self.lb67 = QLabel('(chemical name)')  # 5 Bubbler1
        self.lb61.setStyleSheet("background-color: honeydew")
        self.lb62.setStyleSheet("background-color: honeydew")
        self.lb63.setStyleSheet("background-color: honeydew")
        self.lb64.setStyleSheet("background-color: honeydew")

        self.e61 = QLineEdit('')  # 2 Acetone tank concentration
        self.e62 = QLineEdit('')  # 3 IPA
        self.e63 = QLineEdit('')  # 4 PGME
        self.e64 = QLineEdit('')  # 8 Acetone
        self.e65 = QLineEdit('')  # 5 Bubbler1 unknown
        self.e66 = QLineEdit('')  # 6 Bubbler2 unknown
        self.e67 = QLineEdit('')  # 9 Bubbler3 unknown
        self.e65.setStyleSheet("background-color: cornsilk")
        self.e66.setStyleSheet("background-color: cornsilk")
        self.e67.setStyleSheet("background-color: cornsilk")

        self.b21 = QCheckBox("1-ZAG")
        self.b21.setChecked(True)
        self.b21.stateChanged.connect(self.func21)
        self.b22 = QCheckBox("2-Act")
        self.b22.setChecked(True)
        self.b22.stateChanged.connect(self.func22)
        self.b23 = QCheckBox("3-IPA")
        self.b23.setChecked(True)
        self.b23.stateChanged.connect(self.func23)
        self.b24 = QCheckBox("4-PGME")
        self.b24.setChecked(True)
        self.b24.stateChanged.connect(self.func24)

        self.b25 = QCheckBox("5-Bubbler1")
        self.b25.setChecked(True)
        self.b25.stateChanged.connect(self.func25)
        self.b26 = QCheckBox("6-Bubbler2")
        self.b26.setChecked(True)
        self.b26.stateChanged.connect(self.func26)
        self.b27 = QCheckBox("7-ZAG")
        self.b27.setChecked(True)
        self.b27.stateChanged.connect(self.func27)
        self.b28 = QCheckBox("8-Act")
        self.b28.setChecked(True)
        self.b28.stateChanged.connect(self.func28)
        self.b29 = QCheckBox("9-Bubbler3")
        self.b29.setChecked(True)
        self.b29.stateChanged.connect(self.func29)
        self.b20 = QCheckBox("10-ZA")
        self.b20.setChecked(True)
        self.b20.stateChanged.connect(self.func20)

        try:
            f = open(os.path.join('par1', '2acetone.txt'), 'r')
            self.e61.setText(f.read())
            f = open(os.path.join('par1', '3IPA.txt'), 'r')
            self.e62.setText(f.read())
            f = open(os.path.join('par1', '4PGME.txt'), 'r')
            self.e63.setText(f.read())
            f = open(os.path.join('par1', '8acetone.txt'), 'r')
            self.e64.setText(f.read())
        except:
            print('No tank concentration data available.')

        try:
            f = open(os.path.join('par1', 'bubbler1.txt'), 'r')
            self.e65.setText(f.read())
            f = open(os.path.join('par1', 'bubbler2.txt'), 'r')
            self.e66.setText(f.read())
            f = open(os.path.join('par1', 'bubbler3.txt'), 'r')
            self.e67.setText(f.read())
        except:
            print('No bubbler compound name available.')

        self.g1 = QGridLayout()
        self.g1.addWidget(self.lb21, 0, 0)
        self.g1.addWidget(self.lb22, 1, 0)
        self.g1.addWidget(self.lb23, 2, 0)
        self.g1.addWidget(self.lb24, 3, 0)
        self.g1.addWidget(self.lb25, 4, 0)
        self.g1.addWidget(self.lb26, 5, 0)

        # self.g1.addWidget(self.lb31, 0, 1)
        # self.g1.addWidget(self.lb32, 0, 2)
        # self.g1.addWidget(self.lb33, 0, 3)
        # self.g1.addWidget(self.lb34, 0, 4)
        # self.g1.addWidget(self.lb35, 0, 5)
        # self.g1.addWidget(self.lb36, 0, 6)
        # self.g1.addWidget(self.lb37, 0, 7)
        # self.g1.addWidget(self.lb38, 0, 8)
        # self.g1.addWidget(self.lb39, 0, 9)
        # self.g1.addWidget(self.lb30, 0, 10)

        self.g1.addWidget(self.lb41, 1, 1)
        self.g1.addWidget(self.lb42, 1, 2)
        self.g1.addWidget(self.lb43, 1, 3)
        self.g1.addWidget(self.lb44, 1, 4)
        self.g1.addWidget(self.lb45, 1, 5)
        self.g1.addWidget(self.lb46, 1, 6)
        self.g1.addWidget(self.lb47, 1, 7)
        self.g1.addWidget(self.lb48, 1, 8)
        self.g1.addWidget(self.lb49, 1, 9)
        self.g1.addWidget(self.lb40, 1, 10)

        self.g1.addWidget(self.lb61, 2, 2)
        self.g1.addWidget(self.lb62, 2, 3)
        self.g1.addWidget(self.lb63, 2, 4)
        self.g1.addWidget(self.lb64, 2, 8)
        self.g1.addWidget(self.lb65, 2, 5)
        self.g1.addWidget(self.lb66, 2, 6)
        self.g1.addWidget(self.lb67, 2, 9)

        self.g1.addWidget(self.e61, 3, 2)
        self.g1.addWidget(self.e62, 3, 3)
        self.g1.addWidget(self.e63, 3, 4)
        self.g1.addWidget(self.e64, 3, 8)
        self.g1.addWidget(self.e65, 3, 5)
        self.g1.addWidget(self.e66, 3, 6)
        self.g1.addWidget(self.e67, 3, 9)

        self.g1.addWidget(self.e11, 4, 1)
        self.g1.addWidget(self.e12, 4, 2)
        self.g1.addWidget(self.e13, 4, 3)
        self.g1.addWidget(self.e14, 4, 4)
        self.g1.addWidget(self.e15, 4, 5)
        self.g1.addWidget(self.e16, 4, 6)
        self.g1.addWidget(self.e17, 4, 7)
        self.g1.addWidget(self.e18, 4, 8)
        self.g1.addWidget(self.e19, 4, 9)
        self.g1.addWidget(self.e10, 4, 10)

        self.g1.addWidget(self.lb51, 5, 1)
        self.g1.addWidget(self.lb52, 5, 2)
        self.g1.addWidget(self.lb53, 5, 3)
        self.g1.addWidget(self.lb54, 5, 4)
        self.g1.addWidget(self.lb55, 5, 5)
        self.g1.addWidget(self.lb56, 5, 6)
        self.g1.addWidget(self.lb57, 5, 7)
        self.g1.addWidget(self.lb58, 5, 8)
        self.g1.addWidget(self.lb59, 5, 9)
        self.g1.addWidget(self.lb50, 5, 10)

        self.g1.addWidget(self.b11, 6, 1)
        self.g1.addWidget(self.b12, 6, 2)
        self.g1.addWidget(self.b13, 6, 3)
        self.g1.addWidget(self.b14, 6, 4)
        self.g1.addWidget(self.b15, 6, 5)
        self.g1.addWidget(self.b16, 6, 6)
        self.g1.addWidget(self.b17, 6, 7)
        self.g1.addWidget(self.b18, 6, 8)
        self.g1.addWidget(self.b19, 6, 9)
        self.g1.addWidget(self.b10, 6, 10)

        self.g1.addWidget(self.b21, 0, 1)
        self.g1.addWidget(self.b22, 0, 2)
        self.g1.addWidget(self.b23, 0, 3)
        self.g1.addWidget(self.b24, 0, 4)
        self.g1.addWidget(self.b25, 0, 5)
        self.g1.addWidget(self.b26, 0, 6)
        self.g1.addWidget(self.b27, 0, 7)
        self.g1.addWidget(self.b28, 0, 8)
        self.g1.addWidget(self.b29, 0, 9)
        self.g1.addWidget(self.b20, 0, 10)

        self.L15 = QVBoxLayout()
        self.L15.addLayout(self.g1)
        self.box12.setLayout(self.L15)
        self.L12.addWidget(self.box12)

        ## refresh Alicat label
        self.timer = QTimer()
        self.timer.setInterval(tr)
        self.timer.timeout.connect(self.refresh_label)

        self.fig = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]  #plot real time figures or not, save time

    def layout3(self):  # table
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(11)
        # self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem("Time,s"))
        # self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem("MFC1"))
        # self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem("MFC2"))
        # self.tableWidget.setHorizontalHeaderItem(3, QTableWidgetItem("MFC3"))
        # self.tableWidget.setHorizontalHeaderItem(4, QTableWidgetItem("MFC4"))
        # self.tableWidget.setHorizontalHeaderItem(5, QTableWidgetItem("MFC5"))
        #
        # self.tableWidget.setHorizontalHeaderItem(6, QTableWidgetItem("MFC6"))
        # self.tableWidget.setHorizontalHeaderItem(7, QTableWidgetItem("MFC7"))
        # self.tableWidget.setHorizontalHeaderItem(8, QTableWidgetItem("MFC8"))
        # self.tableWidget.setHorizontalHeaderItem(9, QTableWidgetItem("MFC9"))
        # self.tableWidget.setHorizontalHeaderItem(10, QTableWidgetItem("MFC10"))

        self.tableWidget.setHorizontalHeaderLabels(["Time(min)", "MFC1", "MFC2", "MFC3", "MFC4", "MFC5",
                                                    "MFC6", "MFC7", "MFC8", "MFC9", "MFC10"])
        self.tableWidget.setObjectName("tableWidget")
        # self.tableWidget.horizontalHeader().setStretchLastSection(True)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)

        # header = self.tableWidget.horizontalHeader()
        # header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        # header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        # header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

        self.tableWidget.setColumnWidth(0, 80)
        self.tableWidget.setColumnWidth(1, 80)
        self.tableWidget.setColumnWidth(2, 80)
        self.tableWidget.setColumnWidth(3, 80)
        self.tableWidget.setColumnWidth(4, 80)
        self.tableWidget.setColumnWidth(5, 80)
        self.tableWidget.setColumnWidth(6, 80)
        self.tableWidget.setColumnWidth(7, 80)
        self.tableWidget.setColumnWidth(8, 80)
        self.tableWidget.setColumnWidth(9, 80)
        self.tableWidget.setColumnWidth(10, 80)

        self.L13.addWidget(self.tableWidget)

    def layout4(self):  # bottom row
        self.lb81 = QLabel('Folder')
        self.e81 = QLineEdit()  # Folder'R:\crd_G9000\AVXxx\\3610-NUV1022\R&D\Calibration\Yilin Shi')
        try:
            f = open(os.path.join('par1', 'r_drive.txt'), 'r')
            temp = f.read()
            self.e81.setText(temp)
        except:
            print('error loading folder name.')

        self.lb82 = QLabel('File (csv)')
        self.e82 = QLineEdit()  # csv file name 'sam1'
        try:
            f = open(os.path.join('par1', 'filename.txt'), 'r')
            temp = f.read()
            self.e82.setText(temp)
        except:
            print('error loading file name.')

        self.lb83 = QLabel('Cycle')
        self.e83 = QLineEdit('1')  # cycle
        self.e83.setToolTip('Number of cycles of above time series.\n'
                            'Positive integers only.\n'
                            'Type in 0 for infinity loop.')

        self.lb0 = QLabel('     ')  # progress hint
        self.lb0.setStyleSheet("background-color: lightgrey")
        self.lb84 = QLabel('Time Unit:')
        self.rb81 = QRadioButton("min", self)
        self.rb82 = QRadioButton("s", self)
        self.rb81.setChecked(True)

        self.lb85 = QLabel('    ')  # error hint
        self.lb86 = QLabel('    ')  # total time hint
        self.lb88 = QLabel('    ')  # gap
        self.lb89 = QLabel('     ')  # gap

        self.b8 = QPushButton("Change")
        self.b8.clicked.connect(self.cycletime)
        self.b8.setEnabled(False)

        self.g3 = QGridLayout()
        self.g3.addWidget(self.lb81, 0, 0, 1, 1)
        self.g3.addWidget(self.e81, 0, 1, 1, 8)
        self.g3.addWidget(self.lb88, 0, 9, 1, 1)
        self.g3.addWidget(self.lb82, 1, 0, 1, 1)
        self.g3.addWidget(self.e82, 1, 1, 1, 1)
        self.g3.addWidget(self.lb89, 1, 2, 1, 1)
        self.g3.addWidget(self.lb83, 1, 3, 1, 1)  # 'cycle'
        self.g3.addWidget(self.e83, 1, 4, 1, 1)
        self.g3.addWidget(self.lb84, 1, 5, 1, 1)  # 'time unit:'
        self.g3.addWidget(self.rb81, 1, 6, 1, 1)  # min
        self.g3.addWidget(self.rb82, 1, 7, 1, 1)  # s
        self.g3.addWidget(self.b8, 1, 8, 1, 1)

        self.g3.addWidget(self.lb0, 2, 0, 1, 4)
        self.g3.addWidget(self.lb85, 2, 4, 1, 2)  # total time hint
        self.g3.addWidget(self.lb86, 2, 6, 1, 3)  # error hint

        self.b1 = QToolButton()
        self.b1.setIcon(QIcon("icons/list2.png"))
        self.b1.setIconSize(QSize(40, 40))
        self.b1.setToolTip("load selected csv file")
        self.b1.clicked.connect(self.func1)
        self.lb1 = QLabel('Load csv')

        self.b2 = QToolButton()
        self.b2.setIcon(QIcon("icons/start1.png"))
        self.b2.setIconSize(QSize(40, 40))
        self.b2.setToolTip("Start")
        self.b2.clicked.connect(self.func2)
        self.b2.setEnabled(False)
        self.lb2 = QLabel('  Start  ')

        self.b3 = QToolButton()
        self.b3.setIcon(QIcon("icons/pause2.png"))
        self.b3.setIconSize(QSize(40, 40))
        self.b3.setToolTip("Pause the table and Tab2 plot or stop")
        self.b3.clicked.connect(self.func3)
        self.b3.setEnabled(False)
        self.lb3 = QLabel('Pause/Stop')

        self.b4 = QToolButton()
        self.b4.setIcon(QIcon("icons/resu1.png"))
        self.b4.setIconSize(QSize(40, 40))
        self.b4.setToolTip("Resume the table and Tab2 plot")
        self.b4.clicked.connect(self.func4)
        self.b4.setEnabled(False)
        self.lb4 = QLabel(' Resume')

        self.b5 = QToolButton()
        self.b5.setIcon(QIcon("icons/zero.png"))
        self.b5.setIconSize(QSize(40, 40))
        self.b5.setToolTip("Zero all MFCs")
        self.b5.clicked.connect(self.func5)
        self.lb5 = QLabel('Zero ALL')

        self.b9 = QToolButton()
        self.b9.setIcon(QIcon("icons/stop1.png"))
        self.b9.setIconSize(QSize(40, 40))
        self.b9.setToolTip("Close")
        self.b9.clicked.connect(self.exitFunc)
        self.lb9 = QLabel('   Close')

        self.lb91 = QLabel('  ')  # gap
        self.lb92 = QLabel('  ')  # gap
        self.lb93 = QLabel('  ')  # gap
        self.lb94 = QLabel('  ')  # gap
        self.lb95 = QLabel('  ')  # gap

        self.g4 = QGridLayout()
        self.g4.addWidget(self.b1, 0, 0)
        self.g4.addWidget(self.lb1, 1, 0)
        self.g4.addWidget(self.lb91, 1, 1)

        self.g4.addWidget(self.b2, 0, 2)
        self.g4.addWidget(self.lb2, 1, 2)
        self.g4.addWidget(self.lb92, 1, 3)

        self.g4.addWidget(self.b3, 0, 4)
        self.g4.addWidget(self.lb3, 1, 4)
        self.g4.addWidget(self.lb93, 1, 5)

        self.g4.addWidget(self.b4, 0, 6)
        self.g4.addWidget(self.lb4, 1, 6)
        self.g4.addWidget(self.lb94, 1, 7)

        self.g4.addWidget(self.b5, 0, 8)
        self.g4.addWidget(self.lb5, 1, 8)
        self.g4.addWidget(self.lb95, 1, 9)

        self.g4.addWidget(self.b9, 0, 10)
        self.g4.addWidget(self.lb9, 1, 10)

        self.L16 = QHBoxLayout()
        self.L17 = QHBoxLayout()
        self.L16.addLayout(self.g3)
        self.L17.addLayout(self.g4)
        self.L14.addLayout(self.L16)
        self.L14.addLayout(self.L17)

    ################### tab2  ###################
    def layout5(self):
        self.figure1 = plt.figure()
        self.canvas1 = FigureCanvas(self.figure1)
        self.toolbar1 = NavigationToolbar(self.canvas1, self)
        self.L201.addWidget(self.canvas1)
        self.L201.addWidget(self.toolbar1)  # *** matplotlib tool bar

    ################### tab3  ###################
    def layout6(self):
        self.figure2 = plt.figure()
        self.canvas2 = FigureCanvas(self.figure2)
        self.toolbar2 = NavigationToolbar(self.canvas2, self)
        self.L301.addWidget(self.canvas2)
        self.L301.addWidget(self.toolbar2)  # *** matplotlib tool bar

    ################### tab3  ###################
    def layout7(self):
        self.lb302 = QLabel(" ")
        self.lb300 = QLabel()
        self.pixmap = QPixmap('icons/sam1.png')
        self.lb300.setPixmap(
            self.pixmap.scaled(900, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        # self.lb300.setPixmap(self.pixmap)
        self.lb300.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.L401.addWidget(self.lb300)

    ################### tab4  ###################
    def layout8(self):
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

        self.lb214 = QLabel("Alicat Sample1:")
        self.lb215 = QLabel("Serial Port:")
        self.e202 = QLineEdit()   # '/dev/cu.usbserial-A908UXOQ' '/dev/tty.usbserial-A908UXOQ'
        self.lb216 = QLabel(" ")  ## port not found
        self.b202 = QPushButton("Detect", self)
        self.b202.clicked.connect(self.func202)
        self.b202.setStyleSheet("font: bold")
        self.b202.setToolTip("Detect the name of the port connected to Alicat.")

        self.lb217 = QLabel("Alicat Sample2:")
        self.lb218 = QLabel("Serial Port:")
        self.e203 = QLineEdit()   # '/dev/cu.usbserial-A908UXOQ' '/dev/tty.usbserial-A908UXOQ'
        self.lb219 = QLabel(" ")  ## port not found
        self.b203 = QPushButton("Detect", self)
        self.b203.clicked.connect(self.func203)
        self.b203.setStyleSheet("font: bold")
        self.b203.setToolTip("Detect the name of the port connected to Alicat.")


        self.lb298 = QLabel('    ')
        self.lb299 = QLabel('Yilin Shi | Version 1.0 | Spring 2022 | Santa Clara, CA    ')
        self.lb299.setFont(QFont('Arial', 10))
        self.lb299.setAlignment(Qt.AlignmentFlag.AlignRight)

        try:
            f = open(os.path.join('par1', 'analyzer.txt'), "r")
            temp = f.read()  # .splitlines()
            self.e201.setText(temp)  # analyzer
            f = open(os.path.join('par1', 'alicat1.txt'), "r")
            temp = f.read()
            self.e202.setText(temp)  # alicat1
            f = open(os.path.join('par1', 'alicat2.txt'), "r")
            temp = f.read()
            self.e203.setText(temp)  # alicat2
        except:
            print('failed to load port names')

        self.g21 = QGridLayout()
        self.g21.addWidget(self.lb201, 0, 0)
        self.g21.addWidget(self.rb201, 1, 0)
        self.g21.addWidget(self.rb202, 2, 0)
        self.g21.addWidget(self.rb203, 3, 0)
        self.g21.addWidget(self.b200,  4, 0)
        self.g21.addWidget(self.e200,  5, 0, 1, 3)

        self.g21.addWidget(self.lb211, 6, 0)
        self.g21.addWidget(self.lb212, 7, 0)
        self.g21.addWidget(self.e201,  7, 1)
        self.g21.addWidget(self.b201,  7, 2)
        self.g21.addWidget(self.lb213, 8, 1)

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

        self.g21.addWidget(self.lb298, 15, 1)
        self.g21.addWidget(self.lb299, 16, 1, 1, 3)

        self.L501.addLayout(self.g21)
        self.L501.addStretch()  # *** will tight the space

    ##################################################
    ################### Functions  ###################
    ##################################################
    def mfcs(self):  # check all MFCs connection
        try:
            port_ali1 = self.e202.text()
            port_ali2 = self.e203.text()
            self.fc1 = FlowController(port=port_ali1, address='A')
            self.fc2 = FlowController(port=port_ali1, address='B')
            self.fc3 = FlowController(port=port_ali1, address='C')
            self.fc4 = FlowController(port=port_ali1, address='D')
            self.fc5 = FlowController(port=port_ali1, address='E')
            self.fc6 = FlowController(port=port_ali1, address='F')
            self.fc7 = FlowController(port=port_ali2, address='G')
            self.fc8 = FlowController(port=port_ali2, address='H')
            self.fc9 = FlowController(port=port_ali2, address='I')
            self.fc10 = FlowController(port=port_ali2, address='J')
            self.conn = 1
        except:
            self.lb0.setText('MFCs are not connected.')
            self.conn = 0

    ########### Set MFCs  ###########
    def func11(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb31.text()
                b = float(self.e11.text())
                if b > 10:
                    self.lb0.setText('MFC%s takes value 0-10.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb51.text()
                    self.fc1.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func12(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb32.text()
                b = float(self.e12.text())
                if b > 50:
                    self.lb0.setText('MFC%s takes value 0-50.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb52.text()
                    self.fc2.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func13(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb33.text()
                b = float(self.e13.text())
                if b > 100:
                    self.lb0.setText('MFC%s takes value 0-100.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb53.text()
                    self.fc3.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func14(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb34.text()
                b = float(self.e14.text())
                if b > 50:
                    self.lb0.setText('MFC%s takes value 0-50.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb54.text()
                    self.fc4.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func15(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb35.text()
                b = float(self.e15.text())
                if b > 10:
                    self.lb0.setText('MFC%s takes value 0-10.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb55.text()
                    self.fc5.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func16(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb36.text()
                b = float(self.e16.text())
                if b > 10:
                    self.lb0.setText('MFC%s takes value 0-10.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb56.text()
                    self.fc6.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func17(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb37.text()
                b = float(self.e17.text())
                if b > 10:
                    self.lb0.setText('MFC%s takes value 0-10.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb57.text()
                    self.fc7.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func18(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb38.text()
                b = float(self.e18.text())
                if b > 50:
                    self.lb0.setText('MFC%s takes value 0-50.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb58.text()
                    self.fc8.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func19(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb39.text()
                b = float(self.e19.text())
                if b > 10:
                    self.lb0.setText('MFC%s takes value 0-10.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb59.text()
                    # self.greybox(self.e67)
                    self.fc9.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    def func10(self):
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                a = self.lb30.text()
                b = float(self.e10.text())
                if b > 200:
                    self.lb0.setText('MFC%s takes value 0-200.' % a)
                elif b < 0:
                    self.lb0.setText('Please enter a number >=0.')
                else:
                    c = self.lb50.text()
                    self.fc10.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.' % (a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')

    ########### plot real time figure or not   ###########
    def func21(self, checked):
        if checked:
            self.fig[0] = 1
        else:
            self.fig[0] = 0
        self.show()

    def func22(self, checked):
        if checked:
            self.fig[1] = 1
        else:
            self.fig[1] = 0
        self.show()

    def func23(self, checked):
        if checked:
            self.fig[2] = 1
        else:
            self.fig[2] = 0
        self.show()

    def func24(self, checked):
        if checked:
            self.fig[3] = 1
        else:
            self.fig[3] = 0
        self.show()

    def func25(self, checked):
        if checked:
            self.fig[4] = 1
        else:
            self.fig[4] = 0
        self.show()

    def func26(self, checked):
        if checked:
            self.fig[5] = 1
        else:
            self.fig[5] = 0
        self.show()

    def func27(self, checked):
        if checked:
            self.fig[6] = 1
        else:
            self.fig[6] = 0
        self.show()

    def func28(self, checked):
        if checked:
            self.fig[7] = 1
        else:
            self.fig[7] = 0
        self.show()

    def func29(self, checked):
        if checked:
            self.fig[8] = 1
        else:
            self.fig[8] = 0
        self.show()

    def func20(self, checked):
        if checked:
            self.fig[9] = 1
        else:
            self.fig[9] = 0
        self.show()


    ########### last block   ###########
    def cycletime(self):
        try:
            folder = self.e81.text()
            fname = self.e82.text()
            fn = os.path.join(folder, fname + '.csv')
            cycle = int(self.e83.text())
            df = pd.read_csv(fn)
            tc = df.iloc[:, 0]  # first column is time
            if self.rb81.isChecked():  # min, time unit
                tc = tc * 60
                self.tableWidget.setHorizontalHeaderLabels(["Time(min)", "MFC1", "MFC2", "MFC3", "MFC4", "MFC5",
                                                            "MFC6", "MFC7", "MFC8", "MFC9", "MFC10"])
            else:  # s, time unit
                self.tableWidget.setHorizontalHeaderLabels(["Time(s)", "MFC1", "MFC2", "MFC3", "MFC4", "MFC5",
                                                            "MFC6", "MFC7", "MFC8", "MFC9", "MFC10"])

            tcyc = sum(list(tc))  # time of 1 cycle
            if tcyc < 3600:
                tcyc1 = str(round(tcyc / 60, 1)) + ' min'
            else:
                tcyc1 = str(round(tcyc / 3600, 1)) + ' h'

            if cycle < 0:
                self.lb86.setText('Please put in an integer >=0.')
            elif cycle:
                total_time = tcyc * cycle
                if total_time < 3600:
                    total = str(round(total_time / 60, 1)) + ' min'
                elif total_time < 86400:
                    total = str(round(total_time / 3600, 1)) + ' h'
                else:
                    total = str(round(total_time / 86400, 1)) + ' d'
                self.lb86.setText(tcyc1 + '/cycle, total time: %s' % (total))
            else:
                self.lb86.setText('Infinity loop, ' + tcyc1 + '/cycle.')
            return 1
        except:
            self.lb86.setText('Please enter an integer >=0.')
            return 0

    def func1(self):  # load csv
        folder = self.e81.text()
        fname = self.e82.text()
        fn = os.path.join(folder, fname + '.csv')
        if not os.path.isdir(folder):
            self.lb0.setText('Folder not found.')
        elif not os.path.isfile(fn):
            self.lb0.setText('csv file not found.')
        else:
            try:
                df = pd.read_csv(fn)
                result = df.to_numpy()
                print(result.shape)

                self.tableWidget.setRowCount(0)
                for row_number, row_data in enumerate(result):
                    self.tableWidget.insertRow(row_number)
                    for column_number, data in enumerate(row_data):
                        if column_number == 0:
                            self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(int(data))))
                            self.tableWidget.item(row_number, 0).setBackground(QColor(170, 170, 170))
                        else:
                            self.tableWidget.setItem(row_number, column_number, QTableWidgetItem(str(data)))

                self.cycletime()

                fnn = os.path.join('par1', 'r_drive.txt')
                if os.path.isfile(fnn):
                    os.remove(fnn)
                with open(fnn, 'a') as f:
                    f.write(folder)
                fnn = os.path.join('par1', 'filename.txt')
                if os.path.isfile(fnn):
                    os.remove(fnn)
                with open(fnn, 'a') as f:
                    f.write(fname)

                self.lb0.setText('%s.csv file loaded' % (fname))
                self.b2.setEnabled(True)
                self.b3.setEnabled(False)
                self.b4.setEnabled(False)
                self.b8.setEnabled(True)
            except:
                self.lb0.setText('Error loading %s.csv file.' % (fname))

    def refresh_label(self):
        try:
            fl1 = self.fc1.get()['mass_flow']
            fl2 = self.fc2.get()['mass_flow']
            fl3 = self.fc3.get()['mass_flow']
            fl4 = self.fc4.get()['mass_flow']
            fl5 = self.fc5.get()['mass_flow']
            fl6 = self.fc6.get()['mass_flow']
            fl7 = self.fc7.get()['mass_flow']
            fl8 = self.fc8.get()['mass_flow']
            fl9 = self.fc9.get()['mass_flow']
            fl10 = self.fc10.get()['mass_flow']

            try:
                host = self.e201.text()
                ipadd = 'http://' + host
                MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection",
                                                        IsDontCareConnection=False)
                MeasSystem.Backdoor.SetData('MFC1_flow', fl1)
                MeasSystem.Backdoor.SetData('MFC2_flow', fl2)
                MeasSystem.Backdoor.SetData('MFC3_flow', fl3)
                MeasSystem.Backdoor.SetData('MFC4_flow', fl4)
                MeasSystem.Backdoor.SetData('MFC5_flow', fl5)
                MeasSystem.Backdoor.SetData('MFC6_flow', fl6)
                MeasSystem.Backdoor.SetData('MFC7_flow', fl7)
                MeasSystem.Backdoor.SetData('MFC8_flow', fl8)
                MeasSystem.Backdoor.SetData('MFC9_flow', fl9)
                MeasSystem.Backdoor.SetData('MFC10_flow', fl10)
                self.lb85.setText('Data sent to Analyzer.')
            except:
                self.lb85.setText('Analyzer port error.')

            self.lb41.setText(str(fl1))
            self.lb42.setText(str(fl2))
            self.lb43.setText(str(fl3))
            self.lb44.setText(str(fl4))
            self.lb45.setText(str(fl5))
            self.lb46.setText(str(fl6))
            self.lb47.setText(str(fl7))
            self.lb48.setText(str(fl8))
            self.lb49.setText(str(fl9))
            self.lb40.setText(str(fl10))

            # concentration labels, ppb
            try:
                con1 = round(float(fl2) / float(fl1) * self.c2acetone, 4)
                con2 = round(float(fl3) / float(fl1) * self.c3IPA, 4)
                con3 = round(float(fl4) / float(fl1) * self.c4PGME, 4)
                con4 = round(float(fl8) / float(fl7) * self.c8acetone, 4)
                self.lb61.setText(str(con1))  # 2 Acetone
                self.lb62.setText(str(con2))  # 3 IPA
                self.lb63.setText(str(con3))  # 4 PGME
                self.lb64.setText(str(con4))  # 8 Acetone
            except:  # when fl1 = 0
                self.lb61.setText('0')
                self.lb62.setText('0')
                self.lb63.setText('0')
                self.lb64.setText('0')
        except:
            self.lb85.setText('Error refresh Alicat.')

    def tank(self):  # check if tank concentration has valid value
        tag = 1
        try:
            self.c2acetone = float(self.e61.text())
            if self.c2acetone < 0:
                self.redbox(self.e61)
                tag = 0
            else:
                self.greybox(self.e61)
        except:
            self.redbox(self.e61)
            tag = 0

        try:
            self.c3IPA = float(self.e62.text())
            if self.c3IPA < 0:
                self.redbox(self.e62)
                tag = 0
            else:
                self.greybox(self.e62)
        except:
            self.redbox(self.e62)
            tag = 0

        try:
            self.c4PGME = float(self.e63.text())
            if self.c4PGME < 0:
                self.redbox(self.e63)
                tag = 0
            else:
                self.greybox(self.e63)
        except:
            self.redbox(self.e63)
            tag = 0

        try:
            self.c8acetone = float(self.e64.text())
            if self.c8acetone < 0:
                self.redbox(self.e64)
                tag = 0
            else:
                self.greybox(self.e64)
        except:
            self.redbox(self.e64)
            tag = 0

        if not tag:
            self.lb0.setText('Error, check tank concentration.')
        return tag


    def bub(self): #check if bubbler chemical name filled
        tag = 1
        if self.e65.text() == '':
            self.redbox(self.e65)
            tag = 0
        else:
            self.greybox(self.e65)
            self.e65.setStyleSheet("background-color: cornsilk")

        if self.e66.text() == '':
            self.redbox(self.e66)
            tag = 0
        else:
            self.greybox(self.e66)
            self.e66.setStyleSheet("background-color: cornsilk")

        if self.e67.text() == '':
            self.redbox(self.e67)
            tag = 0
        else:
            self.greybox(self.e67)
            self.e67.setStyleSheet("background-color: cornsilk")

        if not tag:
            self.lb0.setText('Error, missing bubbler compound information.')
        return tag


    def analyzerip(self):
        try:
            host = self.e201.text()
            socket.create_connection((host, port_in), 3)
            # self.lb0.setText('Analyzer in port ready')
            self.anaip = 1
        except:
            self.lb0.setText('Analyzer in port not ready.')

    def func2(self):  # start run csv data, refresh label, plot
        folder = self.e81.text()
        fnpar = os.path.join(folder, 'par')
        tag = 1
        if os.path.isdir(fnpar):
            reply = QMessageBox.question(self, 'Warning',
                                         "Experiment Parameters folder 'par' already exist.\n "
                                         "You need to delete or rename it to start a new experiment.\n"
                                         "Delete 'par' folder?", QMessageBox.StandardButton.Yes |
                                         QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)

            if reply == QMessageBox.StandardButton.Yes:
                shutil.rmtree(fnpar)
            else:
                tag = 0

        if tag:
            try:
                if not self.anaip:
                    self.analyzerip()

                if self.anaip and self.tank() and self.bub():
                    # print('test')
                    self.canvas1.close_event()
                    self.figure1.clear()
                    self.canvas2.close_event()
                    self.figure2.clear()

                    if self.cycletime():
                        if not self.conn:
                            self.mfcs()
                        if self.conn:
                            self.timer.start()  # alicat data, refresh label, send to analyzer backdoor
                            self.plot1()
                            self.b1.setEnabled(False)
                            self.b3.setEnabled(True)
                            self.b4.setEnabled(False)

                            t1 = int(time.time())
                            t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))
                            self.label1 = 'Start: %s ' % t
                            self.lb0.setText(self.label1)
                            self.lb85.setText(' ')

                            folder = self.e81.text()
                            fnpar = os.path.join(folder, 'par')
                            os.mkdir(fnpar)
                            fn = os.path.join(folder, 'par', 't1.txt')
                            t = time.strftime('%Y%m%d%H%M', time.localtime(t1))
                            with open(fn, 'a') as f:
                                f.write('%s\n%s\n%s' % (t[:8], t[8:10], t[10:]))

                            # save parameters in 'par'
                            fn = os.path.join(folder, 'par', '2acetone.txt')
                            with open(fn, 'a') as f:
                                f.write(self.e61.text()+'\nppm')
                            fn = os.path.join(folder, 'par', '3IPA.txt')
                            with open(fn, 'a') as f:
                                f.write(self.e62.text()+'\nppm')
                            fn = os.path.join(folder, 'par', '4PGME.txt')
                            with open(fn, 'a') as f:
                                f.write(self.e63.text()+'\nppm')
                            fn = os.path.join(folder, 'par', '8acetone.txt')
                            with open(fn, 'a') as f:
                                f.write(self.e64.text()+'\nppm')
                            fn = os.path.join(folder, 'par', 'bubbler1.txt')
                            with open(fn, 'a') as f:
                                f.write(self.e65.text().rstrip())  #remove end return
                            fn = os.path.join(folder, 'par', 'bubbler2.txt')
                            with open(fn, 'a') as f:
                                f.write(self.e66.text().rstrip())
                            fn = os.path.join(folder, 'par', 'bubbler3.txt')
                            with open(fn, 'a') as f:
                                f.write(self.e67.text().rstrip())
                            fn = os.path.join(folder, 'par', 'cycle.txt')
                            with open(fn, 'a') as f:
                                f.write('0 of %s cycles done.\n\n'%self.e83.text())

                            # save parameters in 'par1' of source code
                            p = os.path.join('par1', '2acetone.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e61.text())

                            p = os.path.join('par1', '3IPA.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e62.text())

                            p = os.path.join('par1', '4PGME.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e63.text())

                            p = os.path.join('par1', '8acetone.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e64.text())

                            p = os.path.join('par1', 'bubbler1.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e65.text())

                            p = os.path.join('par1', 'bubbler2.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e66.text())

                            p = os.path.join('par1', 'bubbler3.txt')
                            if os.path.isfile(p):
                                os.remove(p)
                            with open(p, 'a') as f:
                                f.write(self.e67.text())
            except:
                self.conn = 0
                self.lb0.setText('Error run experiment.')

    def gen_mfc(self, total, cycle=0):
        if cycle:
            folder = self.e81.text()
            for j in range(cycle):
                for i in range(total):
                    # print(i)
                    yield i

            t1 = int(time.time())
            fn = os.path.join(folder, 'par', 't3.txt')
            if os.path.isfile(fn):
                os.remove(fn)
            t = time.strftime('%Y%m%d%H%M', time.localtime(t1))
            with open(fn, 'a') as f:
                f.write('%s\n%s\n%s' % (t[:8], t[8:10], t[10:12]))

            self.timer.stop()
            self.lb0.setText(self.label1)
            t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))
            self.lb85.setText('Finished at %s.' % t)
            self.b1.setEnabled(True)
            self.b2.setEnabled(True)
            self.b3.setEnabled(False)
            self.b4.setEnabled(False)
        else:
            for i in range(total):
                yield i

    def plot1(self):  # start run csv data, plots shown on 2 figures
        try:
            folder = self.e81.text()
            fname = self.e82.text()
            fn = os.path.join(folder, fname + '.csv')
            df = pd.read_csv(fn)
            tc = df.iloc[:, 0]  # first column is time, s
            nr = df.shape[0]  # row number
            nc = df.shape[1]  # column number
            cycle = int(self.e83.text())
            self.fn3 = os.path.join(folder, 'par', 't3.txt')
            self.fn4 = os.path.join(folder, 'par', 'cycle.txt')

            if self.rb81.isChecked():  # use time unit min
                tc = tc * 60

            tc = list(tc)
            t_start = []  # s, start row
            t_end = []  # s, end row
            sum = 0
            for t in tc:
                t_start.append(sum)
                sum += t
                t_end.append(sum - 1)
            total = sum
            print('total points')
            print(total)
            self.ct = 1  # cycle counter

            x = []     ## epoch time 1641259801
            xx = []    ## epoch time, x labels that will be marked
            xmak = []  ## clock time x label

            x2 = []
            xx2 = []
            xmak2 = []

            y1 = []
            y2 = []
            y3 = []
            y4 = []
            y5 = []
            y6 = []
            y7 = []
            y8 = []
            y9 = []
            y10 = []

            ax1 = self.figure1.add_subplot(321)
            ax2 = self.figure1.add_subplot(322)
            ax3 = self.figure1.add_subplot(323)
            ax4 = self.figure1.add_subplot(324)
            ax5 = self.figure1.add_subplot(325)
            ax6 = self.figure1.add_subplot(326)

            ax7 = self.figure2.add_subplot(221)
            ax8 = self.figure2.add_subplot(222)
            ax9 = self.figure2.add_subplot(223)
            ax0 = self.figure2.add_subplot(224)

            box = ax1.get_position()  # Shrink current axis's height by 10% on the bottom
            ax1.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax2.get_position()
            ax2.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax3.get_position()
            ax3.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax4.get_position()  # Shrink current axis's height by 10% on the bottom
            ax4.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax5.get_position()
            ax5.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax6.get_position()
            ax6.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

            box = ax7.get_position()
            ax7.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax8.get_position()
            ax8.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax9.get_position()
            ax9.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax0.get_position()
            ax0.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

            t1 = time.strftime("%Y%m%d")  # current time
            self.figure1.text(0.4, 0.04, 'Clock Time (Y-M-D), %s-%s-%s' % (t1[:4], t1[4:6], t1[-2:]))
            self.figure1.text(0.72, 0.04, '---- Set', color='g')
            self.figure1.text(0.8, 0.04, '---- Measured', color='k')

            self.figure2.text(0.4, 0.04, 'Clock Time (Y-M-D), %s-%s-%s' % (t1[:4], t1[4:6], t1[-2:]))
            self.figure2.text(0.72, 0.04, '---- Set', color='g')
            self.figure2.text(0.8, 0.04, '---- Measured', color='k')

            self.view_point = int(spec_xt * 60)  # 1 pt/s, total pt displayed in window
            print(self.view_point)

            # target y value list
            yy1 = []
            yy2 = []
            yy3 = []
            yy4 = []
            yy5 = []
            yy6 = []
            yy7 = []
            yy8 = []
            yy9 = []
            yy10 = []

            # current target value
            self.f1 = 0
            self.f2 = 0
            self.f3 = 0
            self.f4 = 0
            self.f5 = 0
            self.f6 = 0
            self.f7 = 0
            self.f8 = 0
            self.f9 = 0
            self.f10 = 0

            def animate(i):
                print(i)
                if i == 0:
                    print('reset background color')
                    for p in range(nr):  # time column deep grey
                        self.tableWidget.item(p, 0).setBackground(QColor(170, 170, 170))
                    for p in range(nr):  # remaining cells white
                        for q in range(1, nc):
                            self.tableWidget.item(p, q).setBackground(QColor(250, 250, 250))
                    QApplication.processEvents()  # must present to show the effect
                    itemMeasVal = self.tableWidget.item(0, 0)
                    self.tableWidget.setItem(0, 0, itemMeasVal)
                    self.tableWidget.scrollToItem(itemMeasVal, QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)

                if i in t_start:  # start a row, set MFC, set green color
                    idx = t_start.index(i)
                    print(idx)
                    row = list(df.iloc[idx])
                    self.f1 = row[1]
                    self.f2 = row[2]
                    self.f3 = row[3]
                    self.f4 = row[4]
                    self.f5 = row[5]
                    self.f6 = row[6]
                    self.f7 = row[7]
                    self.f8 = row[8]
                    self.f9 = row[9]
                    self.f10 = row[10]

                    self.fc1.set_flow_rate(self.f1)
                    self.fc2.set_flow_rate(self.f2)
                    self.fc3.set_flow_rate(self.f3)
                    self.fc4.set_flow_rate(self.f4)
                    self.fc5.set_flow_rate(self.f5)
                    self.fc6.set_flow_rate(self.f6)
                    self.fc7.set_flow_rate(self.f7)
                    self.fc8.set_flow_rate(self.f8)
                    self.fc9.set_flow_rate(self.f9)
                    self.fc10.set_flow_rate(self.f10)

                    self.tableWidget.item(idx, 0).setBackground(QColor(115, 130, 95))  # green grey
                    for j in range(1, nc):
                        self.tableWidget.item(idx, j).setBackground(QColor(151, 186, 102))  # green
                    QApplication.processEvents()  # must present to show the effect

                    itemMeasVal = self.tableWidget.item(idx, 0)  ## set to visible in window
                    self.tableWidget.setItem(idx, 0, itemMeasVal)
                    # self.tableWidget.scrollToItem(itemMeasVal,QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible)
                    self.tableWidget.scrollToItem(itemMeasVal, QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)
                    # This is for the bar to scroll automatically and then the current item added is always visible

                tag = (len(x) == self.view_point)
                if tag:  ## x-axis number
                    x.pop(0)
                t = int(time.time())  # epoch time
                x.append(t)

                ## create labels
                clock = time.strftime('%H:%M', time.localtime(t))
                if len(xx):
                    clock0 = time.strftime('%H:%M', time.localtime(x[-2]))  # previous time string
                    if ((clock0[-2:] == '59' and clock[-2:] == '00') or
                            (clock0[-2:] == '14' and clock[-2:] == '15') or
                            (clock0[-2:] == '44' and clock[-2:] == '45') or
                            (clock0[-2:] == '29' and clock[-2:] == '30')):
                        xx.append(t)
                        xmak.append(clock)
                else:  # no label yet, add current as first
                    xx.append(t)
                    xmak.append(clock)

                if (len(xx) > 0) and (xx[0] < x[0]):
                    xx.pop(0)
                    xmak.pop(0)

                if self.fig[0]:
                    fl1 = self.fc1.get()
                    if tag:
                        y1.pop(0)
                        yy1.pop(0)
                    y1.append(fl1['mass_flow'])
                    yy1.append(self.f1)

                    ax1.clear()
                    ax1.plot(x, y1, linewidth=0.5, c='k')  # measured
                    ax1.plot(x, yy1, linewidth=0.5, c='g')  # target
                    ax1.set_xticks(xx, xmak)
                ax1.set_xlabel('MFC1, ZAG')

                if self.fig[1]:
                    fl2 = self.fc2.get()
                    if tag:
                        y2.pop(0)
                        yy2.pop(0)
                    y2.append(fl2['mass_flow'])
                    yy2.append(self.f2)

                    ax2.clear()
                    ax2.plot(x, y2, linewidth=0.5, c='k')
                    ax2.plot(x, yy2, linewidth=0.5, c='g')
                    ax2.set_xticks(xx, xmak)
                ax2.set_xlabel('MFC2, Acetone')

                if self.fig[2]:
                    fl3 = self.fc3.get()
                    if tag:
                        y3.pop(0)
                        yy3.pop(0)
                    y3.append(fl3['mass_flow'])
                    yy3.append(self.f3)

                    ax3.clear()
                    ax3.plot(x, y3, linewidth=0.5, c='k')
                    ax3.plot(x, yy3, linewidth=0.5, c='g')
                    ax3.set_xticks(xx, xmak)
                ax3.set_xlabel('MFC3, IPA')

                if self.fig[3]:
                    fl4 = self.fc4.get()
                    if tag:
                        y4.pop(0)
                        yy4.pop(0)
                    y4.append(fl4['mass_flow'])
                    yy4.append(self.f4)

                    ax4.clear()
                    ax4.plot(x, y4, linewidth=0.5, c='k')
                    ax4.plot(x, yy4, linewidth=0.5, c='g')
                    ax4.set_xticks(xx, xmak)
                ax4.set_xlabel('MFC4, PGME')

                if self.fig[4]:
                    fl5 = self.fc5.get()
                    if tag:
                        y5.pop(0)
                        yy5.pop(0)
                    y5.append(fl5['mass_flow'])
                    yy5.append(self.f5)

                    ax5.clear()
                    ax5.plot(x, y5, linewidth=0.5, c='k')
                    ax5.plot(x, yy5, linewidth=0.5, c='g')
                    ax5.set_xticks(xx, xmak)
                ax5.set_xlabel('MFC5, Bubbler1')

                if self.fig[5]:
                    fl6 = self.fc6.get()
                    if tag:
                        y6.pop(0)
                        yy6.pop(0)
                    y6.append(fl6['mass_flow'])
                    yy6.append(self.f6)

                    ax6.clear()
                    ax6.plot(x, y6, linewidth=0.5, c='k')
                    ax6.plot(x, yy6, linewidth=0.5, c='g')
                    ax6.set_xticks(xx, xmak)
                ax6.set_xlabel('MFC6, Bubbler2')


                if i in t_end:  # end a row: grey color
                    idx = t_end.index(i)
                    self.tableWidget.item(idx, 0).setBackground(QColor(170, 170, 170))  # deep gray
                    for j in range(1, nc):
                        self.tableWidget.item(idx, j).setBackground(QColor(230, 230, 230))  # light gray
                    QApplication.processEvents()  # must present to show the effect

                if (i + 1) == total:  # one cycle finish
                    tlog = time.strftime('%Y%m%d %H:%M:%S', time.localtime(int(time.time())))
                    note = 'Cycle %s of %s done.\n%s\n\n' % (self.ct, self.e83.text(), tlog)
                    print(note)

                    if os.path.isfile(self.fn3):
                        os.remove(self.fn3)
                    with open(self.fn3, 'a') as f:
                        f.write('%s\n%s\n%s' % (tlog[:8], tlog[9:11], tlog[12:14]))

                    # with open(self.fn4, 'a') as f:   #there is instance r drive disconnect, this will crash whole program
                    #     f.write(note)
                    try:
                        with open(self.fn4, 'a') as f:
                            f.write(note)
                    except:
                        pass

                    self.lb85.setText('')
                    self.lb0.setText(self.label1 + 'Cycle %s done.' % self.ct)
                    self.ct += 1

            def animate2(i):
                tag = (len(x2) == self.view_point)
                if tag:  ## x-axis
                    x2.pop(0)
                t = int(time.time())  # epoch time
                x2.append(t)

                ## create labels
                clock = time.strftime('%H:%M', time.localtime(t))
                if len(xx2):
                    clock0 = time.strftime('%H:%M', time.localtime(x2[-2]))  # previous time string
                    if ((clock0[-2:] == '59' and clock[-2:] == '00') or
                            (clock0[-2:] == '14' and clock[-2:] == '15') or
                            (clock0[-2:] == '44' and clock[-2:] == '45') or
                            (clock0[-2:] == '29' and clock[-2:] == '30')):
                        xx2.append(t)
                        xmak2.append(clock)
                else:  # no label yet, add current as first
                    xx2.append(t)
                    xmak2.append(clock)

                if (len(xx2) > 0) and (xx2[0] < x2[0]):
                    xx2.pop(0)
                    xmak2.pop(0)

                if self.fig[6]:
                    fl7 = self.fc7.get()
                    if tag:  ## x-axis
                        y7.pop(0)
                        yy7.pop(0)
                    y7.append(fl7['mass_flow'])
                    yy7.append(self.f7)

                    ax7.clear()
                    ax7.plot(x2, y7, linewidth=0.5, c='k')  # measured
                    ax7.plot(x2, yy7, linewidth=0.5, c='g')  # target
                    ax7.set_xticks(xx2, xmak2)
                ax7.set_xlabel('MFC7, ZAG2')

                if self.fig[7]:
                    fl8 = self.fc8.get()
                    if tag:
                        y8.pop(0)
                        yy8.pop(0)
                    y8.append(fl8['mass_flow'])
                    yy8.append(self.f8)

                    ax8.clear()
                    ax8.plot(x2, y8, linewidth=0.5, c='k')
                    ax8.plot(x2, yy8, linewidth=0.5, c='g')
                    ax8.set_xticks(xx2, xmak2)
                ax8.set_xlabel('MFC8, Acetone2')

                if self.fig[8]:
                    fl9 = self.fc9.get()
                    if tag:
                        y9.pop(0)
                        yy9.pop(0)
                    y9.append(fl9['mass_flow'])
                    yy9.append(self.f9)
                    ax9.clear()
                    ax9.plot(x2, y9, linewidth=0.5, c='k')
                    ax9.plot(x2, yy9, linewidth=0.5, c='g')
                    ax9.set_xticks(xx2, xmak2)
                ax9.set_xlabel('MFC9, Bubbler3')

                if self.fig[9]:
                    fl10 = self.fc10.get()
                    if tag:
                        y10.pop(0)
                        yy10.pop(0)
                    y10.append(fl10['mass_flow'])
                    yy10.append(self.f10)

                    ax0.clear()
                    ax0.plot(x2, y10,  linewidth=0.5, c='k')
                    ax0.plot(x2, yy10, linewidth=0.5, c='g')
                    ax0.set_xticks(xx2, xmak2)
                ax0.set_xlabel('MFC10, ZeroAir')

            if cycle:
                print('cycle')
                self.anim1 = FuncAnimation(self.figure1, animate, frames=self.gen_mfc(total, cycle), interval=ti,
                                           repeat=False)
                self.anim2 = FuncAnimation(self.figure2, animate2, frames=self.gen_mfc(total, cycle), interval=ti,
                                           repeat=False)
            else:
                print('infinity')
                self.anim1 = FuncAnimation(self.figure1, animate, frames=self.gen_mfc(total), interval=ti)
                self.anim2 = FuncAnimation(self.figure2, animate2, frames=self.gen_mfc(total),interval=ti)
            self.canvas1.draw()
            self.canvas2.draw()
        except:
            self.conn = 0
            self.lb85.setText('Error plot.')

    def func3(self):  # pause
        try:
            self.anim1.pause()
            self.anim2.pause()

            t1 = int(time.time())  #write down end time
            folder = self.e81.text()
            fn = os.path.join(folder, 'par', 't3.txt')
            if os.path.isfile(fn):
                os.remove(fn)
            t = time.strftime('%Y%m%d%H%M', time.localtime(t1))
            with open(fn, 'a') as f:
                f.write('%s\n%s\n%s' % (t[:8], t[8:10], t[10:]))

            self.lb85.setText('Experiment paused.')
            self.b1.setEnabled(True)
            self.b4.setEnabled(True)
        except:
            self.lb85.setText('Error pause experiment.')

    def func4(self):  # resume
        try:
            self.anim1.resume()
            self.anim2.resume()
            self.lb85.setText('Experiment resumed.')
            self.b1.setEnabled(False)
        except:
            self.lb85.setText('Error resume experiment.')

    def func5(self):  # zero all
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                self.fc1.set_flow_rate(0)
                self.fc2.set_flow_rate(0)
                self.fc3.set_flow_rate(0)
                self.fc4.set_flow_rate(0)
                self.fc5.set_flow_rate(0)
                self.fc6.set_flow_rate(0)
                self.fc7.set_flow_rate(0)
                self.fc8.set_flow_rate(0)
                self.fc9.set_flow_rate(0)
                self.fc10.set_flow_rate(0)

                self.e11.setText('')
                self.e12.setText('')
                self.e13.setText('')
                self.e14.setText('')
                self.e15.setText('')
                self.e16.setText('')
                self.e17.setText('')
                self.e18.setText('')
                self.e19.setText('')
                self.e10.setText('')
                self.lb0.setText('All MFCs are zero-ed.')
        except:

            self.lb0.setText('Error zero all.')

    ################### Tab4 Functions ###############
    def func200(self):
        portusb = [p.device for p in ls.comports()]
        # print(portusb)
        self.e200.setPlainText(str(portusb))

    def func201(self):  # detect analyzer IP address
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

    def func202(self):  # detect Alicat board1/sample1 port
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

            p = os.path.join('par1', 'alicat1.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(self.e202.text())

    def func203(self):  # detect Alicat sample2/board2 port
        self.lb219.setText('...')
        QApplication.processEvents()
        port_ali = self.e203.text()

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
                flow_controller1 = FlowController(port=port_ali, address='G')
                flow_controller2 = FlowController(port=port_ali, address='H')
                print(flow_controller1.get())
                print(flow_controller2.get())
            except:
                port_ali = ''

        if port_ali == '':
            self.lb219.setText('Port not found.')
        else:
            self.e203.setText(port_ali)
            self.lb219.setText('Port found.')

            p = os.path.join('par1', 'alicat2.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(self.e203.text())



    def exitFunc(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)

        if reply == QMessageBox.StandardButton.Yes:
            self.close()


def main():
    app = QApplication(sys.argv)
    window = Window()
    app.setWindowIcon(QIcon('icons/logo.png'))
    window.show()
    app.exec()


if __name__ == '__main__':
    main()

# @author: Yilin Shi   2022.4.1
# shiyilin890@gmail.com
# Bog the fat crocodile^^^^^^
