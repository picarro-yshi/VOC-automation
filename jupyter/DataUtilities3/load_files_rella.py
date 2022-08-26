# -*- coding: utf-8 -*-
"""
Created on Thu Oct 03 17:31:32 2013

@author: chris
"""

import string
import numpy as np
import matplotlib.pyplot as plt
import os
import copy
import tables
import h5py
import datetime
import zipfile
import time
try:
    import re
except:
    print('regular expressions not available')

import DataUtilities3.ZipFileUtilsRella as Zippy

class extrema(object):
    def __init__(self):
        self.minguy = np.inf
        self.maxguy = -np.inf
    
    def addData(self, x):
        if min(x) <= self.minguy: 
            self.minguy = min(x)
        if max(x) >= self.maxguy:
            self.maxguy = max(x)
    
    def get(self):
        return self.minguy, self.maxguy
    
    def get_plotlimits(self, hipad=0.05, lopad=0.05, logscale=False):
        sp = self.maxguy - self.minguy
        if logscale:
            logsp = max([10, self.maxguy/self.minguy])
            rat = logsp**pad
            return [self.minguy/rat, self.maxguy*rat]
        else:
            return [self.minguy - lopad*sp, self.maxguy + hipad*sp]

    def __repr__(self):
        return '%.5g, %.5g' % (self.minguy, self.maxguy)
            

class HandyTool(object):
    def __init__(self, ht, dat):
        self.ht = ht
        self.dat = dat
        
    def P(self,tag):
        return self.dat[:, self.ht.index(tag)]

ParseCRDSName = r'^([A-Z]+)([0-9]{4})-([0-9]{4})([0-9]{2})([0-9]{2})-([0-9]{2})([0-9]{2})([0-9]{2})Z?-([^.]+).(dat|h5)$'

class CRDSFileName():
    def __init__(self, model, SN, yr, mo, day, hr, mn, s, fileType, ext):
        self.model = model
        self.SN = int(SN)
        self.fullName = model+SN
        self.datetime = datetime.datetime(*list(map(int, (yr, mo, day, hr, mn, s))))
        self.fileType = fileType
        self.ext = ext

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
       
class bindat():
    def __init__(self, dat = [], xdat = []):
        self.dat = dat
        self.xdat = xdat
        self.stats()

    def stats(self):
        self.N = len(self.dat)
        if self.N != 0:
            self.m = np.mean(self.dat)
            self.s = np.std(self.dat)
            self.N = len(self.dat)
            self.min = min(self.dat)
            self.max = max(self.dat)
            self.med = np.median(self.dat)
            if len(self.dat) == len(self.xdat):
                self.x = np.mean(self.xdat)
                self.xs = np.std(self.xdat)
            else:
                self.x = None
                self.xs = None
        else:
            self.m = None
            self.s = None
            self.min = None
            self.max = None
            self.med = None
            self.x = None
            self.xs = None

class binAve ():
    """    X - data for establishing the bins
           Y - data to be binned
           xbins - cut points for bins, # bins = len(xbins) - 1
           returns mean, stddev, median, max, min, N in each bin (list of tuples)"""
    def __init__(self, X, Y, xbins, removeEmpty = False, replaceWithEnsemble = False):
        self.X = X
        self.Y = Y
        self.xbins = xbins
        self.bincenters = np.array([0.5*(self.xbins[i] + self.xbins[i+1]) for i in range(len(self.xbins)-1)])
        self.removeEmpty = removeEmpty
        self.replaceWithEnsemble = replaceWithEnsemble
        self.average()
        
        
    def average(self):
        ybins = []
        for i in range(len(self.xbins)-1):
            lo = self.xbins[i]
            hi = self.xbins[i+1]
            thisbin = []
            thisx = []
            for k in range(len(self.X)):
                if lo <= self.X[k] < hi:
                    thisbin.append(self.Y[k])
                    thisx.append(self.X[k])
            ybins.append(bindat(dat = thisbin, xdat = thisx))
        if self.removeEmpty:
            fybins = [Y for Y in ybins if Y.N != 0]
        else:
            fybins = ybins[:]

        self.m = np.array([y.m if y.N != 0 else -999 for y in fybins])
        self.s = np.array([y.s if y.N != 0 else -999 for y in fybins])
        self.N = np.array([y.N for y in fybins])
        self.min = np.array([y.min if y.N != 0 else -999 for y in fybins])
        self.max = np.array([y.max if y.N != 0 else +999 for y in fybins])
        self.med = np.array([y.med if y.N != 0 else 0 for y in fybins])
        self.x = np.array([y.x if y.N != 0 else 999 for y in fybins])
        self.xs = np.array([y.xs if y.N != 0 else 999 for y in fybins])
        
