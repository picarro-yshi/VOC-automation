## calibration factor for droplet experiment, adapted from jupyter notebook
## basic library
import sys
import numpy as np
import os
import shutil
import time
import datetime
import matplotlib.pyplot as plt
from zipfile import ZipFile
import h5py     #need by Windows
import tables   #need by windows

## customized files
# helperpath = '../code/Rella-Python/'    ## './' in same folder
# sys.path.append(helperpath)
import DataUtilities3.RellaColor as RC
import DataUtilities3.MPL_rella as RMPL
import DataUtilities3.load_files_rella as LF
from spectral_logger1 import SpectralLogReader as slog
import GoldenCalibrationUtilities as GCU

RMPL.SetTheme('FIVE')
color4 = RC.Tetrad(primary=1, useRGY=True)

## for unzip files
## copy files in selected time range:
def copyselec(fn, dst, epo1, epo3):  ## source and destination folder path, start and end time
    files = []
    tag = 0
    for f in os.listdir(fn):
        #print(f)
        t = os.path.getmtime(os.path.join(fn, f))
        files.append([f, int(t)])       ## list[string, int]
    files = sorted(files, key=lambda x: x[1])
    #print(files)

    for f in files:
        fname = os.path.join(fn, f[0])
        t = f[1]
        if t > epo1:
           shutil.copy2(fname, dst)   ## src, dst
           #print(f)
        if t > epo3:
            tag = t
            idx = files.index(f)
            break

    if ('combo' in fn) and tag !=0:     #extra step for combo log, time tag must exist
        for f in files[idx+1:]:         ##for files create in same minutes
            if f[1] == tag:
                fname = os.path.join(fn, f[0])
                shutil.copy2(fname, dst)   ## src, dst
                #print(f)
            else:
                break

## unzip file with original time stamp
def unzip(zipfile, outDirectory):
    dirs = {}
    with ZipFile(zipfile, 'r') as z:
        for f in z.infolist():
            z.extract(f, outDirectory)
            name = os.path.join(outDirectory, f.filename)
            # still need to adjust the dt o/w item will have the current dt
            # changes to dir dt will have no effect right now since files are
            # being created inside of it; hold the dt and apply it later
            date_time = time.mktime(f.date_time + (0, 0, -1))
            dirs[name] = date_time

    # done creating files, now update dir dt
    for name in dirs:
       date_time = dirs[name]
       os.utime(name, (date_time, date_time))


def uz_rdf(fnr, epo1, epo3):  # unzip RDF files
    t1 = time.time()
    print('Unzip RDF files...')

    ## RDF files location on analyzer:
    ## /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c/RDFs/home/picarro/I2000/Log/RDF
    # fnrr = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20220314t1b/RDFs/"
    fnrr = os.path.join(fnr, 'RDFs')
    tempfd = os.path.join(fnrr, 'tempfd')
    os.mkdir(tempfd)
    os.mkdir(os.path.join(fnrr, 'unpackedFiles'))
    # copyselec(fnar1, tempfd, epo1, epo3)  # move RDF zips to temp folder locally on analyzer
    for f in os.listdir(fnrr):
        if f.endswith('.zip'):
            # print(f)
            unzip(os.path.join(fnrr, f), tempfd)

    # fn1 = tempfd + '/home/picarro/I2000/Log/RDF'
    fn1 = os.path.join(tempfd, 'home')  # join one by one
    fn1 = os.path.join(fn1, 'picarro')
    fn1 = os.path.join(fn1, 'I2000')
    fn1 = os.path.join(fn1, 'Log')
    fn1 = os.path.join(fn1, 'RDF')
    copyselec(fn1, os.path.join(fnrr, 'unpackedFiles'), epo1, epo3 + 60)
    # move RDF unzipped from temp folder to unpack, last minute data

    shutil.rmtree(tempfd)  # delete temp folder
    print(time.time() - t1)
    print('RDF files unzipped and copied.')


