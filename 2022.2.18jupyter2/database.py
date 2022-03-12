import json
import os
import re
import sys
import time
from bisect import bisect
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple, Union

import dotenv
# from lologger.lologger_client import get_lologger_client_by_os_env
from numpy import inf
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError

DB_JSON_FILENAME = r'SpectralDatabaseDefinitionLinux.json'


try:
    DB_CONFIG = {
        'username': dotenv.dotenv_values("/etc/picarro/sl_env").get("NAME"),
        'password': dotenv.dotenv_values("/etc/picarro/sl_env").get("PASS")
    }
    # print(DB_CONFIG)
except PermissionError:
    DB_CONFIG = {
        'username': None,
        'password': None
    }


# if getattr(sys, 'frozen', False) or hasattr(sys, '_MEIPASS'):
#     DATABASE_DEFINITION = Path(sys._MEIPASS) / DB_JSON_FILENAME
# else:
#     DATABASE_DEFINITION = Path(__file__).parent / DB_JSON_FILENAME

DATABASE_DEFINITION = DB_JSON_FILENAME

# LOGGER = get_lologger_client_by_os_env(__name__)

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
            self.client.list_database_names()
        except OperationFailure:
            self.client = MongoClient(host=f'{DB_host}:27017', serverSelectionTimeoutMS=2000, **DB_CONFIG)
            self.client.list_database_names()

        # LOGGER.debug('Attempting connection to MongoDB server on default port...')
        try:
            # The ismaster command is cheap and does not require auth.
            self.client.admin.command('ismaster')
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


def retrieve_empirical_spectrum_record(db: 'SpectralDatabase', cid: int, nu_min: float,
                                       nu_max: float,  nominal_pressure: float, version: int = 0,
                                       date_str: str = '') -> Dict[str, Any]:
    version = version_by_cid(db, cid, version)
    nominal_pressure = closest_nominal_pressure(db, cid, version, nominal_pressure)
    if date_str == '':
        date_str = time.strftime("%Y%m%d", time.localtime())
    data_collection_date, spline_creation_date = latest_data_collection_date_by_upload_time(db, cid, date_str, nominal_pressure)
    e_compound_search = {'cid': cid,
                         'version': version,
                         'dataCollectionDate': data_collection_date,
                         'splineCreationDate': spline_creation_date,
                         'pNominal': nominal_pressure}
    # LOGGER.debug(f'Fetching {e_compound_search}')
    return load_empirical_spectrum(db, nu_min, nu_max, e_compound_search)


def version_by_cid(db, cid: int, wanted_version: int = 0) -> int:
    """ EmpiricalSpectra documents can be partitioned by version. This function will select a version
    by the following logic:

    If the the ``wanted_version`` parameter is 0, choose the latest version.
    Otherwise, choose the version that is less than or equal to the ``wanted_version``.
    ``wanted_version`` must be non-negative.
    """
    if wanted_version < 0:
        raise ValueError(f'Parameter "wanted_version" should be positive: {wanted_version}')
    versions = [x['version'] for x in db.empiricalSpectra.find({'cid': cid}, {'version': 1, '_id': 0})]
    versions = sorted(set(versions))
    if wanted_version == 0:
        wanted_version = max(versions)

    index = bisect(versions, wanted_version)
    # Note: bisect.bisect will return an insertion index for maintaining and ordered list.
    # To get the wanted version itself, we must subtract one from that index.
    version = versions[index - 1]
    return version


def closest_nominal_pressure(db, cid, version, wanted_pressure):
    """ Given a CID and a version, choose the closest nominal pressure to ``wanted_pressure``, in
    an absolute sense. """
    # Find all unique pressures
    pressures = set([x['pNominal'] for x in db.empiricalSpectra.find({'cid': cid, 'version': version}, {'pNominal': 1, '_id': 0})])

    # Find minimum difference between nominal pressure from spectral library and the wanted_pressure
    norms = [(nominal_pressure, abs(wanted_pressure - nominal_pressure)) for nominal_pressure in pressures]
    return min(norms, key=lambda x: x[1])[0]


