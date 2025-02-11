# For a given region, save defoliation image, composite of image in defol time frame, 
# composite before and after defol time frame, and time series of mean observations and std dev
# This data is used to create Fig. 2

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
# Preprocessing functions for each image in scene
##################################################################

pheno_coll = ee.ImageCollection('projects/ee-cjc378/assets/average_phenology_New_York')
model_coll = ee.ImageCollection('projects/ee-cjc378/assets/seasonal_trend_New_York')
qa_masks = ee.ImageCollection('projects/ee-cjc378/assets/qa_masks_New_York')

# Cloud Score+ image collection. Note Cloud Score+ is produced from Sentinel-2
# Level 1C data and can be applied to either L1C or L2A collections.
csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')

# Use 'cs' or 'cs_cdf', depending on your use case; see docs for guidance.
QA_BAND = 'cs_cdf'

# The threshold for masking; values between 0.50 and 0.65 generally work well.
# Higher values will remove thin clouds, haze & cirrus shadows.
CLEAR_THRESHOLD = 0.65

qa_mask = qa_masks.mosaic()
mask = ee.Number(2**15 + 1056*2**(year - 2019)).toUint16()
qa_mask = qa_mask.bitwiseAnd(mask).eq(mask)

# Get phenology and models for relevant cell
phenology = pheno_coll.filterBounds(gridCell).mosaic();
models = model_coll.filterBounds(gridCell).mosaic();

def preprocess(image):
    # New Bands
    image_s = image.divide(10000)
    EVI = image_s.expression(
        '2.5 * ((NIR-RED) / (NIR + 6 * RED - 7.5* BLUE + 1))', {
            'NIR': image_s.select('B8'),
            'RED': image_s.select('B4'),
            'BLUE': image_s.select('B2')
        }).rename('EVI')

    doy = image.date().getRelative('day', 'year')
    doy_band = ee.Image.constant(doy).uint16().rename('doy')

    # Masks
    EVI_mask = EVI.lte(1).And(EVI.gte(0))
    pheno_mask = doy_band.gte(phenology.select('SoS')).And(doy_band.lte(phenology.select('EoS')))
    cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD)


    return (image.addBands(ee.Image([EVI, doy_band]))
                 #.updateMask(forest_mask)
                 .updateMask(EVI_mask)
                 .updateMask(pheno_mask)
                 .updateMask(cloud_mask)
                 .updateMask(qa_mask)
                 .copyProperties(image, ['system:time_start']))

# Harmonized Sentinel-2 Level 2A collection.
s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(gridCell)
        .filterDate(START_DATE, END_DATE)
        .linkCollection(csPlus, [QA_BAND])
        .map(preprocess))

##################################################################
# Specify download region and cloud removal parameters
##################################################################

mt_pleasant = ee.Geometry.Polygon(
    [-76.38845246824344, 42.46436087095481,
     -76.37167256864628, 42.46436087095481,
     -76.37167256864628, 42.47417424877469,
     -76.38845246824344, 42.47417424877469], None, False)

positive_sample = ee.Geometry.Polygon(
    [-76.41623453360863,42.41051611482946,
     -76.37769655448265,42.41051611482946,
     -76.37769655448265,42.430158205380344,
     -76.41623453360863,42.430158205380344], None, False)

negative_sample = ee.Geometry.Polygon(
    [-74.62383683191842,43.046694487257746,
     -74.61315091120309,43.046694487257746,
     -74.61315091120309,43.05230810581971,
     -74.62383683191842,43.05230810581971], None, False)

region = ee.FeatureCollection([mt_pleasant, positive_sample, negative_sample]).union(1)

START_DATE = '2020-01-01'
END_DATE = '2022-01-01'
CLOUD_FILTER = 60
CLD_PRB_THRESH = 50
NIR_DRK_THRESH = 0.25
CLD_PRJ_DIST = 1
BUFFER = 40


##################################################################
# Sentinel-2 MSI data preparation
##################################################################
# Add cloud masks to images
s2_sr_cld_col_eval = get_s2_sr_cld_col(region, START_DATE, END_DATE)
s2_sr_cld_col_eval_disp = s2_sr_cld_col_eval.map(add_cld_shdw_mask)

# Setup Sentinel-2 image collection over study region with low(ish) cloud cover and forest landcover
site_images = (s2_sr_cld_col_eval_disp
    .map(lambda image: image.divide(10_000)                       # Rescale band values back into reflectances
            .copyProperties(image, ['system:index', 'system:time_start']))  
    .map(addDOY)                                                  # Add DOY for regression feature.
    .map(lambda image: mask_nonforest(image, nlcd_landcover))     # Mask any region that is definitely not forest
    .map(mask_non_growing_season)                                 # Mask images that are outside of the estimated growing season                    
    .map(addVegetationIndices))                                   # Calculate EVI (currently no other VIs are used)     


##################################################################
# Downlaod previous year median image
##################################################################

median_2020 = site_images.filterDate('2020-01-01', '2021-01-01').filter(ee.Filter.calendarRange(161, 208, 'day_of_year')).median()

