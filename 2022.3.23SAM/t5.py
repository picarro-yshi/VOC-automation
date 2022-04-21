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
rt = 2000      ## ms, Alicat label refresh time
spec_xt = 60  ## min, spectrum plot animation: x axis time window duration 400'=6h40', 500'=8h20'

cAcetone1 = 10.42    # 400 ppm
cIPA = 1.11  # 500 ppm
cPGME = 399.3  # 500 ppm

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
        self.layout1()    # title
        self.layout2()    # MFC control
        self.layout3()    # table
        self.layout4()    # bottom row
        self.layout5()    # tab 2  sample1 viewer
        self.layout6()    # tab 3  sample2 viewer
        self.layout7()    # tab 4
        self.layout8()    # tab 5

    def mainlayout(self):
        mainLayout=QVBoxLayout()
        self.tabs =QTabWidget()
        self.tab1=QWidget()
        self.tab2=QWidget()
        self.tab3=QWidget()
        self.tab4=QWidget()
        self.tab5=QWidget()
        self.tabs.addTab(self.tab1, "   ⬥ Experiment Settings   ")
        # self.tabs.addTab(self.tab2, "   ⬥ MFC View Real Time    ")
        self.tabs.addTab(self.tab2, "   ⬥ Sample 1 Real Time    ")
        self.tabs.addTab(self.tab3, "   ⬥ Sample 2 Real Time    ")
        self.tabs.addTab(self.tab4, "   ⬥ SAM Design Diagram    ")
        self.tabs.addTab(self.tab5, "     ⬥ Port Detection      ")
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)
        self.show()

        ## initialize parameters
        # self.baseline = []
        # self.view_point = 0   #total points plotted in spectrum viewer window
        # self.total_point = 0  #total points processed, for all three analyzer data source
        self.conn=0   # check if all MFCs are connected

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
    def layout1(self):     # title
        self.img = QLabel()
        self.pixmap = QPixmap('icons/picarro.png')
        self.img.setPixmap(self.pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.img2 = QLabel()
        self.pixmap = QPixmap('icons/sam2.png')
        self.img2.setPixmap(self.pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.L11.addStretch()
        self.L11.addWidget(self.img)
        self.L11.addWidget(self.img2)
        self.L11.addStretch()


    def layout2(self):     # MFC control
        self.box12 = QGroupBox()
        self.box12.setStyleSheet(style.box12())

        self.lb21 = QLabel('  MFC#  ')
        self.lb22 = QLabel('  Flow  ')
        self.lb23 = QLabel('Conc.ppm')
        self.lb24 = QLabel('  Set   ')
        self.lb25 = QLabel('  Max.  ')

        self.lb31 = QLabel('1-ZAG')
        self.lb32 = QLabel('2-Act')
        self.lb33 = QLabel('3-IPA')
        self.lb34 = QLabel('4-PGME')
        self.lb35 = QLabel('5-ZA')
        self.lb36 = QLabel('6-Bubbler1')
        self.lb37 = QLabel('7-Bubbler2')
        self.lb38 = QLabel('8-Act')
        self.lb39 = QLabel('9-ZA')
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

        self.lb41 = QLabel('  ')  #real time label
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
        self.lb61.setStyleSheet("background-color: honeydew")
        self.lb62.setStyleSheet("background-color: honeydew")
        self.lb63.setStyleSheet("background-color: honeydew")
        self.lb64.setStyleSheet("background-color: honeydew")

        self.g1 = QGridLayout()
        self.g1.addWidget(self.lb21,  0, 0)
        self.g1.addWidget(self.lb22,  1, 0)
        self.g1.addWidget(self.lb23,  2, 0)
        self.g1.addWidget(self.lb24,  3, 0)
        self.g1.addWidget(self.lb25,  4, 0)

        self.g1.addWidget(self.lb31,  0, 1)
        self.g1.addWidget(self.lb32,  0, 2)
        self.g1.addWidget(self.lb33,  0, 3)
        self.g1.addWidget(self.lb34,  0, 4)
        self.g1.addWidget(self.lb35,  0, 5)
        self.g1.addWidget(self.lb36,  0, 6)
        self.g1.addWidget(self.lb37,  0, 7)
        self.g1.addWidget(self.lb38,  0, 8)
        self.g1.addWidget(self.lb39,  0, 9)
        self.g1.addWidget(self.lb30,  0, 10)

        self.g1.addWidget(self.lb41,  1, 1)
        self.g1.addWidget(self.lb42,  1, 2)
        self.g1.addWidget(self.lb43,  1, 3)
        self.g1.addWidget(self.lb44,  1, 4)
        self.g1.addWidget(self.lb45,  1, 5)
        self.g1.addWidget(self.lb46,  1, 6)
        self.g1.addWidget(self.lb47,  1, 7)
        self.g1.addWidget(self.lb48,  1, 8)
        self.g1.addWidget(self.lb49,  1, 9)
        self.g1.addWidget(self.lb40,  1, 10)

        self.g1.addWidget(self.lb61,  2, 2)
        self.g1.addWidget(self.lb62,  2, 3)
        self.g1.addWidget(self.lb63,  2, 4)
        self.g1.addWidget(self.lb64,  2, 8)

        self.g1.addWidget(self.e11,   3, 1)
        self.g1.addWidget(self.e12,   3, 2)
        self.g1.addWidget(self.e13,   3, 3)
        self.g1.addWidget(self.e14,   3, 4)
        self.g1.addWidget(self.e15,   3, 5)
        self.g1.addWidget(self.e16,   3, 6)
        self.g1.addWidget(self.e17,   3, 7)
        self.g1.addWidget(self.e18,   3, 8)
        self.g1.addWidget(self.e19,   3, 9)
        self.g1.addWidget(self.e10,   3, 10)

        self.g1.addWidget(self.lb51,  4, 1)
        self.g1.addWidget(self.lb52,  4, 2)
        self.g1.addWidget(self.lb53,  4, 3)
        self.g1.addWidget(self.lb54,  4, 4)
        self.g1.addWidget(self.lb55,  4, 5)
        self.g1.addWidget(self.lb56,  4, 6)
        self.g1.addWidget(self.lb57,  4, 7)
        self.g1.addWidget(self.lb58,  4, 8)
        self.g1.addWidget(self.lb59,  4, 9)
        self.g1.addWidget(self.lb50,  4, 10)

        self.g1.addWidget(self.b11,   5, 1)
        self.g1.addWidget(self.b12,   5, 2)
        self.g1.addWidget(self.b13,   5, 3)
        self.g1.addWidget(self.b14,   5, 4)
        self.g1.addWidget(self.b15,   5, 5)
        self.g1.addWidget(self.b16,   5, 6)
        self.g1.addWidget(self.b17,   5, 7)
        self.g1.addWidget(self.b18,   5, 8)
        self.g1.addWidget(self.b19,   5, 9)
        self.g1.addWidget(self.b10,   5, 10)

        self.L15 = QVBoxLayout()
        self.L15.addLayout(self.g1)
        self.box12.setLayout(self.L15)
        self.L12.addWidget(self.box12)

        ## refresh Alicat label
        self.timer = QTimer()
        self.timer.setInterval(rt)
        self.timer.timeout.connect(self.refresh_label)


    def layout3(self):     # table
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

        self.tableWidget.setHorizontalHeaderLabels(["Time(s)", "MFC1", "MFC2", "MFC3", "MFC4","MFC5",
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

    def layout4(self):   # bottom row
        self.lb81 = QLabel('Folder')
        self.lb82 = QLabel('File (csv)')
        self.lb83 = QLabel('Cycle')
        self.e81 = QLineEdit() # Folder'R:\crd_G9000\AVXxx\\3610-NUV1022\R&D\Calibration\Yilin Shi')
        try:
            f = open(os.path.join('par1', 'r_drive.txt'), 'r')
            temp = f.read()
            self.e81.setText(temp)
        except:
            print('error loading folder name.')

        self.e82 = QLineEdit()   #csv file name 'sam1'
        try:
            f = open(os.path.join('par1', 'filename.txt'), 'r')
            temp = f.read()
            self.e82.setText(temp)
        except:
            print('error loading file name.')

        self.e83 = QLineEdit('1')  # cycle
        self.e83.setToolTip('Number of cycles of above time series.\n'
                            'Positive integers only.\n'
                            'Type in 0 for infinity loop.')

        self.lb0 = QLabel('     ')  #for hint
        self.lb0.setStyleSheet("background-color: lightgrey")
        self.lb84 = QLabel('    ')
        self.lb85 = QLabel('    ')
        self.lb89 = QLabel('     ')

        self.b8 = QPushButton("Change")
        self.b8.clicked.connect(self.cycletime)
        self.b8.setEnabled(False)

        self.g3 = QGridLayout()
        self.g3.addWidget(self.lb81,  0, 0, 1, 1)
        self.g3.addWidget(self.e81,   0, 1, 1, 5)
        self.g3.addWidget(self.lb89,  0, 6, 1, 1)
        self.g3.addWidget(self.lb82,  1, 0, 1, 1)
        self.g3.addWidget(self.e82,   1, 1, 1, 1)
        self.g3.addWidget(self.lb84,  1, 2, 1, 1)
        self.g3.addWidget(self.lb83,  1, 3, 1, 1)
        self.g3.addWidget(self.e83,   1, 4, 1, 1)
        self.g3.addWidget(self.b8,    1, 5, 1, 1)
        self.g3.addWidget(self.lb0,   2, 0, 1, 2)
        self.g3.addWidget(self.lb85,  2, 4, 1, 2)


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

        self.lb91 = QLabel('  ')  #gap
        self.lb92 = QLabel('  ')  #gap
        self.lb93 = QLabel('  ')  #gap
        self.lb94 = QLabel('  ')  #gap
        self.lb95 = QLabel('  ')  #gap

        self.g4 = QGridLayout()
        self.g4.addWidget(self.b1,   0, 0)
        self.g4.addWidget(self.lb1,  1, 0)
        self.g4.addWidget(self.lb91, 1, 1)

        self.g4.addWidget(self.b2,   0, 2)
        self.g4.addWidget(self.lb2,  1, 2)
        self.g4.addWidget(self.lb92, 1, 3)

        self.g4.addWidget(self.b3,   0, 4)
        self.g4.addWidget(self.lb3,  1, 4)
        self.g4.addWidget(self.lb93, 1, 5)

        self.g4.addWidget(self.b4,   0, 6)
        self.g4.addWidget(self.lb4,  1, 6)
        self.g4.addWidget(self.lb94, 1, 7)

        self.g4.addWidget(self.b5,   0, 8)
        self.g4.addWidget(self.lb5,  1, 8)
        self.g4.addWidget(self.lb95, 1, 9)

        self.g4.addWidget(self.b9,   0, 10)
        self.g4.addWidget(self.lb9,  1, 10)

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
        self.lb300.setPixmap(self.pixmap.scaled(900, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
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

        self.lb214 = QLabel("Alicat:")
        self.lb215 = QLabel("Serial Port:")
        self.e202 = QLineEdit()  # '/dev/cu.usbserial-A908UXOQ' '/dev/tty.usbserial-A908UXOQ'
        self.lb216 = QLabel(" ")  ## port not found
        self.b202 = QPushButton("Detect", self)
        self.b202.clicked.connect(self.func202)
        self.b202.setStyleSheet("font: bold")
        self.b202.setToolTip("Detect the name of the port connected to Alicat.")

        self.lb298 = QLabel('    ')
        self.lb299 = QLabel('Yilin Shi | Version 1.0 | Spring 2022 | Santa Clara, CA    ')
        self.lb299.setFont(QFont('Arial', 10))
        self.lb299.setAlignment(Qt.AlignmentFlag.AlignRight)

        try:
            f = open('par1/analyzer.txt', "r")
            temp = f.read()  # .splitlines()
            self.e201.setText(temp)  # analyzer
            f = open('par1/alicat.txt', "r")
            temp = f.read()
            self.e202.setText(temp)  # alicat
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

        self.g21.addWidget(self.lb214, 9, 0)
        self.g21.addWidget(self.lb215,10, 0)
        self.g21.addWidget(self.e202, 10, 1)
        self.g21.addWidget(self.b202, 10, 2)
        self.g21.addWidget(self.lb216,11, 1)

        self.g21.addWidget(self.lb298,12, 1)
        self.g21.addWidget(self.lb299,13, 1, 1, 3)

        self.L501.addLayout(self.g21)
        self.L501.addStretch()  # *** will tight the space

    ##################################################
    ################### Functions  ###################
    ##################################################
    def mfcs(self):   # check all MFCs connection
        try:
            port_ali = self.e202.text()
            self.fc1 = FlowController(port=port_ali, address='A')
            self.fc2 = FlowController(port=port_ali, address='B')
            self.fc3 = FlowController(port=port_ali, address='C')
            self.fc4 = FlowController(port=port_ali, address='D')
            self.fc5 = FlowController(port=port_ali, address='E')
            self.fc6 = FlowController(port=port_ali, address='F')
            self.fc7 = FlowController(port=port_ali, address='G')
            self.fc8 = FlowController(port=port_ali, address='H')
            self.fc9 = FlowController(port=port_ali, address='I')
            self.fc10 = FlowController(port=port_ali, address='J')
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.fc9.set_flow_rate(float(b))
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
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
                    self.lb0.setText('MFC%s set to %s %s.'%(a, b, c[-4:]))
        except:
            self.lb0.setText('Please enter a number.')


    ########### last block   ###########
    def cycletime(self):
        try:
            folder = self.e81.text()
            fname = self.e82.text()
            fn = os.path.join(folder, fname + '.csv')
            cycle = int(self.e83.text())
            df = pd.read_csv(fn)
            tc = df.iloc[:, 0]  # first column is time, s
            tcyc = sum(list(tc))

            if cycle<0:
                self.lb85.setText('Please put in an integer >=0.')
            elif cycle:
                total_time = tcyc*cycle
                if total_time < 60:
                    total = str(total_time) + ' s'
                elif total_time < 3600:
                    total = str(round(total_time/60, 1)) + ' min'
                elif total_time < 86400:
                    total = str(round(total_time/3600, 1)) + ' h'
                else:
                    total = str(round(total_time/86400, 1)) + ' d'
                self.lb85.setText('%s s/cycle, total time: %s' % (tcyc, total))
            else:
                self.lb85.setText('Infinity loop, %s s/cycle.'% (tcyc))
            return 1
        except:
            self.lb85.setText('Please enter an integer >=0.')
            return 0


    def func1(self):     # load csv
        folder = self.e81.text()
        fname = self.e82.text()
        fn = os.path.join(folder, fname+'.csv')
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

                self.lb0.setText('%s.csv file loaded'%(fname))
                self.b2.setEnabled(True)
                self.b3.setEnabled(False)
                self.b4.setEnabled(False)
                self.b8.setEnabled(True)
            except:
                self.lb0.setText('Error loading %s.csv file.'%(fname))


    def refresh_label(self):
        try:
            host = self.e201.text()
            # port_ali = self.e202.text()
            ipadd = 'http://' + host

            fl1 = self.fc1.get()['mass_flow']
            fl2 = self.fc2.get()['mass_flow']
            fl3 = self.fc3.get()['mass_flow']
            fl4 = self.fc4.get()['mass_flow']
            fl5 = self.fc5.get()['mass_flow']

            MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection", IsDontCareConnection=False)
            MeasSystem.Backdoor.SetData('MFC1_flow', fl1)
            MeasSystem.Backdoor.SetData('MFC2_flow', fl2)
            MeasSystem.Backdoor.SetData('MFC3_flow', fl3)
            MeasSystem.Backdoor.SetData('MFC4_flow', fl4)
            MeasSystem.Backdoor.SetData('MFC5_flow', fl5)
            self.lb41.setText(str(fl1))
            self.lb42.setText(str(fl2))
            self.lb43.setText(str(fl3))
            self.lb44.setText(str(fl4))
            self.lb45.setText(str(fl5))

            # concentration labels
            con1 = round(float(fl2)/1000/float(fl1) * cAcetone1, 4)
            con2 = round(float(fl3)/1000/float(fl1) * cIPA, 4)
            con3 = round(float(fl4)/1000/float(fl1) * cPGME, 4)
            # con4 = round(float(fl2)/float(fl7)*1000, 4)
            self.lb61.setText(str(con1))    # 2 Acetone
            self.lb62.setText(str(con2))    # 3 IPA
            self.lb63.setText(str(con3))    # 4 PGME
            # self.lb64.setText(str(con4))    # 8 Acetone
        except:
            self.lb0.setText('Error refresh Alicat readings.')


    def func2(self):     # start run csv data, refresh label, plot
        try:
            self.canvas1.close_event()
            self.figure1.clear()
            # self.canvas2.close_event()
            # self.figure2.clear()

            if self.cycletime():
                if not self.conn:
                    self.mfcs()
                if self.conn:
                    self.timer.start()  # refresh label
                    self.plot1()
                    self.b1.setEnabled(False)
                    self.b3.setEnabled(True)
                    self.b4.setEnabled(False)
                    self.lb0.setText('Experiment started.')
        except:
            self.lb0.setText('Error run experiment.')


    def gen_mfc(self, total, cycle=0):
        if cycle:
            for j in range(cycle):
                for i in range(total):
                    # print(i)
                    yield i

            self.timer.stop()  # track baseline
            self.lb0.setText('Experiment finished.')
            self.b1.setEnabled(True)
            self.b2.setEnabled(True)
            self.b3.setEnabled(False)
            self.b4.setEnabled(False)
        else:
            for i in range(total):
                yield i


    def plot1(self):     # start run csv data
        try:
            folder = self.e81.text()
            fname = self.e82.text()
            fn = os.path.join(folder, fname + '.csv')
            df = pd.read_csv(fn)
            tc = df.iloc[:, 0]    # first column is time, s
            nr = df.shape[0]      # row number
            nc = df.shape[1]      # column number
            cycle = int(self.e83.text())

            tc = list(tc)
            t_start = []   # s, start row
            t_end = []     # s, end row
            sum = 0
            for t in tc:
                t_start.append(sum)
                sum += t
                t_end.append(sum-1)
            total = sum
            print(total)
            self.ct = 1     # cycle counter

            x = []     ## epoch time 1641259801
            xx = []    ## epoch time, x labels that will be marked
            xmak = []  ## clock time x label

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

            ax1 = self.figure1.add_subplot(321) # 221
            ax2 = self.figure1.add_subplot(322)
            ax3 = self.figure1.add_subplot(323)
            ax4 = self.figure1.add_subplot(324)
            ax5 = self.figure1.add_subplot(325)

            box = ax2.get_position()    # Shrink current axis's height by 10% on the bottom
            ax2.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax3.get_position()
            ax3.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax4.get_position()
            ax4.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

            box = ax1.get_position()
            ax1.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])
            box = ax5.get_position()
            ax5.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

            t1 = time.strftime("%Y%m%d")   # current time
            self.figure1.text(0.4, 0.04,'Clock Time (Y-M-D), %s-%s-%s'%(t1[:4], t1[4:6], t1[-2:]))
            self.figure1.text(0.72, 0.04,  '---- Set', color='g')
            self.figure1.text(0.8, 0.04, '---- Measured', color='k')

            # self.figure2.text(0.4, 0.04,'Clock Time (Y-M-D), %s-%s-%s'%(t1[:4], t1[4:6], t1[-2:]))
            # self.figure2.text(0.72, 0.04,  '---- Set', color='g')
            # self.figure2.text(0.8, 0.04, '---- Measured', color='k')

            self.view_point = int(spec_xt * 60)   # 1 pt/s, total pt displayed in window
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
            yy0 = []

            #current target value
            self.f1 = 0
            self.f2 = 0
            self.f3 = 0
            self.f4 = 0
            self.f5 = 0
            self.f6 = 0
            self.f7 = 0
            self.f8 = 0
            self.f9 = 0
            self.f0 = 0

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

                if i in t_start:  #start a row
                    idx = t_start.index(i)
                    print(idx)
                    row = list(df.iloc[idx])
                    self.f1 = row[1]
                    self.f2 = row[2]
                    self.f3 = row[3]
                    self.f4 = row[4]
                    self.f5 = row[5]

                    self.fc1.set_flow_rate(self.f1)
                    self.fc2.set_flow_rate(self.f2)# / 50)
                    self.fc3.set_flow_rate(self.f3)
                    self.fc4.set_flow_rate(self.f4)  #/ 50)
                    self.fc5.set_flow_rate(self.f5)
                    # self.fc6.set_flow_rate(row[6])
                    # self.fc7.set_flow_rate(row[7])
                    # self.fc8.set_flow_rate(row[8])
                    # self.fc9.set_flow_rate(row[9])
                    # self.fc10.set_flow_rate(row[10])

                    self.tableWidget.item(idx, 0).setBackground(QColor(115, 130, 95))  #green grey
                    for j in range(1, nc):
                        self.tableWidget.item(idx, j).setBackground(QColor(151, 186, 102))  #green
                    QApplication.processEvents()  #must present to show the effect

                    itemMeasVal = self.tableWidget.item(idx, 0)       ## set to visible in window
                    self.tableWidget.setItem(idx, 0, itemMeasVal)
                    # self.tableWidget.scrollToItem(itemMeasVal,QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible)
                    self.tableWidget.scrollToItem(itemMeasVal,QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)
                    # This is for the bar to scroll automatically and then the current item added is always visible

                fl1 = self.fc1.get()
                fl2 = self.fc2.get()
                fl3 = self.fc3.get()
                fl4 = self.fc4.get()
                fl5 = self.fc5.get()
                # fl6 = self.fc6.get()
                # fl7 = self.fc7.get()
                # fl8 = self.fc8.get()
                # fl9 = self.fc9.get()
                # fl10 = self.fc10.get()

                if len(x) == self.view_point:  ## x-axis number
                    x.pop(0)
                    y1.pop(0)
                    y2.pop(0)
                    y3.pop(0)
                    y4.pop(0)
                    y5.pop(0)
                    # y6.pop(0)
                    # y7.pop(0)
                    # y8.pop(0)
                    # y9.pop(0)
                    # y10.pop(0)

                    yy1.pop(0)
                    yy2.pop(0)
                    yy3.pop(0)
                    yy4.pop(0)
                    yy5.pop(0)
                    # yy6.pop(0)
                    # yy7.pop(0)
                    # yy8.pop(0)
                    # yy9.pop(0)
                    # yy0.pop(0)

                t = int(time.time())   #epoch time
                x.append(t)   #i

                y1.append(fl1['mass_flow'])
                y2.append(fl2['mass_flow'])
                y3.append(fl3['mass_flow'])
                y4.append(fl4['mass_flow'])
                y5.append(fl5['mass_flow'])
                # y6.append(fl6['mass_flow'])
                # y7.append(fl7['mass_flow'])
                # y8.append(fl8['mass_flow'])
                # y9.append(fl9['mass_flow'])
                # y10.append(fl10['mass_flow'])

                yy1.append(self.f1)
                yy2.append(self.f2)
                yy3.append(self.f3)
                yy4.append(self.f4)
                yy5.append(self.f5)
                # yy6.append(self.f6)
                # yy7.append(self.f7)
                # yy8.append(self.f8)
                # yy9.append(self.f9)
                # yy0.append(self.f0)

                ## create labels
                clock = time.strftime('%H:%M', time.localtime(t))
                if len(xx):
                    clock0 = time.strftime('%H:%M', time.localtime(x[-2])) # previous time string
                    if ((clock0[-2:] == '59' and clock[-2:] == '00') or
                            (clock0[-2:] == '14' and clock[-2:] == '15') or
                            (clock0[-2:] == '44' and clock[-2:] == '45') or
                            (clock0[-2:] == '29' and clock[-2:] == '30')):
                        xx.append(t)
                        xmak.append(clock)
                else:   # no label yet, add current as first
                    xx.append(t)
                    xmak.append(clock)

                if (len(xx) > 0) and (xx[0] < x[0]):
                    xx.pop(0)
                    xmak.pop(0)

                ax1.clear()
                ax2.clear()
                ax3.clear()
                ax4.clear()
                ax5.clear()

                ax1.plot(x, y1,  linewidth=0.5, c='k')  # measured
                ax1.plot(x, yy1, linewidth=0.5, c='g')  # target
                ax2.plot(x, y2,  linewidth=0.5, c='k')
                ax2.plot(x, yy2, linewidth=0.5, c='g')
                ax3.plot(x, y3,  linewidth=0.5, c='k')
                ax3.plot(x, yy3, linewidth=0.5, c='g')
                ax4.plot(x, y4,  linewidth=0.5, c='k')
                ax4.plot(x, yy4, linewidth=0.5, c='g')
                ax5.plot(x, y5,  linewidth=0.5, c='k')
                ax5.plot(x, yy5, linewidth=0.5, c='g')

                # ax2.plot(x, y4, linewidth=0.5, label='MFC4 (50SCCM)')
                # ax1.plot(x, y5, linewidth=0.5, label='MFC5 (10SCCM)')
                # ax1.plot(x, y6, linewidth=0.5, label='MFC6 (10SCCM)')
                # ax1.plot(x, y7, linewidth=0.5, label='MFC7 (10SLPM)')
                # ax2.plot(x, y8, linewidth=0.5, label='MFC8 (50SCCM)')
                # ax1.plot(x, y9, linewidth=0.5, label='MFC9 (10SCCM)')
                # ax2.plot(x, y10, linewidth=0.5,label='MFC10(200SCCM)')
                ## ax1.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))  ## has to be inside
                ## ax2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.2e'))  ## has to be inside

                ax1.set_xticks(xx, xmak)
                ax2.set_xticks(xx, xmak)
                ax3.set_xticks(xx, xmak)
                ax4.set_xticks(xx, xmak)
                ax5.set_xticks(xx, xmak)

                ax1.set_xlabel('MFC1, ZAG')
                ax2.set_xlabel('MFC2, Acetone')
                ax3.set_xlabel('MFC3, IPA')
                ax4.set_xlabel('MFC4, PGME')
                ax5.set_xlabel('MFC5, Bubbler1')

                # t1 = time.strftime("%Y%m%d")   # current time
                # ax1.set_xlabel('Clock Time (Y-M-D), %s-%s-%s'%(t1[:4], t1[4:6], t1[-2:]), fontsize=11)
                # ax1.set_ylabel('MFC (up to 10)', fontsize=11)
                # ax2.set_ylabel('MFC (up to 200)', fontsize=11)
                # # Put a legend below current axis
                # ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.1),fancybox=True, shadow=True, ncol=5)
                # ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),fancybox=True, shadow=True, ncol=5)

                if i in t_end:  #end a row
                    idx = t_end.index(i)
                    self.tableWidget.item(idx, 0).setBackground(QColor(170, 170, 170))  # deep gray
                    for j in range(1, nc):
                        self.tableWidget.item(idx, j).setBackground(QColor(230, 230, 230))  # light gray
                    QApplication.processEvents()  # must present to show the effect

                if (i+1) % total == 0:
                    self.lb0.setText('cycle %s done.' % self.ct)
                    self.ct += 1

            if cycle:
                print('cycle')
                self.anim1 = FuncAnimation(self.figure1, animate, frames=self.gen_mfc(total, cycle), interval=1000, repeat=False)
                # self.anim2 = FuncAnimation(self.figure2, animate, frames=self.gen_mfc(total, cycle), interval=1000, repeat=False)
            else:
                print('infinity')
                self.anim1 = FuncAnimation(self.figure1, animate, frames=self.gen_mfc(total), interval=1000) #, repeat=False)
            self.canvas1.draw()

        except:
            self.lb0.setText('Error plot.')


    def func3(self):     # pause
        try:
            self.anim1.pause()
            self.lb0.setText('Experiment paused.')
            self.b1.setEnabled(True)
            self.b4.setEnabled(True)
        except:
            self.lb0.setText('Error pause experiment.')


    def func4(self):    # resume
        try:
            self.anim1.resume()
            self.lb0.setText('Experiment resumed.')
            self.b1.setEnabled(False)
        except:
            self.lb0.setText('Error resume experiment.')

    def func5(self):     # zero all
        try:
            if not self.conn:
                self.mfcs()
            if self.conn:
                self.fc1.set_flow_rate(0)
                self.fc2.set_flow_rate(0)
                self.fc3.set_flow_rate(0)
                self.fc4.set_flow_rate(0)
                self.fc5.set_flow_rate(0)
                # self.fc6.set_flow_rate(0)
                # self.fc7.set_flow_rate(0)
                # self.fc8.set_flow_rate(0)
                # self.fc9.set_flow_rate(0)
                # self.fc10.set_flow_rate(0)

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



    def exitFunc(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit?", QMessageBox.StandardButton.Yes |
                                     QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)

        if reply == QMessageBox.StandardButton.Yes:
            self.close()

def main():
    app=QApplication(sys.argv)
    window = Window()
    app.setWindowIcon(QIcon('icons/logo.png'))
    window.show()
    app.exec()

if __name__=='__main__':
    main()



# @author: Yilin Shi   2022.4.1
# shiyilin890@gmail.com
# Bog the fat crocodile^^^^^^



