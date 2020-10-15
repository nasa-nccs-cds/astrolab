import ipywidgets as ip
from typing import List, Union, Tuple, Optional, Dict, Callable
import time
from functools import partial
import xarray as xa
import numpy as np
import ipywidgets as ipw
from .points import PointCloudManager
import traitlets.config as tlc
from astrolab.model.base import AstroSingleton

class ControlPanel(tlc.SingletonConfigurable,AstroSingleton):

    def __init__(self, **kwargs):
        super(ControlPanel, self).__init__(**kwargs)
        self._wGui: ipw.Box = None
        self._buttons = {}
        self.wSelectedClass: ipw.ToggleButtons = None

    @property
    def current_class(self) -> str:
        return self.wSelectedClass.value

    @property
    def current_cid(self) -> str:
        return self.wSelectedClass.index

    def gui(self, **kwargs ) -> ipw.Box:
        if self._wGui is None:
            self._wGui = self._createGui( **kwargs )
        return self._wGui

    def on_button_click( self, task, button: ipw.Button = None ):
        from .table import TableManager
        tmgr = TableManager.instance()
        if task ==   "embed":  PointCloudManager.instance().reembed()
        elif task == "mark":   tmgr.mark_selection()
        elif task == "spread": tmgr.spread_selection()
        elif task == "clear":  tmgr.clear_current_class()
        elif task == "undo":   tmgr.undo_action()
        elif task == "distance": tmgr.display_distance()

    def _createGui( self, **kwargs ) -> ipw.Box:
        from astrolab.model.labels import LabelsManager
        for task in [ "embed", "mark", "spread", "distance", "undo", "clear" ]:
            button = ipw.Button( description=task )
            button.layout = ipw.Layout( width='auto', flex="1 0 auto" )
            button.on_click( partial( self.on_button_click, task ) )
            self._buttons[ task ] = button
        classes = LabelsManager.instance().labels
        self.wSelectedClass = ipw.ToggleButtons( options=classes, description='Class:', disabled=False, tooltip="Set current class" )
        self.wSelectedClass.layout = ipw.Layout( width = "auto", height = "auto" )
        buttonBox =  ipw.HBox( list(self._buttons.values()) )
        buttonBox.layout = ipw.Layout( width = "500px" )
        gui = ipw.VBox( [buttonBox, self.wSelectedClass] )
        gui.layout = ipw.Layout( width = "100%", flex='0 0 200px' )
        return gui

    def embed(self):
        self.on_button_click("embed")

