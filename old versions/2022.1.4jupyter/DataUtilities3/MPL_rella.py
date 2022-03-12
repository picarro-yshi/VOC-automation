
import string
import matplotlib.pyplot as plt
from matplotlib.path import Path
import matplotlib.patches as patches
import matplotlib as mpl
import numpy as np
import time
import sys
import matplotlib.gridspec as gridspec
import os
try:
    import imageio
except ImportError:
    print('imageio module unavailable - unable to create animated gifs')
import datetime

def thisDate(epochTimeIn, fmt='%Y%m%d'):
    return time.strftime(fmt, time.localtime(epochTimeIn))

def thisDateTime(epochTimeIn, fmt='%Y%m%d_%H%M'):
    return time.strftime(fmt, time.localtime(epochTimeIn))

def thisDateTimeSec(epochTimeIn, fmt='%Y%m%d_%H%M%S'):
    return time.strftime(fmt, time.localtime(epochTimeIn))

def thisDateTimeSecMsec(epochTimeIn, fmt='%Y%m%d_%H%M%S'): 
    return time.strftime(fmt, time.localtime(epochTimeIn))+ ('%.3f' % (epochTimeIn % 1))[1:]

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

RM = r'$\mathrm{%s}$'
MATH =  r'${%s}$'
PERMIL = r'$\hspace{0.2}[$'+u'$\u2030$'+'$]$'
PERMIL_nobrack = u'$\hspace{0.2}$'+u'$\u2030$'
CH4 = (RM % r'CH_4') + r' [ppm]'
CH4noppm = RM % r'CH_4'
GAUSS = r'$e^{-t^{2}\hspace{-0.3}/\sigma^{2}}$'
EXP = r'$e^{-t/\tau}$'
invCH4 = (RM % r'CH_4^{-1}') + '  ' + (RM % r'[ppm^{-1}]')
d13CH4 = '$\delta\mathrm{{}^{13}\hspace{0.2}\!CH_4}$'
d13CH4permil = d13CH4 + '' + PERMIL
C2H6 = (RM % r'C_2H_6') + r' [ppm]'
C2toC1 = RM % r'C_2 / C_1 ratio'
H2O = (RM % r'H_2O ')
H2Opct = (RM % r'H_2O') + '%'
CO2 = (RM % r'CO_2 ')
N2O = (RM % r'N_2O ')
C2H6noppm = RM % r'C_2H_6'
sigdel = r"$\sigma_{%s}$" % d13CH4.replace('$','') + PERMIL
sigma = r"$\sigma$"
delta = r'$\delta$'
DELTA = r'$\Delta$'
C12H4 = (RM % r'^{12}\hspace{0.2}\!CH_4')
C13H4 = (RM % r'^{13}\hspace{0.2}\!CH_4') 
#     plume scanner paper
windpower = (RM % r'\frac{u}{u_0} = (\frac{z}{z_0})^{K}')
zrat = (RM % r'{z}/{z_0}')
urat = (RM % r'{u}/{u_0}')
emisrat = (RM % r'E_{meas}/E_{act}')
emisratln = (RM % r'ln(E_{meas}/E_{act})')
emisln = (RM % r'ln(E_{meas} [kg/hr])')
rtop = (RM % r'r_{top}')
plume_width = 'plume width ' + (RM % '\sigma') + ' [m]'
pw_mod = 'model plume width ' + (RM % '\sigma') + ' [m]'
pw_meas = 'meas. plume width ' + (RM % '\sigma') + ' [m]'

emisratmod = (RM % r'E_{integral}/E_{total}')
q0 = RM % r'q_0'
q0unit = RM % r'q_0 \/\/[kg / hr \/m^{-1}\/ s^{-1/2}]'

Q0 = RM % r'Q_0'
Q0unit = RM % r'Q_0 \/\/[kg / hr]'
emistrap = RM % r'E_{TRAP} \/ \/[kg / hr]'
emisGF = RM % r'E_{GF} \/ \/[kg / hr]'

conclog = RM % r'log_{10}[CH_4]'
thetavect = RM % r'(\theta_{pump}, \theta_{surface})'
thetaperp = RM % r'(\theta_{pump}, -\theta_{surface})'

wavenumbers = r'frequency ' + MATH % r'[cm^{-1}]'


FS1 = (6.5,4)
FS2 = (6,5)
FS3 = (5,5)
FS4 = (7.5,2.5)
FS5 = (6,3)
FS6 = (12,5)
FS7 = (2,3)
FS8 = (10,5)
FS9 = (8,4)
FS10 = (9,9)
FS11 = (7,7)
FS12 = (4,4)
FS13 = (7,12)
FS14 = (3,0.5)
FS15 = (1,0.25)
FS16 = (12,4)
FS17 = (3,9)
FS18 = (14,9)
FS19 = (12, 8.07)

