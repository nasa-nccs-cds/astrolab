from ipysheet import sheet, column, cell
from typing import List, Union, Tuple, Optional, Dict, Callable
import numpy as np
from astrolab.data.manager import dataManager

config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),

)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()
_cols = {}
_headers = {}

def style_observer( event: Dict ):
    print( f"Style event: {event}")

project_data = dataManager.loadCurrentProject()
cols = [ "target_names", "obsids" ]

sheet0 = None
for iC, cname in enumerate(cols):
    col_data = project_data[cname].values.tolist()
    if sheet0 is None:
        sheet0 = sheet( "sheet0", len(col_data)+1, len(cols) )
    __col = column( iC, col_data, 1, read_only=True )
    __col.observe( style_observer, 'style', 'All' )
    _cols[ cname ] = __col
    _headers[ cname ] = cell( 0, iC, cname, color="yellow", background_color="black", font_style="bold", read_only=True )

sheet0