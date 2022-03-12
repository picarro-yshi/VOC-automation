## Mongo database test

# from random import randint
# import matplotlib.pyplot as plt
# from matplotlib.animation import FuncAnimation

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

# import dotenv
import sys
# from pathlib import Path
from typing import Any, Dict, Tuple, Union
import json
import os
# from pprint import pprint

gas = '176 - Acetic Acid'
cid = 176
date = '20211124'
gas_name = 'broadband_gasConcs_' + str(cid)
spline_name = 'broadband_splineconc_' + str(cid)
volume = 10/1000 #droplet in mL
weight = 0.0090 #g
startTime = '20211124 08:00'
endTime = '20211124 23:59'
thing = ''

# client = MongoClient('localhost1:27017')
DB_JSON_FILENAME = r'SpectralDatabaseDefinitionLinux.json'

# try:
#     DB_CONFIG = {
#         'username': dotenv.dotenv_values("/etc/picarro/sl_env").get("NAME"),
#         'password': dotenv.dotenv_values("/etc/picarro/sl_env").get("PASS")
#     }
#     print(DB_CONFIG)
#     print('get')
# except PermissionError:
#     DB_CONFIG = {
#         'username': None,
#         'password': None
#     }

DATABASE_DEFINITION = DB_JSON_FILENAME

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

    def load_spectral_db_definition(self, filename=DATABASE_DEFINITION):
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







