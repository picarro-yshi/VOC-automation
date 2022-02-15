# -*- coding: utf-8 -*-
"""
Created on Fri May 10 12:19:45 2019

@author: chris
"""

from experiments.data_processing.DataUtilities import MPL_rella as RMPL
from experiments.data_processing.DataUtilities import RellaColor as RC
from experiments.data_processing.DataUtilities import load_files_rella as LF
from experiments.data_processing.DataUtilities import RDF_analysis_GroupStatistics as RDF
from experiments.data_processing.DataUtilities import allan_stddev_rella as astd
import os
import numpy as np


def outlierFilter(x,threshold,minPoints=2):
    """ Return Boolean array giving points in the vector x which lie
    within +/- threshold * std_deviation of the mean. The filter is applied iteratively
    until there is no change or unless there are minPoints or fewer remaining"""
    good = np.ones(x.shape,np.bool_)
    order = list(x.argsort())
    while len(order)>minPoints:
        maxIndex = order.pop()
        good[maxIndex] = 0
        mu = np.mean(x[good])
        sigma = np.std(x[good])
        if abs(x[maxIndex]-mu)>=(threshold*sigma):
            continue
        good[maxIndex] = 1
        minIndex = order.pop(0)
        good[minIndex] = 0
        mu = np.mean(x[good])
        sigma = np.std(x[good])
        if abs(x[minIndex]-mu)>=(threshold*sigma):
            continue
        good[minIndex] = 1
        break
    return good

dataDIR = r'R:\crd_G9000\AVXxx\1249-AVX80_9001\EtO development\20190906 - CO2 steps\NoiseAnalysisRella'
outDIR = os.path.split(dataDIR)[0]
saver = RMPL.SaveFigure(DIR=outDIR).savefig

rdf = RDF.RDF()
files = os.listdir(dataDIR)
for j in range(-50,-10,1):
    rdf.addFile(os.path.join(dataDIR, files[j]))

rdf.makeGroups()
J = rdf.ht.index('uncorrectedAbsorbance')

spectrum = rdf.groupedDat['0']
uniqueNU = []
ss = []
for k,v in spectrum.items():
    uniqueNU.append(float(k))
    al = astd.Allan(v[:,J])        
    #ss.append(v[:,J].std()/v[:,J].mean()*100.0)
    ss.append(al.S[0]/v[:,J].mean()*100.0)
    
nu, loss, numeas = rdf.getCommon()
good = loss > 0.2
nu, loss, numeas = nu[good], loss[good], numeas[good]
t = rdf.getColumn('timestamp')
print('RD rate = %.2f' % (len(t)/(max(t) - min(t))*1000.))
print('median shot-to-shot = %.4f%%' % (np.median(ss)))
RMPL.SetTheme('SIX')
A,F = RMPL.Maker()
A.scatter(nu, loss, s=3,alpha=0.5, c=RMPL.dkgreen)
saver(F, 'spectrum.png')

A, F = RMPL.Maker()
A.scatter(uniqueNU, ss, s=5,alpha=0.5, c=RMPL.blue)
A.set_yscale('log')
A.set_ylim([0.02, 0.5])
A.set_xlabel('frequency [wvn]')
A.set_ylabel('ss [%]')
saver(F, 'ssVnu.png')

binny = np.linspace(0.01, 0.5, 100)
A,F = RMPL.Maker()
RMPL.StandardHist(A, ss, binny,alpha=0.7, ec=RMPL.dkblue,c=RMPL.blue)
A.set_xlabel('ss [%]')
A.set_ylabel('#')
saver(F,'sshist.png')