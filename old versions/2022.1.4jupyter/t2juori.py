## original jupyter notebook translation

from random import randint
from matplotlib.animation import FuncAnimation

import sys
sys.path.append('../code/Rella-Python-master')      ## DataUtilities3
sys.path.append('../code/voc-fitter-develop/src')   ## voc_fitter

import numpy as np
import os
import shutil
from pathlib import Path

# os.environ['LOLOGGER_SERVERLESS'] = "1"

import time
from datetime import datetime
import DataUtilities3.RellaColor as RC
import timestamp_from_host as timestamp  ## ?????
import DataUtilities3.MPL_rella as RMPL
import DataUtilities3.load_files_rella as LF
import matplotlib.pyplot as plt

## copied from voc_fitter
import database

# from voc_fitter.model.library import database
# from voc_fitter.spectral_logger import SpectralLogReader as slog
# from pprint import pprint      ## ??????

spec_lib = database.SpectralDatabase(verbose=True).MDB.db
spec_lib.list_collection_names()

print(spec_lib)
print(spec_lib.list_collection_names())
# exit()

def h(name):
    j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
    return dat[:, j]

def timestamp_to_julian(tstamp):    # #no use
    U = timestamp.timestampToLocalDatetime(tstamp)
    U0 = datetime(U.year, 1, 1)
    doy = (U - U0).total_seconds() / 3600 / 24
    julian_day = doy + 1
    return julian_day

def epochTime_to_julian(epoch_time):    ## no use
    tstamp = timestamp.unixTimeToTimestamp(epoch_time)
    return timestamp_to_julian(tstamp)


def datestdtojd(stddate):
    fmt = '%Y%m%d %H:%M'
    sdtdate = datetime.strptime(stddate, fmt)
    sdtdate = sdtdate.timetuple()
    jdate = sdtdate.tm_yday + sdtdate.tm_hour / 24 + sdtdate.tm_min / (24 * 60)
    return (jdate)


RMPL.SetTheme('FIVE')
color4 = RC.Tetrad(primary=1, useRGY=True)

# fname = r'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'        ##Linux
fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'    ##Mac

gas = '176 - Acetic Acid'
cid = 176
date = '20211124a'
gas_name = 'broadband_gasConcs_' + str(cid)
spline_name = 'broadband_splineconc_' + str(cid)
volume = 10/1000 #droplet in mL
weight = 0.0090 #g
startTime = '20211124 08:00'
endTime = '20211124 23:59'
thing = ''

#
# ##unzip .h5 files
# rdfDIR = os.path.join(fname, gas, date, 'RDFs')
# privateDIR = os.path.join(fname, gas, date, 'PrivateData')
#
# # Unzip files
# if not os.path.exists(os.path.join(rdfDIR, 'unpackedFiles')):
#     LF.unpackZipArchives(rdfDIR)
# if not os.path.exists(os.path.join(privateDIR, 'unpackedFiles')):
#     LF.unpackZipArchives(privateDIR)
#
# privateDIR2 = os.path.join(privateDIR, 'unpackedFiles')
#
# if os.path.exists(privateDIR2):
#     private_new = os.path.join(privateDIR, 'private')
#     broadband_new = os.path.join(privateDIR, 'broadband')
#     if not os.path.exists(private_new):
#         os.mkdir(private_new)
#
#         if not os.path.exists(broadband_new):
#             os.mkdir(broadband_new)
#
#             for f in os.listdir(privateDIR2):
#                 if 'VOC_broadband' in f:
#                     shutil.move(os.path.join(privateDIR2, f), os.path.join(privateDIR, 'broadband'))
#                 elif 'DataLog_Private' in f:
#                     shutil.move(os.path.join(privateDIR2, f), os.path.join(privateDIR, 'private'))


privateDIR = os.path.join(fname, gas, date, 'PrivateData', 'private')
broadbandDIR = os.path.join(fname, gas, date, 'PrivateData', 'broadband')
log_path = os.path.join(fname, gas, date, 'ComboResults')
saveDIR = os.path.join(fname, gas, date)
saver = RMPL.SaveFigure(DIR=saveDIR).savefig

# NMP
density = 1.05
MW = 60.052

mol_beaker = volume * density / MW  # mL*(g/mL)/(g/mol)
mol_beaker_wt = weight / MW


