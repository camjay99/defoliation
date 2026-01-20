import argparse

import ee

import geometries
import preprocessing


##############################################################
# Parse arguments
##############################################################

parser = argparse.ArgumentParser(
    description='Options for calculating growing season')

# The script will ONLY submit the run when -s or --submit is included.
parser.add_argument('--submit', '-s', action='store_true')

# The project to submit the code in. 
# You may be prompted to to authenticate.
parser.add_argument('--project', '-p', action='store', 
                    default=None, required=True)

# The first and last years to look for calculating average phenology.
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
parser.add_argument('--state', '-x', action='store', default=None)

# The crs to use for the output
parser.add_argument('--crs', '-c', action='store', default='epsg:5070')

# The width/length of grid cells to use for computation (in lat/lon degrees)
parser.add_argument('--width', '-w', action='store', type=int, default=0.75)
parser.add_argument('--length', '-l', action='store', type=int, default=0.75)

### Algorithm parameters
# Window size for calculating mean before/after conditions
parser.add_argument('--change_window', '-c', action='store', type=int, default=30)

# Threshold for initial binary classification
parser.add_argument('--threshold', '-t', action='store', type=int, default=30)

# Window size for smoothing data series
parser.add_argument('--smooth_window', '-W', action='store', type=int, default=30)

# Spacing between days of year evaluated as a potential change point
# Increasing the value will make the algorithm run faster at the
# expense of lower fidelity in change dates
parser.add_argument('--period', 'p', action='store', type=int, default=1)

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

description_base = f'{name}_Phenology_{args.data}'
assetID=f'projects/{args.project}/assets/average_phenology_{name}/average_phenology_{args.data}'


##################################################################
# Split study regions into grid cells of specified size.
##################################################################

#Specify grid size in projection, x and y units (based on projection).
projection = 'EPSG:4326' # WGS84 lat lon

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

    start_date = ee.Date.fromYMD(args.start, 1, 1)
    end_date = ee.Date.fromYMD(args.end + 1, 1, 1)

    ############################
    ############################
    # NEED TO REPLACE PHENOLOGY IN CALL HERE!!!
    ############################
    ############################
    if args.data == 'Landsat':
        col = preprocessing.preprocess_Landsat(start_date, end_date,
                                               gridCell, phenology)
    elif args.data == 'MODIS':
        col = preprocessing.preprocess_MODIS(start_date, end_date,
                                             gridCell, phenology)
    elif args.data == 'Sentinel2':
        col = preprocessing.preprocess_Sentinel2(start_date, end_date,
                                                 gridCell, phenology)
    elif args.data == 'HLS':
        col = preprocessing.preprocess_HLS(start_date, end_date,
                                           gridCell, phenology)


    #################################
    # Window smoothing
    #################################
    doys = ee.List.sequence(0, 365, 1)
    def window_smooth(day):
        day = ee.Number(day)
        doy_ims = col.filter(
            ee.Filter.dayOfYear(
                day.subtract(window_radius).add(365).mod(365), 
                day.add(window_radius).mod(365)))
        return ee.Image(doy_ims.mean()).set('system:time_start', day.multiply(86400000))
        
    col_smoothed = (ee.ImageCollection(doys.map(window_smooth))
                      .filter(ee.Filter.listContains('system:band_names', 'EVI')))


    ############################################
    # Helper functions for Maximum Separability
    ############################################

    def convert_to_binary(image):
        bin_image = image.gt(thresh)
        return bin_image.copy_properties(image, 'system:time_start')

    def mask_binary(image):
        return image.updateMask(image)


    ############################################
    # Estimate absolute threshold over region
    ############################################

    max_EVI = col_smoothed.select('EVI').reduce(ee.Reducer.percentile([95]))
    min_EVI = col_smoothed.select('EVI').reduce(ee.Reducer.percentile([5]))
    amplitude = max_EVI.subtract(min_EVI)
    thresh = (amplitude.multiply(args.threshold)
                       .add(min_EVI))


    ##################################################
    # Estimate ratio of observations above the 
    # threshold before and after each day of the year
    ##################################################

    list_dates = ee.List.sequence(0, 365, lag);
    col_bin = col_smoothed.map(convert_to_binary)

    def calc_ratio_difference(doy):
        target_day = ee.Number(doy)

        # Calculate ratio of green days before doy
        window_start = target_day.subtract(args.change_window).add(365).mod(365)
        window_end = target_day
        col_before = col_bin.filter(ee.Filter.dayOfYear(window_start, window_end))
        ratio_before = col_before.select('EVI').mean().rename('EVI')
        
        # Calculate ratio of green days after doy
        window_start = target_day
        window_end = target_day.add(args.change_window).add(365).mod(365)
        col_after = col_bin.filter(ee.Filter.dayOfYear(window_start, window_end))
        ratio_after = col_after.select('EVI').mean().rename('EVI')

        # Calculate difference in ratios
        ratio_diff = (ratio_after.subtract(ratio_before)
                                 .multiply(-1)
                                 .rename('ratio_diff')
                                 .addBands(ee.Image(target_day).toFloat().rename('doy'))
                                 .set('system:time_start', target_day.multiply(86400000))
        return ratio_diff

    ratio_diffs = list_dates.calc_ratio_difference(doy)


    ##################################################
    # Extract SoS and EoS
    ##################################################

    phenometrics = ratio_diffs.reduce(
        ee.Reducer.min(2).combine(
            ee.Reducer.max(2), "", true))
    SoS = phenometrics.select('min1').rename('SoS')
    EoS = phenometrics.select('max1').rename('SoS')


    ##################################################
    # Export results
    ##################################################

    export_image = SoS.addBands(EoS).int16();
    if args.submit:
        if gridSize > 1:
            image_name = f'{assetID}_tile_{i}'
            description = f'{description_base}_tile_{i}'
        else:
            image_name = assetID
            description = description_base

        task = ee.batch.Export.image.toAsset(
            image=export_image,
            description=description,
            assetId=image_name,
            region=gridCell, 
            scale=preprocessing.resolutions[args.data],
            crs=args.crs,
            pyramidingPolicy={'.default': 'mean'},
            maxPixels=1e10
        )
        task.start()