# -*- coding: utf-8 -*-
"""
Created on Wed May 17 13:54:54 2017

@author: chris
"""

import DataUtilities3.MPL_rella as RMPL
import DataUtilities3.RellaColor as RC
import DataUtilities3.load_files_rella as LF

import numpy as np
import os
import time
from collections import defaultdict



def sparseFilter(loss, sigma=4.0):
    indices = [i for i in range(len(loss))]
    flag = len(loss) >= 3
    while flag:
        thisloss = loss[indices]
        dloss = thisloss - thisloss.mean()
        maxIndex = np.argmax(abs(dloss))
        maxguy = indices[maxIndex]
        indices.pop(maxIndex)
        outlier = abs(loss[maxguy] - loss[indices].mean())
        if outlier / loss[indices].std() >= sigma:
            flag = True
        else:
            flag = False
        flag = flag & (len(indices) >= 4)
    return indices
  
class RDF():
    basicFilterSet = [{'mode':'ppbcm'},
                      {'mode':'nusort'},
                      {'mode':'nuset', 'maxDNu':0.03},
                      {'mode':'range', 'minLoss':100.0, 'maxLoss':1e4},
                      {'mode':'sparse', 'sigma':4.0, 'maxDNu':6e-3}]
    def __init__(self):
        self.ht = None
        self.dat = None
        self.npoints = None
        self.sensors = None
        self.fileInfo = None
        self.c4 = RC.Tetrad(primary = 1, useRGY=True)
        self.numfn = 0
        self.loadNames()

    def loadNames(self):
        self.lossname = 'uncorrectedAbsorbance'
        self.nusetname = 'waveNumberSetpoint'
        self.numeasname = 'waveNumber'
        self.timename = 'timestamp'
        self.pztname = 'pztValue'
        self.Pname = 'cavityPressure'
        self.tunername = 'tunerValue'
        self.Tname = 'CavityTemp'
        self.cload = [self.lossname, self.nusetname, self.numeasname, self.pztname, self.timename]
        
    def addFile (self, fn):
        ht, dat = LF.loadRDFfile(fn, verbose=False)
        self.numfn += 1
        if self.ht == None:
            self.ht = ht
            self.dat = dat
        else:
            if self.ht != ht:
                print('column names have changed!')
                print('OLD names ***')
                print(self.ht)
                print('\nNEW names')
                print(ht)
            else:
                self.dat = np.vstack((self.dat, dat))
    
    def addFullFile (self, fn):
        ht, dat, sensors, fileInfo = LF.loadRDFfileWithSchemeInfo(fn, verbose=False, cload=self.cload)
        self.numfn += 1
        if self.ht == None:
            self.ht = ht
            self.dat = dat
            self.sensors = sensors
            self.fileInfo = [fileInfo]
        else:
            if self.ht != ht:
                print('column names have changed!')
                print('OLD names ***')
                print(self.ht)
                print('\nNEW names')
                print(ht)
            else:
                self.dat = np.vstack((self.dat, dat))
                self.fileInfo.append(fileInfo)
                for k,v in self.sensors.items():
                    self.sensors[k] = np.append(v,sensors[k])
    
    def checkIT (self):
        print(self.ht)
        print(self.dat.mean(axis=0))

    def getColumn(self, columnName):
        return self.dat[:, self.ht.index(columnName)]
    
    def getCommon(self, params = ['waveNumberSetpoint', 'uncorrectedAbsorbance', 'waveNumber']):
        if self.npoints is None:
            return tuple([self.getColumn(p) for p in params])
        else:
            thing = [self.getColumn(p) for p in params]
            thing += [self.npoints]
            return tuple(thing)

    def convertToPPBCM(self):
        self.dat[:, self.ht.index(self.lossname)] *= 1000.0

    def sortByNu(self):
        nu = self.dat[:, self.ht.index(self.numeasname)] 
        self.dat = self.dat[np.argsort(nu),:]
        
    def applyNuSetFilter(self, filterDict):
        maxDNu = filterDict['maxDNu']
        nuset = self.dat[:, self.ht.index(self.nusetname)]
        numeas = self.dat[:, self.ht.index(self.numeasname)]
        good = (abs(nuset - numeas) < maxDNu)
        self.dat = self.dat[good, :]
  
    def applyRangeFilter(self, filterDict):
        minLoss = filterDict['minLoss']
        maxLoss = filterDict['maxLoss']
        loss = self.getColumn(self.lossname)
        good = (loss > minLoss) & (loss < maxLoss)
        self.dat = self.dat[good, :]
    
    def applySparsefilter(self, filterDict):
        sigma = filterDict['sigma']
        maxDNu = filterDict['maxDNu']
        
        i_loss = self.ht.index(self.lossname)
        i_numeas = self.ht.index(self.numeasname)
        blockIndices = [[]]
        nu = self.dat[:, i_numeas]
        for j in range(len(nu)):
            if len(blockIndices[-1]) == 0:
                blockIndices[-1].append(j)
            else:
                theseNU = nu[blockIndices[-1]]
                maxNU = max((max(theseNU), nu[j]))
                minNU = min((min(theseNU), nu[j]))
                if (maxNU - minNU) > maxDNu:
                    blockIndices.append([j])
                else:
                    blockIndices[-1].append(j)
        newdat = np.zeros((len(blockIndices), len(self.dat[0,:])))
        newpoints = np.zeros(len(blockIndices))
        for b, block in enumerate(blockIndices):
            blockdat = self.dat[block, :]
            bloss = blockdat[:, i_loss]
            good = sparseFilter(bloss, sigma=sigma)
            newdat[b,:] = blockdat[good,:].mean(axis=0)
            newpoints[b] = len(blockdat[good,0])
        self.dat = newdat
        self.npoints = newpoints
    
    def applyFilters(self, filterList=[]):
        for filt in filterList:
            if filt['mode'] == 'ppbcm':
                self.convertToPPBCM()
            elif filt['mode'] == 'nusort':
                self.sortByNu()
            elif filt['mode'] == 'range':
                self.applyRangeFilter(filt)
            elif filt['mode'] == 'sparse':
                self.applySparsefilter(filt)
            elif filt['mode'] == 'nuset':
                self.applyNuSetFilter(filt)
                
    def makeGroups (self):
        """creates a groupedDat dictionary tree of lasers and wavelengths"""
        rows = self.dat.shape[0]
        key='waveNumberSetpoint'
        laser = 'laserUsed'
        self.lasers = []
        self.values = []
        self.groupedDat = {}
        k = self.ht.index(key)
        kl = self.ht.index(laser)
        for r in range(rows):
            if r % int(rows / 20.) == 0: print('-', end=' ')
            v = '%.5f' % self.dat[r,k]
            l = '%d' % self.dat[r,kl]
            if l in self.groupedDat:
                if v in self.groupedDat[l]:
                    self.groupedDat[l][v] = np.vstack((self.groupedDat[l][v], self.dat[r,:]))
                else:
                    self.groupedDat[l][v] = self.dat[r,:]
            else:
                #print 'new laser: ', self.dat[r, kl]
                self.lasers.append(int(self.dat[r,kl]))
                self.groupedDat[l] = {v:self.dat[r,:]}
        print('x')

    def columnStatistics(self, laserNum, lowlim=0.1, highlim=30.0):
        g = lambda x: self.ht.index(x)
        ky = g('uncorrectedAbsorbance')
        spectrum = self.groupedDat['%d' % laserNum]
        self.outStuff = {}
        for tag in self.ht:
            self.outStuff[tag] = [[],[]]
        for wvnset in spectrum:
            D = spectrum[wvnset]
            loss = D[:,ky]
            good = (loss > lowlim) & (loss < highlim)
            for j, tag in enumerate(self.ht):
                self.outStuff[tag][0].append(D[good,j].mean())
                self.outStuff[tag][1].append(D[good,j].std())
        for stuff in self.outStuff:
            self.outStuff[stuff][0] = np.array(self.outStuff[stuff][0])
            self.outStuff[stuff][1] = np.array(self.outStuff[stuff][1])

            
    def generateNuAndAbs(self, laserNum, removeOutliers=False, removeBadRingdowns=True):
        g = lambda x: self.ht.index(x)
        
        kx = g('waveNumberSetpoint')
        kxmeas = g('waveNumber')
        ky = g('uncorrectedAbsorbance')
        
        X, sX = [], []
        Y, sY = [], []
        N = []
        spectrum = self.groupedDat['%d' % laserNum]
        removed = 0
        total = 0
        lowlim = 0.1
        highlim = 30.0

        for wvnset in spectrum:
            D = spectrum[wvnset]
            if removeBadRingdowns:
                loss = D[:,ky]
                good = (loss > lowlim) & (loss < highlim)
                M = len(loss) - sum(good)
                D = D[good,:]
                
            if removeOutliers:
                nD = LF.sparse(ky, D, 5, 4)
                M += len(D[:, 0]) - len(nD[:,0])
            else:
                nD = D
            
            removed += M
            total += len(D[:,0])
            #if M > 1: print '%d removed (%d remaining)' % (M, len(nD[:,0]))
            X.append(nD[:,kxmeas].mean())
            sX.append(nD[:,kxmeas].std())
            Y.append(nD[:,ky].mean())
            sY.append(nD[:,ky].std())
            N.append(len(nD[:,ky])/self.numfn)
        self.X = np.array(X)
        self.sX = np.array(sX)
        self.Y = np.array(Y)
        self.sY = np.array(sY)            
        return removed, total

    def makeFlatSpectrum(self, useSparse=False,sortMe=False, removeBad=False):
        g = lambda x: self.ht.index(x)
        
        kx = g('waveNumberSetpoint')
        kxmeas = g('waveNumber')
        ky = g('uncorrectedAbsorbance')
        
        self.nuset = []
        self.loss = []
        for laser in self.groupedDat:
            spectrum = self.groupedDat[laser]
            for wvnset in spectrum:
                D = spectrum[wvnset]
                if len(D.shape) == 1:
                    D = np.array([D])
                
                good = (D[:,ky]>0.3) & (D[:,ky]<20.0)
                D = D[good,:]
                if useSparse:
                    D = LF.sparse(ky, D, 2.5, 4)
                self.nuset.append(D[:,kx].mean())
                self.loss.append(D[:,ky].mean())
        
        self.nuset = np.array(self.nuset)
        self.loss = np.array(self.loss)
        if sortMe:
            I = np.argsort(self.nuset)
            self.nuset = self.nuset[I]
            self.loss = self.loss[I]
            

    def generateSpectralFourPlot(self, outDIR=None):
        g = lambda x: self.ht.index(x)
        kx = g('waveNumberSetpoint')
        kxmeas = g('waveNumber')
        ky = g('uncorrectedAbsorbance')
        for laser in self.groupedDat:
            #iterate over lasers
            A, F = RMPL.Maker(grid=(4,1), size = (5.5,8))
            
            X, sX = [], []
            Y, sY = [], []
            N = []
            spectrum = self.groupedDat[laser]
            for wvnset in spectrum:
                D = spectrum[wvnset]
                X.append(D[:,kxmeas].mean())
                sX.append(D[:,kxmeas].std())
                Y.append(D[:,ky].mean())
                sY.append(D[:,ky].std())
                N.append(len(D[:,ky])/self.numfn)
            X = np.array(X)
            sX = np.array(sX)
            Y = np.array(Y)
            sY = np.array(sY)
            A[0].scatter(X, Y, c = self.c4[0], edgecolor = 'none', s = 80)
            A[1].scatter(X, sY, c = self.c4[1], edgecolor = 'none', s = 80)
            A[2].scatter(X, sY/Y*100.0, c = self.c4[2], edgecolor = 'none', s = 80)
            A[3].scatter(X, sX, c = self.c4[3], edgecolor = 'none', s = 80)
            
            xlim = RMPL.getTightRange(X)
            
            thisY = [Y, sY, sY/Y*100.0, sX]
            ylab = ['loss [ppm/cm]', 'loss noise [ppm/cm]', 'shot-to-shot [%]', 'freq. target [wvn]']
            for j, a in enumerate(A):
                a.scatter(X, thisY[j], c = self.c4[j], edgecolor = 'none', s = 80)
                ylim = RMPL.getTightRange(thisY[j], lowpadX=0.1, highpadX=0.25)
                a.set_xlim(xlim)
                a.set_ylim(ylim)
                a.set_ylabel(ylab[j])
                if j == 0:
                    a.set_title('Laser %s' % laser)
                    yspan = ylim[1] - ylim[0]
                    for jn, n in enumerate(N):
                        a.annotate('%d' % n, xy = (X[jn], thisY[j][jn] + 0.07*yspan), fontsize = 10, ha = 'center')
                if j < 3:
                    a.set_xticklabels([])
                else:
                    a.set_xlabel('frequency [wvn]')
            for n in N:
                A[0]
            F.tight_layout()
            F.show()
            if outDIR is not None:
                fn = os.path.join(outDIR, 'laser_%s_FourPlot.png' % laser)
                F.savefig(fn, dpi = 400)

