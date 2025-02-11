# TODO: Get rid of unnecessary copyProperties
# TODO: Confirm whether doy is 0 indexed or 1 indexed

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
# START_YEAR = 2016
# END_YEAR = 2020
# START_DATE = '2016-01-01'
# END_DATE = '2021-01-01'

# description = 'MODIS_Quabbin_Defol'
# assetID = 'Quabbin_Defoliation/MODIS'

# phenology = ee.Image('projects/ee-cjc378/assets/Quabbin_Phenology_Maps/MODIS')

# models = ee.Image("projects/ee-cjc378/assets/Quabbin_Trends/MODIS")

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

# description = 'MODIS_Mt_Pleasant_Defol'
# assetID = 'Mt_Pleasant_Defoliation/MODIS'

# phenology = ee.Image('projects/ee-cjc378/assets/Mt_Pleasant_Phenology_Maps/MODIS')

# models = ee.Image("projects/ee-cjc378/assets/Mt_Pleasant_Trends/MODIS")

# # Allegheny
# region = ee.Geometry.Polygon([[[-79.1986092128225, 42.249085326281715],
#                                          [-79.1986092128225, 41.72954071466429],
#                                          [-78.33343587297875, 41.72954071466429],
#                                          [-78.33343587297875, 42.249085326281715]]], None, False)
# START_YEAR = 2019
# END_YEAR = 2023
# START_DATE = '2019-01-01';
# END_DATE = '2024-01-01';

# description = 'MODIS_Allegheny_Defoliation'
# assetID = 'Allegheny_Defoliation/MODIS'

# phenology = ee.Image('projects/ee-cjc378/assets/Allegheny_Phenology_Maps/MODIS')

# models = ee.Image("projects/ee-cjc378/assets/Allegheny_Trends/MODIS")

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

# description = 'MODIS_NJPB_Defoliation'
# assetID = 'NJPB_Defoliation/MODIS'

# phenology = ee.Image('projects/ee-cjc378/assets/NJPB_Phenology_Maps/MODIS')

# models = ee.Image("projects/ee-cjc378/assets/NJPB_Trends/MODIS")

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

# description = 'MODIS_Turkey_Point_Defoliaiton'
# assetID = 'Turkey_Point_Defoliation/MODIS'

# phenology = ee.Image('projects/ee-cjc378/assets/Turkey_Point_Phenology_Maps/MODIS')

# models = ee.Image("projects/ee-cjc378/assets/Turkey_Point_Trends/MODIS")

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

# description = 'MODIS_Arnot_Forest_Defoliation'
# assetID = 'Arnot_Forest_Defoliation/MODIS'

# phenology = ee.Image('projects/ee-cjc378/assets/Arnot_Forest_Phenology_Maps/MODIS')

# models = ee.Image("projects/ee-cjc378/assets/Arnot_Forest_Trends/MODIS")

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

description = 'MODIS_Adirondacks_Defoliation'
assetID = 'Adirondacks_Defoliation/MODIS'

phenology = ee.Image('projects/ee-cjc378/assets/Adirondacks_Phenology_Maps/MODIS')

models = ee.Image("projects/ee-cjc378/assets/Adirondacks_Trends/MODIS")

##################################################################
# Prepare MODIS EVI
##################################################################

# Load IGBP MODIS land cover classifications
landcover = (ee.ImageCollection("MODIS/061/MCD12Q1")
                    .select('LC_Type1')
                    .filter(ee.Filter.eq('system:index', '2016_01_01'))
                    .first())