def uz_p(fnr, epo1, epo3):   # unzip private files
    t1 = time.time()
    print('unzip private files')

    ## private files location on analyzer
    # /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/home/picarro/I2000/Log/DataLogger/DataLog_Private
    # fnrp = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/'
    fnrp = os.path.join(fnr, 'PrivateData')
    tempfd = os.path.join(fnrp, 'unpackedFiles')
    os.mkdir(tempfd)
    # copyselec(fnap1, tempfd, epo1, epo3)  # move RDF zips to temp folder, on analyzer
    for f in os.listdir(fnrp):
        if f.endswith('.zip'):
            # print(f)
            unzip(os.path.join(fnrp, f), tempfd)

    # fn2 = tempfd + 'home/picarro/I2000/Log/DataLogger/DataLog_Private'
    fn2 = os.path.join(tempfd, 'home')  # join one by one
    fn2 = os.path.join(fn2, 'picarro')
    fn2 = os.path.join(fn2, 'I2000')
    fn2 = os.path.join(fn2, 'Log')
    fn2 = os.path.join(fn2, 'DataLogger')
    fn2 = os.path.join(fn2, 'DataLog_Private')

    fn3 = os.path.join(fnrp, 'broadband')
    fn4 = os.path.join(fnrp, 'private')
    fn31 = os.path.join(fnrp, 'broadband1')  # separate to different catagories
    fn41 = os.path.join(fnrp, 'private1')

    ## move unziped files to folders
    os.mkdir(fn3)
    os.mkdir(fn4)
    os.mkdir(fn31)
    os.mkdir(fn41)

    for f in os.listdir(fn2):
        if 'NewFitter' in f:
            shutil.move(os.path.join(fn2, f), fn31)
        elif 'DataLog_Private' in f:
            shutil.move(os.path.join(fn2, f), fn41)
    copyselec(fn31, fn3, epo1, epo3 + 60)
    copyselec(fn41, fn4, epo1, epo3 + 60)
    shutil.rmtree(fn31)
    shutil.rmtree(fn41)
    print(time.time() - t1)
    print('Private files unzipped and copied.')


