# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 18:11:31 2019

@author: chris
"""

import zipfile
import time
import re
import calendar
import datetime
import os
import shutil
from experiments.data_processing.DataUtilities import load_files_rella as LF
import numpy as np
from collections import defaultdict

ParseCRDSName = r'^([A-Z]+)([0-9]{4})-([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})([0-9]{2})Z?-([^.]+).(dat|h5)$'

class CRDSFileName():
    def __init__(self, model, SN, yr, mo, day, hr, mn, s, fileType, ext):
        self.model = model
        self.SN = int(SN)
        self.fullName = model+SN
        self.datetime = datetime.datetime(*list(map(int, (yr, mo, day, hr, mn, s))))
        self.fileType = fileType
        self.ext = ext
        epochdate = datetime.datetime(1970,1,1)
        self.createTime = (self.datetime - epochdate).total_seconds()
        self.fileAge = time.time() - self.createTime 
        self.fileAgeHrs = self.fileAge/3600.

def parseFileName(fn):
    match = re.match(ParseCRDSName, fn)
    if match is None:
        return None
    Z = CRDSFileName(*match.groups())
    return Z

class RDF_fn(object):
    RDF_RE = r'^(RD_)([0-9]+)\.h5'
    def __init__(self, fn):
        self.fn = fn
        match = re.match(self.RDF_RE, fn)
        self.createTime = int(match.groups()[1])/1000.0
        self.fileAge = time.time() - self.createTime
        self.fileAgeHrs = self.fileAge/3600.0
        
class PicarroZip(object):
    #RDF_ZIP_RE = r'^RDF_([0-9]+)_([0-9]+).zip$'
    # groups yyyy, mm, dd, hh, mm, ss    
    RDF_ZIP_RE = r'^RDF_([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})\.zip$'
    PRIVATE_ZIP_RE = r'^DataLog_Private_([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})\.zip$'

    def __init__(self, fpath):
        self.fpath = fpath
        self.fn = os.path.split(fpath)[1]
        self.ftype = None
        codes = [PicarroZip.RDF_ZIP_RE, PicarroZip.PRIVATE_ZIP_RE]
        filetypes = ['rdf', 'private']
        for ftype, code in zip(filetypes, codes):
            match = re.match(code, self.fn)
            if match is not None:
                self.ftype = ftype
                break
        if self.ftype is not None:
            self.timetuple = tuple([int(match.groups()[i]) for i in range(6)])
            LastModified = calendar.timegm(self.timetuple) #UTC conversion        
            self.AGE = (time.time() - LastModified)/3600.0
            self.zippy = zipfile.ZipFile(self.fpath)

    def extractZipFile(self, targetDIR, agelim=1e6, maxcount=1e9, verbose=True):
        #sorts in reverse order, considers only maxcount files (whether or not they are in the directory)
        if (self.ftype is None) and verbose:
            print('Not a valid RDF or private log zip')
            return None
        g = lambda x: os.path.split(x.filename)[-1] #sort on filename (not path)

        self.filesInZip = sorted(self.zippy.filelist, key=g, reverse=False)
        count = 0

        for f in self.filesInZip[:int(maxcount)]:
            thisfn = os.path.split(f.filename)[-1]
            if self.ftype == 'rdf':
                self.fileInfo = RDF_fn(thisfn)
            elif self.ftype == 'private':
                self.fileInfo = parseFileName(thisfn)
            AGE =  self.fileInfo.fileAgeHrs
            LastModified = time.mktime(f.date_time + (0,0,0))
            if AGE <= agelim:
                source = self.zippy.open(f)
                targetfn = os.path.join(targetDIR, thisfn)
                if not(os.path.exists(targetfn)):
                    target = open(targetfn, 'wb')
                    shutil.copyfileobj(source,target)
                    target.close()
                    os.utime(targetfn, (int(LastModified), int(LastModified)))
                    if verbose: print('%s extracted to %s' % (thisfn, targetDIR))
                    count += 1
        return count

def pathTree(fpath):
    npath = os.path.normpath(fpath)
    return npath.split(os.sep)

def extractPrivateFromZip(archiveDIR, targetDIR):
    archtree = pathTree(archiveDIR)
    files = LF.directoryDrillDown(archiveDIR, ext='.zip')
    print('Processing %d zip files...' % len(files))
    count = 0
    for n, fpath in enumerate(files):
        thistree = pathTree(fpath)
        archroot = thistree.index(archtree[-1])+1
        subdirName = '_'.join(thistree[archroot:-2])
        thisTargetDIR = os.path.join(targetDIR, subdirName)
        if not os.path.exists(thisTargetDIR):
            os.mkdir(thisTargetDIR)
        thisZIP = PicarroZip(fpath)
        K = thisZIP.extractZipFile(thisTargetDIR, verbose=False)
        count += K
        print('    Total Files Extracted: %d | %d zip files remaining | file age = %.1f days' % (count, len(files) - n - 1, thisZIP.fileInfo.fileAgeHrs/24.))

class RetrievePrivateData(object):
    def __init__(self, h5archive):
        self.h5archive = h5archive
        self.indexFiles()
        epoch1970= datetime.datetime(1970,1,1)
        epoch0 = datetime.datetime(1,1,1)
        self.timestampOffset = (epoch1970 - epoch0).total_seconds()
    
    def indexFiles(self, verbose=False):
        self.files = LF.directoryDrillDown(self.h5archive, ext='.h5')
        self.startTimes = []
        self.info = []
        for i, fpath in enumerate(self.files):
            fn = os.path.split(fpath)[1]
            info = parseFileName(fn)
            self.info.append(info)
            self.startTimes.append(info.createTime)
        if verbose: print('%d h5 files indexed' % (len(self.files)))
    
    def retrieveFileNames(self, startTime, duration):
        def whichGuy(t):
            closest = min(self.startTimes, key = lambda st: abs(int(st - t)))
            goodflag = (abs(closest - t) < 3600.)
            return self.startTimes.index(closest), goodflag
        s, goodflag_s = whichGuy(startTime)
        e, goodflag_e = whichGuy(startTime + duration)
        return s, e, (goodflag_s | goodflag_e | (s != e))
    
    def timestampToEpoch(self, timestamp):
        return timestamp/1000. - self.timestampOffset
    
    def epochToTimestamp(self,epoch):
        return (epoch + self.timestampOffset)*1000.
    
    def loadPrivateDataByTimeStamp(self, startstamp, endstamp, colList=None):
        return self.loadPrivateData(self.timestampToEpoch(startstamp), self.timestampToEpoch(endstamp), colList=colList)
    
    def loadPrivateData(self, startTime, duration, blackList=[]):
        s, e, good = self.retrieveFileNames(startTime, duration)
        if not(good):
            print('Private data archive does not cover date ranges')
            return None
        print(s, e, good)
        outputs = []
        theseTags = None
        thisDat = None
        for j, fn in enumerate(self.files[s:e+1]):
            ht, dat = LF.loadFileH5(fn, verbose=False)
            if theseTags != ht:
                if thisDat is not None:
                    outputs.append({'dat':thisDat, 'ht':theseTags})
                theseTags = ht
                thisDat = dat
            else:
                thisDat = np.vstack((thisDat, dat))
        outputs.append({'dat':thisDat, 'ht':theseTags})
        
        goodOutputs = []
        for block in outputs:
            thisDat = block['dat']
            theseTags = block['ht']
            goodJ = []
            goodTags = []
            for j, tag in enumerate(theseTags):
                if tag not in blackList:
                    goodJ.append(j)
                    goodTags.append(tag) 
            goodOutputs.append({'dat':thisDat[:,goodJ], 'ht':goodTags})
        
        finalOutputs = []
        for guy in goodOutputs:
            tdat = guy['dat']
            tht = guy['ht']
            h = lambda tag: tdat[:, tht.index(tag)]
            ts = h('time')
            keepers = (ts > startTime) & (ts < startTime + duration)
            finalOutputs.append({'dat':tdat[keepers,:], 'ht':tht})
        return finalOutputs

if __name__ == '__main__':
    archiveDIR = r'R:\crd_G9000\AVXxx\1249-AVX80_9001\Private Archive'
    targetDIR = r'R:\crd_G9000\AVXxx\1249-AVX80_9001\ExtractedPrivateLogs\h5'
    #extractPrivateFromZip(archiveDIR, targetDIR)
    now = time.time()
    then = now - 1200.*3600.
    #then = now
    
    RPD = RetrievePrivateData(targetDIR)
    myTags = ['ch4_conc_ppmv_final', 'co2_conc', 'h2o_conc_precal']
    myTags.extend(['pztMedian', 'overallTargetAdjust', 'wlm1_offset', 'timestamp'])
    data = RPD.loadPrivateData(then, 100., colList=myTags)

    print(data['timestamp'].mean()/1000. - J - then)
    
    from experiments.data_processing.DataUtilities import MPL_rella as RMPL    
    
    A, F = RMPL.Maker()
    A.plot(data['timestamp'], data['co2_conc'])
    
    