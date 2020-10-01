import logging
from typing import List, Union, Tuple, Optional, Dict, Callable
from IPython.core.debugger import set_trace
from functools import partial
import xarray as xa
import numpy as np
import ipywidgets as ipw
from astrolab.data.manager import dataManager
import ipywidgets as widgets
from traitlets import traitlets
import traitlets.config as tc

class Astrolab( tc.Application ):

    def __init__(self, **kwargs ):
        super(Astrolab, self).__init__( **kwargs )




