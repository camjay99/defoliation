##############################################################
# Parse arguments
##############################################################

import argparse
import geometries

parser = argparse.ArgumentParser(
    description='Options for calculating defoliation')

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

# The geomtry to calculate defoliation within. A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--crs', '-c', action='store', default='epsg:4326')

# Parse arguments provided to script
args = parser.parse_args()

##############################################################
# Specify base names and load previous results
##############################################################

import ee 

try:
    ee.Initialize(project=args.project)
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize(project=args.project)

##################################################################
# Specify download region and cloud removal parameters
##################################################################

description = f'Sentinel2_{args.geometry}_Defoliation'
assetID = f'projects/{args.project}/assets/{args.geometry}_Defoliation/Sentinel2'

phenology = ee.Image(f'projects/{args.project}/assets/{args.geometry}_Phenology_Maps/Sentinel2')
models = ee.Image(f'projects/{args.project}/assets/{args.geometry}_Trends/Sentinel2')

geometry = geometries.get_geometry(args.geometry)

#################################
# Sentinel-2 MSI data preparation
#################################

start_date = ee.Date.fromYMD(args.start, 1, 1)
end_date = ee.Date.fromYMD(args.end + 1, 1, 1)

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
    
    doy = image.date().getRelative('day', 'year')
    doy_band = ee.Image.constant(doy).uint16().rename('doy')
    
    # Masks
    EVI_mask = EVI.lte(1).And(EVI.gte(0))
    pheno_mask = doy_band.gte(phenology.select('SoS')).And(doy_band.lte(phenology.select('EoS')))
    cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD)
    
    return (image.addBands(ee.Image([EVI, doy_band]))
                 .updateMask(EVI_mask)
                 .updateMask(pheno_mask)
                 .updateMask(cloud_mask)
                 .copyProperties(image, ['system:time_start']))
    
# Harmonized Sentinel-2 Level 2A collection.
s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .linkCollection(csPlus, [QA_BAND])
        .map(preprocess))

#################################
# Rescale within each year
#################################    

def rescale(year):
    year = ee.Number(year)
    start = ee.Date.fromYMD(year,1,1)
    end   = ee.Date.fromYMD(year.add(1),1,1)
    year_max = s2.select('EVI').filterDate(start, end).max()
    return (s2.filterDate(start, end)
              .map(lambda image: 
                       image.addBands(
                           image.select('EVI').divide(year_max).rename('EVI_scaled')).copyProperties(image, ['system:time_start'])))

years = ee.List.sequence(START_YEAR, END_YEAR)
s2_scaled = ee.ImageCollection(ee.FeatureCollection(years.map(rescale)).flatten())

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
    mean_intensity = images.select("EVI_scaled_anom").filter(ee.Filter.dayOfYear(161, 208)).mean().rename("mean_intensity")
    
    return mean_intensity.set('method', 'Sentinel2').set('year', year)

#################################
# Submit batch job
#################################

if args.submit:
    for year in range(args.start, args.end+1):
        defol = calc_statistics(s2_scaled.filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year+1, 1, 1))).set('system:index', str(year))
    
        task = ee.batch.Export.image.toAsset(
            image            = defol,
            description      = f'{description}_{year}',
            assetId          = f'{assetID}_{year}',
            region           = geometry, 
            scale            = 10,
            crs              = args.crs,
            pyramidingPolicy = {'.default': 'mean'},
            maxPixels        = 1e10
        )
    task.start()