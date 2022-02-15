## basic library
import sys
import numpy as np
import os
import shutil
from typing import Any, Dict, Tuple, Union, List
import json
import time
# from datetime import datetime
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

def datestdtojd(stddate):
    fmt = '%Y%m%d %H:%M'
    sdtdate = datetime.datetime.strptime(stddate, fmt)
    sdtdate = sdtdate.timetuple()
    jdate = sdtdate.tm_yday + sdtdate.tm_hour / 24 + sdtdate.tm_min / (24 * 60)
    return jdate


RMPL.SetTheme('FIVE')
color4 = RC.Tetrad(primary=1, useRGY=True)

# # fname = r'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'        ##Linux
# fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'    ##Mac
# gas = '176 - Acetic Acid'
# cid = 176
# volume = 10/1000     #droplet in mL
# weight = 0.0090      #g
# startTime = '20211124 08:00'
# endTime = '20211124 23:59'
# suffix = 'd'           ## folder suffix or empty ''

def jupyternotebook(fname, gas, cid, volume, weight, density, MW, startTime, endTime, suffix, showgraph=False, savefig=False):
    volume = volume/1000
    gas_name = 'broadband_gasConcs_' + str(cid)
    spline_name = 'broadband_splineconc_' + str(cid)
    date = startTime[:8]
    fname = os.path.join(fname, gas, date+suffix)
    print(fname)
    # fname = fname + gas + '/' + date + suffix + '/'

    def h(name):
        j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
        return dat[:, j]

    ## check data drive is attached or not
    if not os.path.exists(fname):
        print('Error, did not find data. Please check if data exist or attach the data/R drive.')
    else:
        ## check if still need to unzip
        ## RDF files are here:
        ## /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c/RDFs/home/picarro/I2000/Log/RDF
        # fnzip1 = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c/RDFs/"
        # fnzip1 = fname + 'RDFs/'
        fnzip1 = os.path.join(fname, 'RDFs')
        fn1 = os.path.join(fnzip1, '/home/picarro/I2000/Log/RDF')
        # ## private files location on Linux
        # /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/home/picarro/I2000/Log/DataLogger/DataLog_Private
        # fnzip2 = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/'
        # fnzip2 = fname + 'PrivateData/'
        fnzip2 = os.path.join(fname, 'PrivateData')
        fn2 = os.path.join(fnzip2, 'home/picarro/I2000/Log/DataLogger/DataLog_Private')
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
            shutil.move(fn1, fnzip1, copy_function=shutil.copytree)  ## move up in directory
            os.rename(os.path.join(fnzip1, 'RDF'), os.path.join(fnzip1, 'unpackedFiles'))          ## rename folder
            shutil.rmtree(os.path.join(fnzip1, 'home'))                             ## delete 'home' folder
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
            shutil.rmtree(os.path.join(fnzip2, 'home'))                ## delete 'home' folder

            ## move unziped files to folders
            if os.path.exists(fn3):
                shutil.rmtree(fn3)
            if os.path.exists(fn4):
                shutil.rmtree(fn4)
            os.mkdir(fn3)
            os.mkdir(fn4)

            for f in os.listdir(fn5):
                if 'VOC_broadband' in f:
                    shutil.move(os.path.join(fn5, f), fn3)
                elif 'DataLog_Private' in f:
                    shutil.move(os.path.join(fn5, f), fn4)

            t2=time.time()
            print(t2-t1)
        # exit()

        # privateDIR = os.path.join(fname, gas, date, 'PrivateData', 'private')
        # broadbandDIR = os.path.join(fname, gas, date, 'PrivateData', 'broadband')
        # log_path = os.path.join(fname, gas, date, 'ComboResults')   #
        # saveDIR = os.path.join(fname, gas, date)

        saver = RMPL.SaveFigure(DIR=fname).savefig

        # density = 1.05
        # MW = 60.052
        mol_beaker = volume * density / MW  # mL*(g/mL)/(g/mol)
        mol_beaker_wt = weight / MW

        Cal = spec_lib.EmpiricalSpectra.find_one({'cid':cid, 'version':2, 'pNominal':140})
        # print(Cal)
        print('cal[calibration]')
        print(Cal['calibration'])
        # exit()

        # set_cal = Cal['calibration']['20210331']['concentration']
        # set_cal*1e6

        #load broadband logs
        # DIR = broadbandDIR
        ht, dat = LF.loadFilesH5(fn3, N=-1)  ## headtag, data
        # print(dat)
        # print(ht)
        # exit()

        T_bb2 = h('JULIAN_DAYS')
        das_temp2 = h('DasTemp')
        cal_gas2 = h(gas_name)*1e6
        ch42 = h('broadband_gasConcs_297')*1e6
        co22 = h('broadband_gasConcs_280')*1e6
        h2o2 = h('broadband_gasConcs_962')*1e6
        set_cal2 = h(spline_name)*1e6
        MFC1_2 = h('MFC1_flow')*1000.0
        MFC2_2 = h('MFC2_flow')

        #### find zero
        shift = 0.   #-60
        startdate = datestdtojd(startTime) + shift/(24*60)
        enddate = datestdtojd(endTime) + shift/(24*60)
        # print(startdate)         ##328.3333333333333
        indices = np.where(T_bb2 > startdate)
        # exit()

        T_bb = T_bb2[indices]
        das_temp = das_temp2[indices]
        cal_gas = cal_gas2[indices]
        ch4 = ch42[indices]
        co2 = co22[indices]
        h2o = h2o2[indices]
        set_cal = set_cal2[indices]
        MFC1 = MFC1_2[indices]
        MFC2 = MFC2_2[indices]

        indices2 = np.where(T_bb < enddate)

        T_bb = T_bb[indices2]
        das_temp = das_temp[indices2]
        cal_gas = cal_gas[indices2]
        ch4 = ch4[indices2]
        co2 = co2[indices2]
        h2o = h2o[indices2]
        set_cal = np.mean(set_cal[indices2])*1e-6
        MFC1 = MFC1[indices2]
        MFC2 = MFC2[indices2]

        first = T_bb[0]
        T_bb -= first
        T = T_bb*24*60   ## in minutes

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
        T_pulse = T_end - T_start
        # print(T_pulse)
        # zero, len(zero1),set_cal

        ## Plot
        [A1, A2], F = RMPL.MakerCal(size = (10,8), N = 2) # this sets up a new plot that can be displayed and later saved
        A1.plot(T[zero1],cal_gas[zero1], label = gas, color = RMPL.dkgreen)
        A1.plot([T[0], T[zero1[-1]]], [np.mean(cal_gas[zero1]),np.mean(cal_gas[zero1])], label='mean', color = RMPL.ltgreen)
        A1.legend(loc=0, fontsize=12)
        A1.set_xlabel('time [Minutes]', fontsize=14)
        A1.set_ylabel('cal gas [ppm]', fontsize=14)

        A2.plot(T[cal_index],cal_gas[cal_index], label = (RMPL.MATH % '%s' %gas) +  '\nlength of pulse %.2f minutes' % (T_pulse))
        A2.legend(loc=0, fontsize=12)
        A2.set_xlabel('time [Minutes]', fontsize=14)
        A2.set_ylabel('cal gas [ppm]', fontsize=14)
        A2.set_xlim(T[cal_index[0]], T[cal_index[-1]])
        plt.show(block=False)
        F1 = F
        if savefig:
            saver(F, date +'timeline_droplet')
        # exit()

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
        plt.show(block=False)
        if savefig:
            saver(F, date +'timeline_ambient')
        F2 = F
        # exit()

        A1, F = RMPL.Maker() # this sets up a new plot that can be displayed and later saved
        A1.plot(T,MFC1, label = 'Dilution', color = RMPL.dkgreen)
        A1.set_xlabel('time [Minutes]', fontsize=14)
        A1.set_ylabel('Dilution,pump (sccm)', fontsize=14, color = RMPL.dkgreen)
        A3 = A1.twinx()
        A3.plot(T,MFC2,label = 'Beaker',color = RMPL.dkblue )
        A3.set_ylabel('beaker (sccm)', fontsize=14, color = RMPL.dkblue)
        # A1.set_xlim(T[cal_index[0]], T[cal_index[-1]])
        plt.show(block=False)
        if savefig:
            saver(F, date +'Flowrates')
        F3 = F
        # exit()

        Y = cal_gas - zero
        S = [0.0]
        S2 = [0.0]
        DT = [T[1] - T[0]]
        s = 0.0
        s2 = 0.0
        # print('len T')
        # print(len(T))  ## 10449

        for i in range(len(T) - 1):
            flow_tot = MFC1[i] + MFC2[i]  # sccm
            mflow_tot = flow_tot / 24455  # 22400 #mol/min #24466
            dt = T[i + 1] - T[i]
            dY = 0.5 * (Y[i + 1] + Y[i])
            dY2 = 0.5 * (h2o[i + 1] + h2o[i])
            moles = dY * mflow_tot * dt
            moles2 = dY2 * mflow_tot * dt
            s += moles    # micromoles
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

        cal = cal_factor * set_cal * 1e6
        print(cal)    #### this is!
        if os.path.isfile('cal.txt'):
            os.remove('cal.txt')
        with open('cal.txt', 'w') as f:
            f.write(str(cal))
        # exit()

        #Integrated droplet
        A, F = RMPL.Maker(grid=(2,1), size=(10,8))
        A[0].plot(T, Y, c = color4[0], lw = 2, label = RMPL.MATH % 'evaporated \ %s' %gas)   ## c='r'
        A[1].plot(T, S, c = color4[1], lw = 2, label = (RMPL.MATH % 'integrated \ %s \ signal' %gas) +  ' [%.2f]' % (S[-1]))
        A[0].set_title(RMPL.MATH % ('Droplet \ Calibration \ of \ %s ' %gas) + '- cal = %.3f' %cal, fontsize = 16)
        for a in A:
            a.legend(loc = 'best', fontsize = 12)
        A[0].set_xticklabels([])
        A[1].set_xlabel('time [Minutes]', fontsize = 14)
        A[0].set_ylabel(RMPL.MATH % ' Sample \ [ppm]', fontsize = 14)
        A[1].set_ylabel(RMPL.MATH % ' Sample \ [\mu moles]', fontsize = 14)
        F.tight_layout()
        plt.show(block=False)
        F4 = F
        if savefig:
            saver(F, date +'DropletCal', dpi=400)
        # exit()

        # Integrated H2O droplet
        A, F = RMPL.Maker(grid=(2, 1), size=(6, 6))
        A[0].plot(T, h2o, c=color4[0], lw=2, label=RMPL.MATH % 'evaporated \ H2O')
        A[1].plot(T, S2, c=color4[1], lw=2, label=(RMPL.MATH % 'integrated \ H2O \ signal') + ' [%.2f]' % (S2[-1]))
        A[0].set_title(RMPL.MATH % ('Droplet \ Calibration \ of \ %s ' % gas) + '- cal = %.3f' % cal, fontsize=16)
        for a in A:
            a.legend(loc='best', fontsize=12)
        A[0].set_xticklabels([])
        A[1].set_xlabel('time [Minutes]', fontsize=14)
        A[0].set_ylabel(RMPL.MATH % ' Sample \ [amplitude]', fontsize=14)
        A[1].set_ylabel(RMPL.MATH % ' Sample \ [\mu moles]', fontsize=14)
        F.tight_layout()
        plt.show(block=False)
        F5 = F
        if savefig:
            saver(F, date + 'H2O', dpi=400)
        # exit()

        A, F = RMPL.Maker(size=(6, 4))
        A.plot(T, DT * 60, c=color4[2], lw=2)
        A.set_xlabel('time [Minutes]', fontsize=14)
        A.set_ylabel('measurement interval [sec]', fontsize=14)
        plt.show(block=False)
        F.tight_layout()
        F6 = F
        if savefig:
            saver(F, date + 'time interval', dpi=400)
        # exit()

        A1, F = RMPL.Maker()  # this sets up a new plot that can be displayed and later saved
        Dilution = MFC2 / (MFC1 + MFC2)
        A1.plot(T, Y * cal_factor / Dilution, label=' %s (ppm)' % gas)
        A3 = A1.twinx()
        A1.set_ylabel('Concentration in flask (ppm)', fontsize=14)
        A1.set_xlabel('time [Minutes]', fontsize=14)
        plt.show(block=False)
        F7 = F
        if savefig:
            saver(F, date + 'ConcentrationInFlask')
        # exit()

        A1, F = RMPL.Maker()  # this sets up a new plot that can be displayed and later saved
        A1.plot(T[cal_index], h2o[cal_index], label='H2O', color=RMPL.dkgreen)
        A1.set_xlabel('time [Minutes]', fontsize=14)
        A1.set_ylabel('H2O ppm', fontsize=14, color=RMPL.dkgreen)
        A3 = A1.twinx()
        A3.plot(T[cal_index], das_temp[cal_index], label='hmdso', color=RMPL.dkblue)
        A3.set_ylabel('Das Temp(C)', fontsize=14, color=RMPL.dkblue)
        plt.show(block=False)
        F8 = F
        # plt.waitforbuttonpress()  # any key to proceed
        # plt.close()
        if savefig:
            saver(F, date + 'DasTemp')
        # exit()

        read = slog(os.path.join(fname, 'ComboResults'), verbose=True)
        data = read.get_spectra_row('broadband', 1800, pull_results=True)
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
        # F.canvas.manager.set_window_title('Figure 9')  ## figure window title
        F9 = F
        if savefig:
            saver(F, date + 'RawSpectraFit')
        plt.show(block=False)
        if showgraph:
            plt.waitforbuttonpress()  # press any key to close all plots
            plt.close()
        return F1, F2, F3, F4, F5, F6, F7, F8, F9


if __name__ == "__main__":
    # fname = r'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'        ##Linux
    fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration'    ##Mac
    gas = '176 - Acetic Acid'
    cid = 176
    volume = 10       ## droplet in uL
    weight = 0.0090   ## g
    density = 1.05
    MW = 60.052
    startTime = '20211124 08:00'
    endTime = '20211124 23:59'
    suffix = 'd'    ## folder suffix 'g' or empty ''

    jupyternotebook(fname, gas, cid, volume, weight, density, MW, startTime, endTime, suffix, showgraph=True)
    ## to save figure, add savefig=True


#####
# from voc_fitter.model.library import database
# import DataUtilities3
# sys.path.append('../code/Rella-Python-master')      ## DataUtilities3
# sys.path.append('../code/voc-fitter-develop/src')   ## voc_fitter




