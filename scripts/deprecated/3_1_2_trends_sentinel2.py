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

# The first year to look for defoliation signals in.
parser.add_argument('--start', '-S', action='store', default=2019)

# The last year to look for defoliation signals in (inclusive).
parser.add_argument('--end', '-E', action='store', default=2023)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--geometry', '-g', action='store', default='Mt_Pleasant', choices=geometries.site_names)

# State to calculate defoliation over. If specified, geometry is ignored
parser.add_argument('--state', '-t', action='store', default=None)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--crs', '-c', action='store', default='epsg:4326')

# Parse arguments provided to script
args = parser.parse_args()

##############################################################
# Initialize Google Earth Engine API
##############################################################

import ee 

try:
    ee.Initialize(project=args.project)
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize(project=args.project)

##################################################################
# Specify base names and load previous results for small site
##################################################################

if args.state == None:
    description = f'Sentinel2_unscaled_{args.geometry}_Trends'
    assetID = f'projects/{args.project}/assets/{args.geometry}_Trends/Sentinel2_unscaled'
    
    phenology = ee.Image(f'projects/{args.project}/assets/{args.geometry}_Phenology_Maps/Sentinel2')
    
    geometry = geometries.get_geometry(args.geometry)
else:
    description = f'Sentinel2_unscaled_{args.state.replace(" ", "_")}_Trends'
    assetID=f'projects/{args.project}/assets/seasonal_trend_{args.state.replace(" ", "_")}/seasonal_trend'
    
    pheno_coll = ee.ImageCollection(f'projects/{args.project}/assets/average_phenology_{args.state.replace(" ", "_")}')

    geometry = geometries.get_state(args.state)

start_date = ee.Date.fromYMD(args.start, 1, 1)
end_date = ee.Date.fromYMD(args.end+1, 1, 1)

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

    if args.state != None:
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
            .filterDate(start_date, end_date)
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

    if args.submit:
        if gridSize > 1:
            imageName = f'{assetID}_tile_{i}'
        else:
            imageName = assetID
        
        task = ee.batch.Export.image.toAsset(
            image            = ss,
            description      = description,
            assetId          = imageName,
            region           = gridCell, 
            scale            = 10,
            crs              = args.crs,
            pyramidingPolicy = {'.default': 'mean'},
            maxPixels        = 1e10
        )
        time.sleep(0.5)
        task.start()
