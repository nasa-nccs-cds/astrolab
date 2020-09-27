import qgrid, logging
from typing import List, Union, Tuple, Optional, Dict, Callable
from IPython.core.debugger import set_trace
from functools import partial
import xarray as xa
import numpy as np
import pandas as pd
from astrolab.gui.widgets import ToggleButton
from astrolab.data.manager import dataManager
import ipywidgets as widgets
from traitlets import traitlets

class TableManager(object):

    def __init__(self):
        self._wGui: widgets.VBox = None
        self._classes: List[str] = None
        self._dataFrame: pd.DataFrame = None
        self._cols: List[str] = None
        self._tables: List[qgrid.QgridWidget] = []
        self._wTablesWidget: widgets.Tab = None
        self._current_column_index: int = 0
        self._current_table: qgrid.QgridWidget = None
        self._current_selection: List[int] = []
        self._selection_listeners: List[Callable[[Dict],None]] = [ self._internal_listener ]
        self._search_widgets = None
        self._match_options = {}

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

    def add_selection_listerner( self, listener: Callable[[Dict],None] ):
        self._selection_listeners.append( listener )

    def _handle_table_event(self, event, widget):
        self._current_table = widget
        ename = event['name']
        print( f"table_event: {event}")
        self.logger.info( f"table_event: {event}" )

        if( ename == 'sort_changed'):
            self._current_column_index = self._cols.index( event['new']['column'] )
            self._clear_selection()
        elif (ename == 'selection_changed'):
            itab_index = self._tables.index( widget )
            cname = self._classes[ itab_index ]
            selection_event = dict( classname=cname, **event )
            for listener in self._selection_listeners: listener( selection_event )

    def _internal_listener(self, selection_event: Dict ):
        print(f" selection_change: {selection_event}")

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
        wTable.on( traitlets.All, self._handle_table_event )
        return wTable

    def _createGui( self ) -> widgets.VBox:
        wSelectionPanel = self._createSelectionPanel()
        self._wTablesWidget = self._createTableTabs()
        return widgets.VBox([wSelectionPanel, self._wTablesWidget])

    def _createSelectionPanel( self ) -> widgets.HBox:
        unclass = 'unclassified'
        self._wFind = widgets.Text( value='', placeholder='Find items', description='Find:', disabled=False, continuous_update = False )
        self._wFind.observe(self._process_find, 'value')
        wFindOptions = self._createFindOptionButtons()
        wSelectedClass = widgets.Dropdown( options=[unclass] + self._classes, value=unclass, description='Class:' )
        return widgets.HBox( [ self._wFind, wFindOptions, wSelectedClass ], justify_content="space-around", flex_wrap="wrap" )

    def _createFindOptionButtons(self):
        if self._search_widgets is None:
            self._search_widgets = dict(
                find_select=     ToggleButton( [ 'search-location', 'th-list'], ['find','select'], [ 'find first', 'select all'] ),
                case_sensitive=  ToggleButton( ['font', 'asterisk'], ['true', 'false'],['case sensitive', 'case insensitive']),
                match=           ToggleButton( ['caret-square-left', 'caret-square-right', 'caret-square-down'], ['begins-with', 'ends-with', 'contains'], ['begins with', 'ends with', 'contains'])
            )
            for name, widget in self._search_widgets.items():
                widget.add_listener( partial( self._process_find_options, name ) )
                self._match_options[ name ] = widget.state

        return widgets.HBox( [ w.gui() for w in self._search_widgets.values() ] )

    def _process_find(self, event: Dict[str,str]):
        print( f"process_find: {event}")
        match = self._match_options['match']
        case_sensitive = ( self._match_options['case_sensitive'] == "true" )
        df: pd.DataFrame = self._current_table.get_changed_df()
        cname = self._cols[ self._current_column_index ]
        np_coldata = df[cname].values.astype('U')
        if not case_sensitive: np_coldata = np.char.lower( np_coldata )
        match_str = event['new'] if case_sensitive else event['new'].lower()
        if match == "begins-with":   mask = np.char.startswith( np_coldata, match_str )
        elif match == "ends-with":   mask = np.char.endswith( np_coldata, match_str )
        elif match == "contains":    mask = ( np.char.find( np_coldata, match_str ) >= 0 )
        else: raise Exception( f"Unrecognized match option: {match}")
        self._current_selection = df.index[mask].values
        self._apply_selection()

    def _clear_selection(self):
        self._current_selection = []
        self._wFind.value = ""

    def _apply_selection(self):
        if len( self._wFind.value ) > 0:
            find_select = self._match_options['find_select']
            selection = self._current_selection if find_select=="select" else self._current_selection[:1]
            self._current_table.change_selection( selection )

    def _process_find_options(self, name: str, state: str ):
        print( f"process_find_options[{name}]: {state}" )
        self._match_options[ name ] = state
        if name == 'find_select':
            self._apply_selection()
        else:
            self._process_find( dict( new=self._wFind.value ) )

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

