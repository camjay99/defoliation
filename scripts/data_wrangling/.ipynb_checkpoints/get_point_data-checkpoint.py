# Collect all the observations for a specified lat/lon point and save them to drive
# This data is used to create Fig. 1
    
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
    
# Load NLCD 2019 landcover map
nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
    .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')

# Update mask based on NLCD landcover classification
def mask_nonforest(image, landcover):
    forest_mask = landcover.gte(41).And(landcover.lte(71))
    return image.updateMask(forest_mask).copyProperties(image, ['system:index', 'system:time_start'])

# Calculate EVI for the scene
def addVegetationIndices(image):
    EVI = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED + 7.5 * BLUE + 1))',
        {
            'NIR': image.select('B8'),
            'RED': image.select('B4'),
            'BLUE': image.select('B2')
        }).rename('EVI')
    
    # Return the masked image with EVI bands.
    return image.addBands(EVI).copyProperties(image, ['system:index', 'system:time_start'])

#
# Function to add doy to an image.
# Modified from https://gis.stackexchange.com/questions/268234/add-a-date-day-of-year-band-to-each-image-in-a-collection-using-google-earth-e
# @param {ee.Image} image Sentinel-2 image
# @return {ee.Image} Sentinel-2 image with doy band
#
def addDOY(image):
    doy = image.date().getRelative('day', 'year')
    doyBand = ee.Image.constant(doy).uint16().rename('doy')
  
    return image.addBands(doyBand).set('doy', doy).copyProperties(image, ['system:index', 'system:time_start']);


##################################################################
# s2cloudless cloud and cloud shadow removing algorithm
##################################################################

def get_s2_sr_cld_col(aoi, start_date, end_date):
    # Import and filter S2 SR.
    s2_sr_col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(aoi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.dayOfYear(1, 300))
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', CLOUD_FILTER)))

    # Import and filter s2cloudless.
    s2_cloudless_col = (ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')
        .filterBounds(aoi)
        .filterDate(start_date, end_date))

    # Join the filtered s2cloudless collection to the SR collection by the 'system:index' property.
    return ee.ImageCollection(ee.Join.saveFirst('s2cloudless').apply(**{
        'primary': s2_sr_col,
        'secondary': s2_cloudless_col,
        'condition': ee.Filter.equals(**{
            'leftField': 'system:index',
            'rightField': 'system:index'
        })
    }))

def add_cloud_bands(img):
    # Get s2cloudless image, subset the probability band.
    cld_prb = ee.Image(img.get('s2cloudless')).select('probability')

    # Condition s2cloudless by the probability threshold value.
    is_cloud = cld_prb.gt(CLD_PRB_THRESH).rename('clouds')

    # Add the cloud probability layer and cloud mask as image bands.
    return img.addBands(ee.Image([cld_prb, is_cloud]))

def add_shadow_bands(img):
    # Identify water pixels from the SCL band.
    not_water = img.select('SCL').neq(6)

    # Identify dark NIR pixels that are not water (potential cloud shadow pixels).
    SR_BAND_SCALE = 1e4
    dark_pixels = img.select('B8').lt(NIR_DRK_THRESH*SR_BAND_SCALE).multiply(not_water).rename('dark_pixels')

    # Determine the direction to project cloud shadow from clouds (assumes UTM projection).
    shadow_azimuth = ee.Number(90).subtract(ee.Number(img.get('MEAN_SOLAR_AZIMUTH_ANGLE')));

    # Project shadows from clouds for the distance specified by the CLD_PRJ_DIST input.
    cld_proj = (img.select('clouds').directionalDistanceTransform(shadow_azimuth, CLD_PRJ_DIST*10)
        .reproject(**{'crs': img.select(0).projection(), 'scale': 100})
        .select('distance')
        .mask()
        .rename('cloud_transform'))

    # Identify the intersection of dark pixels with cloud shadow projection.
    shadows = cld_proj.multiply(dark_pixels).rename('shadows')

    # Add dark pixels, cloud projection, and identified shadows as image bands.
    return img.addBands(ee.Image([dark_pixels, cld_proj, shadows]))

