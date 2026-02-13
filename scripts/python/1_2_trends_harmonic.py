import argparse
import time

import ee 

import geometries

##############################################################
# Parse arguments
##############################################################

parser = argparse.ArgumentParser(
    description='Options for calculating seasonal trends')

# The script will ONLY submit the run when -s or --submit is included.
parser.add_argument('--submit', '-s', action='store_true')

# The project to submit the code in. You may be prompted to to authenticate.
parser.add_argument('--project', '-p', action='store', default=None, required=True)

# The first year to look for defoliation signals in.
parser.add_argument('--start', '-S', action='store', type=int, default=2019)

# The last year to look for defoliation signals in (inclusive).
parser.add_argument('--end', '-E', action='store', type=int, default=2023)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--geometry', '-g', action='store', default='Mt_Pleasant', choices=geometries.site_names)

# State to calculate defoliation over. If specified, geometry is ignored
parser.add_argument('--state', '-t', action='store', default=None)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--crs', '-c', action='store', default='epsg:5070')

# The width/length of grid cells to use for computation (in lat/lon degrees)
parser.add_argument('--width', '-w', action='store', type=float, default=0.75)
parser.add_argument('--length', '-l', action='store', type=float, default=0.75)

# Parse arguments provided to script
args = parser.parse_args()

##############################################################
# Initialize Google Earth Engine API
##############################################################

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
    description = f'Sentinel2_harmonic_{args.geometry}_Trends'
    assetID = f'projects/{args.project}/assets/{args.geometry}_Trends/Sentinel2_harmonic'
    geometry = geometries.get_geometry(args.geometry)
else:
    description = f'Sentinel2_harmonic_{args.state.replace(" ", "_")}_Trends'
    assetID=f'projects/{args.project}/assets/seasonal_trend_{args.state.replace(" ", "_")}/harmonic_trend'
    geometry = geometries.get_state(args.state)

start_date = ee.Date.fromYMD(args.start, 1, 1)
end_date = ee.Date.fromYMD(args.end+1, 1, 1)

##################################################################
# Split study regions into grid cells of specified size.
##################################################################

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326'; # WGS84 lat lon

# Make grid and visualize.
proj = ee.Projection(projection).scale(args.width, args.length)
grid = geometry.coveringGrid(proj)

gridSize = grid.size().getInfo()
gridList = grid.toList(gridSize)

for i in range(gridSize):
    gridCell = ee.Feature(gridList.get(i)).geometry()

    ##################################################################
    # Prepare Data
    ##################################################################

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

    def preprocess(image):
        # New Bands
        image_s = image.divide(10000)
        EVI = image_s.expression(
            '2.5 * ((NIR-RED) / (NIR + 6 * RED - 7.5* BLUE + 1))', {
                'NIR': image_s.select('B8'),
                'RED': image_s.select('B4'),
                'BLUE': image_s.select('B2')
            }).rename('EVI')
        
        days = image.date().difference(start_date, 'days')
        days_band = ee.Image(days).toFloat().rename('days')
        
        # Bands for model fitting
        constant = ee.Image(1)
        sin_12 = ee.Image(days.multiply(2*3.14159265359/365.25).sin()).toFloat().rename('sin_12')
        cos_12 = ee.Image(days.multiply(2*3.14159265359/365.25).cos()).toFloat().rename('cos_12')
        sin_4 = ee.Image(days.multiply(3*2*3.14159265359/365.25).sin()).toFloat().rename('sin_4')
        cos_4 = ee.Image(days.multiply(3*2*3.14159265359/365.25).cos()).toFloat().rename('cos_4')

        features = ee.Image([constant, days_band, sin_12, cos_12, sin_4, cos_4, EVI])

        # Masks
        EVI_mask = EVI.lte(1).And(EVI.gte(0))
        cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD)

        return (features.updateMask(EVI_mask)
                        .updateMask(cloud_mask)
                        .copyProperties(image, ['system:time_start']))

    # Harmonized Sentinel-2 Level 2A collection.
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(gridCell)
            .filterDate(start_date, end_date)
            .linkCollection(csPlus, [QA_BAND])
            .map(preprocess))

    #################################
    # Harmonic model fitting
    #################################
    
    models = (s2.reduce(ee.Reducer.linearRegression(6, 1))
                .select(['coefficients'])
                .arrayFlatten([['constant', 'doy', 'sin_12', 'cos_12', 'sin_4', 'cos_4'], ['EVI']]))

    models = models.set('method', 'harmonic')

    #################################
    # Submit batch job
    #################################

    if args.submit:
        if gridSize > 1:
            imageName = f'{assetID}_tile_{i}'
        else:
            imageName = assetID
        
        task = ee.batch.Export.image.toAsset(
            image            = models,
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
