import xarray as xa
import time, traceback
import numpy as np

from .embedding import reductionManager
from functools import partial
from hyperclass.graph.flow import activationFlowManager
from umap.model import UMAP
from collections import OrderedDict
from typing import List, Tuple, Optional, Dict
from hyperclass.plot.point_cloud import PointCloud
from ..data.manager import dataManager
# from hyperclass.gui.tasks import taskRunner, Task

cfg_str = lambda x:  "-".join( [ str(i) for i in x ] )

class UMAPManager(object):

    UNDEF = -1
    INIT = 0
    NEW_DATA = 1
    PROCESSED = 2

    def __init__(self,  **kwargs ):
        self.point_cloud: PointCloud = PointCloud( )
        self._point_data = None
        self._gui = None
        self._current_event = None
        self.embedding_type = kwargs.pop('embedding_type', 'umap')
        self.conf = kwargs
        self._state = self.UNDEF
        self.learned_mapping: Optional[UMAP] = None
        self._mapper: Dict[ str, UMAP ] = {}
        self._current_mapper: UMAP = None
        self.update_signal.connect( self.gui_update )
        self.menu_actions = OrderedDict( Plots =  [ [ "Increase Point Sizes", 'Ctrl+}',  None, partial( self.update_point_sizes, True ) ],
                                                    [ "Decrease Point Sizes", 'Ctrl+{',  None, partial( self.update_point_sizes, False ) ] ] )

    def set_point_colors( self, **kwargs ):
        if self._gui is not None:
            self._gui.set_point_colors(**kwargs)

    @classmethod
    def newinit( cls, init_method: str ):
        event = dict( event='gui', type='newinit', method=init_method )
        taskRunner.submitEvent( event, EventMode.Foreground )

    def plotMarkers(self, **kwargs ):
        clear = kwargs.get( 'clear', False )
        if clear: self._gui.set_point_colors()
        self._gui.plotMarkers( **kwargs )
        self.update_signal.emit({})

    def undoMarkerPlot(self, **kwargs ):
