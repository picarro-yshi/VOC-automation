# -*- coding: utf-8 -*-
"""
Created on Fri Feb 03 14:21:53 2017

@author: chris
"""

import numpy as np
import copy

class Trigger ():
    def __init__ (self, T, Y, N, thresh, incl_ends=False, point_delay=0):
        self.T = T
        self.Y = Y
        self.N = N
        self.thresh = thresh
        self.calcDifferences()
        self.findTransitions(self.thresh, incl_ends, point_delay)
        self.set_call_params()
        
    def calcDifferences(self):
        M = len(self.T) - self.N*2
        self.D = []
        for i in range(M):
            s1 = i
            s2 = i + self.N
            s3 = i + 2*self.N
            D2 = self.Y[s1:s2] #first block
            D1 = self.Y[s2:s3] #second block
            D2 = D2[::-1]
            P1 = [D1[k]*(k+0.5) for k in range(len(D1))]
            P2 = [D2[j]*(j+0.5) for j in range(len(D2))]
            N1 = [(k+0.5) for k in range(len(D1))]
            N2 = [(j+0.5) for j in range(len(D2))]
            #self.D[i] = abs(np.mean(D1) - np.mean(D2))
            self.D.append(abs(np.sum(P1)/np.sum(N1) - np.sum(P2)/np.sum(N2)))
        self.D = np.array(self.D)
        self.Td = self.T[self.N:-self.N]
        self.Yd = self.Y[self.N:-self.N]
        self.I = np.array([i for i in range(len(self.D))])
    
    def findTransitions(self, thresh, incl_ends, point_delay):
        if thresh != self.thresh:
            self.thresh = thresh
        self.transitions = []
        if incl_ends:
            self.transitions.append(0)
        trigger = 'armed'
        thingT = []
        thingD = []
        count = 0
        Npoints = len(self.D)
        for j, d in enumerate(self.D):
            if trigger == 'armed':
                if d >= thresh:
                    trigger = 'triggered'
                    jstart = j
            if trigger == 'triggered':
                if d >= thresh:
                    
                    thingT.append(self.Td[j])
                    thingD.append(self.D[j])
                else:
                    trigger = 'armed'
                    if len(thingT) > self.N/2:
                        count += 1
                        Tseg = thingT - thingT[0]
                        Dseg = thingD
                        a2, a1, a0 = np.polyfit(Tseg, Dseg, 2)
                        dt = (thingT[-1] - thingT[0]) / (len(thingT) - 1)
                        tmax = -a1 / 2.0 / a2 + dt*self.N + self.Td[jstart]
                        #tmax = -a1 / 2.0 / a2 + self.Td[jstart]
                        jmax = np.interp(tmax, self.Td, self.I)
                        final_j = min(Npoints-1, int(np.round(jmax))+point_delay)
                        self.transitions.append(final_j)
                    thingT, thingD = [], []
        if incl_ends:
            self.transitions.append(j)
            
    #floandantonioandalandbellaandellieandcurlosandcamofrogandmitzi!!hiphip!

    def regularize_transitions(self, tolerance = 0.15):
        Tstep = np.diff(self.transitions)
        nominal_step = np.median(Tstep)
        new_transitions = [self.transitions[0]]
        M = len(self.transitions) - 1
        cum = 0
        for m in range(M):
            step = 1
            flag = (m+cum+step) <= M
            while flag:
                s = self.transitions[m+cum]
                try:
                    e = self.transitions[m+cum+step]
                except:
                    breakpoint()
                dur = e - s
                if dur <= (1-tolerance) * nominal_step:
                    print('lower ', m, s, e, dur, step, cum)
                    step += 1
                    flag = (m+cum+step) <= M
                elif dur >= (1+tolerance) * nominal_step:
                    
                    frac = (dur % nominal_step)/nominal_step
                    if (frac < tolerance) or ((1 - frac) < tolerance):
                        print('double ', m, s, e, dur, step, cum)
                        N = int(round(dur/nominal_step))
                        for n in range(N-1):
                            new_transitions.append(s + (n+1)*int(nominal_step))
                        new_transitions.append(e)
                        cum += step - 1

                        flag = False
                    else:
                        print('bigger ', m, s, e, dur, step, cum)
                        step += 1
                        cum += 1
                        flag = (m+cum+step) <= M

                else:
                    new_transitions.append(e)
                    cum += step - 1
                    if step != 1:
                        print('nailed it ', m, s, e, dur, step, cum)
                    flag = False
        self.old_transitions = self.transitions
        self.transitions = new_transitions
    
    def set_call_params(self, startFraction=0.15, endFraction=0.1, startPad=0, endPad=0, mindur=1, maxdur=np.inf, units='count'):
        """applies the MOST restrictive of startFraction & startPad and endFraction & endPad
        mindur, maxdur, startPad, and endPad are in 'units'
           "count":sample count
           "time": units of 'self.T'  """
        self.startFraction = startFraction
        self.endFraction = endFraction
        self.startPad = startPad
        self.endPad = endPad
        self.mindur = mindur
        self.maxdur = maxdur
        self.units = units
        self.determine_segments()
    
    def determine_segments(self):
        M = len(self.transitions) - 1
        self.segments = []
        self.durations = []
        for m in range(M):
            s = self.transitions[m]
            e = self.transitions[m+1]
            if self.units == 'count':
                length = e - s
                spad = max([int(round(length*self.startFraction)), self.startPad])
                epad = max([int(round(length*self.endFraction)), self.endPad])
                s1 = s + spad
                e1 = e - epad
                thisDur = e1 - s1
                if (thisDur > self.mindur) & (thisDur < self.maxdur):
                    self.segments.append((s1, e1))
                    self.durations.append(thisDur)
            elif self.units == 'time':
                T_segment = self.T[s:e+1] * 1
                if len(T_segment) <= 1:
                    continue
                T_segment -= T_segment[0]
                duration = T_segment[-1] - T_segment[0]
                if duration - (self.startPad + self.endPad) <= 0:
                    continue
                spad = max([int(round(duration*self.startFraction)), self.startPad])
                epad = max([int(round(duration*self.endFraction)), self.endPad])
                start_i = np.argmin(abs(T_segment - spad))
                end_i = np.argmin(abs(T_segment - (duration - epad)))
                s1 = s + start_i
                e1 = s + end_i
                thisDur = e1 - s1
                if (thisDur > self.mindur) & (thisDur < self.maxdur):
                    self.segments.append((s1, e1))
                    self.durations.append(thisDur)                
        
    def pull_clean_data(self, X, one_long_array=True):
        steps = []
        for (s1,e1) in self.segments:
            steps.append(X[s1:e1+1])
            
        if one_long_array:
            clean_data = np.array([])
            for j, step in enumerate(steps):
                clean_data = np.append(clean_data, step)
        else:
            clean_data = []
            for j, step in enumerate(steps):
                clean_data.append(step)
        return clean_data

    def __call__(self, X):
        values = []
        for (s1,e1) in self.segments:
            values.append(X[s1:e1+1].mean())
        return np.array(values)
        