def add_cld_shdw_mask(img):
    # Add cloud component bands.
    img_cloud = add_cloud_bands(img)

    # Add cloud shadow component bands.
    img_cloud_shadow = add_shadow_bands(img_cloud)

    # Combine cloud and shadow mask, set cloud and shadow as value 1, else 0.
    is_cld_shdw = img_cloud_shadow.select('clouds').add(img_cloud_shadow.select('shadows')).gt(0)

    # Remove small cloud-shadow patches and dilate remaining pixels by BUFFER input.
    # 20 m scale is for speed, and assumes clouds don't require 10 m precision.
    is_cld_shdw = (is_cld_shdw.focalMin(2).focalMax(BUFFER*2/20)
        .reproject(**{'crs': img.select([0]).projection(), 'scale': 20})
        .rename('cloudmask'))

    # Add the final cloud-shadow mask to the image.
    return img.updateMask(is_cld_shdw.Not()).copyProperties(img, ['system:index', 'system:time_start'])


##################################################################
# Specify download region and cloud removal parameters
##################################################################

# New York boundaries, as specified by FAO Global Administrative Unit Layers
region = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', 'New York'))

# Tompkins County boundaries, as specified by FAO Global Administrative Unit Layers
#region = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM1_NAME', 'New York')).filter(ee.Filter.eq('ADM2_NAME', 'Tompkins'))


START_DATE = '2019-01-01'
END_DATE = '2024-01-01'
CLOUD_FILTER = 60
CLD_PRB_THRESH = 50
NIR_DRK_THRESH = 0.25
CLD_PRJ_DIST = 1
BUFFER = 40


##################################################################
# MODIS landcover dynamics data
##################################################################

# Identify phenological images for 2019 through 2021 NOTE: CHANGE THIS TO 2022 ONCE DATA IS AVAILABLE?
phen_2019 = ee.ImageCollection('MODIS/061/MCD12Q2') \
                 .filter(ee.Filter.date('2019-01-01', '2020-01-01')).first().subtract(ee.Image(17896)).int()
phen_2020 = ee.ImageCollection('MODIS/061/MCD12Q2') \
                 .filter(ee.Filter.date('2020-01-01', '2021-01-01')).first().subtract(ee.Image(18261)).int()
phen_2021 = ee.ImageCollection('MODIS/061/MCD12Q2') \
                 .filter(ee.Filter.date('2021-01-01', '2022-01-01')).first().subtract(ee.Image(18627)).int()

phenology = ee.ImageCollection([phen_2019, phen_2020, phen_2021]).median()

# Only use images that are reasonably expected to be in the growing season to avoid beginning/end of season noise
def mask_non_growing_season(image):
    doy = image.select('doy')
    maturity_mask = phenology.select('Maturity_1').lt(doy.add(14))
    senescence_mask = phenology.select('Senescence_1').gt(doy.subtract(30))
    return image.updateMask(maturity_mask).updateMask(senescence_mask).copyProperties(image, ['system:index', 'system:time_start'])


##################################################################
# Sentinel-2 MSI data preparation
##################################################################
# Add cloud masks to images
s2_sr_cld_col_eval = get_s2_sr_cld_col(region, START_DATE, END_DATE)
s2_sr_cld_col_eval_disp = s2_sr_cld_col_eval.map(add_cld_shdw_mask)

projection = s2_sr_cld_col_eval_disp.first().select('B2').projection().getInfo()
print(projection['crs'])
print(projection['transform'])

# Setup Sentinel-2 image collection over study region with low(ish) cloud cover and forest landcover
site_images = (s2_sr_cld_col_eval_disp
    .map(lambda image: image.divide(10_000)                       # Rescale band values back into reflectances
            .copyProperties(image, ['system:index', 'system:time_start']))  
    .map(addDOY)                                                  # Add DOY for regression feature.
    .map(lambda image: mask_nonforest(image, nlcd_landcover))     # Mask any region that is definitely not forest
    .map(mask_non_growing_season)                                 # Mask images that are outside of the estimated growing season                    
    .map(addVegetationIndices))                                   # Calculate EVI (currently no other VIs are used)                            

