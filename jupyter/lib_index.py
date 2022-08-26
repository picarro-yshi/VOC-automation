# check library value
# cid: value in library
import re

import h5py
import tables
from typing import Any, Dict, Tuple, Union, List
import json
import os
import sys
from pprint import pprint
import numpy as np
import collections

## Mongo
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

DB_JSON_FILENAME = r'SpectralDatabaseDefinitionLinux.json'

class SpectralDatabase:
    admin: 'Collection'
    pubChem: 'Collection'
    hitranAdmin: 'Collection'
    hitranPeaks: 'Collection'
    hitranMolecules: 'Collection'
    picarroPeaks: 'Collection'
    peakOverlays: 'Collection'
    compoundOverlays: 'Collection'
    generalOverlays: 'Collection'
    empiricalSpectra: 'Collection'
    MDB: 'MyMongoDB'

    def __init__(self, load_and_connect: bool = True, dbpath: Union[str, None] = None,
                 mongod_path: Union[str, None] = None, verbose: bool = False) -> None:
        self.database_definition: Dict[str, Any] = dict()
        if load_and_connect:
            self.database_definition = self.load_spectral_db_definition()
            if os.getenv("RUNNING_IN_DOCKER"):
                self.database_definition['admin']['DB_host'] = 'mongodb'

            if dbpath:
                self.database_definition['admin']['DB_path'] = dbpath

            self.database_definition['admin']['mongod_path'] = mongod_path
            self.database_connect(verbose=verbose)

    def load_spectral_db_definition(self, filename=DB_JSON_FILENAME):
        """ Loads the Spectral database definition file """
        with open(filename, 'r') as f:
            db_json = json.load(f)
        # print(db_json)
        return db_json

    def database_connect(self, verbose: bool = False) -> None:
        # connect to mongo server
        db_conf = self.database_definition['admin']
        name = db_conf['DB_name']
        path = db_conf['DB_path']
        host = db_conf['DB_host']
        self.MDB = MyMongoDB(name, path, host)

        self.collection_list = [k for k in self.database_definition if k != 'admin']

        for collection_name in self.collection_list:
            # LOGGER.debug(f'Connecting to {collection_name} collection...')
            try:
                collection = self.MDB.db[self.database_definition[collection_name]['name']]
                self.__setattr__(collection_name, collection)
                # LOGGER.debug(f'Connected to {collection_name}.')
            except KeyError:
                # LOGGER.error(f'{collection_name} collection does not exist')
                raise e

class MyMongoDB:
    client: 'MongoClient'
    mongod = None
    pid = None
    db: Database

    def __init__(self, DB_name: str, DB_path: str, DB_host: str, verbose: bool = False):
        self.DB_name = DB_name
        self.DB_path = DB_path
        self.DB_host = DB_host
        try:
            self.client = MongoClient(host=f'{DB_host}:27017', serverSelectionTimeoutMS=2000)
            # print('DB_host')
            # print(DB_host)
            self.client.list_database_names()
            # print('try1')
        except OperationFailure:
            self.client = MongoClient(host=f'{DB_host}:27017', serverSelectionTimeoutMS=2000, **DB_CONFIG)
            self.client.list_database_names()

        # LOGGER.debug('Attempting connection to MongoDB server on default port...')
        try:
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
            # print('try2')
        except ServerSelectionTimeoutError as e:
            # LOGGER.error('Cound not connect to MongoDB server. Is the server running?')
            raise e
        self.mongod = None

        self.db = self.client[DB_name]

    def terminateConnection(self, closeServer: bool = False) -> None:
        self.client.close()
        if self.mongod is not None and closeServer:  #server spawned from this thread
            # LOGGER.debug('Terminating MongoDB server...')
            self.mongod.terminate()
            while self.mongod.poll():
                time.sleep(0.5)
            # LOGGER.debug('MongoDB terminated successfully')

spec_lib = SpectralDatabase(verbose=True).MDB.db
print(spec_lib)
print(spec_lib.list_collection_names())

class PubChemEntry(object):
    def __init__(self, cid, download_unknown_entry=False):
        self.cid = cid
        self.download_unknown_entry = download_unknown_entry
        self.entry = self.getPubChemRecord(cid)

    def getPubChemRecord(self, cid):
        S = SpectralDatabase().MDB.db
        pubchem = S.pubChemEntries
        searcher = {'cid':cid}
        # FIXME: if not found, there should be a method of downloading the entry from PubChem
        entry = pubchem.find_one(searcher)
        return entry

    def parseFormula(self):
        pattern = r'(\D+)(\d*)'
        formula = self.entry['molecularFormula']
        if formula == 'H3N':
            formula = 'NH3'
        groups = re.findall(pattern, formula)
        txt = ''
        for alph, num in groups:
            if len(num) == 0:
                txt += alph
            else:
                txt += alph + '_{' + num + '}'
        return txt

    def __repr__(self):
        h = lambda name: self.entry[name]
        txt = '%d: %s (%s)' % (self.cid, h('commonName'), h('molecularFormula'))
        return txt

