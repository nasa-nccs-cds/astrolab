import ipysheet
import numpy as np
from astrolab.data.manager import dataManager

config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),

)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()

project_data = dataManager.loadCurrentProject()

target_names: np.ndarray = project_data.target_names.values
obsids: np.ndarray  = project_data.obsids.values
nrows = target_names.shape[0]

sheet = ipysheet.sheet(rows=nrows, columns=3)

for idx in range( nrows ):
    cell1 = ipysheet.cell( idx, 0, target_names[idx] )
    cell2 = ipysheet.cell( idx, 1, obsids[idx] )
    cell3 = ipysheet.cell( idx, 2, idx )

sheet