# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 17:54:13 2013

@author: chris
"""

import numpy as np
import string
import matplotlib.pyplot as plt
import copy

sigma = []

class allen():
    
    def __init__(self,data, T=None, calc=True):
        self.data = data
        self.S = []
        self.N = 1
        self.T = []
        self.E = []
        self.white = -1.0
        self.drift = -1.0
        self.fraction = -1.0
        self.N64 = -1.0
        self.fraction64 = -1.0
        if T is None:
            self.dt = 1.0
        else:
            self.dt = self.calcDT(T)
        if calc:
            self.calcAllen()
    def calcDT(self,T):
        return (max(T) - min(T)) / (len(T) - 1)
        
    def calcAllen(self):
        if np.std(self.data) != 0:
            while len(self.data) >= 2:
                y = self.diffstdev(self.data)
                self.S.append(y)
                self.T.append(self.N)
                points = len(self.data)
                ebar = y/np.sqrt(points)
                self.E.append(ebar)
                self.N *= 2.0
                self.data = self.avepair(self.data)
        self.S = np.array(self.S)
        self.T = np.array(self.T)*self.dt
        self.E = np.array(self.E)
        return self.S, self.T, self.E
        
        
    def diffstdev(self,Y):
        x = []
        for i in range(len(Y)-1):
            x.append(Y[i+1]-Y[i])
        if len(x) > 1:
            #a = np.std(x)/np.sqrt(2)
            a = np.sqrt(np.sum(np.array(x)**2)/(len(x)-1)/2)
        else:
            a = abs(x[0])/np.sqrt(2)
        return a
    
    def avepair(self,Y):
        x = []
        for i in range(int(len(Y)/2)):
            x.append(0.5*(Y[2*i]+Y[2*i+1]))
        return x
    
    def allStats(self):
        R = {}
        R['N'] = self.N
        R['white'] = self.white
        R['drift'] = self.drift
        R['N64'] = self.N64
        R['fraction'] = self.fraction
        R['fraction64'] = self.fraction64d
        R['allenstd'] = self.S
        return R

class Allan(allen):
    pass

class accumulateAllan():
    def __init__ (self, N):
        self.N = N
        self.data = [[] for i in range(self.N)]
        
    def addData (self, X):
        n = len(X)
        M = min(n, self.N)
        for m in range(M):
            self.data[m].append(X[m])
    
    def analyzeData (self):
        self.mn = []
        self.median = []
        self.std = []
        self.num = []
        self.T = []
        for i in range(len(self.data)):
            Y = self.data[i]
            if len(Y) != 0:
                self.mn.append(np.mean(Y))
                self.median.append(np.median(Y))
                self.std.append(np.std(Y))
                self.num.append(len(Y))
                self.T.append(i)
            
        self.mn = np.array(self.mn)
        self.median = np.array(self.median)
        self.std = np.array(self.std)
        self.num = np.array(self.num)
        self.T = np.array(self.T)

if __name__ == "__main__":
    #fname = r"S:\CRDS\Applications_dr\applications development\Oil and Gas\002 - laboratory work\3-bottle test\reanalysis 20130923\Valves_Just V16_1379979884.txt"
    fname = r"S:\CRDS\Applications_dr\applications development\Oil and Gas\002 - laboratory work\3-bottle test\reanalysis 20130923\Valves_Just V16_1379981926.txt"    
    f = open(fname,'r')
    header = f.readline(-1)
    nextline = f.readline(-1)
    
    headtags = string.split(header,',')[:-1]
    print(headtags)
    data = []
    count = 3
    bad = [1,2,3,4,5,6,999,1000,1001,1002,1003]
    for line in f:
        if count in bad:
            pass
        else:
            rowtxt = string.split(line,',')[:]
            rowd = [float(a) for a in rowtxt]
            data.append(rowd)
        count += 1
    D = np.array(data)
    print(D)
    t = (D[:,0]-D[0,0])/3600
    CH4 = D[:,1]
    delta = D[:,8]
    
    #plt.figure(0)
    #plt.plot(t,delta,'bo')
    #plt.show()
    
    print("Corrected Delta is %.3f +/- %.4f" % (average(delta),std(delta)))
#    diffstdev(CH4)
#    diffstdev(delta)
    
    A = allen(delta)
    A.calcAllen()
    print()
    print(A.T, A.S, A.white, A.drift, A.fraction)
    
    C = allen(CH4)
    C.calcAllen()
    print()
    print(C.T,C.S, C.white, C.drift, C.fraction)
    
    