blue = '#0000ff'
dkblue = '#000088'
cyan = '#00ffff'
green = '#00ff00'
dkgreen = '#03A609'
ltgreen = '#ACEBA9'
purp1 = '#cf2dc4'
purp2 = '#E300D0'
dkpurp = '#7C0091'
grpurp = '#995A94'
teal = '#2DBCCF'
flesh = '#FADCB9'
brown1 = '#D6CC9F'
gray1 = '#888888'
dkgray = '#444444'
ltgray = '#cccccc'
red = '#ff0000'
ltred = '#FCC0C0'
dkred = '#880000'
yellow = '#FFFF00'
magenta = '#FF00FF'
ltcyan = '#7AFDFF'
dkorange = '#F0A400'
orange = '#FFAE00'
black = '#000000'
white = '#ffffff'
dkbrown = '#996633'
picarro_green = '#6EB43F'
picarro_gray = '#404040'
picarro_blue = '#23408F'
picarro_red = '#941215'
picarro_orange = '#F58220'

ColorList1 = [blue, red, dkgreen, black, purp1, orange, dkbrown, cyan, green, gray1, yellow, ltred]

tetrade_1 = ['#4188BA','#B041BA', '#4BBA41','#BA7341']
tetrade_2 = ['#0000C4', '#C40062', '#C4C400', '#00C462']

triad_1 = ['#347FF7', '#F7347F', '#7FF734']

six = ['#000000','#0000ff','#ff0000','#03A609','#7C0091','#FFAE00']

def polything (coeffs, xsim):
    ysim = np.polyval(coeffs, xsim)
    ylst = [RM % ('[%.5e]x^%d' % (c,len(coeffs) - i - 1)) for i, c in enumerate(coeffs)]
    ytxt = ' + '.join(ylst)
    return ysim, ytxt

def addPolyPlots(axis, X, Y, polylist=[1], colorlist = [red, green, blue]):
    if len(X) < max(polylist): #not enough points for the fit
        return axis
    xsim = np.linspace(min(X), max(X), 100)
    for j, pol in enumerate(polylist):
        a = np.polyfit(X,Y,pol)
        ysim, ytxt = polything(a, xsim)
        axis.plot(xsim, ysim, c=colorlist[j], label=ytxt)
    return axis

def getTightRange(X, lowpadX = 0.05, highpadX = 0.05):
    """get limits with fractional padding"""
    span = max(X) - min(X)
    return [min(X) - lowpadX*span, max(X) + highpadX*span]

def addRectToPlot (A, x0, x1, y0, y1, c, ec='none', alpha=1.0, lw = 1.0):

    verts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
    path = Path(verts, codes)
    patch = patches.PathPatch(path, facecolor = c, edgecolor = ec, alpha = alpha)
    A.add_patch(patch)
    return A

def lowLeft(A):
    A.xaxis.set_label_position('bottom')
    A.xaxis.tick_bottom()
    A.xaxis.set_ticks_position('both')
    A.yaxis.set_label_position('left')
    A.yaxis.tick_left()
    A.yaxis.set_ticks_position('both')
    
def lowRight(A):
    A.xaxis.set_label_position('bottom')
    A.xaxis.tick_bottom()
    A.xaxis.set_ticks_position('both')
    A.yaxis.set_label_position('right')
    A.yaxis.tick_right()
    A.yaxis.set_ticks_position('both')

def upLeft(A):
    A.xaxis.set_label_position('top')
    A.xaxis.tick_top()
    A.xaxis.set_ticks_position('both')
    A.yaxis.set_label_position('left')
    A.yaxis.tick_left()
    A.yaxis.set_ticks_position('both')

def upRight(A):
    A.xaxis.set_label_position('top')
    A.xaxis.tick_top()
    A.xaxis.set_ticks_position('both')
    A.yaxis.set_label_position('right')
    A.yaxis.tick_right()
    A.yaxis.set_ticks_position('both')

def ColorList(j):
    n = len(ColorList1)
    return ColorList1[j % n]
    
#colormap
def cmap(mappy = 'brg'):
    return plt.get_cmap(mappy)

def GridOn(A, c = '#bbbbbb', lw = 0.25, linestyle='solid'):
    A.grid(which = 'both', color=c, alpha=0.5, linestyle=linestyle, linewidth=lw)

def LogLog(A):
    A.set_xscale('log')
    A.set_yscale('log')
    GridOn(A)

