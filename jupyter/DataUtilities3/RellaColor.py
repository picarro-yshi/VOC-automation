# -*- coding: utf-8 -*-
"""
Created on Wed May 03 14:30:39 2017

@author: chris
"""

import colorsys
import numpy as np
import matplotlib.pyplot as plt
import random

"""
https://computergraphics.stackexchange.com/questions/1748/function-to-convert-hsv-angle-to-ryb-angle
piecewise linear transformation
RYBstop HSVstop
60      35
122     60
165     120
218     180
275     240s
330     300
"""
def convert_to_hex(color_tuple):
    out = '#'
    for rgba in color_tuple:
        out += '%02x' % int(round((rgba*255) % 256))
    return out

class NaomiKuno(object):
    def __init__(self, brtValue=0.0):
        self.setup()
        self.count = None
        self.brtValue = brtValue
        self.createTable()
    
    def setup(self):
        self.name = 'Default'
        self.page = -1
        self.N = -1
        self.sourceColors = []
        
    def normalizeBookRGB(self, RGB):
        return tuple([x/255. for x in RGB])

    def createTable(self):
        self.colors = []
        for source in self.sourceColors:
            self.colors.append(self.adjustBrightness(self.normalizeBookRGB(source), self.brtValue))
        self.NC = len(self.colors)

    def getColor(self):
        self.count = self.count % self.NC
        return convert_to_hex(self.colors[self.count])

    def randomize(self, seed = None):
        if seed:
            random.seed(seed)
        random.shuffle(self.colors)
    
    def make_long(self, brt_list = [0, +0.35, -0.35]):
        self.colors = []
        for brt in brt_list:
            for source in self.sourceColors:
                self.colors.append(self.adjustBrightness(self.normalizeBookRGB(source), brt))
        self.NC = len(self.colors)
        
    def getNext(self):
        if self.count == None:
            self.count = 0
        else:
            self.count += 1    
        return self.getColor()
    
    def getCurrent(self):
        if self.count == None:
            self.count = 0 
        return self.getColor()

    def resetCycle(self):
        self.count = None
        
    def __getitem__ (self, i):
        return convert_to_hex(self.colors[i % self.NC])   

    def adjustBrightness(self, rgb, brt):
        """brt = +1 (goes to white) to -1 (goes to black)"""
        h, s, v = colorsys.rgb_to_hsv(*rgb)
        if brt < 0:
            v = v*(1 + brt) 
        elif brt > 0:
            spn = s + (1 - v)
            if brt*spn <= 1 - v:
                v += brt*spn
            else:                
                s -= brt*spn - (1 - v)
                v = 1.0
        return colorsys.hsv_to_rgb(h, s, v)
    
    def adjustColorTableBrightness(self, brt):
        self.brtValue = brt
        self.createTable()
        
    def demo (self):
        import seaborn as sns
        sz = 1 if len(self.colors) < 10 else 0.5
        sns.palplot([self.colors[j] for j in range(self.NC)], size=sz)

class CuteNordicKnit(NaomiKuno):
    def setup(self):
        self.name = 'CuteNordicKnit'
        self.page = 48
        self.N = 20
        
        self.sourceColors =   [(174, 218, 238),
                               (159, 157, 65), 
                               (244, 159, 58),
                               (237, 121, 139),
                               (104, 69, 99),
                               (219, 60, 53),
                               (229, 157, 161),
                               (248, 191, 136),
                               (133, 79, 63)]

class PsychedelicChakra(NaomiKuno):
    def setup(self):
        self.name = 'PsychedelicChakra'
        self.page = 72
        self.N = 31
        self.order = [0,4,1,5,2,6,3,7]
        self.sourceColors =   [(0, 163, 209),
                               (73, 108, 165), 
                               (134, 76, 148),
                               (0, 173, 174),
                               (236, 121, 33), 
                               (232, 66, 27),
                               (91, 182, 71),
                               (229, 230, 48)]
        self.sourceColors = [self.sourceColors[k] for k in self.order]

class GobelinTapestry(NaomiKuno):
    def setup(self):
        self.name = 'GobelinTapestry'
        self.page = 192
        self.N = 87
        self.order = [0,3,1,5,7,2,6,8,4]
        self.sourceColors =   [(171,106,105), 
                               (125,127,55),
                               (212,201,166),
                               (28,88,119),
                               (159,192,201),
                               (111,131,143),
                               (136, 59,61),
                               (69,71,32),
                               (210,186,123)]
        self.sourceColors = [self.sourceColors[k] for k in self.order]
        
