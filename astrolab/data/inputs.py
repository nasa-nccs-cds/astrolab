from .manager import DataManager
import xarray as xa
import numpy as np
import os, glob
from collections import OrderedDict
from typing import List, Union, Tuple, Optional, Dict
from functools import partial
from typing import Optional, Dict
from astrolab.reduction.embedding import ReductionManager

def getXarray(  id: str, xcoords: Dict, subsample: int, xdims:OrderedDict, **kwargs ) -> xa.DataArray:
    np_data: np.ndarray = DataManager.instance().getInputFileData( id, subsample, tuple(xdims.keys()) )
    dims, coords = [], {}
    for iS in np_data.shape:
        coord_name = xdims[iS]
        dims.append( coord_name )
        coords[ coord_name ] = xcoords[ coord_name ]
    attrs = { **kwargs, 'name': id }
    return xa.DataArray( np_data, dims=dims, coords=coords, name=id, attrs=attrs )

def prepare_inputs( input_vars, ssample = None ):
    dataManager = DataManager.instance()
    subsample = dataManager.subsample if ssample is None else ssample
    np_embedding = dataManager.getInputFileData( input_vars['embedding'], subsample )
    dims = np_embedding.shape
    mdata_vars = list(input_vars['directory'])
    xcoords = OrderedDict( samples = np.arange( dims[0] ), bands = np.arange(dims[1]) )
    xdims = OrderedDict( { dims[0]: 'samples', dims[1]: 'bands' } )
    data_vars = dict( embedding = xa.DataArray( np_embedding, dims=xcoords.keys(), coords=xcoords, name=input_vars['embedding'] ) )
    data_vars.update( { vid: getXarray( vid, xcoords, subsample, xdims ) for vid in mdata_vars } )
    pspec = input_vars['plot']
    data_vars.update( { f'plot-{vid}': getXarray( pspec[vid], xcoords, subsample, xdims, norm=pspec.get('norm','')) for vid in [ 'x', 'y' ] } )
    reduction_method = dataManager.config.value("input.reduction/method",  'None')
    ndim = int(dataManager.config.value("input.reduction/ndim", 32 ))
    epochs = int(dataManager.config.value("input.reduction/epochs", 1))
    if reduction_method != "None":
       reduced_spectra = ReductionManager.instance().reduce( data_vars['embedding'], reduction_method, ndim, epochs )
       coords = dict( samples=xcoords['samples'], model=np.arange(ndim) )
       data_vars['reduction'] =  xa.DataArray( reduced_spectra, dims=['samples','model'], coords=coords )

    dataset = xa.Dataset( data_vars, coords=xcoords, attrs = {'type':'spectra'} )
    dataset.attrs["colnames"] = mdata_vars
    projId = dataManager.config.value('project/id')
    file_name = f"raw" if reduction_method == "None" else f"{reduction_method}-{ndim}"
    if subsample > 1: file_name = f"{file_name}-ss{subsample}"
    outputDir = os.path.join( dataManager.config.value('data/cache'), projId )
    mode = 0o777
    os.makedirs( outputDir, mode, True )
    output_file = os.path.join( outputDir, file_name + ".nc" )
    print( f"Writing output to {output_file}")
    dataset.to_netcdf( output_file, format='NETCDF4', engine='netcdf4' )