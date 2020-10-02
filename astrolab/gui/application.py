import logging
from typing import List, Union, Tuple, Optional, Dict, Callable
from IPython.core.debugger import set_trace
from functools import partial
import xarray as xa
import numpy as np
from astrolab.data.manager import DataManager
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

    def gui(self):
        from astrolab.gui.graph import GraphManager
        from astrolab.gui.points import PointCloudManager
        from astrolab.gui.table import TableManager
        from astrolab.gui.control import ControlPanel
        self.configure()
        tableManager = TableManager.instance()
        graphManager = GraphManager.instance()
        pointCloudManager = PointCloudManager.instance()

        table = tableManager.gui(cols=self.table_cols)
        graph = graphManager.gui(mdata=self.table_cols)
        points = pointCloudManager.instance().gui()
        controller = ControlPanel.instance().gui()

        tableManager.add_selection_listerner(graphManager.on_selection)
        tableManager.add_selection_listerner(pointCloudManager.on_selection)

        control = ipw.VBox([table, controller], layout=ipw.Layout(flex='0 0 500px'))
        plot = ipw.VBox([points, graph], layout=ipw.Layout(flex='1 1 auto'))
        gui = ipw.HBox([control, plot])
        self.save_config()
        return gui

    def __delete__(self, instance):
        self.save_config()





