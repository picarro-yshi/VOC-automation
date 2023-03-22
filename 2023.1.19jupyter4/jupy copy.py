## calibration factor for droplet experiment, adapted from jupyter notebook
## basic library
import sys
import numpy as np
import os
import shutil
import time
import datetime
import matplotlib.pyplot as plt
import h5py     #need by Windows
import tables   #need by windows

from spectral_logger1 import SpectralLogReader as slog
import GoldenCalibrationUtilities as GCU
plt.rcParams["font.family"] = "Arial"


def loadprivate(fnr):   # from Chris's datautility3
    ht = []   #head tags
    dat = None
    fd = os.path.join(fnr, 'PrivateData', 'broadband')
    N = len(os.listdir(fd))
    ct = 1
    for f in os.listdir(fd):
        ext = f[-3:]
        fn = os.path.join(fd, f)
        if ext == 'dat':
            fob = open(fn, 'r')
            header = fob.readline(-1)
            ht = string.split(string.strip(header, ' '))
            mydata = []
            stdlen = -1
            for lines in fob:
                data = string.split(string.strip(lines, ' '))
                row = []
                try:
                    for k in range(len(ht)):
                        try:
                            row.append(float(data[k]))
                        except:
                            row.append(-1.0)
                    if stdlen == -1:
                        stdlen = len(data)
                    if len(data) == stdlen:
                        mydata.append(row)
                except:
                    if verbose: print('!', end=' ')
            fob.close()

        elif ext == '.h5':
            fob5 = tables.open_file(fn)
            D = [g for g in fob5.root]
            if ht == []:
                ht = D[0].colnames

            for tag in ht:
                if tag == ht[0]:
                    datarray = np.array([D[0].col(tag)])
                else:
                    datarray = np.vstack((datarray, D[0].col(tag)))

            mydata = np.transpose(datarray)
            fob5.close()

        try:
            if dat is None:
                dat = mydata
            else:
                dat = np.vstack((dat, mydata))
        except:
            print('dat array dimension changed in file %s. Try remove the first file and re-run.' % f)

        print("Loading %d / %d... " % (ct, N))
        ct += 1
    return ht, dat


