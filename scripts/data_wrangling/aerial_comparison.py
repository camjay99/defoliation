# Compute specified percentiles of mean intensity for each region outlined in 
# aerial survey data. This data is used to help validate our method.

##############################################################
# Imports Packages
##############################################################

import ee       # Google Earth Engine API

try:
    ee.Initialize()
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize()
    
    
##################################################################
# Load defoliation data
##################################################################

defol = ee.Image('projects/ee-cjc378/assets/defol_maps/new_york_2021').select('mean_intensity')


##################################################################
# Load validation data
##################################################################

validation = ee.FeatureCollection('projects/ee-cjc378/assets/aerial_survey')
validation = validation.filter(ee.Filter.eq('year', 2021))


##################################################################
# Calculate appropriate percentile for each region
##################################################################

validation = defol.reduceRegions(
    reducer=ee.Reducer.percentile([10, 29, 50]),
    collection=validation,
    scale=10,
    crs='EPSG:32618'
)


#################################
# Submit batch job
#################################

task = ee.batch.Export.table.toDrive(
    collection=validation,
    description='validation',
    folder='Defoliation',
    fileFormat='CSV',
    selectors=['year', 'PCT_AFFECT', 'p10', 'p29', 'p50']
)

task.start()