def sparse(j, dat, sigma, nmin):
    # removes outliers that are greater than sigma in dat[:,i], with a minimum number of rows (nmin) remaining in dat
    testFlag = True
    chi = lambda z: z - z.mean()
    while testFlag:
        y = dat[:,j]
        if len(y) <= nmin:
            testFlag = False
        else:
            imax = np.argmax(np.abs(chi(y))) #extreme value
            I = [i for i in range(len(y))]
            I.pop(imax)
            reduced_y = y[I]
            #print y.mean(), reduced_y.mean() - y[imax], reduced_y.std(), y.std()
            if np.abs(y[imax] - reduced_y.mean()) > sigma*reduced_y.std():
                #remove this outlier
                dat = dat[I,:]
            else:
                testFlag = False
    return dat
        
        
        

def pull(X,T,L, okay = None):
    """
    given data X, headtags T, and labels L, return a tuple of 1D arrays corresponding to the columns
    if okay = None, it will pull all columns.  Otherwise, it pulls only those indices listed in the list okay
    """
    outs = []
    for lab in L:
        if okay == None:
            Y = X[:,T.index(lab)]
        else:
            Y = [X[i,T.index(lab)] for i in okay]
        outs.append(np.array(Y))
    return tuple(outs)

def remS(s):
    done = False
    while not(done):
        news = s.replace('  ', ' ')
        if news == s:
            done = True
        s = news
    return s

def unpackZipArchives(sourceDIR, targetDIR=None, verbose=False, overwrite=False):
    files = directoryDrillDown(sourceDIR, ext='.zip', verbose=verbose)
    if targetDIR is None:
        targetDIR = os.path.join(os.path.join(sourceDIR, 'unpackedFiles'))
    if not(os.path.exists(targetDIR)):
        os.mkdir(targetDIR)
    filesThere = len(directoryDrillDown(targetDIR, ext='.h5'))
    if (filesThere == 0) or overwrite:
        totalFilesExtracted = 0
        for fzip in files:
            thisZip = Zippy.PicarroZip(fzip)
            numfiles = thisZip.extractZipFile(targetDIR, verbose=verbose)
            if numfiles is not None:
                totalFilesExtracted += numfiles
        if verbose: print (f'Total Files Extracted = {totalFilesExtracted}')
    else:
        print('files present in target directory -- remove files or set overwrite to True')

def loadFileH5(fn, cload=[], verbose=False):
    return loadFile2(fn,cload=cload, verbose=verbose)

def loadFile2(fn, cload = [], verbose=False):
    ext = fn[-3:]
    if ext == 'dat':
            
        fob = open(fn,'r')
        header = fob.readline(-1)
        headtags = string.split(string.strip(header,' '))
        mydata = []
        stdlen = -1
        if verbose: print('.', end=' ')
        count = 0
        for lines in fob:
            count += 1
            data = string.split(string.strip(lines,' '))
            row = []
            try:
                for k in range(len(headtags)):
                    try:
                        row.append(float(data[k]))
                    except:
                        row.append(-1.0)
                if stdlen == -1:
                    stdlen = len(data)
                if len(data) == stdlen:
                    mydata.append(row)
                else:
                    if verbose: print('?', count)
            except:
                if verbose: print('!', end=' ')
        fob.close()
        
    elif ext == '.h5':
        fob5 = tables.open_file(fn)
        D = [g for g in fob5.root]
        if cload == []:
            headtags = D[0].colnames
        else:
            headtags = cload
        for tag in headtags:
            if tag == headtags[0]:
                datarray = np.array([D[0].col(tag)])
            else:
                datarray = np.vstack((datarray, D[0].col(tag)))

        mydata = np.transpose(datarray)
        count = np.shape(mydata)[0]
        fob5.close()
    if verbose: print("loaded %d rows" % count)

    return headtags, mydata