## all parameters must be valid before sending to below functions; no sanity check
## need .h5 files in PrvateData/broadband and ComboResults folder
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

    ht, dat = loadprivate(fnr)
    # print(ht)

    x1 = h('time')
    y1 = h(gas_name) * 1e6
    MFC11 = h('MFC1_flow')*1000.0
    MFC21 = h('MFC2_flow')

    idx = (x1 > ta) & (x1 < tc)      # write in 2 step cause error
    x = x1[idx]              #time
    y = y1[idx]              #concentration
    MFC1 = MFC11[idx]
    MFC2 = MFC21[idx]

    set_cal = h(cal_name)[0]         ## all value same
    print('cal value in lib')
    print(set_cal*1e6)

    idx2 = (x > ta) & (x < ta+1500)  # 25min baseline
    baseline1 = y[idx2]
    zero1 = np.mean(baseline1)
    std1 = np.std(baseline1)
    print('zero1, std1:', zero1, std1)
    # print(zero1)
    # print(std1)

    idxtb = np.where(abs(x-tb)<5)
    tbb = idxtb[0][-1] - 5*12  ## index 5 min before recorded sample adding time
    i = tbb
    tcc = 0
    i += 500       # 40min after add sample, about 12 points/min
    ## Find end time: zero 2 < zero1 + pct*sigma
    while i < len(x):
        zero2 = np.mean(y[i-250: i])
        if zero2 < zero1 + std1*pct:  ## baseline end here
            tcc = i                   ## experiment end point
            break
        i += 200

    if tcc:
        print('calculation end time')
        print(time.ctime(x[tcc]))
    else:
        print('baseline still above mean+sigma')

    y0 = y[tbb:i]-zero1        ##truncated y, zero-ed
    xtruc = x[tbb:i]           ## truncated x in s
    # print(tbb)
    # print(i)
    # print(len(x))
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
    F, A1 = plt.subplots(dpi=150)   #figsize=(6.5, 4.0)
    A1.plot(x3, MFC1, label='Dilution', color='#03A609') #dkgreen
    A1.set_xlabel('Time (minutes)', fontsize=12)
    A1.set_ylabel('Dilution, ZA (sccm)', fontsize=14, color='#03A609')
    A1.set_facecolor('#Ededee')
    A1.grid(c='white')
    A3 = A1.twinx()
    A3.plot(x3, MFC2, label='Beaker', color='#000088')   #dkblue
    A3.set_ylabel('Bubbler (sccm)', fontsize=12, color='#000088')
    # A1.set_xlim(T[cal_index[0]], T[cal_index[-1]])
    A1.set_title(ta1 + ' Flow Rate')
    plt.show(block=False)
    F1 = F
    if savefig:
        plt.savefig(os.path.join(fnr, ta1 +' Flowrates.png'), bbox_inches='tight')
    # exit()

    #Integrated droplet
    F, [A1, A2] = plt.subplots(2, 1, dpi=300, figsize=(10, 8))   #figsize=(6.5, 4.0)
    A1.set_facecolor('#Ededee')
    A2.set_facecolor('#Ededee')
    A1.grid(c='white')
    A2.grid(c='white')
    A1.plot(x0, y0, c='#B5292f', lw=1, label='Time series')
    A2.plot(x0, S, c='#4188BA', lw=1, label=('Integrated, total: %.2f' % S[-1]))
    A1.set_title('Droplet Calibration: cal = %.3f\n%s' %(cal, gas), fontsize=16)
    A1.legend(loc='best', fontsize=10)
    A2.legend(loc='best', fontsize=10)
    A1.set_xticklabels([])
    A2.set_xlabel('Time (minutes)', fontsize=12)
    A1.set_ylabel('Sample (ppm)', fontsize=12)
    A2.set_ylabel('Sample (µ moles)', fontsize=12)
    # F.tight_layout()
    plt.show(block=False)
    F2 = F
    if savefig:
        plt.savefig(os.path.join(fnr, ta1 +' Integration.png'), bbox_inches='tight')
    # exit()

    #Raw data
    F, A = plt.subplots(dpi=150)   #figsize=(6.5, 4.0)
    A.set_facecolor('#Ededee')
    A.grid(c='white')
    F.tight_layout()
    x_t = [x[0]]     # x data that will be marked
    xmak = [time.strftime('%H:%M', time.localtime(x[0]))]

    n= len(x)
    for i in range(1, n):
        clock0 = time.strftime('%M:%S', time.localtime(x[i-1]))
        clock =  time.strftime('%M:%S', time.localtime(x[i]))
        if (clock0[:2] == '29' and clock[:2]=='30') or (clock0[:2] == '59' and clock[:2]=='00'):
            x_t.append(x[i])
            xmak.append(time.strftime('%H:%M', time.localtime(x[i])))

    A.plot(x, y, label=' %s (ppm)' % gas)
    A.set_xticks(x_t, xmak)
    A.set_ylabel('Conc. (ppm)', fontsize=12)
    A.set_xlabel('Clock time', fontsize=12)
    A.set_title('%s Raw Data\n%s'%(ta1,gas))
    F.autofmt_xdate()    # x-label will not overlap
    plt.show(block=False)
    F3 = F
    if savefig:
        plt.savefig(os.path.join(fnr, ta1 +' Raw.png'), bbox_inches='tight')
    # exit()

    ### check if compound has the correct spectrum and RMSE
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    data = read.get_spectra_row('broadband', row, pull_results=True)[0]
    nu = data['nu']
    k = data['absorbance']
    residuals = data['residuals']
    partial_fit = data['partial_fit']
    model = data['model']

    F, [A1, A2] = plt.subplots(2, 1, dpi=150)   #figsize=(10, 8)
    A1.set_facecolor('#Ededee')
    A2.set_facecolor('#Ededee')
    A1.grid(c='white', which='major',lw=1)
    A1.grid(c='white', which='minor', lw=0.5)
    A2.grid(c='white', which='major',lw=1)
    A2.grid(c='white', which='minor', lw=0.5)
    A1.minorticks_on()
    A2.minorticks_on()

    A1.plot(nu, k, label='data', color='#DC61D0', lw=1) #, alpha=0.75)
    A1.plot(nu, model, label='model', color='#00ffff', lw=1) #, alpha=0.4)
    A1.legend(loc=0, fontsize=10)
    A1.set_ylabel('Absorbance', fontsize=12)
    A1.set_title('%s Combo Log\n%s'%(ta1,gas))

    A2.plot(nu, residuals, label='residuals', color='#7068bb', lw=1)   #, alpha=0.75
    A2.set_ylabel('Residuals', color='#7068bb', fontsize=12)
    A4 = A2.twinx()
    A4.plot(nu, partial_fit, label='partial fit', color='#A6ce6a', lw=1 ) #, alpha=0.75)
    A2.set_xlabel('nu (cm-1)', fontsize=12)
    A4.set_ylabel('Partial fit', color='#A6ce6a', fontsize=12)
    A2.legend(loc=0, fontsize=10)
    F4 = F
    if savefig:
        plt.savefig(os.path.join(fnr, ta1 +' RawSpectraFit.png'), bbox_inches='tight')
    plt.show(block=False)
    if showgraph:
        plt.waitforbuttonpress()  # press any key to close all plots
        plt.close()
    return F1, F2, F3, F4