class KawaiiPunchyCute(NaomiKuno):
    def setup(self):
        self.name = 'KawaiiPunchyCute'
        self.page = 64
        self.N = 27
        self.order = [0,4,1,5,2,6,8,7,3]
        self.sourceColors = [(222,46,139),
                             (86,93,168),
                             (238,126,124),
                             (255,255,0),
                             (0,182,221),
                             (124,189, 39),
                             (192,125,178),
                             (142,209,230),
                             (226,2,33)]
        self.sourceColors = [self.sourceColors[k] for k in self.order]

class SeventiesFunk(NaomiKuno):
    def setup(self):
        self.name = 'SeventiesFunk'
        self.page = 64
        self.N = 27
        self.order = [0,4,1,5,2,6,7,3]
        self.sourceColors = [(205,17,50),
                             (112,55,126),
                             (214,113,47),
                             (231,185,32),
                             (24,88,139),
                             (117,79,58),
                             (144,185,33),
                             (0,121,117)]
        self.sourceColors = [self.sourceColors[k] for k in self.order]

class ColorScale():
    def __init__ (self, mappy='brg', N=16):
        self.cz = plt.get_cmap(mappy)
        self.N = N
        self.makeColorArray()
        self.count = None
    
    def makeColorArray(self):
        Z = [float(i)/(self.N-1) for i in range(self.N)]
        self.kolors = [self.cz(z) for z in Z]
    
    def getKolor(self):
        self.count = self.count % self.N
        return convert_to_hex(self.kolors[self.count])
        
    def getNext(self):
        if self.count == None:
            self.count = 0
        else:
            self.count += 1    
        return self.getKolor()
    
    def getCurrent(self):
        if self.count == None:
            self.count = 0 
        return self.getKolor()

    def resetCycle(self):
        self.count = None
        
    def __getitem__ (self, x):
        return self.kolors[x]


def ColorScheme(scheme='classic'):
    """classic: first tetrad
     lotsa: 6 color Ntrad (default)s"""
    if scheme == 'classic':
        return Tetrad(primary = 1, useRGY=True)
    elif scheme == 'lotsa':
        return NTrad(3, primary=4,angle=30,useRGY=True)
    else:
        return NTrad(3, primary=4,angle=30,useRGY=True)
        
        
