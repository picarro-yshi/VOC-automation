## basic library
import sys
import h5py
import tables
import numpy as np
import os
import shutil
from typing import Any, Dict, Tuple, Union, List
import json
import time
import datetime

## Mongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

## plot
import matplotlib.pyplot as plt
import DataUtilities3.RellaColor as RC
import DataUtilities3.MPL_rella as RMPL
import DataUtilities3.load_files_rella as LF
from spectral_logger1 import SpectralLogReader as slog

DB_JSON_FILENAME = r'SpectralDatabaseDefinitionLinux.json'

class SpectralDatabase:
    admin: 'Collection'
    pubChem: 'Collection'
    hitranAdmin: 'Collection'
    hitranPeaks: 'Collection'
    hitranMolecules: 'Collection'
    picarroPeaks: 'Collection'
    peakOverlays: 'Collection'
    compoundOverlays: 'Collection'
    generalOverlays: 'Collection'
    empiricalSpectra: 'Collection'
    MDB: 'MyMongoDB'

    def __init__(self, load_and_connect: bool = True, dbpath: Union[str, None] = None,
                 mongod_path: Union[str, None] = None, verbose: bool = False) -> None:
        self.database_definition: Dict[str, Any] = dict()
        if load_and_connect:
            self.database_definition = self.load_spectral_db_definition()
            if os.getenv("RUNNING_IN_DOCKER"):
                self.database_definition['admin']['DB_host'] = 'mongodb'

            if dbpath:
                self.database_definition['admin']['DB_path'] = dbpath

            self.database_definition['admin']['mongod_path'] = mongod_path
            self.database_connect(verbose=verbose)

    def load_spectral_db_definition(self, filename=DB_JSON_FILENAME):
        """ Loads the Spectral database definition file """
        with open(filename, 'r') as f:
            db_json = json.load(f)
        # print(db_json)
        return db_json

    def database_connect(self, verbose: bool = False) -> None:
        # connect to mongo server
        db_conf = self.database_definition['admin']
        name = db_conf['DB_name']
        path = db_conf['DB_path']
        host = db_conf['DB_host']
        self.MDB = MyMongoDB(name, path, host)

        self.collection_list = [k for k in self.database_definition if k != 'admin']

        for collection_name in self.collection_list:
            # LOGGER.debug(f'Connecting to {collection_name} collection...')
            try:
                collection = self.MDB.db[self.database_definition[collection_name]['name']]
                self.__setattr__(collection_name, collection)
                # LOGGER.debug(f'Connected to {collection_name}.')
            except KeyError:
                # LOGGER.error(f'{collection_name} collection does not exist')
                raise e

class MyMongoDB:
    client: 'MongoClient'
    mongod = None
    pid = None
    db: Database

    def __init__(self, DB_name: str, DB_path: str, DB_host: str, verbose: bool = False):
        self.DB_name = DB_name
        self.DB_path = DB_path
        self.DB_host = DB_host
        try:
            self.client = MongoClient(host=f'{DB_host}:27017', serverSelectionTimeoutMS=2000)
            # print('DB_host')
            # print(DB_host)
            self.client.list_database_names()
            # print('try1')
        except OperationFailure:
            self.client = MongoClient(host=f'{DB_host}:27017', serverSelectionTimeoutMS=2000, **DB_CONFIG)
            self.client.list_database_names()

        # LOGGER.debug('Attempting connection to MongoDB server on default port...')
        try:
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            # print('try2')
        except ServerSelectionTimeoutError as e:
            # LOGGER.error('Cound not connect to MongoDB server. Is the server running?')
            raise e
        self.mongod = None

        self.db = self.client[DB_name]

    def terminateConnection(self, closeServer: bool = False) -> None:
        self.client.close()
        if self.mongod is not None and closeServer:  #server spawned from this thread
            # LOGGER.debug('Terminating MongoDB server...')
            self.mongod.terminate()
            while self.mongod.poll():
                time.sleep(0.5)
            # LOGGER.debug('MongoDB terminated successfully')

spec_lib = SpectralDatabase(verbose=True).MDB.db
print(spec_lib)
print(spec_lib.list_collection_names())
# exit()

RMPL.SetTheme('FIVE')
color4 = RC.Tetrad(primary=1, useRGY=True)