# Mask out points with a total year mean EVI below 0.3,
# as these are likely to be landcovers other than forest
mean_mask = site_images.select('EVI').mean().gt(0.3);
site_images = site_images.map(lambda image: image.updateMask(mean_mask))

# Separate each year, rescale, and only select images in the summer months
max_2019 = site_images.select('EVI').filterDate('2019-01-01', '2020-01-01').max()
site_images_2019 = (site_images.filterDate('2019-01-01', '2020-01-01')
                    .map(lambda image: image.addBands(image.select('EVI').divide(max_2019).rename('EVI_scaled')).copyProperties(image, ['system:index', 'system:time_start'])))
   
max_2020 = site_images.select('EVI').filterDate('2020-01-01', '2021-01-01').max()
site_images_2020 = (site_images.filterDate('2020-01-01', '2021-01-01')
                    .map(lambda image: image.addBands(image.select('EVI').divide(max_2020).rename('EVI_scaled')).copyProperties(image, ['system:index', 'system:time_start'])))
    
max_2021 = site_images.select('EVI').filterDate('2021-01-01', '2022-01-01').max()
site_images_2021 = (site_images.filterDate('2021-01-01', '2022-01-01')
                    .map(lambda image: image.addBands(image.select('EVI').divide(max_2021).rename('EVI_scaled')).copyProperties(image, ['system:index', 'system:time_start'])))
    
max_2022 = site_images.select('EVI').filterDate('2022-01-01', '2023-01-01').max()
site_images_2022 = (site_images.filterDate('2022-01-01', '2023-01-01')
                    .map(lambda image: image.addBands(image.select('EVI').divide(max_2022).rename('EVI_scaled')).copyProperties(image, ['system:index', 'system:time_start'])))

site_images = (site_images_2019.merge(site_images_2020)
                               .merge(site_images_2021)
                               .merge(site_images_2022))


##################################################################
# Load models
##################################################################

new_york_models = ee.Image("projects/ee-cjc378/assets/new_york")


##################################################################
# Get values for a specific point
##################################################################

poi = ee.Geometry.Point([-76.38168370741927,42.469106170531326])

# Adapted from https://spatialthoughts.com/2020/04/13/extracting-time-series-ee/
def get_point_feature(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=poi,
        crsTransform=projection['transform'],
        crs=projection['crs']
      )
    
    # reduceRegion doesn't return any output if the image doesn't intersect
    # with the point or if the image is masked out due to cloud
    # If there was no evi_scaled value found, we set the ndvi to a NoData value -9999
    evi_scaled = (ee.List([stats.get('EVI_scaled'), -9999])
                   .reduce(ee.Reducer.firstNonNull()))
        
    # Create a feature with null geometry and NDVI value and date as properties
    f = ee.Feature(None, {'EVI_scaled': evi_scaled,
                   'date': ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')})
    return f


filtered_images = (site_images.select('EVI_scaled')
                   .filter(ee.Filter.bounds(poi)))
data = ee.FeatureCollection(filtered_images.map(get_point_feature))

model_data = new_york_models.reduceRegions(
    reducer=ee.Reducer.mean(),
    collection=poi,
    crsTransform=projection['transform'],
    crs=projection['crs']
)


#################################
# Submit batch job
#################################

task1 = ee.batch.Export.table.toDrive(
    collection=data,
    description='point_data',
    folder='Defoliation',
    fileFormat='CSV',
    selectors=['date', 'EVI', 'EVI_scaled']
)

task1.start()


task2 = ee.batch.Export.table.toDrive(
    collection=model_data,
    description='point_model_data',
    folder='Defoliation',
    fileFormat='CSV',
    selectors=['slope', 'offset']
)

task2.start()