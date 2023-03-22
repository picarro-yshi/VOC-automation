## unzip and move data during selected time range from analyzer (local) to desired place, e.g. R/Data
## data can be RDF, Private, Combo or any of them
## Yilin Shi | Picarro | 2022.3.8
# how to use: fdpth, date, suffix will be path to the destination folder
# option 1: auto-fill, need a par folder containing:
### t1.txt for start time: yyyymmdd hh mm; t3.txt for end time: yyyymmdd hh mm (separate by return)
# option 2: manually type in stat and end time: yyyymmddhhmm

import sys
import os
import time
import datetime
import shutil
from zipfile import ZipFile

fna = '/home/picarro/I2000/Log/Archive'   #private and RDF
fnc = '/home/picarro/.combo_logger'       # combo results

# fn2 = tempfd + 'home/picarro/I2000/Log/DataLogger/DataLog_Private'
fnpp = os.path.join('home', 'picarro')  #join one by one
fnpp = os.path.join(fnpp, 'I2000')
fnpp = os.path.join(fnpp, 'Log')
fnpp = os.path.join(fnpp, 'DataLogger')
fnpp = os.path.join(fnpp, 'DataLog_Private') 


## copy files in selected time range:
def copyselec(fn, dst, epo1, epo3, bd=0):  ## source and destination folder path, start and end time
    files = []
    tag = 0
    for f in os.listdir(fn):    # sort files on time
        #print(f)
        if bd:   #SAM only needs *broadband*.h5 combo files
            if ('broadband' in f): 
                t = os.path.getmtime(os.path.join(fn, f))
                files.append([f, int(t)])       ## list[string, int]: [filename, time]
        else:    #calibration, takes all combos, including water, 3gas, etc.
            t = os.path.getmtime(os.path.join(fn, f))
            files.append([f, int(t)])       ## list[string, int]: [filename, time]

    files = sorted(files, key=lambda x: x[1])
    #print(files)

    for f in files:
        fpath = os.path.join(fn, f[0])
        t = f[1]
        if t > epo1:
           shutil.copy2(fpath, dst)   ## src, dst
           #print(f)
        if t >= epo3: 
            tag = t
            idx = files.index(f)
            break

    if ('combo' in fn) and tag:     #extra step for combo log, time tag must exist
        for f in files[idx+1:]:     ##for files create in same minutes
            if f[1] == tag:
                fpath = os.path.join(fn, f[0])
                shutil.copy2(fpath, dst)   ## src, dst
                #print(f)
            else: 
                break


## unzip file with original time stamp
def unzip(zipfile, outDirectory):  #path to .zip, destination folder
    dirs = {}
    with ZipFile(zipfile, 'r') as z:
        for f in z.infolist():
            z.extract(f, outDirectory)
            fpath = os.path.join(outDirectory, f.filename)
            # still need to adjust the dt o/w item will have the current dt
            # changes to dir dt will have no effect right now since files are
            # being created inside of it; hold the dt and apply it later
            date_time = time.mktime(f.date_time + (0, 0, -1))
            dirs[fpath] = date_time

    # done creating files, now update dir dt  #time will change when unzip to R drive, not change locally
    for fpath in dirs:
       date_time = dirs[fpath]
       os.utime(fpath, (date_time, date_time))


## move and unzip files 
# RDF
def uzmv1(fnar, fnr, epo1, epo3):   # source, destination r drive, start, end time
    fnrr = os.path.join(fnr, 'RDFs')                  
    tempfd = os.path.join(fnrr, 'tempfd')
    os.mkdir(tempfd)
    copyselec(fnar, tempfd, epo1, epo3)      #move RDF zips to temp folder
    for f in os.listdir(tempfd):
        if f.endswith('.zip'):
            #print(f)
            unzip(os.path.join(tempfd, f), tempfd)  

    if os.listdir(tempfd):  #not empty
        fnru = os.path.join(fnrr, 'unpackedFiles')
        if not os.path.isdir(fnru):
            os.mkdir(fnru)
        # fn1 = tempfd + '/home/picarro/I2000/Log/RDF'
        fn1 = os.path.join(tempfd, 'home')    #join one by one
        fn1 = os.path.join(fn1, 'picarro')
        fn1 = os.path.join(fn1, 'I2000')
        fn1 = os.path.join(fn1, 'Log')
        fn1 = os.path.join(fn1, 'RDF')       
        copyselec(fn1, fnru, epo1, epo3+60)   # move unzipped RDF from temp to unpackedFiles folder.+60: file saved in same minute
    shutil.rmtree(tempfd)                     # delete temp folder

