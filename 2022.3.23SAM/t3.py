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

## Qt GUI
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap, QFont, QIcon, QColor
from PyQt6.QtCore import *
from PyQt6 import QtWidgets, QtGui

## Customized file/libraries
import style
from alicat import FlowController  # pip install alicat

## hard-coded global parameters
rt = 2000  ## ms, Alicat label refresh time


port_ali = 'COM7'  ## '/dev/tty.usbserial-A908UXOQ'
fc1 = FlowController(port=port_ali, address='A')
fc2 = FlowController(port=port_ali, address='B')
fc3 = FlowController(port=port_ali, address='C')
fc4 = FlowController(port=port_ali, address='D')
fc5 = FlowController(port=port_ali, address='E')
fc6 = FlowController(port=port_ali, address='F')
fc7 = FlowController(port=port_ali, address='G')
fc8 = FlowController(port=port_ali, address='H')
fc9 = FlowController(port=port_ali, address='I')
fc10 = FlowController(port=port_ali, address='J')

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("S A M")
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
        self.layout1()
        self.layout2()
        self.layout3()
        self.layout4()
        # self.layout5()
        # self.layout6()
        self.layout7()

    def mainlayout(self):
        mainLayout=QVBoxLayout()
        self.tabs =QTabWidget()
        self.tab1=QWidget()
        self.tab2=QWidget()
        self.tab3=QWidget()
        self.tabs.addTab(self.tab1, "   ⬥ Experiment Settings   ")
        self.tabs.addTab(self.tab2, "     ⬥ Port Detection      ")
        self.tabs.addTab(self.tab3, "   ⬥ SAM Design Diagram    ")
        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)
        self.show()

        ## initialize parameters
        # self.baseline = []
        # self.view_point = 0   #total points plotted in spectrum viewer window
        # self.total_point = 0  #total points processed, for all three analyzer data source

        ###### tabs ###########
        self.L1 = QVBoxLayout()
        self.L11 = QVBoxLayout()
        self.L12 = QHBoxLayout()
        self.L13 = QHBoxLayout()
        self.L14 = QHBoxLayout()
        self.L1.addLayout(self.L11, 10)
        self.L1.addLayout(self.L12, 20)
        self.L1.addLayout(self.L13, 60)
        self.L1.addLayout(self.L14, 10)

        self.tab1.setLayout(self.L1)

        self.L301 = QVBoxLayout()
        self.tab3.setLayout(self.L301)


    ################### tab1  ###################
    def layout1(self):
        self.img = QLabel()
        self.pixmap = QPixmap('icons/picarro.png')
        self.img.setPixmap(self.pixmap.scaled(250, 250, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        self.img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lb11 = QLabel('Yilin Shi | Version 2.0 | Spring 2022 | Santa Clara, CA    ')
        self.lb11.setFont(QFont('Arial', 9))
        self.lb11.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lb12 = QLabel('  ')

        self.L11.addWidget(self.img)
        # self.L11.addWidget(self.lb11)
        # self.L11.addWidget(self.lb12)


    def layout2(self):
        self.box12 = QGroupBox()
        self.box12.setStyleSheet(style.box12())

        self.lb21 = QLabel('  MFC#  ')
        self.lb22 = QLabel('  Flow  ')
        self.lb23 = QLabel('  Set   ')
        self.lb24 = QLabel('  Max.  ')

        self.lb31 = QLabel('1')
        self.lb32 = QLabel('2')
        self.lb33 = QLabel('3')
        self.lb34 = QLabel('4')
        self.lb35 = QLabel('5')
        self.lb36 = QLabel('6')
        self.lb37 = QLabel('7')
        self.lb38 = QLabel('8')
        self.lb39 = QLabel('9')
        self.lb30 = QLabel('10')

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

        self.g1 = QGridLayout()
        self.g1.addWidget(self.lb21,  0, 0)
        self.g1.addWidget(self.lb22,  1, 0)
        self.g1.addWidget(self.lb23,  2, 0)
        self.g1.addWidget(self.lb24,  3, 0)

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

        self.g1.addWidget(self.e11,   2, 1)
        self.g1.addWidget(self.e12,   2, 2)
        self.g1.addWidget(self.e13,   2, 3)
        self.g1.addWidget(self.e14,   2, 4)
        self.g1.addWidget(self.e15,   2, 5)
        self.g1.addWidget(self.e16,   2, 6)
        self.g1.addWidget(self.e17,   2, 7)
        self.g1.addWidget(self.e18,   2, 8)
        self.g1.addWidget(self.e19,   2, 9)
        self.g1.addWidget(self.e10,   2, 10)

        self.g1.addWidget(self.lb51,  3, 1)
        self.g1.addWidget(self.lb52,  3, 2)
        self.g1.addWidget(self.lb53,  3, 3)
        self.g1.addWidget(self.lb54,  3, 4)
        self.g1.addWidget(self.lb55,  3, 5)
        self.g1.addWidget(self.lb56,  3, 6)
        self.g1.addWidget(self.lb57,  3, 7)
        self.g1.addWidget(self.lb58,  3, 8)
        self.g1.addWidget(self.lb59,  3, 9)
        self.g1.addWidget(self.lb50,  3, 10)

        self.g1.addWidget(self.b11,   4, 1)
        self.g1.addWidget(self.b12,   4, 2)
        self.g1.addWidget(self.b13,   4, 3)
        self.g1.addWidget(self.b14,   4, 4)
        self.g1.addWidget(self.b15,   4, 5)
        self.g1.addWidget(self.b16,   4, 6)
        self.g1.addWidget(self.b17,   4, 7)
        self.g1.addWidget(self.b18,   4, 8)
        self.g1.addWidget(self.b19,   4, 9)
        self.g1.addWidget(self.b10,   4, 10)

        self.L15 = QVBoxLayout()
        self.L15.addLayout(self.g1)
        self.box12.setLayout(self.L15)
        self.L12.addWidget(self.box12)

        ## refresh Alicat label
        self.timer = QTimer()
        self.timer.setInterval(rt)
        self.timer.timeout.connect(self.refresh_label)


    def layout3(self):
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

        # self.btn21 = QPushButton("View Holiday")
        # self.btn21.clicked.connect(self.select_data)
        # self.btn22 = QPushButton("Add Holiday")
        # self.btn22.clicked.connect(self.func1)

        self.L13.addWidget(self.tableWidget)

    def layout4(self):
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
        self.lb2 = QLabel(' Start ')

        self.b3 = QToolButton()
        self.b3.setIcon(QIcon("icons/zero.png"))
        self.b3.setIconSize(QSize(40, 40))
        self.b3.setToolTip("Zero all MFCs")
        self.b3.clicked.connect(self.func3)
        self.lb3 = QLabel('Zero ALL')

        self.b5 = QToolButton()
        self.b5.setIcon(QIcon("icons/stop1.png"))
        self.b5.setIconSize(QSize(40, 40))
        self.b5.setToolTip("Close")
        self.b5.clicked.connect(self.exitFunc)
        self.lb5 = QLabel('  Close')

        self.lb0 = QLabel('  ')  #for hint

        self.lb91 = QLabel('  ')  #gap
        self.lb92 = QLabel('  ')  #gap
        self.lb93 = QLabel('  ')  #gap
        self.lb94 = QLabel('  ')  #gap


        self.g4 = QGridLayout()
        self.g4.addWidget(self.b1,  0, 0)
        self.g4.addWidget(self.lb1, 1, 0)
        self.g4.addWidget(self.b2,  0, 2)
        self.g4.addWidget(self.lb2, 1, 2)
        self.g4.addWidget(self.b3,  0, 4)
        self.g4.addWidget(self.lb3, 1, 4)
        self.g4.addWidget(self.b5,  0, 6)
        self.g4.addWidget(self.lb5, 1, 6)
        # self.g4.addWidget(self.lb0, 2, 0, 1, 5)

        self.g4.addWidget(self.lb91, 1, 1)
        self.g4.addWidget(self.lb91, 1, 3)
        self.g4.addWidget(self.lb91, 1, 5)


        self.L14.addLayout(self.g4)
        self.L1.addWidget(self.lb0)


    ################### tab2  ###################


    ################### tab3  ###################
    def layout7(self):
        self.lb302 = QLabel(" ")
        self.lb300 = QLabel()
        self.pixmap = QPixmap('icons/sam1.png')
        self.lb300.setPixmap(self.pixmap.scaled(900, 800, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        # self.lb300.setPixmap(self.pixmap.scaled(900, 800, Qt.AspectRatioMode.KeepAspectRatio))
        # self.lb300.setPixmap(self.pixmap)
        self.lb300.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.L301.addWidget(self.lb300)


    ################### Functions  ###################

    ########### Set MFCs  ###########
    def func11(self):
        a = self.lb31.text()
        b = self.e11.text()
        c = self.lb51.text()
        fc1.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.'%(a, b, c))

    def func12(self):
        a = self.lb32.text()
        b = self.e12.text()
        c = self.lb52.text()
        fc2.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func13(self):
        a = self.lb33.text()
        b = self.e13.text()
        c = self.lb53.text()
        fc3.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func14(self):
        a = self.lb34.text()
        b = self.e14.text()
        c = self.lb54.text()
        fc4.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func15(self):
        a = self.lb35.text()
        b = self.e15.text()
        c = self.lb55.text()
        fc5.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func16(self):
        a = self.lb36.text()
        b = self.e16.text()
        c = self.lb56.text()
        fc6.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func17(self):
        a = self.lb37.text()
        b = self.e17.text()
        c = self.lb57.text()
        fc7.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func18(self):
        a = self.lb38.text()
        b = self.e18.text()
        c = self.lb58.text()
        fc8.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func19(self):
        a = self.lb39.text()
        b = self.e19.text()
        c = self.lb59.text()
        fc9.set_flow_rate(float(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    def func10(self):
        a = self.lb30.text()
        b = self.e10.text()
        c = self.lb50.text()
        print(b)
        fc10.set_flow_rate(int(b))
        self.lb0.setText('MFC%s set to %s %s.' % (a, b, c))

    ########### last row  ###########
    def func1(self):     # load csv
        fn = 'sam1'
        df1 = pd.read_csv(fn + '.csv')
        # print(df.head())
        tc = df1.iloc[:, 0]  # first column is time, s
        df = df1.iloc[:, 1:]  # remove first column
        nr = df.shape[0]  # row number
        nc = df.shape[1]  # column number

        result = df1.to_numpy()
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

        self.b2.setEnabled(True)

    def refresh_label(self):
        try:
            fl1 = fc1.get()
            fl2 = fc2.get()
            fl3 = fc3.get()
            fl4 = fc4.get()
            fl5 = fc5.get()
            # fl6 = fc6.get()
            fl7 = fc7.get()
            fl8 = fc8.get()
            # fl9 = fc9.get()
            fl0 = fc10.get()

            self.lb41.setText(str(fl1['mass_flow']))
            self.lb42.setText(str(fl2['mass_flow']))
            self.lb43.setText(str(fl3['mass_flow']))
            self.lb44.setText(str(fl4['mass_flow']))
            self.lb45.setText(str(fl5['mass_flow']))
            # self.lb46.setText(str(fl6['mass_flow']))
            self.lb47.setText(str(fl7['mass_flow']))
            self.lb48.setText(str(fl8['mass_flow']))
            # self.lb49.setText(str(fl9['mass_flow']))
            self.lb40.setText(str(fl0['mass_flow']))
        except:
            self.lb0.setText('Error refresh Alicat readings.')


    # def func2(self):     # start MFC, refresh label and print figure


    def func2(self):     # start run csv data
        try:
            fn = 'sam1'
            df = pd.read_csv(fn + '.csv')
            tc = df.iloc[:, 0]    # first column is time, s
            nr = df.shape[0]      # row number
            nc = df.shape[1]      # column number

            df1 = df.iloc[:, 1:]  # remove first column
            # nr = df.shape[0]      # row number
            # nc = df.shape[1]      # column number

            for i in range(nr):
                for j in range(1, nc):
                    self.tableWidget.item(i, j).setBackground(QColor(250, 250, 250))
            QApplication.processEvents()  # must present to show the effect
            itemMeasVal = self.tableWidget.item(0, 0)
            self.tableWidget.setItem(0, 0, itemMeasVal)
            self.tableWidget.scrollToItem(itemMeasVal, QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)

            self.lb0.setText('Experiment started.')
            self.timer.start()  # refresh label

            ## set flow rate
            for i in range(nr):  # go row by row
                t = int(tc[i])  # tc is string
                row = list(df.iloc[i])
                print('t, row,')
                print(t, row)

                fc1.set_flow_rate(row[1])
                fc2.set_flow_rate(row[2] / 50)
                fc3.set_flow_rate(row[3])
                fc4.set_flow_rate(row[4] / 50)
                fc5.set_flow_rate(row[5] * 10)
                # fc6.set_flow_rate(row[6])
                fc7.set_flow_rate(row[7])
                fc8.set_flow_rate(row[8])
                # fc9.set_flow_rate(row[9])
                fc10.set_flow_rate(row[10])

                self.tableWidget.item(i, 0).setBackground(QColor(115, 130, 95))  #green grey
                for j in range(1, nc):
                    self.tableWidget.item(i, j).setBackground(QColor(151, 186, 102))  #green
                QApplication.processEvents()  #must present to show the effect

                itemMeasVal = self.tableWidget.item(i, 0)
                self.tableWidget.setItem(i, 0, itemMeasVal)
                # self.tableWidget.scrollToItem(itemMeasVal,QtWidgets.QAbstractItemView.ScrollHint.EnsureVisible)
                self.tableWidget.scrollToItem(itemMeasVal,QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)
                # This is for the bar to scroll automatically and then the current item added is always visible
                time.sleep(t)

                self.tableWidget.item(i, 0).setBackground(QColor(170, 170, 170))   #deep gray
                for j in range(1, nc):
                    self.tableWidget.item(i, j).setBackground(QColor(230, 230, 230))  #light gray
                QApplication.processEvents()  #must present to show the effect
            self.lb0.setText('Experiment ended.')
        except:
            self.lb0.setText('Error run experiment.')



    def func3(self):     # zero all
        fc1.set_flow_rate(0)
        fc2.set_flow_rate(0)
        fc3.set_flow_rate(0)
        fc4.set_flow_rate(0)
        fc5.set_flow_rate(0)
        # fc6.set_flow_rate(0)
        fc7.set_flow_rate(0)
        fc8.set_flow_rate(0)
        # fc9.set_flow_rate(0)
        fc10.set_flow_rate(0)
        self.lb0.setText('All MFCs are zero-ed.')

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



