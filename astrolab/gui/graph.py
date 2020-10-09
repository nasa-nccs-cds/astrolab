from bokeh.plotting import figure
from bokeh.io import output_notebook
import jupyter_bokeh as jbk
import ipywidgets as ip
from typing import List, Union, Tuple, Optional, Dict, Callable
import xarray as xa
import numpy as np
from astrolab.data.manager import DataManager
import ipywidgets as widgets
import traitlets.config as tlc
from astrolab.model.base import AstroSingleton

class JbkGraph:

    def __init__( self, **kwargs ):
        self.init_data(**kwargs)
        self._item_index = 0
        self.fig = figure( title=self.title, height=300, width=1000,  y_range=[self.y.min(),self.y.max()], background_fill_color='#efefef' )
        self._r = self.fig.line( self.x, self.y, color="#8888cc", line_width=1.5, alpha=0.8)
        self._model = jbk.BokehModel( self.fig, layout = ip.Layout( width= 'auto', height= 'auto' ) )
        print( f"BokehModel: {self._model.keys}" )

    def gui(self):
        self.plot()
        return self._model

    @classmethod
    def init_data(cls, **kwargs ):
        if not hasattr(cls, '_x'):
            project_data: xa.Dataset = DataManager.instance().loadCurrentProject()
            cls._x: np.ndarray = project_data["plot-x"].values
            cls._ploty: np.ndarray = project_data["plot-y"].values
            cls._mdata: List[np.ndarray] = [ project_data[mdv].values for mdv in kwargs.get("mdata", []) ]

    def select_item(self, index: int ):
        self._item_index = index

    def plot(self):
        x, y = self.x, self.y
        self.fig.title.text = self.title
        self._r.data_source.data['y'] =  y
        self.fig.y_range.update( start=y.min(), end=y.max() )

    @property
    def x(self) -> np.ndarray:
        return self._x

    @property
    def y(self) -> np.ndarray:
        return self._ploty[self._item_index]

    @property
    def title(self ) -> str:
        return ' '.join( [ str(mdarray[self._item_index]) for mdarray in self._mdata ] )

class GraphManager(tlc.SingletonConfigurable,AstroSingleton):

    def __init__( self, **kwargs ):
        super(GraphManager, self).__init__( **kwargs )
        output_notebook()
        self._wGui: widgets.Tab() = None
        self._graphs: List[JbkGraph] = []
        self._ngraphs = kwargs.get( 'ngraphs', 8)

    def gui(self, **kwargs ) -> widgets.Tab():
        if self._wGui is None:
            self._wGui = self._createGui( **kwargs )
        return self._wGui

    def current_graph(self) -> JbkGraph:
        return self._graphs[ self._wGui.selected_index ]

    def plot_graph( self, item_index: int ):
        current_graph: JbkGraph = self.current_graph()
        current_graph.select_item( item_index )
        current_graph.plot()

    def _createGui( self, **kwargs ) -> widgets.Tab():
        wTab = widgets.Tab( layout = ip.Layout( width='auto', flex='0 0 350px' ) )
        self._graphs = [ JbkGraph( **kwargs ) for iG in range(self._ngraphs) ]
        wTab.children = [ g.gui() for g in self._graphs ]
        for iG in range(self._ngraphs): wTab.set_title(iG, str(iG))
        return wTab

    def on_selection(self, selection_event: Dict ):
        selection = selection_event['pids']
        if len( selection ) > 0:
            print(f" GRAPH.on_selection: nitems = {len(selection)}, pid={selection[0]}")
            self.plot_graph( selection[0] )