## all parameters must be valid before sending to below functions; no sanity check
# droplet
def jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row=500, showgraph=False, savefig=False):
    gas_name = 'broadband_gasConcs_' + str(cid)  ## broadband_gasConcs_176
    cal_name = 'broadband_eCompoundOutputs_'+ str(cid) +'_calibration' ## broadband_eCompoundOutputs_176_calibration
    # fnr = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c"

    ## epoch_time = datetime.datetime(2021,11,24,8,0).timestamp()
    ta = datetime.datetime(int(ta1[:4]), int(ta1[4:6]), int(ta1[-2:]),int(ta2),int(ta3)).timestamp()
    tb = datetime.datetime(int(tb1[:4]), int(tb1[4:6]), int(tb1[-2:]),int(tb2),int(tb3)).timestamp()
    tc = datetime.datetime(int(tc1[:4]), int(tc1[4:6]), int(tc1[-2:]),int(tc2),int(tc3)).timestamp()

    def h(name):
        j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
        return dat[:, j]

    ## check if still need to unzip
    # RDF files are optional
    # if not os.path.exists(os.path.join(fnr, 'RDFs', 'unpackedFiles')):
    #     uz_rdf(fnr, ta, tc)
    if not os.path.exists(os.path.join(fnr, 'PrivateData', 'unpackedFiles')):
        uz_p(fnr, ta, tc)
    # exit()

    ht, dat = LF.loadFilesH5(os.path.join(fnr, 'PrivateData', 'broadband'), N=-1)  ## headtag, data. all data in that range
    # print(ht)
    # exit()
    x1 = h('time')
    y1 = h(gas_name) * 1e6
    MFC11 = h('MFC1_flow')*1000.0
    MFC21 = h('MFC2_flow')

    idx = (x1 > ta) & (x1 < tc)   #write in 2 step cause error
    x = x1[idx]
    y = y1[idx]
    MFC1 = MFC11[idx]
    MFC2 = MFC21[idx]

    set_cal = h(cal_name)[0]  ## all value same
    print('cal value in lib')
    print(set_cal*1e6)

    idx2 = (x > ta) & (x < ta+1500) # 25min baseline
    baseline1 = y[idx2]
    # print(len(baseline1))

    zero1 = np.mean(baseline1)
    std1 = np.std(baseline1)
    print('zero1')
    print(zero1)
    print(std1)

    idxtb = np.where(abs(x-tb)<5)
    tbb = idxtb[0][-1] - 5*12  ## index 5 min before recorded sample adding time
    i = tbb
    slope = []
    gap = 10   # points, about 12 pts/min
    incr = 0
    decr = 0
    peaktime = 0

    while i < len(x)-gap:
        i+=gap
        x2 = x[i-gap: i]
        y2 = y[i-gap:i]
        coeffs = np.polyfit(x2, y2, 1)
        slope1 = coeffs[-2]    #slope of the previous #gap points
        slope.append(slope1)
        if slope1 > 0.01:
            incr = 1
            peaktime = i
        if incr and (slope1 < -0.01):
            decr = 1
        if incr and decr:
            if abs(slope1) < 0.001:
                break
    # plt.plot(slope)
    # plt.show()
    # print('peak time')
    # print(time.ctime(x[peaktime]))

    tcc = 0
    ## Find end time: zero 2 < zero1 + pct*sigma
    i += 100     #points
    while i < len(x):
        zero2 = np.mean(y[i-200: i])
        if zero2 < zero1 + std1*pct:  # baseline end here
            tcc = i  ## experiment end point
            break
        i += 50

    if tcc:
        print('calculation end time')
        print(time.ctime(x[tcc]))
    else:
        print('baseline still above mean+sigma')

    y0 = y[tbb:i]-zero1  ##truncated y, zero-ed
    xtruc = x[tbb:i]        ## truncated x in s
    x0 = (xtruc-xtruc[0])/60   ## in min,start from 0
    x3 = (x-x[0])/60
    # plt.plot(x0, y0)
    # plt.plot(x3, y)    ## raw plot
    # plt.show()
    MFC10=MFC1[tbb:i]
    MFC20=MFC2[tbb:i]

    ## integral under curve
    s = 0
    S = [0]
    for j in range(len(y0)-1):
        flow_tot = MFC10[j] + MFC20[j]  # sccm
        mflow_tot = flow_tot / 24455  # 22400 #mol/min #24466
        dt = x0[j + 1] - x0[j]
        dY = 0.5 * (y0[j + 1] + y0[j])
        moles = dY * mflow_tot * dt
        s += moles    # micromoles
        S.append(s)
    # print(S[-1])

    vol_in = float(weight) / float(MW)
    vol_ratio = vol_in / (S[-1]) * 1E6
    print('ratio')
    print(vol_ratio)
    cal = vol_ratio * set_cal * 1e6
    print('calibration factor')
    print(cal)     #### this is!
    fncal = os.path.join(fnr, 'par', 'calibration_factor.txt')
    if os.path.isfile(fncal):
        os.remove(fncal)
    with open(fncal, 'w') as f:
        f.write(str(cal))
    # exit()

    ########### plots #########
    ## flow control, use all data
    saver = RMPL.SaveFigure(DIR=fnr).savefig
    A1, F = RMPL.Maker()
    A1.plot(x3, MFC1, label='Dilution', color=RMPL.dkgreen)
    A1.set_xlabel('Time (minutes)', fontsize=14)
    A1.set_ylabel('Dilution,ZA (sccm)', fontsize=14, color=RMPL.dkgreen)
    A3 = A1.twinx()
    A3.plot(x3, MFC2, label='Beaker', color=RMPL.dkblue)
    A3.set_ylabel('Bubbler (sccm)', fontsize=14, color=RMPL.dkblue)
    # A1.set_xlim(T[cal_index[0]], T[cal_index[-1]])
    A1.set_title('Flow Rate')
    plt.show(block=False)
    F1 = F
    if savefig:
        saver(F, ta1 +'Flowrates')
    # exit()

    #Integrated droplet
    A, F = RMPL.Maker(grid=(2,1), size=(10,8))
    A[0].plot(x0, y0, c=color4[0], lw=2, label='Time series')
    A[1].plot(x0, S, c=color4[1], lw=2, label=('Integrated, total: %.2f' %S[-1]))
    A[0].set_title('Droplet Calibration: cal = %.3f\n%s' %(cal, gas), fontsize=16)
    for a in A:
        a.legend(loc='best', fontsize=12)
    A[0].set_xticklabels([])
    A[1].set_xlabel('Time (minutes)', fontsize=14)
    A[0].set_ylabel('Sample (ppm)', fontsize=14)
    A[1].set_ylabel('Sample (µ moles)', fontsize=14)
    F.tight_layout()
    plt.show(block=False)
    F2 = F
    if savefig:
        saver(F, ta1 + 'Integration', dpi=400)
    # exit()

    #Raw data
    A1, F = RMPL.Maker()
    # x = list(x)
    x_t = [x[0]]     # x data that will be marked
    xmak = [time.strftime('%H:%M', time.localtime(x[0]))]

    n= len(x)
    for i in range(1, n):
        clock0 = time.strftime('%M:%S', time.localtime(x[i-1]))
        clock =  time.strftime('%M:%S', time.localtime(x[i]))
        if (clock0[:2] == '29' and clock[:2]=='30') or (clock0[:2] == '59' and clock[:2]=='00'):
            x_t.append(x[i])
            xmak.append(time.strftime('%H:%M', time.localtime(x[i])))

    A1.plot(x, y, label=' %s (ppm)' % gas)
    A1.set_xticks(x_t, xmak)
    A1.set_ylabel('Conc. (ppm)', fontsize=14)
    A1.set_xlabel('Clock time', fontsize=14)
    A1.set_title('%s Raw Data\n%s'%(ta1,gas))
    plt.show(block=False)
    F3 = F
    if savefig:
        saver(F, ta1 + 'Raw')
    # exit()

    ### check if compound has the correct spectrum and RMSE
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    data = read.get_spectra_row('broadband', row, pull_results=True)
    nu = data[0]['nu']
    k = data[0]['absorbance']
    residuals = data[0]['residuals']
    partial_fit = data[0]['partial_fit']
    model = data[0]['model']
    big3 = data[0]['big3']
    kol_source = RC.KawaiiPunchyCute(brtValue=0)

    [A1, A2], F = RMPL.MakerCal(size=(10, 8), N=2)  # this sets up a new plot that can be displayed and later saved
    A1.plot(nu, k, label='data', color=kol_source.getNext(), alpha=0.75)
    A1.plot(nu, model, label='model', color=kol_source.getNext(), alpha=0.4)
    A1.legend(loc=0, fontsize=12)
    A1.set_ylabel('Absorbance', fontsize=14)
    A1.set_title('Combo Log Data Analysis')

    colorA2 = color = kol_source.getNext()
    A2.plot(nu, residuals, label='residuals', alpha=0.75, color=colorA2)
    A2.set_ylabel('Residuals', color=colorA2, fontsize=14)
    A4 = A2.twinx()
    colorA4 = color = kol_source.getNext()
    A4.plot(nu, partial_fit, label='partial fit', color=colorA4, alpha=0.75)
    A2.set_xlabel('nu (cm-1)', fontsize=14)
    A4.set_ylabel('Partial fit', color=colorA4, fontsize=14)
    A2.legend(loc=0, fontsize=12)
    # F.canvas.manager.set_window_title('Figure 4')  ## figure window title
    F4 = F
    if savefig:
        saver(F, ta1 + 'RawSpectraFit')
    plt.show(block=False)
    if showgraph:
        plt.waitforbuttonpress()  # press any key to close all plots
        plt.close()
    return F1, F2, F3, F4