# Private
def uzmv2(fnap, fnr, epo1, epo3):   # source, destination r drive, start, end time
    fnrp = os.path.join(fnr, 'PrivateData') 
    tempfd = os.path.join(fnrp, 'tempfd')
    os.mkdir(tempfd)
    copyselec(fnap, tempfd, epo1, epo3)        #move Private zips to temp folder
    for f in os.listdir(tempfd):
        if f.endswith('.zip'):
            #print(f)
            unzip(os.path.join(tempfd, f), tempfd)  

    if os.listdir(tempfd):           #not empty
        fnru = os.path.join(fnrp, 'unpackedFiles')
        if not os.path.isdir(fnru):
            os.mkdir(fnru)  
        # fn2 = tempfd + 'home/picarro/I2000/Log/DataLogger/DataLog_Private'
        fn2 = os.path.join(tempfd, fnpp)     #join one by one
        fn3 = os.path.join(fnrp, 'broadband')
        fn4 = os.path.join(fnrp, 'private')
        fn31 = os.path.join(fnrp, 'broadband1')  # separate to different catagories
        fn41 = os.path.join(fnrp, 'private1')
                                  
        ## move unziped files to folders
        os.mkdir(fn31)
        os.mkdir(fn41)             
        for f in os.listdir(fn2):
            if 'NewFitter' in f:
                shutil.move(os.path.join(fn2, f), fn31)
            elif 'DataLog_Private' in f:
                shutil.move(os.path.join(fn2, f), fn41)   

        if not os.path.isdir(fn3):
            os.mkdir(fn3)
        if not os.path.isdir(fn4):
            os.mkdir(fn4)  
        copyselec(fn31, fn3, epo1+63, epo3)     # move unzipped private from temp to broadband or private folder
        copyselec(fn41, fn4, epo1+63, epo3)     # start the next minute, to avoid datakey error
        shutil.rmtree(fn31)
        shutil.rmtree(fn41)  
    shutil.rmtree(tempfd)                    # delete temp folder   
    

#sorted time list and dict
def sortfile(fpath):  
    a = []            #list of time, small -> large
    b = {}            #dict[time]: filename
    for f in os.listdir(fpath):   
        t = int(os.path.getmtime(os.path.join(fpath, f))) #integer
        a.append(t)   
        b[t] = f      
        a.sort()
    return a, b


# find the last needed folder
def findend(tc1, epo3, fdtype):
    endfd = None  #name of end folder
    if fdtype == 1:    #RDF
        fd3 = os.path.join(fna, tc1[:4]+'-'+tc1[4:6]+'-'+tc1[6:8]+'-RDF', 'RDF')      # end day RDF path  /home/picarro/I2000/Log/Archive/2022-03-01-RDF/RDF
    elif fdtype == 2:  #private
        fd3 = os.path.join(fna, tc1[:4]+'-'+tc1[4:6]+'-'+tc1[6:8], 'DataLog_Private') # end day private path /home/picarro/I2000/Log/Archive/2022-03-01/DataLog_Private
    elif fdtype == 3:  #Combo
        fd3 = os.path.join(fnc, tc1)                                                  # end day Combo path /home/picarro/.combo_logger/20220301
    #print(fd3)

    if os.path.isdir(fd3):
        a, _ = sortfile(fd3)        

        if a[-1] >= epo3:
            endfd = tc1  # data ready!!! end folder= end day
        else:  
            print('check end day+1')
            epo = datetime.datetime(int(tc1[:4]),int(tc1[4:6]),int(tc1[6:8]),23,59).timestamp()+300  # end day+1,  +10s still today          
            t1 = time.strftime('%Y%m%d', time.localtime(epo))                                        # end day+1 date

            if fdtype == 1:    #RDF
                fd4 = os.path.join(fna, t1[:4]+'-'+t1[4:6]+'-'+t1[6:8]+'-RDF', 'RDF')      # end day+1 RDF path  /home/picarro/I2000/Log/Archive/2022-03-02-RDF/RDF 
            elif fdtype == 2:  #private
                fd4 = os.path.join(fna, t1[:4]+'-'+t1[4:6]+'-'+t1[6:8], 'DataLog_Private') # end day+1 private path /home/picarro/I2000/Log/Archive/2022-03-02/DataLog_Private
            elif fdtype == 3:  #Combo
                fd4 = os.path.join(fnc, t1)                                                # end day+1 Combo path /home/picarro/.combo_logger/20220302
                        
            if os.path.isdir(fd4):
                a, _ = sortfile(fd4)                                    
                if a[-1] >= epo3:   # latest time in end day+1
                    endfd = t1  # data ready!!! end folder = end day+1
    return endfd