#        color_data = np.full( shape=[nPoints], fill_value= 0 )
#        self._gui.set_point_colors( data = color_data )
#        self._gui.plotMarkers( **kwargs )
        self._gui.plotMarkers( reset=True )
        self.update_signal.emit({})

    def clear(self,**kwargs):
        keep_markers = kwargs.get('markers', 'discard') == "keep"
        activationFlowManager.clear()
        self._gui._clear_selection()
        if not keep_markers:
            self._gui.clear_markers()
            labelsManager.clearMarkers()
        self.update_signal.emit({})

    def processEvent( self, event: Dict ):
        super().processEvent(event)
        etype = event.get('type')
        eid = event.get('event')
        if dataEventHandler.isDataLoadEvent(event):
            self._point_data = dataEventHandler.getPointData( event, DataType.Embedding )
            self._state = self.INIT
            self.embedding()
        if eid == 'gui':
            if etype == 'keyPress':      self._gui.setKeyState( event )
            elif etype == 'keyRelease':  self._gui.releaseKeyState()
            else:
                if etype in [ 'clear', 'reload' ]:
                    self.clear( markers=event.get('markers','discard') )
                elif etype == 'undo':
                    self.undoMarkerPlot( **event )
                elif etype == 'spread':
                    labels: xa.Dataset = event.get('labels')
                    self._gui.set_point_colors( labels=labels['C'] )
                elif etype == 'distance':
                    labels: xa.Dataset = event.get('labels')
                    D = labels['D']
                    self._gui.color_by_metric( D )
                elif etype == 'reset':
                    self.clear()
                elif etype == 'embed':
                    self.embed( **event )
                elif etype == 'newinit':
                    self._state = self.INIT
                    if self._point_data is not None:
                        ndim = event.get('ndim', 3)
                        mapper = self.getMapper( self._point_data.attrs['dsid'], ndim )
                        mapper.clear_initialization()
                elif etype == 'reinit':
                    ndim = event.get('ndim',3)
                    mapper = self.getMapper( self._point_data.attrs['dsid'], ndim )
                    mapper.clear_embedding()
                    if self._state == self.INIT: self.embed()
                    self._gui.set_colormap(self.class_colors)
                    self._gui.update_plot( mapper.embedding )
                elif etype == 'plot':
                    embedded_data = event.get('value')
                    self._gui.set_colormap(self.class_colors)
                    self._gui.update_plot( embedded_data )
                self.update_signal.emit( event )
        elif eid == 'pick':
            etype = etype
            if etype in [ 'directory', "vtkpoint", "plot", 'reference', 'graph' ]:
                if self._current_mapper is not None:
                    try:
                        pids = [ pid for pid in event.get('pids',[]) if pid >= 0 ]
                        rspecs = event.get('rows', [])
                        for rspec in rspecs: pids.append( rspec.pid )
                        mark = event.get('mark',False)
                        classification = event.get('classification',-1)
                        cid = classification if ( classification > 0) else labelsManager.selectedClass
                        color = labelsManager.colors[cid]
                        labelsManager.addMarker( Marker( color, pids, cid ) )
                        self._gui.plotMarkers( reset = True )
                        self.update_signal.emit({})
                    except Exception as err:
                        print( f"Point selection error: {err}")
                        traceback.print_exc( 50 )

    @property
    def class_colors(self) -> Dict[str,List[float]]:
        return labelsManager.toDict( 1.0 )

    @property
    def class_labels(self) -> List[str]:
        return labelsManager.labels

    def embedding( self,  **kwargs ) -> Optional[xa.DataArray]:
        ndim = kwargs.get('ndim', dataManager.config.value("umap/dims", type=int) )
        mapper: UMAP = self.getMapper( self._point_data.attrs['dsid'], ndim )
        if mapper.embedding is not None:
            return self.wrap_embedding(self._point_data.coords[ self._point_data.dims[0] ], mapper.embedding )
        return self.embed( **kwargs )

    def wrap_embedding(self, ax_samples: xa.DataArray, embedding: np.ndarray, **kwargs )-> xa.DataArray:
        ax_model = np.arange( embedding.shape[1] )
        return xa.DataArray( embedding, dims=['samples','model'], coords=dict( samples=ax_samples, model=ax_model ) )

    def getMapper(self, dsid: str, ndim: int ) -> UMAP:
        mid = f"{ndim}-{dsid}"
        mapper = self._mapper.get( mid )
        if ( mapper is None ):
            n_neighbors = dataManager.config.value("umap/nneighbors", type=int)
            init = dataManager.config.value("umap/init", "random")
            target_weight = dataManager.config.value( "umap/target_weight", 0.5, type=float )
            parms = dict( n_neighbors=n_neighbors, init=init, target_weight=target_weight ); parms.update( **self.conf, n_components=ndim )
            mapper = UMAP(**parms)
            self._mapper[mid] = mapper
        self._current_mapper = mapper
        return mapper

    def iparm(self, key: str ):
        return int( dataManager.config.value(key) )

    def color_pointcloud( self, labels: xa.DataArray, **kwargs ):
        print( f"color_pointcloud: labels shape = {labels.shape}")
        self.point_cloud.set_point_colors( labels = labels.values, **kwargs )

    def clear_pointcloud(self):
        self.point_cloud.clear()

    def update_point_sizes(self, increase: bool  ):
        self.point_cloud.update_point_sizes( increase )

    def supervised(self, block: Block, labels: xa.DataArray, ndim: int, **kwargs) -> Tuple[Optional[xa.DataArray], Optional[xa.DataArray]]:
        from hyperclass.graph.flow import ActivationFlow
        flow = labelsManager.flow()
        if flow.nnd is None:
            event = dict( event="message", type="warning", title='Workflow Message', caption="Awaiting task completion", msg="The NN graph computation has not yet finished" )
            self.submitEvent( event, EventMode.Gui )
            return None, None
        self.learned_mapping: UMAP = self.getMapper( block.dsid, ndim )
        point_data: xa.DataArray = block.getPointData( **kwargs )
        nnd = ActivationFlow.getNNGraph( point_data, **kwargs )
        self.learned_mapping.embed(point_data.data, nnd, labels.values, **kwargs)
        coords = dict(samples=point_data.samples, model=np.arange(self.learned_mapping.embedding.shape[1]))
        return xa.DataArray(self.learned_mapping.embedding, dims=['samples', 'model'], coords=coords), labels

    def apply(self, block: Block, **kwargs ) -> Optional[xa.DataArray]:
        if (self.learned_mapping is None) or (self.learned_mapping.embedding is None):
            Task.taskNotAvailable( "Workflow violation", "Must learn a classication before it can be applied", **kwargs )
            return None
        point_data: xa.DataArray = block.getPointData( **kwargs )
        embedding: np.ndarray = self.learned_mapping.transform( point_data )
        return self.wrap_embedding( point_data.coords['samples'], embedding )

    # def computeMixingSpace(self, block: Block, labels: xa.DataArray = None, **kwargs) -> xa.DataArray:
    #     ndim = kwargs.get( "ndim", 3 )
    #     t0 = time.time()
    #     point_data: xa.DataArray = block.getPointData( **kwargs )
    #     t1 = time.time()
    #     print(f"Completed data prep in {(t1 - t0)} sec, Now fitting umap[{ndim}] with {point_data.shape[0]} samples")
    #     self.mixing_space.setPoints( point_data, labels )
    #     t2 = time.time()
    #     print(f"Completed computing  mixing space in {(t2 - t1)/60.0} min")

    def embed( self, **kwargs ) -> Optional[xa.DataArray]:
        flow = activationFlowManager.getActivationFlow( self._point_data )
        if flow.nnd is None:
            event = dict( event="message", type="warning", title='Workflow Message', caption="Awaiting task completion", msg="The NN graph computation has not yet finished" )
            self.submitEvent( event, EventMode.Gui )
            return None
        ndim = dataManager.config.value("umap/dims", type=int)
        init_method = dataManager.config.value("umap/init", "random")
        if self._state == self.INIT:
            kwargs['nepochs'] = 1
            self._state = self.NEW_DATA
        else:
            if 'nepochs' not in kwargs.keys(): kwargs['nepochs'] = dataManager.config.value("umap/nepochs", type=int)
            if 'alpha' not in kwargs.keys():   kwargs['alpha']   = dataManager.config.value("umap/alpha", type=float)
            self._state = self.PROCESSED
        t0 = time.time()
        mapper = self.getMapper( self._point_data.attrs['dsid'], ndim )
        mapper.flow = flow
        t1 = time.time()
        labels_data: np.ndarray = labelsManager.labels_data().values
        if self._point_data.shape[1] <= ndim:
            mapper.set_embedding( self._point_data )
        else:
            try:

                if mapper.embedding is not None:
                    mapper.clear_initialization()
                    mapper.init = mapper.embedding
                elif init_method == "autoencoder":
                    mapper.init = reductionManager.reduce( self._point_data.data, init_method, ndim )
                else:
                    mapper.init = init_method
                print( f"Completed data prep in {(t1 - t0)} sec, Now fitting umap[{ndim}] with {self._point_data.shape[0]} samples and {np.count_nonzero(labels_data)} labels")

                mapper.embed(self._point_data.data, flow.nnd, labels_data, **kwargs)
            except Exception as err:
                print( f" Embedding error: {err}")
                traceback.print_exc(50)
                return None

        t2 = time.time()
        print(f"Completed umap fitting in {(t2 - t1)/60.0} min, embedding shape = { mapper.embedding.shape}" )
        return self.wrap_embedding( self._point_data.coords['samples'], mapper.embedding )

    @property
    def conf_keys(self) -> List[str]:
        key_list = list(self.conf.keys())
        key_list.sort()
        return key_list

    # def plot_markers_transform(self, block: Block, ycoords: List[float], xcoords: List[float], colors: List[List[float]], **kwargs ):
    #     point_data = block.getSelectedPointData( ycoords, xcoords )
    #     mapper = self.getMapper( block, 3 )
    #     if hasattr(mapper, 'embedding_'):
    #         transformed_data: np.ndarray = mapper.transform(point_data)
    #         self.point_cloud.plotMarkers( transformed_data.tolist(), colors )

    def plot_markers(self, block: Block, ycoords: List[float], xcoords: List[float], colors: List[List[float]], **kwargs ):
        pindices: np.ndarray  = block.multi_coords2pindex( ycoords, xcoords )
        mapper = self.getMapper( block.dsid, 3 )
        if mapper.embedding is not None:
            transformed_data: np.ndarray = mapper.embedding[ pindices]
            self.point_cloud.plotMarkers( transformed_data.tolist(), colors, **kwargs )
            self.update_signal.emit({})

    def reset_markers(self):
        self.point_cloud.initMarkers( )

    @pyqtSlot(dict)
    def gui_update(self, kwargs: Dict ):
        self._gui.gui_update( **kwargs  )

    def transform( self, block: Block, **kwargs ) -> Dict[str,xa.DataArray]:
        t0 = time.time()
        ndim = kwargs.get( 'ndim', 3 )
        mapper = self.getMapper( block.dsid, ndim )
        point_data: xa.DataArray = block.getPointData()
        transformed_data: np.ndarray = mapper.transform(point_data)
        t1 = time.time()
        print(f"Completed transform in {(t1 - t0)} sec for {point_data.shape[0]} samples")
        block_model = xa.DataArray( transformed_data, dims=['samples', 'model'], name=block.tile.data.name, attrs=block.tile.data.attrs,
                                    coords=dict( samples=point_data.coords['samples'], model=np.arange(0,transformed_data.shape[1]) ) )

        transposed_raster = block.data.stack(samples=block.data.dims[-2:]).transpose()
        new_raster = block_model.reindex(samples=transposed_raster.samples).unstack()
        new_raster.attrs['long_name'] = [ f"d-{i}" for i in range( new_raster.shape[0] ) ]
        return   dict( raster=new_raster, points=block_model )


umapManager = UMAPManager()