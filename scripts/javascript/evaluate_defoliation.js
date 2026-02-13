var project = "<insert project here>";

var mtp_points = ee.FeatureCollection("projects/"+project+"/assets/Mt_Pleasant_Random_Sample");
var alle_points = ee.FeatureCollection("projects/"+project+"/assets/Allegheny_Random_Sample1");
var af_points = ee.FeatureCollection("projects/"+project+"/assets/Arnot_Forest_Random_Sample");
var tp_points = ee.FeatureCollection("projects/"+project+"/assets/Turkey_Point_Random_Sample");

// Replace mtp_points with site of interest, and number in get to 
// visualize a difference sample.
var geometry = ee.Feature(mtp_points.toList(200).get(200)).geometry();

/************************************************
 * Sentinel-2 setup
 * **********************************************/
// Cloud Score+ image collection. Note Cloud Score+ is produced from Sentinel-2
// Level 1C data and can be applied to either L1C or L2A collections.
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED')

// Use 'cs' or 'cs_cdf', depending on your use case; see docs for guidance.
var QA_BAND = 'cs_cdf'

// The threshold for masking; values between 0.50 and 0.65 generally work well.
// Higher values will remove thin clouds, haze & cirrus shadows.
var CLEAR_THRESHOLD = 0.65

// Load NLCD 2019 landcover map
var nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD') 
    .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover')

function preprocess_s2(image) {
    // New Bands
    var image_s = image.divide(10000)
    var EVI = image_s.expression(
        '2.5 * ((NIR-RED) / (NIR + 6 * RED - 7.5* BLUE + 1))', {
            'NIR': image_s.select('B8'),
            'RED': image_s.select('B4'),
            'BLUE': image_s.select('B2')
        }).rename('EVI')
    
    var doy = image.date().getRelative('day', 'year')
    var doy_band = ee.Image.constant(doy).uint16().rename('doy')
    
    // Masks
    //var forest_mask = nlcd_landcover.gte(41).and(nlcd_landcover.lte(71))
    var EVI_mask = EVI.lte(1).and(EVI.gte(0))
    var cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD)
                 
    
    return (image.addBands(ee.Image([EVI, doy_band]))
                 //.updateMask(forest_mask.and(EVI_mask).and(cloud_mask))
                 .updateMask(EVI_mask.and(cloud_mask))
                 .set('doy', doy)
                 .copyProperties(image, ['system:time_start']));
}
// Harmonized Sentinel-2 Level 2A collection.
var s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(geometry)
        .filterDate('2019-01-01', '2024-01-01')
        .linkCollection(csPlus, [QA_BAND])
        .map(preprocess_s2));
        
//Map.addLayer(s2.filter(ee.Filter.dayOfYear(161, 208)).select('EVI').count())

// Define the chart and print it to the console.
var chart = ui.Chart.image
                .doySeriesByYear({
                  imageCollection: s2,
                  bandName: 'EVI',
                  region: geometry,
                  regionReducer: ee.Reducer.mean(),
                  scale: 10,
                  sameDayReducer: ee.Reducer.mean(),
                  startDay: 1,
                  endDay: 365
                })
                .setOptions({
                  title: 'Sentinel-2',
                  hAxis: {
                    title: 'Day of year',
                    titleTextStyle: {italic: false, bold: true}
                  },
                  vAxis: {
                    title: 'EVI',
                    titleTextStyle: {italic: false, bold: true}
                  },
                  lineWidth: 5,
                  interpolateNulls: true
                });
print(chart);

var timeSeries = ee.FeatureCollection(s2.map(function(image) {
  var stats = image.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: geometry,
    scale: 10,
    maxPixels: 1e10
  });
  // reduceRegion doesn't return any output if the image doesn't intersect
  // with the point or if the image is masked out due to cloud
  // If there was no ndvi value found, we set the ndvi to a NoData value -9999
  var evi = ee.List([stats.get('EVI'), -9999])
    .reduce(ee.Reducer.firstNonNull());
 
  // Create a feature with null geometry and NDVI value and date as properties
  var f = ee.Feature(null, {'EVI': evi,
    'doy': image.get('doy')});
  return f;
}));