## all parameters must be valid before sending to this function; no check
def jupyternotebook(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row=500, showgraph=False, savefig = False):
    gas_name = 'broadband_gasConcs_' + str(cid)  ## broadband_gasConcs_176
    cal_name = 'broadband_eCompoundOutputs_'+ str(cid) +'_calibration' ## broadband_eCompoundOutputs_176_calibration
    # fnr = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c"

    def h(name):
        j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
        return dat[:, j]

    ## check if still need to unzip
    ## RDF files location on analyzer:
    ## /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c/RDFs/home/picarro/I2000/Log/RDF
    # fnzip1 = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c/RDFs/"
    fnzip1 = os.path.join(fnr, 'RDFs')
    # fn1 = fnzip1 + '/home/picarro/I2000/Log/RDF'
    fn1 = os.path.join(fnzip1, 'home')  #join one by one
    fn1 = os.path.join(fn1, 'picarro')
    fn1 = os.path.join(fn1, 'I2000')
    fn1 = os.path.join(fn1, 'Log')
    fn1 = os.path.join(fn1, 'RDF')

    ## private files location on analyzer
    # /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/home/picarro/I2000/Log/DataLogger/DataLog_Private
    # fnzip2 = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/'
    fnzip2 = os.path.join(fnr, 'PrivateData')
    # fn2 = fnzip2 + 'home/picarro/I2000/Log/DataLogger/DataLog_Private'
    fn2 = os.path.join(fnzip2, 'home')  #has to join one by one
    fn2 = os.path.join(fn2, 'picarro')
    fn2 = os.path.join(fn2, 'I2000')
    fn2 = os.path.join(fn2, 'Log')
    fn2 = os.path.join(fn2, 'DataLogger')
    fn2 = os.path.join(fn2, 'DataLog_Private')

    fn3 = os.path.join(fnzip2, 'broadband')
    fn4 = os.path.join(fnzip2, 'private')
    fn5 = os.path.join(fnzip2, 'unpackedFiles')

    if not os.path.exists(os.path.join(fnzip1, 'unpackedFiles')):
        t1=time.time()
        print('Unzip RDF files...')

        for f in os.listdir(fnzip1):
            if f.endswith('.zip'):
                # print(f)
                shutil.unpack_archive(os.path.join(fnzip1, f), fnzip1)
        print(time.time()-t1)

        print('Moving to unpackedFiles...')
        shutil.move(fn1, fnzip1, copy_function=shutil.copytree)                        ## move up in directory
        os.rename(os.path.join(fnzip1, 'RDF'), os.path.join(fnzip1, 'unpackedFiles'))  ## rename folder
        shutil.rmtree(os.path.join(fnzip1, 'home'))                                    ## delete 'home' folder
        print(time.time()-t1)

    if not os.path.exists(fn5):
        t1=time.time()
        print('unzip private files')

        for f in os.listdir(fnzip2):
            if f.endswith('.zip'):
                # print(f)
                shutil.unpack_archive(os.path.join(fnzip2, f), fnzip2)
        print(time.time()-t1)

        print('Moving to unpackedFiles...')
        shutil.move(fn2, fnzip2, copy_function=shutil.copytree)   ## move up in directory
        os.rename(os.path.join(fnzip2, 'DataLog_Private'), fn5)   ## rename folder
        shutil.rmtree(os.path.join(fnzip2, 'home'))               ## delete 'home' folder

        ## move unziped files to folders
        if os.path.exists(fn3):
            shutil.rmtree(fn3)
        if os.path.exists(fn4):
            shutil.rmtree(fn4)
        os.mkdir(fn3)
        os.mkdir(fn4)

        for f in os.listdir(fn5):
            # if 'VOC_broadband' in f:
            if 'NewFitter' in f:
                shutil.move(os.path.join(fn5, f), fn3)
            elif 'DataLog_Private' in f:
                shutil.move(os.path.join(fn5, f), fn4)

        t2=time.time()
        print(t2-t1)
    # exit()

    Cal = spec_lib.EmpiricalSpectra.find_one({'cid':cid, 'version':2, 'pNominal':140})
    # print(Cal)
    # print(Cal['calibration'])
    set_cal = Cal['calibration']['20210331']['concentration']
    print('cal value in lib')
    print(set_cal*1e6)
    # exit()

    ht, dat = LF.loadFilesH5(fn3, N=-1)  ## headtag, data. all data in that range
    # print(ht)
    # exit()
    x1 = h('time')
    y1 = h(gas_name) * 1e6
    MFC11 = h('MFC1_flow')*1000.0
    MFC21 = h('MFC2_flow')

    ## epoch_time = datetime.datetime(2021,11,24,8,0).timestamp()
    ta = datetime.datetime(int(ta1[:4]), int(ta1[4:6]), int(ta1[-2:]),int(ta2),int(ta3)).timestamp()
    tb = datetime.datetime(int(tb1[:4]), int(tb1[4:6]), int(tb1[-2:]),int(tb2),int(tb3)).timestamp()
    tc = datetime.datetime(int(tc1[:4]), int(tc1[4:6]), int(tc1[-2:]),int(tc2),int(tc3)).timestamp()

    idx = (x1>ta) & (x1<tc)   #write in 2 step cause error wrong
    x = x1[idx]
    y = y1[idx]
    MFC1 = MFC11[idx]
    MFC2 = MFC21[idx]

    set_cal = h(cal_name)[0]  ## all value same
    baselinetime1 = 20        ## min, baseline length
    idx2 = (x > tb-baselinetime1*60-120) & (x < tb-120) ## 2 min before add sample
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

    ## Find end time: zero 2 < zero1 + pct*sigma
    i += 100     #points
    while i < len(x):
        zero2 = np.mean(y[i-200: i])
        if zero2 < zero1 + std1*pct:  # baseline end here
            break
        i += 50

    tcc = i     ## experiment end point
    print('calculation end time')
    print(time.ctime(x[tcc]))
    # print('peak time')
    # print(time.ctime(x[peaktime]))

    y0 = y[tbb:i]-zero1  ##truncated y, zero-ed
    x0 = x[tbb:i]
    x0 = (x0-x0[0])/60   ## truncated x, in min,start from 0
    # print('len y0: %s'%(len(y0)))
    # print('len y: %s'%(len(y)))
    # print('len y1: %s'%(len(y1)))
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
    cal_factor = vol_in / (S[-1]) * 1E6
    # print(cal_factor)
    cal = cal_factor * set_cal * 1e6
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
    A1.plot(x3, MFC1, label = 'Dilution', color = RMPL.dkgreen)
    A1.set_xlabel('time [Minutes]', fontsize=14)
    A1.set_ylabel('Dilution,pump (sccm)', fontsize=14, color = RMPL.dkgreen)
    A3 = A1.twinx()
    A3.plot(x3, MFC2, label = 'Beaker',color = RMPL.dkblue )
    A3.set_ylabel('beaker (sccm)', fontsize=14, color = RMPL.dkblue)
    # A1.set_xlim(T[cal_index[0]], T[cal_index[-1]])
    A1.set_title('Flow rate all time')
    plt.show(block=False)
    F1 = F
    if savefig:
        saver(F, ta1 +'Flowrates')
    # exit()

    #Integrated droplet
    A, F = RMPL.Maker(grid=(2,1), size=(10,8))
    A[0].plot(x0, y0, c=color4[0], lw=2, label=RMPL.MATH % 'evaporated \ %s' %gas)
    A[1].plot(x0, S, c=color4[1], lw=2, label=(RMPL.MATH % 'integrated \ %s \ signal' %gas) + ' [%.2f]' % (S[-1]))
    A[0].set_title(RMPL.MATH % ('Droplet \ Calibration \ of \ %s ' %gas) + '- cal = %.3f' %cal, fontsize = 16)
    for a in A:
        a.legend(loc = 'best', fontsize = 12)
    A[0].set_xticklabels([])
    A[1].set_xlabel('time [Minutes]', fontsize = 14)
    A[0].set_ylabel(RMPL.MATH % ' Sample \ [ppm]', fontsize = 14)
    A[1].set_ylabel(RMPL.MATH % ' Sample \ [\mu moles]', fontsize = 14)
    F.tight_layout()
    plt.show(block=False)
    F2 = F
    if savefig:
        saver(F, ta1 +'Integration', dpi=400)
    # exit()

    A1, F = RMPL.Maker()
    Dilution = MFC20 / (MFC10 + MFC20)
    A1.plot(x0, y0 * cal_factor / Dilution, label=' %s (ppm)' % gas)
    A1.set_ylabel('Concentration in flask (ppm)', fontsize=14)
    A1.set_xlabel('time [Minutes]', fontsize=14)
    # A1.set_title('')
    plt.show(block=False)
    F3 = F
    if savefig:
        saver(F, ta1 + 'ConcentrationInFlask')
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
    A1.set_ylabel('absorbance', fontsize=14)

    colorA2 = color = kol_source.getNext()
    A2.plot(nu, residuals, label='residuals', alpha=0.75, color=colorA2)
    A2.set_ylabel('residuals', color=colorA2)
    A4 = A2.twinx()
    colorA4 = color = kol_source.getNext()
    A4.plot(nu, partial_fit, label='partial fit', color=colorA4, alpha=0.75)
    A2.set_xlabel('nu', fontsize=14)
    A4.set_ylabel('partial fit', color=colorA4)
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


