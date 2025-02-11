# TODO: Would replacing scale with a crs_transform improve the accuracy of the vectors?

##############################################################
# Imports Packages
##############################################################

import ee       # Google Earth Engine API

try:
    ee.Initialize()
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize()
    

##################################################################
# Load defoliation data
##################################################################

defol = ee.Image('projects/ee-cjc378/assets/defol_maps/new_york_2021')


##################################################################
# Specify analysis region
##################################################################

# New York boundaries, as specified by FAO Global Administrative Unit Layers
region = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', 'New York'))

# Tompkins County boundaries, as specified by FAO Global Administrative Unit Layers
#region = ee.FeatureCollection('FAO/GAUL/2015/level2').filter(ee.Filter.eq('ADM1_NAME', 'New York')).filter(ee.Filter.eq('ADM2_NAME', 'Tompkins'))

# Regions for separating computations to avoid overfilling cache on aggregation. 
# Broad regions are for initial calculations, 
# narrow are for only keeping results that we are confident didn't go over a border
region1_broad = ee.Geometry.Polygon(
    [-79.78587396577127, 41.36957212690531,
     -78.01707513764627, 41.36957212690531,
     -78.01707513764627, 43.51367897739807,
     -79.78587396577127, 43.51367897739807], None, False)
region1_broad = region.geometry().intersection(region1_broad, maxError=1)
region1_narrow = ee.Geometry.Polygon(
    [-79.78587396577127, 41.36957212690531,
     (-78.01707513764627 + -78.13847370348948) / 2, 41.36957212690531,
     (-78.01707513764627 + -78.13847370348948) / 2, 43.51367897739807,
     -79.78587396577127, 43.51367897739807], None, False)

region2_broad = ee.Geometry.Polygon(
    [-78.13847370348948, 41.40129040756422,
     -76.58390827380198, 41.401290407564221,
     -76.58390827380198, 43.50848394983187,
     -78.13847370348948, 43.50848394983187], None, False)
region2_broad = region.geometry().intersection(region2_broad, maxError=1)
region2_narrow = ee.Geometry.Polygon(
    [(-78.01707513764627 + -78.13847370348948) / 2, 41.40129040756422,
     (-76.58390827380198 + -76.7102188911893) / 2, 41.401290407564221,
     (-76.58390827380198 + -76.7102188911893) / 2, 43.50848394983187,
     (-78.01707513764627 + -78.13847370348948) / 2, 43.50848394983187], None, False)

region3_broad = ee.Geometry.Polygon(
    [-76.7102188911893, 41.399715867396841,
     -75.1611466255643, 41.39971586739684,
     -75.1611466255643, 45.00581982446029,
     -76.7102188911893, 45.00581982446029], None, False)
region3_broad = region.geometry().intersection(region3_broad, maxError=1)
region3_narrow = ee.Geometry.Polygon(
    [(-76.58390827380198 + -76.7102188911893) / 2, 41.399715867396841,
     (-75.1611466255643 + -75.29179501850531) / 2, 41.39971586739684,
     (-75.1611466255643 + -75.29179501850531) / 2, 45.00581982446029,
     (-76.58390827380198 + -76.7102188911893) / 2, 45.00581982446029], None, False)

region4_broad = ee.Geometry.Polygon(
    [-75.29179501850531, 41.0481078945499,
     -74.17668271381781, 41.0481078945499,
     -74.17668271381781, 45.04813090009772,
     -75.29179501850531, 45.04813090009772], None, False)
region4_broad = region.geometry().intersection(region4_broad, maxError=1)
region4_narrow = ee.Geometry.Polygon(
    [(-75.1611466255643 + -75.29179501850531) / 2, 41.0481078945499,
     (-74.17668271381781 + -74.30812088394482) / 2, 41.0481078945499,
     (-74.17668271381781 + -74.30812088394482) / 2, 45.04813090009772,
     (-75.1611466255643 + -75.29179501850531) / 2, 45.04813090009772], None, False)

region5_broad = ee.Geometry.Polygon(
    [-74.30812088394482, 40.38695828853123,
     -73.31385818863232, 40.38695828853123,
     -73.31385818863232, 45.05666725552293,
     -74.30812088394482, 45.05666725552293], None, False)
region5_broad = region.geometry().intersection(region5_broad, maxError=1)
region5_narrow = ee.Geometry.Polygon(
    [(-74.17668271381781 + -74.30812088394482) / 2, 40.38695828853123,
     (-73.31385818863232 + -73.48829167128224) / 2, 40.38695828853123,
     (-73.31385818863232 + -73.48829167128224) / 2, 45.05666725552293,
     (-74.17668271381781 + -74.30812088394482) / 2, 45.05666725552293], None, False)

region6_broad = ee.Geometry.Polygon(
    [-73.48829167128224, 40.311153037773096,
     -71.43934147596974, 40.311153037773096,
     -71.43934147596974, 41.33371472187358,
     -73.48829167128224, 41.33371472187358], None, False)
region6_broad = region.geometry().intersection(region6_broad, maxError=1)
region6_narrow = ee.Geometry.Polygon(
    [(-73.31385818863232 + -73.48829167128224) / 2, 40.311153037773096,
     -71.43934147596974, 40.311153037773096,
     -71.43934147596974, 41.33371472187358,
     (-73.31385818863232 + -73.48829167128224) / 2, 41.33371472187358], None, False)


