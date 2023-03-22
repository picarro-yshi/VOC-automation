import numpy as np
import matplotlib.pyplot as plt
import time
import datetime
import os
import h5py
import tables
# filename = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/8785 - Benzyl Acetate/20230105/PrivateData/broadband/NUV1022-20230105-164351-DataLog_NewFitter_Private.h5'
# print(list(f1.keys()))   ##['results']

fd = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/8785 - Benzyl Acetate/20230105/PrivateData/broadband'
# print(os.listdir(fd))
# exit()
ht=[]

for f in os.listdir(fd):
    # print(f)
    if '.h5' in f:
        filename = os.path.join(fd, f)

        if not len(ht):
            fob5 = tables.open_file(filename)
            D = [g for g in fob5.root]
            ht = D[0].colnames
            print(ht)
            fob5.close()

        with h5py.File(filename, "r") as f:
            dat = f['results']
            # print(len(dat))
            print(dat[0])


    ## original line citing Chris's repo
    # ht, dat = LF.loadFilesH5(os.path.join(fnr, 'PrivateData', 'broadband'), N=-1)  ## headtag, data. all data in that range

    ## this works, but slow
    # ht = []
    # dat = []
    # fd = os.path.join(fnr, 'PrivateData', 'broadband')
    # for f in os.listdir(fd):
    #     # print(f)
    #     if '.h5' in f:
    #         filename = os.path.join(fd, f)
    #         if not len(ht):
    #             print('fill tag')
    #             fob5 = tables.open_file(filename)
    #             D = [g for g in fob5.root]
    #             ht = D[0].colnames
    #             # print(ht)
    #             fob5.close()
    #
    #         with h5py.File(filename, "r") as f:
    #             data = f['results']
    #             n = len(data)
    #             for i in range(n):
    #                 dat.append(list(data[i]))
    # dat = np.array(dat)
    # # print(dat.shape)
    # # print(dat)