### find the correct row number for slog plots
## 1 use animation to automatic scan
from matplotlib.animation import FuncAnimation
def findrowani(fnr, gas, ta1, row=None):
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


## 2 use Chris plot library
def findrow(fnr, gas, ta1, row=None):
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    _, _, max_row = read.get_spectra_row('broadband', 100, pull_results=True)
    print('max row: ' + str(max_row))

    if row is None:
        rowrange = np.arange(100, int(max_row / 100) * 100, 100)
        print('Press anykey to continue to the next plot.')
    else:
        rowrange = [row]

    for i in rowrange:
        data = read.get_spectra_row('broadband', i, pull_results=True)
        nu = data[0]['nu']
        k = data[0]['absorbance']
        model = data[0]['model']
        kol_source = RC.KawaiiPunchyCute(brtValue=0)
        A1, F = RMPL.Maker()
        A1.plot(nu, k, label='data', color=kol_source.getNext(), alpha=0.75)
        A1.plot(nu, model, label='model', color=kol_source.getNext(), alpha=0.4)
        A1.legend(loc=0, fontsize=12)
        A1.set_ylabel('absorbance', fontsize=14)
        A1.set_xlabel('nu', fontsize=14)
        A1.set_title(gas+', row: ' + str(i))
        plt.show(block=False)
        plt.waitforbuttonpress()
        plt.close()


