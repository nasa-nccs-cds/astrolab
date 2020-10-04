import time, numpy as np
from astrolab.data.manager import DataManager
from astrolab.reduction.embedding import ReductionManager
from typing import List, Union, Tuple, Optional, Dict, Callable
from itkwidgets import view
import xarray as xa
import traitlets.config as tlc
from astrolab.model.base import AstroSingleton, Marker
from astrolab.model.labels import LabelsManager

class PointCloudManager(tlc.SingletonConfigurable,AstroSingleton):

    def __init__(self, **kwargs):
        super(PointCloudManager, self).__init__(**kwargs)
        self._gui = None
        self._marker_points = { ic: np.empty( shape=[0,3], dtype=np.float ) for ic in range( LabelsManager.instance().nLabels ) }


    def init_data( self, **kwargs  ):
        project_dataset = DataManager.instance().loadCurrentProject()
        reduced_data: xa.DataArray = project_dataset.reduction
        reduced_data.attrs['dsid'] = 'swift'
        self._embedding = ReductionManager.instance().umap_init( reduced_data, **kwargs  )

    def reembed(self, **kwargs ):
        t0 = time.time()
        self._embedding = ReductionManager.instance().umap_embedding( **kwargs )
        self.update_plot()
        print(f"PointCloudManager: completed embed in {time.time()-t0} sec")

    def update_plot( self, **kwargs ):
        points = kwargs.get( 'points', self._embedding.values )
        new_point_sets = [ points ] + list( self._marker_points.values() )
        self._gui.point_sets = new_point_sets

    def on_selection(self, selection_event: Dict ):
        print( f" POINTS.on_selection: {selection_event}" )
        selection = selection_event['new']
        self.update_markers(selection)

    def update_markers(self, pids: List[int]):
        self._marker_points[0] = self._embedding[ pids, : ]
        self.update_plot()

    def mark_points(self, pids: List[int] ):
        from astrolab.gui.control import ControlPanel
        from astrolab.model.labels import LabelsManager
        ctrl = ControlPanel.instance()
        print( f"Marked[{ctrl.current_cid}]: {pids}")
        self._marker_points[ ctrl.current_cid ] = self._embedding[ pids ]
        LabelsManager.instance().addMarker( Marker( pids, ctrl.current_class ) )
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

    @property
    def point_sets(self):
        ps = [ self._embedding.values ] + list( self._marker_points.values() )
        print( ps )
        return ps

    def gui(self, **kwargs ):
        if self._gui is None:
            self.init_data()
            colors = [ [1.0, 1.0, 1.0, 1.0], ] + LabelsManager.instance().colors
            self._gui = view( point_sets = self.point_sets, point_set_sizes=[1,8], point_set_colors=colors, background=[0,0,0] )
            self._gui.layout = { 'width': 'auto', 'flex': '1 1 auto' }
        return self._gui
