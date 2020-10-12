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
from ipyevents import Event
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
        self._current_selection: List[int] = []
        self._selection_listeners: List[Callable[[Dict],None]] = [ ]
        self._class_map = None
        self._search_widgets = None
        self._match_options = {}
        self._events = []

    def init(self, **kwargs):
        catalog: Dict[str,np.ndarray] = kwargs.get( 'catalog', None )
        project_data: xa.Dataset = DataManager.instance().loadCurrentProject()
        table_cols = kwargs.get('cols', project_data.variables.keys())
        if catalog is None:  catalog = { tcol: project_data[tcol].values for tcol in table_cols }
        nrows = catalog[table_cols[0]].shape[0]
        self._dataFrame: pd.DataFrame = pd.DataFrame( catalog, dtype='U', index=pd.Int64Index( range(nrows), name="Index" ) )
        self._cols = list(catalog.keys()) + [ "Class" ]
        self._class_map = np.zeros( nrows, np.int32 )

    def add_selection_listerner( self, listener: Callable[[Dict],None] ):
        self._selection_listeners.append( listener )

    def mark_selection(self):
        from .points import PointCloudManager
        selection_table: pd.DataFrame = self._tables[0].df.loc[self._current_selection]
        cid: int = PointCloudManager.instance().mark_points( selection_table.index.to_numpy(), update=True )
        self._class_map[self._current_selection] = cid
        for table_index, table in enumerate( self._tables ):
            if table_index == 0:
                index_list: List[int] = selection_table.index.tolist()
                print( f" -----> Setting cid[{cid}] for indices= {index_list[:10]}... ")
                table.edit_cell( index_list, "Class", cid )
            else:
                if table_index == cid:    table.df = pd.concat( [ table.df, selection_table ] ).drop_duplicates()
                else:                     table.df = table.df.drop( index=self._current_selection, errors="ignore" )

    @property
    def selected_class(self):
        return int( self._wTablesWidget.selected_index )

    @property
    def selected_table(self):
        return self._tables[ self.selected_class ]

    def spread_selection(self):
        from astrolab.graph.flow import ActivationFlowManager, ActivationFlow
        from .points import PointCloudManager
        project_dataset: xa.Dataset = DataManager.instance().loadCurrentProject()
        catalog_pids = np.arange( 0, project_dataset.reduction.shape[0] )
        flow: ActivationFlow = ActivationFlowManager.instance().getActivationFlow( project_dataset.reduction )

        if flow.spread(self._class_map, 1) is not None:
            self._class_map = flow.C
            all_classes = (self.selected_class == 0)
            for cid, table in enumerate( self._tables[1:], 1 ):
                if all_classes or (self.selected_class == cid):
                    new_indices: np.ndarray = catalog_pids[ self._class_map == cid ]
                    if new_indices.size > 0:
                        selection_table: pd.DataFrame = self._tables[0].df.loc[ new_indices ]
                        table.df = pd.concat([table.df, selection_table]).drop_duplicates()
                        PointCloudManager.instance().mark_points( selection_table.index.to_numpy(), cid )
            PointCloudManager.instance().update_plot()

    def undo_selection(self):
        pass

    def clear_selection(self):
        from .points import PointCloudManager
        all_classes = (self.selected_class == 0)
        self._tables[0].change_selection([])
        for cid, table in enumerate( self._tables[1:], 1 ):
            if all_classes or (self.selected_class == cid):
                pids = table.df.index.tolist()
                if len( pids ) > 0:
                    PointCloudManager.instance().clear_points( cid )
                    table.remove_rows( pids )
                    table.df.drop( index=pids, inplace=True )
            PointCloudManager.instance().update_plot()

    def _handle_table_event(self, event, widget):
        ename = event['name']
        if( ename == 'sort_changed'):
            cname = event['new']['column']
            print(f"  handle_table_event: {ename}[{cname}]: {self._cols}")
            self._current_column_index = self._cols.index( cname )
            print(f"  ... col-sel ---> ci={self._current_column_index}")
            self._clear_selection()
        elif (ename == 'selection_changed'):
            if event['source'] == 'gui':
                rows = event["new"]
                if len( rows ) == 1 or self.is_block_selection(event):
                    print( f" TABLE.row-sel --->  {rows}" )
                    df = self._tables[0].get_changed_df()
#                    print( f" TABLE[0].row-index[:10] --->  {df.index[:10].to_list()}")
                    self._current_selection = df.index[ rows ].to_list()
