##############################################################
# Imports Packages
##############################################################

import ee       # Google Earth Engine API
import time

try:
    ee.Initialize(project='ee-cjc378')
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize(project='ee-cjc378')
    

##############################################################
# Divide Study Region
##############################################################

START_DATE = '2023-01-01'
END_DATE = '2024-01-01'
year = 2023

exportRegion = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level1").filter(ee.Filter.eq('ADM1_NAME', 'New York'));

defol_coll = ee.ImageCollection('projects/ee-cjc378/assets/defoliation_score_New_York').filter(ee.Filter.eq('year', year))

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326'; # WGS84 lat lon
dx = 0.5;
dy = 0.5;

# Make grid and visualize.
proj = ee.Projection(projection).scale(dx, dy)
grid = exportRegion.geometry().coveringGrid(proj)

gridSize = grid.size().getInfo()
gridList = grid.toList(gridSize)

assetCollection='projects/ee-cjc378/assets/score_denoised_New_York'
imageBaseName='score_denoised'



for i in range(gridSize):
    gridCell = ee.Feature(gridList.get(i)).geometry()
    gridCellBuffer = gridCell.buffer(distance=400)
    
    defol_gridCell = defol_coll.filterBounds(gridCellBuffer).mosaic().clip(gridCellBuffer)
    class_gridCell = defol_gridCell.lte(-0.045)

    groups_gridCell = class_gridCell.connectedPixelCount(15, False)
    too_small = groups_gridCell.lte(10)
    
    groups_denoised = class_gridCell.And(too_small.Not()).toUint8()
    
    groups_denoised = groups_denoised.set('year', year)
    
    #################################
    # Submit batch job
    #################################

    imageName = f'{imageBaseName}_{year}_tile_{i}'
    task = ee.batch.Export.image.toAsset(
        image            = groups_denoised,
        description      = imageName,
        assetId          = f'{assetCollection}/{imageName}',
        region           = gridCell, 
        scale            = 10,
        crs              = "EPSG:4326",
        pyramidingPolicy = {'.default': 'mean'},
        maxPixels        = 1e10
    )
    time.sleep(0.5)
    task.start()