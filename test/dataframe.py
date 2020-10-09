from typing import List, Union, Tuple, Optional, Dict, Callable
import time
import xarray as xa
import pandas as pd
from astrolab.data.manager import DataManager
t0 = time.time()
nrows = 10
table_cols = [ "target_names", "obsids" ]
project_data: xa.Dataset = DataManager.instance().loadCurrentProject()
dropped_vars = [ vname for vname in project_data.data_vars if vname not in table_cols ]
table_data = { tcol: project_data[tcol].values[:nrows] for tcol in table_cols }

df: pd.DataFrame = pd.DataFrame( table_data, dtype='U', index=pd.Int64Index( range(nrows-1,-1,-1), name="Index" ) )
df.insert( len(table_cols), "Class", 0, True )
print( f"Created dataFrame  in {time.time()-t0} sec.")

df.loc[ [5,7], 'Class'] = 10

print( df )