#                    print( f" TABLE[0].current_selection[:10] --->  {self._current_selection[:10]}")
                    self.broadcast_selection_event( self._current_selection )

    def is_block_selection( self, event: Dict ) -> bool:
        old, new = event['old'], event['new']
        if (len(old) == 1) and (new[-1] == old[ 0]) and ( len(new) == (new[-2]-new[-1]+1)): return True
        if (len(old) >  1) and (new[-1] == old[-1]) and ( len(new) == (new[-2]-new[-1]+1)): return True
        return False

    def is_block_selection1( self, event: Dict ) -> bool:
        row_list = event['new'].sort()
        return row_list == list( range( row_list[0], row_list[-1]+1 ) )

    def broadcast_selection_event(self, pids: List[int] ):
        selection_event = dict( pids=pids )
        item_str = "" if len(pids) > 8 else f",  pids={pids}"
        print(f"TABLE.gui->selection_changed, nitems={len(pids)}{item_str}")
        for listener in self._selection_listeners:
            listener( selection_event )

    def _createTable( self, tab_index: int ) -> qgrid.QgridWidget:
        assert self._dataFrame is not None, " TableManager has not been initialized "
        col_opts = dict( editable=False ) #
        grid_opts = dict(  editable=False, maxVisibleRows=40 )
        if tab_index == 0:
            data_table = self._dataFrame.sort_values(self._cols[0] )
            data_table.insert( len(self._cols)-1, "Class", 0, True )
            wTable = qgrid.show_grid( data_table, column_options=col_opts, grid_options=grid_opts, show_toolbar=False )
        else:
            empty_catalog = {col: np.empty( [0], 'U' ) for col in self._cols}
            dFrame: pd.DataFrame = pd.DataFrame(empty_catalog, dtype='U', index=pd.Int64Index( [], name="Index" ) )
            wTable = qgrid.show_grid( dFrame, column_options=col_opts, grid_options=grid_opts, show_toolbar=False )
        wTable.on( traitlets.All, self._handle_table_event )
        wTable.layout = ipw.Layout( width="auto", height="100%", max_height="1000px" )
#        events = Event(source=wTable, watched_events=['keyup', 'keydown'])
#        events.on_dom_event(self._handle_key_event)
#        self._events.append( events )
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
        df: pd.DataFrame = self.selected_table.get_changed_df()
        cname = self._cols[ self._current_column_index ]
        np_coldata = df[cname].to_numpy( dtype='U' )
        if not case_sensitive: np_coldata = np.char.lower( np_coldata )
        match_str = event['new'] if case_sensitive else event['new'].lower()
        if match == "begins-with":   mask = np.char.startswith( np_coldata, match_str )
        elif match == "ends-with":   mask = np.char.endswith( np_coldata, match_str )
        elif match == "contains":    mask = ( np.char.find( np_coldata, match_str ) >= 0 )
        else: raise Exception( f"Unrecognized match option: {match}")
        print( f"process_find[ M:{match} CS:{case_sensitive} col:{self._current_column_index} ], coldata shape = {np_coldata.shape}, match_str={match_str}, coldata[:10]={np_coldata[:10]}" )
        self._current_selection = df.index[mask].to_list()
        print(f" --> cname = {cname}, mask shape = {mask.shape}, mask #nonzero = {np.count_nonzero(mask)}, #selected = {len(self._current_selection)}, selection[:8] = {self._current_selection[:8]}")
        self._select_find_results( )

    def _clear_selection(self):
        self._current_selection = []
        self._wFind.value = ""

    def _select_find_results(self ):
        if len( self._wFind.value ) > 0:
            find_select = self._match_options['find_select']
            selection = self._current_selection if find_select=="select" else self._current_selection[:1]
            print(f"apply_selection[ {find_select} ], nitems: {len(selection)}")
            self.selected_table.change_selection( selection )
            self.broadcast_selection_event( selection )

    def _process_find_options(self, name: str, state: str ):
        print( f"process_find_options[{name}]: {state}" )
        self._match_options[ name ] = state
        self._process_find( dict( new=self._wFind.value ) )

    def _createTableTabs(self) -> widgets.Tab:
        wTab = widgets.Tab()
        self._tables.append( self._createTable( 0 ))
        wTab.set_title( 0, 'Catalog')
        for iC, ctitle in enumerate( LabelsManager.instance().labels[1:], 1 ):
            self._tables.append(  self._createTable( iC ) )
            wTab.set_title( iC, ctitle )
        wTab.children = self._tables
        return wTab

    def _handle_key_event(self, event: Dict ):
        print( f" ################## handle_key_event: {event}  ################## ################## ##################" )

    def gui( self, **kwargs ) -> widgets.VBox:
        if self._wGui is None:
            self.init( **kwargs )
            self._wGui = self._createGui()
            self._wGui.layout = ipw.Layout(width='auto', flex='1 0 500px')
            print( f" STYLE: '{self._wGui.box_style}'")
        return self._wGui