## has input validation check
def pickdata(fdpath, folder, start, end, rdf=1, pri=1, com=1, bd=0):  #desination folder on r drive to put moved and unzipped data
    fnr = os.path.join(fdpath, folder)   #'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20220301' # r drive
    fnrr = os.path.join(fnr, 'RDFs') 
    fnrp = os.path.join(fnr, 'PrivateData')
    fnrc = os.path.join(fnr, 'ComboResults')
    tag = 0

    # check file
    if not os.path.isdir(fnr):
        print('Folder ' + folder + ' not found.')
    elif rdf and os.path.isdir(fnrr):
        print('RDFs folder already exists in %s folder, please delete it.'%folder)
    elif pri and os.path.isdir(fnrp):
        print('PrivateData folder already exists in %s folder, please delete it.'%folder)
    elif com and os.path.isdir(fnrc):
        print('ComboResults folder already exists in %s folder, please delete it.'%folder)
    else:
        tag = 1

    #check time
    if tag: 
        try:
            ta1 = start[:8]    #202206171227
            ta2 = start[8:10]
            ta3 = start[10:12]

            tc1 = end[:8]      #202206190559
            tc2 = end[8:10]
            tc3 = end[10:12]

            epo1 = datetime.datetime(int(ta1[:4]),int(ta1[4:6]),int(ta1[6:8]),int(ta2[:2]),int(ta3[:2])).timestamp()  #start
            epo3 = datetime.datetime(int(tc1[:4]),int(tc1[4:6]),int(tc1[6:8]),int(tc2[:2]),int(tc3[:2])).timestamp()  #end
            if epo1>=epo3:
                tag = 0
                print('Error, start time is after end time.')
        except:
            print('start or end time format wrong; should be yyyymmddhhmm.')
            tag = 0


    if tag:
        try:
            if rdf:     ## RDF 
                endfdr = findend(tc1, epo3, 1)  #name of end folder RDF
                print(endfdr)
                if endfdr is None:
                    print('RDF files not ready. Data acquisition not finished, please check back later.')
                else:
                    print('working on RDF files...') 
                    os.mkdir(fnrr)   #'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20220301/RDFs'                    
                    t = time.time()
                    fd = ta1 # folder date 20220301
                    while 1:
                        fnar = os.path.join(fna, fd[:4]+'-'+fd[4:6]+'-'+fd[6:8]+'-RDF', 'RDF')    # day1 RDF path  /home/picarro/I2000/Log/Archive/2022-03-01-RDF/RDF                         uzmv1(fnr, fnar, epo1, epo3)
                        uzmv1(fnar, fnr, epo1, epo3)  #source, des
                        if fd == endfdr:
                            break
                        else:
                            epo = datetime.datetime(int(fd[:4]),int(fd[4:6]),int(fd[6:8]),23,59).timestamp()+300  # next day          
                            fd = time.strftime('%Y%m%d', time.localtime(epo))  
                    print(time.time()-t)


            if com:     ## Combo
                endfdc = findend(tc1, epo3, 3)  #name of end folder Combo
                print(endfdc)
                if endfdc is None:
                    print('Combo files not ready. Data acquisition not finished, please check back later.')
                else:
                    print('working on Combo files...') 
                    os.mkdir(fnrc)   #'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20220301/ComboResults'                    
                    t = time.time()
                    fd = ta1 # folder date 20220301
                    while 1:
                        fnc1 = os.path.join(fnc, fd)       # day1 Combo path /home/picarro/.combo_logger/20220301
                        copyselec(fnc1, fnrc, epo1, epo3, bd)  #source, des

                        if fd == endfdc:
                            #print('break')
                            break
                        else:
                            epo = datetime.datetime(int(fd[:4]),int(fd[4:6]),int(fd[6:8]),23,59).timestamp()+300  # next day          
                            fd = time.strftime('%Y%m%d', time.localtime(epo))  
                            #print(fd)



                    print(time.time()-t)


            tag1 = 0
            if pri:     ## Private
                endfdp = findend(tc1, epo3, 2)  #name of end folder Private
                print(endfdp)
                if endfdp is None:
                    print('Private files not ready. Data acquisition not finished, please check back later.')
                else:
                    print('working on Private files...') 
                    os.mkdir(fnrp)   #'/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/176 - Acetic Acid/20220301/PrivateData'
                    t = time.time()
                    fd = ta1 # folder date 20220301
                    while 1:
                        fnap = os.path.join(fna, fd[:4]+'-'+fd[4:6]+'-'+fd[6:8], 'DataLog_Private') # day1 private path /home/picarro/I2000/Log/Archive/2022-03-01/DataLog_Private
                        uzmv2(fnap, fnr, epo1, epo3)  #source, des
                        if fd == endfdp:
                            break
                        else:
                            epo = datetime.datetime(int(fd[:4]),int(fd[4:6]),int(fd[6:8]),23,59).timestamp()+300  # next day          
                            fd = time.strftime('%Y%m%d', time.localtime(epo))  
                    print(time.time()-t)


                    # corner case: DataLog_Private
                    bdpath = os.path.join(fnrp, 'broadband')   #for new_fitter
                    a, _ = sortfile(bdpath)
                    if a[-1] < epo3:     #need first file of next private zip
                        print('need next zip for new_fitter in PrivateData/broadband')
                        a, b = sortfile(fnap)   #get fnap from above iteration

                        for i in range(len(a)):
                            if a[i] >= epo3:
                                break
                        idx = i+1  #regular copy stop here, need the next .zip                        

                        if len(a) == idx:  #this is last item in end day folder, look for next day
                            print('end day+1')
                            epo = datetime.datetime(int(endfdp[:4]),int(endfdp[4:6]),int(endfdp[6:8]),23,59).timestamp()+300  # next day          
                            fd = time.strftime('%Y%m%d', time.localtime(epo)) 
                            fnap2 = os.path.join(fna, fd[:4]+'-'+fd[4:6]+'-'+fd[6:8], 'DataLog_Private')
                            print(fnap2)

                            if os.path.isdir(fnap2):
                                a1, b1 = sortfile(fnap2)  
                                fname = b1[a1[0]]  #first .zip name
                                print(fname)
                                
                                tempfd = os.path.join(bdpath, 'tempfd')
                                os.mkdir(tempfd)
                                shutil.copy2(os.path.join(fnap2, fname), bdpath)   #src, dst path
                                unzip(os.path.join(bdpath, fname), tempfd)  

                                tempfd1 = os.path.join(tempfd, fnpp)
                                a1, b1 = sortfile(tempfd1) 
                                fname1 = b1[a1[0]]  #first file name inside the zip
                                print(fname1)

                                shutil.copy2(os.path.join(tempfd1, fname1), bdpath)
                                shutil.rmtree(tempfd)  
                                os.remove(os.path.join(bdpath, fname))                                                                                
                            else:
                                tag1 = 1

                        else:
                            print('one more file in end day folder')
                            fname = b[a[idx]]
                            print(fname)
                            tempfd = os.path.join(bdpath, 'tempfd')
                            os.mkdir(tempfd)
                            shutil.copy2(os.path.join(fnap, fname), bdpath)
                            unzip(os.path.join(bdpath, fname), tempfd)  #path to .zip, destination folder

                            tempfd1 = os.path.join(tempfd, fnpp)
                            a1, b1 = sortfile(tempfd1)
                            fname1 = b1[a1[0]]  #first file name inside the zip
                            print(fname1)

                            shutil.copy2(os.path.join(tempfd1, fname1), bdpath)
                            shutil.rmtree(tempfd) 
                            os.remove(os.path.join(bdpath, fname))  
                        
            if tag1:
                print('All files moved, but need one more new_fitter file to be copied into PrivateData/broadband folder, \nwhich is not ready yet. Please check back later.')
            else:
                print('*** Finish moving and unzip data to folder %s! You may start to analyze now.'%folder)    

        except:
            print('Error extract data.')

        


