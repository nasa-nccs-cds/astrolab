import time, numpy as np
from astrolab.data.manager import dataManager
from astrolab.reduction.embedding import reductionManager
from typing import List, Union, Tuple, Optional, Dict, Callable
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

    def init_data( self, **kwargs  ):
        project_dataset = dataManager.loadCurrentProject()
        reduced_data: xa.DataArray = project_dataset.reduction
        reduced_data.attrs['dsid'] = 'swift'
        self._embedding = reductionManager.umap_init( reduced_data, **kwargs  )
        self._marker_points = np.empty( shape=[0,3], dtype=np.float )

    def reembed(self, **kwargs ):
        t0 = time.time()
        self._embedding = reductionManager.umap_embedding( **kwargs )
        self.update_plot()
        print(f"PointCloudManager: completed embed in {time.time()-t0} sec")

    def update_plot( self, **kwargs ):
        points = kwargs.get( 'points', self._embedding.values )
        markers = kwargs.get('markers', self._marker_points )
        self._gui.point_sets = [ points, markers ]

    def on_selection(self, selection_event: Dict ):
        print( f" POINTS.on_selection: {selection_event}" )
        selection = selection_event['new']
        self.update_markers(selection)

    def update_markers(self, pids: List[int]):
        self._marker_points = self._embedding[ pids, : ]
        self.update_plot()

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
            self._gui = view( point_sets = [ self._embedding.values, self._marker_points ], point_set_sizes=[1,8], point_set_colors=[[1,1,1],[1,0.5,0]], background=[0,0,0] )
            self._gui.layout = { 'width': 'auto', 'flex': '1 1 auto' }
        return self._gui

pointCloudManager = PointCloudManager()