class TimeRDF(object):
    def __init__ (self, files, verbose=False, averageSchemeRow=False, updateFunc = None):
        #provide a list of files to load
        self.rdf = RDF()
        self.files = files
        self.verbose = verbose
        if updateFunc is not None:
            self.updateFunc = updateFunc
        else:
            self.updateFunc = self.passguy
        
        for fn in self.files:
            print('x', end=' ')
            self.rdf.addFile(fn)
        if self.verbose:
            self.rdf.checkIT()
        if averageSchemeRow:
            self.schemeRowMean()
        else:
            self.dat = self.rdf.dat
    
    def passguy(self):
        pass
    
    def schemeRowMean(self):
        print()
        ndat = None
        s = 0
        sr = 0
        nrows = self.rdf.dat.shape[0]
        kschemeRow = self.rdf.ht.index('schemeRow')
        for j in range(nrows):
            if j % 5000 == 0: self.updateFunc()
            if self.rdf.dat[j,kschemeRow] != sr:

                sr = self.rdf.dat[j,kschemeRow]
                if j != 0:
                    ave = np.mean(self.rdf.dat[s:j,:],axis=0)
                    if ndat is None and s != j:
                        ndat = ave
                        
                    else:
                        ndat = np.vstack((ndat, ave))
                    s = j
        self.dat = ndat
        
    def getColumn(self, columnName):
        return self.dat[:, self.rdf.ht.index(columnName)]
    
    def getKeyColumns(self):
        self.T = self.getColumn('timestamp')
        self.nu = self.getColumn('waveNumber')
        self.nuset = self.getColumn('waveNumberSetpoint')
        self.loss = self.getColumn('uncorrectedAbsorbance')

    def makePlots(self, plotMeanOnly=True):
        self.rdf.makeGroups()
        
        meanX, meanY = [], []
        for lasernum in self.rdf.lasers:
            self.rdf.generateNuAndAbs(lasernum)
            meanX.append(self.rdf.X)
            meanY.append(self.rdf.Y)
        return meanX, meanY
                
            