def loadFilesMFCH5(DIR, N = -1, return_inst_name = '', cload=[],MFC_check = ['valveMask2','MFC3_flowset']):
    files = directoryDrillDown(DIR, ext='.h5')
    dat = None
    count = 1
    for k, f in enumerate(files):
        print("Loading %d / %d... " % (k+1, len(files)))
        ht1, dat1 = loadFileH5(f,cload=cload)
        fnonly = os.path.split(f)[1]
        ind = fnonly.find(return_inst_name) + len(return_inst_name)
        if dat is None:
            res = []
            for c, tag in enumerate(MFC_check):
                temp = [i for i in ht1 if MFC_check[c] in i]
                if temp != []:
                    res.append(temp[0])
            print(res) 
            if res != MFC_check:
                print('No MFC_check data.  Ignoring file')
            else:
                dat = dat1[:]
                ht = ht1
            
        else:
            #print np.shape(dat), np.shape(dat1)
            try:
                dat = np.vstack((dat, dat1))
                ht = ht1
            except:
                print('dat array dimension changed in file %s' % f)
        if count == N:
            if return_inst_name == '':
                return ht, dat
            else:
                return ht, dat, fnonly[0:ind+4]
        count += 1
        
    if return_inst_name == '':
        return ht, dat
    else:
        return ht, dat, fnonly[0:ind+4]


def unixTime(timestamp):
    ORIGIN = datetime.datetime(datetime.MINYEAR,1,1,0,0,0,0)
    UNIXORIGIN = datetime.datetime(1970,1,1,0,0,0,0)
    dt = (ORIGIN-UNIXORIGIN)+datetime.timedelta(microseconds=1000*float(timestamp))
    return 86400.0*dt.days + dt.seconds + 1.e-6*dt.microseconds

def addEpoch(ht, dat, tag = 'timestamp'):
    try:
        exists = ht.index('EPOCH_TIME')
        print('epoch time already in data')
        return ht, dat
    except:
        timeStampRow = ht.index(tag)
        epochTime = dat[:,timeStampRow]
        epochTimeArray = [unixTime(x) for x in epochTime]
        ht1 = copy.deepcopy(ht)
        ht1.append('EPOCH_TIME')
        dat1 = np.column_stack((dat,epochTimeArray))

        return ht1, dat1


def loadColsFromFilesH5(DIR, cols, N = -1, cload = []):
    files = directoryDrillDown(DIR, ext='.h5')
    dat = None
    count = 1
    for k, f in enumerate(files):
        print("Loading %d / %d... " % (k+1, len(files)))
        ht1, dat1 = loadFileH5(f,cload=cload)
        
        try:
            I = [ht1.index(c) for c in cols]
            colPresent = True
        except:
            colPresent = False
        if colPresent:
            if dat is None:
                dat = dat1[:,I]
            else:
                dat = np.vstack((dat, dat1[:,I]))
            if count == N:
                return cols, dat
            count += 1

    return cols, dat


def loadRDFfile(fn, cload = [], verbose=True):
    groupNum = 1 #   /controlData =0 ; /rdData = 1; /sensorData = 2;
    fob5 = tables.open_file(fn)
    D = [g for g in fob5.root]
    if cload == []:
        headtags = D[groupNum].colnames
    else:
        headtags = cload
    for tag in headtags:
        if tag == headtags[0]:
            
            datarray = np.array([D[groupNum].col(tag)])
        else:
            datarray = np.vstack((datarray, D[groupNum].col(tag)))

    mydata = np.transpose(datarray)
    count = np.shape(mydata)[0]
    fob5.close()
    if verbose: print("loaded %d rows" % count)

    return headtags, mydata