## gas tank
def jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row=500, showgraph=False, savefig = False):
    gas_name = 'broadband_gasConcs_' + str(cid)  ## broadband_gasConcs_176
    cal_name = 'broadband_eCompoundOutputs_'+ str(cid) +'_calibration' ## broadband_eCompoundOutputs_176_calibration
    # fnr = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c"

    ## epoch_time = datetime.datetime(2021,11,24,8,0).timestamp()
    ta = datetime.datetime(int(ta1[:4]), int(ta1[4:6]), int(ta1[-2:]),int(ta2),int(ta3)).timestamp()
    tb = datetime.datetime(int(tb1[:4]), int(tb1[4:6]), int(tb1[-2:]),int(tb2),int(tb3)).timestamp() #not needed
    tc = datetime.datetime(int(tc1[:4]), int(tc1[4:6]), int(tc1[-2:]),int(tc2),int(tc3)).timestamp()

    def h(name):
        j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
        return dat[:, j]

    ## check if still need to unzip
    # if not os.path.exists(os.path.join(fnr, 'RDFs', 'unpackedFiles')):
    #     uz_rdf(fnr, ta, tc)   #RDF is optional
    if not os.path.exists(os.path.join(fnr, 'PrivateData', 'unpackedFiles')):
        uz_p(fnr, ta, tc)
    # exit()

    ht, dat = LF.loadFilesH5(os.path.join(fnr, 'PrivateData', 'broadband'), N=-1)  ## headtag, data. all data in that range
    # print(ht)
    # exit()
    x1 = h('time')
    y1 = h(gas_name) * 1e6

    idx = (x1 > ta+300) & (x1 < ta + 1560)  # zero1, 20 min
    x0 = x1[idx]
    start0 = x0[0]  # zero start epoch
    x0 = (x0 - x0[0]) / 60  # min, start at 0
    y0 = y1[idx]
    # print(len(x0))

    # idx = (x1 > tb + 600) & (x1 < tc)  # IPA, time to reach constant value, IPA=10min, acetic acid=1h
    # idx = (x1 > tb+60) & (x1 < tc)       # IPA, time during which values are constant
    idx = (x1 > tc-1800) & (x1 < tc)       # IPA, time during which values are constant
    x = x1[idx]
    start = x[0]  # IPA start epoch
    x = (x - x[0]) / 60  # min, start at 0
    y = y1[idx]
    # print(len(x))
    # exit()

    gap = 5  # in minutes, look at data in packages of 5 min
    set_conc = []
    yt = []  # ranged y in min
    data_std = []
    xt = []  # ranged x in min

    # zero
    x_pt = int((x0[-1] - x0[0]) / gap)  # x axis points
    for j in range(x_pt):
        indices = (x0 >= j * gap) & (x0 <= (j + 1) * gap)
        if True in indices:
            set_conc.append(0)
            data_std.append(np.std(y0[indices]))
            yt.append(np.mean(y0[indices]))
            xt.append(x0[indices][-1])

    # gas
    x_pt = int((x[-1] - x[0]) / gap)  # x axis point
    for j in range(x_pt):
        indices = (x >= j * gap) & (x <= (j + 1) * gap)
        if True in indices:
            set_conc.append(tank_conc)
            data_std.append(np.std(y[indices]))
            yt.append(np.mean(y[indices]))
            xt.append(x[indices][-1] + int((start - start0) / 60))

    xt = np.array(xt)
    yt = np.array(yt)
    data_std = np.array(data_std)
    set_conc = np.array(set_conc)

    set_cal = h(cal_name)[100] * 1e6  ## all value same
    print('cal value in lib')
    print(set_cal)
    # print(h(cal_name))

    extra_bit = 0.1 / 1000.0
    zero_error = data_std[np.argmin(yt)]
    units = 'ppm'

    xsim = np.arange(0, np.nanmax(set_conc), extra_bit)
    a = np.polyfit(set_conc, yt, 1.0)
    ysim = np.polyval(a, xsim)
    resids = yt - np.polyval(a, set_conc)
    kf = 3

    if np.all(data_std == 0):
        print('std 0')
        MDL = GCU.calcStuffWeighted(set_conc, yt, zero_error, resids, units=units, k=kf)
    else:
        print('std no 0')
        MDL = GCU.calcStuffWeighted_points(set_conc, yt, data_std, zero_error, units=units, k=kf)
        # (X, Y, point by point uncertainty, uncertainty at 0, unit, sigma)

    fit = set_conc * MDL[0] + MDL[1]
    print(MDL[-2])
    slope = a[0]
    intercept = a[1]
    MDL = MDL[-1]
    cal = set_cal / slope    #cal
    print('initial concentration/cal in library: %.4f ppm' % set_cal)
    if intercept >= 0:
        print('calibration: %.4f [actual] + %.4f' % (slope, intercept))
    else:
        print('calibration: %.4f [actual] - %.4f' % (slope, intercept))
    print('new concentration estimate: %.4f' % cal)

    fncal = os.path.join(fnr, 'par', 'calibration_factor.txt')
    if os.path.isfile(fncal):
        os.remove(fncal)
    with open(fncal, 'w') as f:
        f.write(str(cal))
    # exit()

    ########### plots #########
    ## Raw data
    saver = RMPL.SaveFigure(DIR=fnr).savefig
    A, F = RMPL.Maker()
    idx = (x1 > ta) & (x1 < tc)  # zero1, 30 min
    xtruc = list(x1[idx])
    ytruc = list(y1[idx])
    x_t = [xtruc[0]]     # xtruc data that will be marked
    xmak = [time.strftime('%H:%M', time.localtime(xtruc[0]))]

    n= len(xtruc)
    for i in range(1, n):
        clock0 = time.strftime('%M:%S', time.localtime(xtruc[i-1]))
        clock =  time.strftime('%M:%S', time.localtime(xtruc[i]))
        if (clock0[1] == '9' and clock[1]=='0'):
            x_t.append(xtruc[i])
            xmak.append(time.strftime('%H:%M', time.localtime(xtruc[i])))

    A.plot(xtruc, ytruc, label='Raw')
    A.set_xticks(x_t, xmak)
    A.legend()
    A.set_xlabel('Clock time')
    A.set_ylabel('Conc. (ppm)')
    A.set_title('%s Raw Data\n%s'%(ta1, gas))
    plt.show(block=False)
    F1 = F
    if savefig:
        saver(F, ta1 + 'Raw')
    # exit()

    ## Fitting plot
    A, F = RMPL.Maker()
    A.plot(xt, yt, label='Measurement')
    A.plot(xt, set_conc, '*', label='Tank Conc. from Airgas')
    A.legend()
    A.set_xlabel('Time (min)')
    A.set_ylabel('Conc. (ppm)')
    A.set_title('Gas Tank Calibration: cal = %.3f\n%s' %(cal, gas), fontsize=14)
    plt.show(block=False)
    F2 = F
    if savefig:
        saver(F, ta1 +'measured')
    # exit()

    ### check if compound has the correct spectrum and RMSE
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    data = read.get_spectra_row('broadband', row, pull_results=True)
    nu = data[0]['nu']
    k = data[0]['absorbance']
    residuals = data[0]['residuals']
    partial_fit = data[0]['partial_fit']
    model = data[0]['model']
    big3 = data[0]['big3']
    kol_source = RC.KawaiiPunchyCute(brtValue=0)

    [A1, A2], F = RMPL.MakerCal(size=(10, 8), N=2)  # this sets up a new plot that can be displayed and later saved
    A1.plot(nu, k, label='data', color=kol_source.getNext(), alpha=0.75)
    A1.plot(nu, model, label='model', color=kol_source.getNext(), alpha=0.4)
    A1.legend(loc=0, fontsize=12)
    A1.set_ylabel('Absorbance', fontsize=14)
    A1.set_title('Combo Log Data Analysis')

    colorA2 = kol_source.getNext()
    A2.plot(nu, residuals, label='residuals', alpha=0.75, color=colorA2)
    A2.set_ylabel('Residuals', color=colorA2, fontsize=14)
    A4 = A2.twinx()
    colorA4 = kol_source.getNext()
    A4.plot(nu, partial_fit, label='partial fit', color=colorA4, alpha=0.75)
    A2.set_xlabel('nu (cm-1)', fontsize=14)
    A4.set_ylabel('Partial fit', color=colorA4, fontsize=14)
    A2.legend(loc=0, fontsize=14)
    # F.canvas.manager.set_window_title('Figure 4')  ## figure window title
    F3 = F
    F4 = F
    if savefig:
        saver(F, ta1 + 'RawSpectraFit')
    plt.show(block=False)
    if showgraph:
        plt.waitforbuttonpress()  # press any key to close all plots
        plt.close()

    soni = 0 #Sandhya need the plot
    if soni:
        [A2, A1], F = RMPL.MakerCal(size=(10, 8), N=2)  # this sets up a new plot that can be displayed and later saved
        # colorA2 = kol_source.getNext()
        colorA2 = 'forestgreen'
        # A2.plot(nu, residuals, label='residuals', alpha=0.75, color=colorA2)
        # A2.set_ylabel('Residuals', color=colorA2, fontsize=14)
        A2.plot(nu, model, label='model', color=colorA2, alpha=0.75)
        A2.set_ylabel('Absorption (ppb/cm)', fontsize=14)
        # A1.plot(nu, model, label='model', color=kol_source.getNext(), alpha=0.4)
        # A4 = A2.twinx()
        # colorA4 = kol_source.getNext()
        colorA4 = 'k'
        A2.plot(nu, partial_fit, label='data', marker='.', markersize=2, color=colorA4, linewidth=0, alpha=0.75)
        # A2.set_xlabel('nu (cm-1)', fontsize=14)
        # A4.set_ylabel('Partial fit', color=colorA4, fontsize=14)
        A2.set_title('7946-Propylene glycol monomethyl ether acetate (PGMEA)', fontsize = 16)
        A2.legend(loc=0, fontsize=12)
        # A4.legend(loc=7, fontsize=12)
        # F.canvas.manager.set_window_title('Figure 4')  ## figure window title
        # F3 = F
        # F4 = F

        # A1.plot(nu, k, label='data', color=kol_source.getNext(), alpha=0.75)
        # A1.plot(nu, model, label='model', color=kol_source.getNext(), alpha=0.4)

        colorA1 = 'k'
        r1 = residuals
        # a = max(r1)
        # b = min(r1)
        # r2 = []
        # for i in r1:
        #     if i>=0:
        #         r2.append(i/a*10)
        #     else:
        #         r2.append(-i/b*10)

        A1.plot(nu, r1, label='Residuals', color=colorA1, alpha=0.4)
        # A1.legend(loc=0, fontsize=12)
        A1.set_ylabel('Residuals (ppb/cm)', color = colorA1, fontsize=14)
        # A1.set_title('Combo Log Data Analysis')
        A1.set_xlabel('Frequency (cm-1)', fontsize=14)
        plt.ylim(-10, 10)

        if savefig:
            saver(F, ta1 + 'RawSpectraFit')
        # plt.show(block=False)
        plt.show()
        # if showgraph:
        #     plt.waitforbuttonpress()  # press any key to close all plots
        #     plt.close()

    if soni: #time series
        saver = RMPL.SaveFigure(DIR=fnr).savefig
        A, F = RMPL.Maker()
        ta = datetime.datetime(2022,6,16,16,10).timestamp()
        tc = datetime.datetime(2022,6,16,16,31).timestamp()

        idx = (x1 > ta) & (x1 < tc)  # zero1, 30 min
        xtruc = list(x1[idx])
        ytruc = list(y1[idx]/3.6258)
        x_t = [xtruc[0]]  # xtruc data that will be marked
        xmak = [time.strftime('%H:%M', time.localtime(xtruc[0]))]

        n = len(xtruc)
        for i in range(1, n):
            clock0 = time.strftime('%M:%S', time.localtime(xtruc[i - 1]))
            clock = time.strftime('%M:%S', time.localtime(xtruc[i]))
            if (clock0[1] == '9' and clock[1] == '0') or (clock0[1] == '4' and clock[1] == '5'):
                x_t.append(xtruc[i])
                xmak.append(time.strftime('%H:%M', time.localtime(xtruc[i])))

        A.plot(xtruc, ytruc)
        A.set_xticks(x_t, xmak)
        # A.legend()
        A.set_xlabel('Clock time')
        A.set_ylabel('Conc. (ppm)')
        A.set_title(' Raw Data:\n' + gas)
        plt.ylim(0, 4)
        plt.show()
        # plt.show(block=False)
        # F1 = F
        # if savefig:
        #     saver(F, ta1 + 'Raw')


    return F1, F2, F3, F4


