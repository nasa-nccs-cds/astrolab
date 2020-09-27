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

    def __init__(self):
        self.init_data()
        self._item_index = 0
        self.fig = figure( background_fill_color='#efefef')   # plot_height=300, plot_width=600,
        self.model = jbk.BokehModel(self.fig)
        self._r = None

    @classmethod
    def init_data(cls):
        try:   test = cls._x
        except NameError:
            project_data: xa.Dataset = dataManager.loadCurrentProject()
            cls._x: np.ndarray = project_data["plot-x"].values
            cls._ploty: np.ndarray = project_data["plot-y"].values
            cls._target_names = project_data.target_names.values
            cls._obsids = project_data.obsids.values

    def select_item(self, index: int ):
        self._item_index = index

    def plot(self):
        x, y = self.x, self.y
        self.fig.y_range.update( start=y.min(), end=y.max() )
        self.fig.title.text = self.title
        if self._r is None:     self._r = self.fig.line( x, y, color="#8888cc", line_width=1.5, alpha=0.8)
        else:                   self._r.data_source.data['y'] =  y

    @property
    def x(self) -> np.ndarray:
        return self._x

    @property
    def y(self) -> np.ndarray:
        return self._ploty[self._item_index]

    @property
    def title(self ) -> str:
        return f"{self._target_names[ self._item_index ]} ({self._obsids[ self._item_index ]})"

class GraphManager:

    def __init__( self, **kwargs ):
        self._wGui: widgets.Tab() = None
        self._graphs: List[JbkGraph] = []
        self._ngraphs = kwargs.get( 'ngraphs', 8)

    def gui(self) -> widgets.Tab():
        if self._wGui is None:
            self._wGui = self._createGui()
        return self._wGui

    def current_graph(self) -> JbkGraph:
        return self._graphs[ self._wGui.selected_index ]

    def plot_graph( self, item_index: int ):
        current_graph: JbkGraph = self.current_graph()
        current_graph.select_item( item_index )
        current_graph.plot()

    def _createGui(self) -> widgets.Tab():
        wTab = widgets.Tab()
        for iG in range(self._ngraphs):
            self._graphs.append( JbkGraph() )
            wTab.set_title( iG, str(iG) )
        wTab.children = self._graphs
        return wTab


graphManager = GraphManager()