class Tetrad():
    HSV_rgb_to_rgy_deg = list(zip(*[(0,0), (35, 60), (60, 122), (120, 165), (180, 218), (240, 275), 
                      (300, 330), (360, 360)]))
    palettes = [((0.02, 0.66,0.75),40), #red green blue orange/brown less saturated
                ((0.02, 1.0 ,0.75),40), #red green blue orange/brown more saturated
                ((0.48, 0.87,0.85),50), #teal/orange/redbrown/blue
                ((0.55, 0.66,0.75),30),] # blue/orange 
    symbolCycle = ['o', 's', '^', 'v', '>', '<', '8', 'h', '*']
    
    def __init__ (self, primary = 0, angle = 30.0, useRGY = False):
        """Takes an RGB primary value and creates a palette of four RGB colors related as a tetrad
           angle is in degrees; internal angle is """
        self.hue_shift = angle/360.0
        
        if type(primary) is int:
            temp = self.palettes[primary][0]
            self.hue_shift = self.palettes[primary][1]/360.0
            primary = colorsys.hsv_to_rgb(*temp)
        self.primary_rgb = primary
        self.useRGY = useRGY
        
        self.rescaleInterpolant()
        
        self.prim = colorsys.rgb_to_hsv(*primary)

        self.createTetrad()
        self.buildArray()
        self.count = -1
    
    def rescaleInterpolant(self):
        X, Y = self.HSV_rgb_to_rgy_deg
        newX = [x/360.0 for x in X]
        newY = [y/360.0 for y in Y]
        self.HSV_rgb_to_rgy = [newX, newY]
    
    def RGBtoRGY (self, hsv_rgb):
        return np.interp(hsv_rgb, self.HSV_rgb_to_rgy[0], self.HSV_rgb_to_rgy[1])
        
    def RGYtoRGB (self, hsv_rgy):
        return np.interp(hsv_rgy, self.HSV_rgb_to_rgy[1], self.HSV_rgb_to_rgy[0])
        
    def kickHue(self, hsv, angle):
        """angle from 0-1"""
        return (hsv[0] + angle) % 1, hsv[1], hsv[2]
        
    def createTetrad(self):
        """hue is a number from 0.0 to 1.0 that covers 360 degrees of the color wheel
           R = 0, G = 1/3, B = 2/3
           R = 0 deg, G = 120 deg, B = 240 deg"""
        if self.useRGY:
            self.prim = self.RGBtoRGY(self.prim)
        self.sec1 = self.kickHue(self.prim, self.hue_shift)
        self.sec2 = self.kickHue(self.prim, -0.5)
        self.tert = self.kickHue(self.sec1, 0.5)
        #print self.__str__()
        if self.useRGY:
            self.prim = self.RGYtoRGB(self.prim)
            self.sec1 = self.RGYtoRGB(self.sec1)
            self.sec2 = self.RGYtoRGB(self.sec2)
            self.tert = self.RGYtoRGB(self.tert)
    
    
    def __str__(self):
        t = lambda n, x: '%s = ' % (n) + '(%.3f, %.3f, %.3f)\n' % (colorsys.hsv_to_rgb(*x))
        txt = ''
        txt += t('primary', self.prim)
        txt += t('secondary #1', self.sec1)
        txt += t('secondary #2', self.sec2)
        txt += t('tertiary', self.tert)
        
        print(self.prim[0], self.sec1[0], self.sec2[0], self.tert[0])
        return txt
    
    def listTetrad(self):
        k = lambda x: colorsys.hsv_to_rgb(*x)
        return [k(self.prim), k(self.tert), k(self.sec2), k(self.sec1)]
    
    def adjBrightness(self, C, x):
        """C in hsv format; x = +1 (goes to white) to -1 (goes to black)"""
        h, s, v = C
        if x < 0:
            v = v*(1 + x)
        elif x > 0:
            spn = s + (1 - v)
            if x*spn <= 1 - v:
                v += x*spn
            else:                
                s -= x*spn - (1 - v)
                v = 1.0
        return h, s, v
        
    def buildArray (self, brightness_adjust = [0, -0.55, 0.55, -0.3, 0.3]):
        self.C = []
        X = brightness_adjust
        F = self.prim, self.tert, self.sec2, self.sec1
        k = lambda x: colorsys.hsv_to_rgb(*x)
        t = lambda n, x: '%s = ' % (n) + '(%.3f, %.3f, %.3f)\n' % (colorsys.hsv_to_rgb(*x))
        for f in F:
            row = []
            for x in X:
                aC = self.adjBrightness(f, x)
                row.append(k(aC))
            self.C.append(row)
        return self.C
    
    def __getitem__ (self, x):
        if type(x) is int or type(x) is np.int64:
            xx = x % 20
            col = int(xx/4)
            row = xx % 4
            return self.C[row][col]
        elif len(x) == 2:
            return self.C[x[0]][x[1]]
        else:
            return None

    def getMarker(self):
        return self.symbolCycle[int(self.count/4) % len(self.symbolCycle)]            
    
    def getNext(self):
        self.count += 1
        return self.countToColor()
    
    def countToColor(self):
        y = self.count % 20
        col = int(y/4)
        row = y % 4        
        return self.C[row][col]
    
    def getCurrent(self):
        if self.count == -1:
            self.count == 0
        return self.countToColor()
    
    def resetCycle(self, n = -1):
        self.count = n
    
    def plotFullArray (self):
        import seaborn as sns
        for family in self.C:
            sns.palplot([family[j] for j in [1,3,0,4,2]])
    
    def plotFamily (self):
        import seaborn as sns
        sns.palplot([self.C[j][0] for j in range(4)])

