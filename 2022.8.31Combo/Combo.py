## look at combo log data, RMSE time series

import os
import matplotlib.pyplot as plt
from spectral_logger1 import SpectralLogReader as slog
import GoldenCalibrationUtilities as GCU


def lookcombo(fnr):
    read = slog(os.path.join(fnr, 'ComboResults'), verbose=True)
    _, _, max_row = read.get_spectra_row('broadband', 100, pull_results=True)
    ycombo = []
    yconc = []
    # x = list(range(max_row))
    x = list(range(1300, 1700))

    for row in x:
        data = read.get_spectra_row('broadband', row, pull_results=True)
        residuals = data[0]['residuals']
        partial_fit = data[0]['partial_fit']

        n = len(residuals)
        f = 0
        r = 0
        for i in range(n):
            f += partial_fit[i] ** 2
            r += residuals[i] ** 2
        ycombo.append(((f / n) ** 0.5) / ((r / n) ** 0.5))
        yconc.append(data[1]['gasConcs_24764'] * 1000000)

    col1 = 'steelblue'
    col2 = 'dimgrey'
    figure, axis = plt.subplots(2)
    ax1 = axis[0]
    ax2 = axis[1]
    ax1.set_title('Combo Log Study')
    ax1.set_xlabel('row')

    ax1.plot(x, ycombo, color=col1)
    ax1.set_ylabel('Phi/RMSE(residue)', color=col1, fontsize=14)
    ax1.spines['right'].set_color(col2)

    ax1a = ax1.twinx()
    ax1a.plot(x, yconc, color=col2)
    ax1a.set_ylabel('Concentration, ppm', color=col2, fontsize=14)
    ax1a.spines['left'].set_color(col1)

    # spectrum of 2 rows
    data = read.get_spectra_row('broadband', 1400, pull_results=True)
    nu = data[0]['nu']
    k = data[0]['absorbance']
    ax2.plot(nu, k, col1, label='row = 1400 spectrum')

    data = read.get_spectra_row('broadband', 1450, pull_results=True)
    nu = data[0]['nu']
    k = data[0]['absorbance']
    ax2.plot(nu, k, col1, linestyle='dashed', label='row = 1450 spectrum')
    ax2.legend()
    ax2.set_ylabel('Absorbance', color=col1, fontsize=14)
    ax2.spines['right'].set_color(col2)

    #spectrum of dif
    ax2a = ax2.twinx()
    ax2.set_xlabel('nu')
    # ax2.set_title('Selected Spectra')

    data = read.get_spectra_row('broadband', 1400, pull_results=True)
    nu = data[0]['nu']
    k1 = data[0]['absorbance']
    data = read.get_spectra_row('broadband', 1450, pull_results=True)
    k2 = data[0]['absorbance']
    ax2a.plot(nu, k1-k2, col2)
    ax2a.set_ylabel('row difference 1400-1450', color=col2, fontsize=14)
    ax2a.spines['left'].set_color(col1)

    plt.show()



if __name__ == "__main__":
    # fname = r'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/'          ##Linux
    fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration'       ##Mac
    # fname = 'R:\crd_G9000\AVXxx\\3610-NUV1022\R&D\Calibration'               ## Windows
    pct = 3  # zero 2 < zero1 + pct*sigma, end experiment

    start = '20220825'   #20220609 droplet   20220608t2b tank no RDF
    suffix = 'd2'
    gas = '24764 - Hexamethyldisiloxane (HMDSO)'

    fnr = os.path.join(fname, gas, start+suffix)
    print(fnr)
    lookcombo(fnr)




