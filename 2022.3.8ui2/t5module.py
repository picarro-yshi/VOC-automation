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
import scipy.stats

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
analyzer_source = 'analyze_VOC_broadband_custom'   ## listener data key
rt = 2000                 ## ms, Alicat label refresh time
spec_xt = 400             ## min, spectrum plot animation: x axis time window duration 500min=8h20'
baseline_time = 20        ## min, 20 min sample baseline time
MT_IP = '10.100.3.148'    ## Mettler Toledo scale TCP_IP
MT_PORT = 8001            ## Mettler Toledo scale TCP_PORT

## Customized file/libraries
from alicat import FlowController     # pip install alicat
import CmdFIFO_py3 as CmdFIFO
from Listener_py3 import Listener
import StringPickler_py3 as StringPickler
import style
from spviewer import t8               ## spectrum animation

jupyterpath = '../2022.2.18jupyter2/' ## './' in same folder
sys.path.append(jupyterpath)          ## jupyternotebook re-write
from t6ju import *                    ## droplet test
from t7tk import *                    ## gas tank


######## module testing  ########################
host = '10.100.3.123'      ## IP address of analyzer
ipadd = 'http://'+host     ## ulr
def checkip(host, port):
    try:
        socket.create_connection((host, port), 5)  #only try 5s time out
        print('connected')
        # MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection",IsDontCareConnection=False)
        # print(MeasSystem.GetStates())
    except:
        print('not connected')

def anl_backdoor():
    checkip(host, port_in)
    MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{port_in}", "test_connection", IsDontCareConnection=False)
    MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port_in}", "test_connection", IsDontCareConnection=False) #time out has no effect
    print(MeasSystem.GetStates())

def anl_listener():
    dm_queue = Queue(180)  ## data manager
    listener = Listener(dm_queue, host, port_out, StringPickler.ArbitraryObject, retry=True)

    i=0
    # t1 = time.time()
    while True:
        dm = dm_queue.get(timeout=10)
        # print(dm['source'])
        # print(dm)
        # print(len(dm['data']))

        # print(time.time()-t1)
        # t1 = time.time()
        if dm['source'] == analyzer_source:  # 'analyze_VOC_broadband_custom'
            # print(dm)
            # print(dm['data'])
            # print(len(dm['data']))
            anakey = list(dm['data'].keys())
            print(anakey)
            break
        if i == 5:
            print (analyzer_source + ' not exist. Your litho_fitter on the analyzer may stop running.\n'
                   'Please start the fitter and try again.')
            break
        i += 1


## find USB port for equipment: Mac, Windows, Linux
# Alicat flow control
port_ali = 'COM7'  ## '/dev/tty.usbserial-A908UXOQ'
def alicat_fc():
    # flow_controller1 = FlowController(port=port_ali, address='A')
    # flow_controller2 = FlowController(port=port_ali, address='B')
    # flow_controller3 = FlowController(port=port_ali, address='C')

    # flow_controller4 = FlowController(port=port_ali, address='D')
    # flow_controller5 = FlowController(port=port_ali, address='E')
    flow_controller6 = FlowController(port=port_ali, address='F')

    flow_controller7 = FlowController(port=port_ali, address='G')
    flow_controller8 = FlowController(port=port_ali, address='H')
    flow_controller9 = FlowController(port=port_ali, address='I')

    # print(flow_controller1.get())  ## need get, Bose AE2 soundlink will connect too
    # print(flow_controller2.get())
    # print(flow_controller3.get())
    # print(flow_controller4.get())
    # print(flow_controller5.get())
    print(flow_controller6.get())
    print(flow_controller7.get())
    print(flow_controller8.get())
    print(flow_controller9.get())


    # fc1 = flow_controller1.get()
    # fc2 = flow_controller2.get()
    # print(fc1['pressure'])
    # print(fc1['temperature'])
    # print(fc1['mass_flow'])
    # print(fc1['setpoint'])
    # print(fc2['pressure'])
    # print(fc2['temperature'])
    # print(fc2['mass_flow'])
    # print(fc2['setpoint'])

    # flow_controller1.close()
    # flow_controller2.close()
    # flow_controller3.close()
    # flow_controller4.close()
    # flow_controller5.close()
    flow_controller6.close()
    flow_controller7.close()
    flow_controller8.close()
    flow_controller9.close()
    print ("connections closed")

# US Solid Scale
port_so = '/dev/cu.usbserial-14310'   ##'COM4'
def ussolid():
    serialPort = serial.Serial(port= port_so, baudrate=1200,
                               bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    serialString = ""  # Used to hold data coming over UART
    while (1):
        # Wait until there is data waiting in the serial buffer
        if serialPort.in_waiting > 0:
            time.sleep(2)
            # Read data out of the buffer until a carraige return / new line is found
            serialString = serialPort.readline()
            # print(serialString.decode('Ascii'))   ## windows
            # print(len(serialString))
            weight = serialString.decode("utf-8")   ## Mac
            print(float(weight[5:12]))

# Mettler Toledo Scale: USB-A works on Windows, not Mac; RS232 does not work
# port_mt = '/dev/cu.usbserial-14420'  ## Mac
def mt_serial():
    serialPort = serial.Serial(port= 'COM4', baudrate=9600,
                               bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
    serialString = ""  # Used to hold data coming over UART
    while (1):
        # Wait until there is data waiting in the serial buffer
        # serialPort.write(b'W\r\n')
        # if serialPort.in_waiting > 0:
        if 1:
            time.sleep(2)
            # Read data out of the buffer until a carraige return / new line is found
            serialString = serialPort.readline()
            print(serialString)

## Mettler Toledo Scale    range 120g - 0.01 mg
BUFFER_SIZE = 1024
def mt_ethernet():
    try:
        s = socket.create_connection((MT_IP, MT_PORT), 5)  # only try 5s time out
        s.settimeout(2)
        print('Mettler Toledo Scale connected')
        # s.send('I0\r\n'.encode())
        # s.send(b'T\r\n')   #Tare, must >0
        # s.send(b'Z\r\n')   # Zero

        try:
            print(s.recv(BUFFER_SIZE))
            print('Mettler Toledo scale is ready.')
        except:
            print('Wake up the Mettler Toledo scale')
            s.send(b'@\r\n')     # Wake up scale
            k = s.recv(BUFFER_SIZE)  #= clear buffer
            # time.sleep(1)

        for i in range(10):
            k = s.recv(BUFFER_SIZE)
            # print(k)
            k = k.decode("utf-8")
            # print(k)
            k1 = round(float(k[3:15]), 5)
            print(k1)
        s.close()

    except:
        print('Mettler Toledo scale not connected to internet.')


if __name__ == "__main__":
    ## analyzer backdoor and listener test
    # anl_backdoor()
    # anl_listener()

    ## alicat flow control
    alicat_fc()

    ## US Solid scale
    # ussolid()

    ## Mettler Toledo scale
    # mt_serial()     #USB-A cable only works on Windows
    # mt_ethernet()   # use ethernet cable to connect




