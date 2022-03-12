"""
Created on Thr 2021/12/15
@author: Yilin
"""

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap
from PyQt6.QtGui import QFont
from PyQt6.QtCore import QTimer
from alicat import FlowController

import CmdFIFO_py3 as CmdFIFO

port = 50070
ipadd = 'http://1022.corp.picarro.com'
# MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"http://localhost:{port}", "test_connection", IsDontCareConnection=False)
MeasSystem = CmdFIFO.CmdFIFOServerProxy(f"{ipadd}:{port}", "test_connection", IsDontCareConnection=False)
print(MeasSystem.GetStates())

## on Linux computer, default port
# flow_controller1 = FlowController(address = 'A')   #port='/dev/ttyUSB0',
# flow_controller2 = FlowController(address = 'C')
## on Windows computer, check device manager and see port number COM?
# flow_controller1 = FlowController(port='COM4', address='A')
flow_controller1 = FlowController(port='/dev/tty.usbserial-A908UXOQ', address='A')
flow_controller2 = FlowController(port='/dev/tty.usbserial-A908UXOQ', address='C')
print(flow_controller1.get())
print(flow_controller2.get())
rt = 2000  ##ms, refresh time

# import serial
import serial.tools.list_ports as ls
print([p.device for p in ls.comports()])


exit()