def setLabels(A, xlabel='', ylabel='', title='', fontsize=14):
    if xlabel != '':
        A.set_xlabel(xlabel, fontsize=fontsize)
    if ylabel != '':
        A.set_ylabel(ylabel, fontsize=fontsize)
    if title != '':
        A.set_title(title, fontsize=int(fontsize*1.25))

def colorLegend(legend, c):
    return legend.get_frame().set_facecolor(c)

def StandardAllanVariance(axis, Y, T, c=blue, s=70,linec = red, label='', taulabel=None, alpha=1.0):

    if Y is not None:
        Tsim = np.arange(min(T), max(T), min(T))
        axis.scatter(T, Y, c=c, edgecolor='none', s=s, zorder=10,label=label, alpha=alpha)
        if not taulabel:
            taulabel = f'[{Y[0]*np.sqrt(T[0]):.2e}] ' + RM % 't^{-0.5}'
        axis.plot(Tsim, Y[0]/np.sqrt(Tsim/T[0]), c = linec, lw = 2, label = taulabel, alpha=alpha)
    axis.set_yscale('log')
    axis.set_xscale('log')
    axis.grid(b=True, which='minor',c='0.96',lw=0.5)
    return axis
    
def StandardHist(axis, data, binny, c = blue, ec='none', label = '', alpha = 1.0, zorder = 0, density=False, **kwargs):
    a, b, patches = axis.hist(data, bins = binny, color = c, label = label, alpha = alpha, zorder = zorder, density=density, **kwargs)
    for p in patches:
        p.set_edgecolor(ec)
    return axis

def StandardErrorbar(axis, X, Y, Yerr, c = blue, ec = blue, s = 70, Xerr = [], zorder=0, lw = 0.5, capwidth = 0.5, capsize = 3, label = '', alpha = 1.0):
    axis.scatter(X, Y, edgecolor = ec, c = c, s = s, zorder=zorder, label = label, alpha=alpha)
    if len(Xerr) == 0:
        plots, caps, bars = axis.errorbar(X, Y, yerr = Yerr, fmt = 'none', ecolor = ec, zorder=zorder, elinewidth = lw, capsize = capsize, alpha=alpha)
    else:
        plots, caps, bars = axis.errorbar(X, Y, xerr = Xerr, yerr = Yerr, fmt = 'none', ecolor = ec, zorder=zorder, elinewidth = lw, capsize=capsize, alpha=alpha)
    for cap in caps:
        cap.set_color(ec)
        cap.set_markeredgewidth(capwidth)

def StandardTimeAndAllanPlot(A, T, Y, color=blue, label='', N_ave=1, averaging_multiplier=1):
    try:
        import DataUtilities3.allan_stddev_rella as astd
    except ImportError:
        print('Allan Standard Deviation code unavailable')
        return
    A[0].plot(WA(T,N_ave), WA(Y, N_ave), c=color, label = label)
    A[0].legend(loc='best')
    noise = astd.Allan(Y, T=T*averaging_multiplier)
    StandardAllanVariance(A[1], noise.S, noise.T, c=color)
    A[1].set_ylim([min(noise.S)*0.5, max(noise.S)*2.0])
    return A
        
def polar(X,Y):
    nX, nY = [], []
    for i in range(len(X)):
        if Y[i] < 0.0:
            nX.append(X[i]+np.pi)
            nY.append(-Y[i])
        else:
            nX.append(X[i])
            nY.append(Y[i])
    return np.array(nX), np.array(nY)

def Maker(size = FS1, grid = (1,1), proj = 'rectilinear', sharex=False):
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
                if sharex and ((x>0) or (y>0)):
                    A.append(plt.subplot(gs[x,y], projection = proj[n], sharex=A[0]))
                else:
                    A.append(plt.subplot(gs[x,y], projection = proj[n]))
                n += 1
    return A, FIG

def MakerGridSpec(size=FS1, grid=(1,1), proj='rectilinear', sharex=False, **gskwargs):
    """makes a standard figure using gridspec; returns gridspec
    returns A, FIG, gs tuple
    Valid values for projection are: [aitoff, hammer, lambert, mollweide, polar, rectilinear]
    left, right,top, bottom, wspace, hspace"""
    FIG = plt.figure(figsize=size)
    N = grid[0]*grid[1]
    gs = gridspec.GridSpec(grid[0], grid[1], **gskwargs)
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
                if sharex and ((x>0) or (y>0)):
                    A.append(plt.subplot(gs[x,y], projection = proj[n], sharex=A[0]))
                else:
                    A.append(plt.subplot(gs[x,y], projection = proj[n]))
                n += 1
    return A, FIG, gs