def processMultipleRDF(filelist, runMakeGroups=True):
    rdf = RDF()
    for fn in filelist:
        rdf.addFile(fn)
    #rdf.checkIT()
    if runMakeGroups:
        rdf.makeGroups()
    return rdf
    
def main(DIR=None, Nfiles=-1):
    start = time.time()
    
    RMPL.SetTheme('FIVE')
    
    if DIR == None:
        DIR = r'C:\Users\chris\Desktop\tester\Oxygen\Fitter\SampleRDFs'
    
    outputDIR = os.path.join(DIR, 'outputs')
    if os.path.exists(outputDIR) != True:
        os.mkdir(outputDIR)
        
    files = LF.directoryDrillDown(DIR, ext = '.h5')
    count = 0    
    
    rdf = RDF()
    
    for fn in files[:]:
        if count < Nfiles or Nfiles < 0:
            rdf.addFile(fn)
            count += 1
            print(count, end=' ')
        else:
            break
        RDF
    
    rdf.checkIT()
    print(rdf.dat.shape)
    rdf.makeGroups()
    #rdf.generateSpectralFourPlot(outDIR=outputDIR)
    return rdf

    
if __name__ == '__main__':
    DIR = r'C:\Users\chris\Desktop\tester\Oxygen\Fitter\SampleRDFs'
    #DIR = r'R:\crd_G2000\TADS\2925-TADS2000\Special Tests\RDF analysis\20170807 - RDF samples\starting point'
    rdf = main(DIR=DIR, Nfiles=10)
    