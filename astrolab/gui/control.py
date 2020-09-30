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

    def __init__( self ):
        self._wGui: ipw.Box = None
        self._buttons = {}

    def gui(self, **kwargs ) -> ipw.Box:
        if self._wGui is None:
            self._wGui = self._createGui( **kwargs )
            self._wGui.layout = ipw.Layout(width='auto', flex='0 0 300px')
        return self._wGui

    def _createGui( self, **kwargs ) -> ipw.Box:
        for task in [ "embed", "mark", "spread", "clear", "reset" ]:
            self._buttons[ task ] = ipw.Button( description=task, layout = ipw.Layout(width='auto') )
        return ipw.HBox( list(self._buttons.values()) )

controlPanel = ControlPanel()