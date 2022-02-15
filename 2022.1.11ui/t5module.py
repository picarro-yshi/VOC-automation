## VOC Automation: equipment testing for main GUI
## Yilin Shi | Picarro | 2022.2.10

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


######## module testing
# host = '10.100.4.20'      ## IP address of analyzer
# ipadd = 'http://'+host
# # ipadd = 'http://1022.corp.picarro.com'     ## ulr
# def checkip(host, port):
#     try:
#         socket.create_connection((host, port), 5)  #only try 5s time out
#         print('connected')
#         # MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection",IsDontCareConnection=False)
#         # print(MeasSystem.GetStates())
#     except:
#         print('not connected')

## MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{port}", "test_connection", IsDontCareConnection=False)
# MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection", IsDontCareConnection=False) #time out has no effect
# print(MeasSystem.GetStates())
# checkip(host, port_in)
# exit()

# dm_queue = Queue(180)  ## data manager
# listener = Listener(dm_queue, host, port_out, StringPickler.ArbitraryObject, retry=True)

# i=0
# while True:
#     dm = dm_queue.get(timeout=10)
#     print(dm)
#     print(dm['source'])
#     if dm['source'] == 'analyze_VOC_broadband_cal':
#         # print(dm)
#         # print(dm['data'])
#         # print(len(dm['data']))
#         anakey = list(dm['data'].keys())
#         print(anakey)
#         break
#     if i == 5:
#         print ('analyze_VOC_broadband_cal not exist. Your litho_fitter on the analyzer may stop running.\n'
#                'Please start the fitter and try again.')
#         break
#     i += 1
# exit()

## find USB port for equipment: Mac, Windows, Linux
## Alicat
# port_ali = '/dev/tty.usbserial-A908UXOQ'   ## 'COM4'
## US Solid Scale
# port_so = '/dev/cu.usbserial-14310'   ##'COM4'
## Mettler Toledo Scale not working
# port_mt = '/dev/cu.usbserial-14420'    ## Mac

# serialPort = serial.Serial(port= port_so, baudrate=1200,
#                            bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
# serialString = ""  # Used to hold data coming over UART
# while (1):
#     # Wait until there is data waiting in the serial buffer
#     if serialPort.in_waiting > 0:
#         time.sleep(2)
#         # Read data out of the buffer until a carraige return / new line is found
#         serialString = serialPort.readline()
#         # print(serialString.decode('Ascii'))   ## windows
#         # print(len(serialString))
#         weight = serialString.decode("utf-8")   ## Mac
#         print(float(weight[5:12]))

## Mettler Toledo Scale: USB-A works on Windows; RS232 does not work
# serialPort = serial.Serial(port= 'COM4', baudrate=9600,
#                            bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
# serialString = ""  # Used to hold data coming over UART
# while (1):
#     # Wait until there is data waiting in the serial buffer
#     # serialPort.write(b'W\r\n')
#     # if serialPort.in_waiting > 0:
#     if 1:
#         time.sleep(2)
#         # Read data out of the buffer until a carraige return / new line is found
#         serialString = serialPort.readline()
#         print(serialString)


# try:
#     port_so = self.e203.text()
#     if opsystem == 'Windows':  # need to close serial port
#         self.serialPort.close()
#     serialPort = serial.Serial(port=port_so, baudrate=1200,
#                                bytesize=8, timeout=10, stopbits=serial.STOPBITS_ONE)
#     # while (1):
#     #     if serialPort.in_waiting > 0:
#     w2=[]
#     if 1:
#         for i in range(5):
#             time.sleep(1)
#             serialString = serialPort.readline()
#             w1 = serialString.decode("utf-8")
#             print(w1)
#             if w1[0] == 'G':
#                 weight = float(w1[5:12])
#                 w3 = round(weight, 5)
#                 self.lb29.setText(str(w3))
#                 self.e92.setText(str(w3))
#                 self.lb42.setText('\u2713')
#                 break
# except:
#     self.lb42.setText('\u2717')
#     self.lb20.setText('!Scale not found.')


# ## Mettler Toledo Scale    range 120g - 0.01 mg
# TCP_IP = '10.100.3.148'
# TCP_PORT = 8001
# BUFFER_SIZE = 1024
# try:
#     s = socket.create_connection((TCP_IP, TCP_PORT), 5)  # only try 5s time out
#     s.settimeout(2)
#     print('Mettler Toledo Scale connected')
#     # s.send('I0\r\n'.encode())
#     # s.send(b'T\r\n')   #Tare, must >0
#     # s.send(b'Z\r\n')   # Zero
#
#     try:
#         print(s.recv(BUFFER_SIZE))
#         print('Mettler Toledo scale is ready.')
#     except:
#         print('Wake up the Mettler Toledo scale')
#         s.send(b'@\r\n')     # Wake up scale
#         k = s.recv(BUFFER_SIZE)  #= clear buffer
#         # time.sleep(1)
#
#     for i in range(10):
#         k = s.recv(BUFFER_SIZE)
#         # print(k)
#         k = k.decode("utf-8")
#         # print(k)
#         k1 = round(float(k[3:15]), 5)
#         print(k1)
#     s.close()
#
# except:
#     print('Mettler Toledo scale not connected to internet.')
# exit()


# ## Jupyternotebook calibration factor
# if __name__ == "__main__":
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
#
#     jupyternotebook(fname, gas, cid, volume, weight, density, MW, startTime, endTime, suffix, showgraph=True)
#     ## to save figure, add savefig=Trueexit()


# try:
#     f = open('log/rdrive.txt', "r")
#     temp = f.read()
#     self.e81.setPlainText(temp)
# except:
#     self.e81.setPlainText('/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/')  ## Mac


# if os.path.isfile('log/port.txt'):
#     os.remove('log/port.txt')
# with open('log/port.txt', 'a') as f:
#     f.write(self.e201.text() + '\n')
#     f.write(self.e202.text() + '\n')

# def func203(self):
#     self.lb219.setText('...')
#     port_so = self.e203.text()
#
#     if port_so == '':
#         portusb = [p.device for p in ls.comports()]
#         bk = False
#         for i in reversed(portusb):
#             print(i)
#             try:
#                 serialPort = serial.Serial(port=i, baudrate=1200,
#                                            bytesize=8, timeout=5, stopbits=serial.STOPBITS_ONE)
#                 time.sleep(1)
#                 for j in range(4):  ## avoid infinity while loop
#                     serialString = serialPort.readline()
#                     w1 = serialString.decode("utf-8")
#                     print(w1)
#                     if any(s.isdigit() for s in w1):
#                         port_so = i
#                         bk = True
#                         break
#                 if bk:
#                     break
#             except:
#                 pass
#     else:
#         try:
#             serialPort = serial.Serial(port=port_so, baudrate=1200,
#                                        bytesize=8, timeout=10, stopbits=serial.STOPBITS_ONE)
#             serialString = serialPort.readline()
#             w1 = serialString.decode("utf-8")
#             print(w1)
#         except:
#             port_so = ''
#
#     if port_so == '':
#         self.lb219.setText('Port not found.')
#     else:
#         self.e203.setText(port_so)
#         self.lb219.setText('Port found.')
#         if os.path.isfile('log/scaleuso.txt'):
#             os.remove('log/scaleuso.txt')
#         with open('log/scaleuso.txt', 'a') as f:
#             f.write(self.e203.text())



