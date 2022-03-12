# -*- coding: utf-8 -*-
"""
Created on Wed Mar 20 15:11:22 2019

@author: chris
"""

import time
import re
import calendar
import datetime
import os
import shutil
from experiments.data_processing.DataUtilities import load_files_rella as LF
from experiments.data_processing.DataUtilities import MPL_rella as RMPL
from experiments.data_processing.DataUtilities import RellaColor as RC
import numpy as np
from collections import defaultdict
from . import PrivateDataArchiveManager as PDAM
import pprint


RMPL.SetTheme('SIX')

blackList1 = [
                'AccelX',
                'AccelY',
                'AccelZ',
                'AmbientPressure',
                'Battery_Charge',
                'Battery_Current',
                'Battery_Temperature',
                'Battery_Voltage',
          #      'CavityPressure',
          #      'CavityTemp',
                'CavityTemp1',
                'CavityTemp2',
                'CavityTemp3',
                'CavityTemp4',
                'CombCenter',
                'DasTemp',
                'Etalon1',
                'Etalon2',
                'EtalonTemp',
                'Extra1',
                'Extra2',
                'Extra3',
                'Extra4',
                'FRAC_DAYS_SINCE_JAN1',
                'FRAC_HRS_SINCE_JAN1',
                'FanState',
                'Flow1',
                'HotBoxHeater',
                'HotBoxHeatsinkTemp',
                'HotBoxTec',
                'INST_STATUS',
                'InletValve',
           #     'JULIAN_DAYS',
                'Laser1Current',
                'Laser1Tec',
                'Laser1Temp',
                'Laser2Current',
                'Laser2Tec',
                'Laser2Temp',
                'Laser3Current',
                'Laser3Tec',
                'Laser3Temp',
                'Laser4Current',
                'Laser4Tec',
                'Laser4Temp',
                'MPVPosition',
           #     'MPV_Valco_CP',
                'OutletValve',
                'ProcessedLoss1',
                'ProcessedLoss2',
                'ProcessedLoss3',
                'ProcessedLoss4',
                'Ratio1',
                'Ratio2',
                'Reference1',
                'Reference2',
                'SchemeTable',
                'SchemeVersion',
                'SpectrumID',
                'ValveMask',
                'WarmBoxHeatsinkTemp',
                'WarmBoxTec',
                'WarmBoxTemp',
            #    'adjust_24',
            #    'base_24',
                'bottle_P_amb',
                'bottle_T_amb',
            #    'bottle_flow',
            #    'bottle_flowset',
                'bubbler_P_amb',
                'bubbler_T_amb',
            #    'bubbler_flow',
            #    'bubbler_flowset',
                'bypass_P_amb',
                'bypass_T_amb',
            #    'bypass_flow',
            #    'bypass_flowset',
                'cal_enabled',
                'cavity_pressure',
                'cavity_temperature',
                'ch4_adjconc_ppmv',
                'ch4_adjust',
                'ch4_base',
                'ch4_base_avg',
            #    'ch4_conc_ppmv_final',
                'ch4_fit_time',
                'ch4_interval',
                'ch4_pzt_mean',
                'ch4_pzt_std',
                'ch4_res',
                'ch4_shift',
                'ch4_splinemax',
                'ch4_tuner_mean',
                'ch4_tuner_std',
                'ch4_vy',
                'ch4_y',
            #    'co2_conc',
                'currentPressureSetPoint',
                'das_temp',
                'dm_latency',
            #    'fsr_adjust_24',
                'fsr_base_24',
                'fsr_ch4_adjconc_ppmv',
                'fsr_ch4_adjust',
                'fsr_ch4_base',
                'fsr_ch4_base_avg',
                'fsr_ch4_conc_ppmv_final',
                'fsr_ch4_res',
                'fsr_ch4_shift',
                'fsr_ch4_splinemax',
                'fsr_ch4_vy',
                'fsr_ch4_y',
                'fsr_co2_conc',
                'fsr_h2o_adjust',
                'fsr_h2o_conc_precal',
                'fsr_h2o_peak',
                'fsr_h2o_quality',
                'fsr_h2o_res',
                'fsr_h2o_shift',
                'fsr_h2o_str',
                'fsr_h2o_y',
                'fsr_h2o_z',
                'fsr_peak_24',
                'fsr_shift_24',
                'fsr_strength_24',
                'fsr_vch4_conc_ppmv',
                'fsr_vy_24',
                'fsr_y_24',
                'goodCH4',
                'goodCO2',
                'goodH2O',
                'h2o_adjust',
            #    'h2o_conc_precal',
                'h2o_peak',
                'h2o_pzt_adjust',
                'h2o_pzt_mean',
                'h2o_pzt_std',
                'h2o_quality',
                'h2o_res',
                'h2o_shift',
                'h2o_str',
                'h2o_tuner_mean',
                'h2o_y',
                'h2o_z',
                'max_fitter_latency',
            #    'overallTargetAdjust',
                'peak_24',
                'pztAdjustGuy_new',
                'pztMean',
            #    'pztMedian',
                'pztMode',
                'pztStd',
                'pzt_per_fsr',
                'shift_24',
                'solenoid_valves',
                'species',
                'spect_duration',
                'spect_latency',
                'strength_24',
            #    'time',
                'timestamp',
            #    'valveMask',
                'vch4_conc_ppmv',
                'vy_24',
                'wlm1_offset',
                'wlmMode',
            #    'wlm_offset',
                'y_24',
                ]