def PrivateMaker(Nrows=1,Ncols=3,size = (9,9)):
    """makes a plot with Nrows rows and Ncols cols, where the Ncol-1 cols are grouped into one plot"""
    FIG = plt.figure(figsize=size)
    gs = gridspec.GridSpec(Nrows, Ncols)
    A = []
    for i in range(Nrows):
        A.append(plt.subplot(gs[i,0:Ncols-1]))
        A.append(plt.subplot(gs[i,-1]))
        
    for i in range(Nrows):
        if i != Nrows - 1:
            A[2*i].set_xticklabels([])
            A[2*i+1].set_xticklabels([])
        lowRight(A[2*i+1])
    return A, FIG

def MakerCal(size = (6,8), N = 3):
    """makes a standard linearity + residuals plot
    the top plot is square
    the bottom plot is narrower vertically"""
    FIG = plt.figure(figsize = size)
    gs = gridspec.GridSpec(N,1)
    A = []
    A.append(plt.subplot(gs[0:N-1,0]))
    A.append(plt.subplot(gs[-1,0]))
    return A, FIG
    
def MakerSideBySide(size = (8,5), N = 2):
    """makes a standard linearity + residuals plot
    the left plot is square
    the right plot is narrower vertically"""
    FIG = plt.figure(figsize = size)
    gs = gridspec.GridSpec(1,N)
    A = []
    A.append(plt.subplot(gs[0,0:N-1]))
    A.append(plt.subplot(gs[0,-1]))
    return A, FIG

def MakerCalSharedX(size = (6,8), N = 3):
    """makes a standard linearity + residuals plot
    the top plot is square
    the bottom plot is narrower vertically"""
    FIG = plt.figure(figsize = size)
    gs = gridspec.GridSpec(N,1)
    A = []
    ax1 = plt.subplot(gs[0:N-1,0])
    ax2 = plt.subplot(gs[-1,0], sharex=ax1)
    A.append(ax1)
    A.append(ax2)
    return A, FIG
    
def MakerSideBySideSharedY(size = (8,5), N = 2):
    """makes a standard linearity + residuals plot
    the left plot is square
    the right plot is narrower vertically"""
    FIG = plt.figure(figsize = size)
    gs = gridspec.GridSpec(1,N)
    A = []
    ax1 = plt.subplot(gs[0,0:N-1])
    ax2 = plt.subplot(gs[0,-1], sharey=ax1)
    A.append(ax1)
    A.append(ax2)
    return A, FIG

def MakerArbGrid(size=(6,6), grid=(1,1), panels = [[(0,1), (0,1)]], **gskwargs):
    FIG = plt.figure(figsize=size)
    gs = gridspec.GridSpec(grid[0], grid[1], **gskwargs)
    A = []
    for x in panels:
        a = x[0]
        b = x[1]
        A.append(plt.subplot(gs[a[0]:a[1], b[0]:b[1]]))
    return A, FIG

def MakeFileName(name,dirname,prefix = "", fext = '.csv', TIMEY = False):
    if TIMEY:
        t = "%d" % time.time()
    else:
        t = ''
    fname = os.path.join(dirname, prefix + name + t + fext)
    return fname

def breakPlot(A, X, Y, dxmax, newdxmax=-1, label='', **kwargs):
    bigX, bigY, bigkick = [], [], []
    xstart = 0
    for j in range(len(X)-1):
        if X[j+1] - X[j] > dxmax:
            bigX.append(X[xstart:j+1])
            bigY.append(Y[xstart:j+1])
            if newdxmax >=0:
                kicker = X[j+1] - X[j] - newdxmax
            else:
                kicker = 0.0
            bigkick.append(kicker)
            xstart = j+1
    bigX.append(X[xstart:])
    bigY.append(Y[xstart:])
    if len(bigkick) > 0:
        finalkick = [sum(bigkick[:i]) for i in range(len(bigkick))]
        finalkick.append(finalkick[-1]+bigkick[-1])
        
        count = 0
        for bx, by, thiskick in zip(bigX, bigY, finalkick):
            if count == 0:
                labby = label
            else:
                labby = ''
            A.plot(bx - thiskick, by, label=labby, **kwargs)
            count += 1
    else:
        A.plot(X,Y,label=label, **kwargs)
    return A

def xmap ( x):
    return 1.0e7 / x
    
def xunmap (z):
    return 1.0e7 / z

