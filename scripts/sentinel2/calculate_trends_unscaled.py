# TODO: Get rid of unnecessary copyProperties
# TODO: Doy calculation does not appear to be working correctly... Figure out how to correct that.

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
    
    
##################################################################
# Specify download region and cloud removal parameters
##################################################################

# New York boundaries, as specified by FAO Global Administrative Unit Layers
# region = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', 'New York'))

# Tompkins County boundaries, as specified by FAO Global Administrative Unit Layers
# region = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM1_NAME', 'New York')).filter(ee.Filter.eq('ADM2_NAME', 'Tompkins'))

# Mt. Pleasant
# region = ee.Geometry.Polygon(
#         [[[-76.40472618414064, 42.48029198346047],
#           [-76.40472618414064, 42.3696708995445],
#           [-76.16963592840334, 42.3696708995445],
#           [-76.16963592840334, 42.48029198346047]]], None, False)
# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01'
# END_DATE = '2024-01-01'

# description = 'Sentinel2_unscaled_Mt_Pleasant_Trend'
# assetID = 'Mt_Pleasant_Trends/Sentinel2_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Mt_Pleasant_Phenology_Maps/Sentinel2')


# # Allegheny
# region = ee.Geometry.Polygon([[[-79.1986092128225, 42.249085326281715],
#                                          [-79.1986092128225, 41.72954071466429],
#                                          [-78.33343587297875, 41.72954071466429],
#                                          [-78.33343587297875, 42.249085326281715]]], None, False)
# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01';
# END_DATE = '2024-01-01';

# description = 'Sentinel2_unscaled_Allegheny_Trends'
# assetID = 'Allegheny_Trends/Sentinel2_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Allegheny_Phenology_Maps/Sentinel2')

# # New Jersey Pine Barrens
# region = ee.Geometry.Polygon(
#         [[[-75.25635105039267, 40.082652678839224],
#           [-75.25635105039267, 38.91920308341379],
#           [-74.03686862851767, 38.91920308341379],
#           [-74.03686862851767, 40.082652678839224]]], None, False);

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01';
# END_DATE = '2024-01-01';

# description = 'Sentinel2_unscaled_NJPB_Trends'
# assetID = 'NJPB_Trends/Sentinel2_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/NJPB_Phenology_Maps/Sentinel2')

# # Turkey Point
# region = ee.Geometry.Polygon(
#         [[[-80.57997293051788, 42.649124560997215],
#           [-80.57997293051788, 42.61988855677763],
#           [-80.5315644222171, 42.61988855677763],
#           [-80.5315644222171, 42.649124560997215]]], None, False)

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01'
# END_DATE = '2024-01-01'

# description = 'Sentinel2_unscaled_Turkey_Point_Trends'
# assetID = 'Turkey_Point_Trends/Sentinel2_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Turkey_Point_Phenology_Maps/Sentinel2')

# # Arnot Forest
# region = ee.Geometry.Polygon(
#         [[[-76.68476578221755, 42.29975344583736],
#           [-76.68476578221755, 42.25466417545956],
#           [-76.60614487157302, 42.25466417545956],
#           [-76.60614487157302, 42.29975344583736]]], None, False)

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01'
# END_DATE = '2024-01-01'

# description = 'Sentinel2_unscaled_Arnot_Forest_Trends'
# assetID = 'Arnot_Forest_Trends/Sentinel2_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Arnot_Forest_Phenology_Maps/Sentinel2')

# Southern Adirondacks
# region = ee.Geometry.Polygon(
#          [[[-74.74286212961913, 43.71354670972063],
#            [-74.74286212961913, 43.109001186493664],
#            [-74.00128498118163, 43.109001186493664],
#            [-74.00128498118163, 43.71354670972063]]], None, False)

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01'
# END_DATE = '2024-01-01'

# description = 'Sentinel2_unscaled_Trends_Phenology'
# assetID = 'Adirondacks_Trends/Sentinel2_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Adirondacks_Phenology_Maps/Sentinel2')

# NJ Pine Barrens
# region = ee.Geometry.Polygon(
#         [[[-75.25635105039267, 40.082652678839224],
#           [-75.25635105039267, 38.91920308341379],
#           [-74.03686862851767, 38.91920308341379],
#           [-74.03686862851767, 40.082652678839224]]], None, False)

