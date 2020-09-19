# astrolab
Jupyterlab workbench supporting visual exploration and classification of astronomical xray and light curve data.

### Create conda env
   
    > conda create --name astrolab
    > conda activate astrolab
    > conda install -c conda-forge nodejs jupyterlab ipywidgets itkwidgets ipycanvas ipyevents numpy pynndescent xarray gdal vtk rasterio umap-learn scipy scikit-learn toml keras tensorflow rioxarray numba itk dask netcdf4 toolz scikit-image matplotlib itk
    > jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-matplotlib jupyterlab-datawidgets itkwidgets ipycanvas ipyevents
    
### Start Server

    > jupyter lab 