# -*- coding: utf-8 -*-
"""
Created on Mon Jun 23 13:49:41 2014

@author: chris
"""

import numpy as np
import random
import matplotlib.pyplot as plt
from DataUtilities3 import MPL_rella as RMPL
#from plotting_utilities 

eps = 1e-21
def linearFit(X, Y, W=1.0): 
    """for individually weighted points, supply W the same length array as X and Y"""
    n = len(X)
    W = W/np.sum(W)
    X_bar = np.sum(X*W)
    Y_bar = np.sum(Y*W)
    SS_xx = np.sum(W*(X - X_bar)**2)
    SS_xy = np.sum(W*(X - X_bar)*(Y - Y_bar))
    m = SS_xy / SS_xx
    b = Y_bar - m*X_bar
    chi1 = np.sum(W*(Y - Y_bar)**2)
    chi2 = np.sum(W*(Y - m*X - b)**2)
    r2 = 1. - chi2/(chi1+eps)
    if r2 < 0:
        print(r2)
        raise ValueError
    return (m, b), r2

class PCA():
    """Alist is the list of independent columns"""
    def __init__(self, Alist, plotme = False, labels = None):
        self.Alist = Alist
        self.eigen = None
        self.C = None
        self.labels = labels
        self.plotme = plotme
        self.calc_PCA()
        self.VectVal()
        if self.plotme:
            self.Plotter()
            
    def combo(self,m):
        L = []
        for i in range(m-1):
            for j in range(i+1,m,1):
                L.append((i,j))
        return L
    
    def Plotter(self):
        #cmap = plt.get_cmap('RdPu')
        
        L = self.combo(self.m)
        for pair in L:
            x = pair[0]
            y = pair[1]
            A, F = RMPL.Maker(size = RMPL.FS12)
            alph = min(1.0, 10.0/self.n**0.5)
            sz = min(100, 100/self.n**0.3)
            A.scatter(self.Alist[x], self.Alist[y], s = sz, edgecolors = 'none', alpha = alph)
            if self.labels != None:
                A.set_xlabel(self.labels[x])
                A.set_ylabel(self.labels[y])
            F.tight_layout()
            F.show()
        
        
    def VectVal(self):
        VM = self.eigen[1]
        EVect = []
        for i in range(self.m):
            EVect.append(VM[:,i])
        self.evect = EVect
        self.EV = self.eigen[0]
        return
        
    def calc_PCA(self):
        NA = []
        
        for a in self.Alist:
            NA.append(a - np.mean(a))

        (self.m, self.n) = np.shape(self.Alist)
        A = np.matrix(NA)
        C =  1.0/(self.n-1.0)*A*A.T
        self.eigen = np.linalg.eig(C)
        self.C = C
        return
        
class LSQ:
    """ Alist is a list of independent columns
    """
    def __init__(self,Alist, y, e=None, plotme = None, labels = None, xlabel = '', ylabel = '', parameterNames=[]):
        self.Alist = Alist
        self.y = y
        if e is None:
            self.e = np.ones(y.shape)
        else:
            self.e = e
        self.plotme = plotme
        self.A = None
        self.result = None
        self.err_result = None
        self.residuals = None
        self.std_residuals = None
        self.eigenvalues = None
        self.eigenvectors = None
        self.CL = None
        self.fity = None
        self.R2 = None
        if labels != None:
            self.labels = labels
        else:
            self.labels = ['' for i in range(len(Alist))]
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.parameterNames = parameterNames
        if len(parameterNames) == 0:
            self.parameterNames = ['A%d' % i for i in range(len(Alist))]
        self.fitLSQ()

    
    def __str__(self):
        txt = ''
        for k in range(len(self.result)):
            if self.labels[k] == '':
                sl = ''
            else:
                sl = ' (%s) ' % self.labels[k]
            paramtxt = self.parameterNames[k]
            txt += "%s %s= %.7g +/- %.6g\n" % (paramtxt,sl,self.result[k],self.err_result[k])
        txt +=  "R squared = %.6g\n" % self.R2
        txt +=  "std dev residuals = %.6g\n" % self.std_residuals
        
        return txt    
    
    def reportCL(self,B):

        unc = B*self.eigenvectors*self.eigenvalues
    
        rows, cols = np.shape(unc)
        
        CL = []
        for r in range(rows):
            thisrow = []
            for k in range(cols):
                thisrow.append(unc.item(r,k)**2)
            CL.append(np.sqrt(sum(thisrow)))
        CLa = np.array(CL)
        return CLa
    
    def makeMatrix(self,Xlist):

        return np.matrix(Xlist).T
        
    def fitLSQ(self):     
         # Alist is a list of 1-D arrays that corresponds to the different parameters that will be fit
        atlist = []
        for al in self.Alist:
            atlist.append(al/self.e)

        A = self.makeMatrix(atlist)
        bigA = self.makeMatrix(self.Alist)
        
        self.A = bigA
        
        Y = np.matrix(self.y)
        E = np.matrix(self.e)    
        YE = Y/E
        AT = A.T
        P = AT*A
        Q = P.I
        
        eigen = np.linalg.eig(Q)
        #print "eigenvalues: ", eigen[0]
        #print "\neigenvectors"
        #print eigen[1]
        
        self.eigenvectors = eigen[1]

        R = Q*AT
        result = R*YE.T
        self.result = [r.item() for r in result]
        self.resultDict = {}
        for pname, res in zip(self.parameterNames, self.result):
            self.resultDict[pname] = res
        LM = np.sqrt(np.diag(eigen[0]))         #create diagonal matrix with eigenvalues
        self.eigenvalues = LM
        
        CLa = self.reportCL(bigA)
  
        self.CL = CLa
        
        err_result = np.matrix(np.sqrt(np.diag(Q))).T
        
        self.err_result = [er.item() for er in err_result]
        
        self.fity = np.array(bigA*result)[:,0]
        residuals = np.array(Y.T - bigA*result)[:,0]
        self.residuals = residuals
        self.std_residuals = np.std(residuals)
        self.R2 = 1 - np.std(residuals/self.e)**2 / np.std(self.y/self.e)**2 
        
    
        
        pm = self.plotme
        cbarflag = False
        if pm is not(None):
            X = self.Alist[pm[0]]
            if len(pm) <= 1:
                colr = 'blue'
            elif pm[1] == -1:
                colr = list(self.e)
                cbarflag = True
            elif pm[1] >= 0:
                colr = list(self.Alist[pm[1]])
                cbarflag = True
            else:
                colr = 'blue'
            plt.scatter(list(self.Alist[pm[0]]),list(self.y),c = colr, s = 10 + 500/np.sqrt(len(residuals)), alpha = 0.5, edgecolors = 'none')
            if cbarflag: plt.colorbar()
            PX,PY = self.dualSort(list(self.Alist[pm[0]]),list(self.fity))
            plt.plot(PX,PY,'g', linewidth = 2)
            PX,PY = self.dualSort(list(self.Alist[pm[0]]),CLa+self.fity)
            plt.plot(PX,PY,'r--')
            PX,PY = self.dualSort(list(self.Alist[pm[0]]),self.fity-CLa)
            plt.plot(PX,PY,'b--')
            plt.xlabel(self.xlabel)
            plt.ylabel(self.ylabel)
            plt.show()
            #
        return
        
    def dualSort(self,X,Y):      #sorts on X
        Z = list(zip(X,Y))
        Z.sort(key = lambda row: row[0])
        X,Y = list(zip(*Z))
        return X,Y

