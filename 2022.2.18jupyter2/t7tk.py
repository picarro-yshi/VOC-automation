## calibration factor for gas tank experiment, adapted from jupyter notebook
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
from zipfile import ZipFile
import matplotlib.pyplot as plt
from lib_index import lib_date

## Mongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

## customized files
helperpath = '../code/Rella-Python/'    ## './' in same folder
sys.path.append(helperpath)
import DataUtilities3.RellaColor as RC
import DataUtilities3.MPL_rella as RMPL
import DataUtilities3.load_files_rella as LF
from spectral_logger1 import SpectralLogReader as slog
import GoldenCalibrationUtilities as GCU

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


## all parameters must be valid before sending to this function; no check
def jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row=500, showgraph=False, savefig = False):
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
    if not os.path.exists(os.path.join(fnr, 'RDFs', 'unpackedFiles')):
        uz_rdf(fnr, ta, tc)
    if not os.path.exists(os.path.join(fnr, 'PrivateData', 'unpackedFiles')):
        uz_p(fnr, ta, tc)
    # exit()

    # Cal = spec_lib.EmpiricalSpectra.find_one({'cid': cid, 'version': 2, 'dataCollectionDate': '20200306', 'pNominal': 140})
    Cal = spec_lib.EmpiricalSpectra.find_one({'cid':cid, 'version':2, 'pNominal':140})
    # print(Cal)
    # print(Cal['calibration'])
    # set_cal = Cal['calibration']['20210330']['concentration']   #IPA
    set_cal = Cal['calibration'][lib_date[cid]]['concentration'] #IPA 20210330, aa 20210331
    print('cal value in lib')
    print(set_cal*1e6)

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
    idx = (x1 > tb+60) & (x1 < tc)       # IPA, time during which values are constant
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

    set_cal = h(cal_name)[0] * 1e6  ## all value same
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
    new_response_scale = slope
    new_assigned_conc_ppm = set_cal / new_response_scale
    print('initial concentration: %.4f ppm' % set_cal)
    if intercept >= 0:
        print('calibration: %.4f [actual] + %.4f' % (slope, intercept))
    else:
        print('calibration: %.4f [actual] - %.4f' % (slope, intercept))
    print('new concentration estimate: %.4f' % new_assigned_conc_ppm)

    fncal = os.path.join(fnr, 'par', 'calibration_factor.txt')
    if os.path.isfile(fncal):
        os.remove(fncal)
    with open(fncal, 'w') as f:
        f.write(str(new_assigned_conc_ppm))
    # exit()
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
    A.set_xlabel('clock time')
    A.set_ylabel(gas)
    A.set_title(ta1 + ': Raw Data')
    plt.show(block=False)
    F1 = F
    if savefig:
        saver(F, ta1 + 'Raw')
    # exit()

    ## Fitting plot
    A, F = RMPL.Maker()
    A.plot(xt, yt, label='measurement')
    A.plot(xt, set_conc, '*', label='input')
    A.legend()
    A.set_xlabel('time, min')
    A.set_ylabel(gas)
    A.set_title('Measured and Set Values')
    plt.show(block=False)
    F2 = F
    if savefig:
        saver(F, ta1 +'Measured')
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
    F3 = F
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

    # start = '20220411'
    # suffix = ''          ## folder suffix or empty ''
    # row1 = 600          ## test a specific row value
    # gas = '3776 - 2-Propanol'
    # cid = 3776
    # tank_conc = 1.11   #
    # tank_conc = 9.873
    # tank_conc = 9.974
    # tank_conc = 10.28   #
    # tank_conc = 402.6   #
    # tank_conc = 10.94   #1300
    # tank_conc = 4.97  #600
    # tank_conc = 1.104  #600
    # # gas_name = 'broadband_gasConcs_' + str(cid)  ## broadband_gasConcs_176
    # # cal_name = 'broadband_eCompoundOutputs_' + str(cid) + '_calibration'  ## broadband_eCompoundOutputs_176_calibration

    start = '20220411'
    suffix = ''          ## folder suffix or empty ''
    row1 = 1000          ## test a specific row value
    gas = '176 - Acetic Acid'
    cid = 176
    tank_conc = 8.006


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

        # tb1, tb2, tb3 = '20220406', '18', '30'
        # tc1, tc2, tc3 = '20220406', '19', '00'

        # print(ta1,ta2,ta3)
        # print(tb1,tb2,tb3)
        # print(tc1,tc2,tc3)


        # jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, showgraph=True)
        jupyternotebook_tk(fnr, gas, cid, tank_conc, ta1, ta2, ta3, tb1, tb2, tb3, tc1, tc2, tc3, row1, showgraph=True)
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



