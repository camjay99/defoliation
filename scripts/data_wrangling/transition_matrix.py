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
    
transitions = []
for year in [2019, 2020, 2021, 2022]:
    ##################################################################
    # Load defoliation data
    ##################################################################
    
    qa_masks = ee.ImageCollection('projects/ee-cjc378/assets/qa_masks_New_York').mosaic()
    mask_curr = ee.Number(2).pow(ee.Number(year).subtract(2019)).multiply(33).add(32768).toUint16()
    mask_next = ee.Number(2).pow(ee.Number(year+1).subtract(2019)).multiply(33).add(32768).toUint16()
    qa_masks_marked_curr = qa_masks.bitwiseAnd(mask_curr).eq(mask_curr)
    qa_masks_marked_next = qa_masks.bitwiseAnd(mask_next).eq(mask_next)

    scores_curr = (ee.ImageCollection('projects/ee-cjc378/assets/score_denoised_New_York')
                   .filter(ee.Filter.eq('year', year))
                   .mosaic()
                   .updateMask(qa_masks_marked_curr))
    scores_next = (ee.ImageCollection('projects/ee-cjc378/assets/score_denoised_New_York')
                   .filter(ee.Filter.eq('year', year+1))
                   .mosaic()
                   .updateMask(qa_masks_marked_next))


    ##################################################################
    # Specify analysis region
    ##################################################################

    # New York boundaries, as specified by FAO Global Administrative Unit Layers
    region = ee.FeatureCollection('FAO/GAUL/2015/level1').filter(ee.Filter.eq('ADM1_NAME', 'New York'))


    ##################################################################
    # Classify by defoliation intensity
    ##################################################################

    # Classification Threshold for Defoliation
    thresh = -0.045

    # Calculate points below each threshold
    ## Current
    defol_curr = scores_curr
    clear_curr = ee.Image(1).subtract(defol_curr)

    ## Next
    defol_next = scores_next
    clear_next = ee.Image(1).subtract(defol_next)

    # Compute next year changes
    clear_to_clear = clear_curr.And(clear_next)
    clear_to_defol = clear_curr.And(defol_next)

    defol_to_clear = defol_curr.And(clear_next)
    defol_to_defol = defol_curr.And(defol_next)


    ##################################################################
    # Reduce to compute each transition area
    ##################################################################

    def reduce_to_transition_count(image, from_state, to_state, year):
        result = image.reduceRegions(
            collection=region,
            reducer=ee.Reducer.sum(),
            scale=10,
            crs='EPSG:32618',
        ).map(lambda feature: feature.set({'from':from_state, 'to':to_state, 'year':year}))

        return result

    transitions.append(reduce_to_transition_count(clear_to_clear, 'clear', 'clear', year))
    transitions.append(reduce_to_transition_count(clear_to_defol, 'clear', 'defol', year))
    transitions.append(reduce_to_transition_count(defol_to_clear, 'defol', 'clear', year))
    transitions.append(reduce_to_transition_count(defol_to_defol, 'defol', 'defol', year))

#################################
# Submit batch job
#################################
transitions_coll = ee.FeatureCollection(transitions).flatten()
task = ee.batch.Export.table.toDrive(
    collection=transitions_coll,
    description=f'transition_data',
    folder='defoliation',
    selectors=['from', 'to', 'year', 'sum']
    #assetId='projects/ee-cjc378/assets/outbreak_centroids/region1',
)
task.start()
