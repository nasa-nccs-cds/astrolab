import qgrid, logging
from typing import List, Union, Tuple, Optional, Dict, Callable
from IPython.core.debugger import set_trace
from functools import partial
import xarray as xa
import numpy as np
import pandas as pd
import ipywidgets as ipw
from .widgets import ToggleButton
from astrolab.data.manager import DataManager
import ipywidgets as widgets
from traitlets import traitlets
from astrolab.model.labels import LabelsManager
import traitlets.config as tlc
from astrolab.model.base import AstroSingleton

class TableManager(tlc.SingletonConfigurable,AstroSingleton):

    def __init__(self, **kwargs):
        super(TableManager, self).__init__(**kwargs)
        self._wGui: widgets.VBox = None
        self._dataFrame: pd.DataFrame = None
        self._cols: List[str] = None
        self._tables: List[qgrid.QgridWidget] = []
        self._wTablesWidget: widgets.Tab = None
        self._current_column_index: int = 0
        self._current_table: qgrid.QgridWidget = None
        self._current_selection: List[int] = []
        self._selection_listeners: List[Callable[[Dict],None]] = [ self._internal_listener ]
        self._class_map = None
        self._search_widgets = None
        self._match_options = {}

    def init(self, **kwargs):
        catalog: Dict[str,np.ndarray] = kwargs.get( 'catalog', None )
        project_data: xa.Dataset = DataManager.instance().loadCurrentProject()
        table_cols = kwargs.get('cols', project_data.variables.keys())
        if catalog is None:  catalog = { tcol: project_data[tcol].values for tcol in table_cols }
        nrows = catalog[table_cols[0]].shape[0]
        self._dataFrame: pd.DataFrame = pd.DataFrame( catalog, dtype='U', index=pd.Int64Index( range(nrows), name="Index" ) )
        self._cols = list(catalog.keys())
        self._class_map = np.zeros( nrows, np.int32 )

    def add_selection_listerner( self, listener: Callable[[Dict],None] ):
        self._selection_listeners.append( listener )

    def mark_selection(self):
        from .points import PointCloudManager
        selection_table: pd.DataFrame = self._tables[0].df.loc[self._current_selection]
        cid: int = PointCloudManager.instance().mark_points( selection_table.index, update=True )
        self._class_map[self._current_selection] = cid
        for table_index, table in enumerate( self._tables[1:] ):
            if table_index+1 == cid:    table.df = pd.concat( [ table.df, selection_table ] ).drop_duplicates()
            else:                       table.df = table.df.drop( index=self._current_selection, errors="ignore" )

    def spread_selection(self):
        from astrolab.graph.flow import ActivationFlowManager, ActivationFlow
        from .points import PointCloudManager
        project_dataset: xa.Dataset = DataManager.instance().loadCurrentProject()
        catalog_pids = np.arange( 0, project_dataset.reduction.shape[0] )
        flow: ActivationFlow = ActivationFlowManager.instance().getActivationFlow( project_dataset.reduction )
        if flow.spread(self._class_map, 1) is not None:
            self._class_map = flow.C
            for cid, table in enumerate( self._tables[1:], 1 ):
                new_indices: np.ndarray = catalog_pids[ self._class_map == cid ]
                if new_indices.size > 0:
                    selection_table: pd.DataFrame = self._tables[0].df.loc[ new_indices ]
                    table.df = pd.concat([table.df, selection_table]).drop_duplicates()
                    PointCloudManager.instance().mark_points( selection_table.index, cid )
            PointCloudManager.instance().update_plot()

    def _handle_table_event(self, event, widget):
        self._current_table = widget
        ename = event['name']
        if( ename == 'sort_changed'):
            self._current_column_index = self._cols.index( event['new']['column'] )
            self._clear_selection()
        elif (ename == 'selection_changed'):
            itab_index = self._tables.index( widget )
            cname = LabelsManager.instance().labels[ itab_index ]
            selection_event = dict( classname=cname, **event )
            new_pids = self._tables[0].df.index[ event["new"] ]  #  [catalog.df.index[idx] for idx in event["new"]]
            selection_event['pids'] = self._current_selection = new_pids
            item_str = "" if len(new_pids) > 8 else f", rows={event['new']}, pids={new_pids}"
            print(f"TABLE.selection_changed[{itab_index}:{cname}], nitems={len(new_pids)}{item_str}")
            for listener in self._selection_listeners:
                listener( selection_event )

    def _internal_listener(self, selection_event: Dict ):
        new_items = selection_event['new']
        print(f" TABLE-internal, selection_change: nitems={len(new_items)}")

    def _createTable( self, tab_index: int ) -> qgrid.QgridWidget:
        assert self._dataFrame is not None, " TableManager has not been initialized "
        col_opts = dict( editable=False )
        grid_opts = dict( editable=False, maxVisibleRows=40 )
        if tab_index == 0:
            wTable = qgrid.show_grid( self._dataFrame.sort_values(self._cols[0] ), column_options=col_opts, grid_options=grid_opts, show_toolbar=False )
        else:
            empty_catalog = {col: np.empty( [0], 'U' ) for col in self._cols}
            dFrame: pd.DataFrame = pd.DataFrame(empty_catalog, dtype='U', index=pd.Int64Index( [], name="Index" ) )
            wTable = qgrid.show_grid( dFrame, column_options=col_opts, grid_options=grid_opts, show_toolbar=False )
        wTable.on( traitlets.All, self._handle_table_event )
        wTable.layout = ipw.Layout( width="auto", height="100%", max_height="1000px" )
        return wTable

    def _createGui( self ) -> widgets.VBox:
        wSelectionPanel = self._createSelectionPanel()
        self._wTablesWidget = self._createTableTabs()
        return widgets.VBox([wSelectionPanel, self._wTablesWidget])

    def _createSelectionPanel( self ) -> widgets.HBox:
        self._wFind = widgets.Text( value='', placeholder='Find items', description='Find:', disabled=False, continuous_update = False, tooltip="Search in sorted column" )
        self._wFind.observe(self._process_find, 'value')
        wFindOptions = self._createFindOptionButtons()
        wSelectionPanel = widgets.HBox( [ self._wFind, wFindOptions ] )
        wSelectionPanel.layout = ipw.Layout( justify_content = "center", align_items="center", width = "auto", height = "50px", min_height = "50px", border_width=1, border_color="white" )
        return wSelectionPanel

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

        buttonbox =  widgets.HBox( [ w.gui() for w in self._search_widgets.values() ] )
        buttonbox.layout = ipw.Layout( width = "300px", min_width = "300px", height = "auto" )
        return buttonbox

    def _process_find(self, event: Dict[str,str]):
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
        print( f"process_find[ M:{match} CS:{case_sensitive} CI:{self._current_column_index} ], cname = {cname}, nitems: {mask.shape[0]}")
        self._current_selection = df.index[mask].values
        self._apply_selection()

    def _clear_selection(self):
        self._current_selection = []
        self._wFind.value = ""

    def _apply_selection(self):
        if len( self._wFind.value ) > 0:
            find_select = self._match_options['find_select']
            selection = self._current_selection if find_select=="select" else self._current_selection[:1]
            print(f"apply_selection[ {find_select} ], nitems: {len(selection)}")
            self._current_table.change_selection( selection )

    def _process_find_options(self, name: str, state: str ):
        print( f"process_find_options[{name}]: {state}" )
        self._match_options[ name ] = state
        self._process_find( dict( new=self._wFind.value ) )

    def _createTableTabs(self) -> widgets.Tab:
        wTab = widgets.Tab()
        self._current_table = self._createTable( 0 )
        self._tables.append( self._current_table )
        wTab.set_title( 0, 'Catalog')
        for iC, ctitle in enumerate( LabelsManager.instance().labels[1:] ):
            self._tables.append(  self._createTable( iC+1 ) )
            wTab.set_title( iC+1, ctitle )
        wTab.children = self._tables
        return wTab

    def gui( self, **kwargs ) -> widgets.VBox:
        if self._wGui is None:
            self.init( **kwargs )
            self._wGui = self._createGui()
            self._wGui.layout = ipw.Layout(width='auto', flex='1 0 500px')
        return self._wGui

