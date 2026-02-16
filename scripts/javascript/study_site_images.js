var project = "ee-cjc378";

// These are used for Figure 1
var alle_polygon = ee.Geometry.Polygon([[-79.09303776782116, 42.154449896225515],
          [-79.09303776782116, 41.754107496880174],
          [-78.64259831469616, 41.754107496880174],
          [-78.64259831469616, 42.154449896225515]]);
var mtp_polygon = ee.Geometry.Polygon([[-76.40060016519821, 42.47727532465593],
          [-76.40060016519821, 42.443208497007845],
          [-76.3556248844365, 42.443208497007845],
          [-76.3556248844365, 42.47727532465593]]);
var tp_polygon = ee.Geometry.Polygon(
         [[[-80.57997293051788, 42.649124560997215],
           [-80.57997293051788, 42.61988855677763],
           [-80.5315644222171, 42.61988855677763],
           [-80.5315644222171, 42.649124560997215]]], null, false);
var af_polygon = ee.Geometry.Polygon(
         [[[-76.68476578221755, 42.29975344583736],
           [-76.68476578221755, 42.25466417545956],
           [-76.60614487157302, 42.25466417545956],
           [-76.60614487157302, 42.29975344583736]]], null, false);

// These are used for Figure S5
var mtp_polygon2 = ee.Geometry.Polygon(
    [-76.38845246824344, 42.46436087095481,
     -76.37167256864628, 42.46436087095481,
     -76.37167256864628, 42.47417424877469,
     -76.38845246824344, 42.47417424877469], null, false);

var pos_polygon = ee.Geometry.Polygon(
    [-76.41623453360863,42.41051611482946,
     -76.37769655448265,42.41051611482946,
     -76.37769655448265,42.430158205380344,
     -76.41623453360863,42.430158205380344], null, false);

var neg_polygon = ee.Geometry.Polygon(
    [-74.62383683191842,43.046694487257746,
     -74.61315091120309,43.046694487257746,
     -74.61315091120309,43.05230810581971,
     -74.62383683191842,43.05230810581971], null, false);

// Specify the region to be analyzed, the base year, and the defoliation year.
var region = af_polygon;
var region_name = 'arnot_forest';
var clear_year = 2019;
var year = 2020;

// Put together average summer image.

// Cloud Score+ image collection. Note Cloud Score+ is produced from Sentinel-2
// Level 1C data and can be applied to either L1C or L2A collections.
var csPlus = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');

// Use 'cs' or 'cs_cdf', depending on your use case; see docs for guidance.
var QA_BAND = 'cs_cdf';

// The threshold for masking; values between 0.50 and 0.65 generally work well.
// Higher values will remove thin clouds, haze & cirrus shadows.
var CLEAR_THRESHOLD = 0.65;
function preprocess_s2(image) {
    // New Bands
    var image_s = image.divide(10000);
    var EVI = image_s.expression(
        '2.5 * ((NIR-RED) / (NIR + 6 * RED - 7.5* BLUE + 1))', {
            'NIR': image_s.select('B8'),
            'RED': image_s.select('B4'),
            'BLUE': image_s.select('B2')
        }).rename('EVI');
    
    var doy = image.date().getRelative('day', 'year');
    var doy_band = ee.Image.constant(doy).uint16().rename('doy');
    
    // Masks
    //var forest_mask = nlcd_landcover.gte(41).and(nlcd_landcover.lte(71))
    var EVI_mask = EVI.lte(1).and(EVI.gte(0));
    var cloud_mask = image.select(QA_BAND).gte(CLEAR_THRESHOLD);
                 
    return (image.addBands(ee.Image([EVI, doy_band]))
                 .updateMask(EVI_mask.and(cloud_mask))
                 .set('doy', doy)
                 .copyProperties(image, ['system:time_start']));
}

// Harmonized Sentinel-2 Level 2A collection.
var s2_clear = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region)
        .filterDate(clear_year + '-01-01', (clear_year + 1) + '-01-01')
        .filter(ee.Filter.dayOfYear(150, 250))
        .linkCollection(csPlus, [QA_BAND])
        .map(preprocess_s2))
        .select(['B4', 'B3', 'B2']);
        
var s2_clear_mean = s2_clear.mean().clip(region);

// Harmonized Sentinel-2 Level 2A collection.
var s2 = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region)
        .filterDate(year + '-01-01', (year + 1) + '-01-01')
        .filter(ee.Filter.dayOfYear(150, 250))
        .linkCollection(csPlus, [QA_BAND])
        .map(preprocess_s2))
        .select(['B4', 'B3', 'B2']);

var s2_mean = s2.mean().clip(region);

if (region_name == 'turkey_point') {
  var synth = ee.Image('projects/'+project+'/assets/Turkey_Point_Trends/Sentinel2_unscaled');
  synth = synth.select('slope').multiply(185).add(synth.select('offset'));
  var scores = ee.ImageCollection('projects/'+project+'/assets/Turkey_Point_Defoliation')
                  .filter(ee.Filter.eq('method', 'Sentinel2_unscaled'))
                  .filter(ee.Filter.eq('year', year))
                  .select('mean_intensity').mosaic();
  var classes = scores.lte(-0.04);
  var forest = ee.FeatureCollection(ee.Feature(turkey_point_forest, {forest:1}))
    .reduceToImage({
      properties: ['forest'],
      reducer: ee.Reducer.first()
    })
    .unmask().clip(region);
  forest = ee.Image(1).subtract(forest);
    
  var logging = ee.Image(0);
  var obs = s2.filter(ee.Filter.dayOfYear(161, 208)).select('B2').count().lt(2);
} else {
  var synth = trends.filter(ee.Filter.neq('source', 'HLS'))
                    .mosaic().clip(region);
  synth = synth.select('slope').multiply(185).add(synth.select('offset'));       
  var scores = defol_scores.filter(ee.Filter.eq('year', year))
                           .filter(ee.Filter.eq('method', 'Sentinel2_unscaled'))
                           .mosaic().clip(region);
  var classes = defol_denoised.filter(ee.Filter.eq('year', year)).mosaic().clip(region);
  
  var qa = qa_masks.filterBounds(region).mosaic().clip(region);
  Map.addLayer(qa);
  // For Mask 2^15 for forests and 132 for observation/logging masks
  // Maybe can also just do 2^2 for obs and 2^7 for logging
  
  var forest_mask = ee.Number(2).pow(ee.Number(15)).toUint16(); // Forest
  var logging_mask = ee.Number(2).pow(ee.Number(year - 2019 + 5)).toUint16(); // Logging
  var obs_mask = ee.Number(2).pow(ee.Number(year-2019)).toUint16(); // Observation mask
  
  var forest = qa.bitwiseNot().bitwiseAnd(forest_mask).eq(forest_mask); // Regions that are forest
  var logging = qa.bitwiseNot().bitwiseAnd(logging_mask).eq(logging_mask); // Regions with logging
  var obs = qa.bitwiseNot().bitwiseAnd(obs_mask).eq(obs_mask); // Regions with insufficient images
}
Map.addLayer(forest)
var image = ee.Image([s2_mean, s2_clear_mean, synth, scores, classes, forest, logging, obs]).toFloat();
Map.addLayer(image)
Map.addLayer(obs);
Export.image.toDrive({
  image: image,
  description: 'defol_eval_' + region_name + '_' + year,
  folder: 'Defoliation',
  region: region,
  scale: 10,
  crs: 'EPSG:32618'
});