# astrolab
Jupyterlab workbench supporting visual exploration and classification of astronomical xray and light curve data.

### Create conda env + jupyterlab with extensions
   
    > conda create --name astrolab
    > conda activate astrolab
    > conda install -c conda-forge nodejs jupyterlab ipywidgets itkwidgets ipycanvas ipyevents ipympl qgrid numpy pynndescent xarray gdal jupyter_bokeh vtk rasterio umap-learn scipy scikit-learn toml keras tensorflow rioxarray numba itk dask netcdf4 toolz scikit-image itk
    > jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-matplotlib jupyterlab-datawidgets itkwidgets ipycanvas ipyevents qgrid2 @bokeh/jupyter_bokeh
    > jupyter nbextension enable --py --sys-prefix qgrid
    > jupyter nbextension enable --py --sys-prefix widgetsnbextension
   
### Start Server

    > jupyter lab 