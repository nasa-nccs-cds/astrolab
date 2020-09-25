from typing import List, Union, Tuple, Optional, Dict, Callable
import time
import xarray as xa
import pandas as pd
from astrolab.data.manager import dataManager
t0 = time.time()

table_cols = [ "target_names", "obsids" ]
config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),
)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()

project_data: xa.Dataset = dataManager.loadCurrentProject()
dropped_vars = [ vname for vname in project_data.data_vars if vname not in table_cols ]
table_data = { tcol: project_data[tcol].values for tcol in table_cols }

dataFrame: pd.DataFrame = pd.DataFrame( table_data, dtype='U' )
print( f"Created dataFrame  in {time.time()-t0} sec.")
dataFrame.info()