class NTrad():
    HSV_rgb_to_rgy_deg = list(zip(*[(0,0), (35, 60), (60, 122), (120, 165), (180, 218), (240, 275), 
                      (300, 330), (360, 360)]))
    palettes = [((0.02, 0.66,0.75),40), #red green blue orange/brown less saturated
                ((0.02, 1.0 ,0.75),40), #red green blue orange/brown more saturated
                ((0.48, 0.87,0.85),50), #teal/orange/redbrown/blue
                ((0.55, 0.66,0.75),30), # blue/orange 
                ((0.388, 1.0, 0.8),40)] #okay 6Trad
    symbolCycle = ['o', 's', '^', 'v', '>', '<', '8', 'h', '*']
    
    def __init__ (self, N, primary = 0, angle = 30.0, useRGY = False):
        """N = 2 for Tetrad
           Takes an RGB primary value and creates a palette of four RGB colors related as a tetrad
           angle is in degrees; internal angle is """
        self.N = N
        self.hue_shift = angle/360.0
        
        if type(primary) is int:
            temp = self.palettes[primary][0]
            self.hue_shift = self.palettes[primary][1]/360.0
            primary = colorsys.hsv_to_rgb(*temp)
        self.primary_rgb = primary
        self.useRGY = useRGY
        
        self.rescaleInterpolant()
        
        self.prim = colorsys.rgb_to_hsv(*primary)

        self.createColors()
        self.buildArray()
        self.count = -1
    
    def rescaleInterpolant(self):
        X, Y = self.HSV_rgb_to_rgy_deg
        newX = [x/360.0 for x in X]
        newY = [y/360.0 for y in Y]
        self.HSV_rgb_to_rgy = [newX, newY]
    
    def RGBtoRGY (self, hsv_rgb):
        return np.interp(hsv_rgb, self.HSV_rgb_to_rgy[0], self.HSV_rgb_to_rgy[1])
        
    def RGYtoRGB (self, hsv_rgy):
        return np.interp(hsv_rgy, self.HSV_rgb_to_rgy[1], self.HSV_rgb_to_rgy[0])
        
    def kickHue(self, hsv, angle):
        """angle from 0-1"""
        return (hsv[0] + angle) % 1, hsv[1], hsv[2]
        
    def createColors(self):
        """hue is a number from 0.0 to 1.0 that covers 360 degrees of the color wheel
           R = 0, G = 1/3, B = 2/3
           R = 0 deg, G = 120 deg, B = 240 deg"""
        if self.useRGY:
            temp_prim = self.RGBtoRGY(self.prim)
        else:
            temp_prim = self.prim
        self.Colors = []
        for i in range(self.N):
            z = self.kickHue(temp_prim, self.hue_shift*i)
            self.Colors.append(z)
            z = self.kickHue(temp_prim, self.hue_shift*i - 0.5)
            self.Colors.append(z)
        
        if self.useRGY:
            self.Colors = [self.RGYtoRGB(c) for c in self.Colors]
        
    def adjBrightness(self, C, x):
        """C in hsv format; x = +1 (goes to white) to -1 (goes to black)"""
        h, s, v = C
        if x < 0:
            v = v*(1 + x)
        elif x > 0:
            spn = s + (1 - v)
            if x*spn <= 1 - v:
                v += x*spn
            else:                
                s -= x*spn - (1 - v)
                v = 1.0
        return h, s, v
        
    def buildArray (self, brightness_adjust = [0, -0.55, 0.55, -0.3, 0.3]):
        self.C = []
        X = brightness_adjust
        F = self.Colors
        k = lambda x: colorsys.hsv_to_rgb(*x)
        t = lambda n, x: '%s = ' % (n) + '(%.3f, %.3f, %.3f)\n' % (colorsys.hsv_to_rgb(*x))
        for f in F:
            row = []
            for x in X:
                aC = self.adjBrightness(f, x)
                row.append(k(aC))
            self.C.append(row)
        return self.C
    
    def __getitem__ (self, x):
        if type(x) is int or type(x) is np.int64:
            xx = x % (5*self.N*2)
            col = int(xx/(self.N*2))
            row = xx % (self.N*2)  
            return self.C[row][col]
        elif len(x) == 2:
            return self.C[x[0]][x[1]]
        else:
            return None

    def getMarker(self):
        return self.symbolCycle[int(self.count/(self.N*2)) % len(self.symbolCycle)]            
    
    def getNext(self):
        self.count += 1
        return self.countToColor()
    
    def countToColor(self):
        y = self.count % (5*self.N*2)
        col = int(y/(self.N*2))
        row = y % (self.N*2)
        return self.C[row][col]
    
    def getCurrent(self):
        if self.count == -1:
            self.count == 0
        return self.countToColor()
    
    def resetCycle(self, n = -1):
        self.count = n
    
    def plotFullArray (self):
        import seaborn as sns
        for family in self.C:
            sns.palplot([family[j] for j in [1,3,0,4,2]])
    
    def plotFamily (self):
        import seaborn as sns
        sns.palplot([self.C[j][0] for j in range(self.N*2)])


def adjustRGBBrightness(rgb, x):
    """rgb is 3 element tuple; x = +1 (goes to white) to -1 (goes to black)"""
    print(rgb, x)
    hsv = colorsys.rgb_to_hsv(*rgb)
    newhsv = adjBrightness(hsv, x)
    return colorsys.hsv_to_rgb(*newhsv)

def adjBrightness(C, x):
    """C in hsv format; x = +1 (goes to white) to -1 (goes to black)"""
    h, s, v = C
    if x < 0:
        v = v*(1 + x)
    elif x > 0:
        spn = s + (1 - v)
        if x*spn <= 1 - v:
            v += x*spn
        else:                
            s -= x*spn - (1 - v)
            v = 1.0
    return h, s, v

if __name__ == '__main__':
    Test = CuteNordicKnit()
    print(Test.colors)
    
        



    
        