if __name__ == "__main__":
    # fname = r'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'          ##Linux
    fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration'     ##Mac
    # fname = 'R:\crd_G9000\AVXxx\\3610-NUV1022\R&D\Calibration'                 ## Windows

    pct = 1  # zero 2 < zero1 + pct*sigma, end experiment
    # start = '20211124'
    # row1 = 7600           # for slog
    # row1 = 2700           # 'd'
    # start = '20211215'
    # suffix = ''          ## folder suffix 'g' or empty ''
    # row1 = 10300         ## test a specific row value
    start = '20220302'
    suffix = ''          ## folder suffix 'g' or empty ''
    row1 = 750         ## test a specific row value

    gas = '176 - Acetic Acid'
    cid = 176
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

        f = open(os.path.join(fnrp, 'weight.txt'), 'r')
        temp = f.read().splitlines()
        weight = temp[0]
        f = open(os.path.join(fnrp, 'molecular_weight.txt'), 'r')
        temp = f.read().splitlines()
        MW = temp[0]

        # jupyternotebook(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, showgraph=True)
        jupyternotebook(fnr, gas, cid, weight, MW, pct, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row1, showgraph=True)
        ## to save figure, add savefig=True, row = row1

        # findrowani(fnr, gas, ta1)            # find row number
        # findrowani(fnr, gas, ta1, row=row1)  #test specific row number

        # findrow(fnr, gas, ta1)
        # findrow(fnr, gas, ta1, row=row1)






#####
# from voc_fitter.model.library import database
# import DataUtilities3
# sys.path.append('../code/Rella-Python-master')      ## DataUtilities3
# sys.path.append('../code/voc-fitter-develop/src')   ## voc_fitter

    # volume = 10       ## droplet in uL
    # density = 1.05
    # MW = 60.052
    # weight = 0.0090   ## g
    # startTime = '20211124 08:00'
    # endTime = '20211124 23:59'
    # weight = 0.0094
    # startTime = '20211215 14:00'
    # endTime = '20211215 17:00'

# print(h('co2_6104_epochTime')[1700])
# print(h('threeGasVarP_epochTime')[1700])
# print(h('threeGas_epochTime')[1700])
# print(h('water5962_epochTime')[1700])
# print(h('time')[1700])
# x1 = h('broadband_epochTime')  #this time has only min resolution



