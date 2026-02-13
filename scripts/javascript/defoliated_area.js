var project = "<insert project name here>";

var scores_2020 = ee.Image("projects/"+project+"/assets/scores_mask_2020");
var scores_2021 = ee.Image("projects/"+project+"/assets/scores_mask_2021");
var scores_2022 = ee.Image("projects/"+project+"/assets/scores_mask_2022");
var scores_2023 = ee.Image("projects/"+project+"/assets/scores_mask_2023");
var raw_scores = ee.ImageCollection("projects/"+project+"/assets/defoliation_score_New_York");

var new_york = ee.FeatureCollection("FAO/GAUL/2015/level1").filter(ee.Filter.eq('ADM1_NAME', 'New York'));

var raw_scores_2020 = raw_scores.filter(ee.Filter.eq('year', 2020))
                                .filter(ee.Filter.neq('source', 'HLS')).mosaic();
// Two versions, one for mappable masked by qa_mask and one for scores masked by score
var raw_scores_2020_qa = raw_scores_2020.updateMask(scores_2020.select('qa_mask_3'));
var raw_scores_2020_sc = raw_scores_2020.updateMask(scores_2020.select('score_3'));
var mappable_2020 = raw_scores_2020_qa.mask().rename('mappable');
var defol_2020 = raw_scores_2020_sc.lt(-0.04).rename('defol');
var severe_2020 = raw_scores_2020_sc.lt(-0.2).rename('severe');
var im_2020 = ee.Image([mappable_2020, defol_2020, severe_2020]).set('year', 2020);

var raw_scores_2021 = raw_scores.filter(ee.Filter.eq('year', 2021))
                                .filter(ee.Filter.neq('source', 'HLS')).mosaic();
                                
var raw_scores_2021_qa =  raw_scores_2021.updateMask(scores_2021.select('qa_mask_3'));
var raw_scores_2021_sc =  raw_scores_2021.updateMask(scores_2021.select('score_3'));
var mappable_2021 = raw_scores_2021_qa.mask();
var defol_2021 = raw_scores_2021_sc.lt(-0.04).rename('defol');
var severe_2021 = raw_scores_2021_sc.lt(-0.2).rename('severe');
var im_2021 = ee.Image([mappable_2021, defol_2021, severe_2021]).set('year', 2021);

var raw_scores_2022 = raw_scores.filter(ee.Filter.eq('year', 2022))
                                .filter(ee.Filter.neq('source', 'HLS')).mosaic()
                                
var raw_scores_2022_qa = raw_scores_2022.updateMask(scores_2022.select('qa_mask_3'));
var raw_scores_2022_sc = raw_scores_2022.updateMask(scores_2022.select('score_3'));
var mappable_2022 = raw_scores_2022_qa.mask();
var defol_2022 = raw_scores_2022_sc.lt(-0.04).rename('defol');
var severe_2022 = raw_scores_2022_sc.lt(-0.2).rename('severe');
var im_2022 = ee.Image([mappable_2022, defol_2022, severe_2022]).set('year', 2022);

var raw_scores_2023 = raw_scores.filter(ee.Filter.eq('year', 2023))
                                .filter(ee.Filter.neq('source', 'HLS')).mosaic()
var raw_scores_2023_qa = raw_scores_2023.updateMask(scores_2023.select('qa_mask_3'));
var raw_scores_2023_sc = raw_scores_2023.updateMask(scores_2023.select('qa_mask_3'));
var mappable_2023 = raw_scores_2023_qa.mask();
var defol_2023 = raw_scores_2023_sc.lt(-0.04).rename('defol');
var severe_2023 = raw_scores_2023_sc.lt(-0.2).rename('severe');
var im_2023 = ee.Image([mappable_2023, defol_2023, severe_2023]).set('year', 2023);


var images = ee.ImageCollection([im_2020,im_2021,im_2022,im_2023]);
var results = images.map(function (image) {
  var stats = image.multiply(ee.Image.pixelArea()).reduceRegions({
    collection: new_york,
    reducer: ee.Reducer.sum(),
    scale: 10,
    crs: 'EPSG:5070',
  });
  return stats.first().set('year', image.get('year'));
});

Export.table.toDrive({
  collection: results,
  description: 'area_sums',
  folder: 'Defoliation',
  fileFormat: 'CSV',
  selectors: ['year', 'defol', 'severe']
});