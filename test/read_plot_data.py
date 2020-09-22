from typing import List, Union, Tuple, Optional, Dict, Callable
import time, logging
import xarray as xa
import numpy as np
from astrolab.data.manager import dataManager
t0 = time.time()
logger = logging.getLogger()

config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),
)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()

project_data: xa.Dataset = dataManager.loadCurrentProject()
plotx: np.ndarray = project_data["plot-x"].values
ploty: np.ndarray = project_data["plot-y"].values

index = 0
x = plotx
y = ploty[index]
y_range = ( y.min(), y.max() )

print( x.shape )
print( y.shape )