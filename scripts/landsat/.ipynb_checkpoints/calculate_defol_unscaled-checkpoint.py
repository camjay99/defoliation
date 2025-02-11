##############################################################
# Parse arguments
##############################################################

import argparse

parser = argparse.ArgumentParser(
    description='Options for calculating defoliation')

# The script will ONLY submit the run when -s or --submit is included.
parser.add_argument('--submit', '-s', action='store_true')

# The first year to look for defoliation signals in.
parser.add_argument('--start', '-S', action='store', default=2019)

# The last year to look for defoliation signals in (inclusive).
parser.add_argument('--end', '-E', action='store', default=2023)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--geometry', '-g', action = 'store', default = 'Mt_Pleasant')

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--crs', '-c', action = 'store', default = 'epsg:4326')

# Parse arguments provided to script
args = parser.parse_args()

##############################################################
# Initialize Google Earth Engine API
##############################################################

import ee 

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
# START_YEAR = 2014
# END_YEAR = 2020
# START_DATE = '2014-01-01'
# END_DATE = '2021-01-01'

# description = 'Landsat_unscaled_Quabbin_Trend'
# assetID = 'Quabbin_Defoliation/Landsat_unscaled'

# # Load SoS/EoS map
# phenology = ee.Image('projects/ee-cjc378/assets/Quabbin_Phenology_Maps/Landsat')

# models = ee.Image("projects/ee-cjc378/assets/Quabbin_Trends/Landsat_unscaled")


# # Mt Pleasant
# region = ee.Geometry.Polygon(
#         [[[-76.40472618414064, 42.48029198346047],
#           [-76.40472618414064, 42.3696708995445],
#           [-76.16963592840334, 42.3696708995445],
#           [-76.16963592840334, 42.48029198346047]]], None, False);

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01'
# END_DATE = '2024-01-01'

# description = 'Landsat_unscaled_Mt_Pleasant_Defol'
# assetID = 'Mt_Pleasant_Defoliation/Landsat_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Mt_Pleasant_Phenology_Maps/Landsat')

# models = ee.Image("projects/ee-cjc378/assets/Mt_Pleasant_Trends/Landsat_unscaled")

# # Allegheny
# region = ee.Geometry.Polygon([[[-79.1986092128225, 42.249085326281715],
#                                          [-79.1986092128225, 41.72954071466429],
#                                          [-78.33343587297875, 41.72954071466429],
#                                          [-78.33343587297875, 42.249085326281715]]], None, False)
# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01';
# END_DATE = '2024-01-01';

# description = 'Landsat_unscaled_Allegheny_Defoliation'
# assetID = 'Allegheny_Defoliation/Landsat_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Allegheny_Phenology_Maps/Landsat')

# models = ee.Image("projects/ee-cjc378/assets/Allegheny_Trends/Landsat_unscaled")

# # New Jersey Pine Barrens
# region = ee.Geometry.Polygon(
#         [[[-75.25635105039267, 40.082652678839224],
#           [-75.25635105039267, 38.91920308341379],
#           [-74.03686862851767, 38.91920308341379],
#           [-74.03686862851767, 40.082652678839224]]], None, False)

# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01'
# END_DATE = '2024-01-01'

# description = 'Landsat_unscaled_NJPB_Defoliation'
# assetID = 'NJPB_Defoliation/Landsat_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/NJPB_Phenology_Maps/Landsat')

# models = ee.Image("projects/ee-cjc378/assets/NJPB_Trends/Landsat_unscaled")

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

# description = 'Landsat_unscaled_Turkey_Point_Defoliaiton'
# assetID = 'Turkey_Point_Defoliation/Landsat_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Turkey_Point_Phenology_Maps/Landsat')

# models = ee.Image("projects/ee-cjc378/assets/Turkey_Point_Trends/Landsat_unscaled")

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

# description = 'Landsat_unscaled_Arnot_Forest_Defoliation'
# assetID = 'Arnot_Forest_Defoliation/Landsat_unscaled'

# phenology = ee.Image('projects/ee-cjc378/assets/Arnot_Forest_Phenology_Maps/Landsat')

# models = ee.Image("projects/ee-cjc378/assets/Arnot_Forest_Trends/Landsat_unscaled")

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

description = 'Landsat_unscaled_Adirondacks_Defoliation'
assetID = 'Adirondacks_Defoliation/Landsat_unscaled'

phenology = ee.Image('projects/ee-cjc378/assets/Adirondacks_Phenology_Maps/Landsat')

models = ee.Image("projects/ee-cjc378/assets/Adirondacks_Trends/Landsat_unscaled")

##################################################################
# Prepare Landsat 7 and 8
##################################################################

start_date = ee.Date.fromYMD(args.start, 1, 1)
end_date = ee.Date.fromYMD(args.end + 1, 1, 1)

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
        .filterDate(start_date, end_date)
        .map(applyScaleFactors))
l8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(region)
        .filterDate(start_date, end_date)
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
                 .updateMask(EVI_mask).copyProperties(image, ['system:time_start']))

ls = ls.map(preprocess)

######################################
# Estimate defoliation in given window
######################################

# Calculate anomaly
def calc_anom(image):
    slope = models.select('slope')
    offset = models.select('offset')
    doy = image.select('doy')
    predict = slope.multiply(doy).add(offset)
    anom = image.select('EVI').subtract(predict)
    
    return image.addBands(anom.rename('EVI_anom'))

def calc_statistics(images): 
    images = images.map(calc_anom)

    # Main defol calculation 
    mean_intensity = images.select("EVI_anom").filter(ee.Filter.dayOfYear(161, 208)).mean().rename("mean_intensity")


    # Defol timing estimates
    intense_observation = images.map(lambda image: image.updateMask(image.select('EVI_anom').lte(-0.1)))
    ## Start date
    start_date = intense_observation.select('doy').min().rename("start_date")

    ## End date
    end_date = intense_observation.select('doy').max().rename("end_date")

    ## Mid date
    mid_date = end_date.add(start_date).divide(2).rename("mid_date")
    
    ## Peak date
    peak_date = intense_observation.qualityMosaic('EVI_anom').select('doy').rename('peak_date')

    # Quality Mask (how to incorporate logging into this?)
    #quality_mask = images.select("EVI").count().gt(4).rename("quality_mask")

    defol = ee.Image([mean_intensity, start_date, end_date, mid_date, peak_date])
    
    return defol.set('method', 'Landsat_unscaled')


#################################
# Submit batch job
#################################

if args.submit:
    for year in range(args.start, args.end+1):
        defol = calc_statistics(ls.filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year+1, 1, 1))).set('system:index', str(year))

        task = ee.batch.Export.image.toAsset(
            image            = defol,
            description      = f'{description}_{year}',
            assetId          = f'projects/ee-cjc378/assets/{assetID}_{year}',
            region           = region, 
            scale            = 30,
            crs              = args.crs,
            pyramidingPolicy = {'.default': 'mean'},
            maxPixels        = 1e10
        )
        task.start()