## gas tank
def jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row=500, showgraph=False, savefig=False):
    gas_name = 'broadband_gasConcs_' + str(cid)  ## broadband_gasConcs_176
    cal_name = 'broadband_eCompoundOutputs_'+ str(cid) +'_calibration' ## broadband_eCompoundOutputs_176_calibration
    # fnr = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c"

    ## epoch_time = datetime.datetime(2021,11,24,8,0).timestamp()
    ta = datetime.datetime(int(ta1[:4]), int(ta1[4:6]), int(ta1[-2:]),int(ta2),int(ta3)).timestamp()
    # tb = datetime.datetime(int(tb1[:4]), int(tb1[4:6]), int(tb1[-2:]),int(tb2),int(tb3)).timestamp() #not needed
    tc = datetime.datetime(int(tc1[:4]), int(tc1[4:6]), int(tc1[-2:]),int(tc2),int(tc3)).timestamp()

    def h(name):
        j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
        return dat[:, j]

    ht, dat = loadprivate(fnr)
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

    idx = (x1 > tc-1800) & (x1 < tc-300)       # IPA, time during which values are constant
    x = x1[idx]
    start = x[0]         # IPA start epoch
    x = (x - x[0]) / 60  # min, start at 0
    y = y1[idx]
    # print(len(x))
    # exit()

    gap = 5  # in minutes, look at data in packages of 5 min
    set_conc = []
    data_std = []
    yt = []  # ranged y in min
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

    set_conc = np.array(set_conc)
    data_std = np.array(data_std)
    yt = np.array(yt)
    xt = np.array(xt)

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

    set_cal = h(cal_name)[100] * 1e6  ## all value same
    fit = set_conc * MDL[0] + MDL[1]
    print(MDL[-2])
    slope = a[0]
    intercept = a[1]
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
    F, A = plt.subplots(dpi=150)   #figsize=(6.5, 4.0)
    A.set_facecolor('#Ededee')
    A.grid(c='white')
    idx = (x1 > ta) & (x1 < tc)  # zero1, 30 min
    xtruc = list(x1[idx])
    ytruc = list(y1[idx])
    x_t = [xtruc[0]]    # xtruc data that will be marked
    xmak = [time.strftime('%H:%M', time.localtime(xtruc[0]))]

    n = len(xtruc)
    for i in range(1, n):
        clock0 = time.strftime('%M:%S', time.localtime(xtruc[i-1]))
        clock =  time.strftime('%M:%S', time.localtime(xtruc[i]))
        if (clock0[1] == '9' and clock[1]=='0'):
            x_t.append(xtruc[i])
            xmak.append(time.strftime('%H:%M', time.localtime(xtruc[i])))

    A.plot(xtruc, ytruc, label='Raw')
    A.set_xticks(x_t, xmak)
    A.legend()
    A.set_xlabel('Clock time', fontsize=12)
    A.set_ylabel('Conc. (ppm)', fontsize=12)
    A.set_title('%s Raw Data\n%s'%(ta1, gas))
    F.autofmt_xdate()    #x-label will not overlap
    plt.show(block=False)
    F1 = F
    if savefig:
        plt.savefig(os.path.join(fnr, ta1 +' Raw.png'), bbox_inches='tight')
    # exit()

    ## Fitting plot
    F, A = plt.subplots(dpi=150)   #figsize=(6.5, 4.0)
    A.set_facecolor('#Ededee')
    A.grid(c='white')
    A.plot(xt, yt, label='Measurement')
    A.plot(xt, set_conc, '*', label='Tank Conc. from Airgas')
    A.legend(loc=0, fontsize=10)
    A.set_xlabel('Time (min)', fontsize=12)
    A.set_ylabel('Conc. (ppm)', fontsize=12)
    A.set_title('Gas Tank Calibration: cal = %.3f\n%s' %(cal, gas), fontsize=14)
    plt.show(block=False)
    F2 = F
    if savefig:
        plt.savefig(os.path.join(fnr, ta1 +' measured.png'), bbox_inches='tight')
    # exit()

    ### check if compound has the correct spectrum and RMSE
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    data = read.get_spectra_row('broadband', row, pull_results=True)
    nu = data[0]['nu']
    k = data[0]['absorbance']
    residuals = data[0]['residuals']
    partial_fit = data[0]['partial_fit']
    model = data[0]['model']

    F, [A1, A2] = plt.subplots(2, 1, dpi=150)   #figsize=(10, 8)
    A1.set_facecolor('#Ededee')
    A2.set_facecolor('#Ededee')
    A1.grid(c='white', which='major', lw=1)
    A1.grid(c='white', which='minor', lw=0.5)
    A2.grid(c='white', which='major', lw=1)
    A2.grid(c='white', which='minor', lw=0.5)
    A1.minorticks_on()
    A2.minorticks_on()
    A1.plot(nu, k, label='data', color='#DC61D0', lw=1) #, alpha=0.75)
    A1.plot(nu, model, label='model', color='#00ffff', lw=1) #, alpha=0.4)
    A1.legend(loc=0, fontsize=10)
    A1.set_ylabel('Absorbance', fontsize=12)
    A1.set_title('%s Combo Log\n%s'%(ta1,gas))

    A2.plot(nu, residuals, label='residuals', color='#7068bb', lw=1)   #, alpha=0.75
    A2.set_ylabel('Residuals', color='#7068bb', fontsize=12)
    A4 = A2.twinx()
    A4.plot(nu, partial_fit, label='partial fit', color='#A6ce6a', lw=1 ) #, alpha=0.75)
    A2.set_xlabel('nu (cm-1)', fontsize=12)
    A4.set_ylabel('Partial fit', color='#A6ce6a', fontsize=12)
    A2.legend(loc=0, fontsize=10)
    F3 = F
    F4 = F
    if savefig:
        plt.savefig(os.path.join(fnr, ta1 +' RawSpectraFit.png'), bbox_inches='tight')
    plt.show(block=False)
    if showgraph:
        plt.waitforbuttonpress()  # press any key to close all plots
        plt.close()

    return F1, F2, F3, F4