def prepareTimeSeries(image):
    withObs = image.select('num_observations_1km').gt(0)
    QA = image.select('state_1km')
    snowMask = QA.bitwiseAnd(1 << 15).eq(0).rename('snowMask')
    shadowMask = QA.bitwiseAnd(1 << 2).eq(0)
    cloudMask = QA.bitwiseAnd(1 << 10).eq(0)
    cirrusMask1 = QA.bitwiseAnd(1 << 8).eq(0)
    cirrusMask2 = QA.bitwiseAnd(1 << 9).eq(0)
    mask = cirrusMask1.And(cirrusMask2).And(cloudMask).And(shadowMask).And(snowMask)

    EVI = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED + 7.5 * BLUE + 1))',
        {
            'NIR': image.select('sur_refl_b02').divide(10000),
            'RED': image.select('sur_refl_b01').divide(10000),
            'BLUE': image.select('sur_refl_b03').divide(10000)
        }).rename('EVI');
    doy = image.date().getRelative('day', 'year')
    doy_band = ee.Image.constant(doy).uint16().rename('doy')
    
    forest_mask = landcover.gte(1).And(landcover.lte(5))
    pheno_mask = doy_band.gte(phenology.select('SoS')).And(doy_band.lte(phenology.select('EoS')))
    EVI_mask = EVI.lte(1).And(EVI.gte(0))
    mask = mask.And(forest_mask).And(pheno_mask).And(EVI_mask)

    return (image.addBands(ee.Image([EVI, doy_band]))
                 .addBands(image.metadata('system:time_start','date1'))
                 .updateMask(withObs)
                 .updateMask(mask)
                 .copyProperties(image))

TOC = (ee.ImageCollection('MODIS/061/MOD09GQ')
        .linkCollection(ee.ImageCollection("MODIS/061/MOD09GA"), ["num_observations_1km", "state_1km", "sur_refl_b03"])
        .filterDate(START_DATE,END_DATE)
        .map(prepareTimeSeries))


#################################
# Rescale within each year
#################################                
def rescale(year):
    year = ee.Number(year)
    start = ee.Date.fromYMD(year,1,1)
    end   = ee.Date.fromYMD(year.add(1),1,1)
    year_max = TOC.select('EVI').filterDate(start, end).max()
    return (TOC.filterDate(start, end)
              .map(lambda image: 
                       image.addBands(
                           image.select('EVI').divide(year_max).rename('EVI_scaled')).copyProperties(image, ['system:time_start'])))

years = ee.List.sequence(START_YEAR, END_YEAR)
TOC_scaled = ee.ImageCollection(ee.FeatureCollection(years.map(rescale)).flatten())


######################################
# Estimate defoliation in given window
######################################

# Calculate anomaly
def calc_anom(image):
    slope = models.select('slope')
    offset = models.select('offset')
    doy = image.select('doy')
    predict = slope.multiply(doy).add(offset)
    anom = image.select('EVI_scaled').subtract(predict)
    
    return image.addBands(anom.rename('EVI_scaled_anom'))

def calc_statistics(images): 
    images = images.map(calc_anom)

    # Main defol calculation 
    mean_intensity = images.select("EVI_scaled_anom").filter(ee.Filter.dayOfYear(161, 208)).mean().rename("mean_intensity")

    # Defol timing estimates
    intense_observation = images.map(lambda image: image.updateMask(image.select('EVI_scaled_anom').lte(-0.1)))
    ## Start date
    start_date = intense_observation.select('doy').min().rename("start_date")

    ## End date
    end_date = intense_observation.select('doy').max().rename("end_date")

    ## Mid date
    mid_date = end_date.add(start_date).divide(2).rename("mid_date")
    
    ## Peak date
    peak_date = intense_observation.qualityMosaic('EVI_scaled_anom').select('doy').rename('peak_date')

    # Quality Mask (how to incorporate logging into this?)
    # quality_mask = images.select("EVI").count().gt(4).rename("quality_mask")

    defol = ee.Image([mean_intensity, start_date, end_date, mid_date, peak_date])
    
    return defol.set('method', 'MODIS')


#################################
# Submit batch job
#################################

for year in range(START_YEAR, END_YEAR+1):
    defol = calc_statistics(TOC_scaled.filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year+1, 1, 1))).set('system:index', str(year))

    task = ee.batch.Export.image.toAsset(
        image            = defol,
        description      = f'{description}_{year}',
        assetId          = f'projects/ee-cjc378/assets/{assetID}_{year}',
        region           = region, 
        scale            = 250,
        crs              = "EPSG:4326",
        pyramidingPolicy = {'.default': 'mean'},
        maxPixels        = 1e10
    )
    task.start()