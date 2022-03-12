
from random import randint

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# a = [1,2,3,2,5]
# print(a[-1])

# f = open('j1.txt', 'r')
# temp = f.read().splitlines()
# print(temp[0])
# exit()

fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/j1.txt'
# fname = 'smb://10.100.1.172/Data/j1.txt'

with open(fname, 'r') as fp:
    temp = fp.read().splitlines()
    print(temp[0])

    # for line in fp:
    #     print (line)

exit()



# gas = '176 - Acetic Acid'
# cid = 176
# date = '20211124'
# gas_name = 'broadband_gasConcs_' + str(cid)
# spline_name = 'broadband_splineconc_' + str(cid)
# volume = 10/1000 #droplet in mL
# weight = 0.0090 #g
# startTime = '20211124 08:00'
# endTime = '20211124 23:59'
# thing = ''
#
# ##unzip .h5 files
# rdfDIR = os.path.join(fname, gas, date, 'RDFs')
# privateDIR = os.path.join(fname, gas, date, 'PrivateData')