// Export to CSV
Export.table.toDrive({
    collection: timeSeries,
    description: 'Winter_Harvest_Time_Series',
    folder: 'Defoliation',
    selectors: ['EVI', 'doy'],
    fileFormat: 'CSV'
})

/*********************************************************
* Prepare Landsat 7 and 8
**********************************************************/

function applyScaleFactors(image) {
    // Bits 4 and 3 are cloud shadow and cloud, respectively.
    var cloudShadowBitMask = 1 << 4;
    var cloudsBitMask = 1 << 3;
    // Get the pixel QA band.
    var qa = image.select('QA_PIXEL');
    // Both flags should be set to zero, indicating clear conditions.
    var mask = (qa.bitwiseAnd(cloudShadowBitMask).eq(0)
                .and(qa.bitwiseAnd(cloudsBitMask).eq(0)));
    
    var opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2);
    return (image.addBands(opticalBands, null, true) 
                 .updateMask(mask).copyProperties(image, ['system:time_start']));
}
var l7 = (ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        .filterBounds(geometry)
        .filterDate('2019-01-01', '2024-01-01')
        .map(applyScaleFactors));
var l8 = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(geometry)
        .filterDate('2019-01-01', '2024-01-01')
        .map(applyScaleFactors));


/*******************************************************************
* Harmonize Landsat 7 and 8
********************************************************************/

function harmonizeL7(image) {
    return image.select(['SR_B1', 'SR_B2', 'SR_B3', 'SR_B4', 'SR_B5', 'SR_B7'],['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2']).copyProperties(image, ['system:time_start']);
}

function harmonizeL8(image){
    return image.select(['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7'],['BLUE', 'GREEN', 'RED', 'NIR', 'SWIR1', 'SWIR2']);
}

// Map harmonizations and create combined collection
var l7 = l7.map(harmonizeL7);
var l8 = l8.map(harmonizeL8);

// Combined collection
var ls = l7.merge(l8);


/*******************************************************************
 * Mask nonforest/off-season and compute NDVI and DOY for each image
********************************************************************/

// Load NLCD 2019 landcover map
var nlcd_landcover = ee.ImageCollection('USGS/NLCD_RELEASES/2019_REL/NLCD')
    .filter(ee.Filter.eq('system:index', '2019')).first().select('landcover');
// Calculate EVI for the scene
function preprocess(image) {
    // New bands
    var EVI = image.expression(
        '2.5 * ((NIR - RED) / (NIR + 6 * RED + 7.5 * BLUE + 1))',
        {
            'NIR': image.select('NIR'),
            'RED': image.select('RED'),
            'BLUE': image.select('BLUE')
        }).rename('EVI');
    
    var doy = image.date().getRelative('day', 'year');
    var doy_band = ee.Image.constant(doy).uint16().rename('doy');
    
    // Masks
    //var forest_mask = nlcd_landcover.gte(41).and(nlcd_landcover.lte(71));
    var EVI_mask = EVI.lte(1).and(EVI.gte(0));
    
    // Return the masked image with EVI bands.
    return (image.addBands(ee.Image([EVI, doy_band]))
                 //.updateMask(forest_mask)
                 .updateMask(EVI_mask)
                 .copyProperties(image, ['system:time_start']));
}

ls = ls.map(preprocess);

// Define the chart and print it to the console.
var chart = ui.Chart.image
                .doySeriesByYear({
                  imageCollection: ls,
                  bandName: 'EVI',
                  region: geometry,
                  regionReducer: ee.Reducer.mean(),
                  scale: 30,
                  sameDayReducer: ee.Reducer.mean(),
                  startDay: 1,
                  endDay: 365
                })
                .setOptions({
                  title: 'Landsat',
                  hAxis: {
                    title: 'Day of year',
                    titleTextStyle: {italic: false, bold: true}
                  },
                  vAxis: {
                    title: 'EVI',
                    titleTextStyle: {italic: false, bold: true}
                  },
                  lineWidth: 5,
                  interpolateNulls: true
                });
print(chart);