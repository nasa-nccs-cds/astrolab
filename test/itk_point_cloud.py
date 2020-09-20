import numpy as np
from itkwidgets import view
from astrolab.data.manager import dataManager
from astrolab.reduction.embedding import reductionManager
import xarray as xa

config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),
    umap = dict( dims=3, nepochs=100, alpha=0.25, nneighbors=8 ),

)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()

project_dataset = dataManager.loadCurrentProject()
reduced_data: xa.DataArray = project_dataset.reduction
reduced_data.attrs['dsid'] = 'swift'

embedding = reductionManager.umap_embedding( reduced_data )

view( point_sets=[embedding.data] )