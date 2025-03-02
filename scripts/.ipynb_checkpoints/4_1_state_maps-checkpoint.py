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

# The first year to generate a map for.
parser.add_argument('--start', '-S', action='store', type=int, default=2019)

# The last year to generate a map for.
parser.add_argument('--end', '-E', action='store', type=int, default=2023)

# State to generate a map for.
parser.add_argument('--state', '-t', action='store', default='New York')

# Scale (in meters) for the resulting map.
parser.add_argument('--scale', '-u', action='store', type=int, default=250)

# Google Drive folder to save result in.
parser.add_argument('--folder', '-f', action='store', default='Defoliation')

# The CRS to output the resulting layers in. Should be a projected to system to properly make sense of scale argument.
parser.add_argument('--crs', '-c', action='store', default='epsg:2629')

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
# Specify analysis region
##################################################################

description = f'Generate_{args.state.replace(" ", "_")}_Maps_{args.scale}m'
fileName = f'{args.state.replace(" ", "_")}_mean_defoliated_area_{args.scale}m'

geometry = geometries.get_state(args.state)
denoised_coll = ee.ImageCollection(f'projects/{args.project}/assets/score_denoised_{args.state.replace(" ", "_")}')
qa_masks = ee.ImageCollection(f'projects/{args.project}/assets/qa_masks_{args.state.replace(" ", "_")}')
    
##################################################################
# Load defoliation data
##################################################################

for year in range(args.start, args.end+1):
    images = denoised_coll.filter(ee.Filter.eq('year', year))
    defol = images.mosaic()

    # TO DO: Create a separate masking function to facilitate scaling to other time periods/regions
    qa_mask = qa_masks.mosaic()
    mask = ee.Number(2**15 + 1056*2**(year - 2019)).toUint16()
    qa_mask = qa_mask.bitwiseAnd(mask).eq(mask)
    defol = defol.updateMask(qa_mask).unmask()
    

    # Make sure mosaic has correct projection. In the future, update process to only use projected systems and to properly apply pyramiding to avoid having to do this.
    defol = defol.clip(geometry).reproject(crs=args.crs, scale=args.scale).reduceResolution(reducer=ee.Reducer.mean(), maxPixels=15000)

    if args.submit:
        task_upscaled_intensity = ee.batch.Export.image.toDrive(
            image         = defol,
            description   = f'{fileName}_{year}',
            folder        = args.folder,
            region        = geometry,
            scale         = args.scale,
            crs           = args.crs
        )
        task_upscaled_intensity.start()