def updateSpectralPlot (A,B):
    res = 8
    xl, xr = A.get_xlim()
    zl, zr = xmap(xl), xmap(xr)
    zx, zm = max((zl, zr)), min((zl, zr))
    zp = zx - zm #span
    dz = zp / res #approximate z step

    order = np.log10(dz)
    rm = order % 1.0
    k = np.floor(order)
    if rm < 0.175:
        step = 10.0**k
    elif 0.175 <= rm < 0.5:
        step = 2.0 * 10.0**k
    elif 0.5 <= rm < 0.85:
        step = 5.0 * 10.0**k
    else:
        step = 10.0 * 10.0**k
    zmstart = np.ceil(zm/step)*step
    zvals = []
    nextGuy = zmstart
    while True:
        zvals.append(nextGuy)
        nextGuy += step
        if nextGuy > zx:
            break
    fmval = int(np.round(np.max([-k,0])))
    if fmval == 0:
        fmtstr = '%d'
    else:
        fmtstr = '%%.%df' % fmval

    zlabels = [fmtstr % z for z in zvals]
    xvals = [xunmap(z) for z in zvals]

    B.set_xlim([xl, xr])
    B.set_xticks(xvals)
    B.set_xticklabels(zlabels, color = RMPL.dkgreen)

def MakerSpectrumWithWavelength(**kwargs):
    """use updateSpectalPlot once xlim are set"""
    A, F = Maker(**kwargs)
    B = A.twiny()
    B.grid(which = 'both', axis='x', color=kwargs.get('c', '#88ff00'), alpha=kwargs.get('alpha', 0.9),
            linestyle=kwargs.get('linestyle', ':'), linewidth=kwargs.get('lw', 0.45))
    B.set_xlabel('wavelength [nm]', fontsize=12, color=RMPL.dkgreen)
    return (A,B), F

