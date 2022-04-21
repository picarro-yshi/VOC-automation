# -*- coding: utf-8 -*-
"""
Created on 20190926 1530

@author: rella

NOTES: this is a self contained analysis script for analyzing cross-talk - it takes h5 files as input.  They do not need to be concatenated.
"""

import numpy as np
import os
import tables
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

def Maker(size = (6,4), grid = (1,1), proj = 'rectilinear'):
    """makes a standard figure using gridspec
    returns A, FIG tuple
    Valid values for projection are: [aitoff, hammer, lambert, mollweide, polar, rectilinear]"""
    FIG = plt.figure(figsize=size)
    N = grid[0]*grid[1]
    gs = gridspec.GridSpec(grid[0], grid[1])
    if type(proj) == list:
        p0 = proj[0]
    else:
        proj = [proj for i in range(grid[0] * grid[1])]
        p0 = proj[0]
    if N == 1:
        A = plt.subplot(gs[0], projection = p0)
    else:
        A = []
        n = 0
        for x in range(grid[0]):
            for y in range(grid[1]):
                A.append(plt.subplot(gs[x,y], projection = proj[n]))
                n += 1
    return A, FIG

def directoryDrillDown(DIR, ext = '.dat', verbose=False,nmax=10000):
    """Supply a directory; returns a sorted list of all .dat files within that directory and subdirectory"""
    dirlist = [os.path.abspath(DIR)]
    filelist = []
    counter = 0
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
                if verbose: print('bad file name: %s' % fn)
    g = lambda x: os.path.split(x)[1]
    return sorted(filelist, key=g)
                
def loadFilesH5(DIR, N = -1, return_inst_name = ''):
    files = directoryDrillDown(DIR, ext='.h5')
    dat = None
    count = 1
    for k, f in enumerate(files):
        print("Loading %d / %d... " % (k+1, len(files)), end=' ')
        ht1, dat1 = loadFileH5(f)
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

def loadFileH5(fn, cload = [], verbose=False):
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

def sigmaFilter(X, n=5):
    """X is the data set; n is the number of sigma to filter from the group"""
    if max(abs(X - X.mean())) > n*X.std():
        i = np.argmax(abs(X - X.mean()))
        X = np.delete(X, i)
        X = sigmaFilter(X,n=n)
    return X


def savefigfunc(F, fn=None, dpi=400):
    F.show()
    F.tight_layout()
    if fn is not None:
        F.savefig(fn, dpi=dpi)

def createDIR(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)
    return dirname

class SaveFigure(object):
    def __init__ (self, DIR=None, namecode=''):
        if DIR is not None:
            self.addDIR(DIR)
        else:
            self.DIR = None
        self.namecode = namecode
    
    def addDIR(self,DIR):
        self.DIR = DIR
        if not os.path.exists(self.DIR):
            os.mkdir(self.DIR)
        
    def addNameCode(self,namecode):
        self.namecode=namecode        

    def makeFilePath(self,fn):
        
        thisFN = self.namecode + fn
        if self.DIR is not None:
            thisFN = os.path.join(self.DIR, thisFN)
            
        return thisFN

    def savefig(self,F,fn=None,dpi=400, closeMe=False):
        F.show()
        F.tight_layout()
        
        if fn is not None:
            savefigfunc(F, fn=self.makeFilePath(fn), dpi=dpi)      
        if closeMe:
            plt.close(F)

def polything (coeffs, xsim):
    ysim = np.polyval(coeffs, xsim)
    ylst = ['[%.5e]x^%d' % (c,len(coeffs) - i - 1) for i, c in enumerate(coeffs)]
    ytxt = ' + '.join(ylst)
    return ysim, ytxt

def sparse(j, dat, sigma, nmin):
    # removes outliers that are greater than sigma in dat[:,j], with a minimum number of rows (nmin) remaining in dat
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

homeDIR = r'/Volumes/Data/crd_G9000/AVXxx/1249-AVX80_9001/EtO development/20190924-H2O steps in ZA' #point to root directory
dataDIR = os.path.join(homeDIR, 'private Data') #adjust to point to data subdirectory name.  The h5 files need to be unzipped, but they do not need to be concatenated -- 
outputDIR = os.path.join(homeDIR, 'AnalysisPlotsRellaTest') #plots end up here

ht, dat = loadFilesH5(dataDIR, N=-1) #loads files (-1 loads all, set N to load first N h5 files); returns ht (column names) and dat (2D array of data)

Nave = 45 # number of spectra in average
s = 800   #start points to skip
e = 2000 #end points to skip
h = lambda name: WA(dat[s:-e, ht.index(name)], Nave) #function takes column name 

T = h('JULIAN_DAYS')
T -= T[0]

saver = SaveFigure(DIR=outputDIR).savefig #convenience function for saving

xname = 'H2O'
yname = 'ETO'

A, F = Maker(size=(6,7), grid=(2,1)) #makes a plot object
A[0].plot(T, h(xname), c='blue')
A[0].set_ylabel(xname)
A[1].plot(T, h(yname), c='blue')
A[1].set_ylabel(yname)
A[1].set_xlabel('Time [days]')
saver(F, 'TimeSeries_%s_%s.png' % (xname, yname))

X, Y = h(xname), h(yname)
lin = np.polyfit(X, Y, 1)
quad = np.polyfit(X,Y,2)

xsim = np.linspace(min(X), max(X), 100)
ylin, lintxt  = polything(lin,xsim)
yquad, quadtxt = polything(quad, xsim)

A, F = Maker(size=(6,6))
A.scatter(X, Y, s=20, c='black', alpha=0.5)
A.plot(xsim, ylin, c='red', label = lintxt)
A.plot(xsim, yquad, c='green', label = quadtxt)
A.legend(loc='best', fontsize=12)
A.set_xlabel(xname)
A.set_ylabel(yname)
saver(F, 'Correlation_%s_v_%s.png' % (yname, xname))
