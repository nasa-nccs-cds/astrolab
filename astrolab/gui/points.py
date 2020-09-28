import numpy as np
from astrolab.data.manager import dataManager
from astrolab.reduction.embedding import reductionManager
from itkwidgets import view
import xarray as xa

config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),
    umap = dict( dims=3, nepochs=100, alpha=0.25, nneighbors=8 ),
)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()

class PointCloudManager:

    def __init__(self):
        self._gui = None

    def init_data( self ):
        project_dataset = dataManager.loadCurrentProject()
        reduced_data: xa.DataArray = project_dataset.reduction
        reduced_data.attrs['dsid'] = 'swift'
        self._embedding = reductionManager.umap_embedding(reduced_data)

    def configure(self, **kwargs ):
        width = kwargs.get( 'width', None )
        height = kwargs.get( 'height', None )
        if width is not None:
            self._gui.layout.width = width
            self._gui.layout.max_width = width
            self._gui.layout.min_width = width
        if height is not None:
            self._gui.layout.height = height
            self._gui.layout.max_height = height
            self._gui.layout.min_height = height

    def gui(self, **kwargs ):
        if self._gui is None:
            self.init_data()
            self._gui = view( point_sets = [ self._embedding.values ] )
#            self.configure( **kwargs )
            self._gui.layout = { 'width': '100%', 'height': '100%', 'max_height': "2000px", 'max_width': "2000px" }
        return self._gui

pointCloudManager = PointCloudManager()