def SetTheme(theme = "ONE", fontsize = None):

    if theme == "ONE":
        mpl.rcParams["figure.figsize"]=(6,6)
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = "Verdana"
        if fontsize == None:
            mpl.rcParams["font.size"] = 11
        else:
            mpl.rcParams["font.size"] = fontsize
        mpl.rcParams["axes.linewidth"] = 2
        mpl.rcParams["xtick.major.width"] = 1.5
        mpl.rcParams["ytick.major.width"] = 1.5
        mpl.rcParams["xtick.major.size"] = 6
        mpl.rcParams["xtick.major.pad"] = 6
        mpl.rcParams["ytick.major.size"] = 6
        mpl.rcParams["ytick.major.pad"] = 6
        mpl.rcParams["figure.subplot.bottom"] = 0.2
        mpl.rcParams["figure.subplot.left"] = 0.2
        mpl.rcParams["xtick.minor.size"] = 4
        mpl.rcParams["xtick.minor.width"] = 1
        mpl.rcParams["ytick.minor.size"] = 4
        mpl.rcParams["ytick.minor.width"] = 1
        txt = 'theme set: Rella20140701'
    elif theme == "TWO":
        mpl.rcParams["figure.figsize"]=(6,6)
        mpl.rcParams["font.family"] = "serif"
        mpl.rcParams["font.serif"] = 'Times New Roman'
        if fontsize == None:
            mpl.rcParams["font.size"] = 14
        else:
            mpl.rcParams["font.size"] = fontsize
        mpl.rcParams["axes.linewidth"] = 2
        mpl.rcParams["xtick.major.width"] = 1.5
        mpl.rcParams["ytick.major.width"] = 1.5
        mpl.rcParams["xtick.major.size"] = 6
        mpl.rcParams["xtick.major.pad"] = 6
        mpl.rcParams["ytick.major.size"] = 6
        mpl.rcParams["ytick.major.pad"] = 6
        mpl.rcParams["figure.subplot.bottom"] = 0.2
        mpl.rcParams["figure.subplot.left"] = 0.2
        mpl.rcParams["xtick.minor.size"] = 4
        mpl.rcParams["xtick.minor.width"] = 1
        mpl.rcParams["ytick.minor.size"] = 4
        mpl.rcParams["ytick.minor.width"] = 1
        txt = 'theme set: Rella20140729'
    elif theme == "THREE":
        mpl.rcParams["figure.figsize"]=(6,6)
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = "Verdana"
        if fontsize == None:
            mpl.rcParams["font.size"] = 9
        else:
            mpl.rcParams["font.size"] = fontsize
        mpl.rcParams["axes.linewidth"] = 1.5
        mpl.rcParams["xtick.major.width"] = 1
        mpl.rcParams["ytick.major.width"] = 1
        mpl.rcParams["xtick.major.size"] = 4
        mpl.rcParams["xtick.major.pad"] = 4
        mpl.rcParams["ytick.major.size"] = 4
        mpl.rcParams["ytick.major.pad"] = 4
        mpl.rcParams["figure.subplot.bottom"] = 0.2
        mpl.rcParams["figure.subplot.left"] = 0.2
        mpl.rcParams["xtick.minor.size"] = 3
        mpl.rcParams["xtick.minor.width"] = 1
        mpl.rcParams["ytick.minor.size"] = 3
        mpl.rcParams["ytick.minor.width"] = 1
        txt = 'theme set: Rella20140701'
    elif theme == "FOUR":
        mpl.rcParams["figure.figsize"]=(6,6)
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = "Verdana"
        if fontsize == None:
            mpl.rcParams["font.size"] = 20
        else:
            mpl.rcParams["font.size"] = fontsize
        mpl.rcParams["axes.linewidth"] = 2.0
        mpl.rcParams["xtick.major.width"] = 1
        mpl.rcParams["ytick.major.width"] = 1
        mpl.rcParams["xtick.major.size"] = 4
        mpl.rcParams["xtick.major.pad"] = 4
        mpl.rcParams["ytick.major.size"] = 4
        mpl.rcParams["ytick.major.pad"] = 4
        mpl.rcParams["figure.subplot.bottom"] = 0.2
        mpl.rcParams["figure.subplot.left"] = 0.2
        mpl.rcParams["xtick.minor.size"] = 3
        mpl.rcParams["xtick.minor.width"] = 1
        mpl.rcParams["ytick.minor.size"] = 3
        mpl.rcParams["ytick.minor.width"] = 1
        txt = 'theme set: Rella20140701'
    elif theme == 'FIVE':
        mpl.rcParams['axes.axisbelow'] = True
        mpl.rcParams['axes.edgecolor'] = '.25'
        mpl.rcParams['axes.facecolor'] = '0.92'
        
        mpl.rcParams['axes.labelcolor'] = '0.15'
        mpl.rcParams['axes.linewidth'] = 1.5
        mpl.rcParams['figure.facecolor'] = 'white'
        mpl.rcParams['font.family'] = ['sans-serif']
        mpl.rcParams['font.sans-serif'] = ['Arial', 'Liberation Sans', 
                                         'Bitstream Vera Sans', 'sans-serif']
        mpl.rcParams['grid.color'] = '0.98'
        mpl.rcParams['grid.linestyle'] = '-'
        mpl.rcParams['grid.linewidth'] = 1.0
        mpl.rcParams['axes.grid'] = True
        mpl.rcParams['image.cmap'] = 'Greys'
        mpl.rcParams['legend.frameon'] = True
        mpl.rcParams['legend.numpoints'] = 1
        mpl.rcParams['legend.scatterpoints'] = 3
        mpl.rcParams['lines.solid_capstyle'] = 'round'
        mpl.rcParams['legend.facecolor'] = 'white'
        mpl.rcParams['legend.edgecolor'] = '0.15'
        mpl.rcParams['text.color'] = '.15'
        mpl.rcParams['xtick.color'] = '.20'
        mpl.rcParams['xtick.direction'] = 'in'
        mpl.rcParams['xtick.major.size'] = 5.0
        mpl.rcParams['xtick.minor.size'] = 2.0
        mpl.rcParams['ytick.color'] = '.20'
        mpl.rcParams['ytick.direction'] = 'in'
        mpl.rcParams['ytick.major.size'] = 5.0
        mpl.rcParams['ytick.minor.size'] = 2.0
        mpl.rcParams['mathtext.default'] = 'regular'
        txt = 'theme set: Rella20170503'
    elif theme == 'SIX':
        mpl.rcParams['agg.path.chunksize'] = 10000
        mpl.rcParams['axes.axisbelow'] = True
        mpl.rcParams['axes.edgecolor'] = '.25'
        mpl.rcParams['axes.facecolor'] = '1.0'
        mpl.rcParams['figure.autolayout'] = True
        mpl.rcParams['axes.labelcolor'] = '0.15'
        mpl.rcParams['axes.linewidth'] = 1.5
        mpl.rcParams['figure.facecolor'] = 'white'
        mpl.rcParams['figure.max_open_warning'] = 500
        mpl.rcParams['font.family'] = ['sans-serif']
        mpl.rcParams['font.sans-serif'] = ['Arial', 'Liberation Sans', 
                                         'Bitstream Vera Sans', 'sans-serif']
        mpl.rcParams['grid.color'] = '0.95'
        mpl.rcParams['grid.linestyle'] = '-'
        mpl.rcParams['grid.linewidth'] = 1.0
        mpl.rcParams['axes.grid'] = True
        mpl.rcParams['image.cmap'] = 'Greys'
        mpl.rcParams['legend.frameon'] = True
        mpl.rcParams['legend.numpoints'] = 1
        mpl.rcParams['legend.scatterpoints'] = 3
        mpl.rcParams['lines.solid_capstyle'] = 'round'
        mpl.rcParams['legend.facecolor'] = 'white'
        mpl.rcParams['legend.edgecolor'] = '0.15'
        mpl.rcParams['text.color'] = '.15'
        mpl.rcParams['xtick.color'] = '.20'
        mpl.rcParams['xtick.direction'] = 'in'
        mpl.rcParams['xtick.major.size'] = 5.0
        mpl.rcParams['xtick.minor.size'] = 2.0
        mpl.rcParams['ytick.color'] = '.20'
        mpl.rcParams['ytick.direction'] = 'in'
        mpl.rcParams['ytick.major.size'] = 5.0
        mpl.rcParams['ytick.minor.size'] = 2.0
        mpl.rcParams['mathtext.default'] = 'regular'
        txt = 'theme set: Rella20180318'
    elif theme == 'SEVEN':
        mpl.rcParams["figure.figsize"]=(6,6)
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = "Verdana"
        if fontsize == None:
            mpl.rcParams["font.size"] = 11
        else:
            mpl.rcParams["font.size"] = fontsize
        mpl.rcParams["axes.linewidth"] = 0
        mpl.rcParams["xtick.major.width"] = 1.5
        mpl.rcParams["ytick.major.width"] = 1.5
        mpl.rcParams["xtick.major.size"] = 6
        mpl.rcParams["xtick.major.pad"] = 6
        mpl.rcParams["ytick.major.size"] = 6
        mpl.rcParams["ytick.major.pad"] = 6
        mpl.rcParams["figure.subplot.bottom"] = 0.1
        mpl.rcParams["figure.subplot.left"] = 0.1
        mpl.rcParams["xtick.minor.size"] = 4
        mpl.rcParams["xtick.minor.width"] = 1
        mpl.rcParams["ytick.minor.size"] = 4
        mpl.rcParams["ytick.minor.width"] = 1
        txt = 'theme set: Rella20140701'
    elif theme == 'EIGHT':
        mpl.rcParams['agg.path.chunksize'] = 10000
        mpl.rcParams['axes.axisbelow'] = True
        mpl.rcParams['axes.edgecolor'] = '.25'
        mpl.rcParams['axes.facecolor'] = '1.0'
        mpl.rcParams['figure.autolayout'] = False
        mpl.rcParams['axes.labelcolor'] = '0.15'
        mpl.rcParams['axes.linewidth'] = 1.5
        mpl.rcParams['figure.facecolor'] = 'white'
        mpl.rcParams['figure.max_open_warning'] = 500
        mpl.rcParams['font.family'] = ['sans-serif']
        mpl.rcParams['font.sans-serif'] = ['Arial', 'Liberation Sans', 
                                         'Bitstream Vera Sans', 'sans-serif']
        mpl.rcParams['grid.color'] = '0.95'
        mpl.rcParams['grid.linestyle'] = '-'
        mpl.rcParams['grid.linewidth'] = 1.0
        mpl.rcParams['axes.grid'] = True
        mpl.rcParams['image.cmap'] = 'Greys'
        mpl.rcParams['legend.frameon'] = True
        mpl.rcParams['legend.numpoints'] = 1
        mpl.rcParams['legend.scatterpoints'] = 3
        mpl.rcParams['lines.solid_capstyle'] = 'round'
        mpl.rcParams['legend.facecolor'] = 'white'
        mpl.rcParams['legend.edgecolor'] = '0.15'
        mpl.rcParams['text.color'] = '.15'
        mpl.rcParams['xtick.color'] = '.20'
        mpl.rcParams['xtick.direction'] = 'in'
        mpl.rcParams['xtick.major.size'] = 5.0
        mpl.rcParams['xtick.minor.size'] = 2.0
        mpl.rcParams['ytick.color'] = '.20'
        mpl.rcParams['ytick.direction'] = 'in'
        mpl.rcParams['ytick.major.size'] = 5.0
        mpl.rcParams['ytick.minor.size'] = 2.0
        mpl.rcParams['mathtext.default'] = 'regular'
        txt = 'theme set: Rella20200926 - SIX with tight_layout disabled'
    else:
        mpl.rcParams["figure.figsize"]=(6,6)
        mpl.rcParams["font.family"] = "sans-serif"
        mpl.rcParams["font.sans-serif"] = "Verdana"
        if fontsize == None:
            mpl.rcParams["font.size"] = 11
        else:
            mpl.rcParams["font.size"] = fontsize
        mpl.rcParams["axes.linewidth"] = 2
        mpl.rcParams["xtick.major.width"] = 1.5
        mpl.rcParams["ytick.major.width"] = 1.5
        mpl.rcParams["xtick.major.size"] = 6
        mpl.rcParams["xtick.major.pad"] = 6
        mpl.rcParams["ytick.major.size"] = 6
        mpl.rcParams["ytick.major.pad"] = 6
        mpl.rcParams["figure.subplot.bottom"] = 0.2
        mpl.rcParams["figure.subplot.left"] = 0.2
        mpl.rcParams["xtick.minor.size"] = 4
        mpl.rcParams["xtick.minor.width"] = 1
        mpl.rcParams["ytick.minor.size"] = 4
        mpl.rcParams["ytick.minor.width"] = 1
        txt = 'theme set: Rella20140701'    
    return txt