archiveDIR = r'..\Private Archive'
extractedDIR = r'..\ExtractedPrivateLogs\h5'

def ExtractH5():
    # extract h5 files from private data zip files    
    PDAM.extractPrivateFromZip(archiveDIR, extractedDIR)

class RDFTimeExtrema(object):
    def __init__(self):
        self.mn = np.inf
        self.mx = -np.inf
    
    def addRdf(self, fpath):
        rdf = PDAM.RDF_fn(os.path.split(fpath)[1])
        T = rdf.createTime
        self.mn = min(self.mn, T)
        self.mx = max(self.mx, T)
        
    def __repr__(self):
        return '%.5f duration (%.4f to %.4f)' % (self.mx - self.mn, self.mn, self.mx)
        
class ExperimentPrivateData():
    
    def __init__(self, sortedDIR):
        self.sortedDIR = sortedDIR
        self.archive = PDAM.RetrievePrivateData(extractedDIR)
        self.archiveSubDir = os.path.join(self.sortedDIR, 'ArchiveData')
        if not os.path.exists(self.archiveSubDir):
            os.mkdir(self.archiveSubDir)
        
        
    def collectedDIRs(self):
        contents = os.listdir(self.sortedDIR)
        self.analysisDIRs = defaultdict(list)
        for item in contents:
            itemPath = os.path.join(self.sortedDIR, item)
            if os.path.isdir(itemPath):
                if 'ArchiveData' not in item:
                    exptpaths = os.listdir(itemPath)
                    for expt in exptpaths:
                        exptDIR = os.path.join(itemPath, expt)
                        if os.path.isdir(exptDIR):
                            self.analysisDIRs[item].append(exptDIR)
                        
    def getArchiveForDIR(self, thisDIR):
        rdfs = LF.directoryDrillDown(thisDIR, ext='.h5')
        rdfstart = PDAM.RDF_fn(os.path.split(rdfs[0])[1])
        
        rdfend = PDAM.RDF_fn(os.path.split(rdfs[-1])[1])
        data = self.archive.loadPrivateData(rdfstart.createTime, rdfend.createTime-rdfstart.createTime)
        self.rdfs = (rdfstart, rdfend)
        return data
    
    
    
    def processDIRs(self):        
        self.XT = RDFTimeExtrema()
        self.experimentCycles = defaultdict(RDFTimeExtrema)
        for name, dirList in self.analysisDIRs.items():
            for DIR in dirList:
                exptname = os.path.split(DIR)[1]
                rdfs = LF.directoryDrillDown(DIR, ext='.h5', verbose=False)
                if len(rdfs) > 0:
                    self.XT.addRdf(rdfs[0])
                    self.XT.addRdf(rdfs[-1])
                    if ('DOWN' in name):
                        self.experimentCycles[exptname].addRdf(rdfs[0])
                        self.experimentCycles[exptname].addRdf(rdfs[-1])                
        self.fulldata = self.archive.loadPrivateData(self.XT.mn, self.XT.mx - self.XT.mn, blackList=blackList1)
        
        self.allTags = set([])
        for j, fd in enumerate(self.fulldata):
            ht = fd['ht']
            self.allTags.update(ht)
            dat = fd['dat']
            fn = 'ArchiveBlock%d.txt' % j
            fpath = os.path.join(self.archiveSubDir, fn)
            np.savetxt(fpath, dat, header=' '.join(ht), comments='')
    
    def loadArchiveBlocks(self):
        files = LF.directoryDrillDown(self.archiveSubDir, ext='.txt')
        self.fulldata = []
        self.allTags = set([])
        for f in files:
            ht, dat = LF.loadFile(f, verbose=False)
            self.allTags.update(ht)
            self.fulldata.append({'ht':ht, 'dat':dat})
    
    def getColumn(self,tag):
        T, Y = np.array([]), np.array([])
        for fd in self.fulldata:
            ht, dat = fd['ht'], fd['dat']
            T = np.append(T, dat[:, ht.index('time')])
            Y = np.append(Y, dat[:, ht.index(tag)])
        return T, Y
    
    def basicPlots(self, closeMe=True):
        figDIR = os.path.join(self.archiveSubDir, 'Plots')
        oldfigs = os.listdir(figDIR)
        for fig in oldfigs:
            if fig[-4:] == '.png':
                os.remove(os.path.join(figDIR, fig))
        print(figDIR)
        saver = RMPL.SaveFigure(DIR=figDIR).savefig
        kolor = RC.ColorScale(N=len(self.allTags))
        for tag in self.allTags:
            T, Y = self.getColumn(tag)
            T0 = T[0]
            tt = lambda this: (this - T0)/3600.
            T = tt(T)
            A,F = RMPL.Maker(size=(8,5))
            A.plot(T,Y,c=kolor.getNext(), lw=0.5)
            ylim = A.get_ylim()
            sp = ylim[1] - ylim[0]
            ykick = [0.0, -0.05*sp]
            count = 0
            expts = list(self.experimentCycles.keys())
            expts.sort()
            for expt in expts:
                xtreme = self.experimentCycles[expt]
                times = xtreme.mn, xtreme.mx
                xy = (tt(times[0]), max(Y) + ykick[count%len(ykick)])
                A.annotate(expt, xy, fontsize=6, color=RMPL.gray1)
                count += 1
                
            A.set_ylabel(tag)
            A.set_xlabel('time [hrs]')
            fn = '%s_%d.png' % (tag, T0)
            saver(F, fn, closeMe=closeMe)

