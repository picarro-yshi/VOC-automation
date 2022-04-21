import time

import pandas as pd
import numpy as np
import sys

from alicat import FlowController     # pip install alicat

# Alicat flow control
port_ali = 'COM7'  ## '/dev/tty.usbserial-A908UXOQ'
fc1 = FlowController(port=port_ali, address='A')
fc1.set_flow_rate(0.85)
print(fc1.get())
exit()

def alicat_fc():
    # fc1 = FlowController(port=port_ali, address='A')
    # fc2 = FlowController(port=port_ali, address='B')
    # fc3 = FlowController(port=port_ali, address='C')
    # fc4 = FlowController(port=port_ali, address='D')
    # fc5 = FlowController(port=port_ali, address='E')

    fc6 = FlowController(port=port_ali, address='F')
    fc7 = FlowController(port=port_ali, address='G')
    fc8 = FlowController(port=port_ali, address='H')
    fc9 = FlowController(port=port_ali, address='I')
    # fc10 = FlowController(port=port_ali, address='J')

    board = [fc1, fc2, fc3, fc4, fc5, fc6, fc7, fc8, fc9, fc10]

    # flow_controller1.set_flow_rate(flow=F1)
    for t in tc:
        ## set flow rate
        for i in range(nr):   #go row by row
            row = df.iloc[i]
            for j in range(nc):
                board[j].set_flow_rate(row[j])
        time.sleep(t)

        # send data
        for i in range(nr):   #go row by row
            for j in range(nc):
                print(board[j].get())


    # print(fc1.get())  ## need get, Bose AE2 soundlink will connect too
    # print(fc2.get())
    # print(fc3.get())
    # print(fc4.get())
    # print(fc5.get())
    # print(fc6.get())
    # print(fc7.get())
    # print(fc8.get())
    # print(fc9.get())

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


    # fc1.close()
    # fc2.close()
    # fc3.close()
    # fc4.close()
    # fc5.close()
    fc6.close()
    fc7.close()
    fc8.close()
    fc9.close()
    # fc10.close()
    print ("connections closed")

if __name__ == "__main__":
    alicat_fc()