def loadRDFfileWithSchemeInfo(fn, cload = [], verbose=True):
    #rewritten using h5py because I couldn't figure out how to read file attributes using pytables
    with h5py.File(fn, 'r') as fob5:
        S = fob5['sensorData']
        sensorColumns = list(S.dtype.fields.keys())
        
        sensorData = {}
        for sc in sensorColumns:
            sensorData[sc] = S[sc]
            
    
        fileAttributes = {}
        for k,v in zip(list(fob5.attrs.keys()), list(fob5.attrs.values())):
            fileAttributes[k] = v
        
        D = fob5['rdData']
        if cload == []:
            headtags = list(D.dtype.fields.keys())
        else:
            headtags = cload
        mydata = np.zeros((D.shape[0], len(headtags)))
        for j, tag in enumerate(headtags):
            mydata[:,j] = D[tag]
  
        if mydata.shape[0] == 0:
            mydata = None
            headtags = None

    return headtags, mydata, sensorData, fileAttributes

def loadRDFfileWithSchemeInfoOld(fn, cload = [], verbose=True):
    #rewritten using h5py because I couldn't figure out how to read file attributes using pytables
    fob5 = h5py.File(fn)
    S = fob5['sensorData']
    sensorColumns = list(S.dtype.fields.keys())
    
    sensorData = {}
    for sc in sensorColumns:
        sensorData[sc] = S[sc]
        
    D = fob5['rdData']
    
    fileAttributes = {}
    for k,v in zip(list(fob5.attrs.keys()), list(fob5.attrs.values())):
        fileAttributes[k] = v
    

    if len(D[headtags[0]]) > 0:
        for tag in headtags:
            
            if tag == headtags[0]:
                
                datarray = np.array([D[tag]])
            else:
                datarray = np.vstack((datarray, D[tag]))
    
        mydata = np.transpose(datarray)
        count = np.shape(mydata)[0]
        if verbose: print("loaded %d rows" % count)
        fob5.close()
    else:
        mydata = None
        if verbose: print("no data in file")
    return headtags, mydata, sensorData, fileAttributes

def cleaner(ht, dt, key, condition, verbose = True):
    """cleans data based on a given column name & condition (in an eval statement, where y is the variable name to be evaluated)"""
    if type(key) is list:
        col = [ht.index(k) for k in key]
    else:
        col = ht.index(key)
    deleters = []
    for i, y in enumerate(dt[:,col]):
        if eval(condition):
            deleters.append(i)
    newguy =  np.delete(dt, deleters, axis = 0)
    if verbose:
        if type(key) is list:
            stuffs = key
        else:
            stuffs = [key]
        stuffs.extend([condition, ' cleaned %d | %d remaining' % (len(deleters), len(newguy[:,0]))])
        print(' | '.join(stuffs))
    return newguy

def loadFile(fn, DELIM = ' ', maxlines = -1, strdat = False, verbose = True, extraread = 0):
    """returns headtags, data (and raw string data, if strdat = True) in array form"""
    fob = open(fn,'r')
    
    for i in range(extraread):
        fob.readline(-1)
    header = fob.readline(-1)    
    header = header.strip(' ')
    if DELIM == ' ':  header = remS(header)
    headtags = header.strip(' ').split(DELIM)
    mydata = []
    if strdat: mystrdat = []
    stdlen = -1
    if verbose:
        print('.', end=' ')
    count = 0
    for lines in fob:

        count += 1
        ll = lines.strip(' ')
        if DELIM == ' ':  ll = remS(ll)
        data = ll.strip(' ').split(DELIM)
        row = []
        if strdat: strrow = []
        try:
            for k in range(len(headtags)):
                if strdat: strrow.append(data[k])
                try:
                    row.append(float(data[k]))
                except:
                    row.append(-1.0)
            if stdlen == -1:
                stdlen = len(data)
            if len(data) == stdlen:
                if strdat: mystrdat.append(strrow)
                mydata.append(row)
            else:
                if verbose:
                    print('?', count, fn)
        except:
            if verbose:
                print('!', end=' ')
        if count == maxlines: break
        if count%10000 == 0 and verbose: print('-', end=' ')
    if verbose:
        print("loaded %d rows" % count)
    fob.close()
    for k in range(len(headtags)):
        if '\n' in headtags[k]:
            headtags[k] = headtags[k][:-1]
    if strdat:
        return headtags, np.array(mydata), mystrdat
    else:
        return headtags, np.array(mydata)

