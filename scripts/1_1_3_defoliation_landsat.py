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
# Specify base names and load previous results
##################################################################

description = f'Landsat_unscaled_{args.geometry}_Defoliation'
assetID = f'projects/{args.project}/assets/{args.geometry}_Defoliation/Landsat_unscaled'

phenology = ee.Image(f'projects/{args.project}/assets/{args.geometry}_Phenology_Maps/Landsat')
models = ee.Image(f'projects/{args.project}/assets/{args.geometry}_Trends/Landsat_unscaled')

geometry = geometries.get_geometry(args.geometry)

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
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .map(applyScaleFactors))
l8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(geometry)
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
    mean_intensity = images.select("EVI_anom").filter(ee.Filter.dayOfYear(161, 208)).mean().rename("mean_intensity")
    
    return mean_intensity.set('method', 'Landsat_unscaled').set('year', year)

#################################
# Submit batch job
#################################

if args.submit:
    for year in range(args.start, args.end+1):
        defol = calc_statistics(ls.filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year+1, 1, 1))).set('system:index', str(year))

        task = ee.batch.Export.image.toAsset(
            image            = defol,
            description      = f'{description}_{year}',
            assetId          = f'{asset_ID}_{year}',
            region           = geometry, 
            scale            = 30,
            crs              = args.crs,
            pyramidingPolicy = {'.default': 'mean'},
            maxPixels        = 1e10
        )
        task.start()