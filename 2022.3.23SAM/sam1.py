import os.path
import time
import pandas as pd
import numpy as np
import sys

# df1 = pd.read_csv('sam1.csv')
# # print(df.head())
# tc = df1.iloc[:, 0]  # first column is time, s
# df = df1.iloc[:, 1:]  #remove first column
# nr = df.shape[0]   #row number
# nc = df.shape[1]   #column number

from alicat import FlowController     # pip install alicat

port_ali = 'COM7'
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

def alicat_fc(fn, port_ali):
    df = pd.read_csv(fn+'.csv')
    # print(df.head())
    tc = df.iloc[:, 0]  # first column is time, s
    nr = df.shape[0]  # row number
    nc = df.shape[1]  # column number

    df1 = df.iloc[:, 1:]  # remove first column


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

    # all Alicat for SAM
    # board = [fc1, fc2, fc3, fc4, fc5, fc6, fc7, fc8, fc9, fc10]
    board = [fc1, fc1, fc2, fc3, fc4, fc5, fc6, fc7, fc8, fc9, fc10]

    ## set flow rate
    for i in range(nr):   #go row by row
        t = int(tc[i])  #tc is string
        row = list(df.iloc[i])
        print('t, row,')
        print(t, row)

        # for j in [1, 2, 3, 4, 5, 7, 8, 10]:  #only 8 Alicat available
        # # for j in range(nc):
        #     board[j].set_flow_rate(row[j])

        fc1.set_flow_rate(row[1])
        fc2.set_flow_rate(row[2]/50)
        fc3.set_flow_rate(row[3])
        fc4.set_flow_rate(row[4]/50)
        fc5.set_flow_rate(row[5]*10)
        # fc6.set_flow_rate(row[6])
        fc7.set_flow_rate(row[7])
        fc8.set_flow_rate(row[8])
        # fc9.set_flow_rate(row[9])
        fc10.set_flow_rate(row[10])

        time.sleep(t)

        # send data
        for j in [1, 2, 3, 4, 5, 7, 8, 10]:
        # for j in range(nc):
            print(board[j].get())



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


    fc1.close()
    fc2.close()
    fc3.close()
    fc4.close()
    fc5.close()
    fc6.close()
    fc7.close()
    fc8.close()
    fc9.close()
    fc10.close()
    print ("connections closed")

if __name__ == "__main__":
    fn = 'sam1'  ## csv file
    port_ali = 'COM7'  ## '/dev/tty.usbserial-A908UXOQ'

    if not os.path.isfile(fn+'.csv'):
        print('Could not find file %s.csv'%flowtime)
    else:
        t1 = time.time()
        alicat_fc(fn, port_ali)
        print(time.time()-t1)