def directoryDrillDown(DIR, ext = '.dat', verbose=False,nmax=10000):
    """Supply a directory; returns a sorted list of all .dat files within that directory and subdirectory"""
    dirlist = [os.path.abspath(DIR)]
    filelist = []
    counter = 0
    badguy = 0
    dirguy = 0
    while (len(dirlist) != 0):
        if counter > nmax:
            break

        d = dirlist.pop(0)
        fs = os.listdir(d)
        for f in fs:
            fn = os.path.join(d,f)
            if os.path.isdir(fn):
                dirlist.append(fn)
            elif fn[-(len(ext)):] == ext:
                counter += 1
                filelist.append(fn)
            else:
                if verbose and False: print('bad file name: %s' % fn)
                badguy += 1
        dirguy += 1
        if verbose: print (f'{dirguy} dirs evaluated out of {len(dirlist)} found, with {counter} {ext} out of {counter+badguy} files')
    g = lambda x: os.path.split(x)[1]
    return sorted(filelist, key=g)
                
def loadFiles(DIR, N = -1, return_inst_name = ''):
    files = directoryDrillDown(DIR)
    dat = None
    count = 1

    for f in files:
        ht, dat1 = loadFile(f)
        fnonly = os.path.split(f)[1]
        if dat is None:
            dat = dat1[:]
        else:
            dat = np.vstack((dat, dat1))
        if count == N:
            if return_inst_name == '':
                return ht, dat
            else:
                return ht, dat, parseFileName(fnonly)
        count += 1
    if return_inst_name == '':
        return ht, dat
    else:
        return ht, dat, parseFileName(fnonly)

def loadFilesH5(DIR, N = -1, return_inst_name = '', cload=[]):
    files = directoryDrillDown(DIR, ext='.h5')
    dat = None
    count = 1
    for k, f in enumerate(files):
        print("Loading %d / %d... " % (k+1, len(files)))
        ht1, dat1 = loadFileH5(f,cload=cload)
        fnonly = os.path.split(f)[1]
        ind = fnonly.find(return_inst_name) + len(return_inst_name)
        if dat is None:
            dat = dat1[:]
            ht = ht1
        else:
            #print np.shape(dat), np.shape(dat1)
            try:
                dat = np.vstack((dat, dat1))
                ht = ht1
            except:
                print('dat array dimension changed in file %s' % f)
        if count == N:
            if return_inst_name == '':
                return ht, dat
            else:
                return ht, dat, fnonly[0:ind+4]
        count += 1
        
    if return_inst_name == '':
        return ht, dat
    else:
        return ht, dat, fnonly[0:ind+4]

def pullCols(cols, ht, dat):
    if type(cols) is list:
        D = []
        for c in cols:
            i = ht.index(c)
            D.append(dat[:, i])
        return tuple(D)
    else:
        i = ht.index(cols)
        return dat[:, i]


def loadColsFromFiles(DIR, cols, N = -1):
    files = directoryDrillDown(DIR)
    dat = None
    count = 1
    for f in files:
        ht, dat1 = loadFile(f)
        I = [ht.index(c) for c in cols]
        if dat is None:
            dat = dat1[:,I]
        else:
            dat = np.vstack((dat, dat1[:,I]))
        if count == N:
            return cols, dat
        count += 1
    return cols, dat


def bimodalCleaner(Z, sigma=15., minDiff = 0.01):
    """sigma selects on the difference of the means / composite std. dev of the bins;
       minDiff is minimum difference between bin means"""
    if len(Z) < 4:
        return Z, None
    Z = np.sort(Z)
    
    lowBin = [Z[0]]
    hiBin = [Z[-1]]
    s = 1
    e = len(Z) - 2
    flag = True
    while flag:
        lowmean = np.mean(lowBin)
        himean = np.mean(hiBin)
        dlow = abs(Z[s] - lowmean)
        dhi = abs(Z[e] - himean)
        if s == e:
            flag = False
        if dlow <= dhi:
            lowBin.append(Z[s])
            s += 1
        else:
            hiBin.append(Z[e])
            e -= 1
    if len(lowBin) > len(hiBin):
        goodbin, badbin = lowBin, hiBin
    else:
        goodbin, badbin = hiBin, lowBin
        
    if len(badbin) <= 1:
        return Z, None
    siggy = np.sqrt(np.std(goodbin)**2 + np.std(badbin)**2)
    diff = abs(np.mean(goodbin) - np.mean(badbin))
    if (diff/siggy > sigma) and (diff > minDiff):
        return (np.array(goodbin), np.array(badbin))
    else:
        return (Z, None)
    
