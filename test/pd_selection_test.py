import qgrid
from typing import List, Union, Tuple, Optional, Dict, Callable
from IPython.core.debugger import set_trace
import time, logging
from functools import partial
import xarray as xa
import numpy as np
import pandas as pd
from astrolab.data.manager import dataManager


table_cols = [ "target_names", "obsids" ]
config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),
)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()


project_data: xa.Dataset = dataManager.loadCurrentProject()
catalog = {tcol: project_data[tcol].values for tcol in table_cols}
df: pd.DataFrame = pd.DataFrame(catalog, dtype='U')
cols = list(catalog.keys())

search_str = "EX"
select_all = True
cname = "target_names"
np_coldata = df[cname].values.astype('U')
mask = np.char.startswith( np_coldata, search_str )
selection = df.index[ mask ].values
print("")
#        if not select_all: selection = selection[:1]

