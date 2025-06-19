##############################################################
# Imports Packages
##############################################################

import ee       # Google Earth Engine API

try:
    ee.Initialize(project='ee-cjc378')
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize(project='ee-cjc378')

    
##################################################################
# Specify analysis region
##################################################################

# New York boundaries, as specified by FAO Global Administrative Unit Layers
region = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', 'New York'))


##################################################################
# Helper functions
##################################################################
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
    EVI_mask = EVI.lte(1).And(EVI.gte(0))
    cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD)

    return (image.addBands(ee.Image([EVI, doy_band]))
                 .updateMask(EVI_mask)
                 .updateMask(cloud_mask)
                 .set('doy', doy)
                 .copyProperties(image, ['system:time_start']))

def combine_masks(current_element, previous_result):
    previous_result = ee.Image(previous_result)
    return previous_result.leftShift(1).add(current_element)


##################################################################
# Create Observation Mask
##################################################################

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326'; # WGS84 lat lon
dx = 1.5;
dy = 1.5;

# Make grid and visualize.
proj = ee.Projection(projection).scale(dx, dy)
grid = region.geometry().coveringGrid(proj)

gridSize = grid.size().getInfo()
gridList = grid.toList(gridSize)

for i in range(gridSize):
    # Initialize gri cell region
    gridCell = ee.Feature(gridList.get(i)).geometry()
    
    # Cloud mask parameters
    csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
    QA_BAND = 'cs_cdf'
    CLEAR_THRESHOLD = 0.65
    
    # Create yearly observation mask
    def yearly_obs_mask(year, threshold):
        year = ee.Date.fromYMD(year, 1, 1)
        # Collect observations
        obs = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(gridCell)
            .filterDate(year, year.advance(1, 'year'))
            .filter(ee.Filter.dayOfYear(161, 208))
            .linkCollection(csPlus, [QA_BAND])
            .map(lambda image: image.select(QA_BAND).gte(CLEAR_THRESHOLD).copyProperties(image, ['system:time_start'])))
        
        # Combine days with multipe observations
        withDates = obs.map(lambda image: image.set('date', image.date().format('YYYY-MM-dd')))

        mosaicList = (withDates.aggregate_array('date')
            .distinct()
            .map(lambda date: obs.filterDate(ee.Date(date), ee.Date(date).advance(1, 'day')).max()))
             
        obs_counts = (ee.ImageCollection.fromImages(mosaicList)
            .sum()
            .gte(threshold)
            .toUint16()
            .unmask(0))
        
        return obs_counts
    
    years = ee.List([2023, 2022, 2021, 2020, 2019])
    strong_obs_masks = years.map(lambda year: yearly_obs_mask(year, 3))
    combined_strong_obs_mask = ee.Image(strong_obs_masks.iterate(combine_masks, ee.Image(0)))

    weak_obs_masks = years.map(lambda year: yearly_obs_mask(year, 2))
    combined_weak_obs_mask = ee.Image(weak_obs_masks.iterate(combine_masks, ee.Image(0)))
    
    # Preseason max across all years
    ## All years images
    s2_all_years = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(gridCell)
            .filterDate('2019-01-01', '2024-01-01')
            .linkCollection(csPlus, [QA_BAND])
            .map(preprocess));
    
    preseason_max_all_years = s2_all_years.filter(ee.Filter.dayOfYear(140, 160)).select('EVI').reduce(ee.Reducer.percentile([95]))
    
    ## Create yearly preseason mask
    def yearly_preseason_mask(year):
        year = ee.Date.fromYMD(year, 1, 1)
        # Target Year Images
        s2 = s2_all_years.filterDate(year, year.advance(1, 'year'))
        
        preseason_max_target = s2.filter(ee.Filter.dayOfYear(130, 170)).select('EVI').reduce(ee.Reducer.percentile([95]))
        preseason_max_count = s2.filter(ee.Filter.dayOfYear(130, 170)).select('EVI').reduce(ee.Reducer.count()).eq(0).unmask(0)
        s2_pre_max_gap = preseason_max_target.subtract(preseason_max_all_years).gte(-0.3).unmask(0)

        # Ensure we have large gap and observtions to base this on.
        return s2_pre_max_gap.Or(preseason_max_count).toUint16()
    
    preseason_masks = years.map(yearly_preseason_mask)
    combined_preseason_mask = ee.Image(preseason_masks.iterate(combine_masks, ee.Image(0)))

    # Currently not doing post-season masking, instead use space for two levels of obs masks.
    # # Postseason max across all years
    # postseason_max_all_years = s2_all_years.filter(ee.Filter.dayOfYear(220, 250)).select('EVI').reduce(ee.Reducer.percentile([95]))
    
    # ## Create yearly postseason mask
    # def yearly_postseason_mask(year):
    #     year = ee.Date.fromYMD(year, 1, 1)
    #     # Target Year Images
    #     s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    #             .filterBounds(gridCell)
    #             .filterDate(year, year.advance(1, 'year'))
    #             .linkCollection(csPlus, [QA_BAND])
    #             .map(preprocess))
        
    #     postseason_max_target = s2.filter(ee.Filter.dayOfYear(220, 250)).select('EVI').reduce(ee.Reducer.percentile([95]))
    #     s2_post_max_gap = postseason_max_target.subtract(postseason_max_all_years)
    #     return s2_post_max_gap.gte(-0.15).toUint16().unmask(0)
    
    # postseason_masks = years.map(yearly_postseason_mask)
    # combined_postseason_mask = ee.Image(postseason_masks.iterate(combine_masks, ee.Image(0)))
    
    # Create forest cover mask
    ## Load NLCD 2019 landcover map
    nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
        .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')
    forest_mask = nlcd_landcover.gte(41).And(nlcd_landcover.lte(43)).toUint16()
    
    
    # Combine masks into single layer
    qa_mask = (forest_mask.leftShift(15)
        .add(combined_strong_obs_mask.leftShift(10))
        .add(combined_preseason_mask.leftShift(5))
        .add(combined_weak_obs_mask))
    
    # Create Task
    task = ee.batch.Export.image.toAsset(
        image            = qa_mask,
        description      = f'qa_mask_{i}',
        assetId          = f'projects/ee-cjc378/assets/qa_masks_New_York/qa_mask_{i}',
        region           = gridCell, 
        scale            = 10,
        crs              = "EPSG:4326",
        pyramidingPolicy = {'.default': 'mean'},
        maxPixels        = 1e10
    )
    task.start()