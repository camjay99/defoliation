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

# The year to look for defoliation signals in.
parser.add_argument('--year', '-S', action='store', type=int, default=2019)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--geometry', '-g', action='store', default='Mt_Pleasant', choices=geometries.site_names)

# State to calculate defoliation over. If specified, geometry is ignored
parser.add_argument('--state', '-t', action='store', default=None)

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--crs', '-c', action='store', default='epsg:5070')

# The period to calculate the deviation over
parser.add_argument('--period', '-P', action='store', default='all_year', choices=['all_year', 'summer', 'growing_season'])

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
    description = f'Sentinel2_harmonic_{args.geometry}_Defoliation'
    assetID = f'projects/{args.project}/assets/{args.geometry}_Defoliation/Sentinel2_harmonic_{args.year}_{args.period}'
    models = (ee.ImageCollection(f'projects/{args.project}/assets/{args.geometry}_Trends')
              .filter(ee.Filter.eq('method', 'harmonic'))
              .mosaic())
    geometry = geometries.get_geometry(args.geometry)
else:
    description = f'Sentinel2_harmonic_{args.state.replace(" ", "_")}_Defoliation'
    assetID=f'projects/{args.project}/assets/defoliation_score_{args.state.replace(" ", "_")}/defoliation_score_harmonic_{args.year}_{args.period}'
    model_coll = (ee.ImageCollection(f'projects/{args.project}/assets/seasonal_trend_{args.state.replace(" ", "_")}')
                  .filter(ee.Filter.eq('method', 'harmonic')))
    geometry = geometries.get_state(args.state)

start_date = ee.Date.fromYMD(args.year, 1, 1)
end_date = ee.Date.fromYMD(args.year+1, 1, 1)

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326'; # WGS84 lat lon
dx = 1;
dy = 1;

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
    
    # Get phenology and models for relevant cell
    if args.state != None:
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

        days = image.date().difference(start_date, 'days')
        days_band = ee.Image(days).toFloat().rename('days')

        # Masks
        EVI_mask = EVI.lte(1).And(EVI.gte(0))
        cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD)

        return (image.addBands(ee.Image([EVI, days_band]))
                     .updateMask(EVI_mask)
                     .updateMask(cloud_mask)
                     .copyProperties(image, ['system:time_start']))

    # Harmonized Sentinel-2 Level 2A collection.
    s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
            .filterBounds(gridCell)
            .filterDate(start_date, end_date)
            .linkCollection(csPlus, [QA_BAND])
            .map(preprocess))

    ######################################
    # Estimate defoliation in given window
    ######################################

    # Calculate anomaly
    def calc_anom(image):
        predict = ee.Image().expression(
          'constant + a*doy + a_1*sin(2*pi/365.25*doy) + b_1*cos(2*pi/365.25*doy) + a_3*sin(3*2*pi/365.25*doy) + b_3*cos(3*2*pi/365.25*doy)',
          {'constant': models.select('constant_EVI'),
           'a': models.select('doy_EVI'),
           'a_1': models.select('sin_12_EVI'),
           'b_1': models.select('cos_12_EVI'),
           'a_3': models.select('sin_4_EVI'),
           'b_3': models.select('cos_4_EVI'),
           'doy': image.select('days'),
           'pi': ee.Image(3.14159265359)
          })

        anom = image.select('EVI').subtract(predict)

        return image.addBands(anom.rename('EVI_anom'))

    def calc_statistics(images): 
        # TO ADD: control on this
        ## In the original paper, Valerie et al used the whole year of anomalies. I will include that as well as only the focus period
        images = images.map(calc_anom)
        if args.period == 'summer':
            mean_intensity = images.select("EVI_anom").filter(ee.Filter.dayOfYear(161, 208)).mean().rename('mean_intensity').set('period', 'summer')
        elif args.period == 'all_year':
            mean_intensity = images.select("EVI_anom").mean().rename('mean_intensity').set('period', 'all_year')
        else:
            mean_intensity = images.select("EVI_anom").filter(ee.Filter.dayOfYear(121, 273)).mean().rename('mean_intensity').set('period', 'growing_season')

        return mean_intensity.set('method', 'harmonic').set('year', args.year)

    #################################
    # Submit batch job
    #################################

    if args.submit:
        defol = calc_statistics(s2.filterDate(start_date, end_date))
        
        if gridSize > 1:
            imageName = f'{assetID}_tile_{i}'
        else:
            imageName = assetID

        task = ee.batch.Export.image.toAsset(
            image            = defol,
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