if __name__=='__main__':
    # option 1: auto-fill, need a par folder containing start and end time
    # option 2: manually type in stat and end time: yyyymmddhhmm
    # rdf=1: pick RDF data; 0: no
    # pri=1: pick private data; 0: no
    # com=1: pick combo logs; 0: no
    # bd=1 only pick combo files has 'broadband' in their names; bd=0: pick all combo files

    option = 1  # 1: calibration, read time automatically; 2: pick some data

    if option == 1:    # for calibration
        fname = '/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration'   ## R drive
        #gas = '7501 - Styrene'
        #gas = '7929 - m-Xylene'
        #gas = '7874 - Tetradecamethylcycloheptasiloxane (D7)'
        #gas = '8857 - Ethyl Acetate'
        #gas = '7950 - 1,3,5-trichlorobenzene'
        #gas = '7947 - 1,3,5-trimethylbenzene'
        #gas = '7239 - 1,2-Dichlorobenzene'
        #gas = '7247 - 1,2,4-trimethylbenzene'
        #gas = '4685 - 1,4-dichlorobenzene'
        #gas = '11169 - Octamethylcyclotetrasiloxane (D4)'
        #gas = '6895 - 1,2,3-trichlorobenzene'
        gas = '7410 - acetophenone'
        #gas = '7967 - cyclohexanone'   
        date = '20230321'     
        suffix = ''           ## folder suffix or ''
        fdpath = os.path.join(fname, gas)    #destination
        folder = date + suffix

        fnrpar = os.path.join(fdpath, folder, 'par')
        if not os.path.isfile(os.path.join(fnrpar, 't1.txt')):
            print('Experiment start time  par/t1.txt  not found.')
        elif not os.path.isfile(os.path.join(fnrpar, 't3.txt')):
            print('Experiment end time  par/t3.txt  not found.')
        else:
            try:
                f = open(os.path.join(fnrpar, 't1.txt'), 'r')
                temp = f.read().splitlines()
                ta1 = temp[0]
                ta2 = temp[1]
                ta3 = temp[2]
                f = open(os.path.join(fnrpar, 't3.txt'), 'r')
                temp = f.read().splitlines()
                tc1 = temp[0]
                tc2 = temp[1]
                tc3 = temp[2]

                start = ta1+ta2+ta3
                end = tc1+tc2+tc3
                print(start, end)
                pickdata(fdpath, folder, start, end)
                #pickdata(fdpath, folder, start, end, 0, 1, 0)
                #pickdata(fdpath, folder, start, end, 1, 0, 1)
            except:
                print('t1.txt or t3.txt format wrong, should by yyyymmdd hh mm separated by return.')    

    # pick some data: 
    elif option == 2:
        #fdpath = '/mnt/r/Validation_test_bed'
        fdpath = '/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/20230222 - ZA 3000 ppm CO2 TP'
        #fdpath = '/mnt/r/crd_G9000/AVXxx/3610-NUV1022/R&D/Calibration/24764 - Hexamethyldisiloxane (HMDSO)'
        #folder = '20220824'      #destination
        folder = 'CO2b'      #destination
        start = '202302221444'   #yyyymmddhhmm
        end   = '202302221545'   #yyyymmddhhmm
        #pickdata(fdpath, folder, start, end, rdf=1, pri=1, com=1, bd=0)
        pickdata(fdpath, folder, start, end, rdf=1, pri=0, com=0, bd=0)

    
    















