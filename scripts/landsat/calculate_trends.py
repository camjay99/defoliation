# TODO: Add Landsat based cloud masking
#       Add polygon for analysis

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
# Specify download region and cloud removal parameters
##################################################################

# New York boundaries, as specified by FAO Global Administrative Unit Layers
#region = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', 'New York'))

# Tompkins County boundaries, as specified by FAO Global Administrative Unit Layers
#region = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM1_NAME', 'New York')).filter(ee.Filter.eq('ADM2_NAME', 'Tompkins'))


# # Quabbin Watershed, which experienced extensive defoliation in 2017
# region = ee.Geometry.Polygon([-72.46672740331262,42.27084785748798,
#                               -72.16254344335168,42.27084785748798,
#                               -72.16254344335168,42.47224049291286,
#                               -72.46672740331262,42.47224049291286], None, False)

# # Long time period surrounding year of interest
# START_DATE = '2014-01-01'
# END_DATE = '2021-01-01'

# description = 'Landsat_Quabbin_Trend'
# assetID = 'Quabbin_Trends/Landsat'

# # Load SoS/EoS map
# phenology = ee.Image('projects/ee-cjc378/assets/Quabbin_Phenology_Maps/Landsat')


# # Mt. Pleasant
# region = ee.Geometry.Polygon(
#         [[[-76.40472618414064, 42.48029198346047],
#           [-76.40472618414064, 42.3696708995445],
#           [-76.16963592840334, 42.3696708995445],
#           [-76.16963592840334, 42.48029198346047]]], None, False);

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01'
# END_DATE = '2024-01-01'

# description = 'Landsat_Mt_Pleasant_Trend'
# assetID = 'Mt_Pleasant_Trends/Landsat'

# phenology = ee.Image('projects/ee-cjc378/assets/Mt_Pleasant_Phenology_Maps/Landsat')

# Allegheny
# region = ee.Geometry.Polygon([[[-79.1986092128225, 42.249085326281715],
#                                          [-79.1986092128225, 41.72954071466429],
#                                          [-78.33343587297875, 41.72954071466429],
#                                          [-78.33343587297875, 42.249085326281715]]], None, False)

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01';
# END_DATE = '2024-01-01';

# description = 'Landsat_Allegheny_Trends'
# assetID = 'Allegheny_Trends/Landsat'

# phenology = ee.Image('projects/ee-cjc378/assets/Allegheny_Phenology_Maps/Landsat')

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

# description = 'Landsat_NJPB_Trends'
# assetID = 'NJPB_Trends/Landsat'

# phenology = ee.Image('projects/ee-cjc378/assets/NJPB_Phenology_Maps/Landsat')


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

# description = 'Landsat_Turkey_Point_Trends'
# assetID = 'Turkey_Point_Trends/Landsat'

# phenology = ee.Image('projects/ee-cjc378/assets/Turkey_Point_Phenology_Maps/Landsat')

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

# description = 'Landsat_Arnot_Forest_Trends'
# assetID = 'Arnot_Forest_Trends/Landsat'

# phenology = ee.Image('projects/ee-cjc378/assets/Arnot_Forest_Phenology_Maps/Landsat')

# Southern Adirondacks
region = ee.Geometry.Polygon(
         [[[-74.74286212961913, 43.71354670972063],
           [-74.74286212961913, 43.109001186493664],
           [-74.00128498118163, 43.109001186493664],
           [-74.00128498118163, 43.71354670972063]]], None, False)

START_YEAR = 2019
END_YEAR = 2023
START_DATE = '2019-01-01'
END_DATE = '2024-01-01'

description = 'Landsat_Trends_Phenology'
assetID = 'Adirondacks_Trends/Landsat'

phenology = ee.Image('projects/ee-cjc378/assets/Adirondacks_Phenology_Maps/Landsat')

##################################################################
# Prepare Landsat 7 and 8
##################################################################