## box2
Cal = spec_lib.EmpiricalSpectra.find_one({'cid':cid, 'version':2, 'pNominal':140})
# print(Cal)
# # pprint(Cal)
# pprint(Cal['calibration'])
print(Cal['calibration'])
# exit()

## box3
set_cal = Cal['calibration']['20210331']['concentration']
# set_cal*1e6

## box
#load broadband logs
DIR = broadbandDIR
ht, dat = LF.loadFilesH5(DIR, N = -1)

T_bb2 = h('JULIAN_DAYS')

das_temp2 = h('DasTemp')
cal_gas2 = h(gas_name)*1e6
ch42 = h('broadband_gasConcs_297')*1e6
co22 = h('broadband_gasConcs_280')*1e6
h2o2 = h('broadband_gasConcs_962')*1e6
set_cal2 = h(spline_name)*1e6

MFC1_2 = h('MFC1_flow')*1000.0
MFC2_2 = h('MFC2_flow')

f_tot = 1000

## box
#### find zero

shift = 0.   #-60
startdate = datestdtojd(startTime) + shift/(24*60)
enddate = datestdtojd(endTime) + shift/(24*60)

indices = np.where(T_bb2 > startdate)

T_bb = []
das_temp = []
cal_gas = []
ch4 = []
co2 = []
h2o = []
MFC1 = []
MFC2 = []

T_bb = T_bb2[indices]
das_temp = das_temp2[indices]
cal_gas = cal_gas2[indices]
ch4 = ch42[indices]
co2 = co22[indices]
h2o = h2o2[indices]
MFC1 = MFC1_2[indices]
MFC2 = MFC2_2[indices]
set_cal = set_cal2[indices]

indices2 = np.where(T_bb < enddate)

T_bb = T_bb[indices2]
das_temp = das_temp[indices2]
cal_gas = cal_gas[indices2]
ch4 = ch4[indices2]
co2 = co2[indices2]
h2o = h2o[indices2]
MFC1 = MFC1[indices2]
MFC2 = MFC2[indices2]
set_cal = np.mean(set_cal[indices2])*1e-6

first = T_bb[0]
T_bb -= first

T = T_bb*24*60
cal_max = max(cal_gas)
cal_index = [i for i, p in enumerate(cal_gas) if (p > cal_max*0.01)]

zero1 = [i for i, p in enumerate(cal_gas) if (abs(p) < cal_max*0.03 and T[i]< T[cal_index[0]] and cal_gas[i] != 0)]
zero2 = [i for i, p in enumerate(cal_gas) if (abs(p) < cal_max*0.03 and T[i]> T[cal_index[-1]] and cal_gas[i] != 0)]

zero1 = zero1[0:-35]
if len(zero1)==0:
    zero1 = [0]
zero = np.mean(cal_gas[zero1])
T_start = T[cal_index[0]]
T_end = T[cal_index[-1]]
T_pulse = (T_end - T_start)
print(T_pulse)

## box
# zero, len(zero1),set_cal

## box
[A1,A2], F = RMPL.MakerCal(size = (10,8), N = 2) # this sets up a new plot that can be displayed and later saved
A1.plot(T[zero1],cal_gas[zero1], label = gas, color = RMPL.dkgreen)
A1.plot([T[0], T[zero1[-1]]], [np.mean(cal_gas[zero1]),np.mean(cal_gas[zero1])], label = 'mean', color = RMPL.ltgreen)
A1.legend(loc=0, fontsize=12)
A1.set_xlabel('time [Minutes]', fontsize=14)
A1.set_ylabel('cal gas [ppm]', fontsize=14)

A2.plot(T[cal_index],cal_gas[cal_index], label = (RMPL.MATH % '%s' %gas) +  '\nlength of pulse %.2f minutes' % (T_pulse))
A2.legend(loc=0, fontsize=12)
A2.set_xlabel('time [Minutes]', fontsize=14)
A2.set_ylabel('cal gas [ppm]', fontsize=14)
A2.set_xlim(T[cal_index[0]], T[cal_index[-1]])

saver(F, date +'timeline_droplet'+thing)

