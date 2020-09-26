# astrolab
Jupyterlab workbench supporting visual exploration and classification of astronomical xray and light curve data.

#### Create conda env + jupyterlab with extensions
   
    > conda create --name astrolab
    > conda activate astrolab
    > conda install -c conda-forge nodejs jupyterlab ipywidgets ipycanvas ipyevents qgrid numpy pynndescent xarray jupyter_bokeh rasterio umap-learn scipy scikit-learn toml keras tensorflow rioxarray numba dask netcdf4 toolz scikit-image
    > jupyter labextension install @jupyter-widgets/jupyterlab-manager  ipycanvas ipyevents qgrid2 @bokeh/jupyter_bokeh 
    > npm i @jupyterlab/apputils

#### Install Astrolab

    > git clone https://github.com/nasa-nccs-cds/astrolab.git
    > cd astrolab
    > python setup.py install
       
#### Start Server

    > jupyter lab 
    
    
 
 
 
 
### Experimental
    
##### ipyvolume
    > pip install ipyvolume
    > jupyter labextension install ipyvolume

##### k3d    
    > git clone https://github.com/nasa-nccs-cds/K3D-jupyter.git
    > cd K3D-jupyter
    > pip install -e .
    > jupyter labextension install ./js 
    
    >> jlpm cache clean
    >> 
   
