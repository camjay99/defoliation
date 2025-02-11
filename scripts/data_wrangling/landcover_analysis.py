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
# Prepare landcover maps
##################################################################

# Load NLCD 2019 landcover map
nlcd_landcover = (ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD')
    .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover'))

# Select deciduous forest
deciduous = nlcd_landcover.eq(41)
# Select evergreen forest
evergreen = nlcd_landcover.eq(42)
# Select mixed forest
mixed = nlcd_landcover.eq(43)


##################################################################
# Create Observation Mask
##################################################################

def generate_obs_mask(year, region):
    year = ee.Number(year)

    # Use 'cs' or 'cs_cdf', depending on your use case; see docs for guidance.
    QA_BAND = 'cs_cdf'

    # The threshold for masking; values between 0.50 and 0.65 generally work well.
    # Higher values will remove thin clouds, haze & cirrus shadows.
    CLEAR_THRESHOLD = 0.65

    def preprocess(image):
        return image.select(QA_BAND).gte(CLEAR_THRESHOLD)

    # Make Observation Mask
    s2 = (ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')
        .filterBounds(region)
        .filterDate(ee.Date.fromYMD(year, 1, 1), ee.Date.fromYMD(year.add(1), 1, 1))
        .filter(ee.Filter.dayOfYear(161, 208))
        .map(preprocess))
    
    obs_mask = s2.sum()
    
    return obs_mask

##################################################################
# Load defoliation data
##################################################################

images = ee.ImageCollection('projects/ee-cjc378/assets/defoliation_score_New_York')


##################################################################
# Specify analysis region
##################################################################

# New York boundaries, as specified by FAO Global Administrative Unit Layers
region = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', 'New York'))

# Tompkins County boundaries, as specified by FAO Global Administrative Unit Layers
#region = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM1_NAME', 'New York')).filter(ee.Filter.eq('ADM2_NAME', 'Tompkins'))


##################################################################
# Use masks to estimate amount of defoliated area in each landcover type
##################################################################

nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
        .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')
forest_mask = nlcd_landcover.gte(41).And(nlcd_landcover.lte(43))

def calculate_counts(images, year, landcover, threshold):
    # Mosaic target year image
    image = images.filter(ee.Filter.eq('year', year)).mosaic()
    image = image.updateMask(forest_mask)
    
    obs_mask = generate_obs_mask(year, region)
    image = image.where(obs_mask.lte(1), 0)
    
    # First, compute the total number of pixels in this landcover type
    total_counts = image.reduceRegions(
                        reducer=ee.Reducer.count().setOutputs(["total"]),
                        collection=region,
                        crsTransform=[10, 0, 600000, 0, -10, 4700040],
                        crs='EPSG:32618')
    
    # Second, compute the number of intense defoliation pixels in this landcover type
    intense_defol = image.lte(threshold)
    defol_counts = intense_defol.reduceRegions(
                                    reducer=ee.Reducer.sum().setOutputs(["intense"]),
                                    collection=total_counts,
                                    crsTransform=[10, 0, 600000, 0, -10, 4700040],
                                    crs='EPSG:32618')
    
    # Update feature to include information about year and landcover
    return defol_counts.map(lambda feature: feature.set({'year':year, 'landcover':landcover}))

years = ee.List([2019, 2020, 2021, 2022, 2023])

# Deciduous forest
defol_deciduous = images.map(lambda image: image.updateMask(deciduous))
count_deciduous = ee.FeatureCollection(years.map(lambda year: calculate_counts(defol_deciduous, year, 'deciduous', -0.045))).flatten()

# Evergreen forest
defol_evergreen = images.map(lambda image: image.updateMask(evergreen))
count_evergreen = ee.FeatureCollection(years.map(lambda year: calculate_counts(defol_evergreen, year, 'evergreen', -0.045))).flatten()

# Mixed forest
defol_mixed = images.map(lambda image: image.updateMask(mixed))
count_mixed = ee.FeatureCollection(years.map(lambda year: calculate_counts(defol_mixed, year, 'mixed', -0.045))).flatten()

counts = count_deciduous.merge(count_evergreen).merge(count_mixed)


#################################
# Submit batch job
#################################

task = ee.batch.Export.table.toDrive(
    collection=counts,
    description='landcover_counts',
    folder='Defoliation',
    fileFormat='CSV',
    selectors=['landcover', 'total', 'intense', 'year']
)

task.start()