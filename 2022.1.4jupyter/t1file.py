## file operations: unzip, move, create

import numpy as np
from random import randint
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# # a = [1,2,3,2,5]
# # print(a[-1])
# dat = np.array([[1, 2, 3],
#               [0, 1, 2]])
# ht = ['a', 'bo', 'cat']
#
# def h(name):
#     j = ht.index(name)  # finds the index of the list ht that corresponds to 'name'
#     return dat[:, j]
#
# b=h('bo')
# print(b)
# a='1234a'
# print(not a.isdigit())

# fn = "RDF_20211124_163022.zip"
import shutil
import os
import datetime

# fname = '/lll'
# gas = '176- fg'
# date = '20211124'
# rdfDIR = os.path.join(fname, gas, date, 'RDFs')
# print (rdfDIR)
epoch_time = datetime.datetime(2021,11,24,8,0).timestamp()
a1 = '20211124'
a2 = '08'
a3 = '10'
epo1 = datetime.datetime(int(a1[:4]), int(a1[4:6]), int(a1[-2:]), int(a2), int(a3)).timestamp()
print(epo1)
print(epoch_time)
exit()



## check data drive is attached or not

t1=time.time()
# print('Unzip RDF files...')
# ## RDF files are here:
# ## /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c/RDFs/home/picarro/I2000/Log/RDF
# fnzip1 = "/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124c/RDFs/"
# fn1 = fnzip1 + '/home/picarro/I2000/Log/RDF/'
# for f in os.listdir(fnzip1):
#     if f.endswith('.zip'):
#         # print(f)
#         shutil.unpack_archive(fnzip1+f, fnzip1)
# print(time.time()-t1)
#
# print('Moving to unpackedFiles...')
# shutil.move(fn1, fnzip1, copy_function=shutil.copytree)  ## move up in directory
# os.rename(fnzip1+'RDF', fnzip1+'unpackedFiles')  ## rename folder
# shutil.rmtree(fnzip1+'home')                    ## delete 'home' folder
#
#
# ## private files location on Linux
# /mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/home/picarro/I2000/Log/DataLogger/DataLog_Private
fnzip2 = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20211124d/PrivateData/'
fn2 = fnzip2 + 'home/picarro/I2000/Log/DataLogger/DataLog_Private'

# for f in os.listdir(fnzip2):
#     if f.endswith('.zip'):
#         # print(f)
#         shutil.unpack_archive(fnzip2+f, fnzip2)
# print(time.time()-t1)
#
# print('Moving to unpackedFiles...')
# shutil.move(fn2, fnzip2, copy_function=shutil.copytree)  ## move up in directory
# os.rename(fnzip2+'DataLog_Private', fnzip2+'unpackedFiles')  ## rename folder
# shutil.rmtree(fnzip2+'home')                    ## delete 'home' folder

## move unziped files to folders
fn3 = fnzip2 + 'broadband/'
fn4 = fnzip2 + 'private/'
fn5 = fnzip2 + 'unpackedFiles/'

if os.path.exists(fn3):
    shutil.rmtree(fn3)
if os.path.exists(fn4):
    shutil.rmtree(fn4)
os.mkdir(fn3)
os.mkdir(fn4)

for f in os.listdir(fn5):
    if 'VOC_broadband' in f:
        shutil.move(fn5+f, fn3)
    elif 'DataLog_Private' in f:
        shutil.move(fn5+f, fn4)




t2=time.time()
print(t2-t1)


# from zipfile import ZipFile
# import zipfile
# zf = ZipFile(fnzip+f, 'r')
# zf.extractall(fnzip)
# # zf.close()

## slow
# for f in os.listdir(fn2):
#     # shutil.move(fn2+f, fnzip+'unp')  ## 7.9220969676971436s
#     os.rename(fn2 + f, fnzip +'unp/' + f)




# fname = '/Volumes/Data/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/j1.txt'
# with open(fname, 'r') as fp:
#     temp = fp.read().splitlines()
#     print(temp[0])