### find the correct row number for slog plots
## use animation to automatic scan
from matplotlib.animation import FuncAnimation
def findrowani(fnr, gas, row=None):
    viewtime = 1000  ##ms, animation interval
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    _, _, max_row = read.get_spectra_row('broadband', 100, pull_results=True)
    print('max row: ' + str(max_row))

    if row is None:
        rowrange = np.arange(100, int(max_row/100)*100, 100)
        print('Please memorize row value when it shows the spectrum and terminate the program.')

        figure2 = plt.figure()
        ax2 = figure2.add_subplot(111)

        def gen():
            for i in rowrange:
                yield i

        def animate(i):
            data = read.get_spectra_row('broadband', i, pull_results=True)
            nu = data[0]['nu']
            k = data[0]['absorbance']
            model = data[0]['model']
            ax2.clear()
            ax2.plot(nu, k, linewidth=0.5)
            ax2.plot(nu, model, linewidth=0.5)
            ax2.set_ylabel('absorbance')
            ax2.set_xlabel('nu, cm-1')
            ax2.set_title(gas+', row: '+str(i))

        anim2 = FuncAnimation(figure2, animate, frames=gen(), repeat=False, interval=viewtime)
        plt.show()

    else:
        data = read.get_spectra_row('broadband', row, pull_results=True)
        nu = data[0]['nu']
        k = data[0]['absorbance']
        model = data[0]['model']

        fig, ax = plt.subplots()
        ax.plot(nu, k)
        ax.plot(nu, model)
        ax.set_xlabel('nu, cm-1')
        ax.set_ylabel('absorbance')
        ax.set_title(gas + ', row: '+str(row))
        plt.show()