"""
class Palette():
    self.P0 = '#FF3500'
    self.P1 = '#FF9C82'
    self.P2 = '#FF5B2F'
    self.P3 = '#C22900'
    self.P4 = '#841B00'
    
    self.S1 = '#FF8900'
    self.S2 = '#FFC582'
    self.S3 = '#FF9F2F'
    self.S4 = '#C26800'
    self.S5 = '#844700'

    self.
*** Secondary color (2):

   shade 0 = #009BE6 = rgb(  0,155,230) = rgba(  0,155,230,1) = rgb0(0,0.608,0.902)
   shade 1 = #88D8FF = rgb(136,216,255) = rgba(136,216,255,1) = rgb0(0.533,0.847,1)
   shade 2 = #3ABFFF = rgb( 58,191,255) = rgba( 58,191,255,1) = rgb0(0.227,0.749,1)
   shade 3 = #00537B = rgb(  0, 83,123) = rgba(  0, 83,123,1) = rgb0(0,0.325,0.482)
   shade 4 = #003853 = rgb(  0, 56, 83) = rgba(  0, 56, 83,1) = rgb0(0,0.22,0.325)

*** Complement color:

   shade 0 = #00EC66 = rgb(  0,236,102) = rgba(  0,236,102,1) = rgb0(0,0.925,0.4)
   shade 1 = #82FFB8 = rgb(130,255,184) = rgba(130,255,184,1) = rgb0(0.51,1,0.722)
   shade 2 = #2FFF8A = rgb( 47,255,138) = rgba( 47,255,138,1) = rgb0(0.184,1,0.541)
   shade 3 = #008B3C = rgb(  0,139, 60) = rgba(  0,139, 60,1) = rgb0(0,0.545,0.235)
   shade 4 = #005E29 = rgb(  0, 94, 41) = rgba(  0, 94, 41,1) = rgb0(0,0.369,0.161)


#####  Generated by Paletton.com (c) 2002-2014"""

