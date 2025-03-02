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
parser.add_argument('--year', '-S', action='store',  type=int, default=2019)

# State to calculate defoliation over.
parser.add_argument('--state', '-t', action='store', default='New York')

# The CRS to output the resulting layers in.
parser.add_argument('--crs', '-c', action='store', default='epsg:5070')

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

##############################################################
# Divide Study Region
##############################################################

description = f'Sentinel2_unscaled_{args.state.replace(" ", "_")}_Denoised'
assetID = f'projects/{args.project}/assets/score_denoised_{args.state.replace(" ", "_")}/score_denoised_{args.year}'
defol_coll = ee.ImageCollection(f'projects/{args.project}/assets/defoliation_score_{args.state.replace(" ", "_")}').filter(ee.Filter.eq('year', args.year))
geometry = geometries.get_state(args.state)

# Assemble mask
qa_masks = ee.ImageCollection('projects/ee-cjc378/assets/qa_masks_New_York')
year_masks = {2019:1056, 2020:2144, 2021:4320, 2022:8672, 2023:17376}
mask_value = ee.Number(2).pow(15).add(ee.Number(year_masks[args.year])).toUint16()
qa = qa_masks.mosaic()
qa_mask = qa.bitwiseAnd(mask_value).eq(mask_value)

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

    ###############################################################################
    # Create buffer around region to ensure accurate denoising at grid cell edges
    ###############################################################################
    
    gridCell = ee.Feature(gridList.get(i)).geometry()
    gridCellBuffer = gridCell.buffer(distance=400)
    
    defol_gridCell = defol_coll.filterBounds(gridCellBuffer).mosaic().clip(gridCellBuffer)
    class_gridCell = (defol_gridCell.lte(-0.040)
                                    .updateMask(qa_mask))

    ################################################
    # Remove pixels that are part of small patches
    ################################################

    groups_gridCell = class_gridCell.connectedPixelCount(15, False)
    too_small = groups_gridCell.lte(10)
    
    groups_denoised = class_gridCell.And(too_small.Not()).toUint8()
    
    groups_denoised = groups_denoised.set('year', args.year)
    
    #################################
    # Submit batch job
    #################################

    if args.submit:
        imageName = f'{assetID}_tile_{i}'
        task = ee.batch.Export.image.toAsset(
            image            = groups_denoised,
            description      = f'{description}_tile_{i}',
            assetId          = imageName,
            region           = gridCell, 
            scale            = 10,
            crs              = args.crs,
            pyramidingPolicy = {'.default': 'mean'},
            maxPixels        = 1e10
        )
        time.sleep(0.5)
        task.start()
