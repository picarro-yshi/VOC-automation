## Master Flow Control for 10 MFCs
## send MFC value to analyzer

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
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib
matplotlib.use('ps')

## Qt GUI
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor
from PyQt6.QtCore import *
from PyQt6 import QtWidgets, QtGui

## Customized file/libraries
import style
from alicat import FlowController  # no need pip install alicat
import CmdFIFO_py3 as CmdFIFO

## hard-coded global parameters
port_in = 50070   ## backdoor, send data to fitter on analyzer
port_out = 40060  ## listener, get data from analyzer
tr = 2000         ## ms, Alicat label refresh time
spec_xt = 60      ## min, spectrum plot animation x axis time window duration 400'=6h40', 500'=8h20'
ti = 1000         ## 1s animation time interval
maxflow = ['10 SLPM', '100 SCCM', '50 SCCM', '10 SCCM', '1 SLPM',
           '100 SCCM', '1 SLPM', '1 SLPM', '10 SLPM', '100 SCCM']
# port_ali = 'COM7'  ## '/dev/tty.usbserial-A908UXOQ'


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Picarro - M F C")
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
        self.conn = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]   #list of available MFC number
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
        self.pixmap = QPixmap('icons/mfc.png')
        self.img2.setPixmap(
            self.pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img2.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.L11.addStretch()
        self.L11.addWidget(self.img)
        self.L11.addWidget(self.img2)
        self.L11.addStretch()

    # def redbox(self, e):
    #     e.setStyleSheet('border: 2px solid red')  #set entry box border red
    #
    # def greybox(self, e):
    #     e.setStyleSheet('border: 1px solid grey')  #restore to grey


    def layout2(self):  # MFC control
        self.box12 = QGroupBox()
        self.box12.setStyleSheet(style.box12())

        self.l11 = QLabel('  MFC#  ')
        self.l11.setToolTip('Check the box if this MFC is available.')
        self.l12 = QLabel('Real Time')
        self.l13 = QLabel(' Target ')
        self.l14 = QLabel('  ')   #set buttons
        self.l15 = QLabel('Max. Flow')
        self.l16 = QLabel('  Notes  ')

        self.l21 = QCheckBox("    1  ")
        # self.l21.setChecked(True)
        # self.l21.stateChanged.connect(self.func21)
        self.l22 = QCheckBox("    2  ")
        self.l23 = QCheckBox("    3  ")
        self.l24 = QCheckBox("    4  ")
        self.l25 = QCheckBox("    5  ")
        self.l26 = QCheckBox("    6  ")
        self.l27 = QCheckBox("    7  ")
        self.l28 = QCheckBox("    8  ")
        self.l29 = QCheckBox("    9  ")
        self.l20 = QCheckBox("   10  ")

        self.l31 = QLabel('  ')  # real time label
        self.l32 = QLabel('  ')
        self.l33 = QLabel('  ')
        self.l34 = QLabel('  ')
        self.l35 = QLabel('  ')
        self.l36 = QLabel('  ')
        self.l37 = QLabel('  ')
        self.l38 = QLabel('  ')
        self.l39 = QLabel('  ')
        self.l30 = QLabel('  ')

        self.l31.setStyleSheet("background-color: lightgrey")
        self.l32.setStyleSheet("background-color: lightgrey")
        self.l33.setStyleSheet("background-color: lightgrey")
        self.l34.setStyleSheet("background-color: lightgrey")
        self.l35.setStyleSheet("background-color: lightgrey")
        self.l36.setStyleSheet("background-color: lightgrey")
        self.l37.setStyleSheet("background-color: lightgrey")
        self.l38.setStyleSheet("background-color: lightgrey")
        self.l39.setStyleSheet("background-color: lightgrey")
        self.l30.setStyleSheet("background-color: lightgrey")

        self.e11 = QLineEdit('')  # target MFC values
        self.e12 = QLineEdit('')
        self.e13 = QLineEdit('')
        self.e14 = QLineEdit('')
        self.e15 = QLineEdit('')
        self.e16 = QLineEdit('')
        self.e17 = QLineEdit('')
        self.e18 = QLineEdit('')
        self.e19 = QLineEdit('')
        self.e10 = QLineEdit('')

        self.b11 = QPushButton("Set")
        self.b12 = QPushButton("Set")
        self.b13 = QPushButton("Set")
        self.b14 = QPushButton("Set")
        self.b15 = QPushButton("Set")
        self.b16 = QPushButton("Set")
        self.b17 = QPushButton("Set")
        self.b18 = QPushButton("Set")
        self.b19 = QPushButton("Set")
        self.b10 = QPushButton("Set")

        self.b11.setEnabled(False)
        self.b12.setEnabled(False)
        self.b13.setEnabled(False)
        self.b14.setEnabled(False)
        self.b15.setEnabled(False)
        self.b16.setEnabled(False)
        self.b17.setEnabled(False)
        self.b18.setEnabled(False)
        self.b19.setEnabled(False)
        self.b10.setEnabled(False)

        self.l21.stateChanged.connect(lambda: self.func01(self.l21, self.b11))  # (checkbox, button)
        self.l22.stateChanged.connect(lambda: self.func01(self.l22, self.b12))
        self.l23.stateChanged.connect(lambda: self.func01(self.l23, self.b13))
        self.l24.stateChanged.connect(lambda: self.func01(self.l24, self.b14))
        self.l25.stateChanged.connect(lambda: self.func01(self.l25, self.b15))
        self.l26.stateChanged.connect(lambda: self.func01(self.l26, self.b16))
        self.l27.stateChanged.connect(lambda: self.func01(self.l27, self.b17))
        self.l28.stateChanged.connect(lambda: self.func01(self.l28, self.b18))
        self.l29.stateChanged.connect(lambda: self.func01(self.l29, self.b19))
        self.l20.stateChanged.connect(lambda: self.func01(self.l20, self.b10))


        self.l41 = QLabel(maxflow[0])
        self.l42 = QLabel(maxflow[1])
        self.l43 = QLabel(maxflow[2])
        self.l44 = QLabel(maxflow[3])
        self.l45 = QLabel(maxflow[4])
        self.l46 = QLabel(maxflow[5])
        self.l47 = QLabel(maxflow[6])
        self.l48 = QLabel(maxflow[7])
        self.l49 = QLabel(maxflow[8])
        self.l40 = QLabel(maxflow[9])

        self.l41.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l42.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l43.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l44.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l45.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l46.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l47.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l48.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l49.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.l40.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.e21 = QLineEdit('')  # notes
        self.e22 = QLineEdit('')
        self.e23 = QLineEdit('')
        self.e24 = QLineEdit('')
        self.e25 = QLineEdit('')
        self.e26 = QLineEdit('')
        self.e27 = QLineEdit('')
        self.e28 = QLineEdit('')
        self.e29 = QLineEdit('')
        self.e20 = QLineEdit('')

        self.l51 = QLabel('  P (psi)')
        self.l52 = QLabel('   ')    #real time display
        self.l52.setStyleSheet("background-color: lightgrey")
        self.l53 = QLabel('  T (°C)')
        self.l54 = QLabel('   ')    #real time display
        self.l54.setStyleSheet("background-color: lightgrey")

        self.g1 = QGridLayout()
        self.g1.addWidget(self.l11, 0, 0)
        self.g1.addWidget(self.l12, 1, 0)
        self.g1.addWidget(self.l13, 2, 0)
        self.g1.addWidget(self.l14, 3, 0)
        self.g1.addWidget(self.l15, 4, 0)
        self.g1.addWidget(self.l16, 5, 0)

        self.g1.addWidget(self.l21, 0, 1)
        self.g1.addWidget(self.l22, 0, 2)
        self.g1.addWidget(self.l23, 0, 3)
        self.g1.addWidget(self.l24, 0, 4)
        self.g1.addWidget(self.l25, 0, 5)
        self.g1.addWidget(self.l26, 0, 6)
        self.g1.addWidget(self.l27, 0, 7)
        self.g1.addWidget(self.l28, 0, 8)
        self.g1.addWidget(self.l29, 0, 9)
        self.g1.addWidget(self.l20, 0, 10)

        self.g1.addWidget(self.l31, 1, 1)
        self.g1.addWidget(self.l32, 1, 2)
        self.g1.addWidget(self.l33, 1, 3)
        self.g1.addWidget(self.l34, 1, 4)
        self.g1.addWidget(self.l35, 1, 5)
        self.g1.addWidget(self.l36, 1, 6)
        self.g1.addWidget(self.l37, 1, 7)
        self.g1.addWidget(self.l38, 1, 8)
        self.g1.addWidget(self.l39, 1, 9)
        self.g1.addWidget(self.l30, 1, 10)

        self.g1.addWidget(self.e11, 2, 1)
        self.g1.addWidget(self.e12, 2, 2)
        self.g1.addWidget(self.e13, 2, 3)
        self.g1.addWidget(self.e14, 2, 4)
        self.g1.addWidget(self.e15, 2, 5)
        self.g1.addWidget(self.e16, 2, 6)
        self.g1.addWidget(self.e17, 2, 7)
        self.g1.addWidget(self.e18, 2, 8)
        self.g1.addWidget(self.e19, 2, 9)
        self.g1.addWidget(self.e10, 2, 10)

        self.g1.addWidget(self.b11, 3, 1)
        self.g1.addWidget(self.b12, 3, 2)
        self.g1.addWidget(self.b13, 3, 3)
        self.g1.addWidget(self.b14, 3, 4)
        self.g1.addWidget(self.b15, 3, 5)
        self.g1.addWidget(self.b16, 3, 6)
        self.g1.addWidget(self.b17, 3, 7)
        self.g1.addWidget(self.b18, 3, 8)
        self.g1.addWidget(self.b19, 3, 9)
        self.g1.addWidget(self.b10, 3, 10)

        self.g1.addWidget(self.l41, 4, 1)
        self.g1.addWidget(self.l42, 4, 2)
        self.g1.addWidget(self.l43, 4, 3)
        self.g1.addWidget(self.l44, 4, 4)
        self.g1.addWidget(self.l45, 4, 5)
        self.g1.addWidget(self.l46, 4, 6)
        self.g1.addWidget(self.l47, 4, 7)
        self.g1.addWidget(self.l48, 4, 8)
        self.g1.addWidget(self.l49, 4, 9)
        self.g1.addWidget(self.l40, 4, 10)

        self.g1.addWidget(self.e21, 5, 1)
        self.g1.addWidget(self.e22, 5, 2)
        self.g1.addWidget(self.e23, 5, 3)
        self.g1.addWidget(self.e24, 5, 4)
        self.g1.addWidget(self.e25, 5, 5)
        self.g1.addWidget(self.e26, 5, 6)
        self.g1.addWidget(self.e27, 5, 7)
        self.g1.addWidget(self.e28, 5, 8)
        self.g1.addWidget(self.e29, 5, 9)
        self.g1.addWidget(self.e20, 5, 10)

        self.g1.addWidget(self.l51, 6, 0)
        self.g1.addWidget(self.l52, 6, 1)
        self.g1.addWidget(self.l53, 6, 2)
        self.g1.addWidget(self.l54, 6, 3)

        self.L15 = QVBoxLayout()
        self.L15.addLayout(self.g1)
        self.box12.setLayout(self.L15)
        self.L12.addWidget(self.box12)

        ## refresh Alicat label
        self.timer = QTimer()
        self.timer.setInterval(tr)
        self.timer.timeout.connect(self.refresh_label)


    def layout3(self):  # table
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(11)
        # self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem("Time"))
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

        self.tableWidget.setHorizontalHeaderLabels(["Time", "MFC1", "MFC2", "MFC3", "MFC4", "MFC5",
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
        self.l81 = QLabel('Folder')
        self.e81 = QLineEdit()  # Folder'R:\crd_G9000\AVXxx\\3610-NUV1022\R&D\Calibration\Yilin Shi')
        try:
            f = open(os.path.join('par1', 'r_drive.txt'), 'r')
            temp = f.read()
            self.e81.setText(temp)
        except:
            print('error loading folder name.')

        self.l82 = QLabel('File (csv)')
        self.e82 = QLineEdit('   ')  # csv file name 'sam1'
        try:
            f = open(os.path.join('par1', 'filename.txt'), 'r')
            temp = f.read()
            self.e82.setText(temp)
        except:
            print('error loading file name.')

        self.l83 = QLabel('Cycle')
        self.e83 = QLineEdit('1')     # cycle
        self.e83.setToolTip('Number of cycles of above table.\n'
                            'Positive integers only.\n'
                            'Type in 0 for infinity loop.')

        self.l84 = QLabel('Time Unit:')
        self.rb81 = QRadioButton("min", self)
        self.rb82 = QRadioButton("s", self)
        self.rb81.setChecked(True)
        self.l85 = QLabel('    ')  # gap

        self.l88 = QLabel('     ')  # progress hint
        self.l88.setStyleSheet("background-color: lightgrey")
        self.l89 = QLabel('    ')   # error hint
        self.l80 = QLabel('    ')   # total time hint

        self.b8 = QPushButton("Change")
        self.b8.clicked.connect(self.cycletime)
        self.b8.setEnabled(False)

        self.g2 = QGridLayout()  # 10 columns
        self.g2.addWidget(self.l81,  0, 0, 1, 1)
        self.g2.addWidget(self.e81,  0, 1, 1, 8)
        self.g2.addWidget(self.l85,  0, 9, 1, 1)   #gap
        self.g2.addWidget(self.l82,  1, 0, 1, 1)
        self.g2.addWidget(self.e82,  1, 1, 1, 2)   #file name entry
        self.g2.addWidget(self.l83,  1, 3, 1, 1)   # 'cycle'
        self.g2.addWidget(self.e83,  1, 4, 1, 1)
        self.g2.addWidget(self.l84,  1, 5, 1, 1)   # 'time unit:'
        self.g2.addWidget(self.rb81, 1, 6, 1, 1)   # min
        self.g2.addWidget(self.rb82, 1, 7, 1, 1)   # s
        self.g2.addWidget(self.b8,   1, 8, 1, 1)

        self.g2.addWidget(self.l88,  2, 0, 1, 4)
        self.g2.addWidget(self.l89, 2, 4, 1, 2)    # total time hint
        self.g2.addWidget(self.l80, 2, 6, 1, 3)    # error hint

        self.b1 = QToolButton()
        self.b1.setIcon(QIcon("icons/list2.png"))
        self.b1.setIconSize(QSize(40, 40))
        self.b1.setToolTip("load selected csv file")
        self.b1.clicked.connect(self.func1)
        self.l1 = QLabel('Load csv')

        self.b2 = QToolButton()
        self.b2.setIcon(QIcon("icons/start1.png"))
        self.b2.setIconSize(QSize(40, 40))
        self.b2.setToolTip("Start")
        self.b2.clicked.connect(self.func2)
        self.b2.setEnabled(False)
        self.l2 = QLabel('   Start  ')

        self.b3 = QToolButton()
        self.b3.setIcon(QIcon("icons/pause2.png"))
        self.b3.setIconSize(QSize(40, 40))
        self.b3.setToolTip("Stop")
        self.b3.clicked.connect(self.func3)
        self.b3.setEnabled(False)
        self.l3 = QLabel('   Stop  ')

        self.b4 = QToolButton()
        self.b4.setIcon(QIcon("icons/zero.png"))
        self.b4.setIconSize(QSize(40, 40))
        self.b4.setToolTip("Zero all MFCs")
        self.b4.clicked.connect(self.func4)
        self.l4 = QLabel('Zero ALL')

        self.b0 = QToolButton()
        self.b0.setIcon(QIcon("icons/close.png"))
        self.b0.setIconSize(QSize(40, 40))
        self.b0.setToolTip("Close")
        self.b0.clicked.connect(self.exitFunc)
        self.l0 = QLabel('   Close')

        self.l91 = QLabel(' ')  # gap
        self.l92 = QLabel(' ')  # gap
        self.l93 = QLabel(' ')  # gap
        self.l94 = QLabel(' ')  # gap

        self.g3 = QGridLayout()
        self.g3.addWidget(self.b1,  0, 0)
        self.g3.addWidget(self.l1,  1, 0)
        self.g3.addWidget(self.l91, 1, 1)

        self.g3.addWidget(self.b2,  0, 2)
        self.g3.addWidget(self.l2,  1, 2)
        self.g3.addWidget(self.l92, 1, 3)

        self.g3.addWidget(self.b3,  0, 4)
        self.g3.addWidget(self.l3,  1, 4)
        self.g3.addWidget(self.l93, 1, 5)

        self.g3.addWidget(self.b4,  0, 6)
        self.g3.addWidget(self.l4,  1, 6)
        self.g3.addWidget(self.l94, 1, 7)

        self.g3.addWidget(self.b0, 0, 8)
        self.g3.addWidget(self.l0, 1, 8)

        self.L16 = QHBoxLayout()
        self.L17 = QHBoxLayout()
        self.L16.addLayout(self.g2)
        self.L17.addLayout(self.g3)
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


    ################### tab4  ###################
    def layout7(self):
        self.lb302 = QLabel(" ")
        self.lb300 = QLabel()
        self.pixmap = QPixmap('icons/sam1.png')
        self.lb300.setPixmap(
            self.pixmap.scaled(900, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        # self.lb300.setPixmap(self.pixmap)
        self.lb300.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.L401.addWidget(self.lb300)

    ################### tab5  ###################
    def layout8(self):
        self.l201 = QLabel("Your system:")
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

        self.l211 = QLabel("Analyzer")
        self.l212 = QLabel("IP Address:")
        self.e201 =  QLineEdit('')   ## 10.100.4.20
        self.l213 = QLabel(" ")      ## port not found
        self.b201 =  QPushButton("Detect", self)
        self.b201.clicked.connect(self.func201)
        self.b201.setStyleSheet("font: bold")
        self.b201.setToolTip("Detect connection.")

        self.l214 = QLabel("Alicat Board 1:")
        self.l215 = QLabel("Serial Port:")
        self.e202 = QLineEdit()    # '/dev/cu.usbserial-A908UXOQ' '/dev/tty.usbserial-A908UXOQ'
        self.e202.setToolTip('Pick a port name from the top box and try.')
        self.l216 = QLabel(" ")    ## port not found
        self.b202 = QPushButton("Detect", self)
        self.b202.clicked.connect(self.func202)
        self.b202.setStyleSheet("font: bold")
        self.b202.setToolTip("Detect the name of the port connected to Alicat.")

        self.l217 = QLabel("Alicat Board 2:")
        self.l218 = QLabel("Serial Port:")
        self.e203 = QLineEdit()    # '/dev/cu.usbserial-A908UXOQ' '/dev/tty.usbserial-A908UXOQ'
        self.e203.setToolTip('Pick a port name from the top box and try.')
        self.l219 = QLabel(" ")    ## port not found
        self.b203 = QPushButton("Detect", self)
        self.b203.clicked.connect(self.func203)
        self.b203.setStyleSheet("font: bold")
        self.b203.setToolTip("Detect the name of the port connected to Alicat.")
        self.l220 = QLabel("MFC Communication Ports:")

        try:
            f = open(os.path.join('par1', 'analyzer.txt'), "r")
            temp = f.read()  # .splitlines()
            self.e201.setText(temp)  # analyzer
            f = open(os.path.join('par1', 'board1.txt'), "r")
            temp = f.read()
            self.e202.setText(temp)  # alicat1
            f = open(os.path.join('par1', 'board2.txt'), "r")
            temp = f.read()
            self.e203.setText(temp)  # alicat2
        except:
            print('failed to load port names')

        self.g7 = QGridLayout()
        self.g7.addWidget(self.l201, 0, 0)
        self.g7.addWidget(self.rb201, 1, 0)
        self.g7.addWidget(self.rb202, 2, 0)
        self.g7.addWidget(self.rb203, 3, 0)
        self.g7.addWidget(self.b200,  4, 0)
        self.g7.addWidget(self.e200,  5, 0, 1, 3)

        self.g7.addWidget(self.l211, 6, 0)
        self.g7.addWidget(self.l212, 7, 0)
        self.g7.addWidget(self.e201, 7, 1)
        self.g7.addWidget(self.b201, 7, 2)
        self.g7.addWidget(self.l213, 8, 1)

        self.g7.addWidget(self.l214,  9, 0)
        self.g7.addWidget(self.l215, 10, 0)
        self.g7.addWidget(self.e202, 10, 1)
        self.g7.addWidget(self.b202, 10, 2)
        self.g7.addWidget(self.l216, 11, 1)

        self.g7.addWidget(self.l217, 12, 0)
        self.g7.addWidget(self.l218, 13, 0)
        self.g7.addWidget(self.e203, 13, 1)
        self.g7.addWidget(self.b203, 13, 2)
        self.g7.addWidget(self.l219, 14, 1)
        self.g7.addWidget(self.l220, 15, 0)


        self.l221 = QLabel("Name")
        self.l222 = QLabel(" ID ")
        self.l223 = QLabel("Board 1")
        self.l224 = QLabel("Board 2")
        self.l221.setToolTip('Datakey name as displayed in the analyzer')
        self.l222.setToolTip('Set ID on Alicat')
        self.l223.setToolTip('MFCs plugged into board #1')
        self.l224.setToolTip('MFCs plugged into board #2')

        self.l231 = QLabel("  MFC1 ")
        self.l232 = QLabel("  MFC2 ")
        self.l233 = QLabel("  MFC3 ")
        self.l234 = QLabel("  MFC4 ")
        self.l235 = QLabel("  MFC5 ")
        self.l236 = QLabel("  MFC6 ")
        self.l237 = QLabel("  MFC7 ")
        self.l238 = QLabel("  MFC8 ")
        self.l239 = QLabel("  MFC9 ")
        self.l230 = QLabel("  MFC10")

        self.e211 = QLineEdit('')   # ID
        self.e212 = QLineEdit('')
        self.e213 = QLineEdit('')
        self.e214 = QLineEdit('')
        self.e215 = QLineEdit('')
        self.e216 = QLineEdit('')
        self.e217 = QLineEdit('')
        self.e218 = QLineEdit('')
        self.e219 = QLineEdit('')
        self.e210 = QLineEdit('')

        self.rb1  = QRadioButton('', self)
        self.rb1a = QRadioButton('', self)
        self.rb2  = QRadioButton('', self)
        self.rb2a = QRadioButton('', self)
        self.rb3  = QRadioButton('', self)
        self.rb3a = QRadioButton('', self)
        self.rb4  = QRadioButton('', self)
        self.rb4a = QRadioButton('', self)
        self.rb5  = QRadioButton('', self)
        self.rb5a = QRadioButton('', self)
        self.rb6  = QRadioButton('', self)
        self.rb6a = QRadioButton('', self)
        self.rb7  = QRadioButton('', self)
        self.rb7a = QRadioButton('', self)
        self.rb8  = QRadioButton('', self)
        self.rb8a = QRadioButton('', self)
        self.rb9  = QRadioButton('', self)
        self.rb9a = QRadioButton('', self)
        self.rb0  = QRadioButton('', self)
        self.rb0a = QRadioButton('', self)

        #func02 (n, radio button, ID, target flow entry)
        self.b11.clicked.connect(lambda: self.func02(1, self.rb1, self.e211, self.e11))
        self.b12.clicked.connect(lambda: self.func02(2, self.rb2, self.e212, self.e12))
        self.b13.clicked.connect(lambda: self.func02(3, self.rb3, self.e213, self.e13))
        self.b14.clicked.connect(lambda: self.func02(4, self.rb4, self.e214, self.e14))
        self.b15.clicked.connect(lambda: self.func02(5, self.rb5, self.e215, self.e15))
        self.b16.clicked.connect(lambda: self.func02(6, self.rb6, self.e216, self.e16))
        self.b17.clicked.connect(lambda: self.func02(7, self.rb7, self.e217, self.e17))
        self.b18.clicked.connect(lambda: self.func02(8, self.rb8, self.e218, self.e18))
        self.b19.clicked.connect(lambda: self.func02(9, self.rb9, self.e219, self.e19))
        self.b10.clicked.connect(lambda: self.func02(10,self.rb0, self.e210, self.e10))


        self.g8 = QGridLayout()
        self.g8.addWidget(self.l221, 0, 0)
        self.g8.addWidget(self.l222, 1, 0)
        self.g8.addWidget(self.l223, 2, 0)
        self.g8.addWidget(self.l224, 3, 0)

        self.g8.addWidget(self.l231, 0, 1)  #MFC
        self.g8.addWidget(self.l232, 0, 2)
        self.g8.addWidget(self.l233, 0, 3)
        self.g8.addWidget(self.l234, 0, 4)
        self.g8.addWidget(self.l235, 0, 5)
        self.g8.addWidget(self.l236, 0, 6)
        self.g8.addWidget(self.l237, 0, 7)
        self.g8.addWidget(self.l238, 0, 8)
        self.g8.addWidget(self.l239, 0, 9)
        self.g8.addWidget(self.l230, 0, 10)

        self.g8.addWidget(self.e211, 1, 1)  #MFC ID
        self.g8.addWidget(self.e212, 1, 2)
        self.g8.addWidget(self.e213, 1, 3)
        self.g8.addWidget(self.e214, 1, 4)
        self.g8.addWidget(self.e215, 1, 5)
        self.g8.addWidget(self.e216, 1, 6)
        self.g8.addWidget(self.e217, 1, 7)
        self.g8.addWidget(self.e218, 1, 8)
        self.g8.addWidget(self.e219, 1, 9)
        self.g8.addWidget(self.e210, 1, 10)

        self.g8.addWidget(self.rb1, 2, 1)  #board1
        self.g8.addWidget(self.rb2, 2, 2)
        self.g8.addWidget(self.rb3, 2, 3)
        self.g8.addWidget(self.rb4, 2, 4)
        self.g8.addWidget(self.rb5, 2, 5)
        self.g8.addWidget(self.rb6, 2, 6)
        self.g8.addWidget(self.rb7, 2, 7)
        self.g8.addWidget(self.rb8, 2, 8)
        self.g8.addWidget(self.rb9, 2, 9)
        self.g8.addWidget(self.rb0, 2, 10)

        self.g8.addWidget(self.rb1a, 3, 1)  #board2
        self.g8.addWidget(self.rb2a, 3, 2)
        self.g8.addWidget(self.rb3a, 3, 3)
        self.g8.addWidget(self.rb4a, 3, 4)
        self.g8.addWidget(self.rb5a, 3, 5)
        self.g8.addWidget(self.rb6a, 3, 6)
        self.g8.addWidget(self.rb7a, 3, 7)
        self.g8.addWidget(self.rb8a, 3, 8)
        self.g8.addWidget(self.rb9a, 3, 9)
        self.g8.addWidget(self.rb0a, 3, 10)

        # group the buttons
        self.bg1 = QButtonGroup()
        self.bg1.addButton(self.rb1)
        self.bg1.addButton(self.rb1a)
        self.bg2 = QButtonGroup()
        self.bg2.addButton(self.rb2)
        self.bg2.addButton(self.rb2a)
        self.bg3 = QButtonGroup()
        self.bg3.addButton(self.rb3)
        self.bg3.addButton(self.rb3a)
        self.bg4 = QButtonGroup()
        self.bg4.addButton(self.rb4)
        self.bg4.addButton(self.rb4a)
        self.bg5 = QButtonGroup()
        self.bg5.addButton(self.rb5)
        self.bg5.addButton(self.rb5a)

        self.bg6 = QButtonGroup()
        self.bg6.addButton(self.rb6)
        self.bg6.addButton(self.rb6a)
        self.bg7 = QButtonGroup()
        self.bg7.addButton(self.rb7)
        self.bg7.addButton(self.rb7a)
        self.bg8 = QButtonGroup()
        self.bg8.addButton(self.rb8)
        self.bg8.addButton(self.rb8a)
        self.bg9 = QButtonGroup()
        self.bg9.addButton(self.rb9)
        self.bg9.addButton(self.rb9a)
        self.bg0 = QButtonGroup()
        self.bg0.addButton(self.rb0)
        self.bg0.addButton(self.rb0a)


        # fill in values from last time
        def fillvalue(n, a, b, c, d, e, g, h):
            try:
                f = open(os.path.join('par1', 'alicat%s.txt' % n), 'r')
                x = f.read().splitlines()
                if int(x[0]):            #checked: 1
                    a.setChecked(True)   #l21  check box
                    b.setEnabled(True)   #b11  set button
                c.setText(x[1])          #e11  target flow entry
                d.setText(x[2])          #e211  Alicat ID
                if int(x[3]):            #board1: 1
                    e.setChecked(True)   #rb1
                else:
                    g.setChecked(True)   #rb1a
                h.setText(x[4])          #note
            except:
                print('Failed to fill in previous values for MFC%s.'%n)

        fillvalue(1,  self.l21, self.b11, self.e11, self.e211, self.rb1, self.rb1a, self.e21)
        fillvalue(2,  self.l22, self.b12, self.e12, self.e212, self.rb2, self.rb2a, self.e22)
        fillvalue(3,  self.l23, self.b13, self.e13, self.e213, self.rb3, self.rb3a, self.e23)
        fillvalue(4,  self.l24, self.b14, self.e14, self.e214, self.rb4, self.rb4a, self.e24)
        fillvalue(5,  self.l25, self.b15, self.e15, self.e215, self.rb5, self.rb5a, self.e25)
        fillvalue(6,  self.l26, self.b16, self.e16, self.e216, self.rb6, self.rb6a, self.e26)
        fillvalue(7,  self.l27, self.b17, self.e17, self.e217, self.rb7, self.rb7a, self.e27)
        fillvalue(8,  self.l28, self.b18, self.e18, self.e218, self.rb8, self.rb8a, self.e28)
        fillvalue(9,  self.l29, self.b19, self.e19, self.e219, self.rb9, self.rb9a, self.e29)
        fillvalue(10, self.l20, self.b10, self.e10, self.e210, self.rb0, self.rb0a, self.e20)

        self.lb298 = QLabel('    ')
        self.lb299 = QLabel('Yilin Shi | Version 2.0 | Winter 2022 | Santa Clara, CA    ')
        self.lb299.setFont(QFont('Arial', 10))
        self.lb299.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.L501.addLayout(self.g7)
        self.L501.addLayout(self.g8)
        self.L501.addWidget(self.lb298)
        self.L501.addWidget(self.lb299)
        self.L501.addStretch()  # *** will tight the space


    ##################################################
    ################### Functions  ###################
    ##################################################
    # check which MFCs are available
    def mfcs(self):
        try:
            port_ali1 = self.e202.text()
            port_ali2 = self.e203.text()

            # self.fc2 = FlowController(port=port_ali1, address = self.e22.text())
            def ck(a, b, c):    #checkbox, radio button1, ID entry
                if a.isChecked():
                    if b.isChecked():
                        port = port_ali1
                    else:
                        port = port_ali2
                    x = FlowController(port=port, address=c.text())  # 'A'
                    print(x.get())
                    return x

            self.fc1 = ck(self.l21, self.rb1, self.e211)  #MFC reading
            self.fc2 = ck(self.l22, self.rb2, self.e212)
            self.fc3 = ck(self.l23, self.rb3, self.e213)
            self.fc4 = ck(self.l24, self.rb4, self.e214)
            self.fc5 = ck(self.l25, self.rb5, self.e215)
            self.fc6 = ck(self.l26, self.rb6, self.e216)
            self.fc7 = ck(self.l27, self.rb7, self.e217)
            self.fc8 = ck(self.l28, self.rb8, self.e218)
            self.fc9 = ck(self.l29, self.rb9, self.e219)
            self.fc10 =ck(self.l20, self.rb0, self.e210)

            if self.fc1 is not None:
                self.conn[0] = 1   #MFC number
            if self.fc2 is not None:
                self.conn[1] = 1
            if self.fc3 is not None:
                self.conn[2] = 1
            if self.fc4 is not None:
                self.conn[3] = 1
            if self.fc5 is not None:
                self.conn[4] = 1
            if self.fc6 is not None:
                self.conn[5] = 1
            if self.fc7 is not None:
                self.conn[6] = 1
            if self.fc8 is not None:
                self.conn[7] = 1
            if self.fc9 is not None:
                self.conn[8] = 1
            if self.fc10 is not None:
                self.conn[9] = 1
        except:
            self.l89.setText('No MFC connected.')


    ##### Set check box
    def func01(self, a, b):  #checkbox, button
        if a.isChecked():
            b.setEnabled(True)
        else:
            b.setEnabled(False)


    ##### Set MFCs
    def func02(self, n, a, b, c):  #n, radio button, Alicat ID, target flow entry
        try:
            if a.isChecked():
                port = self.e202.text()
            else:
                port = self.e203.text()
            fc = FlowController(port=port, address = b.text()) #'A'
            x = float(c.text())
            fc.set_flow_rate(x)
            self.l88.setText('MFC%s is set to %s.' % (n, x))
        except:
            self.l88.setText('Error set MFC%s'%n)


    ########### last block   ###########
    def cycletime(self):
        try:
            folder = self.e81.text()
            fname = self.e82.text()
            fn = os.path.join(folder, fname + '.csv')
            cycle = int(self.e83.text())
            df = pd.read_csv(fn)
            tc = df.iloc[:, 0]         # first column is time
            if self.rb81.isChecked():  # min, time unit
                tc = tc * 60

            tcyc = sum(list(tc))  # time of 1 cycle
            if tcyc < 3600:
                tcyc1 = str(round(tcyc / 60, 1)) + ' min'
            else:
                tcyc1 = str(round(tcyc / 3600, 1)) + ' h'

            if cycle < 0:
                self.l80.setText('Please put in an integer >=0.')
            elif cycle:
                total_time = tcyc * cycle
                if total_time < 3600:
                    total = str(round(total_time / 60, 1)) + ' min'
                elif total_time < 86400:
                    total = str(round(total_time / 3600, 1)) + ' h'
                else:
                    total = str(round(total_time / 86400, 1)) + ' d'
                self.l80.setText(tcyc1 + '/cycle, total time: %s' % (total))
            else:
                self.l80.setText('Infinity loop, ' + tcyc1 + '/cycle.')
            return 1
        except:
            self.l80.setText('Please enter an integer >=0.')
            return 0


    def func1(self):  # load csv
        folder = self.e81.text()
        fname = self.e82.text()
        fn = os.path.join(folder, fname + '.csv')
        if not os.path.isdir(folder):
            self.l88.setText('Folder not found.')
        elif not os.path.isfile(fn):
            self.l88.setText('csv file not found.')
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

                self.l88.setText('%s.csv file loaded. ' % (fname))
                self.b2.setEnabled(True)
                self.b3.setEnabled(False)
                self.b8.setEnabled(True)  #change
            except:
                self.l88.setText('Error loading %s.csv file.' % (fname))

    def refresh_label(self):
        try:
            host = self.e201.text()
            ipadd = 'http://' + host
            MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection",
                                                    IsDontCareConnection=False)

            if self.conn[0]:
                fl = self.fc1.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC1', fl)
                self.l31.setText(str(fl))

                # pressure and temperature of the first MFC
                try:
                    self.l52.setText(str((self.fc1.get()['pressure'])))
                    self.l54.setText(str(self.fc1.get()['temperature']))
                except:
                    pass

            if self.conn[1]:
                fl = self.fc2.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC2', fl)
                self.l32.setText(str(fl))

            if self.conn[2]:
                fl = self.fc3.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC3', fl)
                self.l33.setText(str(fl))

            if self.conn[3]:
                fl = self.fc4.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC4', fl)
                self.l34.setText(str(fl))

            if self.conn[4]:
                fl = self.fc5.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC5', fl)
                self.l35.setText(str(fl))

            if self.conn[5]:
                fl = self.fc6.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC6', fl)
                self.l36.setText(str(fl))

            if self.conn[6]:
                fl = self.fc7.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC7', fl)
                self.l37.setText(str(fl))

            if self.conn[7]:
                fl = self.fc8.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC8', fl)
                self.l38.setText(str(fl))

            if self.conn[8]:
                fl = self.fc9.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC9', fl)
                self.l39.setText(str(fl))

            if self.conn[9]:
                fl = self.fc10.get()['mass_flow']
                MeasSystem.Backdoor.SetData('MFC10', fl)
                self.l30.setText(str(fl))

            self.l89.setText('Data sent to Analyzer.')
        except:
            self.l89.setText('Error refresh Alicat.')

    ## check of analyzer is connected
    def analyzerip(self):
        try:
            host = self.e201.text()
            socket.create_connection((host, port_in), 3)
            # self.l88.setText('Analyzer in port ready')
            self.anaip = 1
        except:
            self.l89.setText('Analyzer in port not ready.')


    def func2(self):  # start run csv data, refresh label, plot
        try:
            if not self.anaip:
                self.analyzerip()

            if self.anaip:
                self.conn = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
                self.mfcs()
                print(self.conn)

                if len(self.conn): #>0
                    self.canvas1.close_event()
                    self.figure1.clear()
                    self.canvas2.close_event()
                    self.figure2.clear()

                    self.timer.start()  # alicat data, refresh label, send to analyzer backdoor
                    self.plot1()
                    self.b1.setEnabled(False)
                    self.b2.setEnabled(False)
                    self.b3.setEnabled(True)

                    # save parameters in 'par'
                    folder = self.e81.text()
                    fnpar = os.path.join(folder, 'par')
                    if os.path.isdir(fnpar):
                        shutil.rmtree(fnpar)
                    os.mkdir(fnpar)

                    t1 = int(time.time())
                    t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))
                    self.label1 = 'Start: %s. ' % t
                    self.l88.setText(self.label1)
                    self.l89.setText(' ')

                    fn = os.path.join(fnpar, 't1.txt')
                    t = time.strftime('%Y%m%d%H%M', time.localtime(t1))
                    with open(fn, 'a') as f:
                        f.write('%s\n%s\n%s' % (t[:8], t[8:10], t[10:]))

                    fn = os.path.join(fnpar, 'cycle.txt')
                    with open(fn, 'a') as f:
                        f.write(self.e83.text())

                    def save(n, e): #n, note
                        p = os.path.join(fnpar, 'mfc%s.txt'%n)
                        if os.path.isfile(p):
                            os.remove(p)
                        with open(p, 'a') as f:
                            f.write(e.text() + '\n')

                    # save parameters in 'par1' of source code
                    def save1(n, a, b, c, d, e): #n, checkbox, set value, Alicat ID, rb1, note
                        p = os.path.join('par1', 'alicat%s.txt'%n)
                        if os.path.isfile(p):
                            os.remove(p)
                        with open(p, 'a') as f:
                            if a.isChecked():
                                f.write('1\n')
                            else:
                                f.write('0\n')
                            f.write(b.text() + '\n')
                            f.write(c.text() + '\n')
                            if d.isChecked():
                                f.write('1\n')
                            else:
                                f.write('0\n')
                            f.write(e.text() + '\n')

                    if self.conn[0]:
                        save(1, self.e21)
                        save1(1, self.l21, self.e11, self.e211, self.rb1, self.e21)
                    if self.conn[1]:
                        save(2, self.e22)
                        save1(2, self.l22, self.e12, self.e212, self.rb2, self.e22)
                    if self.conn[2]:
                        save(3, self.e23)
                        save1(3, self.l23, self.e13, self.e213, self.rb3, self.e23)
                    if self.conn[3]:
                        save(4, self.e24)
                        save1(4, self.l24, self.e14, self.e214, self.rb4, self.e24)
                    if self.conn[4]:
                        save(5, self.e25)
                        save1(5, self.l25, self.e15, self.e215, self.rb5, self.e25)
                    if self.conn[5]:
                        save(6, self.e26)
                        save1(6, self.l26, self.e16, self.e216, self.rb6, self.e26)
                    if self.conn[6]:
                        save(7, self.e27)
                        save1(7, self.l27, self.e17, self.e217, self.rb7, self.e27)
                    if self.conn[7]:
                        save(8, self.e28)
                        save1(8, self.l28, self.e18, self.e218, self.rb8, self.e28)
                    if self.conn[8]:
                        save(9, self.e29)
                        save1(9, self.l29, self.e19, self.e219, self.rb9, self.e29)
                    if self.conn[9]:
                        save(10, self.e20)
                        save1(10,self.l20, self.e10, self.e210, self.rb0, self.e20)

                else:
                    self.l88.setText('MFC not available. Select a MFC or check analyzer IP, computer port number, unit ID.')
        except:
            self.l88.setText('Error run experiment.')


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
            t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))
            self.l89.setText('Finished at %s.' % t)
            self.b1.setEnabled(True)
            self.b2.setEnabled(True)
            self.b3.setEnabled(False)
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

                    if self.conn[0]:
                        self.fc1.set_flow_rate(self.f1)
                    if self.conn[1]:
                        self.fc2.set_flow_rate(self.f2)
                    if self.conn[2]:
                        self.fc3.set_flow_rate(self.f3)
                    if self.conn[3]:
                        self.fc4.set_flow_rate(self.f4)
                    if self.conn[4]:
                        self.fc5.set_flow_rate(self.f5)
                    if self.conn[5]:
                        self.fc6.set_flow_rate(self.f6)
                    if self.conn[6]:
                        self.fc7.set_flow_rate(self.f7)
                    if self.conn[7]:
                        self.fc8.set_flow_rate(self.f8)
                    if self.conn[8]:
                        self.fc9.set_flow_rate(self.f9)
                    if self.conn[9]:
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

                if self.conn[0]:
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
                    ax1.set_xlabel(' MFC1 ')

                if self.conn[1]:
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
                    ax2.set_xlabel(' MFC2 ')

                if self.conn[2]:
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
                    ax3.set_xlabel(' MFC3 ')

                if self.conn[3]:
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
                    ax4.set_xlabel(' MFC4 ')

                if self.conn[4]:
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
                    ax5.set_xlabel(' MFC5 ')

                if self.conn[5]:
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
                    ax6.set_xlabel(' MFC6 ')


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
                    # try:
                    #     with open(self.fn4, 'a') as f:
                    #         f.write(note)
                    # except:
                    #     pass

                    # self.l89.setText('')
                    self.l88.setText(self.label1 + 'Cycle %s done.' % self.ct)
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

                if self.conn[6]:
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
                    ax7.set_xlabel(' MFC7 ')

                if self.conn[7]:
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
                    ax8.set_xlabel(' MFC8 ')

                if self.conn[8]:
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
                    ax9.set_xlabel(' MFC9 ')

                if self.conn[9]:
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
                    ax0.set_xlabel(' MFC10 ')

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
            # self.conn = 0
            self.l89.setText('Error plot.')

    def func3(self):  # pause is used as stop
        try:
            self.anim1.pause()
            self.anim2.pause()
            self.timer.stop()

            t1 = int(time.time())  #write down end time
            folder = self.e81.text()
            fn = os.path.join(folder, 'par', 't3.txt')
            if os.path.isfile(fn):
                os.remove(fn)
            t = time.strftime('%Y%m%d%H%M', time.localtime(t1))
            with open(fn, 'a') as f:
                f.write('%s\n%s\n%s' % (t[:8], t[8:10], t[10:]))

            t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t1))
            self.l89.setText('Finished at %s.' % t)
            self.b1.setEnabled(True)
            self.b2.setEnabled(True)
            self.b3.setEnabled(False)

        except:
            self.l89.setText('Error stop experiment.')


    def func4(self):  # zero all
        try:
            if sum(self.conn) == 0:
                self.mfcs()

            if sum(self.conn):
                if self.conn[0]:
                    self.fc1.set_flow_rate(0)
                if self.conn[0]:
                    self.fc2.set_flow_rate(0)
                if self.conn[0]:
                    self.fc3.set_flow_rate(0)
                if self.conn[0]:
                    self.fc4.set_flow_rate(0)
                if self.conn[0]:
                    self.fc5.set_flow_rate(0)
                if self.conn[0]:
                    self.fc6.set_flow_rate(0)
                if self.conn[0]:
                    self.fc7.set_flow_rate(0)
                if self.conn[0]:
                    self.fc8.set_flow_rate(0)
                if self.conn[0]:
                    self.fc9.set_flow_rate(0)
                if self.conn[0]:
                    self.fc10.set_flow_rate(0)

                # self.e11.setText('')
                # self.e12.setText('')
                # self.e13.setText('')
                # self.e14.setText('')
                # self.e15.setText('')
                # self.e16.setText('')
                # self.e17.setText('')
                # self.e18.setText('')
                # self.e19.setText('')
                # self.e10.setText('')
                self.l89.setText('All MFCs are zero-ed.')
            else:
                self.l89.setText('No MFC available.')

        except:
            self.l89.setText('Error zero all.')

    ################### Tab4 Functions ###############
    def func200(self):
        portusb = [p.device for p in ls.comports()]
        # print(portusb)
        self.e200.setPlainText(str(portusb))

    def func201(self):  # detect analyzer IP address
        self.l213.setText('')
        try:
            host = self.e201.text()
            socket.create_connection((host, port_out), 5)
            socket.create_connection((host, port_in), 5)
            self.l213.setText('Analyzer connected')
            p = os.path.join('par1', 'analyzer.txt')
            if os.path.isfile(p):
                os.remove(p)
            with open(p, 'a') as f:
                f.write(host)
        except:
            self.l213.setText('!Analyzer not connected.')

    def func202(self):  # detect Alicat board1/sample1 port
        # self.l216.setText('...')
        # QApplication.processEvents()
        port_ali = self.e202.text()

        if port_ali == '':
            self.l216.setText('Please pick a port name from the top box and try.')
        else:
            try:
                flow_controller1 = FlowController(port=port_ali, address='A')
                print(flow_controller1.get())
                self.l216.setText('Port found.')
                p = os.path.join('par1', 'board1.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e202.text())
            except:
                self.l216.setText('Port (with alicat ID=A) not found.')


    def func203(self):  # detect Alicat sample2/board2 port
        # self.l219.setText('...')
        # QApplication.processEvents()
        port_ali = self.e203.text()

        if port_ali == '':
            self.l219.setText('Please pick a port name from the top box and try.')
        else:
            try:
                flow_controller1 = FlowController(port=port_ali, address='A')
                print(flow_controller1.get())
                self.l219.setText('Port found.')

                p = os.path.join('par1', 'board2.txt')
                if os.path.isfile(p):
                    os.remove(p)
                with open(p, 'a') as f:
                    f.write(self.e202.text())
            except:
                self.l219.setText('Port (with alicat ID=A) not found.')


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






## Yilin Shi | Picarro | 2023.1.3
# shiyilin890@gmail.com
# Bog the fat crocodile vvvvvvv
#                       ^^^^^^^
