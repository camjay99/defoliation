##############################################################
# Parse arguments
##############################################################

import argparse
import geometries

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

description = f'MODIS_unscaled_{args.geometry}_Phenology'
assetID = f'projects/{args.project}/assets/{args.geometry}_Trends/MODIS_unscaled'

phenology = ee.Image(f'projects/{args.project}/assets/{args.geometry}_Phenology_Maps/MODIS')

geometry = geometries.get_geometry(args.geometry)

##################################################################
# Prepare MODIS EVI
##################################################################

start_date = ee.Date.fromYMD(args.start, 1, 1)
end_date = ee.Date.fromYMD(args.end + 1, 1, 1)

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
        .filterDate(start_date, end_date)
        .map(prepareTimeSeries))


#################################
# Theil-Sen model fitting
#################################

ss = TOC.select(['doy', 'EVI']).reduce(ee.Reducer.sensSlope()).set('method', 'MODIS_unscaled')

#################################
# Submit batch job
#################################

if args.submit:
    task = ee.batch.Export.image.toAsset(
        image            = ss,
        description      = description,
        assetId          = assetID,
        region           = geometry, 
        scale            = 250,
        crs              = args.crs,
        pyramidingPolicy = {'.default': 'mean'},
        maxPixels        = 1e10
    )
    task.start()