def processAllDirectories():
    #ExtractH5()
    
    rndDIR = r'R:\crd_G9000\AVXxx\1249-AVX80_9001\R&D'
    things = os.listdir(rndDIR)
    candidateDIRs = []
    checks = ['SortedRDFs', 'RDFs', 'SummarySpectra']
    for guy in things:
        guypath = os.path.join(rndDIR, guy)
        
        if os.path.isdir(guypath):
            subthings = set(os.listdir(guypath))
            flag = True
            for check in checks:
                flag &= check in subthings
            if flag:
                #oldArchiveDataDIR = os.path.join(guypath,'ArchiveData')
                #if os.path.exists(oldArchiveDataDIR):
                #    shutil.rmtree(oldArchiveDataDIR)
                candidateDIRs.append(os.path.join(guypath, 'SortedRDFs'))
    
    for thisDIR in candidateDIRs:
        processDIR(thisDIR)

def processDIR(dirguy):
    paths = PDAM.pathTree(dirguy)
    print('processing %s...' % paths[-2])
    E = ExperimentPrivateData(dirguy)  
    E.collectedDIRs()
    E.processDIRs()
    E.loadArchiveBlocks()
    E.basicPlots()
    
if __name__ == '__main__':
    dirguy = r'R:\crd_G9000\AVXxx\1249-AVX80_9001\R&D\20190222-20190224 - Propylene MPV10, 1-Butene MPV11, R32 Difluoromethane MPV12\SortedRDFs'
    these = processAllDirectories()
    
    