##################################################################
# Calculate size of regions larger than threshold
##################################################################

threshold = -0.2

# Mark regions lower than threshold
intense_defol = defol.select('mean_intensity').lte(threshold)

# Count number of adjacent defoliation pixels
boundaries = intense_defol.reduceNeighborhood(
    ee.Reducer.sum(),
    ee.Kernel.plus(radius=1, normalize=False)
)

# Calculate the number of adjecent non-defoliation pixels
boundaries = ee.Image(5).subtract(boundaries).multiply(intense_defol).rename('boundaries')

# Append new bands for reducer
intense_defol = intense_defol.addBands(boundaries)

# Reduce to vector, then filter results to valid region.
# This needs to be done for a set of subregions to ensure that feature collections are small enough for aggregation.
## Region 1
intense_vectors_region1 = (
        intense_defol.reduceToVectors(
            reducer=ee.Reducer.count().combine(ee.Reducer.sum(), sharedInputs=True),
            geometry=region1_broad,
            geometryType='centroid',
            scale=10,
            crs="EPSG:32618",
            maxPixels=1e10,
        ).map(lambda feature: feature.set({'year':intense_defol.get('year')})))
intense_vectors_region1 = intense_vectors_region1.filterBounds(region1_narrow)

## Region 2
intense_vectors_region2 = (
        intense_defol.reduceToVectors(
            reducer=ee.Reducer.count().combine(ee.Reducer.sum(), sharedInputs=True),
            geometry=region2_broad,
            geometryType='centroid',
            scale=10,
            crs="EPSG:32618",
            maxPixels=1e10,
        ).map(lambda feature: feature.set({'year':intense_defol.get('year')})))
intense_vectors_region2 = intense_vectors_region2.filterBounds(region2_narrow)

## Region 3
intense_vectors_region3 = (
        intense_defol.reduceToVectors(
            reducer=ee.Reducer.count().combine(ee.Reducer.sum(), sharedInputs=True),
            geometry=region3_broad,
            geometryType='centroid',
            scale=10,
            crs="EPSG:32618",
            maxPixels=1e10,
        ).map(lambda feature: feature.set({'year':intense_defol.get('year')})))
intense_vectors_region3 = intense_vectors_region3.filterBounds(region3_narrow)

## Region 4
intense_vectors_region4 = (
        intense_defol.reduceToVectors(
            reducer=ee.Reducer.count().combine(ee.Reducer.sum(), sharedInputs=True),
            geometry=region4_broad,
            geometryType='centroid',
            scale=10,
            crs="EPSG:32618",
            maxPixels=1e10,
        ).map(lambda feature: feature.set({'year':intense_defol.get('year')})))
intense_vectors_region4 = intense_vectors_region4.filterBounds(region4_narrow)

## Region 5
intense_vectors_region5 = (
        intense_defol.reduceToVectors(
            reducer=ee.Reducer.count().combine(ee.Reducer.sum(), sharedInputs=True),
            geometry=region5_broad,
            geometryType='centroid',
            scale=10,
            crs="EPSG:32618",
            maxPixels=1e10,
        ).map(lambda feature: feature.set({'year':intense_defol.get('year')})))
intense_vectors_region5 = intense_vectors_region5.filterBounds(region5_narrow)

## Region 6
intense_vectors_region6 = (
        intense_defol.reduceToVectors(
            reducer=ee.Reducer.count().combine(ee.Reducer.sum(), sharedInputs=True),
            geometry=region6_broad,
            geometryType='centroid',
            scale=10,
            crs="EPSG:32618",
            maxPixels=1e10,
        ).map(lambda feature: feature.set({'year':intense_defol.get('year')})))
intense_vectors_region6 = intense_vectors_region6.filterBounds(region6_narrow)

#################################
# Submit batch job
#################################

task1 = ee.batch.Export.table.toAsset(
    collection=intense_vectors_region1,
    description='outbreak_centroids',
    #folder='defoliation'
    assetId='projects/ee-cjc378/assets/outbreak_centroids/region1',
)
task1.start()

task2 = ee.batch.Export.table.toAsset(
    collection=intense_vectors_region2,
    description='outbreak_centroids',
    #folder='defoliation'
    assetId='projects/ee-cjc378/assets/outbreak_centroids/region2',
)
task2.start()

task3 = ee.batch.Export.table.toAsset(
    collection=intense_vectors_region3,
    description='outbreak_centroids',
    #folder='defoliation'
    assetId='projects/ee-cjc378/assets/outbreak_centroids/region3',
)
task3.start()

task4 = ee.batch.Export.table.toAsset(
    collection=intense_vectors_region4,
    description='outbreak_centroids',
    #folder='defoliation'
    assetId='projects/ee-cjc378/assets/outbreak_centroids/region4',
)
task4.start()

task5 = ee.batch.Export.table.toAsset(
    collection=intense_vectors_region5,
    description='outbreak_centroids',
    #folder='defoliation'
    assetId='projects/ee-cjc378/assets/outbreak_centroids/region5',
)
task5.start()

task6 = ee.batch.Export.table.toAsset(
    collection=intense_vectors_region6,
    description='outbreak_centroids',
    #folder='defoliation'
    assetId='projects/ee-cjc378/assets/outbreak_centroids/region6',
)
task6.start()