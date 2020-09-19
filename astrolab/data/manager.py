import numpy as np
from typing import List, Union, Tuple, Optional, Dict
import os, math, pickle
import xarray as xa
from astrolab.config.settings import SettingsManager

class DataManager(SettingsManager):

    def __init__( self, **kwargs ):
        SettingsManager.__init__(  self, **kwargs )

    def getInputFileData(self, input_file_id: str, subsample: int = 1, dims: Tuple[int] = None ):
        data_dir = self.config.get(f"data").get("dir")
        input_file_path = os.path.join( data_dir, f"{input_file_id}.pkl")
        try:
            if os.path.isfile(input_file_path):
                print(f"Reading unstructured {input_file_id} data from file {input_file_path}")
                with open(input_file_path, 'rb') as f:
                    result = pickle.load(f)
                    if   isinstance( result, np.ndarray ):
                        if dims is not None and (result.shape[0] == dims[1]) and result.ndim == 1: return result
                        return result[::subsample]
                    elif isinstance( result, list ):
                        if dims is not None and ( len(result) == dims[1] ): return result
                        subsampled = [ result[i] for i in range( 0, len(result), subsample ) ]
                        if isinstance( result[0], np.ndarray ):  return np.vstack( subsampled )
                        else:                                    return np.array( subsampled )
            else:
                print( f"Error, the input path '{input_file_path}' is not a file.")
        except Exception as err:
            print(f" Can't read data[{input_file_id}] file {input_file_path}: {err}")

    def loadDataset( self, dsid: str, *args, **kwargs ) -> xa.Dataset:
        data_file = os.path.join( self.datasetDir, dsid + ".nc" )
        dataset: xa.Dataset = xa.open_dataset( data_file )
        print( f"Opened Dataset {dsid} from file {data_file}")
        dataset.attrs['dsid'] = dsid
        dataset.attrs['type'] = 'spectra'
        return dataset

    def loadCurrentProject(self):
        reduce_method = dataManager.config.get("reduce").get("method")
        reduce_dims = dataManager.config.get("reduce").get("dims")
        reduce_subsample = dataManager.config.get("reduce").get("subsample")
        projId = f"{reduce_method}-{reduce_dims}-ss{reduce_subsample}"
        return self.loadDataset( projId )

    @property
    def datasetDir(self):
        dsdir = os.path.join( dataManager.config.get('data').get('cache'), dataManager.project_name )
        os.makedirs( dsdir, exist_ok=True )
        return dsdir

dataManager = DataManager()