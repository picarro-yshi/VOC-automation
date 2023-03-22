import matplotlib.pyplot as plt
import numpy as np
import os
import h5py
import tables
import time
# filename = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/8785 - Benzyl Acetate/20230105/PrivateData/broadband/NUV1022-20230105-164351-DataLog_NewFitter_Private.h5'


def loadprivate(fnr):   # from Chris's datautility3
    ht = []   #head tags
    dat = None
    # fd = os.path.join(fnr, 'PrivateData', 'broadband')
    fd = fnr
    N = len(os.listdir(fd))
    ct = 1
    for f in os.listdir(fd):
        ext = f[-3:]
        if ext == '.h5':
            fn = os.path.join(fd, f)
            fob5 = tables.open_file(fn)
            D = [g for g in fob5.root]
            if ht == []:
                ht = D[0].colnames

            for tag in ht:
                if tag == ht[0]:
                    datarray = np.array([D[0].col(tag)])
                else:
                    datarray = np.vstack((datarray, D[0].col(tag)))

            mydata = np.transpose(datarray)
            fob5.close()

        try:
            if dat is None:
                dat = mydata
            else:
                dat = np.vstack((dat, mydata))
        except:
            print('dat array dimension changed in file %s. Try remove the first file and re-run.' % f)

        print("Loading %d / %d... " % (ct, N))
        ct += 1
    return ht, dat


def h(name):
    j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
    return dat[:, j]


if __name__ == "__main__":
    fnr = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/8785 - Benzyl Acetate/20230105/PrivateData/broadband'
    ht, dat = loadprivate(fnr)
    gas_name = 'broadband_gasConcs_8785'
    x = h('time')
    y = h(gas_name) * 1e6

    x_t = [x[0]]  # x data that will be marked
    xmak = [time.strftime('%H:%M', time.localtime(x[0]))]

    n = len(x)
    for i in range(1, n):
        clock0 = time.strftime('%M:%S', time.localtime(x[i - 1]))
        clock = time.strftime('%M:%S', time.localtime(x[i]))
        if (clock0[:2] == '29' and clock[:2] == '30') or (clock0[:2] == '59' and clock[:2] == '00'):
            x_t.append(x[i])
            xmak.append(time.strftime('%H:%M', time.localtime(x[i])))

    F, A = plt.subplots(dpi=150)
    A.set_facecolor('#Ededee')
    A.grid(c='white')
    # F.tight_layout()
    A.plot(x, y)
    A.set_xticks(x_t, xmak)
    A.set_ylabel('Conc. (ppm)', fontsize=12)
    A.set_xlabel('Clock time', fontsize=12)
    A.set_title(' Private Data')
    F.autofmt_xdate()         # x-label will not overlap
    plt.show()