task1_mt_pleasant = ee.batch.Export.image.toDrive(
    image=median_2020.select(['B4', 'B3', 'B2']),
    description='mt_pleasant_normal',
    folder='Defoliation',
    region=mt_pleasant,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task1_mt_pleasant.start()

task1_positive = ee.batch.Export.image.toDrive(
    image=median_2020.select(['B4', 'B3', 'B2']),
    description='positive_normal',
    folder='Defoliation',
    region=positive_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task1_positive.start()

task1_negative = ee.batch.Export.image.toDrive(
    image=median_2020.select(['B4', 'B3', 'B2']),
    description='negative_normal',
    folder='Defoliation',
    region=negative_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task1_negative.start()


##################################################################
# Downlaod defoliation image
##################################################################

defol = ee.Image('projects/ee-cjc378/assets/defol_maps/new_york_2021').select('mean_intensity')

task2_mt_pleasant = ee.batch.Export.image.toDrive(
    image=defol,
    description='mt_pleasant_defol',
    folder='Defoliation',
    region=mt_pleasant,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task2_mt_pleasant.start()

task2_positive = ee.batch.Export.image.toDrive(
    image=defol,
    description='positive_defol',
    folder='Defoliation',
    region=positive_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task2_positive.start()

task2_negative = ee.batch.Export.image.toDrive(
    image=defol,
    description='negative_defol',
    folder='Defoliation',
    region=negative_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task2_negative.start()


##################################################################
# Download median image
##################################################################

median_2021 = site_images.filterDate('2021-01-01', '2022-01-01').filter(ee.Filter.calendarRange(161, 208, 'day_of_year')).median()

task3_mt_pleasant = ee.batch.Export.image.toDrive(
    image=median_2021.select(['B4', 'B3', 'B2']),
    description='mt_pleasant_median',
    folder='Defoliation',
    region=mt_pleasant,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task3_mt_pleasant.start()

task3_positive = ee.batch.Export.image.toDrive(
    image=median_2021.select(['B4', 'B3', 'B2']),
    description='positive_median',
    folder='Defoliation',
    region=positive_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task3_positive.start()

task3_negative = ee.batch.Export.image.toDrive(
    image=median_2021.select(['B4', 'B3', 'B2']),
    description='negative_median',
    folder='Defoliation',
    region=negative_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618'
)
task3_negative.start()


##################################################################
# Identify and download main defoliation region
##################################################################

threshold = -0.2

# Mark regions lower than threshold
intense_defol = defol.select('mean_intensity').lte(threshold)
intense_defol = intense_defol.updateMask(intense_defol).addBands(ee.Image(1))

vector_mt_pleasant = ee.Feature(intense_defol.reduceToVectors(
    reducer=ee.Reducer.count(),
    geometry=mt_pleasant,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618',
    maxPixels=1e10
).sort('count', False).first())

task4_mt_pleasant = ee.batch.Export.table.toDrive(
    collection=ee.FeatureCollection(vector_mt_pleasant),
    description='mt_pleasant_vector',
    folder='Defoliation',
    fileFormat='SHP'
)
task4_mt_pleasant.start()


vector_positive = ee.Feature(intense_defol.reduceToVectors(
    reducer=ee.Reducer.count(),
    geometry=positive_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618',
    maxPixels=1e10
).sort('count', False).first())

task4_positive = ee.batch.Export.table.toDrive(
    collection=ee.FeatureCollection(vector_positive),
    description='positive_vector',
    folder='Defoliation',
    fileFormat='SHP'
)
task4_positive.start()


vector_negative = ee.Feature(intense_defol.reduceToVectors(
    reducer=ee.Reducer.count(),
    geometry=negative_sample,
    crsTransform=[10, 0, 600000, 0, -10, 4700040],
    crs='EPSG:32618',
    maxPixels=1e10
).sort('count', False).first())

task4_negative = ee.batch.Export.table.toDrive(
    collection=ee.FeatureCollection(vector_negative),
    description='negative_vector',
    folder='Defoliation',
    fileFormat='SHP'
)
task4_negative.start()


##################################################################
# Download Mean + std of EVI
##################################################################

def get_mean_std(image, region):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(),sharedInputs=True),
        geometry=region,
        crsTransform=[10, 0, 600000, 0, -10, 4700040],
        crs='EPSG:32618'
    )
    
    f = ee.Feature(None, {'EVI_mean':stats.get('EVI_mean'), 'EVI_std':stats.get('EVI_stdDev'),
                          'date':ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')})
    
    return f

region_obs_mt_pleasant = site_images.select('EVI').map(lambda x: get_mean_std(x, mt_pleasant))

task5_mt_pleasant = ee.batch.Export.table.toDrive(
    collection=region_obs_mt_pleasant,
    description='mt_pleasant_mean_obs',
    folder='Defoliation',
    fileFormat='CSV'
)
task5_mt_pleasant.start()


region_obs_positive = site_images.select('EVI').map(lambda x: get_mean_std(x, positive_sample))

task5_positive = ee.batch.Export.table.toDrive(
    collection=region_obs_positive,
    description='positive_mean_obs',
    folder='Defoliation',
    fileFormat='CSV'
)
task5_positive.start()


region_obs_negative = site_images.select('EVI').map(lambda x: get_mean_std(x, negative_sample))

task5_negative = ee.batch.Export.table.toDrive(
    collection=region_obs_negative,
    description='negative_mean_obs',
    folder='Defoliation',
    fileFormat='CSV'
)
task5_negative.start()