if __name__ == "__main__":
    # fname = r'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'          ##Linux
    fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration'       ##Mac
    # fname = 'R:\crd_G9000\AVXxx\\3610-NUV1022\R&D\Calibration'               ## Windows
    pct = 3  # zero 2 < zero1 + pct*sigma, end experiment

    start = '20220801'   #20220609 droplet   20220608t2b tank no RDF
    suffix = ''
    # gas = '180 - Acetone'
    # gas = '7900 - Propylene glycol methyl ether (PGME)'
    # gas = '7946 - Propylene glycol monomethyl ether acetate (PGMEA)'
    # gas = '13387 - NMP'
    # gas = '1140 - Toluene'
    gas = '10914 - hexamethylcyclotrisiloxane (D3)'
    row1 = 500

    fnr = os.path.join(fname, gas, start+suffix)
    print(fnr)
    fnrp = os.path.join(fnr, 'par')

    ## check data drive is attached or not
    if not os.path.exists(fnr):
        print('Error, did not find data. Please check if data exist or attach the data/R drive.')
    elif not os.path.exists(fnrp):
        print('Error, did not find parameters data.')
    else:
        f = open(os.path.join(fnrp, 't1.txt'), 'r')
        temp = f.read().splitlines()
        ta1 = temp[0]
        ta2 = temp[1]
        ta3 = temp[2]

        f = open(os.path.join(fnrp, 't2.txt'), 'r')
        temp = f.read().splitlines()
        tb1 = temp[0]
        tb2 = temp[1]
        tb3 = temp[2]

        f = open(os.path.join(fnrp, 't3.txt'), 'r')
        temp = f.read().splitlines()
        tc1 = temp[0]
        tc2 = temp[1]
        tc3 = temp[2]

        # print(ta1,ta2,ta3)
        # print(tb1,tb2,tb3)
        # print(tc1,tc2,tc3)

        f = open(os.path.join(fnrp, 'cid.txt'), 'r')
        temp = f.read().splitlines()
        cid = int(temp[0])

        droplet = 1
        if droplet:
            f = open(os.path.join(fnrp, 'weight.txt'), 'r')
            temp = f.read().splitlines()
            weight = temp[0]
            f = open(os.path.join(fnrp, 'molecular_weight.txt'), 'r')
            temp = f.read().splitlines()
            MW = temp[0]
            # jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, showgraph=True)
            jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row1, showgraph=True)
            # jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row1, showgraph=True, savefig=True)

        else: #tank
            f = open(os.path.join(fnrp, 'tankconc.txt'), 'r')
            temp = f.read().splitlines()
            tank_conc = float(temp[0])
            jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3,row1, showgraph=True)
            # jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3,row1, showgraph=True, savefig=True)

        # findrowani(fnr, gas)            # find row number
        # findrowani(fnr, gas, row=row1)  #test specific row number