## look at combo log data, RMSE time series
def lookcombo(fnr, gas, cid, r1, r2, r3, r4, ta1, savefig=False):
    note = ''
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    _, _, max_row = read.get_spectra_row('broadband', 100, pull_results=True)
    print('max_row: ', max_row)

    if r1 > max_row or r2 > max_row or r3 > max_row or r4 > max_row:
        note = 'Row, Range numbers must be\nless than max_row: %s' % max_row
    else:
        if r4 == 0:
            r4 = max_row
        x = list(range(r3, r4))
        ycombo = [0] * len(x)
        yconc = [0] * len(x)

        for j, row in enumerate(x):
            a, b, _ = read.get_spectra_row('broadband', row, pull_results=True) #spectrum, results, max_row
            residuals = a['residuals']
            partial_fit = a['partial_fit']

            n = len(residuals)
            f = 0
            r = 0
            for i in range(n):
                f += partial_fit[i] ** 2
                r += residuals[i] ** 2
            ycombo[j] = ((f / n) ** 0.5) / ((r / n) ** 0.5)
            yconc[j] = b['gasConcs_'+str(cid)] * 1000000
        print('finish loading data')

        col1 = 'steelblue'
        col2 = 'dimgrey'
        F, [ax1, ax2] = plt.subplots(2, 1, dpi=150)
        ax1.set_facecolor('#Ededee')
        ax2.set_facecolor('#Ededee')
        ax1.grid(c='white')
        ax2.grid(c='white')
        F.tight_layout()

        ax1.set_title('%s Combo Log: %s'%(ta1, gas))
        ax1.set_xlabel('row#')
        ax1.plot(x, ycombo, color=col1, lw=1)
        ax1.set_ylabel('Phi/RMSE(residue)', color=col1, fontsize=12)
        ax1.spines['right'].set_color(col2)

        ax1a = ax1.twinx()
        ax1a.plot(x, yconc, color=col2, lw=1)
        ax1a.set_ylabel('Concentration, ppm', color=col2, fontsize=12)
        ax1a.spines['left'].set_color(col1)

        # spectra of 2 rows
        data = read.get_spectra_row('broadband', r1, pull_results=True)
        nu = data[0]['nu']
        k1 = data[0]['absorbance']
        print(len(nu), len(k1))
        # print(nu)

        data = read.get_spectra_row('broadband', r2, pull_results=True)
        # nu = data[0]['nu']
        k2 = data[0]['absorbance']
        print(len(k2))
        # print(nu)
        ax2.plot(nu, k1, col1, lw=1, label='row = %s' % r1)
        ax2.legend()
        ax2.set_ylabel('Absorbance Spectrum', color=col1, fontsize=12)
        ax2.set_xlabel('nu (cm-1)')

        if len(k1) == len(k2):
            try:
                ax2.plot(nu, k2, col1, lw=1, linestyle='dashed', label='row = %s'%r2)
                ax2.legend()   # need this line to show legend
                ax2.spines['right'].set_color(col2)

                #spectrum of difference
                ax2a = ax2.twinx()
                # ax2.set_title('Selected Spectra')
                ax2a.plot(nu, k1-k2, col2, lw=1)
                ax2a.set_ylabel('row difference %s vs %s'%(r1, r2), color=col2, fontsize=12)
                ax2a.spines['left'].set_color(col1)
            except:
                note = 'Error making combo plot.'
        else:
            note = 'Row1,2 dimensions are different.\n(wave number arrays different)\nTry to pick different row numbers.'
        if savefig:
            plt.savefig(os.path.join(fnr, ta1 +' ComboLog.png'), bbox_inches='tight')
        plt.show()

    print(note)
    return note


