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

# New York county boundaries, as specified by FAO Global Administrative Unit Layers
counties = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM1_NAME', 'New York'))

geometry = ee.Geometry.Polygon(
        [[[-79.91201863498242, 43.7092073903781],
          [-79.91201863498242, 41.493793156688646],
          [-78.29702840060742, 41.493793156688646],
          [-78.29702840060742, 43.7092073903781]]], None, False)
geometry2 = ee.Geometry.Polygon(
        [[[-75.74820027560742, 45.02076322621862],
          [-75.74820027560742, 40.18057909211616],
          [-71.65029988498242, 40.18057909211616],
          [-71.65029988498242, 45.02076322621862]]], None, False);

    
##################################################################
# Load defoliation data
##################################################################

threshold = -0.045
nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') \
        .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')
qa_masks = ee.ImageCollection('projects/ee-cjc378/assets/qa_masks_New_York')

for year in [2019, 2020, 2021, 2022, 2023]:
    images = ee.ImageCollection('projects/ee-cjc378/assets/score_denoised_New_York').filter(ee.Filter.eq('year', year))#.filterBounds(geo)
    defol = images.mosaic()
    
    
    qa_mask = qa_masks.mosaic()
    mask = ee.Number(2**15 + 1056*2**(year - 2019)).toUint16()
    qa_mask = qa_mask.bitwiseAnd(mask).eq(mask)
    defol = defol.updateMask(qa_mask).unmask()
    

    # Make sure mosaic has correct projection
    defol = defol.clip(region).reproject(crs='EPSG:32618', scale=1000).reduceResolution(reducer=ee.Reducer.mean(), maxPixels=15000)
    #defol = defol.clip(region).reproject(crs='EPSG:32618', scale=10).reduceResolution(reducer=ee.Reducer.mean(), maxPixels=10000)

    # Intensity maps
    task_upscaled_intensity = ee.batch.Export.image.toDrive(
        image=defol,
        description=f'upscaled_class_{year}_1000',
        folder='Defoliation',
        region=region.geometry(),
        scale=1000,
        crs='EPSG:2829'
    )
    task_upscaled_intensity.start()

#     # Intensity
#     means_intensity = defol.reduceRegions(
#         collection=counties,
#         reducer=ee.Reducer.mean(),
#         crsTransform=[10, 0, 600000, 0, -10, 4700040],
#         crs='EPSG:32618'
#     )
    
#     task_county_intensity = ee.batch.Export.table.toDrive(
#         collection=means_intensity,
#         description=f'counties_intensity_{year}',
#         folder='Defoliation',
#         fileFormat='GeoJSON'
#         #assetId='projects/ee-cjc378/assets/outbreak_centroids/region1',
#     )
#     task_county_intensity.start()