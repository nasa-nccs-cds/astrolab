from astrolab.data.manager import dataManager

config = dict(
    reduce = dict( method="Autoencoder", dims=16, subsample=5 ),
    data = dict( cache="~/Development/Cache" ),

)

dataManager.initProject( 'swiftclass', 'read_data_test', config )
dataManager.save()

project_data = dataManager.loadCurrentProject()

print( project_data )