class SpecialTrigger(Trigger):
    def remove_bad_transitions(self, period=None, tolerance=0.06, groups = 100, fill_gaps=False):
        revised_transitions = []
        Ngroups = len(self.transitions) // groups + 1
        determine_period = period is None
        for ng in range(Ngroups):
            these_trans = self.transitions[ng*groups:(ng+1)*groups]
            times = np.array([self.T[t] for t in these_trans])

            if determine_period:
                DT = np.diff(times)
                period = np.median(DT)
                good = abs(DT - period)/period < tolerance
                period = np.mean(DT[good])

                print('Period determined to be %.6e' % period)
            C = np.cos(2*np.pi*times/period)
            S = np.sin(2*np.pi*times/period)
            phase = np.arctan2(np.median(S),np.median(C))
            time_fraction = (times - phase*period/2/np.pi)/period
            nearest = np.round(time_fraction)
            error = np.abs(time_fraction - nearest)
            phase_final = np.arctan2(np.median(S[error<=tolerance]),np.median(C[error<=tolerance]))
            good_times = np.arange(int(min(nearest)), int(max(nearest))+1)*period + phase_final/np.pi/2*period
            good_indices = np.interp(good_times, self.T, np.arange(len(self.T)))
            for tm, trn in zip(times, these_trans):
                closest = np.min(abs(good_times - tm))
                if closest <= tolerance*period:
                    if trn not in revised_transitions:
                        revised_transitions.append(trn)
        
        n_removed = len(self.transitions) - len(revised_transitions)
        if fill_gaps:
            revtimes = np.array([self.T[rt] for rt in revised_transitions])
            rev_diff = np.diff(revtimes, prepend=revtimes[0]-period)
            I = np.arange(len(rev_diff))
            extra_transitions = []
            for i in I[rev_diff > 1.5*period]:
                for j in range(int(round(rev_diff[i]/period)) - 1):
                    new_trans = np.argmin(abs(self.T - revtimes[i] + (j+1)*period))
                    extra_transitions.append(new_trans)
            revised_transitions.extend(extra_transitions)
            revised_transitions.sort()
            n_added = len(extra_transitions)
        else:
            n_added = 0
        print('removed %d and added %d transitions to %d' % (n_removed, n_added, len(self.transitions)))
        self.transitions = revised_transitions
        
if __name__ == '__main__':
    T = np.arange(0, 100, 0.1)

    Y = np.array([1 + np.random.normal(0.0, 0.1) if (np.sin(2*np.pi*t/20.0) > 0) else -1 + np.random.normal(0.0, 0.1) for t in T])
    
    N = 4
    trig = Trigger(T, Y, N)
    trig.calcDifferences()
    trig.findTransitions(0.5)
    
    print(trig.transitions)
    