def sigmaFilter(X, n=5):
    """X is the data set; n is the number of sigma to filter from the group"""
    if max(abs(X - X.mean())) > n*X.std():
        i = np.argmax(abs(X - X.mean()))
        X = np.delete(X, i)
        X = sigmaFilter(X,n=n)
    return X

def WA(X, n, mode = 'mean', removeOutlierSigma=-1):
    N = len(X)
    M = int(N/n)
    X_ave = []
    for m in range(M-1):
        if removeOutlierSigma > 0.0:
            Z = sigmaFilter(X[m*n:m*n+n], n=removeOutlierSigma)
        else:
            Z = X[m*n:m*n+n]
        if mode == 'mean':
            thing = np.mean(Z)
        elif mode == 'median':
            thing = np.median(Z)
        X_ave.append(thing)
    return np.array(X_ave)
    
def MA(X, n):
    N = len(X)
    X_ave = []
    for m in range(N):
        s = max([0,m - int(round(n/2))])
        e = min([N-1, m + int(round(n/2))])
        X_ave.append(np.mean(X[s:e]))
    return np.array(X_ave)
    
def delByTime(T, Y, tmin, tmax):
    deleters = []
    for i, t in enumerate(T):
        if t < tmin or t > tmax:
            deleters.append(i)
    return np.delete(T, deleters), np.delete(Y, deleters)

def SpeciesAnalysis(ht, dat, s='species', filterMostCommon=False):
    S = dat[:, ht.index(s)]
    K, N = [], []
    for ss in S:
        if ss in K:
            ind = K.index(ss)
            N[ind] += 1
        else:
            K.append(ss)
            N.append(0)
    imax = np.argmax(N)
    for i, k in enumerate(K):
        print('%s: %d (%d)' % (s, k, N[i]))
    filterGuy = 'y != %d' % K[imax]
    if filterMostCommon:
        dat = cleaner(ht, dat, s, filterGuy)
    return ht, dat, K[imax]


class FullFileLoad():
    def __init__ (self, DIR, N = -1, ext = '.dat', filterMostCommon=False, pullList = [],
                  sparseByN = 1, start=0, end=-1):
        self.DIR = DIR
        self.N = N
        self.ext = ext
        self.pullList = [self.cleanTag(pl) for pl in pullList]
        if self.ext == '.dat':
            self.actual_ht, self.dat = loadFiles(self.DIR, N=self.N)
        elif self.ext == '.h5':
            self.actual_ht, self.dat = loadFilesH5(self.DIR, N=self.N)
        self.ht = []
        for tag in self.actual_ht:
            taggy = self.cleanTag(tag)
            if taggy is not None:
                self.ht.append(taggy)
        if filterMostCommon == True:
            self.ht, self.dat, self.mostCommonSpecies = SpeciesAnalysis(self.ht, self.dat, filterMostCommon=filterMostCommon)
        self.pullList = pullList
        self.sparseByN = sparseByN
        print(self.ht)
        self.makeTemporaryModule()
        self.updateStartEnd(start=start, end=end)
    
    def updateStartEnd(self, start=0, end=-1):
        import CRDSDataName
        self.R = CRDSDataName.dataStructure(self.ht, self.sparseMe(self.dat[start:end,:]), pullList=self.pullList)
        
    def makeTemporaryModule(self):
        fn = os.path.join(os.path.dirname(__file__), 'moduleTemplate.txt')
        f_in = open(fn,'r')
        txt = f_in.read(-1)
        f_in.close()
        for tag in self.ht:
            txt += '        self.%s = None\n' % tag
        fn_out = os.path.join(os.path.dirname(__file__), 'CRDSDataName.py')
        fout = open(fn_out, 'w')
        fout.write(txt)
        fout.close()
        
    def cleanTag(self,tag):
        if len(tag) > 0:
            if tag[0] in '0123456789':
                tag = '_' + tag
            tag = tag.replace(r'-',r'_')
            return tag
        else:
            return None
    
    def sparseMe(self,D):
        if self.sparseByN > 1:
            
            for k in range(D.shape[1]):   #go through each column
                X = WA(D[:,k], self.sparseByN)
                if k == 0:
                    tempD = X
                else:
                    tempD = np.vstack((tempD, X))
            return np.transpose(tempD)
        else:
            return D

