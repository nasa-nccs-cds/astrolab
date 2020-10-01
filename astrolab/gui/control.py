import ipywidgets as ip
from typing import List, Union, Tuple, Optional, Dict, Callable
import time
import xarray as xa
import numpy as np
import pandas as pd
from astrolab.data.manager import dataManager
import ipywidgets as ipw
from traitlets import traitlets


class ControlPanel:

    def __init__( self, **kwargs ):
        self._wGui: ipw.Box = None
        self._buttons = {}
        self._classes: List[str] = None
        self._wSelectedClass: ipw.RadioButtons = None
        self.init(**kwargs)

    def init(self, **kwargs):
        nclass = kwargs.get('nclass',5)
        self._classes = kwargs.get('classes', [ f'class-{iclass}' for iclass in range(nclass)] )

    @property
    def current_class(self) -> str:
        return self._wSelectedClass.value

    @property
    def classes(self) -> List[str]:
        return self._classes

    def get_classname(self, itab_index: int ) -> str:
        return self._classes[ itab_index ]

    def gui(self, **kwargs ) -> ipw.Box:
        if self._wGui is None:
            self._wGui = self._createGui( **kwargs )
        return self._wGui

    def _createGui( self, **kwargs ) -> ipw.Box:
        unclass = 'unclassified'
        for task in [ "embed", "mark", "spread", "clear", "reset" ]:
            button = ipw.Button( description=task )
            button.layout = ipw.Layout( width='auto', flex="1 0 auto" )
            self._buttons[ task ] = button
        self.wSelectedClass = ipw.RadioButtons(options=[unclass] + self._classes, value=unclass, description='Class:', tooltip="Set current class" )
        self.wSelectedClass.layout = ipw.Layout( width = "auto", height = "220px", max_width = "500px", max_height = "500px" )
        buttonBox =  ipw.HBox( list(self._buttons.values()) )
        buttonBox.layout = ipw.Layout( width = "500px" )
        gui = ipw.VBox( [buttonBox, self.wSelectedClass]  ) # width = "auto",  flex='1 0 300px' )
        gui.layout = ipw.Layout( width = "100%",  height='100%' )
        return gui

controlPanel = ControlPanel()