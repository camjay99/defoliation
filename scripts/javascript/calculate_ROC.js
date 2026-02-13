var project = "<insert project here>";

function ROC(image, table, output, scale) {
  table = table.map(function(feature) {
    feature = ee.Feature(feature);
    return feature.setGeometry(
              ee.Geometry.Point(
                [feature.get('longitude'), 
                feature.get('latitude')],
                'EPSG:4326'
              )
            );
  });
  table = table.filter(ee.Filter.gte('combined', 0));

  var mean_intensity = image.select('mean_intensity');

  var thresholds = ee.List.sequence(0.3, -0.40, -0.005);

  var rates = thresholds.map(function(threshold) {
    var thresholded = mean_intensity.lte(ee.Number(threshold));
    
    var classified = thresholded.reduceRegions({
      collection: table,
      reducer: ee.Reducer.mean(),
      scale: scale,  // meters
      crs: 'EPSG:4326',
    });
    
    var valid_classified = classified.filter(ee.Filter.notNull(['mean']));
    
    var corr_classified = valid_classified.map(function(feature) 
      {
        return feature.set('correct', ee.Number(feature.get('mean')).eq(feature.get('combined')));
      }
    );
    
    // These are ones that are actual pos/neg
    var positives = corr_classified.filter(ee.Filter.eq('combined', 1));
    var negatives = corr_classified.filter(ee.Filter.eq('combined', 0));
    
    var true_pos_rate = positives.aggregate_mean('correct');
    var false_pos_rate = ee.Number(1).subtract(negatives.aggregate_mean('correct'));
    
    // These are ones that are class pos/neg
    var class_positives = corr_classified.filter(ee.Filter.eq('mean', 1));
    var class_negatives = corr_classified.filter(ee.Filter.eq('mean', 0));
    
    var pos_ua = class_positives.aggregate_mean('correct');
    var neg_ua = class_negatives.aggregate_mean('correct');
    
    var oa = corr_classified.aggregate_mean('correct');
    
    return ee.Feature(null, {'threshold':threshold, 
                             'TPR':true_pos_rate, 'FPR':false_pos_rate,
                             'OA':oa,
                             'Pos_UA':pos_ua, 'Neg_UA':neg_ua,
                             'valid_classified':valid_classified.size()});
  });


  Export.table.toDrive({
    collection: ee.FeatureCollection(rates),
    description: 'ROC_'+output,
    folder: 'defoliation',
    fileFormat: 'CSV',
    selectors: ['threshold', 'TPR', 'FPR', 'OA', 'Pos_UA', 'Neg_UA', 'valid_classified']
  });
}


// Mt Pleasant
var table = ee.FeatureCollection('projects/'+project+'/assets/mt_pleasant_validation');

var image = ee.Image('projects/'+project+'/assets/Mt_Pleasant_Defoliation/Sentinel2_2021');
var output = 'Mt_Pleasant_Sentinel2_2021';
var scale = 10;
ROC(image, table, output, scale);

image = ee.Image('projects/'+project+'/assets/Mt_Pleasant_Defoliation/Sentinel2_unscaled_2021');
output = 'Mt_Pleasant_Sentinel2_unscaled_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Mt_Pleasant_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'all_year')).mosaic();
output = 'Mt_Pleasant_Sentinel2_harmonic_all_year_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Mt_Pleasant_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'summer')).mosaic();
output = 'Mt_Pleasant_Sentinel2_harmonic_summer_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Mt_Pleasant_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'growing_season')).mosaic();
output = 'Mt_Pleasant_Sentinel2_harmonic_growing_season_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Mt_Pleasant_Defoliation')
          .filter(ee.Filter.eq('method', 'means')).mosaic();
output = 'Mt_Pleasant_Sentinel2_means_2021';
scale = 10;
ROC(image, table, output, scale);


// Allegheny
table = ee.FeatureCollection('projects/'+project+'/assets/allegheny_validation');

image = ee.Image('projects/'+project+'/assets/Allegheny_Defoliation/Sentinel2_2021');
output = 'Allegheny_Sentinel2_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.Image('projects/'+project+'/assets/Allegheny_Defoliation/Sentinel2_unscaled_2021');
output = 'Allegheny_Sentinel2_unscaled_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Allegheny_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'all_year')).mosaic();
output = 'Allegheny_Sentinel2_harmonic_all_year_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Allegheny_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'summer')).mosaic();
output = 'Allegheny_Sentinel2_harmonic_summer_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Allegheny_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'growing_season')).mosaic();
output = 'Allegheny_Sentinel2_harmonic_growing_season_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Allegheny_Defoliation')
          .filter(ee.Filter.eq('method', 'means')).mosaic();
output = 'Allegheny_Sentinel2_means_2021';
scale = 10;
ROC(image, table, output, scale);

// Arnot Forest
table = ee.FeatureCollection('projects/'+project+'/assets/arnot_forest_validation');

image = ee.Image('projects/'+project+'/assets/Arnot_Forest_Defoliation/Sentinel2_2022');
output = 'Arnot_Forest_Sentinel2_2022';
scale = 10;
ROC(image, table, output, scale);

image = ee.Image('projects/'+project+'/assets/Arnot_Forest_Defoliation/Sentinel2_unscaled_2022');
output = 'Arnot_Forest_Sentinel2_unscaled_2022';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Arnot_Forest_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'all_year')).mosaic();
output = 'Arnot_Forest_Sentinel2_harmonic_all_year_2022';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Arnot_Forest_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'summer')).mosaic();
output = 'Arnot_Forest_Sentinel2_harmonic_summer_2022';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Arnot_Forest_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'growing_season')).mosaic();
output = 'Arnot_Forest_Sentinel2_harmonic_growing_season_2022';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Arnot_Forest_Defoliation')
          .filter(ee.Filter.eq('method', 'means')).mosaic();
output = 'Arnot_Forest_Sentinel2_means_2022';
scale = 10;
ROC(image, table, output, scale);

// Turkey Point
table = ee.FeatureCollection('projects/'+project+'/assets/turkey_point_validation');

image = ee.Image('projects/'+project+'/assets/Turkey_Point_Defoliation/Sentinel2_2021');
output = 'Turkey_Point_Sentinel2_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.Image('projects/'+project+'/assets/Turkey_Point_Defoliation/Sentinel2_unscaled_2021');
output = 'Turkey_Point_Sentinel2_unscaled_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Turkey_Point_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'all_year')).mosaic();
output = 'Turkey_Point_Sentinel2_harmonic_all_year_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Turkey_Point_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'summer')).mosaic();
output = 'Turkey_Point_Sentinel2_harmonic_summer_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Turkey_Point_Defoliation')
          .filter(ee.Filter.eq('method', 'harmonic'))
          .filter(ee.Filter.eq('period', 'growing_season')).mosaic();
output = 'Turkey_Point_Sentinel2_harmonic_growing_season_2021';
scale = 10;
ROC(image, table, output, scale);

image = ee.ImageCollection('projects/'+project+'/assets/Turkey_Point_Defoliation')
          .filter(ee.Filter.eq('method', 'means')).mosaic();
output = 'Turkey_Point_Sentinel2_means_2021';
scale = 10;
ROC(image, table, output, scale);