def latest_data_collection_date_by_upload_time(db, cid: int, desired_date: str, pnom: float) -> str:
    """ Choose the latest ``dataCollectionDate`` for which ``splineCreationDate`` is prior to
    ``desired_date``. The ``desired_date`` must be a string with format YYYYMMDD."""
    date = int(desired_date)
    dates = set([(x['dataCollectionDate'][-1], x['splineCreationDate'])
                    for x in db.empiricalSpectra.find({'cid': cid, 'pNominal': pnom},
                                                      {'dataCollectionDate': 1,
                                                      'splineCreationDate': 1,
                                                      '_id': 0})])
    dates = sorted(dates, key=lambda x: int(x[1]))
    date_lambda = lambda x: int(x[1]) < date
    dates_prior = list(filter(date_lambda, dates))
    if not dates_prior:
        raise ValueError(f"No records found prior to {desired_date} for CID {cid}, with nominal pressure {pnom}")
    data_collection_date = dates_prior[-1][0]
    spline_creation_date = dates_prior[-1][1]
    return (data_collection_date, spline_creation_date)


def load_empirical_spectrum(db: 'SpectralDatabase', nu_left: float, nu_right: float,
                            e_compound_dict: Dict[str, Any]) -> Dict[str, Dict[Any, Any]]:
    """ Search some database records and reshape the document roughly into spectral arrays and
    additional metadata about said spectra """

    search_terms = get_search_terms(nu_left, nu_right, e_compound_dict)
    search_dict = {'$and': search_terms}
    info: Dict[Any, Any] = {}
    spectra: Dict[Any, Any] = {}
    if not db.empiricalSpectra.count_documents(search_dict) == 0:
        search_results = db.empiricalSpectra.find(search_dict)
        xtremeStart = extrema()
        xtremeEnd = extrema()
        for i, item in enumerate(search_results):
            itemDict = convertStrKeysToNumeric(item)
            xtremeStart.addData([item['nustart']])
            xtremeEnd.addData([item['nuend']])
            if i == 0:
                info = {}
                for k, v in itemDict.items():
                    if k != 'dataDict':
                        info[k] = v
                    else:
                        spectra = {}
                        for kd in v:
                            spectra[kd] = defaultdict(list)
            for kd, vd in itemDict['dataDict'].items():
                for ki, vi in vd.items():
                    if ki in ['Top', 'Pop']:
                        spectra[kd][ki].append(vi)
                    else:
                        spectra[kd][ki].extend(vi)
        info['nustart'] = xtremeStart.min
        info['nuend'] = xtremeEnd.max
    return {'infoDict': info, 'spectrumDict': spectra}


def load_update_dict_from_db(cid: int, nu_left: float, nu_right: float) -> Tuple:
    db = SpectralDatabase()
    search_terms = {"$and": [
                {'cid': cid},
                {'nu': {'$gte': nu_left}},
                {'nu': {'$lte': nu_right}}
            ]
        }
    search_results = db.peakOverlays.find(search_terms)
    update_dict = {}
    for item in search_results:
        U = convertStrKeysToNumeric(item)
        peak = U['ht']
        update_dict[peak] = U['updateDict']
    return update_dict


def get_search_terms(nu_left: float, nu_right: float, e_compound_dict: Dict[str, Union[float, str,
                                                                                    int]]):
    def nuInBin(nu: float):
        nuterms = []
        nuterms.append({'nustart': {'$lte': nu}})
        nuterms.append({'nuend': {'$gte': nu}})
        return {'$and': nuterms}

    def binInNurange(nu_left: float, nu_right: float):
        nuterms = []
        nuterms.append({'nustart': {'$lte': nu_right}})
        nuterms.append({'nustart': {'$gte': nu_left}})
        return {'$and': nuterms}

    cid = e_compound_dict['cid']
    dataCollectionDate = e_compound_dict['dataCollectionDate']
    # So not PEP8, following pattern here
    splineCreationDate = e_compound_dict['splineCreationDate']
    version = e_compound_dict['version']
    pnom = e_compound_dict['pNominal']
    allNUTerms = []
    allNUTerms.append(nuInBin(nu_left))
    allNUTerms.append(nuInBin(nu_right))
    allNUTerms.append(binInNurange(nu_left, nu_right))
    nuSearch = {'$or': allNUTerms}

    search_terms = []
    search_terms.append({'cid': cid})
    search_terms.append({'dataCollectionDate': dataCollectionDate})
    search_terms.append({'splineCreationDate': splineCreationDate})
    search_terms.append({'version': version})
    search_terms.append({'pNominal': pnom})
    search_terms.append(nuSearch)
    return search_terms


