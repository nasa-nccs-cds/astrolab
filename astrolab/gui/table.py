import qgrid
from typing import List, Union, Tuple, Optional, Dict, Callable
from IPython.core.debugger import set_trace
from functools import partial
import xarray as xa
import numpy as np
import pandas as pd
from astrolab.data.manager import dataManager
import ipywidgets as widgets

class TableManager(object):

    def __init__(self):
        qgrid.on('All', self.handle_table_event )
        self._wGui: widgets.VBox = None
        self._classes: List[str] = None
        self._dataFrame: pd.DataFrame = None
        self._cols: List[str] = None
        self._select_all: widgets.Checkbox = None
        self._tables: List[qgrid.QgridWidget] = []
        self.wTablesWidget: widgets.Tab = None
        self._current_column_index: int = 0
        self._current_table: qgrid.QgridWidget = None
        self._select_all = False

    def init(self, **kwargs):
        nclass = kwargs.get('nclass',5)
        self._classes = kwargs.get('classes', [ f'class-{iclass}' for iclass in range(nclass)] )
        catalog: Dict[str,np.ndarray] = kwargs.get( 'catalog', None )
        if catalog is None:
            project_data: xa.Dataset = dataManager.loadCurrentProject()
            table_cols = kwargs.get( 'cols', project_data.variables.keys() )
            catalog = { tcol: project_data[tcol].values for tcol in table_cols }
        self._dataFrame: pd.DataFrame = pd.DataFrame(catalog, dtype='U')
        self._cols = list(catalog.keys())

    def handle_table_event(self, event, widget):
        self._current_table = widget
        ename = event['name']
        if( ename == 'sort_changed'):
            self._current_column_index = self._cols.index( event['new']['column'] )
            self.update_finder()
        elif (ename == 'selection_changed'):
            print(f" selection_change: {event}")

    def _createTable( self, tab_index: int ) -> qgrid.QgridWidget:
        assert self._dataFrame is not None, " TableManager has not been initialized "
        col_opts = {'editable': False}
        grid_opts = {'editable': False}
        if tab_index == 0:
            wTable = qgrid.show_grid( self._dataFrame, column_options=col_opts, grid_options=grid_opts, show_toolbar=False )
        else:
            empty_catalog = {col: np.empty( [0], 'U' ) for col in self._cols}
            dFrame: pd.DataFrame = pd.DataFrame(empty_catalog, dtype='U')
            wTable = qgrid.show_grid( dFrame, column_options=col_opts, grid_options=grid_opts, show_toolbar=False )
        return wTable

    def _createGui( self ) -> widgets.VBox:
        wSelectionPanel = self._createSelectionPanel()
        self.wTablesWidget = self._createTableTabs()
        return widgets.VBox([wSelectionPanel, self.wTablesWidget])

    def _createSelectionPanel( self ) -> widgets.HBox:
        unclass = 'unclassified'
        self._wFind = widgets.Text( value='', placeholder='Find items', description='Find:', disabled=False, continuous_update = False )
        wSelectAll = widgets.Checkbox(value=False, description='Select all', disabled=False, indent=False)
        self._wFind.observe( self.process_find, 'value' )
        wSelectAll.observe(self.process_select_all, 'value')
        wSelectedClass = widgets.Dropdown( options=[unclass] + self._classes, value=unclass, description='Class:' )
        return widgets.HBox( [ self._wFind, wSelectAll, wSelectedClass ], justify_content="space-around", flex_wrap="wrap" )

    def process_find(self, event ):
        df: pd.DataFrame = self._current_table.get_changed_df()
        cname = self._cols[ self._current_column_index ]
        np_coldata = df[cname].values.astype('U')
        mask = np.char.startswith(np_coldata, event['new'] )
        selection = df.index[mask].values
        if not self._select_all: selection = selection[:1]
        print( f" process_find, select_all={self._select_all}, event = {event}, selection={selection}")
        self._current_table.change_selection( selection )

    def update_finder(self) -> str:
        cval = self._wFind.value
        self._wFind.value = cval + "$@#"
        self._wFind.value = cval
        return cval

    def process_select_all(self, event):
        self.update_finder()
        self._select_all = event['new']

        print( f"process_select_all: {event}, self._select_all = {self._select_all}" )

    def _createTableTabs(self) -> widgets.Tab:
        wTab = widgets.Tab()
        self._current_table = self._createTable( 0 )
        self._tables.append( self._current_table )
        wTab.set_title( 0, 'Catalog')
        for iC, ctitle in enumerate(self._classes):
            self._tables.append(  self._createTable( iC+1 ) )
            wTab.set_title( iC+1, ctitle )
        wTab.children = self._tables
        return wTab

    def gui(self) -> widgets.VBox:
        if self._wGui is None:
            self._wGui = self._createGui()
        return self._wGui


tableManager = TableManager()