# Arnot Forest
# region = ee.Geometry.Polygon(
#         [[[-76.69465224518224, 42.3106617087853],
#           [-76.69465224518224, 42.242582633332354],
#           [-76.61139647735997, 42.242582633332354],
#           [-76.61139647735997, 42.3106617087853]]], None, False)

# Southern Adirondacks
# region = ee.Geometry.Polygon(
#         [[[-74.74286212961913, 43.71354670972063],
#           [-74.74286212961913, 43.109001186493664],
#           [-74.00128498118163, 43.109001186493664],
#           [-74.00128498118163, 43.71354670972063]]], null, false)


START_DATE = '2019-01-01'
END_DATE = '2024-01-01'
START_YEAR = 2019
END_YEAR = 2023

exportRegion = ee.FeatureCollection("FAO/GAUL_SIMPLIFIED_500m/2015/level1").filter(ee.Filter.eq('ADM1_NAME', 'New York'));

pheno_coll = ee.ImageCollection('projects/ee-cjc378/assets/average_phenology_New_York')

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326'; # WGS84 lat lon
dx = 0.75;
dy = 0.75;

# Make grid and visualize.
proj = ee.Projection(projection).scale(dx, dy)
grid = exportRegion.geometry().coveringGrid(proj)

gridSize = grid.size().getInfo()
gridList = grid.toList(gridSize)

assetCollection='projects/ee-cjc378/assets/seasonal_trend_New_York'
imageBaseName='seasonal_trend'

for i in range(gridSize):
  
    gridCell = ee.Feature(gridList.get(i)).geometry()

    #################################
    # Sentinel-2 MSI data preparation
    #################################

    # Cloud Score+ image collection. Note Cloud Score+ is produced from Sentinel-2
    # Level 1C data and can be applied to either L1C or L2A collections.
    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')

    # Use 'cs' or 'cs_cdf', depending on your use case; see docs for guidance.
    QA_BAND = 'cs_cdf'

    # The threshold for masking; values between 0.50 and 0.65 generally work well.
    # Higher values will remove thin clouds, haze & cirrus shadows.
    CLEAR_THRESHOLD = 0.65

    # Load NLCD 2019 landcover map
    nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
        .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')
    
    phenology = pheno_coll.filterBounds(gridCell).mosaic();

    def preprocess(image):
        # New Bands
        image_s = image.divide(10000)
        EVI = image_s.expression(
            '2.5 * ((NIR-RED) / (NIR + 6 * RED - 7.5* BLUE + 1))', {
                'NIR': image_s.select('B8'),
                'RED': image_s.select('B4'),
                'BLUE': image_s.select('B2')
            }).rename('EVI')
        doy = image.date().getRelative('day', 'year').add(1)
        doy_band = ee.Image.constant(doy).uint16().rename('doy')

        # Masks
        forest_mask = nlcd_landcover.gte(41).And(nlcd_landcover.lte(71))
        EVI_mask = EVI.lte(1).And(EVI.gte(0))
        pheno_mask = doy_band.gte(phenology.select('SoS')).And(doy_band.lte(phenology.select('EoS')))
        cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD)


        return (image.addBands(ee.Image([EVI, doy_band]))
                     #.updateMask(forest_mask)
                     .updateMask(EVI_mask)
                     .updateMask(pheno_mask)
                     .updateMask(cloud_mask)
                     .copyProperties(image, ['system:time_start']))

    # Harmonized Sentinel-2 Level 2A collection.
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(gridCell)
            .filterDate(START_DATE, END_DATE)
            .linkCollection(csPlus, [QA_BAND])
            .map(preprocess))


    # Calculate mean and std deviation of the rescaled EVI across all years
    mean = s2.select('EVI').mean()
    std = s2.select('EVI').reduce(ee.Reducer.stdDev())
    # Mask any pixels with EVI_scaled below 1 std of the mean (noise that may interfere with model fitting process)
    s2_scaled = s2.map(lambda image: image.updateMask(image.select('EVI').gte(mean.subtract(std))))


    #################################
    # Theil-Sen model fitting
    #################################

    ss = s2.select(['doy', 'EVI']).reduce(ee.Reducer.sensSlope())


    #################################
    # Submit batch job
    #################################
    imageName = f'{imageBaseName}_tile_{i}'
    task = ee.batch.Export.image.toAsset(
        image            = ss,
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
