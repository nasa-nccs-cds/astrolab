from typing import List, Union, Tuple, Optional, Dict, Callable
from IPython.core.debugger import set_trace
from functools import partial
from collections import OrderedDict
import os, ipywidgets as ipw
import traitlets.config as tlc
import traitlets as tl
from astrolab.model.base import AstroSingleton

class Astrolab( tlc.SingletonConfigurable, AstroSingleton ):

    HOME = os.path.dirname(os.path.realpath(__file__))
    name = tl.Unicode('astrolab').tag(config=True)
    config_file = tl.Unicode().tag(config=True)
    table_cols = tl.List( tl.Unicode, ["target_names", "obsids"], 1, 100 )

    @tl.default('config_file')
    def _default_config_file(self):
        return os.path.join( os.path.expanduser("~"), "." + self.name, "configuration.py" )

    def __init__(self, **kwargs ):
        super(Astrolab, self).__init__( **kwargs )

    def configure(self):
        app = tlc.Application.instance()
        if os.path.isfile( self.config_file ):
            print(f"Loading config file: {self.config_file}")
            app.load_config_file( self.config_file )

    def save_config(self):
        conf_txt = AstroSingleton.generate_config_file()
        cfg_dir = os.path.dirname(os.path.realpath( self.config_file ) )
        os.makedirs( cfg_dir, exist_ok=True )
        with open( self.config_file, "w" ) as cfile_handle:
            print( f"Writing config file: {self.config_file}")
            cfile_handle.write( conf_txt )

    def getFilePanel(self) -> ipw.HBox:
        files = ipw.Select( options = [ "dset1", "dset2", "dset3" ], description='Datasets:',disabled=False )
        load = ipw.Button( description="Load")
        filePanel = ipw.HBox( [files, load ], layout=ipw.Layout( width="100%", flex='0 0 100px' ), border= '2px solid firebrick' )
        return filePanel

    def getControlPanel( self ) -> ipw.DOMWidget:
        from astrolab.gui.control import ActionsPanel
        from astrolab.model.labels import LabelsManager
        file: ipw.HBox = self.getFilePanel()
        actions: ipw.HBox = ActionsPanel.instance().gui()
        classes: ipw.ToggleButtons = LabelsManager.instance().gui()
        gui = ipw.VBox([file, actions, classes], layout = ipw.Layout( width="100%" )  )
        return gui

    def process_menubar_action(self, mname, dname, op, b ):
        print(f" process_menubar_action.on_value_change: {mname}.{dname} -> {op}")

    def gui( self, embed: bool = False ):
        from astrolab.gui.graph import GraphManager
        from astrolab.gui.points import PointCloudManager
        from astrolab.gui.table import TableManager
        from astrolab.gui.control import ActionsPanel
        self.configure()
        css_border = '1px solid blue'

        tableManager = TableManager.instance()
        graphManager = GraphManager.instance()
        pointCloudManager = PointCloudManager.instance()

        table = tableManager.gui(cols=self.table_cols)
        graph = graphManager.gui(mdata=self.table_cols)
        points = pointCloudManager.instance().gui()

        tableManager.add_selection_listerner(graphManager.on_selection)
        tableManager.add_selection_listerner(pointCloudManager.on_selection)
        controlPanel = self.getControlPanel( )

        control = ipw.VBox([controlPanel, table], layout=ipw.Layout( flex='0 0 500px', border=css_border) )
        plot = ipw.VBox([points, graph], layout=ipw.Layout( flex='1 1 auto', border=css_border) )
        gui = ipw.HBox([control, plot])
        self.save_config()
        if embed: ActionsPanel.instance().embed()
        return gui

    def __delete__(self, instance):
        self.save_config()