def MandS(start,end,data,cols):
    AA = []
    for c in cols:
        a = [] 
        for k in range(len(start)):
            a.append(np.average(data[start[k]:end[k],c]))
        AA.append(a)
    return np.array(AA)
    
def movingaverage(interval, window_size):
    window= np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

def SparseAverage(Y,n):
    N = len(Y)
    M = N/n
    aY = []
    for i in range(M):
        aY.append(np.mean(Y[i*n:(i+1)*n]))
    try:
        aY.append(np.mean(Y[(M-1)*n:]))
    except:
        pass
    return np.array(aY)

def savefigfunc(F, fn, dpi=400):
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

    def savefig(self,F,fn=None,dpi=400, closeMe=False, useTightLayout=True):
        F.show()
        if useTightLayout:
            F.tight_layout()        
        if fn is not None:
            savefigfunc(F, self.makeFilePath(fn), dpi=dpi)
        if closeMe:
            plt.close(F)

def makeAnimatedGif(imagesDIR, pattern='.png', outname=r'animatedGif.gif'): 
    files = os.listdir(imagesDIR) 
    files.sort()
    with imageio.get_writer(outname, mode='I', fps=30, subrectangles=True) as writer:
        for fn in files:
            if pattern in fn:
                print(fn)
                image = imageio.imread(os.path.join(imagesDIR, fn))
                writer.append_data(image)                
    writer.close()
    


if __name__ == "__main__":   
    def arbgridtest():
        A,F = MakerArbGrid(size=(6,6), grid=(2,3), panels=[[(0,1), (0,2)],
                                                           [(1,2), (0,2)],
                                                           [(0,1), (2,3)],
                                                           [(1,2), (2,3)]])
    