class datFileContinuousFeed():
    def __init__ (self, DIR, N=-1, ext='.dat', filterMostCommon=False, pullCols = []):
        self.DIR = DIR
        self.N = N
        self.ext = ext
        self.filterMostCommon = filterMostCommon
        self.files = directoryDrillDown(self.DIR, ext=self.ext)
        self.files = self.files[:self.N]
        self.dat = None
        self.ht = None
        self.pullCols = pullCols
        self.loadNextFile()
        
    
    def loadNextFile (self):
        if len(self.files) > 0:
            print(len(self.files), end=' ')
            nextFile = self.files.pop(0)
            if self.ext == '.dat':
                ht, dat = loadFile(nextFile)
            elif self.ext == '.h5':
                ht, dat = loadFileH5(nextFile, cload=self.pullCols)
            if self.ht is None:
                print(ht)
                self.ht = ht
            elif self.ht != ht:
                print("Column Names Changed!")
                print(nextFile)
                print("x "*10)
                print(nextFile)
            if self.dat is None:
                self.dat = dat[:]
            else: 
                 self.dat = np.vstack((self.dat, dat))
    
    def __iter__(self):
        return self
        
    def __next__(self):
        if self.dat.shape[0] < 10:
            self.loadNextFile()
        try:
            X = self.dat[0,:]
            self.dat = self.dat[1:, :]
            return X
        except:
            raise StopIteration

def breakPlot(A, X, Y, dxmax, **kwargs):
    """breaks one continuous plot into single line plots when the dx exceeds dxmax"""
    bigX, bigY = [], []
    xstart = 0
    for j in range(len(X)-1):
        if X[j+1] - X[j] > dxmax:
            bigX.append(X[xstart:j])
            bigY.append(Y[xstart:j])
            xstart = j+1
    bigX.append(X[xstart:])
    bigY.append(Y[xstart:])
    for bx, by in zip(bigX, bigY):
        A.plot(bx, by, **kwargs)
    return A

def breakPlotPanel(X, Y, dxmax, minPlotSize=10, **kwargs):
    """breaks one continuous plot into separate panels when dx exceeds dxmax"""
    from StickyGasAnalysis.Utilities import MPL_rella as RMPL
    bigX, bigY = [], []
    xstart = 0
    ymx = np.max(Y)
    ymn = np.min(Y)
    ysp = ymx - ymn
    ylim = [ymn - 0.1*ysp, ymx + 0.1*ysp]
    for j in range(len(X)-1):
        if X[j+1] - X[j] > dxmax:
            if len(X[xstart:j]) > minPlotSize:
                bigX.append(X[xstart:j])
                bigY.append(Y[xstart:j])
            xstart = j+1
    if len(X[xstart:]) > minPlotSize:
        bigX.append(X[xstart:])
        bigY.append(Y[xstart:])
    Npanels = len(bigX)

    if Npanels > 1:
        A, F = RMPL.Maker(size = (3.0*Npanels, 4), grid=(1,Npanels))
        bigZ = list(zip(bigX, bigY))
        for j, z in enumerate(bigZ):
            A[j].plot(z[0], z[1], **kwargs)
            A[j].set_ylim(ylim)
    else:
        A, F = RMPL.Maker()
        for bx, by in zip(bigX, bigY):
            A.plot(bx,by, **kwargs)

    return A, F

def findHT(taglist, ht):
    for tag in taglist:
        if tag in ht:
            return tag
    print('tag not found')
    return None

if __name__ == "__main__":

    fn = r'AMBDS2030-20170921-085820-DataLog_User.dat'
    
    X  = parseFileName(fn)
    X.model
