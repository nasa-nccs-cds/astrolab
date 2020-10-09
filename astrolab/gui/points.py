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
        self._embedding: np.ndarray = None
        self._marker_points: List[np.ndarray] = [ self.empty_pointset for ic in range( LabelsManager.instance().nLabels ) ]

    @property
    def empty_pointset(self) -> np.ndarray:
        return np.empty(shape=[0, 3], dtype=np.float)

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
        points = kwargs.get( 'points', self._embedding )
        new_point_sets = [ points ] + self._marker_points[::-1]
#        print( f"  ***** update_plot- new_point_set shapes = {[ps.shape for ps in new_point_sets]}" )
        self._gui.point_sets = new_point_sets

    def on_selection(self, selection_event: Dict ):
        selection = selection_event['pids']
        self.update_markers(selection)

    def update_markers(self, pids: List[int]):
        self._marker_points[0] = self._embedding[ pids, : ]
        print( f"  ***** POINTS- mark_points[0], #pids = {len(pids)}")
        self.update_plot()

    def mark_points(self, pids: np.ndarray, cid: int = -1, update=False):
        from astrolab.gui.control import ControlPanel
        from astrolab.model.labels import LabelsManager
        ctrl: ControlPanel = ControlPanel.instance()
        icid: int = cid if cid > 0 else ctrl.current_cid
        marked_points: np.ndarray = self._embedding[ pids, : ]
        print( f"  ***** POINTS- mark_points[{icid}], #pids = {len(pids)}, #points = {marked_points.shape[0]}")
        self._marker_points[ 0 ] = self.empty_pointset
        self._marker_points[ icid ] = np.concatenate(  [ self._marker_points[ icid ], marked_points ] )
        LabelsManager.instance().addMarker( Marker( pids, icid ) )
        if update: self.update_plot()
        return ctrl.current_cid

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
        return [ self._embedding ] + self._marker_points[::-1]

    def gui(self, **kwargs ):
        if self._gui is None:
            self.init_data()
            ptcolors = [ [1.0, 1.0, 1.0, 1.0], ] + LabelsManager.instance().colors[::-1]
            ptsizes = [1] + [8]*LabelsManager.instance().nLabels
            self._gui = view( point_sets = self.point_sets, point_set_sizes=ptsizes, point_set_colors=ptcolors, background=[0,0,0] )
            self._gui.layout = { 'width': 'auto', 'flex': '1 1 auto' }
        return self._gui