def convertStrKeysToNumeric(obj: Dict[Any, Any]) -> Dict[Any, Any]:
    if isinstance(obj, dict):
        newdict = {}
        for k, v in obj.items():
            if '_int_' in k:
                new_key = int(k[5:])
            elif isinstance(k, str):
                new_key = str(k)
            else:
                new_key = k
            new_val = convertStrKeysToNumeric(v)
            if new_key == 'ht':
                new_val = tuple(new_val)
            newdict[new_key] = new_val
        return newdict
    return obj


class extrema:
    def __init__(self):
        self.min = inf
        self.max = -1 * inf

    def addData(self, x):
        if min(x) <= self.min:
            self.min = min(x)
        if max(x) >= self.max:
            self.max = max(x)


@dataclass
class HTcollectionInfo():
    def __init__(self, s, e, name):
        self.s = int(s)
        self.e = int(e)
        self.name = name


def parseHTcollection(s):
    regexHTline = r'^W(\d+)_(\d+)$'
    match = re.match(regexHTline, s)
    collection_info = None
    if match:
        args = match.groups() + (s, )
        collection_info = HTcollectionInfo(*args)
    return collection_info


def findHTPeakCollections(db, verbose=False):
    htcols = []
    for c in db.list_collection_names():
        k = parseHTcollection(c)
        if k is not None:
            htcols.append(k)
    # LOGGER.debug(f'{len(htcols)} Hitran peak collections found')
    return htcols


def retrievePeaksByCID(db, cid, start, end):
    """ Retrieves a peak document from `db` filtering on cid, start, and end (wavenumbers) """
    terms = []
    terms.append({'cid': cid})
    terms.append({'nu': {'$gte': start}})
    terms.append({'nu': {'$lte': end}})
    search_dict = {"$and": terms}

    peaks = db.Lines.find(search_dict)
    return peaks


def retrieve_peak_by_nu_sw_cid(db: 'SpectralDatabase.MDB.db', nu: float, sw: float, cid: int):
    """ Retrieves a peak document that matches nu, sw, cid
    """
    terms = []
    terms.append({'nu': nu})
    terms.append({'sw': sw})
    terms.append({'cid': cid})
    query = {'$and': terms}

    try:
        peak = db.Lines.find(query).__next__()
    except StopIteration:
        raise ValueError(f'Wave number {nu} not found in spectral library')
    return peak


def retrieve_overlay_by_nu_sw_cid(db: 'SpectralDatabase.MDB.db', nu: float, sw: float, cid: int):
    """ Retrieves an overlay document that matches nu, sw, cid
    """
    terms = []
    terms.append({'nu': nu})
    terms.append({'sw': sw})
    terms.append({'cid': cid})
    query = {'$and': terms}

    collection_name = 'PeakOverlays'
    try:
        overlay_document = db[collection_name].find(query).__next__()
    except StopIteration:
        overlay_document = {}

    return overlay_document

def get_hitran_line_args(HTmol, peaks, line_model='galatry'):
    """ Turns a hitran molecule record, and a hitran peak record args that a HitranLine can
    consume. Performs a join.
    Yields from a generator because the `peaks` can be arbitralily long. In fact the `peaks`
    object here is a pymongo cursor-like object, which itself is a generator.
    """
    for hitran_record in peaks:
        nu = hitran_record['nu']
        e_lower = hitran_record['elower']
        mol_number = hitran_record['molec_id']
        sw = hitran_record['sw']
        n_air = hitran_record['n_air']
        cid = hitran_record['cid']
        gamma_air = hitran_record['gamma_air']
        gamma_self = hitran_record['gamma_self']
        delta_air = hitran_record['delta_air']

        molecule_record = HTmol.find_one({'M': hitran_record['molec_id'], 'I': hitran_record['local_iso_id']})
        mass = molecule_record['mass']
        abundance = molecule_record['abundance']
        iso_number = molecule_record['I']

        yield dict(nu=nu,
                   e_lower=e_lower,
                   mol_number=mol_number,
                   sw=sw,
                   n_air=n_air,
                   cid=cid,
                   gamma_air=gamma_air,
                   gamma_self=gamma_self,
                   delta_air=delta_air,
                   mass=mass,
                   abundance=abundance,
                   iso_number=iso_number,
                   model_type=line_model
                   )
