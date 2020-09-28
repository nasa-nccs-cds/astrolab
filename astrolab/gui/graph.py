from bokeh.plotting import figure
from bokeh.io import output_notebook
import bokeh.models.widgets as bk
import jupyter_bokeh as jbk
import ipywidgets as ip
from typing import List, Union, Tuple, Optional, Dict, Callable
import time
import xarray as xa
import numpy as np
import pandas as pd
from astrolab.data.manager import dataManager
import ipywidgets as widgets
from traitlets import traitlets

class JbkGraph:

    def __init__( self, **kwargs ):
        self.init_data(**kwargs)
        self._item_index = 0
        self.fig = figure( title=self.title, plot_height=300, y_range=[self.y.min(),self.y.max()], background_fill_color='#efefef' )
        self._r = self.fig.line( self.x, self.y, color="#8888cc", line_width=1.5, alpha=0.8)
        self._model = jbk.BokehModel(self.fig)
        print( f"BokehModel: {self._model.keys}" )

    def gui(self):
        self.plot()
        return self._model

    @classmethod
    def init_data(cls, **kwargs ):
        if not hasattr(cls, '_x'):
            project_data: xa.Dataset = dataManager.loadCurrentProject()
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
        self._model.layout = {'width': '100%', 'max_width': "2000px"}

    @property
    def x(self) -> np.ndarray:
        return self._x

    @property
    def y(self) -> np.ndarray:
        return self._ploty[self._item_index]

    @property
    def title(self ) -> str:
        return ' '.join( [ str(mdarray[self._item_index]) for mdarray in self._mdata ] )

class GraphManager:

    def __init__( self, **kwargs ):
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
        wTab = widgets.Tab()
        self._graphs = [ JbkGraph( **kwargs ) for iG in range(self._ngraphs) ]
        wTab.children = [ g.gui() for g in self._graphs ]
        for iG in range(self._ngraphs): wTab.set_title(iG, str(iG))
        return wTab

    def on_selection(self, selection_event: Dict ):
        print( f" GRAPH.on_selection: {selection_event}" )
        selection = selection_event['new']
        self.plot_graph( selection[0] )


graphManager = GraphManager()