def comboarray(fnr, r1, r2):  #plot the combo data array dimension
    note = ''
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    _, _, max_row = read.get_spectra_row('broadband', 100, pull_results=True)
    print('max_row: ', max_row)
    if r1 > max_row or r2 > max_row:
        note = 'Row, Range numbers must be\nless than max_row: %s' % max_row
        print(note)
    else:
        x = list(range(r1, r2))
        for j, row in enumerate(x):
            data = read.get_spectra_row('broadband', row, pull_results=True)
            nu = data[0]['nu']
            print(row, len(nu))
    return note


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
    pct = 4  # zero 2 < zero1 + pct*sigma, end experiment

    start = '20220912'  #20230105
    suffix = 't2'
    # gas = '180 - Acetone'
    # gas = '7900 - Propylene glycol methyl ether (PGME)'
    # gas = '7946 - Propylene glycol monomethyl ether acetate (PGMEA)'
    # gas = '13387 - NMP'
    # gas = '31404 - BHT'
    # gas = '8785 - Benzyl Acetate'
    # gas = '1146 - Trimethylamine'
    # gas = '244 - Benzyl Alcohol'
    gas = '241 - Benzene'
    # gas = '7500 - Ethylbenzene'
    row1 = 400

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

        # tb1 = '20220826'
        # tb2 = '17'
        # tb3 = '00'
        # tc1 = '20220826'
        # tc2 = '17'
        # tc3 = '05'

        print(ta1,ta2,ta3)
        print(tb1,tb2,tb3)
        print(tc1,tc2,tc3)

        f = open(os.path.join(fnrp, 'cid.txt'), 'r')
        temp = f.read().splitlines()
        cid = int(temp[0])

        experiment = 2   #1: droplet, 2: tank, 3: combo study, 4: find row num, 5: row dimensions
        if experiment == 1:
            f = open(os.path.join(fnrp, 'weight.txt'), 'r')
            temp = f.read().splitlines()
            weight = temp[0]
            f = open(os.path.join(fnrp, 'molecular_weight.txt'), 'r')
            temp = f.read().splitlines()
            MW = temp[0]
            # jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, showgraph=True)
            jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row1, showgraph=True)
            # jupyternotebook_dp(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row1, showgraph=True, savefig=True)

        elif experiment == 2: #tank
            f = open(os.path.join(fnrp, 'tankconc.txt'), 'r')
            temp = f.read().splitlines()
            tank_conc = float(temp[0])
            jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row1, showgraph=True)
            # jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3,row1, showgraph=True, savefig=True)

        elif experiment == 3:
            r1 = 280     # compare 2 rows
            r2 = 290
            r3 = 0      # 0 for minimum row#
            r4 = 0      # 0 for maximum row#
            lookcombo(fnr, gas, cid, r1, r2, r3, r4, ta1)
            # lookcombo(fnr, gas, cid, r1, r2, r3, ta1, savefig=True)

        elif experiment == 4:
                # findrowani(fnr, gas)            # find row number
                findrowani(fnr, gas, row=row1)  #test specific row number

        else:
            r1 = 1050
            r2 = 1150
            comboarray(fnr, r1, r2)

# ## import customized files from other folder
# helperpath = '../code/Rella-Python/'    ## './' in same folder
# sys.path.append(helperpath)
# import DataUtilities3.load_files_rella as LF