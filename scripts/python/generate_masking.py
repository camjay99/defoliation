##############################################################
# Parse arguments
##############################################################

import argparse
import geometries
import time

parser = argparse.ArgumentParser(
    description='Options for calculating seasonal trends')

# The script will ONLY submit the run when -s or --submit is included.
parser.add_argument('--submit', '-s', action='store_true')

# The project to submit the code in. You may be prompted to to authenticate.
parser.add_argument('--project', '-p', action='store', default=None, required=True)

# The year to create a qa mask for.
parser.add_argument('--year', '-S', action='store', type=int, default=2019)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--geometry', '-g', action='store', default='Mt_Pleasant', choices=geometries.site_names)

# State to calculate defoliation over. If specified, geometry is ignored
parser.add_argument('--state', '-t', action='store', default=None)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--crs', '-c', action='store', default='epsg:5070')

# Parse arguments provided to script
args = parser.parse_args()

##############################################################
# Initialize Google Earth Engine API
##############################################################

import ee       # Google Earth Engine API

try:
    ee.Initialize(project='ee-cjc378')
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize(project='ee-cjc378')

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

##################################################################
# Specify base names and load previous results for small site
##################################################################

if args.state == None:
    description = f'qa_mask_{args.geometry}'
    assetID = f'projects/{args.project}/assets/qa_mask_{args.geometry}/qa_mask_{args.year}'
    geometry = geometries.get_geometry(args.geometry)
else:
    description = f'qa_mask_{args.state.replace(" ", "_")}'
    assetID=f'projects/{args.project}/assets/qa_mask_{args.state.replace(" ", "_")}/qa_mask_{args.year}'
    geometry = geometries.get_state(args.state)

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326'; # WGS84 lat lon
dx = 0.75;
dy = 0.75;

# Make grid and visualize.
proj = ee.Projection(projection).scale(dx, dy)
grid = geometry.coveringGrid(proj)

gridSize = grid.size().getInfo()
gridList = grid.toList(gridSize)

for i in range(gridSize):
  
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

    strong_obs_mask = yearly_obs_mask(args.year, 3)

    weak_obs_mask = yearly_obs_mask(args.year, 2)

    # Preseason max across all years
    ## All years images
    s2_all_years = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(gridCell)
            .filterDate('2019-01-01', '2025-01-01')
            .linkCollection(csPlus, [QA_BAND])
            .map(preprocess));

    preseason_max_all_years = s2_all_years.filter(ee.Filter.dayOfYear(130, 170)).select('EVI').reduce(ee.Reducer.percentile([95]))

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

    preseason_mask = yearly_preseason_mask(args.year)

    # Create forest cover mask
    ## Load NLCD 2019 landcover map
    nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
        .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')
    forest_mask = nlcd_landcover.gte(41).And(nlcd_landcover.lte(43)).toUint16()

    # Combine masks into single image
    qa_mask = ee.Image([forest_mask.rename('forest'),
                        preseason_mask.rename('preseason'),
                        strong_obs_mask.rename('count_3'),
                        weak_obs_mask.rename('count_2')])
    
    # Create Task
    if args.submit:
        if gridSize > 1:
            imageName = f'{assetID}_tile_{i}'
            description = f'{description}_tile_{i}'
        else:
            imageName = assetID
            description = description
            
        task = ee.batch.Export.image.toAsset(
            image            = qa_mask,
            description      = description,
            assetId          = imageName,
            region           = gridCell,
            scale            = 10,
            crs              = args.crs,
            pyramidingPolicy = {'.default': 'mean'},
            maxPixels        = 1e10
        )
        task.start()