class LSQ2:
    """ Alist is a list of independent columns
    """
    def __init__(self,FitDict, y, e=None, ):
        self.parameterNames = []
        self.Alist = []
        for name, data in FitDict.items():
            self.parameterNames.append(name)
            self.Alist.append(data)


        self.y = y
        if e is None:
            self.e = np.ones(y.shape)
        else:
            self.e = e

        self.A = None
        self.result = None
        self.err_result = None
        self.residuals = None
        self.std_residuals = None
        self.eigenvalues = None
        self.eigenvectors = None
        self.CL = None
        self.fity = None
        self.R2 = None

        self.fitLSQ()

    
    def __str__(self):
        txt = ''

        U = np.argsort(abs(self.err_result/self.result))
        for k in U:
            paramtxt = self.parameterNames[k]
            txt += "%s = %.7g +/- %.6g\n" % (paramtxt,self.result[k],self.err_result[k])
        txt +=  "R squared = %.6g\n" % self.R2
        txt +=  "std dev residuals = %.6g\n" % self.std_residuals
        
        return txt    
    
    def reportCL(self,B):

        unc = B*self.eigenvectors*self.eigenvalues
    
        rows, cols = np.shape(unc)
        
        CL = []
        for r in range(rows):
            thisrow = []
            for k in range(cols):
                thisrow.append(unc.item(r,k)**2)
            CL.append(np.sqrt(sum(thisrow)))
        CLa = np.array(CL)
        return CLa
    
    def makeMatrix(self,Xlist):

        return np.matrix(Xlist).T
        
    def fitLSQ(self):     
         # Alist is a list of 1-D arrays that corresponds to the different parameters that will be fit
        atlist = []
        for al in self.Alist:
            atlist.append(al/self.e)

        A = self.makeMatrix(atlist)
        bigA = self.makeMatrix(self.Alist)
        
        self.A = bigA
        
        Y = np.matrix(self.y)
        E = np.matrix(self.e)    
        YE = Y/E
        AT = A.T
        P = AT*A
        Q = P.I
        
        eigen = np.linalg.eig(Q)
        #print "eigenvalues: ", eigen[0]
        #print "\neigenvectors"
        #print eigen[1]
        
        self.eigenvectors = eigen[1]

        R = Q*AT
        result = R*YE.T
        self.result = np.array([r.item() for r in result])
        self.resultDict = {}
        for pname, res in zip(self.parameterNames, self.result):
            self.resultDict[pname] = res
        LM = np.sqrt(np.diag(eigen[0]))         #create diagonal matrix with eigenvalues
        self.eigenvalues = LM
        
        CLa = self.reportCL(bigA)
  
        self.CL = CLa
        
        err_result = np.matrix(np.sqrt(np.diag(Q))).T
        
        self.err_result = np.array([er.item() for er in err_result])
        
        self.fity = np.array(bigA*result)[:,0]
        residuals = np.array(Y.T - bigA*result)[:,0]
        self.residuals = residuals
        self.std_residuals = np.std(residuals)
        self.R2 = 1 - np.std(residuals/self.e)**2 / np.std(self.y/self.e)**2 
        
    
        
if __name__=="__main__":
    pass