class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Master Flower Control - Alicat")
        self.setGeometry(100,150,400,400)
        self.UI()

    def UI(self):
        mainLayout=QVBoxLayout() ##h, v both OK, because only 1 tab
        self.tabs =QTabWidget()
        self.tab1=QWidget()
        self.tab2=QWidget()        
        self.tabs.addTab(self.tab1,"Experiment Settings")
        self.tabs.addTab(self.tab2,"Instrument Settings")
        
        ###################Widgets###############
        self.L11=QVBoxLayout()
        self.L12 = QVBoxLayout()
        self.L13 = QHBoxLayout()
        self.L11.addLayout(self.L12, 60)
        self.L11.addLayout(self.L13, 40)
        self.tab1.setLayout(self.L11)

        i=0
        temp = ['14.9', '29', '1', '1', '14.9', '29', '50', '50', '0', '0', '0']

        #### MFC1 ######
        self.lb10=QLabel("MFC1: 1, Dilution line")
        self.lb11=QLabel("Pressure (psi)")
        self.lb11a=QLabel(' ')
        self.e11 = QLineEdit(temp[i])
        self.e11.setDisabled(True)
        self.b11=QPushButton("Change")
        self.b11.clicked.connect(self.func11)
        self.b11.setEnabled(False)
        i +=1

        self.lb12=QLabel("Temperature (C)")
        self.lb12a=QLabel(' ')
        self.e12 = QLineEdit(temp[i])
        self.e12.setDisabled(True)
        i +=1

        self.lb13=QLabel("Mass Flow (sccm)")
        self.lb13a=QLabel(' ')
        self.lb13a.setFixedWidth(50)
        self.e13 = QLineEdit(temp[i])
        self.b13=QPushButton("Change")        
        self.b13.clicked.connect(self.func13) 
        self.b13.setEnabled(False)   
        i +=1

        self.lb14=QLabel("Set Point (sccm)")
        self.lb14a=QLabel(' ')
        self.e14 = QLineEdit(temp[i])
        self.e14.setDisabled(True)
        self.b14=QPushButton("Change")      
        self.b14.clicked.connect(self.func14)  
        self.b14.setEnabled(False)
        i +=1

        self.lb15=QLabel(' ')
        self.lb16=QLabel(' ')
        self.lb17=QLabel(' ')
        self.lb18=QLabel(' ')

        #### MFC2 #######
        self.lb20=QLabel("MFC2: 50, Bubble Line")
        self.lb21=QLabel("Pressure (psi)")
        self.lb21a=QLabel(' ')
        self.e21 = QLineEdit(temp[i])
        self.e21.setDisabled(True)
        self.b21=QPushButton("Change")
        self.b21.clicked.connect(self.func21)
        self.b21.setEnabled(False)
        i +=1

        self.lb22=QLabel("Temperature (C)")
        self.lb22a=QLabel(' ')
        self.e22 = QLineEdit(temp[i])
        self.e22.setDisabled(True)
        i +=1

        self.lb23=QLabel("Mass Flow (sccm)")
        self.lb23a=QLabel(' ')
        #self.e23 = QLineEdit(temp[i])

        self.e23 = QComboBox()
        self.e23.addItems(["50", "20", "80", "100"])
        self.e23.setEditable(True)
        self.b23=QPushButton("Change", self)        
        self.b23.clicked.connect(self.func23)    
        i +=1

        self.lb24=QLabel("Set Point (sccm)")
        self.lb24a=QLabel(' ')
        self.e24 = QLineEdit(temp[i])
        self.e24.setDisabled(True)
        self.b24=QPushButton("Change")      
        self.b24.clicked.connect(self.func24)  
        self.b24.setEnabled(False)
        i +=1

        self.lb99=QLabel(' ')
        self.lb99.setStyleSheet("background-color: lightgrey")

        self.g11 = QGridLayout()
        self.g11.addWidget(self.lb10,  0, 0, 1, 2)
        self.g11.addWidget(self.lb11,  1, 0)
        self.g11.addWidget(self.lb11a, 1, 2)
        self.g11.addWidget(self.e11,   1, 4)
        self.g11.addWidget(self.b11,   1, 5)

        self.g11.addWidget(self.lb12,  2, 0)
        self.g11.addWidget(self.lb12a, 2, 2)
        self.g11.addWidget(self.e12,   2, 4)

        self.g11.addWidget(self.lb13,  3, 0)
        self.g11.addWidget(self.lb13a, 3, 2)
        self.g11.addWidget(self.e13,   3, 4)
        self.g11.addWidget(self.b13,   3, 5)

        self.g11.addWidget(self.lb14,  4, 0)
        self.g11.addWidget(self.lb14a, 4, 2)
        self.g11.addWidget(self.e14,   4, 4)
        self.g11.addWidget(self.b14,   4, 5)
        self.g11.addWidget(self.lb15,  5, 0)
        self.g11.addWidget(self.lb16,  5, 1)
        self.g11.addWidget(self.lb17,  5, 3)


        self.g11.addWidget(self.lb20,  11, 0, 1, 2)
        self.g11.addWidget(self.lb21,  12, 0)
        self.g11.addWidget(self.lb21a, 12, 2)
        self.g11.addWidget(self.e21,   12, 4)
        self.g11.addWidget(self.b21,   12, 5)

        self.g11.addWidget(self.lb22,  13, 0)
        self.g11.addWidget(self.lb22a, 13, 2)
        self.g11.addWidget(self.e22,   13, 4)

        self.g11.addWidget(self.lb23,  14, 0)
        self.g11.addWidget(self.lb23a, 14, 2)
        self.g11.addWidget(self.e23,   14, 4)
        self.g11.addWidget(self.b23,   14, 5)

        self.g11.addWidget(self.lb24,  15, 0)
        self.g11.addWidget(self.lb24a, 15, 2)
        self.g11.addWidget(self.e24,   15, 4)
        self.g11.addWidget(self.b24,   15, 5)
        self.g11.addWidget(self.lb18,  16, 0)
        self.g11.addWidget(self.lb99,  17, 0, 1, 4)

        self.L12.addLayout(self.g11)


        self.b1=QPushButton("Start Measurement", self)
        self.b1.clicked.connect(self.func1)
        self.b2=QPushButton("Stop Flow", self)
        self.b2.clicked.connect(self.func2)
        self.b3=QPushButton("Close")
        self.b3.clicked.connect(self.close)
        self.L13.addWidget(self.b1)
        self.L13.addWidget(self.b2)
        self.L13.addWidget(self.b3)

        self.timer=QTimer()
        self.timer.setInterval(rt)
        self.timer.timeout.connect(self.refresh_label)


        mainLayout.addWidget(self.tabs)
        self.setLayout(mainLayout)

        self.show()


    def refresh_label(self):
        fc1 = flow_controller1.get()
        fc2 = flow_controller2.get()
        #print ('MFC1: %.3f | MFC2: %.3f' % (fc1['mass_flow'], fc2['mass_flow']))

        ## sent measurement data on Alicat to Picarro fitting software
        MeasSystem.Backdoor.SetData('MFC1_P_amb',  fc1['pressure'])
        MeasSystem.Backdoor.SetData('MFC1_flow',   fc1['mass_flow'])
        MeasSystem.Backdoor.SetData('MFC1_flowset',fc1['setpoint'])

        MeasSystem.Backdoor.SetData('MFC2_P_amb',  fc2['pressure'])
        MeasSystem.Backdoor.SetData('MFC2_T_amb',  fc2['temperature'])
        MeasSystem.Backdoor.SetData('MFC2_flow',   fc2['mass_flow'])
        MeasSystem.Backdoor.SetData('MFC2_flowset',fc2['setpoint'])


        self.lb11a.setText(str(fc1['pressure']))
        self.lb12a.setText(str(fc1['temperature']))
        self.lb13a.setText(str(fc1['mass_flow']))
        self.lb14a.setText(str(fc1['setpoint']))

        self.lb21a.setText(str(fc2['pressure']))
        self.lb22a.setText(str(fc2['temperature']))
        self.lb23a.setText(str(fc2['mass_flow']))
        self.lb24a.setText(str(fc2['setpoint']))
        

    def func11(self):
        self.lb99.setText("Button is active")

    def func13(self):
        self.lb99.setText("Button is active")

    def func14(self):
        self.lb99.setText("Button is active")

    def func21(self):
        self.lb99.setText("Button is active")

    def func23(self):
        try:       
            F2 = int(self.e23.currentText())    #bubbler line
            F1 = 1-F2/1000               #dilution
            flow_controller1.set_flow_rate(flow=F1)
            flow_controller2.set_flow_rate(flow=F2)
            #MeasSystem.Backdoor.SetData('my_var',F2)   ### test variable
              
            self.e13.setText(str(F1))
            self.lb99.setText('Bubble line set to ' + str(F2))

        except:
            self.lb99.setText('Unable to set value.')


    def func24(self):
        self.lb99.setText("Button is active")


    def func1(self):
        self.b1.setEnabled(False)
        self.timer.start()
    

    def func2(self):
        try:       
            F2 = 0    #bubbler line
            F1 = 1-F2/1000 #dilution
            flow_controller1.set_flow_rate(flow=F1)
            flow_controller2.set_flow_rate(flow=F2)
            #MeasSystem.Backdoor.SetData('my_var',F2)   ### test variable
              
            self.e13.setText(str(F1))
            self.e23.setCurrentText(str(F2))
            self.lb99.setText('Bubble line stopped.')

        except:
            self.lb99.setText('Unable to set value.')


def main():
    app=QApplication(sys.argv)
    window = Window()
    window.show()
    app.exec()

if __name__=='__main__':
    main()