[A1,A2], F = RMPL.MakerCal(size = (10,8), N = 2) # this sets up a new plot that can be displayed and later saved
A1.plot(T[zero1],ch4[zero1], label = 'CH4', color = RMPL.dkred)
A3 = A1.twinx()
A3.plot(T[zero1],h2o[zero1], label = 'H2O', color = RMPL.dkblue)
A1.legend(loc=2, fontsize=12)
A3.legend(loc=1, fontsize=12)

A1.set_xlabel('time [Minutes]', fontsize=14)
A1.set_ylabel('CH4 [ppm]', fontsize=14)
A3.set_ylabel('H2O [ppm]', fontsize=14)

A2.plot(T[cal_index],ch4[cal_index], label = 'CH4',color = RMPL.dkred)
A4 = A2.twinx()
A4.plot(T[cal_index],h2o[cal_index], label = 'H2O',color = RMPL.dkblue)
A2.legend(loc=2, fontsize=12)
A4.legend(loc=1, fontsize=12)
A2.set_xlabel('time [Minutes]', fontsize=14)
A2.set_ylabel('CH4 [ppm]', fontsize=14)
A4.set_ylabel('H2O [ppm]', fontsize=14)
A2.set_xlim(T[cal_index[0]], T[cal_index[-1]])

saver(F, date +'timeline_ambient'+thing)

## box
A1, F = RMPL.Maker() # this sets up a new plot that can be displayed and later saved
A1.plot(T,MFC1, label = 'Dilution', color = RMPL.dkgreen)
A1.set_xlabel('time [Minutes]', fontsize=14)
A1.set_ylabel('Dilution,pump (sccm)', fontsize=14, color = RMPL.dkgreen)
A3 = A1.twinx()
A3.plot(T,MFC2,label = 'Beaker',color = RMPL.dkblue )
A3.set_ylabel('beaker (sccm)', fontsize=14, color = RMPL.dkblue)
# A1.set_xlim(T[cal_index[0]], T[cal_index[-1]])

saver(F, date +'Flowrates'+thing)

## box
zero_array=[0] #Zeros from 20210420 and elevated signal from 20210421
zero_array[0] = zero
print(zero_array)
cal = []

## box
for i, p in enumerate(zero_array):
    Y = cal_gas - p

    S = [0.0]
    S2 = [0.0]
    DT = [T[1] - T[0]]
    s = 0.0
    s2 = 0.0

    for i in range(len(T) - 1):
        flow_tot = MFC1[i] + MFC2[i]  # sccm
        mflow_tot = flow_tot / 24455  # 22400 #mol/min #24466
        dt = T[i + 1] - T[i]
        dY = 0.5 * (Y[i + 1] + Y[i])
        dY2 = 0.5 * (h2o[i + 1] + h2o[i])
        moles = dY * mflow_tot * dt
        moles2 = dY2 * mflow_tot * dt
        s += moles  # micromoles
        s2 += moles2  # micromoles
        S.append(s)
        s2 += moles2  # micromoles
        S2.append(s2)
        DT.append(dt)

    S = np.array(S)
    S2 = np.array(S2)
    DT = np.array(DT)

    if weight == 0.0:
        cal_factor = (mol_beaker) / (S[-1]) * 1E6

    else:
        cal_factor = (mol_beaker_wt) / (S[-1]) * 1E6
    cal.append(cal_factor * set_cal * 1e6)

print(cal)    #### this is!
exit()


## box: Create plots for data
#Integrated droplet
A, F = RMPL.Maker(grid=(2,1), size=(10,8))
A[0].plot(T, Y, c = color4[0], lw = 2, label = RMPL.MATH % 'evaporated \ %s' %gas)
A[1].plot(T, S, c = color4[1], lw = 2, label = (RMPL.MATH % 'integrated \ %s \ signal' %gas) +  ' [%.2f]' % (S[-1]))
A[0].set_title(RMPL.MATH % ('Droplet \ Calibration \ of \ %s ' %gas) + '- cal = %.3f' %cal[0], fontsize = 16)
for a in A:
    a.legend(loc = 'best', fontsize = 12)
A[0].set_xticklabels([])
A[1].set_xlabel('time [Minutes]', fontsize = 14)
A[0].set_ylabel(RMPL.MATH % ' Sample \ [ppm]', fontsize = 14)
A[1].set_ylabel(RMPL.MATH % ' Sample \ [\mu moles]', fontsize = 14)
F.show()
F.tight_layout()
saver(F,date +'DropletCal', dpi = 400)