class extrema:
    def __init__(self):
        self.min = np.inf
        self.max = - np.inf

    def addData(self, x):
        if min(x) <= self.min:
            self.min = min(x)
        if max(x) >= self.max:
            self.max = max(x)

def survey_library_for_ecompounds(cid=None, version=None, dataCollectionDate=None):
    searchy = {}
    if cid:
        searchy['cid']= cid
    if version:
        searchy['version'] = version
    if dataCollectionDate:
        searchy['dataCollectionDate'] = dataCollectionDate

    S = SpectralDatabase().MDB.db
    recs = S.EmpiricalSpectra.find(searchy)
    ecompid_list = []
    xtr_list = []
    for r in recs:
        ecompid = {k:r[k] for k in ['cid', 'version', 'dataCollectionDate', 'dataType', 'uploadDate']}
        if ecompid not in ecompid_list:
            xtr_list.append(extrema())
            ecompid_list.append(ecompid)
        dkeys = r['dataDict'].keys()
        akey = next(iter(dkeys))
        nuarray = r['dataDict'][akey]['nu']
        xtr_list[ecompid_list.index(ecompid)].addData(nuarray)
    for j, x in enumerate(xtr_list):
        cid = ecompid_list[j]['cid']
        ecompid_list[j].update({'nustart':x.min, 'nuend':x.max, 'compound':str(PubChemEntry(cid))})
    return ecompid_list


def show_markdown_table(indict):
    def makeline(rowlist):
        rowlist = [str(r) for r in rowlist]
        return '| ' + ' | '.join(rowlist) + ' |'

    keys = list(indict.keys())
    txtlist = []
    txtlist.append(makeline(keys))
    txtlist.append(makeline(['----' for k in keys]))
    for row in zip(*tuple([indict[key] for key in keys])):
        txtlist.append(makeline(row))
    print('\n'.join(txtlist))

def display_ecompounds_in_library(ecompid_list):
    ecomp_dict = collections.defaultdict(list)
    for ecomp in ecompid_list:
        for tag in ['cid','compound', 'version', 'dataCollectionDate', 'uploadDate', 'nustart', 'nuend']:
            ecomp_dict[tag].append(ecomp[tag])
    show_markdown_table(ecomp_dict)



           #cid   #Date      #DataCollectionDate
lib_date = {176:  ['20220422'],    #acetic acid
            3776: ['20210330'],    #IPA
            180:  ['20210330', '20200309'],     #Acetone
            7900: ['20210330'],    #PGME
            7946: ['20210330', '20220610'],     #PGMEA
            13387:['20211201'],     # NMP 20210402
            7344:['20211006'],     # Ethyl lactate 20210917
            1140:['20210920', '20210514'],   # Toluene
            10914: ['20210331'],   # D3  20200831
            10911: ['20210330'],    # D6  20200821
            24764: ['20210330'],    # HMDSO  20200508
            284: ['20210330']       # formic acid, '20200422'

            }


if __name__ == "__main__":
    cid = 284 #7946 # 3776  #176 13387
    #show all records
    U = survey_library_for_ecompounds(cid, 2)  # cid, version, datacollection date'20200420'

    # sanity check
    tag = 0
    if len(U) == 0:
        print('Compound not in the library.')
    else:
        display_ecompounds_in_library(U)
        print()
        if cid not in lib_date:
            print('no time record of %s in lib_date, please find from above and add to lib_date.'%cid)
        else:
            if len(lib_date[cid]) == 1:
                Cal = spec_lib.EmpiricalSpectra.find_one({'cid':cid, 'version':2, 'pNominal':140}) #need to specify version
                tag = 1
            elif len(lib_date[cid]) == 2:
                try:
                    # Cal=spec_lib.EmpiricalSpectra.find_one({'cid':cid,'version':2, 'dataCollectionDate':lib_date[cid][1]})
                    Cal=spec_lib.EmpiricalSpectra.find_one({'cid':cid,'version':2, 'pNominal':140,'dataCollectionDate':lib_date[cid][1]})
                    # Cal=spec_lib.EmpiricalSpectra.find_one({'cid':cid,'version':2, 'pNominal':140})
                    tag = 1
                except:
                    print('dataCollectionData wrong, pick one from above table.')

    if tag:
        # pprint(Cal)
        try:
            set_cal = Cal['calibration'][lib_date[cid][0]]['concentration']
            print('cal value in lib')
            print(set_cal * 1e6)
        except:
            print('%s not exist in dataCollectionDate %s, pick one from below:'%
                  (lib_date[cid][0], lib_date[cid][1]))
        pprint(Cal['calibration']) #all dates in this dataCollectionDate



        # set_cal = Cal['calibration']['20210331']['concentration']   #acetic acid
        # set_cal = Cal['calibration']['20210330']['concentration']   #IPA