def applyScaleFactors(image):
    # Bits 4 and 3 are cloud shadow and cloud, respectively.
    cloudShadowBitMask = 1 << 4
    cloudsBitMask = 1 << 3
    # Get the pixel QA band.
    qa = image.select('QA_PIXEL')
    # Both flags should be set to zero, indicating clear conditions.
    mask = (qa.bitwiseAnd(cloudShadowBitMask).eq(0)
             .And(qa.bitwiseAnd(cloudsBitMask).eq(0)))
        
    
    opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
    return (image.addBands(opticalBands, None, True) 
                 .updateMask(mask).copyProperties(image, ['system:time_start']))

l7 = (ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        .filterBounds(region)
        .filterDate(START_DATE, END_DATE)
        .map(applyScaleFactors))
l8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(region)
        .filterDate(START_DATE, END_DATE)
        .map(applyScaleFactors))


##################################################################
# Harmonize Landsat 7 and 8
##################################################################

def harmonizeL7(image):
    return image.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'],['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2']).copyProperties(image, ['system:time_start'])

def harmonizeL8(image):
    return image.select(['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'],['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2'])

# Map harmonizations and create combined collection
l7 = l7.map(harmonizeL7)
l8 = l8.map(harmonizeL8)

# Combined collection
ls = l7.merge(l8)


##################################################################
# Mask nonforest/off-season and compute NDVI and DOY for each image
##################################################################

# Load NLCD 2019 landcover map
nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
    .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')

# Calculate EVI for the scene
def preprocess(image):
    # New bands
    EVI = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED + 7.5 * BLUE + 1))',
        {
            'NIR': image.select('NIR'),
            'RED': image.select('RED'),
            'BLUE': image.select('BLUE')
        }).rename('EVI')
    
    doy = image.date().getRelative('day', 'year')
    doy_band = ee.Image.constant(doy).uint16().rename('doy')
    
    # Masks
    forest_mask = nlcd_landcover.gte(41).And(nlcd_landcover.lte(71))
    pheno_mask = doy_band.gte(phenology.select('SoS')).And(doy_band.lte(phenology.select('EoS')))
    EVI_mask = EVI.lte(1).And(EVI.gte(0))
    
    # Return the masked image with EVI bands.
    return (image.addBands(ee.Image([EVI, doy_band]))
                 #.updateMask(forest_mask)
                 .updateMask(pheno_mask)
                 .updateMask(EVI_mask)
                 .copyProperties(image, ['system:time_start']))

ls = ls.map(preprocess)

# Mask out points with a mean growing season EVI below 0.3,
# as these are likely to be landcovers other than forest
#mean_mask = ls.select('EVI').mean().gt(0.3);
#ls = ls.map(lambda image: image.updateMask(mean_mask).copyProperties(image, ['system:time_start']))


#################################
# Rescale within each year
#################################                
def rescale(year):
    year = ee.Number(year)
    start = ee.Date.fromYMD(year,1,1)
    end   = ee.Date.fromYMD(year.add(1),1,1)
    year_max = ls.select('EVI').filterDate(start, end).max()
    return (ls.filterDate(start, end)
              .map(lambda image: 
                       image.addBands(
                           image.select('EVI').divide(year_max).rename('EVI_scaled')).copyProperties(image, ['system:time_start'])))

years = ee.List.sequence(START_YEAR, END_YEAR)
ls_scaled = ee.ImageCollection(ee.FeatureCollection(years.map(rescale)).flatten())
# Calculate mean and std deviation of the rescaled EVI across all years
mean = ls_scaled.select('EVI_scaled').mean()
std = ls_scaled.select('EVI_scaled').reduce(ee.Reducer.stdDev())
# Mask any pixels with EVI_scaled below 1 std of the mean (noise that may interfere with model fitting process)
#ls_scaled = ls_scaled.map(lambda image: image.updateMask(image.select('EVI_scaled').gte(mean.subtract(std))).copyProperties(image, ['system:time_start']));


#################################
# Theil-Sen model fitting
#################################

ss = ls_scaled.select(['doy', 'EVI_scaled']).reduce(ee.Reducer.sensSlope())


#################################
# Submit batch job
#################################
task = ee.batch.Export.image.toAsset(
    image            = ss,
    description      = description,
    assetId          = f'projects/ee-cjc378/assets/{assetID}',
    region           = region, 
    scale            = 30,
    crs              = "EPSG:4326",
    pyramidingPolicy = {'.default': 'mean'},
    maxPixels        = 1e10
)
task.start()