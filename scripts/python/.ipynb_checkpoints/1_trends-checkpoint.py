import argparse

import ee

import geometries
import preprocessing


##############################################################
# Parse arguments
##############################################################

parser = argparse.ArgumentParser(
    description='Options for calculating seasonal trends')

# The script will ONLY submit the run when -s or --submit is included.
parser.add_argument('--submit', '-s', action='store_true')

# The project to submit the code in. 
# You may be prompted to to authenticate.
parser.add_argument('--project', '-p', action='store', 
                    default=None, required=True)

# The first and last years to look for defoliation signals in (inclusive).
parser.add_argument('--start', '-S', action='store', type=int, default=2019)
parser.add_argument('--end', '-E', action='store', type=int, default=2023)

# The data source to use for calculating trends.
parser.add_argument('--data', '-d', action='store', 
                    default='Sentinel2', choices=preprocessing.sources)

# The geometry to calculate trends within. 
# A list of valid geometries are available in scripts/geometries.py
parser.add_argument('--geometry', '-g', action='store', 
                    default='Mt_Pleasant', choices=geometries.site_names)

# State to calculate trends within.
parser.add_argument('--state', '-x', action='store', 
                    default=None)

# The crs to use for the output
parser.add_argument('--crs', '-c', action='store', default='epsg:5070')

# The width/length of grid cells to use for computation (in lat/lon degrees)
parser.add_argument('--width', '-w', action='store', type=int, default=0.75)
parser.add_argument('--length', '-l', action='store', type=int, default=0.75)

# Rescale within each year to minimize interannual variability
parser.add_argument('--rescale', '-r', action='store_true')

# Parse arguments provided to script
args = parser.parse_args()


##############################################################
# Initialize Google Earth Engine API
##############################################################

try:
    ee.Initialize(project=args.project)
except:
    # need to authenticate with your credential at the first time
    ee.Authenticate()
    ee.Initialize(project=args.project)


##################################################################
# Specify base names and load previous results
##################################################################

if args.state == None:
    name = args.geometry
    geometry = geometry = geometries.get_geometry(args.geometry)
else:
    name = args.state.replace(" ", "_")
    geometry = geometries.get_state(name)

description_base = f'{name}_Trends_{args.data}'
assetID=f'projects/{args.project}/assets/seasonal_trend_{name}/seasonal_trend_{args.data}'
if args.rescale:
    assetID += '_rescaled'
    description_base += '_rescaled'
pheno_coll = ee.ImageCollection(f'projects/{args.project}/assets/average_phenology_{name}')


##################################################################
# Split study regions into grid cells of specified size.
##################################################################

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326'; # WGS84 lat lon

# Make grid and visualize.
proj = ee.Projection(projection).scale(args.width, args.length)
grid = geometry.coveringGrid(proj)

gridSize = grid.size().getInfo()
gridList = grid.toList(gridSize)

for i in range(gridSize):
    gridCell = ee.Feature(gridList.get(i)).geometry()

    ##################################################################
    # Prepare Data
    ##################################################################

    phenology = pheno_coll.filterBounds(gridCell).mosaic()

    start_date = ee.Date.fromYMD(args.start, 1, 1)
    end_date = ee.Date.fromYMD(args.end + 1, 1, 1)

    if args.data == 'Landsat':
        col = preprocessing.preprocess_Landsat(start_date, end_date,
                                               gridCell, phenology)
    elif args.data == 'MODIS':
        col = preprocessing.preprocess_MODIS(start_date, end_date,
                                             gridCell, phenology)
    elif args.data == 'Sentinel2':
        col = preprocessing.preprocess_Sentinel2(start_date, end_date,
                                                 gridCell, phenology)

    if args.rescale:
        col = preprocessing.rescale_years(col, args.start, args.end)


    #################################
    # Theil-Sen model fitting
    #################################

    ss = col.reduce(ee.Reducer.sensSlope())
    ss = (ss.set('method', 'Theil-Sen')
            .set('source', args.data)
            .set('rescaled', args.rescale)
            .set('start', args.start)
            .set('end', args.end))

    #################################
    # Submit batch job
    #################################

    if args.submit:
        if gridSize > 1:
            imageName = f'{assetID}_tile_{i}'
            description = f'{description_base}_tile_{i}'
        else:
            imageName = assetID
            description = description_base

        task = ee.batch.Export.image.toAsset(
            image=ss,
            description=description,
            assetId=imageName,
            region=gridCell, 
            scale=preprocessing.resolutions[args.data],
            crs=args.crs,
            pyramidingPolicy={'.default': 'mean'},
            maxPixels=1e10
        )
        task.start()