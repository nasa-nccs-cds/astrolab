import numpy as np
from typing import List, Union, Tuple, Optional, Dict
import os, math, pickle
import xarray as xa
import traitlets as tl
import traitlets.config as tlc
from astrolab.model.base import AstroSingleton

class DataManager(tlc.SingletonConfigurable,AstroSingleton):
    reduce_method = tl.Unicode("Autoencoder").tag(config=True)
    cache_dir = tl.Unicode("~/Development/Cache").tag(config=True)
    data_dir = tl.Unicode("~/Development/Cache").tag(config=True)
    project_name = tl.Unicode("astrolab").tag(config=True)
    model_dims = tl.Int(16).tag(config=True)
    subsample = tl.Int( 5 ).tag(config=True)

    def __init__(self, **kwargs):
        super(DataManager, self).__init__(**kwargs)

    def getInputFileData(self, input_file_id: str, subsample: int = 1, dims: Tuple[int] = None ):
        input_file_path = os.path.join( self.data_dir, f"{input_file_id}.pkl")
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

    def loadCurrentProject(self) -> xa.Dataset:

        projId = f"{self.reduce_method}-{self.model_dims}-ss{self.subsample}"
        return self.loadDataset( projId )

    @property
    def datasetDir(self):
        dsdir = os.path.join( self.cache_dir, self.project_name )
        os.makedirs( dsdir, exist_ok=True )
        return dsdir