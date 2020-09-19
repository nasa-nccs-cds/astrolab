from typing import List, Union, Tuple, Dict
from keras.layers import *
from keras.models import *
from typing import List, Union, Tuple, Optional, Dict
from ..data.manager import dataManager
from ..graph.flow import activationFlowManager
import umap, xarray as xa
import numpy as np, time, traceback

class ReductionManager(object):

    def __init__( self, **kwargs ):
        self._mapper = {}

    def reduce(self, inputs: np.ndarray, reduction_method: str, ndim: int, nepochs: int = 1  ) -> np.ndarray:
        if reduction_method.lower() == "autoencoder": return self.autoencoder_reduction( inputs, ndim, nepochs )

    def xreduce(self, inputs: xa.DataArray, reduction_method: str, ndim: int ) -> xa.DataArray:
        if reduction_method.lower() == "autoencoder":
            encoded_data = self.autoencoder_reduction( inputs.values, ndim )
            coords = {inputs.dims[0]: inputs.coords[inputs.dims[0]], inputs.dims[1]: np.arange(ndim)}
            return xa.DataArray(encoded_data, dims=inputs.dims, coords=coords, attrs=inputs.attrs)
        return inputs

    def spectral_reduction(data, graph, n_components=3, sparsify=False):
        t0 = time.time()
        graph = graph.tocoo()
        graph.sum_duplicates()
        if sparsify:
            n_epochs = 200
            graph.data[graph.data < (graph.data.max() / float(n_epochs))] = 0.0
            graph.eliminate_zeros()

        random_state = np.random.RandomState()
        initialisation = spectral_layout(data, graph, n_components, random_state, metric="euclidean")
        expansion = 10.0 / np.abs(initialisation).max()
        rv = (initialisation * expansion).astype(np.float32)
        print(f"Completed spectral_embedding in {(time.time() - t0) / 60.0} min.")
        return rv

    def autoencoder_reduction( self, encoder_input: np.ndarray, ndim: int, epochs: int = 1 ) -> np.ndarray:
        input_dims = encoder_input.shape[1]
        reduction_factor = 1.7
        inputlayer = Input( shape=[input_dims] )
        activation = 'tanh'
        encoded = None
        layer_dims, x = input_dims, inputlayer
        while layer_dims > ndim:
            x = Dense(layer_dims, activation=activation)(x)
            layer_dims = int( round( layer_dims / reduction_factor ))
        layer_dims = ndim
        while layer_dims < input_dims:
            x = Dense(layer_dims, activation=activation)(x)
            if encoded is None: encoded = x
            layer_dims = int( round( layer_dims * reduction_factor ))
        decoded = Dense( input_dims, activation='sigmoid' )(x)

#        modelcheckpoint = ModelCheckpoint('xray_auto.weights', monitor='loss', verbose=1, save_best_only=True, save_weights_only=True, mode='auto', period=1)
#        earlystopping = EarlyStopping(monitor='loss', min_delta=0., patience=100, verbose=1, mode='auto')
        autoencoder = Model(inputs=[inputlayer], outputs=[decoded])
        encoder = Model(inputs=[inputlayer], outputs=[encoded])
        autoencoder.compile(loss='mse', optimizer='rmsprop')

        autoencoder.fit( encoder_input, encoder_input, epochs=epochs, batch_size=256, shuffle=True )
        return  encoder.predict( encoder_input )

    def umap_embedding( self,  point_data: xa.DataArray, **kwargs ) -> Optional[xa.DataArray]:
        ndim = int( kwargs.get('ndim', dataManager.config["umap"]["dims"] ) )
        mapper: umap.UMAP = self.getUMapper( point_data.attrs['dsid'], ndim )
        if mapper.embedding is not None:
            return self.wrap_embedding( point_data.coords[ point_data.dims[0] ], mapper.embedding )
        else:
            flow = activationFlowManager.getActivationFlow(point_data)
            # if flow.nnd is None:
            #     event = dict(event="message", type="warning", title='Workflow Message',
            #                  caption="Awaiting task completion",
            #                  msg="The NN graph computation has not yet finished")
            #     self.submitEvent(event, EventMode.Gui)
            #     return None
            ndim = dataManager.config["umap"].get( "dims", 3 )
            init_method = dataManager.config["umap"].get( "init", "random" )
            if self._state == self.INIT:
                kwargs['nepochs'] = 1
                self._state = self.NEW_DATA
            else:
                if 'nepochs' not in kwargs.keys(): kwargs['nepochs'] = dataManager.config["umap"].get( "nepochs", 100 )
                if 'alpha' not in kwargs.keys():   kwargs['alpha'] = dataManager.config["umap"].get( "alpha", 0.1 )
                self._state = self.PROCESSED
            t0 = time.time()
            mapper = self.getUMapper(point_data.attrs['dsid'], ndim)
            mapper.flow = flow
            t1 = time.time()
            labels_data: np.ndarray = labelsManager.labels_data().values
            if point_data.shape[1] <= ndim:
                mapper.set_embedding(point_data)
            else:
                try:

                    if mapper.embedding is not None:
                        mapper.clear_initialization()
                        mapper.init = mapper.embedding
                    elif init_method == "autoencoder":
                        mapper.init = self.reduce( point_data.data, init_method, ndim )
                    else:
                        mapper.init = init_method
                    print(
                        f"Completed data prep in {(t1 - t0)} sec, Now fitting umap[{ndim}] with {point_data.shape[0]} samples and {np.count_nonzero(labels_data)} labels")

                    mapper.embed( point_data.data, flow.nnd, labels_data, **kwargs )
                except Exception as err:
                    print(f" Embedding error: {err}")
                    traceback.print_exc(50)
                    return None

            t2 = time.time()
            print(f"Completed umap fitting in {(t2 - t1) / 60.0} min, embedding shape = {mapper.embedding.shape}")
            return self.wrap_embedding( point_data.coords['samples'], mapper.embedding)

    def wrap_embedding(self, ax_samples: xa.DataArray, embedding: np.ndarray, **kwargs )-> xa.DataArray:
        ax_model = np.arange( embedding.shape[1] )
        return xa.DataArray( embedding, dims=['samples','model'], coords=dict( samples=ax_samples, model=ax_model ) )

    def getUMapper(self, dsid: str, ndim: int ) -> umap.UMAP:
        mid = f"{ndim}-{dsid}"
        mapper = self._mapper.get( mid )
        if ( mapper is None ):
            n_neighbors = dataManager.config["umap"].get("nneighbors",8)
            init = dataManager.config["umap"].get("init","random")
            target_weight = dataManager.config["umap"].get("target_weight", 0.5 )
            parms = dict( n_neighbors=n_neighbors, init=init, target_weight=target_weight ); parms.update( **self.conf, n_components=ndim )
            mapper = umap.UMAP(**parms)
            self._mapper[mid] = mapper
        self._current_mapper = mapper
        return mapper

reductionManager = ReductionManager( )
